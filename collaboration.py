"""Public expert profiles, directed requests, private conversation assets and progress."""
import io,json,time,re,os
from datetime import date
from pathlib import Path
from fastapi import Depends,UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from PIL import Image,ImageOps

REPLY_HOURS=48

def migrate(c):
    c.executescript('''
    CREATE TABLE IF NOT EXISTS request_targets(request_id TEXT PRIMARY KEY REFERENCES requests(id),expert_id TEXT NOT NULL REFERENCES users(id),released INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS reply_deadlines(invite_id TEXT PRIMARY KEY REFERENCES invites(id),due REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS request_reasons(request_id TEXT PRIMARY KEY REFERENCES requests(id),reason TEXT NOT NULL,updated REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS chat_files(id TEXT PRIMARY KEY,invite_id TEXT NOT NULL REFERENCES invites(id),user_id TEXT NOT NULL REFERENCES users(id),name TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,created REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS message_files(message_id TEXT REFERENCES messages(id),file_id TEXT UNIQUE REFERENCES chat_files(id),PRIMARY KEY(message_id,file_id));
    CREATE TABLE IF NOT EXISTS message_receipts(invite_id TEXT REFERENCES invites(id),user_id TEXT REFERENCES users(id),seen REAL NOT NULL,PRIMARY KEY(invite_id,user_id));
    CREATE TABLE IF NOT EXISTS message_tokens(user_id TEXT REFERENCES users(id),token TEXT,message_id TEXT REFERENCES messages(id),PRIMARY KEY(user_id,token));
    CREATE TABLE IF NOT EXISTS expert_views(expert_id TEXT REFERENCES users(id),visitor TEXT,day TEXT,PRIMARY KEY(expert_id,visitor,day));
    ''')

def targeted_match(s,c,row):
    target=c.execute('SELECT * FROM request_targets WHERE request_id=? AND released=0',(row['id'],)).fetchone()
    if not target:return None
    if c.execute('SELECT 1 FROM invites WHERE request_id=?',(row['id'],)).fetchone():return 0
    b=json.loads(row['data'])
    available=c.execute('''SELECT 1 FROM profiles pr WHERE user_id=? AND accepting=1 AND EXISTS(SELECT 1 FROM portfolios p WHERE p.user_id=pr.user_id AND published=1 AND category=? AND (price=0 OR price<=?))''',(target['expert_id'],b['category'],b['budget'])).fetchone()
    if not available or not s.features.eligible(c,target['expert_id'],b):return 0
    key=s.uid();now=time.time()
    c.execute('INSERT INTO invites VALUES(?,?,?,?,?)',(key,row['id'],target['expert_id'],'invited',now))
    c.execute('INSERT INTO reply_deadlines VALUES(?,?)',(key,now+REPLY_HOURS*3600))
    s.notice(c,target['expert_id'],'고객이 회원님을 지정해 의뢰했습니다. 48시간 안에 작업 가능 여부를 알려 주세요.',kind='new_request')
    return 1

def expire(s,c):
    # Ordinary recommendations keep their existing behavior; directed requests require customer consent to release.
    rows=c.execute("SELECT i.* FROM invites i JOIN reply_deadlines d ON d.invite_id=i.id JOIN requests r ON r.id=i.request_id WHERE i.status='invited' AND d.due<? AND r.status='open'",(time.time(),)).fetchall()
    for i in rows:
        c.execute("UPDATE invites SET status='expired' WHERE id=?",(i['id'],))
        client=c.execute('SELECT user_id FROM requests WHERE id=?',(i['request_id'],)).fetchone()[0]
        s.notice(c,client,'전문가의 응답 기한이 지났습니다. 의뢰에서 다른 전문가 추천을 선택할 수 있습니다.')
        s.notice(c,i['expert_id'],'응답 기한이 지나 해당 의뢰의 작업 가능 응답을 마감했습니다.')

def bind_target(s,c,key,expert,user):
    if not expert:
        c.execute('DELETE FROM request_targets WHERE request_id=?',(key,));return
    if expert==user['id']:s.fail('본인에게 의뢰할 수 없습니다.')
    if not c.execute('SELECT 1 FROM portfolios WHERE user_id=? AND published=1',(expert,)).fetchone():s.fail('공개 작업이 있는 전문가를 선택해 주세요.')
    c.execute('INSERT OR REPLACE INTO request_targets VALUES(?,?,0)',(key,expert))

def validate_files(s,c,ids,invite,user):
    if len(set(ids))!=len(ids):s.fail('중복 첨부입니다.')
    for key in ids:
        if not c.execute('SELECT 1 FROM chat_files WHERE id=? AND invite_id=? AND user_id=?',(key,invite,user)).fetchone():s.fail('이 대화에 직접 올린 파일만 첨부할 수 있습니다.')
        if c.execute('SELECT 1 FROM message_files WHERE file_id=?',(key,)).fetchone():s.fail('이미 전송한 파일입니다.')

def file_list(c,message):
    return [dict(f) for f in c.execute('SELECT f.id,f.name,f.mime,f.size FROM chat_files f JOIN message_files m ON m.file_id=f.id WHERE m.message_id=?',(message,))]

class TargetRelease(BaseModel):
    confirmed: bool=False
class Reason(BaseModel):
    reason:str=Field(min_length=2,max_length=300)
class Seen(BaseModel):
    message_id:str=Field(max_length=24)
class Visit(BaseModel):
    visitor:str=Field(pattern=r'^[a-zA-Z0-9-]{8,80}$')

def install(s):
    app=s.app
    @app.get('/api/experts/{key}')
    def expert(key:str):
        with s.db() as c:
            p=c.execute('SELECT u.id,u.name,p.bio,p.category,p.accepting FROM users u JOIN profiles p ON p.user_id=u.id WHERE u.id=?',(key,)).fetchone()
            works=[s.portfolio_record(c,r) for r in c.execute('SELECT * FROM portfolios WHERE user_id=? AND published=1 ORDER BY created DESC',(key,))]
            if not p or not works:s.fail('공개 프로필을 찾을 수 없습니다.',404)
            pref=c.execute('SELECT data FROM expert_preferences WHERE user_id=?',(key,)).fetchone()
            pref=json.loads(pref[0]) if pref else {}
            return {**dict(p),'works':works,'available_from':pref.get('available_from'),'turnaround_days':pref.get('turnaround_days'),'reply_hours':REPLY_HOURS}
    @app.post('/api/experts/{key}/views')
    def view(key:str,body:Visit):
        s.limit('profile-view:'+body.visitor,120,3600)
        with s.db() as c:
            if not c.execute('SELECT 1 FROM portfolios WHERE user_id=? AND published=1',(key,)).fetchone():s.fail('공개 프로필이 없습니다.',404)
            c.execute('INSERT OR IGNORE INTO expert_views VALUES(?,?,?)',(key,body.visitor,date.today().isoformat()))
        return {'ok':True}
    @app.get('/api/my/readiness')
    def readiness(user=Depends(s.current)):
        with s.db() as c:
            profile=c.execute('SELECT * FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
            works=c.execute('SELECT count(*) FROM portfolios WHERE user_id=? AND published=1',(user['id'],)).fetchone()[0]
            schedule=bool(c.execute('SELECT 1 FROM expert_preferences WHERE user_id=?',(user['id'],)).fetchone())
            phone=c.execute("SELECT 1 FROM phone_contacts WHERE user_id=? AND enabled=1 AND mode='production'",(user['id'],)).fetchone()
            mail=c.execute('SELECT data FROM notify_preferences WHERE user_id=?',(user['id'],)).fetchone()
            email_enabled=bool(mail and json.loads(mail[0]).get('email'))
            return {'profile':bool(profile),'published':works,'schedule':schedule,'accepting':bool(profile and profile['accepting']),'can_activate':bool(profile and works and schedule),'external_notifications':bool(s.PRODUCTION and (email_enabled or (phone and s.alimtalk.live(s))))}
    @app.post('/api/my/activate')
    def activate(user=Depends(s.current)):
        r=readiness(user)
        if not r['can_activate']:s.fail('공개 작업과 작업 조건을 먼저 준비해 주세요.')
        with s.db() as c:
            c.execute('UPDATE profiles SET accepting=1 WHERE user_id=?',(user['id'],));s.event(c,user['id'],'expert_activated')
        return {'ok':True}
    @app.post('/api/requests/{key}/recommend-others')
    def release(key:str,body:TargetRelease,user=Depends(s.current)):
        if not body.confirmed:s.fail('다른 전문가에게 전달할지 확인해 주세요.')
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE');r=s.own_request(c,key,user);expire(s,c)
            target=c.execute('SELECT * FROM request_targets WHERE request_id=? AND released=0',(key,)).fetchone()
            if r['status']!='open' or not target:s.fail('전환할 지정 의뢰가 없습니다.')
            if c.execute("SELECT 1 FROM invites WHERE request_id=? AND status NOT IN ('declined','expired')",(key,)).fetchone():s.fail('지정 전문가의 응답을 기다리거나 기존 의뢰를 종료해 주세요.')
            c.execute('UPDATE request_targets SET released=1 WHERE request_id=?',(key,))
            c.execute('UPDATE requests SET updated=? WHERE id=?',(time.time(),key))
            return {'matched':s.match(c,r)}
    @app.get('/api/requests/{key}/progress')
    def progress(key:str,user=Depends(s.current)):
        with s.db() as c:
            r=c.execute('SELECT * FROM requests WHERE id=?',(key,)).fetchone()
            if not r or (r['user_id']!=user['id'] and not c.execute('SELECT 1 FROM invites WHERE request_id=? AND expert_id=?',(key,user['id'])).fetchone()):s.fail('의뢰를 찾을 수 없습니다.',404)
            target=c.execute('SELECT t.*,u.name FROM request_targets t JOIN users u ON u.id=t.expert_id WHERE request_id=?',(key,)).fetchone()
            invites=[dict(i) for i in c.execute('SELECT i.id,i.status,u.name,d.due FROM invites i JOIN users u ON u.id=i.expert_id LEFT JOIN reply_deadlines d ON d.invite_id=i.id WHERE request_id=?',(key,))]
            reason=c.execute('SELECT reason FROM request_reasons WHERE request_id=?',(key,)).fetchone()
            return {'status':r['status'],'target':dict(target) if target else None,'invites':invites,'reason':reason[0] if reason else '', 'can_release':bool(target and not target['released'] and r['status']=='open' and all(i['status'] in ('declined','expired') for i in invites)),'owner':r['user_id']==user['id']}
    @app.post('/api/requests/{key}/pause')
    def pause(key:str,body:Reason,user=Depends(s.current)):
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE');r=s.own_request(c,key,user)
            if r['status']!='open':s.fail('진행 중인 의뢰만 보류할 수 있습니다.')
            c.execute("UPDATE requests SET status='paused',updated=? WHERE id=?",(time.time(),key))
            c.execute('INSERT OR REPLACE INTO request_reasons VALUES(?,?,?)',(key,body.reason,time.time()))
            for i in c.execute('SELECT expert_id FROM invites WHERE request_id=?',(key,)):s.notice(c,i[0],'고객이 의뢰를 보류했습니다. 의뢰에서 사유를 확인해 주세요.',kind='paused')
        return {'ok':True}
    @app.post('/api/requests/{key}/resume')
    def resume(key:str,user=Depends(s.current)):
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE');r=s.own_request(c,key,user)
            if r['status']!='paused':s.fail('보류된 의뢰만 재개할 수 있습니다.')
            if json.loads(r['data']).get('deadline','')<=date.today().isoformat():s.fail('희망일이 지났습니다. 내용을 복사해 새 의뢰를 작성해 주세요.')
            now=time.time();c.execute("UPDATE requests SET status='open',updated=? WHERE id=?",(now,key))
            c.execute("UPDATE reply_deadlines SET due=? WHERE invite_id IN (SELECT id FROM invites WHERE request_id=? AND status='invited')",(now+REPLY_HOURS*3600,key))
            c.execute('DELETE FROM request_reasons WHERE request_id=?',(key,))
            for i in c.execute('SELECT expert_id FROM invites WHERE request_id=?',(key,)):s.notice(c,i[0],'고객이 의뢰를 다시 진행합니다. 의뢰 내용을 확인해 주세요.')
        return {'ok':True}
    @app.get('/api/conversations')
    def conversations(user=Depends(s.current)):
        with s.db() as c:
            result=[]
            for i in c.execute('''SELECT i.*,r.data,r.user_id client_id,r.status request_status FROM invites i JOIN requests r ON r.id=i.request_id WHERE i.expert_id=? OR r.user_id=? ORDER BY i.created DESC''',(user['id'],user['id'])):
                peer=i['client_id'] if user['id']==i['expert_id'] else i['expert_id']
                last=c.execute('SELECT body,created FROM messages WHERE invite_id=? ORDER BY created DESC LIMIT 1',(i['id'],)).fetchone()
                read=c.execute('SELECT seen FROM message_receipts WHERE invite_id=? AND user_id=?',(i['id'],user['id'])).fetchone()
                unread=c.execute('SELECT count(*) FROM messages WHERE invite_id=? AND user_id<>? AND created>?',(i['id'],user['id'],read[0] if read else 0)).fetchone()[0]
                result.append({'id':i['id'],'request_id':i['request_id'],'title':json.loads(i['data'])['title'],'peer':c.execute('SELECT name FROM users WHERE id=?',(peer,)).fetchone()[0],'unread':unread,'last':last['body'] if last else '', 'updated':last['created'] if last else i['created']})
            return sorted(result,key=lambda x:x['updated'],reverse=True)
    @app.post('/api/invites/{key}/read')
    def read(key:str,body:Seen,user=Depends(s.current)):
        with s.db() as c:
            s.invite_access(c,key,user)
            m=c.execute('SELECT created FROM messages WHERE id=? AND invite_id=?',(body.message_id,key)).fetchone()
            if not m:s.fail('메시지를 찾을 수 없습니다.',404)
            c.execute('INSERT INTO message_receipts VALUES(?,?,?) ON CONFLICT(invite_id,user_id) DO UPDATE SET seen=max(seen,excluded.seen)',(key,user['id'],m[0]))
        return {'ok':True}
    @app.post('/api/invites/{key}/files')
    async def upload(key:str,file:UploadFile,user=Depends(s.current)):
        s.limit('chat-file:'+user['id'],30,3600)
        with s.db() as c:
            r=s.invite_access(c,key,user)
            if r['request_status'] in ('closed','paused') or r['status'] in ('declined','expired','not_selected'):s.fail('현재 첨부할 수 없는 대화입니다.')
        raw=await file.read(8*1024*1024+1)
        if len(raw)>8*1024*1024:s.fail('파일은 8MB 이하로 올려 주세요.')
        name=Path((file.filename or '자료').replace('\\','/')).name[:100]
        if name.lower().endswith('.pdf') and raw.startswith(b'%PDF-') and b'%%EOF' in raw[-2048:]:mime='application/pdf'
        else:
            try:
                im=Image.open(io.BytesIO(raw));
                if im.format not in ('JPEG','PNG','WEBP'):s.fail('JPG·PNG·WebP만 올려 주세요.')
                im=ImageOps.exif_transpose(im);im.thumbnail((2400,2400));out=io.BytesIO();im.convert('RGB').save(out,'WEBP',quality=88);raw=out.getvalue();mime='image/webp';name=Path(name).stem+'.webp'
            except Exception:s.fail('JPG·PNG·WebP 이미지 또는 PDF만 올려 주세요.')
        fid=s.uid();folder=s.DATA/'chat-files';folder.mkdir(exist_ok=True);(folder/fid).write_bytes(raw)
        try:
            with s.db() as c:c.execute('INSERT INTO chat_files VALUES(?,?,?,?,?,?,?)',(fid,key,user['id'],name,mime,len(raw),time.time()))
        except Exception:
            (folder/fid).unlink(missing_ok=True);raise
        return {'id':fid,'name':name,'mime':mime,'size':len(raw)}
    @app.get('/api/chat-files/{key}')
    def download(key:str,user=Depends(s.current)):
        with s.db() as c:
            f=c.execute('SELECT * FROM chat_files WHERE id=?',(key,)).fetchone()
            if not f:s.fail('파일을 찾을 수 없습니다.',404)
            s.invite_access(c,f['invite_id'],user)
            if f['user_id']!=user['id'] and not c.execute('SELECT 1 FROM message_files WHERE file_id=?',(key,)).fetchone():s.fail('아직 전송하지 않은 파일입니다.',404)
        return FileResponse(s.DATA/'chat-files'/f['id'],filename=f['name'],media_type=f['mime'],headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"sandbox; default-src 'none'"})
    @app.get('/api/my/statistics')
    def stats(user=Depends(s.current)):
        with s.db() as c:
            views=c.execute('SELECT count(*) FROM expert_views WHERE expert_id=?',(user['id'],)).fetchone()[0]
            cards=c.execute('SELECT count(*) FROM exposures e JOIN portfolios p ON p.id=e.portfolio_id WHERE p.user_id=?',(user['id'],)).fetchone()[0]
            steps={}
            for name,condition in [('received','1=1'),('responded',"status IN ('available','needs_info','declined','quote_requested','quoted','selected','not_selected')"),('quoted','EXISTS(SELECT 1 FROM quotes q WHERE q.invite_id=i.id)'),('selected',"status='selected'")]:
                steps[name]=c.execute('SELECT count(*) FROM invites i WHERE expert_id=? AND '+condition,(user['id'],)).fetchone()[0]
            return {'profile_views':views,'card_views':cards,**steps}
    @app.get('/api/admin/funnel')
    def funnel(user=Depends(s.current)):
        if user['email'].lower() not in {e.strip().lower() for e in os.getenv('ADMIN_EMAILS','').split(',') if e.strip()}:s.fail('운영자만 확인할 수 있습니다.',403)
        with s.db() as c:
            return {'registered':c.execute('SELECT count(*) FROM users').fetchone()[0],'started':c.execute("SELECT count(DISTINCT user_id) FROM events WHERE event='portfolio_started'").fetchone()[0],'published':c.execute('SELECT count(DISTINCT user_id) FROM portfolios WHERE published=1').fetchone()[0],'accepting':c.execute('SELECT count(*) FROM profiles WHERE accepting=1').fetchone()[0],'received':c.execute('SELECT count(DISTINCT expert_id) FROM invites').fetchone()[0],'responded':c.execute("SELECT count(DISTINCT expert_id) FROM invites WHERE status NOT IN ('invited','expired')").fetchone()[0],'quoted':c.execute('SELECT count(DISTINCT i.expert_id) FROM invites i JOIN quotes q ON q.invite_id=i.id').fetchone()[0],'mutual':c.execute('SELECT count(*) FROM (SELECT invite_id FROM agreements WHERE confirmed=1 GROUP BY invite_id HAVING count(*)=2)').fetchone()[0]}
    @app.post('/api/my/registration-start')
    def started(user=Depends(s.current)):
        with s.db() as c:
            if not c.execute("SELECT 1 FROM events WHERE user_id=? AND event='portfolio_started'",(user['id'],)).fetchone():s.event(c,user['id'],'portfolio_started')
        return {'ok':True}

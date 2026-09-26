"""Transactional Kakao Alimtalk via SOLAPI; live sending is explicitly opt-in."""
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timezone
import httpx
from fastapi import Depends, Request
from pydantic import BaseModel, Field

# Fixed, reviewable templates, not arbitrary chat/user text.
EVENTS={
 'new_request':'새 의뢰가 도착했습니다. 작업 가능 여부를 알려 주세요.',
 'availability':'전문가가 작업 가능 여부를 알려왔습니다. 의뢰에서 확인해 주세요.',
 'quote_requested':'고객이 정식 견적을 요청했습니다. 작업 범위를 확인하고 견적을 작성해 주세요.',
 'quote_received':'새 견적이 도착했습니다. 범위·금액·수정 조건을 비교해 주세요.',
 'selection':'고객의 전문가 선택이 끝났습니다. 의뢰에서 결과를 확인해 주세요.',
 'closed':'참여 중인 의뢰가 종료되었습니다. 의뢰에서 내용을 확인해 주세요.',
 'message':'참여 중인 의뢰에 새 메시지가 도착했습니다. 대화에서 확인해 주세요.',
 'reminder':'진행 중인 의뢰에 응답을 기다리고 있습니다. 의뢰 내용을 확인해 주세요.',
 'paused':'참여 중인 의뢰가 응답 대기로 보류되었습니다. 의뢰에서 상태를 확인해 주세요.',
 'agreement':'상대방이 계약 진행 확인을 변경했습니다. 실제 합의 내용과 일치하는지 확인해 주세요.',
}

def migrate(c):
    c.executescript('''
    CREATE TABLE IF NOT EXISTS phone_contacts(user_id TEXT PRIMARY KEY REFERENCES users(id),phone TEXT UNIQUE NOT NULL,enabled INTEGER NOT NULL DEFAULT 0,mode TEXT NOT NULL,verified REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS phone_codes(user_id TEXT PRIMARY KEY REFERENCES users(id),phone TEXT NOT NULL,digest TEXT NOT NULL,expires REAL NOT NULL,attempts INTEGER NOT NULL,mode TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS kakao_outbox(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),event TEXT NOT NULL,phone TEXT NOT NULL,status TEXT NOT NULL,provider_id TEXT,code TEXT,due REAL NOT NULL,created REAL NOT NULL,updated REAL NOT NULL);
    CREATE INDEX IF NOT EXISTS kakao_due ON kakao_outbox(status,due);
    ''')

def configured():return bool(os.getenv('SOLAPI_API_KEY') and os.getenv('SOLAPI_API_SECRET') and os.getenv('SOLAPI_KAKAO_PFID'))
def live(s):return s.PRODUCTION and os.getenv('ALIMTALK_LIVE','false').lower()=='true'
def template(event):return os.getenv('SOLAPI_TEMPLATE_'+event.upper(),'')

def provider_request(method,path,**kwargs):
    stamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
    salt=secrets.token_hex(16)
    sig=hmac.new(os.environ['SOLAPI_API_SECRET'].encode(),(stamp+salt).encode(),hashlib.sha256).hexdigest()
    auth=f"HMAC-SHA256 apiKey={os.environ['SOLAPI_API_KEY']}, date={stamp}, salt={salt}, signature={sig}"
    with httpx.Client(timeout=15,follow_redirects=False) as client:
        response=client.request(method,'https://api.solapi.com'+path,headers={'Authorization':auth},**kwargs)
        response.raise_for_status()
        return response.json()

def send_message(message,key):
    result=provider_request('POST','/messages/v4/send-many/detail',json={'messages':[{**message,'customFields':{'wakeagainNotice':key}}],'allowDuplicates':False})
    rows=result.get('messageList') or []
    if isinstance(rows,dict):rows=list(rows.values())
    if rows and rows[0].get('messageId'):return str(rows[0]['messageId']),str(rows[0].get('statusCode',''))
    errors=result.get('failedMessageList') or []
    if errors:return '',str(errors[0].get('statusCode','rejected'))
    return '', 'unknown'

def queue(s,c,user_id,event,key):
    if event not in EVENTS:return
    contact=c.execute('SELECT * FROM phone_contacts WHERE user_id=? AND enabled=1',(user_id,)).fetchone()
    if not contact:return
    now=time.time()
    # The message route only queues the first incoming message per conversation.
    pref=c.execute('SELECT data FROM notify_preferences WHERE user_id=?',(user_id,)).fetchone()
    due=s.features.notification_due(json.loads(pref['data']) if pref else s.features.NotifyPrefs().model_dump(),now)
    status='pending' if live(s) and contact['mode']=='live' else 'preview'
    c.execute('INSERT OR IGNORE INTO kakao_outbox VALUES(?,?,?,?,?,NULL,NULL,?,?,?)',(key,user_id,event,contact['phone'],status,due,now,now))

def deliver(s):
    if not live(s) or not configured():return
    now=time.time()
    with s.db() as c:
        # An interrupted POST may have reached SOLAPI. Do not send it twice.
        c.execute("UPDATE kakao_outbox SET status='unknown',code='interrupted' WHERE status='sending' AND updated<?",(now-300,))
        c.execute("UPDATE kakao_outbox SET status='expired',code='stale' WHERE status='pending' AND created<?",(now-86400,))
    for _ in range(20):
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute("SELECT * FROM kakao_outbox WHERE status='pending' AND due<=? ORDER BY created LIMIT 1",(now,)).fetchone()
            if not row:break
            row=dict(row)
            contact=c.execute('SELECT * FROM phone_contacts WHERE user_id=?',(row['user_id'],)).fetchone()
            if not contact or not contact['enabled'] or contact['mode']!='live' or contact['phone']!=row['phone']:
                c.execute("UPDATE kakao_outbox SET status='cancelled' WHERE id=?",(row['id'],));continue
            pref=c.execute('SELECT data FROM notify_preferences WHERE user_id=?',(row['user_id'],)).fetchone()
            due=s.features.notification_due(json.loads(pref['data']) if pref else s.features.NotifyPrefs().model_dump(),now)
            if due>now:
                c.execute('UPDATE kakao_outbox SET due=? WHERE id=?',(due,row['id']));continue
            if not template(row['event']):
                c.execute("UPDATE kakao_outbox SET due=?,code='template_missing' WHERE id=?",(now+600,row['id']));continue
            count=c.execute("SELECT count(*) FROM kakao_outbox WHERE updated>? AND status IN ('sending','accepted','delivered','failed','unknown')",(now-86400,)).fetchone()[0]
            if count>=int(os.getenv('ALIMTALK_DAILY_LIMIT','100')):break
            c.execute("UPDATE kakao_outbox SET status='sending',updated=? WHERE id=?",(now,row['id']))
        message={'to':row['phone'],'type':'ATA','kakaoOptions':{'pfId':os.environ['SOLAPI_KAKAO_PFID'],'templateId':template(row['event']),'disableSms':True}}
        try:
            message_id,code=send_message(message,row['id'])
            status='accepted' if message_id else ('unknown' if code=='unknown' else 'failed')
        except (httpx.HTTPError,ValueError,TypeError,KeyError):message_id,code,status='','transport_unknown','unknown'
        with s.db() as c:c.execute('UPDATE kakao_outbox SET status=?,provider_id=?,code=?,updated=?,due=? WHERE id=?',(status,message_id,code,time.time(),time.time()+60,row['id']))
    # Poll authenticated provider results; a successful API POST is not delivery.
    with s.db() as c:rows=[dict(r) for r in c.execute("SELECT * FROM kakao_outbox WHERE status='accepted' AND due<=? LIMIT 20",(now,))]
    for row in rows:
        try:
            result=provider_request('GET','/messages/v4/list',params={'messageIds':json.dumps([row['provider_id']])})
            item=(result.get('messageList') or {}).get(row['provider_id'],{})
            code=str(item.get('statusCode',''))
            status='delivered' if code=='4000' else ('failed' if code.startswith('3') or (code.startswith('4') and code!='4000') else 'accepted')
            if status=='accepted' and now-row['created']>172800:status='unknown'
        except (httpx.HTTPError,ValueError,TypeError,AttributeError):status,code='accepted','lookup_pending'
        with s.db() as c:c.execute('UPDATE kakao_outbox SET status=?,code=?,due=? WHERE id=?',(status,code,now+300,row['id']))

class Phone(BaseModel):
    phone:str=Field(pattern=r'^010[0-9]{8}$')
    consent:bool=False
class PhoneVerify(BaseModel):
    code:str=Field(pattern=r'^[0-9]{6}$')
class Enabled(BaseModel):
    enabled:bool

def install(s):
    @s.app.get('/api/admin/alimtalk')
    def operations(user=Depends(s.current)):
        allowed={e.strip().lower() for e in os.getenv('ADMIN_EMAILS','').split(',') if e.strip()}
        if not s.social_auth.real_email(user['email']) or user['email'].lower() not in allowed:s.fail('운영자 권한이 필요합니다.',403)
        with s.db() as c:
            counts=[dict(r) for r in c.execute('SELECT status,count(*) AS n FROM kakao_outbox GROUP BY status')]
            issues=[dict(r) for r in c.execute("SELECT id,event,status,provider_id,code,created FROM kakao_outbox WHERE status IN ('unknown','failed','pending','expired') ORDER BY created DESC LIMIT 100")]
        return {'live':live(s),'configured':configured(),'missing_templates':[e for e in EVENTS if not template(e)],'counts':counts,'issues':issues}

    @s.app.get('/api/alimtalk')
    def settings(user=Depends(s.current)):
        with s.db() as c:
            contact=c.execute('SELECT * FROM phone_contacts WHERE user_id=?',(user['id'],)).fetchone()
            out=[dict(r) for r in c.execute('SELECT event,status,code,created FROM kakao_outbox WHERE user_id=? ORDER BY created DESC LIMIT 20',(user['id'],))]
        return {'phone':contact['phone'][:3]+'-****-'+contact['phone'][-4:] if contact else None,'enabled':bool(contact and contact['enabled']),'verified_live':bool(contact and contact['mode']=='live'),'live':live(s),'ready':configured() and all(template(e) for e in EVENTS),'events':EVENTS,'outbox':out,'development':not s.PRODUCTION}

    @s.app.post('/api/alimtalk/phone/code')
    def phone_code(body:Phone,request:Request,user=Depends(s.current)):
        if not body.consent:s.fail('휴대전화번호 수집·이용에 동의해 주세요.')
        s.limit('phone-user:'+user['id'],3,600);s.limit('phone-ip:'+request.client.host,10,3600);s.limit('phone-dest:'+s.digest(body.phone),3,3600)
        s.limit('phone-global',int(os.getenv('SMS_DAILY_LIMIT','100')),86400)
        code=f'{secrets.randbelow(1000000):06}'
        mode='live' if s.PRODUCTION else 'development'
        with s.db() as c:c.execute('DELETE FROM phone_codes WHERE user_id=?',(user['id'],))
        if s.PRODUCTION:
            if not live(s) or not os.getenv('SOLAPI_SMS_FROM') or not configured():s.fail('휴대전화 인증을 준비 중입니다.',503)
            try:
                mid,status=send_message({'to':body.phone,'from':os.environ['SOLAPI_SMS_FROM'],'type':'SMS','text':'[웨이크어게인] 인증번호 '+code+' (5분 유효)'},'verify-'+s.uid())
                if not mid:s.fail('인증 문자를 보내지 못했습니다. 잠시 후 다시 시도해 주세요.',503)
            except (httpx.HTTPError,ValueError,TypeError,KeyError):s.fail('문자 발송 결과를 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.',503)
        with s.db() as c:c.execute('INSERT OR REPLACE INTO phone_codes VALUES(?,?,?,?,0,?)',(user['id'],body.phone,s.digest(user['id']+body.phone+code),time.time()+300,mode))
        return {'sent':s.PRODUCTION,**({'development_code':code} if not s.PRODUCTION else {})}

    @s.app.post('/api/alimtalk/phone/verify')
    def verify(body:PhoneVerify,user=Depends(s.current)):
        valid=False;collision=False
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT * FROM phone_codes WHERE user_id=?',(user['id'],)).fetchone()
            if row and row['expires']>time.time() and row['attempts']<5 and row['mode']==('live' if s.PRODUCTION else 'development'):
                valid=hmac.compare_digest(row['digest'],s.digest(user['id']+row['phone']+body.code))
                if not valid:c.execute('UPDATE phone_codes SET attempts=attempts+1 WHERE user_id=?',(user['id'],))
            if valid:
                c.execute('DELETE FROM phone_codes WHERE user_id=?',(user['id'],))
                collision=bool(c.execute('SELECT 1 FROM phone_contacts WHERE phone=? AND user_id<>?',(row['phone'],user['id'])).fetchone())
                if not collision:
                    c.execute("UPDATE kakao_outbox SET status='cancelled' WHERE user_id=? AND status='pending'",(user['id'],))
                    c.execute('INSERT INTO phone_contacts VALUES(?,?,1,?,?) ON CONFLICT(user_id) DO UPDATE SET phone=excluded.phone,enabled=1,mode=excluded.mode,verified=excluded.verified',(user['id'],row['phone'],row['mode'],time.time()))
        if not valid:s.fail('인증번호가 틀렸거나 만료됐습니다.')
        if collision:s.fail('다른 계정에 등록된 번호입니다. 운영 문의를 이용해 주세요.')
        return {'ok':True}

    @s.app.put('/api/alimtalk')
    def toggle(body:Enabled,user=Depends(s.current)):
        with s.db() as c:
            row=c.execute('SELECT mode FROM phone_contacts WHERE user_id=?',(user['id'],)).fetchone()
            if not row:s.fail('휴대전화번호를 먼저 인증해 주세요.')
            if s.PRODUCTION and row['mode']!='live':s.fail('운영 환경에서 전화번호를 다시 인증해 주세요.')
            c.execute('UPDATE phone_contacts SET enabled=? WHERE user_id=?',(int(body.enabled),user['id']))
            if not body.enabled:c.execute("UPDATE kakao_outbox SET status='cancelled' WHERE user_id=? AND status='pending'",(user['id'],))
        return {'ok':True}

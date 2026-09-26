"""Structured briefs, comparable prices, matching preferences and operations.

Added tables preserve the existing SQLite records and their original contracts.
"""
import json
import os
import time
import math
import hashlib
import statistics
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from fastapi import Depends

STYLES = {'any':'스타일 협의','minimal':'간결한','warm':'따뜻한','bold':'강렬한','classic':'정통적인'}
SERVICES = {
    'logo': {'label':'로고 디자인', 'questions':[
        ['kind','로고 형태',{'wordmark':'글자 중심','symbol':'심볼 + 글자','illustration':'일러스트형'}],
        ['quantity','시안 수',{'1':'1개','2':'2개','3':'3개'}],
        ['source','원본 파일',{'yes':'필요','no':'이미지 파일만'}]]},
    'sign': {'label':'간판 디자인', 'questions':[
        ['kind','디자인 대상',{'indoor':'실내 간판','outdoor':'외부 간판'}],
        ['quantity','디자인 수',{'1':'1개','2':'2개','3':'3개'}],
        ['mockup','외관 적용 시안',{'yes':'필요','no':'디자인 파일만'}]]},
    'detail': {'label':'상세페이지', 'questions':[
        ['kind','작업 범위',{'design':'준비된 문구로 디자인','copy':'기획·문구 + 디자인'}],
        ['quantity','상품 수',{'1':'1개','2':'2개','3':'3개'}],
        ['length','상품당 세로 길이',{'5000':'5,000px 이하','10000':'5,001~10,000px','20000':'10,001~20,000px'}]]}
}
SERVICES.update({'print': {'label': '명함·인쇄물', 'questions': [['kind', '인쇄물 종류', {'card': '명함', 'flyer': '전단·포스터', 'booklet': '리플렛·책자'}], ['quantity', '면 수', {'1': '1면', '2': '2면', 'multi': '3면 이상'}], ['source', '편집 가능한 원본', {'yes': '필요', 'no': '결과 파일만'}]]}, 'banner': {'label': '배너·SNS', 'questions': [['kind', '이미지 용도', {'banner': '광고 배너', 'social': 'SNS 콘텐츠', 'thumbnail': '썸네일'}], ['quantity', '이미지 수', {'1': '1장', '5': '2~5장', 'multi': '6장 이상'}], ['source', '편집 가능한 원본', {'yes': '필요', 'no': '결과 파일만'}]]}, 'ppt': {'label': 'PPT 디자인', 'questions': [['kind', '자료 용도', {'proposal': '제안서·회사소개', 'pitch': '투자·사업 발표', 'lecture': '교육·발표 자료'}], ['quantity', '슬라이드 수', {'10': '10장 이하', '30': '11~30장', 'multi': '31장 이상'}], ['source', '편집 가능한 원본', {'yes': '필요', 'no': '결과 파일만'}]]}, 'package': {'label': '패키지 디자인', 'questions': [['kind', '포장 종류', {'box': '상자·단상자', 'label': '라벨·스티커', 'pouch': '파우치·봉투'}], ['quantity', '제품 수', {'1': '1종', '3': '2~3종', 'multi': '4종 이상'}], ['source', '편집 가능한 원본', {'yes': '필요', 'no': '결과 파일만'}]]}, 'ui': {'label': '웹·앱 UI', 'questions': [['kind', '화면 종류', {'web': '웹사이트 화면', 'app': '앱 화면', 'landing': '랜딩페이지 화면'}], ['quantity', '화면 수', {'1': '1개', '5': '2~5개', 'multi': '6개 이상'}], ['source', '편집 가능한 원본', {'yes': '필요', 'no': '결과 파일만'}]]}, 'illustration': {'label': '캐릭터·일러스트', 'questions': [['kind', '그림 종류', {'character': '캐릭터', 'illustration': '일러스트·삽화', 'emoticon': '이모티콘'}], ['quantity', '그림 수', {'1': '1개', '5': '2~5개', 'multi': '6개 이상'}], ['source', '편집 가능한 원본', {'yes': '필요', 'no': '결과 파일만'}]]}})
SERVICES['website'] = {'label':'웹페이지 제작', 'questions':[
    ['kind','제작 목적',{'landing':'서비스·상품 소개 페이지','company':'기업·가게 소개 사이트','portfolio':'개인·전문가 포트폴리오'}],
    ['quantity','필요한 페이지 수',{'1':'1페이지','5':'2~5페이지','multi':'6페이지 이상'}],
    ['feature','필요한 기능',{'info':'정보 안내만','contact':'문의 폼','other':'기타 기능 상담'}],
    ['hosting','도메인·호스팅',{'ready':'이미 준비됨','need':'준비가 필요함','unsure':'상담하며 결정'}]]}
COMMON = [['revisions','수정 횟수',{'1':'1회','2':'2회','3':'3회'}],
          ['materials_ready','자료 준비',{'yes':'모두 준비됨','partial':'일부 준비됨','no':'준비되지 않음'}]]

def questions(category): return SERVICES[category]['questions'] + COMMON

def checked_answers(category, answers, complete=False):
    allowed={k:options for k,_,options in questions(category)}
    if any(k not in allowed or v not in allowed[k] for k,v in answers.items()):
        raise ValueError('선택한 분야의 작업 조건을 다시 확인해 주세요.')
    if complete and set(answers)!=set(allowed):raise ValueError('작업 조건 질문에 모두 답해 주세요.')
    return answers

def signature(category, answers):
    checked_answers(category,answers,True)
    return json.dumps([category,answers],ensure_ascii=False,sort_keys=True,separators=(',',':'))

def scope_text(category,answers):
    return '\n'.join(f'{label}: {options[answers[k]]}' for k,label,options in questions(category) if k in answers)

class Model(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)

class Preferences(Model):
    available_from: date
    turnaround_days: int=Field(ge=1,le=365)
    capacity: int=Field(ge=1,le=20)
    styles: list[Literal['any','minimal','warm','bold','classic']]=Field(min_length=1,max_length=5)
    capabilities: list[str]=Field(min_length=1,max_length=20)

class Guide(Model):
    line: str=Field(min_length=3,max_length=500)
    category: Literal['logo','sign','detail','print','banner','ppt','package','ui','illustration','website']
    answers: dict[str,str]=Field(default_factory=dict)
    style: Literal['any','minimal','warm','bold','classic']='any'

class NotifyPrefs(Model):
    email: bool=False
    start: int=Field(default=9,ge=0,le=23)
    end: int=Field(default=21,ge=0,le=23)
    weekdays: list[int]=Field(default_factory=lambda:list(range(7)),min_length=1,max_length=7)

def notification_due(pref,now):
    kst=timezone(timedelta(hours=9))
    dt=datetime.fromtimestamp(now,kst)
    for minutes in range(0,8*24*60):
        candidate=dt+timedelta(minutes=minutes)
        h=candidate.hour;start,end=pref['start'],pref['end']
        inside=(start==end or (start<=h<end if start<end else h>=start or h<end))
        if candidate.weekday() in pref['weekdays'] and inside:return now if minutes==0 else candidate.timestamp()
    return now+86400*7

def migrate(c):
    c.executescript('''
    CREATE TABLE IF NOT EXISTS portfolio_images(portfolio_id TEXT REFERENCES portfolios(id),path TEXT REFERENCES uploads(path),position INTEGER,PRIMARY KEY(portfolio_id,path));
    CREATE TABLE IF NOT EXISTS expert_preferences(user_id TEXT PRIMARY KEY REFERENCES users(id),data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS notify_preferences(user_id TEXT PRIMARY KEY REFERENCES users(id),data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS email_outbox(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),body TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,due REAL NOT NULL,updated REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS quote_progress(invite_id TEXT PRIMARY KEY REFERENCES invites(id),seconds INTEGER NOT NULL DEFAULT 0,updated REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS comparable_quotes(invite_id TEXT PRIMARY KEY REFERENCES invites(id),signature TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS exposures(portfolio_id TEXT REFERENCES portfolios(id),visitor TEXT,day TEXT,created REAL,PRIMARY KEY(portfolio_id,visitor,day));
    CREATE TABLE IF NOT EXISTS operation_actions(id TEXT PRIMARY KEY,kind TEXT,item_id TEXT,admin_id TEXT REFERENCES users(id),resolution TEXT,created REAL);
    CREATE TABLE IF NOT EXISTS agreements(invite_id TEXT REFERENCES invites(id),user_id TEXT REFERENCES users(id),confirmed INTEGER NOT NULL,created REAL,PRIMARY KEY(invite_id,user_id));
    CREATE TABLE IF NOT EXISTS price_sources(id TEXT PRIMARY KEY,data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS request_submissions(request_id TEXT PRIMARY KEY REFERENCES requests(id),created REAL NOT NULL);
    INSERT OR IGNORE INTO request_submissions SELECT id,created FROM requests WHERE status IN ('open','selected','paused') OR EXISTS(SELECT 1 FROM invites WHERE request_id=requests.id);
    CREATE INDEX IF NOT EXISTS outbox_pending ON email_outbox(status,due);
    CREATE INDEX IF NOT EXISTS exposures_recent ON exposures(created,portfolio_id);
    ''')
    for row in json.loads((Path(__file__).parent/'price_sources.json').read_text(encoding='utf-8')):
        c.execute('INSERT OR IGNORE INTO price_sources VALUES(?,?)',(row['id'],json.dumps(row,ensure_ascii=False)))

def eligible(c,expert,brief,today=None):
    row=c.execute('SELECT data FROM expert_preferences WHERE user_id=?',(expert,)).fetchone()
    # Old profiles without a declared schedule must not be presented as date-verified.
    if not row:return not brief.get('answers')
    p=json.loads(row['data']);today=today or date.today()
    start=max(today,date.fromisoformat(p['available_from']))
    try:
        if start+timedelta(days=p['turnaround_days'])>date.fromisoformat(brief['deadline']):return False
    except ValueError:return False
    active=c.execute("SELECT count(*) FROM invites i JOIN requests r ON r.id=i.request_id WHERE i.expert_id=? AND r.status='open' AND i.status NOT IN ('declined','expired','not_selected')",(expert,)).fetchone()[0]
    if active>=p['capacity']:return False
    style=brief.get('style','any')
    if style!='any' and 'any' not in p['styles'] and style not in p['styles']:return False
    kind=brief.get('answers',{}).get('kind')
    return not kind or brief['category']+':'+kind in p['capabilities']

def price_stats(s,c,category,answers):
    minimum=max(30,int(os.getenv('PRICE_MIN_REQUESTS','30')))
    counts={'requests':0,'experts':0,'clients':0}
    own=None
    if answers:
        sig=signature(category,answers)
        rows=c.execute('''SELECT q.data,i.expert_id,r.user_id AS client_id,r.id AS request_id FROM comparable_quotes cq
          JOIN quotes q ON q.invite_id=cq.invite_id JOIN invites i ON i.id=cq.invite_id JOIN requests r ON r.id=i.request_id
          WHERE cq.signature=? AND q.created>? ORDER BY q.created''',(sig,time.time()-180*86400)).fetchall()
        # Equal weight for each independent request; no one customer's repeated requests dominate.
        groups={};client_requests={}
        for r in rows:
            client_requests.setdefault(r['client_id'],set()).add(r['request_id'])
            if len(client_requests[r['client_id']])>5:continue
            groups.setdefault(r['request_id'],[]).append(r)
        flat=[r for group in groups.values() for r in group]
        counts={'requests':len(groups),'experts':len({r['expert_id'] for r in flat}),'clients':len({r['client_id'] for r in flat})}
        if counts['requests']>=minimum and counts['experts']>=5 and counts['clients']>=5:
            amounts=[json.loads(r['data'])['amount'] for r in flat]
            per_request=[statistics.mean(json.loads(r['data'])['amount'] for r in group) for group in groups.values()]
            own={'min':min(amounts),'average':round(statistics.mean(per_request)),'max':max(amounts),
                 'quotes':len(amounts),**counts,'period_days':180,'basis':'동일 조건 정식 견적 · 의뢰별 평균에 동일 가중치 · 결제액 아님'}
    sources=[]
    for r in c.execute('SELECT data FROM price_sources'):
        item=json.loads(r['data'])
        if item['category']==category and item.get('enabled',True):
            item['stale']=(date.today()-date.fromisoformat(item['checked'])).days>90
            sources.append(item)
    return {'own':own,'sources':sources,'counts':counts,'threshold':minimum,'conditions':scope_text(category,answers) if answers else '',
            'mode':'own' if own else ('external' if sources else 'unavailable'),'note':'우리 사이트의 동일 조건 견적 통계입니다. 실제 계약·결제액과 다를 수 있습니다.' if own else '아직 확인된 참고 가격이 없습니다. 작업 범위를 정리해 전문가 견적을 받아보세요.' if not sources else '외부 공개 안내의 분야별 참고 가격입니다. 선택 조건의 맞춤 견적이 아니며, 플랫폼끼리 합산하지 않습니다.'}

def rank_portfolios(rows,now=None):
    # One work per expert in each pass; daily rotation within newer / established pools.
    now=now or time.time();day=int(now//86400)
    users={}
    for r in rows:users.setdefault(r['user_id'],[]).append(r)
    def order(uid):return hashlib.sha256(f'{day}:{uid}'.encode()).hexdigest()
    fresh=[];established=[]
    for uid,works in users.items():
        works.sort(key=lambda p:hashlib.sha256(f'{day}:{p["id"]}'.encode()).hexdigest())
        (fresh if min(p.get('expert_since',p['created']) for p in works)>now-30*86400 else established).append(uid)
    fresh.sort(key=order);established.sort(key=order)
    sequence=[]
    while fresh or established:
        # One of each three opportunities reserved for new profiles when supply exists.
        if fresh:sequence.append(fresh.pop(0))
        for _ in range(2):
            if established:sequence.append(established.pop(0))
        if not established and fresh:sequence.append(fresh.pop(0))
    result=[]
    while any(users.values()):
        for uid in sequence:
            if users[uid]:result.append(users[uid].pop(0))
    for rank,p in enumerate(result):p['display_rank']=rank
    return result

def queue_notice(s,c,user_id,body,notice_id):
    row=c.execute('SELECT data FROM notify_preferences WHERE user_id=?',(user_id,)).fetchone()
    if not row:return
    p=json.loads(row['data'])
    if p['email']:
        now=time.time()
        c.execute('INSERT OR IGNORE INTO email_outbox VALUES(?,?,?,\'pending\',0,?,?)',(notice_id,user_id,body,notification_due(p,now),now))

def deliver_outbox(s):
    # Development never sends a message; the queue remains visible to its owner for inspection.
    if not s.PRODUCTION or not s.email_ready():return
    for _ in range(20):
        now=time.time()
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute("UPDATE email_outbox SET status='pending' WHERE status='sending' AND updated<?",(now-300,))
            row=c.execute("SELECT o.*,u.email FROM email_outbox o JOIN users u ON u.id=o.user_id WHERE status='pending' AND due<=? ORDER BY due LIMIT 1",(now,)).fetchone()
            if not row:return
            pref=c.execute('SELECT data FROM notify_preferences WHERE user_id=?',(row['user_id'],)).fetchone()
            p=json.loads(pref['data']) if pref else {'email':False}
            if not p['email']:
                c.execute("UPDATE email_outbox SET status='cancelled' WHERE id=?",(row['id'],));continue
            due=notification_due(p,now)
            if due>now+1:
                c.execute('UPDATE email_outbox SET due=? WHERE id=?',(due,row['id']));continue
            c.execute("UPDATE email_outbox SET status='sending',attempts=attempts+1,updated=? WHERE id=?",(now,row['id']))
        try:
            s.send_email(row['email'],'WakeAgain 새 소식',row['body']+'\n\n내 작업 공간에서 확인: '+s.ORIGIN+'\n알림 수신 시간과 해지는 내 작업 공간 > 알림 설정에서 변경할 수 있습니다.',row['id'])
            status='sent'
        except Exception:status='failed' if row['attempts']>=4 else 'pending'
        with s.db() as c:
            c.execute('UPDATE email_outbox SET status=?,due=?,updated=? WHERE id=?',(status,now+min(86400,60*2**row['attempts']),time.time(),row['id']))

def install(s):
    app=s.app
    def admin(user=Depends(s.current)):
        allowed={e.strip().lower() for e in os.getenv('ADMIN_EMAILS','').split(',') if e.strip()}
        if user['email'].lower() not in allowed:s.fail('운영자 권한이 필요합니다.',403)
        return user

    @app.get('/api/catalog')
    def catalog():return {'services':{k:{**v,'questions':questions(k)} for k,v in SERVICES.items()},'styles':STYLES}

    @app.post('/api/brief-guide')
    def guide(body:Guide):
        try:checked_answers(body.category,body.answers)
        except ValueError as ex:s.fail(str(ex))
        missing=[{'key':k,'label':label,'options':options} for k,label,options in questions(body.category) if k not in body.answers]
        return {'questions':missing,'brief':{'title':body.line[:100],'category':body.category,
                'scope':'요청 작업: '+body.line+'\n선택한 작업 조건에 맞는 결과물이 필요합니다.'+('\n간판 디자인 파일 납품만 요청합니다. 제작·시공 제외.' if body.category=='sign' else ''),
                'style':body.style,'answers':body.answers},'complete':not missing}

    @app.put('/api/expert-preferences')
    def preferences(body:Preferences,user=Depends(s.current)):
        valid={cat+':'+kind for cat,v in SERVICES.items() for kind in v['questions'][0][2]}
        if not set(body.capabilities)<=valid:s.fail('지원 가능한 작업 종류를 확인해 주세요.')
        with s.db() as c:
            c.execute('INSERT OR REPLACE INTO expert_preferences VALUES(?,?)',(user['id'],body.model_dump_json()))
            for row in c.execute("SELECT * FROM requests WHERE status='open'").fetchall():
                if json.loads(row['data']).get('deadline','')>date.today().isoformat():s.match(c,row)
        return {'ok':True}

    @app.get('/api/expert-preferences')
    def get_preferences(user=Depends(s.current)):
        with s.db() as c:row=c.execute('SELECT data FROM expert_preferences WHERE user_id=?',(user['id'],)).fetchone()
        return json.loads(row['data']) if row else None

    @app.post('/api/cost/{category}/estimate')
    def estimate(category:Literal['logo','sign','detail','print','banner','ppt','package','ui','illustration','website'],body:dict):
        if set(body)!={'answers'} or not isinstance(body['answers'],dict):s.fail('작업 조건을 확인해 주세요.')
        with s.db() as c:
            try:return price_stats(s,c,category,body['answers'])
            except (ValueError,TypeError):s.fail('작업 조건 질문에 모두 답해 주세요.')

    @app.get('/api/invites/{key}/quote-draft')
    def quote_draft(key:str,user=Depends(s.current)):
        with s.db() as c:
            row=s.invite_access(c,key,user)
            if row['expert_id']!=user['id'] or row['status']!='quote_requested' or row['request_status']!='open':s.fail('정식 견적 요청을 확인해 주세요.')
            b=json.loads(row['brief']);pref=c.execute('SELECT data FROM expert_preferences WHERE user_id=?',(user['id'],)).fetchone()
            c.execute('INSERT OR IGNORE INTO quote_progress VALUES(?,0,?)',(key,time.time()))
        scope=b['scope']+'\n\n'+scope_text(b['category'],b.get('answers',{}))+'\n분위기: '+STYLES[b.get('style','any')]
        return {'title':b['title'],'scope':scope[:3000],'revisions':int(b.get('answers',{}).get('revisions',2)),
                'days':json.loads(pref['data'])['turnaround_days'] if pref else None,'amount':None,
                'exclusions':'제작·시공 비용 제외' if b['category']=='sign' else '추가 작업은 별도 협의',
                'brief':b,'comparable':bool(b.get('answers'))}

    class Heartbeat(Model):
        seconds:int=Field(ge=1,le=60)

    @app.post('/api/invites/{key}/quote-time')
    def quote_time(key:str,body:Heartbeat,user=Depends(s.current)):
        with s.db() as c:
            row=s.invite_access(c,key,user)
            if row['expert_id']!=user['id'] or row['status']!='quote_requested':s.fail('작성 중인 견적이 아닙니다.')
            now=time.time();p=c.execute('SELECT * FROM quote_progress WHERE invite_id=?',(key,)).fetchone()
            if p:
                seconds=min(body.seconds,max(0,int(now-p['updated'])))
                c.execute('UPDATE quote_progress SET seconds=min(86400,seconds+?),updated=? WHERE invite_id=?',(seconds,now,key))
        return {'ok':True}

    @app.get('/api/notification-preferences')
    def notify_preferences(user=Depends(s.current)):
        with s.db() as c:
            r=c.execute('SELECT data FROM notify_preferences WHERE user_id=?',(user['id'],)).fetchone()
            out=[dict(x) for x in c.execute('SELECT body,status,attempts,due FROM email_outbox WHERE user_id=? ORDER BY updated DESC LIMIT 10',(user['id'],))]
        return {'preferences':json.loads(r['data']) if r else NotifyPrefs().model_dump(),'outbox':out,'development':not s.PRODUCTION,'email_ready':s.email_ready() or not s.PRODUCTION}

    @app.put('/api/notification-preferences')
    def set_notify(body:NotifyPrefs,user=Depends(s.current)):
        if body.email and s.PRODUCTION and not s.email_ready():s.fail('이메일 알림은 준비 중입니다.',503)
        if body.email and not s.social_auth.real_email(user['email']):s.fail('로그인·연락처 설정에서 이메일을 먼저 인증해 주세요.')
        if any(d<0 or d>6 for d in body.weekdays):s.fail('수신 요일을 확인해 주세요.')
        with s.db() as c:
            c.execute('INSERT OR REPLACE INTO notify_preferences VALUES(?,?)',(user['id'],body.model_dump_json()))
            if not body.email:c.execute("UPDATE email_outbox SET status='cancelled' WHERE user_id=? AND status='pending'",(user['id'],))
        return {'ok':True}

    class Exposure(Model):
        visitor:str=Field(pattern=r'^[a-f0-9]{32}$')
        ids:list[str]=Field(max_length=200)

    @app.post('/api/exposures')
    def exposure(body:Exposure):
        s.limit('exposure:'+body.visitor,120,3600)
        with s.db() as c:
            for key in set(body.ids):
                if c.execute('SELECT 1 FROM portfolios WHERE id=? AND published=1',(key,)).fetchone():
                    c.execute('INSERT OR IGNORE INTO exposures VALUES(?,?,?,?)',(key,body.visitor,date.today().isoformat(),time.time()))
        return {'ok':True}

    class Agreement(Model):confirmed:bool

    @app.post('/api/invites/{key}/agreement')
    def agreement(key:str,body:Agreement,user=Depends(s.current)):
        with s.db() as c:
            row=s.invite_access(c,key,user)
            if row['status']!='selected':s.fail('선택한 전문가와의 의뢰만 확인할 수 있습니다.')
            c.execute('INSERT OR REPLACE INTO agreements VALUES(?,?,?,?)',(key,user['id'],body.confirmed,time.time()))
            s.notice(c,row['client_id'] if user['id']==row['expert_id'] else row['expert_id'],'상대방이 계약 진행 확인을 변경했습니다. 실제 계약 내용과 일치하는지 확인해 주세요.',kind='agreement')
        return {'ok':True}

    @app.get('/api/invites/{key}/agreement')
    def get_agreement(key:str,user=Depends(s.current)):
        with s.db() as c:
            s.invite_access(c,key,user)
            rows=c.execute('SELECT * FROM agreements WHERE invite_id=?',(key,)).fetchall()
        return {'mine':any(r['user_id']==user['id'] and r['confirmed'] for r in rows),
                'mutual':sum(r['confirmed'] for r in rows)==2}

    @app.get('/api/admin/status')
    def admin_status(user=Depends(s.current)):
        return {'admin':user['email'].lower() in {e.strip().lower() for e in os.getenv('ADMIN_EMAILS','').split(',') if e.strip()}}

    @app.post('/api/admin/retry-emails')
    def retry_emails(user=Depends(admin)):
        with s.db() as c:
            n=c.execute("UPDATE email_outbox SET status='pending',attempts=0,due=? WHERE status='failed'",(time.time(),)).rowcount
            c.execute('INSERT INTO operation_actions VALUES(?,?,?,?,?,?)',(s.uid(),'email','failed',user['id'],f'실패 메일 {n}건 재시도 예약',time.time()))
        return {'queued':n}

    @app.get('/api/admin')
    def operations(user=Depends(admin)):
        with s.db() as c:
            count=lambda sql:c.execute(sql).fetchone()[0]
            numbers={
                'users':count('SELECT count(*) FROM users'),
                'profiles':count('SELECT count(*) FROM profiles'),
                'publishers':count('SELECT count(DISTINCT user_id) FROM portfolios WHERE published=1'),
                'draft_clients':count('SELECT count(DISTINCT user_id) FROM requests'),
                'submitted_clients':count('SELECT count(DISTINCT r.user_id) FROM requests r JOIN request_submissions rs ON rs.request_id=r.id'),
                'requests':count('SELECT count(*) FROM request_submissions'),
                'quoted_requests':count('SELECT count(DISTINCT i.request_id) FROM invites i JOIN quotes q ON q.invite_id=i.id'),
                'selected_requests':count("SELECT count(DISTINCT request_id) FROM invites WHERE status='selected'"),
                'mutual_agreements':count('SELECT count(*) FROM (SELECT invite_id FROM agreements GROUP BY invite_id HAVING sum(confirmed)=2)'),
            }
            times=[r[0] for r in c.execute('SELECT p.seconds FROM quote_progress p JOIN quotes q ON q.invite_id=p.invite_id WHERE p.seconds>0')]
            numbers['quote_active_seconds_median']=round(statistics.median(times)) if times else None
            numbers['quote_timed_samples']=len(times)
            reports=[dict(r) for r in c.execute("SELECT r.*,p.title,p.published,u.name FROM reports r JOIN portfolios p ON p.id=r.portfolio_id JOIN users u ON u.id=r.user_id WHERE NOT EXISTS(SELECT 1 FROM operation_actions a WHERE a.kind='report' AND a.item_id=r.id) ORDER BY r.created")]
            support=[dict(r) for r in c.execute("SELECT r.*,u.name FROM support r JOIN users u ON u.id=r.user_id WHERE NOT EXISTS(SELECT 1 FROM operation_actions a WHERE a.kind='support' AND a.item_id=r.id) ORDER BY r.created")]
            exposure=[dict(r) for r in c.execute('SELECT u.name,p.user_id,count(*) AS views,count(DISTINCT e.visitor) AS visitors FROM exposures e JOIN portfolios p ON p.id=e.portfolio_id JOIN users u ON u.id=p.user_id WHERE e.created>? GROUP BY p.user_id ORDER BY views DESC',(time.time()-30*86400,))]
            emails=[dict(r) for r in c.execute('SELECT status,count(*) AS n FROM email_outbox GROUP BY status')]
            sources=[json.loads(r['data']) for r in c.execute('SELECT data FROM price_sources')]
            history=[dict(r) for r in c.execute('SELECT kind,item_id,resolution,created FROM operation_actions ORDER BY created DESC LIMIT 50')]
        return {'metrics':numbers,'reports':reports,'support':support,'exposures':exposure,'emails':emails,'sources':sources,'history':history}

    class Resolve(Model):
        kind:Literal['report','support']
        id:str=Field(max_length=30)
        resolution:str=Field(min_length=5,max_length=1000)
        hide:bool=False

    @app.post('/api/admin/resolve')
    def resolve(body:Resolve,user=Depends(admin)):
        table='reports' if body.kind=='report' else 'support'
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute(f'SELECT * FROM {table} WHERE id=?',(body.id,)).fetchone()
            if not row:s.fail('접수 내용을 찾을 수 없습니다.',404)
            if c.execute('SELECT 1 FROM operation_actions WHERE kind=? AND item_id=?',(body.kind,body.id)).fetchone():s.fail('이미 처리한 접수입니다.')
            if body.hide and body.kind=='report':
                c.execute('UPDATE portfolios SET published=0 WHERE id=?',(row['portfolio_id'],))
                owner=c.execute('SELECT user_id FROM portfolios WHERE id=?',(row['portfolio_id'],)).fetchone()
                s.notice(c,owner['user_id'],'신고 검토 후 작업물을 비공개로 변경했습니다. 운영 문의에서 이의를 남길 수 있습니다.')
            c.execute('INSERT INTO operation_actions VALUES(?,?,?,?,?,?)',(s.uid(),body.kind,body.id,user['id'],body.resolution,time.time()))
            s.notice(c,row['user_id'],'운영 문의 처리 결과: '+body.resolution)
        return {'ok':True}

    class Source(Model):
        id:str=Field(pattern=r'^[a-z0-9-]{1,40}$')
        category:Literal['logo','sign','detail','print','banner','ppt','package','ui','illustration','website']
        platform:str=Field(min_length=2,max_length=30)
        url:str=Field(pattern=r'^https://(?:soomgo\.com|kmong\.com)/prices/[^\s]+$',max_length=500)
        checked:date
        min:int=Field(ge=0,le=100000000)
        average:int=Field(ge=0,le=100000000)
        max:int=Field(ge=0,le=100000000)
        max_open:bool=False
        note:str=Field(min_length=10,max_length=1000)
        enabled:bool=True

    @app.put('/api/admin/price-source')
    def source(body:Source,user=Depends(admin)):
        if not body.min<=body.average<=body.max or body.checked>date.today():s.fail('가격 순서와 확인일을 확인해 주세요.')
        with s.db() as c:
            c.execute('INSERT OR REPLACE INTO price_sources VALUES(?,?)',(body.id,body.model_dump_json()))
            c.execute('INSERT INTO operation_actions VALUES(?,?,?,?,?,?)',(s.uid(),'price',body.id,user['id'],'가격 근거 갱신',time.time()))
        return {'ok':True}

"""WakeAgain outsourcing MVP. Separate database from the retired project market."""
from __future__ import annotations
import hashlib
import asyncio
import contextlib
import hmac
import io
import json
import os
import re
import secrets
import smtplib
import sqlite3
import time
import warnings
import urllib.request
import ssl
from contextlib import contextmanager, asynccontextmanager
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from PIL import Image, ImageOps
from portfolio_import import import_page, ImportFailure
import service_features as features
import social_auth
import alimtalk
import collaboration

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('MATCH_DATA_DIR', ROOT / 'data'))
DATA.mkdir(parents=True, exist_ok=True)
UPLOADS = DATA / 'uploads'
UPLOADS.mkdir(exist_ok=True)
DB = DATA / 'matching.sqlite3'
PRODUCTION = os.getenv('APP_ENV') == 'production'
ORIGIN = os.getenv('APP_ORIGIN', 'http://127.0.0.1:8766').rstrip('/')
def email_ready():
    return bool((os.getenv('RESEND_API_KEY') and (os.getenv('RESEND_FROM') or os.getenv('SMTP_FROM'))) or (os.getenv('SMTP_HOST') and os.getenv('SMTP_FROM')))

def email_login_enabled():
    return not PRODUCTION or os.getenv('AUTH_EMAIL_ENABLED', 'true').lower() == 'true'

ALLOWED_ORIGINS=set(os.getenv('ALLOWED_ORIGINS',ORIGIN).split(','))
BATCH = max(1, min(5, int(os.getenv('MATCH_BATCH', '3'))))
REMIND_DAYS = max(1,int(os.getenv('REMIND_DAYS','3')))
PAUSE_DAYS = max(REMIND_DAYS+1,int(os.getenv('PAUSE_DAYS','7')))
CATS = Literal['logo', 'sign', 'detail', 'print', 'banner', 'ppt', 'package', 'ui', 'illustration', 'website']
Image.MAX_IMAGE_PIXELS = 20000000

@contextmanager
def db():
    c = sqlite3.connect(DB, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()

def init_db():
    with db() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS codes(email TEXT PRIMARY KEY,digest TEXT NOT NULL,expires REAL NOT NULL,attempts INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS throttle(key TEXT PRIMARY KEY,n INTEGER NOT NULL,until REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS profiles(user_id TEXT PRIMARY KEY REFERENCES users(id),category TEXT NOT NULL,bio TEXT NOT NULL,accepting INTEGER NOT NULL,last_invited REAL NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS uploads(path TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS portfolios(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,category TEXT NOT NULL,image TEXT NOT NULL,description TEXT NOT NULL,scope TEXT NOT NULL,price INTEGER NOT NULL,published INTEGER NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),data TEXT NOT NULL,status TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS invites(id TEXT PRIMARY KEY,request_id TEXT NOT NULL REFERENCES requests(id),expert_id TEXT NOT NULL REFERENCES users(id),status TEXT NOT NULL,created REAL NOT NULL,UNIQUE(request_id,expert_id));
        CREATE TABLE IF NOT EXISTS quotes(id TEXT PRIMARY KEY,invite_id TEXT UNIQUE NOT NULL REFERENCES invites(id),data TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS templates(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),data TEXT NOT NULL,updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,invite_id TEXT NOT NULL REFERENCES invites(id),user_id TEXT NOT NULL REFERENCES users(id),body TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS notices(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),body TEXT NOT NULL,read INTEGER NOT NULL DEFAULT 0,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY,portfolio_id TEXT NOT NULL REFERENCES portfolios(id),user_id TEXT NOT NULL REFERENCES users(id),reason TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,user_id TEXT,event TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS reminders(request_id TEXT PRIMARY KEY REFERENCES requests(id),cycle REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS support(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),body TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS import_sources(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),source TEXT NOT NULL,image TEXT,created REAL NOT NULL);
        ''')
        features.migrate(c)
        social_auth.migrate(c)
        alimtalk.migrate(c)
        collaboration.migrate(c)

@asynccontextmanager
async def lifespan(app):
    if PRODUCTION and not ORIGIN.startswith('https://'):
        raise RuntimeError('Production requires HTTPS APP_ORIGIN')
    if PRODUCTION and email_login_enabled() and not email_ready():
        raise RuntimeError('Email login requires a configured email provider')
    if PRODUCTION and not all(social_auth.ready(p) for p in social_auth.PROVIDERS):
        raise RuntimeError('Production requires both Google and Kakao login credentials')
    if alimtalk.live(__import__(__name__)) and (not alimtalk.configured() or not os.getenv('SOLAPI_SMS_FROM') or not all(alimtalk.template(e) for e in alimtalk.EVENTS)):
        raise RuntimeError('Live Alimtalk requires SOLAPI credentials, verified SMS sender, channel and all approved template IDs')
    init_db()
    task=asyncio.create_task(maintenance_loop())
    try: yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):await task

def maintain():
    now=time.time()
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        collaboration.expire(__import__(__name__),c)
        for row in c.execute("SELECT * FROM requests WHERE status='open'").fetchall():
            elapsed=now-row['updated']
            if elapsed>=PAUSE_DAYS*86400:
                c.execute("UPDATE requests SET status='paused' WHERE id=?",(row['id'],))
                notice(c,row['user_id'],'의뢰에 응답이 없어 자동 보류했습니다. 다시 진행하려면 내용을 복사해 새 의뢰를 작성해 주세요.',kind='paused')
                for i in c.execute('SELECT expert_id FROM invites WHERE request_id=?',(row['id'],)):
                    notice(c,i['expert_id'],'의뢰에 최근 활동이 없어 자동 보류됐습니다. 추가 견적 작업을 멈춰 주세요.',kind='paused')
            elif elapsed>=REMIND_DAYS*86400:
                prior=c.execute('SELECT cycle FROM reminders WHERE request_id=?',(row['id'],)).fetchone()
                if not prior or prior['cycle']!=row['updated']:
                    notice(c,row['user_id'],f'진행 중인 의뢰를 확인해 주세요. 마지막 활동 후 {PAUSE_DAYS}일 동안 응답이 없으면 의뢰가 보류됩니다.',kind='reminder')
                    c.execute('INSERT OR REPLACE INTO reminders VALUES(?,?)',(row['id'],row['updated']))
            if elapsed<PAUSE_DAYS*86400 and json.loads(row['data']).get('deadline','')>date.today().isoformat():
                matched=match(c,row)
                if matched:notice(c,row['user_id'],'조건에 맞는 전문가에게 작업 가능 여부를 추가로 요청했습니다.')

async def maintenance_loop():
    while True:
        try:
            await asyncio.to_thread(maintain)
            await asyncio.to_thread(features.deliver_outbox, __import__(__name__))
            await asyncio.to_thread(alimtalk.deliver, __import__(__name__))
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Maintenance failed; retrying next cycle')
        await asyncio.sleep(60)

class BodyLimit:
    """Bound JSON and multipart bodies, including chunked requests, before parsing."""
    def __init__(self, app):self.app=app
    async def __call__(self, scope, receive, send):
        if scope['type']!='http' or scope['method'] in ('GET','HEAD','OPTIONS') or not scope['path'].startswith('/api/'):
            return await self.app(scope,receive,send)
        maximum=9*1024*1024 if (scope['path']=='/api/uploads' or re.fullmatch(r'/api/invites/[a-f0-9]{24}/files',scope['path'])) else 65536
        parts=[];size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            chunk=message.get('body',b'');size+=len(chunk)
            if size>maximum:
                return await JSONResponse({'detail':'요청 용량이 너무 큽니다.'},status_code=413)(scope,receive,send)
            parts.append(chunk)
            if not message.get('more_body',False):break
        sent=False
        async def replay():
            nonlocal sent
            if not sent:
                sent=True
                return {'type':'http.request','body':b''.join(parts),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)

app = FastAPI(title='WakeAgain Matching', lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(BodyLimit)

@app.middleware('http')
async def security(request: Request, call_next):
    if request.url.path.startswith('/api/'):
        if not PRODUCTION and request.url.hostname not in ('localhost','127.0.0.1','testserver'):
            return JSONResponse({'detail':'개발 서버는 로컬에서만 사용할 수 있습니다.'}, status_code=403)
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin = request.headers.get('origin')
            if (origin and origin not in ALLOWED_ORIGINS) or request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail':'다른 사이트에서 보낸 요청입니다.'},status_code=403)
            if request.headers.get('x-wakeagain') != '1':
                return JSONResponse({'detail':'요청을 새로 시도해 주세요.'},status_code=403)
    result = await call_next(request)
    result.headers['X-Content-Type-Options'] = 'nosniff'
    result.headers['Referrer-Policy'] = 'no-referrer' if '/auth/oauth/' in request.url.path else 'same-origin'
    result.headers['X-Frame-Options'] = 'DENY'
    result.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data: blob:; style-src 'self' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if request.url.path.startswith('/api/'):
        result.headers['Cache-Control'] = 'no-store'
    if request.url.path=='/sw.js':result.headers['Cache-Control']='no-store'
    return result

def uid(): return secrets.token_hex(12)
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def fail(detail, code=400): raise HTTPException(code, detail)
def event(c, user_id, name): c.execute('INSERT INTO events VALUES(?,?,?,?)',(uid(),user_id,name,time.time()))
def notice(c, user_id, body, kind=None):
    key=uid()
    c.execute('INSERT INTO notices VALUES(?,?,?,0,?)',(key,user_id,body,time.time()))
    features.queue_notice(__import__(__name__),c,user_id,body,key)
    alimtalk.queue(__import__(__name__),c,user_id,kind,key)

def send_email(email,subject,body,key):
    if not social_auth.real_email(email):raise ValueError('Verified contact email required')
    message=EmailMessage()
    message['From']=os.getenv('RESEND_FROM') or os.environ['SMTP_FROM']
    message['To']=email;message['Subject']=subject
    message['Message-ID']=f'<{key}@wakeagain.com>'
    message.set_content(body)
    if os.getenv('RESEND_API_KEY'):
        payload=json.dumps({'from':message['From'],'to':[email],'subject':subject,'text':body}).encode()
        req=urllib.request.Request('https://api.resend.com/emails',data=payload,headers={'Authorization':'Bearer '+os.environ['RESEND_API_KEY'],'Content-Type':'application/json','Idempotency-Key':key,'User-Agent':'WakeAgain/1.0'},method='POST')
        with urllib.request.urlopen(req,timeout=15) as res:
            if res.status not in (200,201):raise RuntimeError('Mail unavailable')
    else:
        port=int(os.getenv('SMTP_PORT','587'))
        cls=smtplib.SMTP_SSL if port==465 else smtplib.SMTP
        with cls(os.environ['SMTP_HOST'],port,timeout=15,**({'context':ssl.create_default_context()} if port==465 else {})) as smtp:
            if port!=465:smtp.starttls(context=ssl.create_default_context())
            if os.getenv('SMTP_USER'):smtp.login(os.environ['SMTP_USER'],os.getenv('SMTP_PASSWORD') or os.environ['SMTP_PASS'])
            smtp.send_message(message)
def limit(key, maximum=6, window=600):
    blocked = False
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('DELETE FROM throttle WHERE until < ?', (time.time(),))
        c.execute('INSERT INTO throttle VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET n=n+1',(key,time.time()+window))
        blocked = c.execute('SELECT n FROM throttle WHERE key=?',(key,)).fetchone()['n'] > maximum
    if blocked: fail('요청이 많습니다. 잠시 후 다시 시도해 주세요.',429)

def current(request: Request):
    token = request.cookies.get('wa_session','')
    with db() as c:
        row = c.execute('SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.digest=? AND s.expires>?',(digest(token),time.time())).fetchone()
    if not row: fail('로그인이 필요합니다.',401)
    return dict(row)

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Login(Input):
    email: str = Field(min_length=5,max_length=254)

class Verify(Login):
    code: str = Field(pattern=r'^\d{6}$')
    name: str = Field(min_length=2,max_length=40)

@app.get('/health')
def health(): return {'ok':True,'service':'matching'}

@app.get('/api/config')
def config(): return {'development':not PRODUCTION,'payments':False,'match_batch':BATCH,'remind_days':REMIND_DAYS,'pause_days':PAUSE_DAYS}

@app.post('/api/auth/code')
def send_code(body: Login, request: Request):
    if PRODUCTION and (not email_login_enabled() or not email_ready()):
        fail('이메일 인증은 준비 중입니다. 카카오 또는 Google 로그인으로 시작해 주세요.',503)
    email = body.email.lower()
    if not social_auth.real_email(email): fail('이메일 주소를 확인해 주세요.')
    limit('ip:'+request.client.host,20)
    limit('email:'+email,3)
    code = f'{secrets.randbelow(1000000):06}'
    if PRODUCTION:
        message = EmailMessage()
        message['From'], message['To'], message['Subject'] = os.getenv('RESEND_FROM') or os.environ['SMTP_FROM'],email,'WakeAgain 로그인 인증번호'
        message.set_content(f'인증번호: {code}\n10분 안에 입력해 주세요. 본인이 요청하지 않았다면 무시해 주세요.')
        try:
            if os.getenv('RESEND_API_KEY'):
                payload=json.dumps({'from':os.getenv('RESEND_FROM') or os.environ['SMTP_FROM'],'to':[email],'subject':str(message['Subject']),'text':message.get_content()}).encode()
                req=urllib.request.Request('https://api.resend.com/emails',data=payload,headers={'Authorization':'Bearer '+os.environ['RESEND_API_KEY'],'Content-Type':'application/json','User-Agent':'WakeAgain/1.0'},method='POST')
                with urllib.request.urlopen(req,timeout=15) as res:
                    if res.status not in (200,201):raise RuntimeError('Mail unavailable')
            else:
                port=int(os.getenv('SMTP_PORT','587'))
                smtp_class=smtplib.SMTP_SSL if port==465 else smtplib.SMTP
                with smtp_class(os.environ['SMTP_HOST'],port,timeout=15,**({'context':ssl.create_default_context()} if port==465 else {})) as smtp:
                    if port!=465:smtp.starttls(context=ssl.create_default_context())
                    if os.getenv('SMTP_USER'): smtp.login(os.environ['SMTP_USER'],os.getenv('SMTP_PASSWORD') or os.environ['SMTP_PASS'])
                    smtp.send_message(message)
        except Exception:
            fail('인증 메일을 보내지 못했습니다. 잠시 후 다시 시도해 주세요.',503)
    with db() as c:
        c.execute('INSERT OR REPLACE INTO codes VALUES(?,?,?,0)',(email,digest(email+code),time.time()+600))
    return {'sent':True, **({'development_code':code} if not PRODUCTION else {})}

@app.post('/api/auth/verify')
def verify(body: Verify, response: Response):
    email, now = body.email.lower(),time.time()
    if not social_auth.real_email(email):fail('이메일 주소를 확인해 주세요.')
    valid = False
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        row = c.execute('SELECT * FROM codes WHERE email=?',(email,)).fetchone()
        if row and row['expires']>now and row['attempts']<5:
            valid = hmac.compare_digest(row['digest'],digest(email+body.code))
            if not valid: c.execute('UPDATE codes SET attempts=attempts+1 WHERE email=?',(email,))
        if valid:
            c.execute('DELETE FROM codes WHERE email=?',(email,))
            c.execute('INSERT OR IGNORE INTO users VALUES(?,?,?,?)',(uid(),email,body.name,now))
            user = dict(c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone())
            token = secrets.token_urlsafe(32)
            c.execute('DELETE FROM sessions WHERE expires<?',(now,))
            c.execute('INSERT INTO sessions VALUES(?,?,?)',(digest(token),user['id'],now+604800))
    if not valid: fail('인증번호가 틀렸거나 만료됐습니다. 다시 받아 주세요.')
    response.set_cookie('wa_session',token,max_age=604800,httponly=True,secure=PRODUCTION,samesite='lax',path='/')
    return user

@app.post('/api/auth/logout')
def logout(request: Request,response: Response):
    with db() as c: c.execute('DELETE FROM sessions WHERE digest=?',(digest(request.cookies.get('wa_session','')),))
    response.delete_cookie('wa_session',path='/')
    return {'ok':True}

@app.get('/api/me')
def me(user=Depends(current)):
    with db() as c:
        profile = c.execute('SELECT * FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
    return {**user,'email':user['email'] if social_auth.real_email(user['email']) else None,'profile':dict(profile) if profile else None}

@app.get('/api/session')
def session(request: Request):
    try: return me(current(request))
    except HTTPException as ex:
        if ex.status_code==401:return None
        raise

class Profile(Input):
    name: str = Field(min_length=2,max_length=40)
    category: CATS
    bio: str = Field(min_length=10,max_length=1000)
    accepting: bool

@app.put('/api/profile')
def profile(body: Profile,user=Depends(current)):
    with db() as c:
        c.execute('UPDATE users SET name=? WHERE id=?',(body.name,user['id']))
        c.execute('INSERT INTO profiles VALUES(?,?,?,?,0) ON CONFLICT(user_id) DO UPDATE SET category=excluded.category,bio=excluded.bio,accepting=excluded.accepting',(user['id'],body.category,body.bio,body.accepting))
    return {'ok':True}

@app.post('/api/uploads')
async def upload(file: UploadFile,user=Depends(current)):
    limit('upload:'+user['id'],30,3600)
    data = await file.read(8*1024*1024+1)
    return store_image(data,user)

def store_image(data,user):
    if len(data)>8*1024*1024: fail('이미지는 8MB 이하로 올려 주세요.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in ('JPEG','PNG','WEBP'): fail('JPG, PNG, WebP 이미지만 지원합니다.')
                photo = ImageOps.exif_transpose(source).convert('RGB')
                if min(photo.size)<100: fail('가로·세로 100px 이상의 이미지를 올려 주세요.')
                photo.thumbnail((2000,2000))
                name = uid()+'.webp'
                photo.save(UPLOADS/name,'WEBP',quality=86)
    except HTTPException: raise
    except Exception: fail('읽을 수 없는 이미지입니다.')
    path = '/uploads/'+name
    with db() as c: c.execute('INSERT INTO uploads VALUES(?,?)',(path,user['id']))
    return {'path':path}

class ImportRequest(Input):
    url: str = Field(min_length=10,max_length=2000)
    rights_confirmed: Literal[True]

@app.post('/api/portfolio-import')
def portfolio_import(body:ImportRequest,user=Depends(current)):
    limit('import:'+user['id'],10,3600)
    try: result=import_page(body.url)
    except ImportFailure as ex:fail(str(ex))
    images=[]
    for raw in result.get('images_bytes') or ([result['image_bytes']] if result['image_bytes'] else []):
        try:images.append(store_image(raw,user)['path'])
        except HTTPException:result['warnings'].append('일부 이미지 형식을 읽을 수 없습니다. 직접 올려 주세요.')
    image=images[0] if images else ''
    with db() as c:
        c.execute('INSERT INTO import_sources VALUES(?,?,?,?,?)',(uid(),user['id'],result['source'],image,time.time()))
        event(c,user['id'],'portfolio_imported')
    return {'title':result['title'],'description':result['description'],'image':image,'images':images,'warnings':result['warnings']}

class Portfolio(Input):
    title: str = Field(min_length=3,max_length=100)
    category: CATS
    image: str = Field(max_length=100)
    images: list[str] = Field(default_factory=list,max_length=8)
    description: str = Field(min_length=10,max_length=3000)
    scope: str = Field(min_length=5,max_length=1000)
    price: int = Field(default=0,ge=0,le=100000000)
    published: bool = True

@app.get('/api/portfolios')
def portfolios():
    with db() as c:
        rows = c.execute('SELECT p.*,u.name as expert_name,pr.bio,pr.accepting,(SELECT min(p2.created) FROM portfolios p2 WHERE p2.user_id=p.user_id) AS expert_since FROM portfolios p JOIN users u ON u.id=p.user_id JOIN profiles pr ON pr.user_id=u.id WHERE p.published=1 ORDER BY p.created DESC').fetchall()
        result=[portfolio_record(c,r) for r in rows]
    return features.rank_portfolios(result)[:200]

def portfolio_record(c,row):
    return {**dict(row),'images':[r['path'] for r in c.execute('SELECT path FROM portfolio_images WHERE portfolio_id=? ORDER BY position',(row['id'],))] or [row['image']]}

@app.get('/api/portfolios/{key}')
def public_portfolio(key:str):
    with db() as c:
        row=c.execute('SELECT p.*,u.name AS expert_name,pr.bio,pr.accepting FROM portfolios p JOIN users u ON u.id=p.user_id JOIN profiles pr ON pr.user_id=u.id WHERE p.id=? AND p.published=1',(key,)).fetchone()
        if not row: fail('공개된 작업을 찾을 수 없습니다.',404)
        return portfolio_record(c,row)

@app.get('/api/my/portfolios')
def my_portfolios(user=Depends(current)):
    with db() as c: return [portfolio_record(c,r) for r in c.execute('SELECT * FROM portfolios WHERE user_id=? ORDER BY created DESC',(user['id'],))]

def save_portfolio(body,user,key=None):
    with db() as c:
        images=body.images or [body.image]
        if len(images)!=len(set(images)) or images[0]!=body.image:fail('첫 이미지를 대표 이미지로 선택해 주세요.')
        if not c.execute('SELECT 1 FROM profiles WHERE user_id=?',(user['id'],)).fetchone(): fail('먼저 전문가 소개를 저장해 주세요.')
        for path in images:
            if not c.execute('SELECT 1 FROM uploads WHERE path=? AND user_id=?',(path,user['id'])).fetchone(): fail('직접 올린 이미지를 선택해 주세요.')
        if key and not c.execute('SELECT 1 FROM portfolios WHERE id=? AND user_id=?',(key,user['id'])).fetchone(): fail('작업물을 찾을 수 없습니다.',404)
        values = (body.title,body.category,body.image,body.description,body.scope,body.price,body.published)
        if key: c.execute('UPDATE portfolios SET title=?,category=?,image=?,description=?,scope=?,price=?,published=? WHERE id=?',(*values,key))
        else:
            key = uid()
            c.execute('INSERT INTO portfolios VALUES(?,?,?,?,?,?,?,?,?,?)',(key,user['id'],*values,time.time()))
        c.execute('DELETE FROM portfolio_images WHERE portfolio_id=?',(key,))
        c.executemany('INSERT INTO portfolio_images VALUES(?,?,?)',[(key,path,index) for index,path in enumerate(images)])
        event(c,user['id'],'portfolio_saved')
        if body.published:
            for pending in c.execute("SELECT * FROM requests WHERE status='open' ORDER BY created LIMIT 100").fetchall():
                if json.loads(pending['data']).get('deadline','')>date.today().isoformat():
                    n=match(c,pending)
                    if n:notice(c,pending['user_id'],'등록한 의뢰를 새로 참여한 전문가에게 전달했습니다.')
    return {'id':key}

@app.post('/api/portfolios')
def create_portfolio(body:Portfolio,user=Depends(current)): return save_portfolio(body,user)
@app.put('/api/portfolios/{key}')
def edit_portfolio(key:str,body:Portfolio,user=Depends(current)): return save_portfolio(body,user,key)

@app.delete('/api/portfolios/{key}')
def delete_portfolio(key:str,user=Depends(current)):
    with db() as c:
        if not c.execute('UPDATE portfolios SET published=0 WHERE id=? AND user_id=?',(key,user['id'])).rowcount: fail('작업물을 찾을 수 없습니다.',404)
    return {'ok':True}

@app.get('/api/cost/{category}')
def cost(category:CATS):
    with db() as c:
        rows = [dict(r) for r in c.execute('SELECT p.title,p.price,p.scope,u.name FROM portfolios p JOIN users u ON u.id=p.user_id WHERE p.published=1 AND p.category=? AND p.price>0 ORDER BY p.price LIMIT 30',(category,))]
        event(c,None,'cost_checked')
        stats=features.price_stats(__import__(__name__),c,category,{})
    return {'offers':rows,**stats}

class Brief(Input):
    title: str = Field(min_length=3,max_length=100)
    category: CATS
    scope: str = Field(default='',max_length=3000)
    materials: str = Field(default='',max_length=2000)
    budget: int = Field(default=0,ge=0,le=100000000)
    deadline: str = Field(default='',max_length=10)
    reference: str = Field(default='',max_length=200)
    target_expert: str = Field(default='',max_length=24,pattern=r'^([a-f0-9]{24})?$')
    answers: dict[str,str] = Field(default_factory=dict)
    style: Literal['any','minimal','warm','bold','classic']='any'

def validate_brief(body):
    try:features.checked_answers(body.category,body.answers,bool(body.answers))
    except ValueError as ex:fail(str(ex))

def own_request(c,key,user):
    row = c.execute('SELECT * FROM requests WHERE id=? AND user_id=?',(key,user['id'])).fetchone()
    if not row: fail('의뢰를 찾을 수 없습니다.',404)
    return row

@app.post('/api/requests')
def create_request(body:Brief,user=Depends(current)):
    validate_brief(body)
    limit('request:'+user['id'],30,3600)
    key, now = uid(),time.time()
    with db() as c:
        c.execute('INSERT INTO requests VALUES(?,?,?,?,?,?)',(key,user['id'],body.model_dump_json(),'draft',now,now))
        collaboration.bind_target(__import__(__name__),c,key,body.target_expert,user)
        event(c,user['id'],'draft_saved')
    return {'id':key}

@app.put('/api/requests/{key}')
def edit_request(key:str,body:Brief,user=Depends(current)):
    validate_brief(body)
    with db() as c:
        row=own_request(c,key,user)
        if row['status']!='draft': fail('전달한 의뢰는 변경할 수 없습니다. 종료 후 새 의뢰를 만들어 주세요.')
        c.execute('UPDATE requests SET data=?,updated=? WHERE id=?',(body.model_dump_json(),time.time(),key))
        collaboration.bind_target(__import__(__name__),c,key,body.target_expert,user)
    return {'id':key}

class Confirm(Input):
    confirmed: Literal[True]
    cost_seen: Literal[True]

def match(c,row):
    directed=collaboration.targeted_match(__import__(__name__),c,row)
    if directed is not None:return directed
    brief=json.loads(row['data']);category=brief['category']
    count=c.execute("SELECT COUNT(*) FROM invites WHERE request_id=? AND status NOT IN ('declined','expired')",(row['id'],)).fetchone()[0]
    left=BATCH-count
    if left<=0:return 0
    experts=c.execute('''SELECT pr.user_id FROM profiles pr WHERE accepting=1 AND pr.user_id<>?
      AND EXISTS(SELECT 1 FROM portfolios p WHERE p.user_id=pr.user_id AND p.published=1 AND p.category=? AND (p.price=0 OR p.price<=?))
      AND NOT EXISTS(SELECT 1 FROM invites i WHERE i.request_id=? AND i.expert_id=pr.user_id)
      ORDER BY pr.last_invited ASC,pr.user_id''',(row['user_id'],category,brief['budget'],row['id'])).fetchall()
    experts=[e for e in experts if features.eligible(c,e['user_id'],brief)][:left]
    for expert in experts:
        invite_id=uid()
        c.execute('INSERT INTO invites VALUES(?,?,?,?,?)',(invite_id,row['id'],expert['user_id'],'invited',time.time()))
        c.execute('INSERT INTO reply_deadlines VALUES(?,?)',(invite_id,time.time()+collaboration.REPLY_HOURS*3600))
        c.execute('UPDATE profiles SET last_invited=? WHERE user_id=?',(time.time(),expert['user_id']))
        notice(c,expert['user_id'],'새 의뢰가 도착했습니다. 견적 작성 전에 작업 가능 여부만 알려 주세요.',kind='new_request')
    return len(experts)

@app.post('/api/requests/{key}/submit')
def submit(key:str,body:Confirm,user=Depends(current)):
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        row=own_request(c,key,user)
        if row['status'] not in ('draft','open'): fail('진행 중인 의뢰만 전달할 수 있습니다.')
        data=json.loads(row['data'])
        if len(data['scope'])<20 or len(data['materials'])<5 or data['budget']<=0: fail('작업 범위(20자 이상), 준비 자료, 예산을 확인해 주세요.')
        try: valid=date.fromisoformat(data['deadline'])>date.today()
        except ValueError: valid=False
        if not valid: fail('내일 이후의 희망 완료일을 선택해 주세요.')
        c.execute('UPDATE requests SET status=?,updated=? WHERE id=?',('open',time.time(),key))
        c.execute('INSERT OR IGNORE INTO request_submissions VALUES(?,?)',(key,time.time()))
        matched=match(c,row)
        event(c,user['id'],'request_submitted')
    return {'matched':matched,'status':'open'}

def invite_access(c,key,user):
    row=c.execute('''SELECT i.*,r.user_id AS client_id,r.data AS brief,r.status AS request_status
        FROM invites i JOIN requests r ON r.id=i.request_id WHERE i.id=?''',(key,)).fetchone()
    if not row or user['id'] not in (row['expert_id'],row['client_id']): fail('의뢰를 찾을 수 없습니다.',404)
    return row

class Availability(Input):
    status: Literal['available','declined','needs_info']

@app.post('/api/invites/{key}/availability')
def availability(key:str,body:Availability,user=Depends(current)):
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        row=invite_access(c,key,user)
        if user['id']!=row['expert_id'] or row['request_status']!='open' or row['status'] not in ('invited','needs_info','available'): fail('현재는 응답을 변경할 수 없습니다.')
        c.execute('UPDATE invites SET status=? WHERE id=?',(body.status,key))
        if body.status!='declined':c.execute('INSERT OR REPLACE INTO reply_deadlines VALUES(?,?)',(key,time.time()+collaboration.REPLY_HOURS*3600))
        notice(c,row['client_id'],'전문가가 작업 가능 여부를 알려왔습니다.',kind='availability')
        if body.status=='declined':
            match(c,c.execute('SELECT * FROM requests WHERE id=?',(row['request_id'],)).fetchone())
    return {'ok':True}

@app.post('/api/invites/{key}/request-quote')
def request_quote(key:str,user=Depends(current)):
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        row=invite_access(c,key,user)
        if user['id']!=row['client_id'] or row['request_status']!='open' or row['status']!='available': fail('작업 가능 응답을 받은 뒤 견적을 요청해 주세요.')
        c.execute('UPDATE invites SET status=? WHERE id=?',('quote_requested',key))
        c.execute('INSERT OR REPLACE INTO reply_deadlines VALUES(?,?)',(key,time.time()+collaboration.REPLY_HOURS*3600))
        c.execute('UPDATE requests SET updated=? WHERE id=?',(time.time(),row['request_id']))
        notice(c,row['expert_id'],'고객이 정식 견적을 요청했습니다. 저장한 견적 틀을 꺼내 작성해 보세요.',kind='quote_requested')
    return {'ok':True}

class Quote(Input):
    title: str = Field(min_length=3,max_length=100)
    amount: int = Field(gt=0,le=100000000)
    days: int = Field(ge=1,le=365)
    revisions: int = Field(ge=0,le=50)
    scope: str = Field(min_length=10,max_length=3000)
    exclusions: str = Field(min_length=2,max_length=2000)
    scope_unchanged: bool = False

@app.post('/api/invites/{key}/quote')
def send_quote(key:str,body:Quote,user=Depends(current)):
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        row=invite_access(c,key,user)
        if user['id']!=row['expert_id'] or row['request_status']!='open' or row['status']!='quote_requested': fail('고객의 정식 요청 이후에 견적을 보낼 수 있습니다.')
        brief=json.loads(row['brief'])
        if body.scope_unchanged and brief.get('answers') and body.revisions!=int(brief['answers']['revisions']):fail('수정 횟수가 의뢰 조건과 다릅니다. 동일 조건 통계 포함 체크를 해제해 주세요.')
        c.execute('INSERT INTO quotes VALUES(?,?,?,?)',(uid(),key,body.model_dump_json(exclude_defaults=True),time.time()))
        if body.scope_unchanged and brief.get('answers'):
            c.execute('INSERT INTO comparable_quotes VALUES(?,?)',(key,features.signature(brief['category'],brief['answers'])))
        c.execute('UPDATE invites SET status=? WHERE id=?',('quoted',key))
        c.execute('INSERT OR REPLACE INTO reply_deadlines VALUES(?,?)',(key,time.time()+collaboration.REPLY_HOURS*3600))
        notice(c,row['client_id'],'새 견적이 도착했습니다. 범위·금액·수정 조건을 비교해 보세요.',kind='quote_received')
        event(c,user['id'],'quote_sent')
    return {'ok':True}

@app.post('/api/invites/{key}/select')
def select_quote(key:str,user=Depends(current)):
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        row=invite_access(c,key,user)
        if user['id']!=row['client_id'] or row['request_status']!='open' or row['status']!='quoted': fail('선택할 수 있는 견적이 아닙니다.')
        c.execute('UPDATE requests SET status=?,updated=? WHERE id=?',('selected',time.time(),row['request_id']))
        c.execute('UPDATE invites SET status=? WHERE request_id=? AND id<>?',('not_selected',row['request_id'],key))
        c.execute('UPDATE invites SET status=? WHERE id=?',('selected',key))
        for expert in c.execute('SELECT expert_id FROM invites WHERE request_id=?',(row['request_id'],)):
            notice(c,expert['expert_id'],'고객의 견적 선택이 끝났습니다. 의뢰에서 결과를 확인해 주세요.',kind='selection')
        event(c,user['id'],'quote_selected')
    return {'ok':True}

@app.post('/api/requests/{key}/close')
def close_request(key:str,body:collaboration.Reason|None=None,user=Depends(current)):
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        own_request(c,key,user)
        c.execute('INSERT OR REPLACE INTO request_reasons VALUES(?,?,?)',(key,body.reason if body else '의뢰인이 종료했습니다.',time.time()))
        c.execute('UPDATE requests SET status=?,updated=? WHERE id=?',('closed',time.time(),key))
        for row in c.execute('SELECT expert_id FROM invites WHERE request_id=?',(key,)):
            notice(c,row['expert_id'],'고객이 의뢰를 종료했습니다. 더 이상 견적을 작성하지 않아도 됩니다.',kind='closed')
    return {'ok':True}

class Message(Input):
    body: str = Field(min_length=1,max_length=3000)
    attachments: list[str] = Field(default_factory=list,max_length=5)
    token: str = Field(default='',max_length=80,pattern=r'^[a-zA-Z0-9-]*$')

@app.post('/api/invites/{key}/messages')
def message(key:str,body:Message,user=Depends(current)):
    limit('message:'+user['id'],60,600)
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        row=invite_access(c,key,user)
        if row['request_status'] in ('closed','paused') or row['status'] in ('declined','expired','not_selected'): fail('종료되거나 보류된 대화입니다.')
        if body.token:
            prior=c.execute('SELECT message_id FROM message_tokens WHERE user_id=? AND token=?',(user['id'],body.token)).fetchone()
            if prior:return {'ok':True,'id':prior[0]}
        collaboration.validate_files(__import__(__name__),c,body.attachments,key,user['id'])
        first_message = not c.execute('SELECT 1 FROM messages WHERE invite_id=? AND user_id=? LIMIT 1',(key,user['id'])).fetchone()
        message_id=uid()
        c.execute('INSERT INTO messages VALUES(?,?,?,?,?)',(message_id,key,user['id'],body.body,time.time()))
        for file_id in body.attachments:c.execute('INSERT INTO message_files VALUES(?,?)',(message_id,file_id))
        if body.token:c.execute('INSERT INTO message_tokens VALUES(?,?,?)',(user['id'],body.token,message_id))
        if user['id']==row['client_id']:c.execute('UPDATE requests SET updated=? WHERE id=?',(time.time(),row['request_id']))
        notice(c,row['client_id'] if user['id']==row['expert_id'] else row['expert_id'],'의뢰에 새 메시지가 도착했습니다.',kind='message' if first_message else None)
    return {'ok':True}

@app.get('/api/invites/{key}/messages')
def messages(key:str,user=Depends(current)):
    with db() as c:
        invite_access(c,key,user)
        return [{**dict(r),'attachments':collaboration.file_list(c,r['id'])} for r in c.execute('SELECT m.*,u.name FROM messages m JOIN users u ON u.id=m.user_id WHERE invite_id=? ORDER BY created',(key,))]

@app.get('/api/dashboard')
def dashboard(user=Depends(current)):
    with db() as c:
        requests=[]
        for row in c.execute('SELECT * FROM requests WHERE user_id=? ORDER BY updated DESC',(user['id'],)):
            item=dict(row);item['data']=json.loads(item['data'])
            item['invites']=[dict(i) for i in c.execute('''SELECT i.*,u.name,q.data AS quote FROM invites i JOIN users u ON u.id=i.expert_id LEFT JOIN quotes q ON q.invite_id=i.id WHERE request_id=? ORDER BY i.created''',(row['id'],))]
            for i in item['invites']: i['quote']=json.loads(i['quote']) if i['quote'] else None
            requests.append(item)
        inbox=[]
        for row in c.execute('''SELECT i.*,r.data AS brief,r.status AS request_status,u.name AS client_name,q.data AS quote FROM invites i JOIN requests r ON r.id=i.request_id JOIN users u ON u.id=r.user_id LEFT JOIN quotes q ON q.invite_id=i.id WHERE expert_id=? ORDER BY i.created DESC''',(user['id'],)):
            item=dict(row);item['brief']=json.loads(item['brief']);item['quote']=json.loads(item['quote']) if item['quote'] else None;inbox.append(item)
        notices=[dict(r) for r in c.execute('SELECT * FROM notices WHERE user_id=? ORDER BY created DESC LIMIT 50',(user['id'],))]
    return {'requests':requests,'inbox':inbox,'notices':notices}

@app.post('/api/support')
def support(body:Message,user=Depends(current)):
    limit('support:'+user['id'],5,3600)
    with db() as c:c.execute('INSERT INTO support VALUES(?,?,?,?)',(uid(),user['id'],body.body,time.time()))
    return {'ok':True}

@app.post('/api/notices/read')
def read_notices(user=Depends(current)):
    with db() as c:c.execute('UPDATE notices SET read=1 WHERE user_id=?',(user['id'],))
    return {'ok':True}

@app.get('/api/templates')
def templates(user=Depends(current)):
    with db() as c: return [{'id':r['id'],**json.loads(r['data'])} for r in c.execute('SELECT * FROM templates WHERE user_id=? ORDER BY updated DESC',(user['id'],))]

@app.post('/api/templates')
def template(body:Quote,user=Depends(current)):
    key=uid()
    with db() as c:c.execute('INSERT INTO templates VALUES(?,?,?,?)',(key,user['id'],body.model_dump_json(),time.time()))
    return {'id':key}

@app.delete('/api/templates/{key}')
def delete_template(key:str,user=Depends(current)):
    with db() as c:c.execute('DELETE FROM templates WHERE id=? AND user_id=?',(key,user['id']))
    return {'ok':True}

@app.post('/api/portfolios/{key}/report')
def report(key:str,body:Message,user=Depends(current)):
    limit('report:'+user['id'],10,3600)
    with db() as c:
        if not c.execute('SELECT 1 FROM portfolios WHERE id=?',(key,)).fetchone():fail('작업물을 찾을 수 없습니다.',404)
        c.execute('INSERT INTO reports VALUES(?,?,?,?,?)',(uid(),key,user['id'],body.body,time.time()))
    return {'ok':True}

@app.get('/uploads/{name}')
def public_upload(name:str):
    if not re.fullmatch(r'[a-f0-9]{24}\.webp',name): fail('이미지를 찾을 수 없습니다.',404)
    with db() as c:
        published=c.execute('SELECT 1 FROM portfolios p WHERE published=1 AND (image=? OR EXISTS(SELECT 1 FROM portfolio_images pi WHERE pi.portfolio_id=p.id AND pi.path=?))',('/uploads/'+name,'/uploads/'+name)).fetchone()
    if not published: fail('공개되지 않은 이미지입니다.',404)
    return FileResponse(UPLOADS/name,media_type='image/webp',headers={'Cache-Control':'no-cache'})

@app.get('/api/upload-preview/{name}')
def preview(name:str,user=Depends(current)):
    if not re.fullmatch(r'[a-f0-9]{24}\.webp',name):fail('이미지를 찾을 수 없습니다.',404)
    with db() as c:
        if not c.execute('SELECT 1 FROM uploads WHERE path=? AND user_id=?',('/uploads/'+name,user['id'])).fetchone():fail('이미지를 찾을 수 없습니다.',404)
    return FileResponse(UPLOADS/name,media_type='image/webp')

features.install(__import__(__name__))
social_auth.install(__import__(__name__))
alimtalk.install(__import__(__name__))
collaboration.install(__import__(__name__))
app.mount('/',StaticFiles(directory=ROOT/'public',html=True),name='public')

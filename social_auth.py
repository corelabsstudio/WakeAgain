"""Server-side OAuth code flow. Provider tokens never enter the browser or database."""
import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Literal

PROVIDERS = {
    'google': ('https://accounts.google.com/o/oauth2/v2/auth', 'https://oauth2.googleapis.com/token', 'https://openidconnect.googleapis.com/v1/userinfo', 'openid email profile'),
    'kakao': ('https://kauth.kakao.com/oauth/authorize', 'https://kauth.kakao.com/oauth/token', 'https://kapi.kakao.com/v2/user/me', 'profile_nickname'),
}

def real_email(value):
    return bool(value and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value) and not value.lower().endswith('.invalid'))

def configuration(provider):
    prefix = provider.upper()
    return (os.getenv(prefix+'_CLIENT_ID') or (os.getenv('KAKAO_REST_API_KEY') if provider=='kakao' else '') or '', os.getenv(prefix+'_CLIENT_SECRET', ''))

def ready(provider):
    client, secret = configuration(provider)
    return bool(client and (secret or provider=='kakao'))

def migrate(c):
    c.executescript('''
    CREATE TABLE IF NOT EXISTS social_identities(provider TEXT NOT NULL,subject TEXT NOT NULL,user_id TEXT NOT NULL REFERENCES users(id),created REAL NOT NULL,PRIMARY KEY(provider,subject),UNIQUE(user_id,provider));
    CREATE TABLE IF NOT EXISTS oauth_states(digest TEXT PRIMARY KEY,provider TEXT NOT NULL,browser TEXT NOT NULL,session TEXT NOT NULL,link_user TEXT REFERENCES users(id),verifier TEXT NOT NULL,expires REAL NOT NULL);
    ''')

class RedactCallback(logging.Filter):
    def filter(self, record):
        # Uvicorn's third access-log argument is the request path and query.
        if isinstance(record.args, tuple) and len(record.args)==5 and isinstance(record.args[2],str) and '/auth/oauth/' in record.args[2]:
            args=list(record.args);args[2]=args[2].split('?')[0];record.args=tuple(args)
        return True

logging.getLogger('uvicorn.access').addFilter(RedactCallback())

def identity(provider, code, verifier, redirect):
    client, secret=configuration(provider)
    form={'grant_type':'authorization_code','client_id':client,'code':code,'redirect_uri':redirect}
    if secret:form['client_secret']=secret
    if provider=='google':form['code_verifier']=verifier
    with httpx.Client(timeout=15, follow_redirects=False) as http:
        response=http.post(PROVIDERS[provider][1],data=form)
        response.raise_for_status()
        token=response.json().get('access_token')
        if not isinstance(token,str) or not token or len(token)>16384:raise ValueError('token')
        response=http.get(PROVIDERS[provider][2],headers={'Authorization':'Bearer '+token})
        response.raise_for_status()
        data=response.json()
    if provider=='google':
        subject=data.get('sub')
        if not isinstance(subject,str) or not subject or len(subject)>255:raise ValueError('subject')
        email=data.get('email') if data.get('email_verified') is True else None
        name=data.get('name')
    else:
        if type(data.get('id')) is not int or data['id']<=0:raise ValueError('subject')
        subject=str(data['id']);account=data.get('kakao_account') or {}
        email=account.get('email') if account.get('is_email_valid') is True and account.get('is_email_verified') is True else None
        name=(account.get('profile') or {}).get('nickname')
    email=email.strip().lower() if isinstance(email,str) else None
    if not real_email(email) or len(email)>254:email=None
    return subject,email,(str(name or '새 회원').strip() or '새 회원')[:40]

class Start(BaseModel):
    intent: Literal['login','link']='login'
    consent: bool=False

def install(s):
    app=s.app
    def callback_url(provider):
        # Retain the callback path already registered by the original WakeAgain app.
        return s.ORIGIN+'/api/v1/auth/oauth/'+provider+'/callback'

    def finish(status):
        result=RedirectResponse('/?auth='+status,status_code=303)
        result.delete_cookie('wa_oauth',path='/')
        result.headers['Referrer-Policy']='no-referrer'
        return result

    @app.get('/api/auth/providers')
    def providers(request: Request):
        token=s.digest(request.cookies.get('wa_session',''))
        with s.db() as c:
            linked=[r['provider'] for r in c.execute('SELECT i.provider FROM social_identities i JOIN sessions t ON t.user_id=i.user_id WHERE t.digest=? AND t.expires>?',(token,time.time()))]
        return {**{p:{'ready':ready(p),'linked':p in linked} for p in PROVIDERS},'email_ready':s.email_ready() or not s.PRODUCTION}

    @app.post('/api/auth/oauth/{provider}/start')
    def start(provider: str, body: Start, request: Request):
        if provider not in PROVIDERS:s.fail('지원하지 않는 로그인입니다.',404)
        if not ready(provider):s.fail('로그인 연결을 준비 중입니다. 지금은 이메일로 시작해 주세요.',503)
        if not body.consent:s.fail('계정 정보 수집·이용 동의를 확인해 주세요.')
        link=s.current(request)['id'] if body.intent=='link' else None
        s.limit('oauth:'+request.client.host,20)
        state=secrets.token_urlsafe(32);browser=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48)
        with s.db() as c:
            c.execute('DELETE FROM oauth_states WHERE expires<?',(time.time(),))
            c.execute('INSERT INTO oauth_states VALUES(?,?,?,?,?,?,?)',(s.digest(state),provider,s.digest(browser),s.digest(request.cookies.get('wa_session','')),link,verifier,time.time()+600))
        params={'client_id':configuration(provider)[0],'redirect_uri':callback_url(provider),'response_type':'code','scope':PROVIDERS[provider][3],'state':state}
        if provider=='google':
            params.update(prompt='select_account',code_challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode(),code_challenge_method='S256')
        response=s.JSONResponse({'url':PROVIDERS[provider][0]+'?'+urlencode(params)})
        response.set_cookie('wa_oauth',browser,max_age=600,httponly=True,secure=s.PRODUCTION,samesite='lax',path='/')
        return response

    @app.get('/api/v1/auth/oauth/{provider}/callback')
    def callback(provider: str, request: Request):
        state=request.query_params.get('state','')
        if provider not in PROVIDERS or not 20<=len(state)<=128:return finish('expired')
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT * FROM oauth_states WHERE digest=?',(s.digest(state),)).fetchone()
            if not row or row['expires']<time.time() or row['provider']!=provider or not hmac.compare_digest(row['browser'],s.digest(request.cookies.get('wa_oauth',''))) or not hmac.compare_digest(row['session'],s.digest(request.cookies.get('wa_session',''))):return finish('expired')
            row=dict(row)
            c.execute('DELETE FROM oauth_states WHERE digest=?',(row['digest'],))
        if request.query_params.get('error'):return finish('cancelled')
        code=request.query_params.get('code','')
        if not code or len(code)>4096 or not ready(provider):return finish('failed')
        try:subject,email,name=identity(provider,code,row['verifier'],callback_url(provider))
        except (httpx.HTTPError,ValueError,TypeError,KeyError,AttributeError):return finish('failed')
        now=time.time()
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE')
            linked=c.execute('SELECT user_id FROM social_identities WHERE provider=? AND subject=?',(provider,subject)).fetchone()
            if row['link_user']:
                session=c.execute('SELECT user_id FROM sessions WHERE digest=? AND expires>?',(row['session'],now)).fetchone()
                if not session or session['user_id']!=row['link_user']:return finish('expired')
                if linked and linked['user_id']!=row['link_user']:return finish('in_use')
                prior=c.execute('SELECT subject FROM social_identities WHERE provider=? AND user_id=?',(provider,row['link_user'])).fetchone()
                if prior and prior['subject']!=subject:return finish('in_use')
                if not linked:c.execute('INSERT INTO social_identities VALUES(?,?,?,?)',(provider,subject,row['link_user'],now))
                return finish('linked')
            if linked:user_id=linked['user_id']
            else:
                if email and c.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone():return finish('existing')
                user_id=s.uid()
                c.execute('INSERT INTO users VALUES(?,?,?,?)',(user_id,email or user_id+'@accounts.invalid',name,now))
                c.execute('INSERT INTO social_identities VALUES(?,?,?,?)',(provider,subject,user_id,now))
            token=secrets.token_urlsafe(32)
            c.execute('DELETE FROM sessions WHERE digest=? OR expires<?',(row['session'],now))
            c.execute('INSERT INTO sessions VALUES(?,?,?)',(s.digest(token),user_id,now+604800))
        result=finish('success')
        result.set_cookie('wa_session',token,max_age=604800,httponly=True,secure=s.PRODUCTION,samesite='lax',path='/')
        return result

    @app.post('/api/auth/contact-email')
    def contact_email(body:s.Verify,user=Depends(s.current)):
        # Verify ownership before adding an email to an email-less Kakao account.
        email=body.email.lower();valid=False;collision=False
        if not real_email(email):s.fail('이메일 주소를 확인해 주세요.')
        if real_email(user['email']):s.fail('이미 인증된 이메일이 등록되어 있습니다.')
        with s.db() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT * FROM codes WHERE email=?',(email,)).fetchone()
            if row and row['expires']>time.time() and row['attempts']<5:
                valid=hmac.compare_digest(row['digest'],s.digest(email+body.code))
                if not valid:c.execute('UPDATE codes SET attempts=attempts+1 WHERE email=?',(email,))
            if valid:
                c.execute('DELETE FROM codes WHERE email=?',(email,))
                collision=bool(c.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone())
                if not collision:c.execute('UPDATE users SET email=? WHERE id=?',(email,user['id']))
        if not valid:s.fail('인증번호가 틀렸거나 만료됐습니다.')
        if collision:s.fail('다른 계정에서 사용 중인 이메일입니다. 다른 이메일을 사용하거나 운영자에게 문의해 주세요.')
        return {'ok':True}

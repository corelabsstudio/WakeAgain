"""Approved-feed pipeline. No scraping, third-party API calls or credential handling."""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import math
import os
import re
import time
import uuid
import threading
from functools import wraps
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

DEFAULT = {'enabled': False, 'autoPublish': False, 'intervalSeconds': 3600, 'sources': [], 'programs': []}
MAX_AGE = 86400
_lock=threading.RLock()

def serialized(function):
    @wraps(function)
    def wrapped(*args,**kwargs):
        with _lock:return function(*args,**kwargs)
    return wrapped
PROVIDERS = [
    {'id':'naver','state':'not_connected','reason':'제휴 적격 상품·발급 링크와 데이터 재게시 허용 확인 필요. 일반 쇼핑 검색 API는 제휴 적격 근거가 아닙니다.'},
    {'id':'coupang','state':'not_connected','reason':'Partners 최종 승인 및 API 접근·데이터 사용 범위 확인 필요.'},
    {'id':'toss','state':'excluded','reason':'신규 API 신청 중단 및 가격 목록·가격 비교 사이트 승인 제외.'},
]

def source_allowed(source):
    return source.get('approved') is True and source.get('channelApproved') is True and bool(source.get('approvalReference')) and source.get('redistributionAllowed') is True and source.get('priceComparisonAllowed') is True and https(source.get('termsUrl'))

def read_json(path, fallback):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else fallback

def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, path)

def instant(value):
    try:
        parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return parsed.timestamp() if parsed.tzinfo else 0
    except (ValueError, TypeError): return 0

def iso(value): return datetime.fromtimestamp(value, timezone.utc).isoformat().replace('+00:00','Z')

def https(value):
    try:
        p=urlsplit(value)
        return bool(p.scheme=='https' and p.hostname and not p.username and not p.password and p.port in (None,443))
    except (ValueError, TypeError): return False

def money(value):
    return type(value) in (int,float) and math.isfinite(value) and value>=0

def operator_import(source, data):
    """Only a reviewed local JSON export placed inside the private imports directory."""
    directory=(data/'imports').resolve()
    path=(directory/source.get('file','')).resolve()
    if not path.is_relative_to(directory) or path.suffix!='.json': raise ValueError('import_path')
    if path.stat().st_size>5_000_000: raise ValueError('import_size')
    rows=read_json(path, [])
    if not isinstance(rows,list) or len(rows)>500: raise ValueError('import_shape')
    return rows

# Register only after a provider's official contract/API and usage scope are verified.
ADAPTERS={'operator_import':operator_import}

def validate(row, source, programs, public, now):
    reasons=[]
    def need(ok, label):
        if not ok: reasons.append(label)
    need(isinstance(row,dict), 'record_shape')
    if not isinstance(row,dict): return None,reasons
    required=['sku','option','unit','name','category','merchant','sourceUrl','sourceName','selectionReason']
    need(all(isinstance(row.get(k),str) and 0<len(row[k])<=500 for k in required),'identity_or_source')
    need(https(row.get('sourceUrl')),'source_url')
    quantity=row.get('quantity'); price=row.get('price'); shipping=row.get('shipping')
    need(money(quantity) and quantity>0 and money(price) and money(shipping),'landed_cost')
    checked=instant(row.get('infoCheckedAt'))
    ttl=source.get('maxCacheSeconds',0)
    need(type(ttl) is int and 0<ttl<=MAX_AGE,'source_cache_policy')
    expires=min(checked+min(ttl,MAX_AGE),instant(row.get('expiresAt')) or checked)
    need(0<checked<=now<expires,'stale_or_future')
    need(row.get('stock')=='available','stock')
    need(row.get('shippingVerified') is True,'shipping_verification')
    need(row.get('currency')=='KRW','currency')
    quality=row.get('quality',{})
    need(isinstance(quality,dict) and quality.get('verified') is True and https(quality.get('sourceUrl')) and bool(quality.get('returnSummary')) and bool(quality.get('riskSummary')) and bool(quality.get('checkedAt')) and checked<=instant(quality.get('checkedAt'))<=now,'quality_or_returns')
    popularity=row.get('popularity',{})
    # Review count never becomes sales count or verified bestseller evidence.
    need(isinstance(popularity,dict) and popularity.get('kind') in {'sales_count','sales_rank','official_popularity_rank'} and popularity.get('verified') is True and money(popularity.get('value')) and https(popularity.get('sourceUrl')) and bool(popularity.get('period')) and checked<=instant(popularity.get('checkedAt'))<=now,'sales_evidence')
    quotes=row.get('comparisons',[])
    valid_quotes=[]
    if isinstance(quotes,list):
        for q in quotes:
            if not isinstance(q,dict):continue
            if all(q.get(k)==row.get(k) for k in ['sku','option','unit','quantity']) and money(q.get('price')) and money(q.get('shipping')) and q.get('verified') is True and https(q.get('sourceUrl')) and checked<=instant(q.get('checkedAt'))<=now:
                valid_quotes.append(q)
    need(len({q['sourceUrl'] for q in valid_quotes if q['sourceUrl']!=row.get('sourceUrl')})>=2,'same_sku_comparisons')
    total=price+shipping if money(price) and money(shipping) else 0
    need(bool(valid_quotes) and all(total<=q['price']+q['shipping'] for q in valid_quotes),'value_comparison')
    program=next((p for p in programs if p.get('id')==row.get('programId') and p.get('approved') is True),{})
    hours=program.get('maxVerificationAgeHours',24)
    need(money(hours) and hours>0 and now-checked<=hours*3600,'affiliate_verification_age')
    if money(hours) and hours>0:expires=min(expires,checked+hours*3600)
    url=row.get('affiliateUrl',''); parsed=urlsplit(url) if https(url) else None
    tracking=False
    if parsed:
        if program.get('trackingMode')=='path' and program.get('trackingPathPattern'):
            try: tracking=bool(re.search(program['trackingPathPattern'],parsed.path))
            except re.error: pass
        else:
            keys=program.get('requiredTrackingParams',[])
            tracking=bool(keys) and all(parse_qs(parsed.query).get(k) for k in keys)
    need(bool(parsed) and parsed.hostname in program.get('allowedHosts',[]) and tracking and row.get('affiliateApproved') is True and row.get('linkVerified') is True and bool(row.get('disclosure')),'affiliate_tracking_or_approval')
    image=row.get('imagePath','')
    image_file=(public/image.lstrip('/')).resolve()
    need(image.startswith('/curation/assets/') and image_file.is_relative_to((public/'curation/assets').resolve()) and image_file.suffix.lower() in {'.png','.jpg','.jpeg','.webp'} and image_file.is_file() and row.get('imageUsageAllowed') is True and https(row.get('imagePermissionSource')),'image_permission_or_local_asset')
    if reasons:return None,reasons
    identity='|'.join(str(row[k]) for k in ['sku','option','quantity','unit'])
    ident=hashlib.sha256(identity.encode()).hexdigest()[:20]
    evidence={k:popularity[k] for k in ['kind','value','period','sourceUrl','checkedAt']}
    normalized={k:row[k] for k in required}
    normalized.update(id=ident,space=row.get('space','home'),kind='tray',price=price,shipping=shipping,quantity=quantity,totalPrice=total,unitPrice=round(total/quantity,2),priceCheckedAt=row['infoCheckedAt'],infoCheckedAt=row['infoCheckedAt'],lastVerifiedAt=row['infoCheckedAt'],expiresAt=iso(expires),stock='available',summary=row.get('summary',''),options=row['option'],coreSpec=f"{quantity:g}{row['unit']} · {row['option']}",officialSpecs=row.get('officialSpecs',''),recommendedFor=row.get('recommendedFor',''),notFor=quality['riskSummary'],imagePath=image,imageUsageAllowed=True,popularity=evidence,quality={k:quality[k] for k in ['returnSummary','riskSummary','sourceUrl','checkedAt']},comparisons=valid_quotes,affiliateApproved=True,programId=row['programId'],affiliateUrl=url,linkVerified=True,disclosure=row['disclosure'],valueBasis='배송비 포함 동일 SKU·옵션·수량 비교',sourceId=source['id'],cacheUntil=expires)
    return normalized,[]

def fresh_records(rows, now): return [r for r in rows if r.get('cacheUntil',0)>now and instant(r.get('expiresAt'))>now]

def settings(data):
    config=read_json(data/'settings.json',dict(DEFAULT))
    if not isinstance(config,dict): raise ValueError('settings_shape')
    return config

def purge(data, now):
    for name in ['catalog.json','candidates.json']:
        path=data/name
        if path.exists():
            rows=read_json(path,[]); fresh=fresh_records(rows,now)
            if fresh!=rows: atomic_json(path,fresh)

@serialized
def run(data, public, dry_run=False, now=None):
    now=time.time() if now is None else now
    config=settings(data)
    if not dry_run:purge(data,now)
    if not dry_run and config.get('enabled') is not True:
        return {'state':'disabled','autoPublish':False,'connectedSources':0}
    previous=fresh_records(read_json(data/'catalog.json',[]),now)
    candidates=[]; review=[]; outcomes=[]; failed=set(); succeeded=set(); pending=Counter()
    for source in config.get('sources',[]):
        sid=source.get('id','')
        if source.get('enabled') is not True:continue
        if not sid or not source_allowed(source) or source.get('adapter') not in ADAPTERS or type(source.get('maxCacheSeconds')) is not int or not 0<source['maxCacheSeconds']<=MAX_AGE:
            failed.add(sid);outcomes.append({'source':sid,'state':'approval_required'});continue
        try:
            rows=ADAPTERS[source['adapter']](source,data)
            rejected=0;source_candidates=[]
            for index,row in enumerate(rows):
                product,reasons=validate(row,source,config.get('programs',[]),public,now)
                if product:source_candidates.append(product)
                else:
                    rejected+=1;pending.update(reasons)
                    review.append({'source':sid,'recordIndex':index,'reasons':reasons,'checkedAt':iso(now)})
            candidates.extend(source_candidates)
            succeeded.add(sid);outcomes.append({'source':sid,'state':'ok','received':len(rows),'pending':rejected})
        except (OSError, ValueError, TypeError, KeyError):
            failed.add(sid);outcomes.append({'source':sid,'state':'failed_previous_valid_retained'})
    unique={}
    for row in candidates:
        old=unique.get(row['id'])
        if old is None or (row['totalPrice'],-instant(row['infoCheckedAt']))<(old['totalPrice'],-instant(old['infoCheckedAt'])):unique[row['id']]=row
    result=sorted(unique.values(),key=lambda r:(r['unitPrice'],r['id']))
    # Sources disabled/removed or successfully updated no longer keep an old offer.
    retained=[r for r in previous if r.get('sourceId') in failed]
    merged={r['id']:r for r in retained}
    for r in result:
        old=merged.get(r['id'])
        if old is None or r['totalPrice']<old['totalPrice']:merged[r['id']]=r
    status={'state':'ready' if succeeded else 'disconnected','autoPublish':config.get('autoPublish') is True,'lastRunAt':iso(now),'eligible':len(result),'reviewPending':sum(x.get('pending',0) for x in outcomes),'pendingReasons':dict(pending),'sources':outcomes,'connectedSources':len(succeeded),'published':len(merged) if config.get('autoPublish') is True else len(previous),'dryRun':dry_run}
    if not dry_run:
        atomic_json(data/'candidates.json',result)
        atomic_json(data/'review.json',review)
        if config.get('autoPublish') is True:atomic_json(data/'catalog.json',list(merged.values()))
        atomic_json(data/'status.json',status)
        history=read_json(data/'runs.json',[])[-99:]+[status]
        atomic_json(data/'runs.json',history)
    return status

@serialized
def public_catalog(data, public, now=None):
    now=time.time() if now is None else now
    purge(data,now)
    config=settings(data)
    rows=fresh_records(read_json(data/'catalog.json',[]),now)
    sources={s.get('id'):s for s in config.get('sources',[]) if source_allowed(s) and s.get('enabled') is True}
    verified=[]
    for row in rows:
        source=sources.get(row.get('sourceId'))
        if source:
            # Recheck program permission and image rights on every public read.
            image=(public/row.get('imagePath','').lstrip('/')).resolve()
            program=next((p for p in config.get('programs',[]) if p.get('approved') is True and p.get('id')==row.get('programId')),None)
            if program and image.is_relative_to((public/'curation/assets').resolve()) and image.is_file():
                verified.append({k:v for k,v in row.items() if k not in {'sourceId','cacheUntil'}})
    status=read_json(data/'status.json',{})
    programs=[{k:v for k,v in p.items() if k in {'id','approved','allowedHosts','trackingMode','trackingPathPattern','requiredTrackingParams','maxVerificationAgeHours'}} for p in config.get('programs',[])]
    return {'products':verified,'programs':programs,'providers':PROVIDERS,'status':{'collectionEnabled':config.get('enabled') is True,'autoPublish':config.get('autoPublish') is True,'connectedSources':len(sources),'lastRunAt':status.get('lastRunAt'),'state':status.get('state','disconnected'),'published':len(verified),'reviewPending':status.get('reviewPending',0)}}

async def scheduler(data, public):
    while True:
        try:
            config=settings(data)
            if config.get('enabled') is True:await asyncio.to_thread(run,data,public)
        except (OSError,ValueError,TypeError,KeyError):
            config={}
            atomic_json(data/'status.json',{'state':'configuration_error','autoPublish':False})
        await asyncio.sleep(max(3600,int(config.get('intervalSeconds',3600))))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--public',type=Path,default=Path(__file__).parent/'public')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    print(json.dumps(run(args.data,args.public,args.dry_run),ensure_ascii=False,indent=2))

if __name__=='__main__':main()

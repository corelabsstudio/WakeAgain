"""Public metadata import. No cookies, credentials, JS execution, or access bypass."""
import http.client
import ipaddress
import re
import socket
import ssl
import json
import time
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin, urlunsplit
from urllib.robotparser import RobotFileParser

AGENT='WakeAgainImport'

class ImportFailure(ValueError):pass

def target(url):
    try:
        p=urlsplit(url)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443):raise ValueError()
        host=p.hostname.encode('idna').decode('ascii')
        if any(x in url for x in ('\r','\n','\x00','\\')):raise ValueError()
        addresses=list(dict.fromkeys(row[4][0] for row in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)))
        if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):raise ValueError()
        return p,host,addresses[0]
    except (ValueError,UnicodeError,OSError):raise ImportFailure('공개된 HTTPS 작업 링크를 입력해 주세요. 내부 주소와 특수 포트는 사용할 수 없습니다.')

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,ip):
        super().__init__(host,timeout=8,context=ssl.create_default_context());self.ip=ip
    def connect(self):
        raw=socket.create_connection((self.ip,443),timeout=self.timeout)
        try:self.sock=self._context.wrap_socket(raw,server_hostname=self.host)
        except Exception:raw.close();raise

def fetch(url,limit,accept,redirects=3,obey=False):
    for hop in range(redirects+1):
        p,host,ip=target(url)
        conn=PinnedHTTPS(host,ip)
        try:
            path=urlunsplit(('','',p.path or '/',p.query,''))
            conn.request('GET',path,headers={'User-Agent':AGENT+'/1.0','Accept':accept,'Accept-Encoding':'identity'})
            res=conn.getresponse()
            if res.status in (301,302,303,307,308):
                location=res.getheader('Location')
                if not location or hop==redirects:raise ImportFailure('이동이 많은 링크입니다. 최종 작업 페이지 주소를 넣어 주세요.')
                url=urljoin(url,location)
                if obey:allowed(url)
                continue
            if res.status!=200:return res.status,b'',res.getheader('Content-Type',''),url
            if res.getheader('Content-Encoding','identity').lower() not in ('','identity'):raise ImportFailure('이 페이지는 자동으로 읽을 수 없습니다. 직접 등록해 주세요.')
            data=res.read(limit+1)
            if len(data)>limit:raise ImportFailure('자료가 너무 큽니다. 대표 이미지를 직접 올려 주세요.')
            return res.status,data,res.getheader('Content-Type',''),url
        except ImportFailure:raise
        except (OSError,http.client.HTTPException,ValueError,UnicodeError):raise ImportFailure('사이트에 연결하지 못했습니다. 주소를 확인하거나 직접 등록해 주세요.')
        finally:conn.close()

def allowed(url):
    p,_,_=target(url)
    robot=urlunsplit((p.scheme,p.netloc,'/robots.txt','',''))
    status,data,_,_=fetch(robot,256000,'text/plain')
    if status==404:return
    if status!=200:raise ImportFailure('원본 사이트의 가져오기 허용 여부를 확인할 수 없습니다. 직접 등록해 주세요.')
    rules=RobotFileParser();rules.parse(data.decode('utf-8','replace').splitlines())
    if not rules.can_fetch(AGENT,url):raise ImportFailure('원본 사이트가 자동 가져오기를 허용하지 않습니다. 직접 등록해 주세요.')

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.meta={};self.title=[];self.in_title=False
        self.images=[];self.article=[];self.article_depth=0;self.hidden=0;self.ld=[];self.ld_buffer=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta':
            key=(a.get('property') or a.get('name') or '').lower()
            if key and key not in self.meta:self.meta[key]=a.get('content','')
            if key in ('og:image','og:image:secure_url','twitter:image') and a.get('content'):self.images.append(a['content'])
        if tag=='title':self.in_title=True
        if tag=='article':self.article_depth+=1
        if tag in ('script','style','nav','footer'):self.hidden+=1
        if tag=='script' and a.get('type')=='application/ld+json':self.ld_buffer=[]
        if tag=='img' and self.article_depth and not self.hidden:
            src=a.get('src') or a.get('data-src')
            if src:self.images.append(src)
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if tag=='article':self.article_depth=max(0,self.article_depth-1)
        if tag=='script' and self.ld_buffer is not None:
            try:self.ld.append(json.loads(''.join(self.ld_buffer)))
            except (ValueError,RecursionError):pass
            self.ld_buffer=None
        if tag in ('script','style','nav','footer'):self.hidden=max(0,self.hidden-1)
    def handle_data(self,data):
        if self.in_title:self.title.append(data)
        if self.ld_buffer is not None:self.ld_buffer.append(data)
        if self.article_depth and not self.hidden and data.strip():self.article.append(data.strip())

def structured_work(items):
    found=[]
    def walk(node,depth=0):
        if depth>12:return
        if isinstance(node,list):
            for item in node[:100]:walk(item,depth+1)
        elif isinstance(node,dict):
            types=node.get('@type',[]);types=[types] if isinstance(types,str) else types
            if any(t in ('CreativeWork','VisualArtwork','Article','Product') for t in types):found.append(node)
            if '@graph' in node:walk(node['@graph'],depth+1)
            if 'mainEntity' in node:walk(node['mainEntity'],depth+1)
    walk(items)
    return found[0] if found else {}

def plain(text,limit):return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',text)).strip()[:limit]

def import_page(url):
    allowed(url)
    status,data,kind,final=fetch(url,1500000,'text/html',obey=True)
    if status!=200:raise ImportFailure('로그인이나 접근 제한이 있는 페이지는 가져올 수 없습니다. 직접 등록해 주세요.')
    if final!=url:allowed(final)
    if 'text/html' not in kind.lower():raise ImportFailure('이미지 주소 대신 공개된 작업 소개 페이지 주소를 입력해 주세요.')
    charset=re.search(r'charset=["\s]*([\w-]+)',kind,re.I)
    try:text=data.decode(charset.group(1) if charset else 'utf-8',errors='replace')
    except LookupError:text=data.decode('utf-8',errors='replace')
    parser=Metadata();parser.feed(text);m=parser.meta
    if 'noarchive' in m.get('robots','').lower():raise ImportFailure('원본 페이지가 저장을 제한하고 있습니다. 원본 파일로 직접 등록해 주세요.')
    title=plain(m.get('og:title') or m.get('twitter:title') or ''.join(parser.title),100)
    work=structured_work(parser.ld)
    description=plain(work.get('description') if isinstance(work.get('description'),str) else '\n'.join(parser.article) or m.get('og:description') or m.get('description') or m.get('twitter:description',''),3000)
    if not title and isinstance(work.get('name'),str):title=plain(work['name'],100)
    extra=work.get('image',[]);extra=extra if isinstance(extra,list) else [extra]
    for item in extra:
        src=item if isinstance(item,str) else item.get('contentUrl') or item.get('url') if isinstance(item,dict) else None
        if src:parser.images.append(src)
    result={'title':title,'description':description,'source':final,'image_bytes':None,'images_bytes':[],'warnings':[]}
    images=list(dict.fromkeys(urljoin(final,i) for i in parser.images))[:8]
    if images and 'noimageindex' not in m.get('robots','').lower():
        total=0;started=time.monotonic()
        for image_url in images:
            if total>=24*1024*1024 or time.monotonic()-started>45:
                result['warnings'].append('가져오기 한도에 도달했습니다. 나머지 이미지는 직접 추가해 주세요.');break
            try:
                allowed(image_url)
                status,raw,kind,end=fetch(image_url,8*1024*1024,'image/jpeg,image/png,image/webp',obey=True)
                if end!=image_url:allowed(end)
                if status!=200 or not kind.lower().startswith('image/'):raise ImportFailure('일부 이미지를 자동으로 가져오지 못했습니다.')
                total+=len(raw);result['images_bytes'].append(raw)
            except ImportFailure as ex:result['warnings'].append(str(ex))
        if result['images_bytes']:result['image_bytes']=result['images_bytes'][0]
    else:result['warnings'].append('대표 이미지가 없거나 가져오기가 제한돼 있습니다. 이미지를 직접 올려 주세요.')
    if not parser.article and not work:result['warnings'].append('본문은 원본 페이지에서 공개한 요약만 가져왔습니다. 빠진 내용을 확인해 주세요.')
    if not title and not description and not result['image_bytes']:raise ImportFailure('가져올 작업 정보를 찾지 못했습니다. 직접 등록해 주세요.')
    return result

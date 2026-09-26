'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const won=v=>Number(v).toLocaleString('ko-KR')+'원';
const dates=v=>new Date(v*1000).toLocaleString('ko-KR',{timeZone:'Asia/Seoul',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
const stateNames={draft:'나만 보는 초안',open:'전문가 연결 중',selected:'전문가 선택됨',closed:'종료',paused:'응답이 없어 보류됨',invited:'응답 기다리는 중',available:'작업 가능',declined:'일정이 맞지 않음',needs_info:'추가 정보 필요',quote_requested:'견적 요청됨',quoted:'견적 도착',not_selected:'다른 전문가 선택됨'};
let user=null, config={},realWorks=[],category='all',collection='all',query='',savedOnly=false,returnFocus=null,toastTimer;
let saved=[];try{saved=JSON.parse(localStorage.getItem('wa.saved')||'[]');if(!Array.isArray(saved))saved=[];}catch{}
const allConcepts=[...concepts,...extraConcepts].map(p=>({...p,concept:true}));
const heroOriginals=$$('.hero-piece').map(el=>({el,html:el.innerHTML,id:el.dataset.project,label:el.getAttribute('aria-label')}));
const button=(text,action,value='',kind='secondary')=>`<button type="button" class="button ${kind}" data-action="${action}" data-value="${esc(value)}">${text}</button>`;
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),4200);}
async function api(path,options={}){
 const headers={'X-WakeAgain':'1',...(options.headers||{})};
 if(options.body && !(options.body instanceof FormData)){headers['Content-Type']='application/json';options.body=JSON.stringify(options.body);}
 const r=await fetch('/api'+path,{credentials:'same-origin',...options,headers});
 let data;try{data=await r.json();}catch{throw Error('서버에 연결하지 못했습니다. 다시 시도해 주세요.');}
 if(!r.ok){if(r.status===401){user=null;updateAccount();}const failure=Error(typeof data.detail==='string'?data.detail:'입력한 내용의 길이와 형식을 확인해 주세요.');failure.status=r.status;throw failure;}
 return data;
}
const post=(path,body)=>api(path,{method:'POST',body});
function error(text){const el=$('#form-error');if(el){el.textContent=text;el.scrollIntoView({block:'nearest'});}else toast(text);}
async function run(fn,el){if(el?.disabled)return;try{if(el)el.disabled=true;await fn();}catch(e){error(e.message);}finally{if(el?.isConnected)el.disabled=false;}}
function show(title,body,eyebrow='WAKEAGAIN'){
 const opened=$('dialog[open]');if(opened)opened.close();
 returnFocus=document.activeElement;$('#app-title').textContent=title;$('#app-eyebrow').textContent=eyebrow;
 $('#app-content').innerHTML=body;$('#app-dialog').showModal();document.body.classList.add('modal-open');$('#app-dialog').scrollTop=0;
}
function close(){const d=$('dialog[open]');if(d)d.close();}
$$('dialog').forEach(d=>{d.addEventListener('close',()=>{if(!$('dialog[open]'))document.body.classList.remove('modal-open');if(returnFocus?.isConnected)returnFocus.focus();});d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});});
const err='<p class="app-error" id="form-error" role="alert"></p>';
const input=(name,label,value='',type='text',extra='')=>`<div><label for="f-${name}">${label}</label><input id="f-${name}" name="${name}" type="${type}" value="${esc(value)}" ${extra}></div>`;
const area=(name,label,value='',extra='')=>`<div class="full"><label for="f-${name}">${label}</label><textarea id="f-${name}" name="${name}" ${extra}>${esc(value)}</textarea></div>`;
const catSelect=value=>`<div><label for="f-category">작업 분야</label><select name="category" id="f-category">${Object.entries(categories).map(([k,v])=>`<option value="${k}" ${value===k?'selected':''}>${v}</option>`).join('')}</select></div>`;
function formData(form){return Object.fromEntries(new FormData(form));}
function bindForm(fn){$('#active-form').addEventListener('submit',e=>{e.preventDefault();run(()=>fn(formData(e.currentTarget),e.currentTarget,e.submitter),e.submitter);});}
function empty(title,text,action=''){return `<div class="service-empty"><h3>${title}</h3><p>${text}</p>${action}</div>`;}
function updateAccount(){$('#account-button').textContent=user?'내 작업 공간':'로그인';}
async function requireUser(next){if(user)return next();return login(next);}
function login(next=()=>dashboard()){
 show('이메일로 시작하세요',`<div class="login-panel"><p>비밀번호 없이 인증번호로 로그인합니다.<br>처음이라면 계정이 함께 만들어집니다.</p><form id="active-form">${input('email','이메일','','email','required autocomplete="email" maxlength="254"')}${input('name','표시 이름','','text','required minlength="2" maxlength="40" autocomplete="nickname"')}<p class="subtle">이메일은 인증과 서비스 이용에, 이름은 작업과 상담 화면에 사용됩니다.</p><label class="check"><input type="checkbox" required>위 계정 정보의 수집·이용에 동의합니다. 탈퇴 요청 시 삭제하며, 공개 작업에는 표시 이름만 노출됩니다.</label>${err}<div class="app-actions"><button class="button primary">인증번호 받기</button></div></form></div>`,'WELCOME');
 bindForm(async data=>{
   const result=await post('/auth/code',{email:data.email});
   show('인증번호를 입력해 주세요',`<div class="login-panel"><p>${esc(data.email)}로 보낸 6자리 번호를 입력해 주세요.</p>${result.development_code?`<div class="dev-code">로컬 개발 모드 · 메일은 발송하지 않았습니다.<br>테스트 인증번호: <strong>${result.development_code}</strong></div>`:''}<form id="active-form">${input('code','인증번호','','text','required inputmode="numeric" pattern="[0-9]{6}" maxlength="6" autocomplete="one-time-code"')}${err}<div class="app-actions"><button class="button primary">로그인</button></div></form></div>`);
   bindForm(async code=>{user=await post('/auth/verify',{...data,code:code.code});user=await api('/me');updateAccount();toast('로그인했습니다.');await next();});
 });
}
function works(){return [...realWorks.map(p=>({...p,name:p.title,brand:p.expert_name,keywords:p.description,concept:false})),...allConcepts];}
function gallerySlots(){return fillPortfolioSlots(allConcepts,works().filter(p=>!p.concept));}
function renderHero(slots){
 if(!$('.hero-art'))return;
 let actual=0;
 for(const original of heroOriginals){
  const p=slots.find(s=>s.slot===original.id).work, el=original.el;
  el.classList.toggle('hero-real',!p.concept);
  if(p.concept){el.innerHTML=original.html;el.dataset.project=original.id;el.setAttribute('aria-label',original.label);}
  else{actual++;el.dataset.project=p.id;el.setAttribute('aria-label',p.name+' · '+p.expert_name+' 작업 보기');el.innerHTML=`<img src="${esc(p.image)}" alt="${esc(p.name)}"><span class="image-credit"><b>${esc(p.name)}</b><span>${esc(p.expert_name)} · ${categories[p.category]} ↗</span></span>`;}
 }
 $('.hero-art').setAttribute('aria-label','작업 미리보기');
 $('.art-note span:last-child').textContent=actual===3?'전문가 등록 작업':actual?'등록 작업 · 콘셉트 예시':'콘셉트 예시';
}
function workArt(p){return p.concept?artwork(p.id):`<div class="artwork art-photo"><img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy"></div>`;}
function render(){
 const words=query.trim().toLowerCase().split(/\s+/).filter(Boolean);
 const slots=gallerySlots();renderHero(slots);
 const source=collection==='all'&&!savedOnly?slots.map(s=>s.work):works();
 const list=source.filter(p=>(category==='all'||p.category===category)&&(!savedOnly||saved.includes(p.id))&&(collection==='all'||(collection==='concepts')===p.concept)&&words.every(w=>(p.name+' '+p.keywords+' '+categories[p.category]).toLowerCase().includes(w)));
 const card=p=>`<article class="project-card"><a class="project-image-button" href="/?work=${encodeURIComponent(p.id)}" aria-label="${esc(p.name)} 상세 보기">${workArt(p)}</a><div class="project-caption"><div><p class="card-kind">${p.concept?'콘셉트 예시':esc(p.expert_name)}</p><h3><a href="/?work=${encodeURIComponent(p.id)}">${esc(p.name)}</a></h3></div></div><div class="card-bottom">${p.concept?'<span class="concept-purpose">의뢰 방향 참고용</span>':`<div class="card-offer"><strong>${p.price?won(p.price)+'부터':'금액 협의'}</strong><span>${p.accepting?'일정 협의 가능':'새 의뢰 마감'}</span></div>`}<button class="save-button" data-save="${esc(p.id)}" aria-label="${esc(p.name)} 작업 저장" aria-pressed="${saved.includes(p.id)}">${saved.includes(p.id)?'저장됨':'저장'}</button></div></article>`;
 const grouped=category==='all'&&!query.trim()&&!savedOnly;
 const order=['logo','website','detail','ui','sign','print','banner','ppt','package','illustration'];
 $('#project-grid').classList.toggle('is-grouped',grouped);
 $('#project-grid').innerHTML=grouped?order.map(key=>{
   const items=list.filter(p=>p.category===key);if(!items.length)return '';
   return `<section class="work-category" aria-labelledby="group-${key}"><div class="category-heading"><h3 id="group-${key}">${esc(categories[key])}</h3><button type="button" data-category="${key}" aria-label="${esc(categories[key])} 전체 보기">전체 보기 <span aria-hidden="true">→</span></button></div><div class="category-grid">${items.slice(0,5).map(card).join('')}</div></section>`;
 }).join(''):list.map(card).join('');
 $('#explore-title').textContent=savedOnly?'저장한 작업':query.trim()?'검색 결과':category!=='all'?categories[category]+' 작업':'분야별 작업 둘러보기';
 $('#collection-select').value=collection;
 $('#project-grid').hidden=!list.length;$('#empty-state').hidden=!!list.length;
 const noExpertWorks=collection==='experts'&&!realWorks.length&&!query&&category==='all'&&!savedOnly;
 $('#empty-state h3').textContent=noExpertWorks?'현재 표시할 전문가 작업이 없습니다.':savedOnly?'조건에 맞는 저장한 작업이 없습니다.':'조건에 맞는 작업이 없습니다.';
 $('#empty-state p').textContent=noExpertWorks?'작업 종류에서 콘셉트 예시를 선택해 원하는 작업의 방향을 살펴보세요.':savedOnly?'저장한 작업만 보기 설정을 끄거나 다른 조건으로 찾아보세요.':'검색어나 분야를 바꾸거나 전체 작업을 확인해 보세요.';
 $('#results-line').textContent=`${query?'“'+query+'” · ':''}${list.length}개 작업${collection==='all'?' · 등록 작업 '+list.filter(p=>!p.concept).length+' / 콘셉트 '+list.filter(p=>p.concept).length:''}`;
 $('#saved-count').textContent=saved.length;$('#saved-filter').setAttribute('aria-pressed',savedOnly);
 $$('[data-filter]').forEach(b=>{b.classList.toggle('selected',b.dataset.filter===category);b.setAttribute('aria-pressed',b.dataset.filter===category);});
 $$('[data-collection]').forEach(b=>{b.classList.toggle('active',b.dataset.collection===collection);b.setAttribute('aria-pressed',b.dataset.collection===collection);});
}
async function refreshWorks(){realWorks=await api('/portfolios');render();document.dispatchEvent(new Event('works-ready'));}
function detail(id){
 const p=works().find(p=>p.id===id);if(!p)return;
 const list=p.concept?p.deliverables:[p.scope];
 $('#project-content').innerHTML=`<div class="dialog-head"><div><h1 id="project-title" tabindex="-1">${esc(p.name)}</h1><p class="project-subtitle">${categories[p.category]} · ${p.concept?'가상 브랜드의 콘셉트 작업':esc(p.expert_name)}</p></div></div><div class="project-detail-layout"><div class="project-large-art">${workArt(p)}</div><div class="project-info"><span class="small-label">작업 소개</span><p>${esc(p.description)}</p><h3>${p.concept?'이런 작업에 포함할 수 있어요':'작업 범위'}</h3><ul class="deliverables">${list.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>${!p.concept?`<p>${p.price?won(p.price)+'부터 · 아래 범위 기준':'금액은 범위 확인 후 협의'}<br><small>${p.accepting?'새 의뢰를 받고 있습니다.':'현재 새 의뢰를 쉬고 있습니다.'}</small></p>`:''}<button class="button primary" data-brief="${p.category}" data-reference="${esc(p.name)}">이런 작업 의뢰하기 ↗</button><p class="example-info">작업 범위와 예산을 확인한 뒤 적합한 전문가에게 연결합니다.</p></div></div><div class="project-footer"><span>${p.concept?'WakeAgain이 제작한 콘셉트 예시입니다. 실제 수주 작업이나 등록 전문가의 포트폴리오가 아닙니다.':'전문가가 직접 등록한 작업입니다. 거래 후기나 실적은 별도로 표시하지 않습니다.'}</span>${!p.concept?`<button data-action="report" data-value="${p.id}">작업 신고</button>`:''}</div>`;
 document.title=p.name+' — WakeAgain';
}
async function cost(cat='logo',next=null){
 const result=await api('/cost/'+cat);
 show('먼저, 비용의 기준부터',`<p>비용 확인은 전문가에게 전달되지 않습니다. 필요한 작업에 맞는 기본 범위를 살펴보세요.</p><label for="cost-category">알아볼 분야</label><select id="cost-category">${Object.entries(categories).map(([k,v])=>`<option value="${k}" ${k===cat?'selected':''}>${v}</option>`).join('')}</select><div class="request-summary">${esc(result.note)}</div>${result.offers.length?result.offers.map(o=>`<div class="cost-row"><div><b>${esc(o.title)}</b><br><small>${esc(o.name)}</small></div><strong>${won(o.price)}부터</strong><p>${esc(o.scope)}</p></div>`).join(''):empty('범위에 따라 가격이 달라집니다.','로고는 시안·수정 횟수와 원본 파일, 간판은 크기와 적용안, 상세페이지는 분량과 사진·문구 준비 여부가 기준이 됩니다. 임의의 평균 가격을 제시하지 않습니다.')}<p class="subtle">추가 시안, 촬영, 문구 작성, 제작·시공 등은 포함 여부를 꼭 확인해 주세요.</p>${err}<div class="app-actions"><button class="button secondary" data-close>비용만 확인하고 닫기</button><button class="button primary" id="continue-brief">이제 실제 의뢰 준비하기 →</button></div>`,'BEFORE YOU REQUEST');
 if(next){$('#cost-category').disabled=true;$('#continue-brief').textContent='이 조건으로 의뢰 전달하기 →';const note=document.createElement('p');note.className='subtle';note.textContent=`의뢰 진행 안내: 마지막 응답 후 ${config.remind_days||3}일에 사이트 알림, ${config.pause_days||7}일 동안 응답이 없으면 의뢰를 보류합니다.`;$('#continue-brief').parentElement.before(note);}
 $('#cost-category').addEventListener('change',e=>run(()=>cost(e.target.value,next)));
 $('#continue-brief').addEventListener('click',()=>run(()=>next?next():requireUser(()=>briefForm({category:cat}))));
}
function briefForm(data={},key=null){
 const cat=data.category||'logo';
 const hint={logo:'브랜드 이름·업종 / 새 로고 또는 수정 / 사용처 / 시안·수정 횟수 / 원본 파일',sign:'상호·문구 / 간판 크기 / 설치 장소의 특징 / 디자인 파일·외관 적용안 (제작·시공 제외)',detail:'상품 수 / 페이지 분량 / 판매 채널 / 문구 작성·보정 필요 여부 / 원본 파일'}[cat];
 show(key?'의뢰 초안 수정':'어떤 일을 맡기고 싶으세요?',`<p>저장만 하면 나만 보는 초안입니다. 다음 화면에서 내용을 확인하고 전달 여부를 결정하세요.</p><form id="active-form"><div class="form-grid">${input('title','의뢰 제목',data.title||'','text','required minlength="3" maxlength="100" placeholder="예: 새로 여는 카페의 로고 디자인"')}${catSelect(cat)}${area('scope','필요한 작업과 납품 범위',data.scope||'','maxlength="3000" placeholder="'+hint+'"')}<p class="subtle full" id="scope-hint">${hint}</p>${area('materials','준비된 자료와 참고 사항',data.materials||'','maxlength="2000" placeholder="사진, 로고, 상품 설명 등 준비된 자료와 없는 자료를 적어 주세요. 비밀번호나 민감한 개인정보는 적지 마세요."')}${input('budget','지출 가능한 예산 (원)',data.budget||'','number','min="0" max="100000000" step="1"')}${input('deadline','희망 완료일',data.deadline||'','date')}${input('reference','참고한 작업',data.reference||'','text','maxlength="200"')}</div><div class="request-summary">연락은 로그인한 이메일 계정의 의뢰 대화에서 이어갑니다. 실제 전달 전에는 작업 범위, 자료, 예산, 일정을 모두 확인합니다.</div>${err}<div class="app-actions"><button class="button primary">나만 보는 초안 저장 →</button></div></form>`,'PRIVATE BRIEF');
 $('#f-category').addEventListener('change',e=>{$('#scope-hint').textContent={logo:'새 로고·수정 여부, 사용처, 시안·수정 횟수, 원본 파일을 알려 주세요.',sign:'간판 디자인 파일만 지원합니다. 크기, 설치 장소, 문구, 기존 로고를 알려 주세요. 제작·시공은 포함하지 않습니다.',detail:'상품 수, 분량, 사진·설명 준비 여부, 문구 작성·보정 여부를 알려 주세요.'}[e.target.value];});
 bindForm(async value=>{value.budget=Number(value.budget||0);const result=await api('/requests'+(key?'/'+key:''),{method:key?'PUT':'POST',body:value});toast('초안을 서버에 저장했습니다. 전문가에게는 보이지 않습니다.');await requestDetail(result.id);});
}
let dashboardData={requests:[],inbox:[],notices:[]};
async function dashboard(tab='requests'){
 if(!user)return login(()=>dashboard(tab));
 [dashboardData,user]=await Promise.all([api('/dashboard'),api('/me')]);updateAccount();
 const unread=dashboardData.notices.filter(n=>!n.read).length;
 const tabs=[['requests','내 의뢰'],['inbox','받은 의뢰'],['portfolio','작업물'],['templates','저장한 견적서'],['profile','내 소개'],['notices','알림'+(unread?' '+unread:'')]];
 let body='';
 if(tab==='requests')body=`<div class="row-head"><p>아직 전달하지 않은 초안도 여기에서 이어 쓰세요.</p>${button('새 의뢰','new-brief','','primary')}</div>`+(dashboardData.requests.length?dashboardData.requests.map(r=>`<article class="dashboard-row"><div class="row-head"><h3>${esc(r.data.title)}</h3><span class="state-label">${stateNames[r.status]}</span></div><small>${categories[r.data.category]} · ${r.data.budget?won(r.data.budget):'예산 미정'} · ${r.data.deadline||'일정 미정'}</small><div class="row-actions"><button data-action="request" data-value="${r.id}">내용과 견적 보기 →</button></div></article>`).join(''):empty('첫 의뢰를 정리해 보세요.','필요한 작업과 예산을 정리한 다음, 실제로 진행할 준비가 됐을 때 전문가에게 전달할 수 있습니다.'));
 if(tab==='inbox')body='<p>전문가에게는 조건이 맞는 의뢰만 도착합니다. 먼저 작업 가능 여부만 알려 주세요.</p>'+(dashboardData.inbox.length?dashboardData.inbox.map(i=>`<article class="dashboard-row"><div class="row-head"><h3>${esc(i.brief.title)}</h3><span class="state-label">${i.request_status==='closed'?'종료':stateNames[i.status]}</span></div><small>${esc(i.client_name)} · ${won(i.brief.budget)} · ${esc(i.brief.deadline)}</small><div class="row-actions"><button data-action="invite" data-value="${i.id}">의뢰 확인 →</button></div></article>`).join(''):empty('지금 도착한 의뢰는 없습니다.','작업물과 소개를 등록하고 ‘새 의뢰 받기’를 켜 두세요. 공개 후기 수에 관계없이 분야와 활동 상태에 맞춰 연결합니다.'));
 if(tab==='notices')body=(dashboardData.notices.length?dashboardData.notices.map(n=>`<article class="dashboard-row"><small>${dates(n.created)}${n.read?'':' · 새 알림'}</small><p>${esc(n.body)}</p></article>`).join(''):empty('새 소식이 없습니다.','의뢰 응답과 견적이 도착하면 이곳에서 알려드립니다.'))+`<div class="app-actions">${button('모두 읽음','read-notices')}</div>`;
 if(tab==='portfolio'){
  const list=await api('/my/portfolios');body=`<div class="row-head"><p>수정한 내용은 저장 즉시 반영됩니다.</p>${button('작업물 올리기','edit-work','','primary')}</div>`+(list.length?list.map(p=>`<article class="dashboard-row"><div class="mini-work"><img src="/api/upload-preview/${p.image.split('/').pop()}" alt="${esc(p.title)}"><div><h3>${esc(p.title)}</h3><small>${categories[p.category]} · ${p.published?'공개 중':'비공개'}</small></div></div><div class="row-actions"><button data-action="edit-work" data-value="${p.id}">수정하기</button>${p.published?`<button data-action="hide-work" data-value="${p.id}">비공개로 바꾸기</button>`:''}</div></article>`).join(''):empty('잘하는 일을 보여주세요.','이미지, 짧은 설명, 본인이 맡은 범위로 첫 작업을 등록할 수 있습니다.'));
 }
 if(tab==='templates'){
  const list=await api('/templates');body=`<div class="row-head"><p>범위·납품물·수정 조건을 저장해 다시 쓰세요.</p>${button('견적서 새로 만들기','template','','primary')}</div>`+(list.length?list.map(t=>`<article class="dashboard-row"><h3>${esc(t.title)}</h3><small>${won(t.amount)} · ${t.days}일 · 수정 ${t.revisions}회</small><div class="row-actions"><button data-action="copy-template" data-value="${t.id}">복사해서 수정</button><button data-action="delete-template" data-value="${t.id}">삭제</button></div></article>`).join(''):empty('반복하는 견적, 한 번만 작성하세요.','저장한 견적서을 저장한 뒤 실제 의뢰에 맞는 금액과 조건만 수정할 수 있습니다.'));
 }
 if(tab==='profile'){
  const p=user.profile||{};body=`<p>작업물에 표시할 소개와 새 의뢰 수신 여부를 관리하세요.</p><form id="active-form"><div class="form-grid">${input('name','표시 이름',user.name,'text','required minlength="2" maxlength="40"')}${catSelect(p.category||'logo')}${area('bio','전문가 소개',p.bio||'','required minlength="10" maxlength="1000" placeholder="주로 하는 작업과 맡을 수 있는 범위를 적어 주세요."')}</div><label class="check"><input name="accepting" type="checkbox" ${p.accepting?'checked':''}>새 의뢰 받기</label>${err}<div class="app-actions"><button class="button primary">소개 저장</button>${button('로그아웃','logout')}</div></form>`;
 }
 show(tab==='profile'?'내 소개':'내 작업 공간',`<div class="app-tabs">${tabs.map(([k,v])=>`<button data-action="dashboard" data-value="${k}" class="${k===tab?'active':''}">${v}</button>`).join('')}</div>${body}<div class="row-actions"><button data-action="support">운영 문의 · 계정 삭제 요청</button></div>`,esc(user.name));
 if(tab==='profile')bindForm(async d=>{d.accepting=!!d.accepting;await api('/profile',{method:'PUT',body:d});user=await api('/me');toast('소개를 저장했습니다.');await dashboard('portfolio');});
}
async function requestDetail(key){
 dashboardData=await api('/dashboard');const r=dashboardData.requests.find(r=>r.id===key);if(!r)throw Error('의뢰를 찾을 수 없습니다.');
 const b=r.data;
 if(r.status==='paused'){show(b.title,`<p>응답이 없어 의뢰를 보류했습니다. 전문가에게 추가 작업을 요청하지 않습니다.</p><div class="request-summary">${esc(b.scope)}</div><div class="app-actions">${button('내용을 복사해 새 의뢰','copy-brief',key,'primary')}${button('내 의뢰로','dashboard','requests')}</div>`);return;}
 show(b.title,`<p><span class="state-label">${stateNames[r.status]}</span> · ${categories[b.category]}</p><div class="request-summary"><b>작업 범위</b>\n${esc(b.scope||'아직 작성하지 않았습니다.')}\n\n<b>준비 자료</b>\n${esc(b.materials||'아직 작성하지 않았습니다.')}\n\n<b>예산</b> ${b.budget?won(b.budget):'미정'} · <b>완료일</b> ${esc(b.deadline||'미정')}${b.reference?'\n참고 작업: '+esc(b.reference):''}</div>${r.status==='draft'?`<label class="check"><input id="submit-confirm" type="checkbox">이 예산과 일정으로 실제 견적을 받아보겠습니다. 의뢰 내용이 적합한 전문가에게 전달되는 데 동의합니다.</label><p class="subtle">연락 수단: 로그인한 이메일 계정의 사이트 내 대화. 작업 가능 응답을 받은 뒤 정식 견적을 요청합니다.</p><div class="app-actions">${button('초안 수정','edit-brief',key)}${button('비용 확인 후 의뢰 전달','submit-request',key,'primary')}</div>`:''}${r.status==='open'&&!r.invites.length?empty('조건에 맞는 전문가를 기다리고 있습니다.','아직 전달할 전문가가 없습니다. 등록 작업과 일정이 맞는 전문가가 생기면 아래 버튼으로 다시 연결을 확인해 주세요.',button('연결 다시 확인','rematch',key)):''}${r.status==='selected'?'<div class="information-box">전문가를 선택했습니다. 대화에서 세부 조건을 확인해 주세요. 이 선택은 결제 완료나 계약 체결을 의미하지 않습니다.</div>':''}${r.invites.length?`<h3>전문가 응답과 견적</h3><div class="quote-comparison">${r.invites.map(i=>`<article class="quote-card"><h3>${esc(i.name)}</h3><span class="state-label">${stateNames[i.status]}</span>${i.quote?quoteSummary(i.quote):'<p>작업 가능 여부를 확인하고 있습니다. 이 단계에서는 상세 견적을 요구하지 않습니다.</p>'}${i.status==='available'&&r.status==='open'?button('정식 견적 요청','request-quote',i.id,'primary'):''}${i.quote&&r.status==='open'&&i.status==='quoted'?button('이 전문가 선택','choose-quote',i.id,'primary'):''}${button('의뢰 대화 보기','messages',i.id)}</article>`).join('')}</div>`:''}${err}<div class="app-actions">${button('내 의뢰로','dashboard','requests')}${r.status!=='closed'?button('의뢰 종료','close-request',key):''}</div>`,'MY REQUEST');
}
function quoteSummary(q){return `<div class="quote-price">${won(q.amount)}</div><div class="quote-meta"><span>작업 ${q.days}일</span><span>수정 ${q.revisions}회</span></div><h4>포함 범위·납품물</h4><p class="preserve-lines">${esc(q.scope)}</p><h4>제외 항목·추가 조건</h4><p class="preserve-lines">${esc(q.exclusions)}</p>`;}
async function inviteDetail(key){
 dashboardData=await api('/dashboard');const i=dashboardData.inbox.find(i=>i.id===key);if(!i)throw Error('의뢰를 찾을 수 없습니다.');const b=i.brief;
 const active=i.request_status==='open';
 show(b.title,`<p>${esc(i.client_name)} · ${categories[b.category]} · <span class="state-label">${i.request_status==='closed'?'종료':stateNames[i.status]}</span></p><div class="request-summary"><b>작업 범위</b>\n${esc(b.scope)}\n\n<b>준비 자료</b>\n${esc(b.materials)}\n\n<b>예산</b> ${won(b.budget)} · <b>완료일</b> ${esc(b.deadline)}</div>${active&&['invited','needs_info','available'].includes(i.status)?`<p>아직 상세 견적을 작성하지 않아도 됩니다. 작업 가능 여부만 먼저 알려 주세요.</p><div class="app-actions">${button('작업 가능합니다','availability',key+':available','primary')}${button('추가 정보가 필요해요','availability',key+':needs_info')}${button('일정이 어렵습니다','availability',key+':declined')}</div>`:''}${active&&i.status==='quote_requested'?`<div class="information-box">고객이 정식 견적을 요청했습니다. 아래에서 저장한 틀로 견적을 작성해 주세요.</div><div class="app-actions">${button('견적 작성','quote',key,'primary')}</div>`:''}${i.quote?`<h3>내가 보낸 견적</h3>${quoteSummary(i.quote)}<div class="app-actions">${button('이 견적을 틀로 저장','save-sent-quote',key)}</div>`:''}${err}<div class="app-actions">${button('고객과 대화','messages',key)}${button('받은 의뢰로','dashboard','inbox')}</div>`,'REQUEST INBOX');
}
async function workForm(key=''){
 if(!user.profile){await dashboard('profile');toast('첫 작업을 올리기 전에 소개를 저장해 주세요.');return;}
 const p=key?(await api('/my/portfolios')).find(x=>x.id===key):{};if(!p)throw Error('작업물을 찾을 수 없습니다.');let image=p.image||'';
 show(key?'작업물 수정':'잘하는 일을 보여주세요',`<p>공개를 선택하면 저장 즉시 작업 모음에 올라갑니다. 본인 작업과 공개 권한이 있는 이미지를 올려 주세요.</p><form id="active-form"><div class="form-grid">${input('title','작업 제목',p.title||'','text','required minlength="3" maxlength="100"')}${catSelect(p.category||user.profile.category)}<div class="full"><label for="work-image">대표 이미지 · JPG, PNG, WebP / 8MB 이하</label><input id="work-image" type="file" accept="image/jpeg,image/png,image/webp" ${image?'':'required'}><img id="work-preview" class="upload-preview-image" ${image?'src="/api/upload-preview/'+image.split('/').pop()+'"':'hidden'} alt="업로드할 작업 미리보기"></div>${area('description','작업 설명',p.description||'','required minlength="10" maxlength="3000"')}${area('scope','본인이 수행한 범위 · 기본 금액의 포함 항목',p.scope||'','required minlength="5" maxlength="1000" placeholder="예: 로고 시안 2개, 수정 2회, AI·PNG 파일. 인쇄 제작 제외."')}${input('price','기본 범위의 시작 금액 (선택)',p.price||'','number','min="0" max="100000000"')}</div><label class="check"><input name="published" type="checkbox" ${p.published===0?'':'checked'}>작업 모음에 공개하기</label><label class="check"><input type="checkbox" required>본인이 수행한 작업이며, 이미지와 내용의 공개 권한이 있습니다.</label>${err}<div class="app-actions"><button class="button primary">작업물 저장</button>${button('작업 목록','dashboard','portfolio')}</div></form>`,'YOUR PORTFOLIO');
 const importBox=document.createElement('section');importBox.className='import-work';importBox.innerHTML=`<h3>기존 포트폴리오가 있으신가요?</h3><p>내 작업 링크에서 제목·설명·대표 이미지를 가져옵니다. 내용을 확인한 뒤 게시해 주세요. 공개 작업에는 외부 이동 링크가 표시되지 않습니다.</p><label for="import-url">내 작업의 공개 링크</label><input id="import-url" type="url" placeholder="https://..." maxlength="2000"><label class="check"><input id="import-rights" type="checkbox">본인 작업이며 이미지·설명을 이곳에 다시 게시할 권한이 있습니다. 출처 링크 유지가 필요한 자료는 제외합니다.</label><button type="button" class="button secondary" id="import-work">내 작업 가져오기</button><p id="import-status" role="status" class="subtle"></p>`;$('#active-form').before(importBox);
 $('#import-work').addEventListener('click',e=>run(async()=>{
  const status=$('#import-status');
  if(!$('#import-rights').checked){status.textContent='본인 작업과 재게시 권한을 먼저 확인해 주세요.';return;}
  if(!$('#import-url').value||!$('#import-url').checkValidity()){status.textContent='공개된 작업 링크를 입력해 주세요.';return;}
  if($('#f-title').value||$('#f-description').value||image){
   if(!importBox.querySelector('#import-replace')){const label=document.createElement('label');label.className='check';label.innerHTML='<input type="checkbox" id="import-replace">작성 중인 제목·설명·이미지를 가져온 내용으로 교체합니다.';status.before(label);}
   if(!$('#import-replace').checked){status.textContent='기존 내용 교체에 체크한 뒤 다시 눌러 주세요.';return;}
  }
  status.textContent='작업 정보를 가져오고 있습니다…';
  try{
   const data=await post('/portfolio-import',{url:$('#import-url').value,rights_confirmed:true});
   $('#f-title').value=data.title;$('#f-description').value=data.description;
   image=data.image;$('#work-image').value='';$('#work-image').required=!image;
   $('#work-preview').hidden=!image;if(image)$('#work-preview').src='/api/upload-preview/'+image.split('/').pop();else $('#work-preview').removeAttribute('src');
   status.textContent='초안으로 가져왔습니다. 분야·수행 범위와 내용을 확인하고 아래에서 저장해 주세요. '+data.warnings.join(' ');
   $('#import-replace')?.closest('label').remove();
  }catch(ex){status.textContent=ex.message+' 아래에서 직접 입력하고 이미지를 올릴 수도 있습니다.';}
 },e.currentTarget));
 let previewUrl=null;$('#work-image').addEventListener('change',e=>{if(previewUrl)URL.revokeObjectURL(previewUrl);const f=e.target.files[0];if(f){previewUrl=URL.createObjectURL(f);$('#work-preview').src=previewUrl;$('#work-preview').hidden=false;}});
 bindForm(async d=>{const f=$('#work-image').files[0];if(f){const payload=new FormData();payload.append('file',f);image=(await api('/uploads',{method:'POST',body:payload})).path;}d.image=image;d.price=Number(d.price||0);d.published=!!d.published;await api('/portfolios'+(key?'/'+key:''),{method:key?'PUT':'POST',body:d});if(previewUrl)URL.revokeObjectURL(previewUrl);await refreshWorks();toast(d.published?'작업물을 공개했습니다.':'비공개 작업물로 저장했습니다.');await dashboard('portfolio');});
}
async function quoteForm(invite='',template=null){
 const list=await api('/templates');const q=template||{};
 show(invite?'의뢰에 맞게 견적을 작성하세요':'자주 쓰는 저장한 견적서',`${invite?'<p>보내기 전에 고객의 작업 범위와 이번 조건이 맞는지 확인해 주세요.</p>':'<p>의뢰별로 복사해서 금액과 납품 조건을 빠르게 바꿀 수 있습니다.</p>'}${list.length?`<label for="template-select">저장한 견적서 불러오기</label><select id="template-select"><option value="">직접 작성</option>${list.map(t=>`<option value="${t.id}">${esc(t.title)} · ${won(t.amount)}</option>`).join('')}</select>`:''}<form id="active-form"><div class="form-grid">${input('title','견적 제목',q.title||'','text','required minlength="3" maxlength="100"')}${input('amount','총 견적 금액 (원)',q.amount||'','number','required min="1" max="100000000"')}${input('days','작업 기간 (일)',q.days||'','number','required min="1" max="365"')}${input('revisions','포함된 수정 횟수',q.revisions??2,'number','required min="0" max="50"')}${area('scope','포함 범위·납품물',q.scope||'','required minlength="10" maxlength="3000"')}${area('exclusions','제외 항목·추가 작업 조건',q.exclusions||'','required minlength="2" maxlength="2000"')}</div>${invite?'<label class="check"><input type="checkbox" required>고객의 의뢰 범위를 확인했고, 금액·납기·수정 조건을 검토했습니다.</label>':''}${err}<div class="app-actions"><button class="button primary">${invite?'발송 전 미리보기':'저장한 견적서 저장'}</button></div></form>`,'QUOTE DESK');
 $('#template-select')?.addEventListener('change',e=>{const t=list.find(t=>t.id===e.target.value);if(t)for(const k of ['title','amount','days','revisions','scope','exclusions'])$('#f-'+k).value=t[k];});
 bindForm(async d=>{for(const k of ['amount','days','revisions'])d[k]=Number(d[k]);if(invite)d.scope_unchanged=!!d.scope_unchanged;if(!invite){await post('/templates',d);toast('저장한 견적서을 저장했습니다.');await dashboard('templates');return;}
 show('이 내용으로 보내시겠어요?',`<h3>${esc(d.title)}</h3>${quoteSummary(d)}<p class="subtle">발송 뒤에는 이 견적을 직접 수정할 수 없습니다. 변경 조건은 고객과 대화로 확인해 주세요.</p>${err}<div class="app-actions"><button class="button secondary" id="edit-quote">다시 수정</button><button class="button primary" id="send-quote">정식 견적 보내기</button></div>`,'REVIEW QUOTE');
 $('#edit-quote').addEventListener('click',()=>run(()=>quoteForm(invite,d)));$('#send-quote').addEventListener('click',e=>run(async()=>{await post('/invites/'+invite+'/quote',d);if(typeof draftClear==='function')draftClear('quote/'+invite);toast('견적을 보냈습니다.');await inviteDetail(invite);},e.currentTarget));
 });
}
async function thread(key){
 const messages=await api('/invites/'+key+'/messages');
 show('의뢰 대화',`<p>작업 범위를 확인하고 필요한 자료를 이야기하세요. 비밀번호나 결제 정보는 적지 마세요.</p><div>${messages.length?messages.map(m=>`<article class="thread-message ${m.user_id===user.id?'mine':''}"><small>${esc(m.name)} · ${dates(m.created)}</small><p>${esc(m.body)}</p></article>`).join(''):empty('아직 대화가 없습니다.','범위가 모호하거나 자료가 필요하면 먼저 물어보세요.')}</div><form id="active-form">${area('body','메시지','','required maxlength="3000"')}${err}<div class="app-actions"><button class="button primary">메시지 보내기</button>${button('대화 새로고침','messages',key)}${button('작업 공간','dashboard')}</div></form>`,'CONVERSATION');
 bindForm(async d=>{await post('/invites/'+key+'/messages',d);await thread(key);});
}
function confirmation(title,description,fn){show(title,`<p>${description}</p>${err}<div class="app-actions"><button class="button secondary" data-close>취소</button><button class="button primary" id="confirm-action">확인</button></div>`);$('#confirm-action').addEventListener('click',e=>run(fn,e.currentTarget));}
const actions={
 dashboard:v=>requireUser(()=>dashboard(v||'requests')),
 'new-brief':()=>cost(),
 request:requestDetail,
 invite:inviteDetail,
 'edit-brief':v=>{const r=dashboardData.requests.find(r=>r.id===v);briefForm(r.data,v);},
 'copy-brief':v=>{const r=dashboardData.requests.find(r=>r.id===v);briefForm(r.data);},
 'submit-request':async v=>{if(!$('#submit-confirm').checked)throw Error('실제 견적 요청 의사를 확인해 주세요.');const r=dashboardData.requests.find(r=>r.id===v);await cost(r.data.category,async()=>{const result=await post('/requests/'+v+'/submit',{confirmed:true,cost_seen:true});toast(result.matched?result.matched+'명의 전문가에게 작업 가능 여부를 요청했습니다.':'의뢰를 접수했습니다. 아직 맞는 전문가가 없습니다.');await requestDetail(v);});},
 rematch:async v=>{const r=await post('/requests/'+v+'/submit',{confirmed:true,cost_seen:true});toast(r.matched?r.matched+'명에게 추가로 전달했습니다.':'새로 연결할 전문가가 아직 없습니다.');await requestDetail(v);},
 availability:async v=>{const [id,status]=v.split(':');await post('/invites/'+id+'/availability',{status});await inviteDetail(id);},
 'request-quote':async v=>{await post('/invites/'+v+'/request-quote');toast('정식 견적을 요청했습니다.');await dashboard();},
 'choose-quote':v=>confirmation('이 전문가와 상담을 이어갈까요?','다른 전문가에게는 선택이 끝났다고 알립니다. 결제나 계약이 자동으로 체결되지는 않습니다.',async()=>{await post('/invites/'+v+'/select');await dashboard();}),
 'close-request':v=>confirmation('의뢰를 종료할까요?','연결된 전문가에게 종료를 알리고 추가 견적 작성을 중단합니다.',async()=>{await post('/requests/'+v+'/close');await requestDetail(v);}),
 'edit-work':v=>requireUser(()=>workForm(v)),
 'hide-work':v=>confirmation('작업을 비공개로 바꿀까요?','작업 모음과 비용 안내에서 제외됩니다. 내 작업 공간에서 다시 공개할 수 있습니다.',async()=>{await api('/portfolios/'+v,{method:'DELETE'});await refreshWorks();await dashboard('portfolio');}),
 template:()=>quoteForm(),quote:v=>quoteForm(v),
 'copy-template':async v=>quoteForm('',(await api('/templates')).find(t=>t.id===v)),
 'delete-template':v=>confirmation('저장한 견적서을 삭제할까요?','이미 보낸 견적은 남습니다.',async()=>{await api('/templates/'+v,{method:'DELETE'});await dashboard('templates');}),
 'save-sent-quote':async v=>{const i=dashboardData.inbox.find(x=>x.id===v);await post('/templates',i.quote);toast('보낸 견적을 틀로 저장했습니다.');},
 messages:thread,
 'read-notices':async()=>{await post('/notices/read');await dashboard('notices');},
 logout:async()=>{await post('/auth/logout');user=null;dashboardData={requests:[],inbox:[],notices:[]};updateAccount();close();toast('로그아웃했습니다.');},
 support:()=>{show('운영 문의',`<p>계정 정보 삭제, 작업물 신고 관련 문의, 서비스 오류를 남겨 주세요. 문의는 운영자만 볼 수 있습니다.</p><form id="active-form">${area('body','문의 내용','','required minlength="5" maxlength="3000"')}${err}<div class="app-actions"><button class="button primary">문의 접수</button></div></form>`);bindForm(async d=>{await post('/support',d);show('문의를 접수했습니다.','<p>운영자가 확인할 수 있도록 저장했습니다. 개인정보 삭제 요청은 계정과 진행 중인 의뢰를 확인한 뒤 처리합니다.</p>');});},
 report:v=>requireUser(()=>{show('작업 신고',`<p>권리 침해, 허위 경력, 개인정보 노출 등 확인할 내용을 적어 주세요. 운영자가 접수 내용을 확인합니다.</p><form id="active-form">${area('body','신고 사유','','required minlength="5" maxlength="3000"')}${err}<div class="app-actions"><button class="button primary">신고 접수</button></div></form>`);bindForm(async d=>{await post('/portfolios/'+v+'/report',d);close();toast('신고를 접수했습니다.');});})
};
document.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.hasAttribute('data-close')){close();return;}
 if(b.dataset.action){run(()=>actions[b.dataset.action]?.(b.dataset.value),b);return;}
 if(b.hasAttribute('data-brief')){run(()=>requireUser(()=>briefForm({category:categories[b.dataset.brief]?b.dataset.brief:(categories[category]?category:'logo'),reference:b.dataset.reference||''})),b);return;}
 if(b.hasAttribute('data-cost')){run(()=>cost(categories[category]?category:'logo'),b);return;}
 if(b.hasAttribute('data-workspace')){run(()=>requireUser(()=>dashboard('portfolio')),b);return;}
 if(b.dataset.project){location.href='/?work='+encodeURIComponent(b.dataset.project);return;}
 if(b.dataset.save){const id=b.dataset.save;saved=saved.includes(id)?saved.filter(x=>x!==id):[...saved,id];try{localStorage.setItem('wa.saved',JSON.stringify(saved));}catch{toast('브라우저에 저장하지 못했습니다.');}render();return;}
 if(b.dataset.filter){category=b.dataset.filter;render();return;}
 if(b.dataset.category){category=b.dataset.category;render();$('#explore-title').focus({preventScroll:true});$('#explore').scrollIntoView();return;}
 if(b.dataset.collection){collection=b.dataset.collection;render();return;}
});
$('#collection-select').addEventListener('change',e=>{collection=e.target.value;render();});
$('#account-button').addEventListener('click',()=>run(()=>requireUser(()=>dashboard())));
$('#search-form').addEventListener('submit',e=>{e.preventDefault();query=$('#search-input').value;render();$('#explore').scrollIntoView();});
$('#saved-filter').addEventListener('click',()=>{savedOnly=!savedOnly;render();});
$('#saved-nav')?.addEventListener('click',()=>{savedOnly=true;render();$('#explore').scrollIntoView();});
$('#reset-filters').addEventListener('click',()=>{category='all';collection='all';query='';savedOnly=false;$('#search-input').value='';render();});
$('#about-preview').addEventListener('click',()=>show('WakeAgain 이용 안내',`<h3>좋은 작업에서 시작하는 연결</h3><p>콘셉트 컬렉션은 의뢰 방향을 고르는 예시입니다. 등록 전문가의 작업에는 실제 표시 이름이 붙습니다.</p><h3>비용 확인 → 의뢰 확정 → 작업 가능 응답 → 견적 비교</h3><p>초안과 비용 확인은 전문가에게 노출되지 않습니다. 실제 진행할 의뢰만 적합한 전문가에게 전달합니다.</p><h3>서비스 이용 범위</h3><p>현재 작업 탐색, 의뢰, 견적 비교와 상담을 지원하며, 사이트 내 결제·에스크로·정산은 제공하지 않습니다. 전문가 선택만으로 결제나 계약이 체결되지 않습니다.</p><h3>새로운 전문가에게도 기회를</h3><p>후기 수 순위 대신 분야, 작업 가능 상태와 최근 초대 순서를 기준으로 연결합니다. 견적 발송료를 받지 않습니다.</p>`));
render();
(async()=>{try{config=await api('/config');if(config.development)$('#environment-note').textContent='로컬 베타 · 데이터는 서버에 저장됩니다. 공개 사이트와는 연결되지 않았습니다.';await refreshWorks();user=await api('/session');updateAccount();}catch(e){toast(e.message);$('#environment-note').textContent='서버 연결을 확인해 주세요. 등록 작업을 불러오지 못했습니다.';}})();
setInterval(async()=>{if(user&&document.visibilityState==='visible'){try{const d=await api('/dashboard');const n=d.notices.filter(x=>!x.read).length;$('#account-button').textContent='내 작업 공간'+(n?' '+n:'');}catch{}}},30000);

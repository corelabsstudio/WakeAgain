'use strict';
let workspaceMode=false,workspaceRoute='',workspaceDraftFlush=null,workspaceDraftFailed=false,workspaceBusy=false,submittingRoute=null;
const workspaceRoot=document.createElement('div');workspaceRoot.id='workspace-shell';workspaceRoot.hidden=true;
workspaceRoot.innerHTML='<aside id="workspace-navigation" aria-label="작업 공간 메뉴"></aside><section id="workspace-page" role="main" tabindex="-1"></section>';
$('#app-dialog').before(workspaceRoot);
const pageDialog=$('#app-dialog'),dialogHome=pageDialog.parentNode,originalShow=show,originalClose=close;
const routes={portfolio:'내 작업물',requests:'내 의뢰',inbox:'받은 의뢰',notices:'알림',templates:'저장한 견적서',profile:'내 소개',availability:'작업 조건',settings:'수신 시간·이메일',account:'로그인·연락처',alimtalk:'카카오 알림톡',admin:'운영 관리',preferences:'내 정보',requesthub:'의뢰'};
const groups=[['작업',[['portfolio','내 작업물']]],['의뢰',[['inbox','받은 의뢰'],['requests','내 의뢰']]],['관리',[['templates','저장한 견적서'],['notices','알림'],['preferences','설정']]]];
function mobileSection(){if(/^(chat\/|workspace\/conversations)/.test(workspaceRoute))return 'conversations';if(/^(request\/|invite\/|brief\/|direct\/|quote\/|workspace\/(requests|inbox|requesthub))/.test(workspaceRoute))return 'requesthub';if(/^(work\/|workspace\/portfolio)/.test(workspaceRoute))return 'portfolio';return 'preferences';}
function navigation(){
 if(!user){$('#workspace-navigation').innerHTML='<a class="workspace-home" href="#explore">← 작업 둘러보기</a><p class="workspace-user">전문가 프로필</p>';return;}
 $('#workspace-navigation').innerHTML=`<a class="workspace-home" href="#top">← 작업 둘러보기</a><p class="workspace-user">${esc(user?.name||'WakeAgain')}</p><nav class="mobile-workspace-nav" aria-label="주 메뉴">${[['portfolio','작업'],['requesthub','의뢰'],['conversations','대화'],['preferences','내 정보']].map(([key,label])=>`<a href="#/workspace/${key}" ${mobileSection()===key?'aria-current="page"':''}>${label}</a>`).join('')}</nav>${groups.map(([label,items])=>`<section><h2>${label}</h2>${items.map(([key,text])=>`<a href="#/workspace/${key}" ${workspaceRoute==='workspace/'+key?'aria-current="page"':''}>${text}</a>`).join('')}</section>`).join('')}<button class="workspace-logout" data-action="logout">로그아웃</button>`;
}
function flushDraft(){if(workspaceDraftFlush)workspaceDraftFlush();}
function enterWorkspace(route){
 flushDraft();workspaceDraftFlush=null;workspaceDraftFailed=false;
 const changed=workspaceRoute!==route;workspaceRoute=route;workspaceMode=true;
 const open=$('dialog[open]');if(open)open.close();
 $('#workspace-page').append(pageDialog);workspaceRoot.hidden=false;
 document.body.classList.add('workspace-mode');document.body.classList.remove('modal-open');
 if(location.hash!=='#/'+route)history.pushState(null,'','#/'+route);
 $('.skip').setAttribute('href','#workspace-page');navigation();if(changed)window.scrollTo({top:0,behavior:'instant'});
}
function leaveWorkspace(){
 flushDraft();workspaceDraftFlush=null;workspaceMode=false;workspaceRoute='';workspaceDraftFailed=false;
 if(pageDialog.open)pageDialog.close();dialogHome.append(pageDialog);workspaceRoot.hidden=true;$('.skip').setAttribute('href','#main');document.body.classList.remove('workspace-mode','modal-open');document.title='WakeAgain — 좋은 작업에서 시작하는 외주';
}
show=function(title,body,eyebrow='WAKEAGAIN'){
 flushDraft();workspaceDraftFlush=null;
 if(!workspaceMode){$('#app-title').setAttribute('aria-level','2');pageDialog.classList.toggle('login-dialog',eyebrow==='WELCOME'||title.includes('인증'));return originalShow(title,body,eyebrow);}
 if(pageDialog.open)pageDialog.close();$('#app-title').textContent=title;$('#app-eyebrow').textContent=eyebrow;$('#app-content').innerHTML=body;
 pageDialog.show();document.body.classList.remove('modal-open');document.title=title+' · WakeAgain';$('#app-title').setAttribute('aria-level','1');$('#app-title').setAttribute('tabindex','-1');$('#app-title').focus({preventScroll:true});
};
close=function(){if(workspaceMode){leaveWorkspace();history.pushState(null,'','#top');}else originalClose();};
const compactLogin=login;
login=async function(next=()=>dashboard('portfolio')){
 if(workspaceMode)leaveWorkspace();pageDialog.classList.add('login-dialog');return compactLogin(next);
};
async function page(route,render){
 if(!user){try{sessionStorage.setItem('wa.afterLogin',route);}catch{}return login(()=>page(route,render));}
 enterWorkspace(route);
 try{await render();$('.app-tabs')?.remove();}catch(e){show('화면을 불러오지 못했습니다.',`<p role="alert">${esc(e.message)}</p><a class="button secondary" href="#/workspace/portfolio">내 작업물로</a>`);}
}
function storage(){try{return localStorage;}catch{return null;}}
function draftRead(route){return user&&storage()?DraftStore.read(storage(),user.id,route):null;}
function draftWrite(route,data){const ok=!!(user&&storage()&&DraftStore.write(storage(),user.id,route,data));workspaceDraftFailed=!ok;const status=$('#draft-status');if(status)status.textContent=ok?'이 기기에 초안 저장됨 · 최대 7일 · 로그아웃 시 삭제':'초안을 저장하지 못했습니다. 이 화면을 닫기 전에 저장해 주세요.';return ok;}
function draftClear(route){if(user&&storage())DraftStore.remove(storage(),user.id,route);workspaceDraftFlush=null;workspaceDraftFailed=false;}
function attachFormDraft(route,payload=null){
 const form=$('#active-form');if(!form)return;
 const saved=submittingRoute===route?null:draftRead(route),controls=()=>[...form.elements].filter(e=>e.name&&e.type!=='file'&&!['password','email','tel'].includes(e.type)&&!['code','consent'].includes(e.name));
 if(saved?.fields){
  const category=form.elements.namedItem('category');if(category&&saved.fields.category&&category.value!==saved.fields.category){category.value=saved.fields.category;category.dispatchEvent(new Event('change'));}
  for(const el of controls()){const val=saved.fields[el.name];if(val===undefined)continue;if(el.type==='checkbox')el.checked=Array.isArray(val)?val.includes(el.value):!!val;else el.value=val;}
 }
 const note=document.createElement('p');note.id='draft-status';note.className='draft-status';note.setAttribute('role','status');note.textContent=saved?'이 기기에 저장한 초안을 불러왔습니다.':'입력 내용은 이 기기에 최대 7일 동안 저장되며, 로그아웃하면 삭제됩니다.';form.before(note);
 workspaceDraftFlush=()=>{if(!form.isConnected)return;const fields={};for(const el of controls()){if(el.type==='checkbox'&&['weekdays','capabilities','styles'].includes(el.name)){fields[el.name]||=[];if(el.checked)fields[el.name].push(el.value);}else fields[el.name]=el.type==='checkbox'?el.checked:el.value;}draftWrite(route,{fields,payload});};
 form.addEventListener('input',flushDraft);form.addEventListener('change',flushDraft);if(!saved)flushDraft();
}
const rawBindForm=bindForm;
bindForm=function(fn){const route=workspaceRoute;return rawBindForm(async(...args)=>{submittingRoute=route;try{await fn(...args);if(user&&storage()&&!(workspaceRoute===route&&$('#send-quote')))DraftStore.remove(storage(),user.id,route);}finally{submittingRoute=null;}});};
const originalConfirmation=confirmation;
confirmation=function(title,description,fn){const inWorkspace=workspaceMode;originalConfirmation(title,description,fn);if(inWorkspace){const cancel=$('#app-content [data-close]');cancel.removeAttribute('data-close');cancel.addEventListener('click',()=>run(resolveWorkspace));}};
const oldDashboard=dashboard;
dashboard=async function(tab='portfolio'){
 if(!routes[tab])tab='portfolio';
 return page('workspace/'+tab,async()=>{
  if(tab==='requesthub'){show('의뢰',`<p>맡긴 일과 받은 일을 나누어 확인하세요.</p><div class="settings-list"><a href="#/workspace/requests"><strong>내가 맡긴 의뢰</strong><span>전문가 응답과 도착한 견적을 확인합니다.</span></a><a href="#/workspace/inbox"><strong>내가 받은 의뢰</strong><span>작업 가능 여부를 답하고 견적을 보냅니다.</span></a><a href="#/workspace/templates"><strong>저장한 견적서</strong><span>자주 쓰는 견적서를 꺼내서 수정합니다.</span></a></div>`);return;}
  if(tab==='preferences'){
   const status=await api('/admin/status');
   show('내 정보',`<p>자주 바꾸는 정보만 모았습니다.</p><div class="settings-list">${[['notices','알림','의뢰와 작업의 새 소식을 확인합니다.'],['statistics','내 작업 통계','작업 노출부터 견적 발송까지 확인합니다.'],['templates','저장한 견적서','자주 쓰는 견적서를 관리합니다.'],['profile','이름과 소개','공개 프로필을 수정합니다.'],['availability','작업 조건','시작 가능일과 지원 작업을 설정합니다.'],['account','로그인·연락처','연결 계정과 연락 이메일을 관리합니다.'],['settings','수신 시간·이메일','요일과 시간을 정하고 이메일을 켭니다.'],['alimtalk','카카오 알림톡','휴대전화 인증과 수신 여부를 관리합니다.'],...(status.admin?[['admin','운영 관리','신고·문의와 발송 상태를 확인합니다.']]:[])].map(([key,title,desc])=>`<a href="#/workspace/${key}"><strong>${title}</strong><span>${desc}</span><b aria-hidden="true">↗</b></a>`).join('')}</div><button class="workspace-logout" data-action="logout">로그아웃</button>`);return;
  }
  await oldDashboard(tab);$('.app-tabs')?.remove();$('#app-title').textContent=routes[tab];document.title=routes[tab]+' · WakeAgain';
  if(['profile','availability'].includes(tab))attachFormDraft('workspace/'+tab);
  if(tab==='portfolio'&&draftRead('work/new')){
   const link=$('.portfolio-empty .button');if(link)link.textContent='작성하던 작업 이어가기 →';
  }
 });
};
const oldRequest=requestDetail,oldInvite=inviteDetail,oldThread=thread,oldQuote=quoteForm,oldBrief=briefForm;
requestDetail=key=>page('request/'+key,()=>oldRequest(key));inviteDetail=key=>page('invite/'+key,()=>oldInvite(key));
thread=key=>page('chat/'+key,async()=>{await oldThread(key);attachFormDraft('chat/'+key);});
quoteForm=(key='',template=null)=>page('quote/'+(key||'new'),async()=>{await oldQuote(key,template);attachFormDraft('quote/'+(key||'new'));});
briefForm=(data={},key=null)=>{const route='brief/'+(key||'new')+'/'+(data.scope?'edit':'start');return page(route,async()=>{await oldBrief(data,key);attachFormDraft(route,{data,key});});};
actions.request=key=>requestDetail(key);actions.invite=key=>inviteDetail(key);actions.messages=key=>thread(key);
actions.dashboard=v=>dashboard(v||'portfolio');actions['edit-work']=v=>workForm(v);
const priorLogout=actions.logout;
actions.logout=async()=>{flushDraft();const id=user?.id;await priorLogout();if(id&&storage())DraftStore.clearUser(storage(),id);};
async function resolveWorkspace(){
 if(workspaceBusy){toast('업로드가 끝난 뒤 이동해 주세요.');history.replaceState(null,'','#/'+workspaceRoute);return;}
 const route=location.hash.slice(2),[kind,key,stage]=route.split('/');
 if(!location.hash.startsWith('#/')){if(workspaceMode&&location.hash==='#workspace-page')return;if(workspaceMode)leaveWorkspace();if(location.hash==='#explore')$('#explore').scrollIntoView();return;}
 if(workspaceDraftFailed&&!confirm('초안을 저장하지 못했습니다. 그래도 이동할까요?')){history.replaceState(null,'','#/'+workspaceRoute);return;}
 if(kind==='workspace'&&routes[key])return dashboard(key);
 if(kind==='work'&&(key==='new'||/^[a-f0-9]{24}$/.test(key)))return workForm(key==='new'?'':key);
 if(['request','invite','chat','quote'].includes(kind)&&(/^[a-f0-9]{24}$/.test(key)||(kind==='quote'&&key==='new')))return ({request:requestDetail,invite:inviteDetail,chat:thread,quote:quoteForm}[kind])(key==='new'?'':key);
 if(kind==='brief'&&(key==='new'||/^[a-f0-9]{24}$/.test(key))){
  if(!user)return page(route,()=>resolveWorkspace());
  const cached=draftRead(route)?.payload;
  if(cached)return briefForm(cached.data,cached.key);
  if(key!=='new'){const d=await api('/dashboard');const request=d.requests.find(r=>r.id===key);if(request)return briefForm(request.data,key);}
  return briefForm();
 }
 return dashboard('portfolio');
}
window.resumeWorkspace=async()=>{let route;try{route=sessionStorage.getItem('wa.afterLogin');sessionStorage.removeItem('wa.afterLogin');}catch{}history.replaceState(null,'',route?'#/'+route:'#/workspace/portfolio');await resolveWorkspace();};
window.addEventListener('hashchange',()=>run(resolveWorkspace));
window.addEventListener('beforeunload',e=>{flushDraft();if(workspaceBusy||workspaceDraftFailed){e.preventDefault();e.returnValue='';}});
document.addEventListener('click',e=>{
 const target=e.target.closest('a,button');
 if(workspaceBusy&&target&&!target.closest('#image-editor')){e.preventDefault();e.stopImmediatePropagation();toast('현재 처리가 끝난 뒤 이동해 주세요.');return;}
 if(workspaceDraftFailed&&target&&!target.closest('#active-form')&&!confirm('초안을 저장하지 못했습니다. 그래도 이동할까요?')){e.preventDefault();e.stopImmediatePropagation();return;}
 const anchor=e.target.closest('a[href^="#/"]');if(anchor&&anchor.getAttribute('href')===location.hash){e.preventDefault();e.stopImmediatePropagation();run(resolveWorkspace);return;}
 if(workspaceMode&&e.target.closest('#saved-nav')){leaveWorkspace();history.pushState(null,'','#explore');}
 const b=e.target.closest('[data-workspace]');
 if(b){e.preventDefault();e.stopImmediatePropagation();run(()=>workForm());return;}
},true);
window.addEventListener('load',()=>run(async()=>{if(new URL(location.href).searchParams.has('auth'))return;user=await api('/session');updateAccount();if(location.hash.startsWith('#/'))await resolveWorkspace();}));

'use strict';
// Shared account UI. All counts and rows come from the signed-in user's API data.
let workspaceRole='client';
const workspaceFilters={};
const deskIcons={portfolio:'portfolio',requests:'request',inbox:'request',templates:'quote',conversations:'chat',notices:'notice',statistics:'quote',preferences:'settings',profile:'portfolio',availability:'settings',account:'settings',settings:'settings',alimtalk:'notice'};
function deskIcon(key,cls=''){return `<img class="desk-icon ${cls}" src="assets/workspace/${deskIcons[key]||key||'request'}.webp" alt="" width="64" height="64" aria-hidden="true">`;}
function defaultWorkspaceTab(){try{return localStorage.getItem('wa.role.'+user?.id)==='expert'?'portfolio':'requests';}catch{return user?.profile?'portfolio':'requests';}}
function deskEmpty(kind,title,description,action=''){return `<section class="desk-empty">${deskIcon(kind)}<h3>${esc(title)}</h3><p>${esc(description)}</p>${action?`<div class="desk-empty-action">${action}</div>`:''}</section>`;}
const baseEmpty=empty;
empty=function(title,text,action=''){return workspaceMode?deskEmpty(workspaceRoute.startsWith('chat/')?'chat':deskIcons[workspaceRoute.split('/')[1]]||'request',title,text,action):baseEmpty(title,text,action);};
navigation=function(){
 if(!user){$('#workspace-navigation').innerHTML='<div class="desk-nav-foot"><a href="#explore">작업 둘러보기</a></div>';return;}
 const key=workspaceRoute.split('/')[1],kind=workspaceRoute.split('/')[0];
 if(['portfolio','inbox','templates','statistics','profile','availability'].includes(key)||['work','invite','quote'].includes(kind))workspaceRole='expert';
 else if(key==='requests'||['request','brief','direct'].includes(kind))workspaceRole='client';
 else {try{workspaceRole=localStorage.getItem('wa.role.'+user?.id)||workspaceRole;}catch{}}
 if(user){try{localStorage.setItem('wa.role.'+user.id,workspaceRole);}catch{}}
 const expert=workspaceRole==='expert',items=expert?[['portfolio','내 작업물'],['inbox','받은 의뢰'],['templates','견적서 보관함'],['statistics','작업 통계']]:[['requests','내 의뢰']];
 const active=k=>key===k||(k==='preferences'&&['profile','availability','settings','account','alimtalk','admin'].includes(key))||(k==='conversations'&&kind==='chat');
 const links=rows=>rows.map(([k,label])=>`<a href="#/workspace/${k}" ${active(k)?'aria-current="page"':''}>${deskIcon(k)}<span>${label}</span></a>`).join('');
 $('#workspace-navigation').innerHTML=`<div class="desk-member"><span class="desk-avatar" aria-hidden="true">${user?.avatar?`<img src="${profilePhotoUrl(user.avatar)}" alt="">`:esc((user?.name||'W').slice(0,1))}</span><div><strong>${esc(user?.name||'WakeAgain')}</strong><a href="#/workspace/member-profile">프로필 관리 <span aria-hidden="true">›</span></a></div></div><div class="desk-role" role="group" aria-label="이용 화면"><button type="button" data-action="workspace-role" data-value="client" aria-pressed="${!expert}">의뢰인</button><button type="button" data-action="workspace-role" data-value="expert" aria-pressed="${expert}">전문가</button></div><nav class="desk-navigation" aria-label="내 업무"><div>${links(items)}</div><div>${links([['conversations','대화'],['notices','알림'],['preferences','설정']])}</div></nav><div class="desk-nav-foot"><a href="#explore">작업 둘러보기 <span aria-hidden="true">↗</span></a><button data-action="logout">로그아웃</button></div>`;
};
actions['workspace-role']=async role=>{workspaceRole=role==='expert'?'expert':'client';try{localStorage.setItem('wa.role.'+user.id,workspaceRole);}catch{}await dashboard(workspaceRole==='expert'?'portfolio':'requests');};
const deskShow=show;
show=function(title,body,eyebrow){deskShow(title,body,eyebrow);if(workspaceMode){workspaceRoot.dataset.route=workspaceRoute.split('/')[0];workspaceRoot.dataset.page=workspaceRoute.split('/')[1]||'';workspaceRoot.dataset.ui='form';}};
function deskHeader(title,subtitle,action=''){$('#app-title').textContent=title;document.title=title+' · WakeAgain';$('.desk-page-description')?.remove();$('.desk-page-action')?.remove();$('#app-title').insertAdjacentHTML('afterend',`<p class="desk-page-description">${esc(subtitle)}</p>`);if(action)$('#app-dialog>.dialog-head').insertAdjacentHTML('beforeend',`<div class="desk-page-action">${action}</div>`);}
// Remove any previous page's header action before rendering forms or another route.
const deskPageShow=show;
show=function(...args){$('.desk-page-description')?.remove();$('.desk-page-action')?.remove();return deskPageShow(...args);};
function deskStats(items){return `<div class="desk-stats">${items.map(([icon,label,n,filter])=>`<button type="button" data-desk-filter="${filter||'all'}">${deskIcon(icon)}<span>${esc(label)}<strong>${n}<small>건</small></strong></span></button>`).join('')}</div>`;}
function deskList(items,options){
 const {kind,filters,title,description,action,render}=options;
 const state=workspaceFilters[kind]||{filter:'all',query:''};workspaceFilters[kind]=state;
 const html=`<div class="desk-surface"><div class="desk-list-tools"><div class="desk-filters" role="group" aria-label="상태별 보기">${filters.map(([key,label,predicate])=>`<button type="button" data-desk-filter="${key}" aria-pressed="${state.filter===key}">${label}<span>${items.filter(predicate).length}</span></button>`).join('')}</div><label class="desk-search"><span class="sr-only">${esc(routes[kind]||'내역')} 검색</span><input type="search" id="desk-search" placeholder="제목 검색" value="${esc(state.query)}"></label></div><div id="desk-results"></div></div>`;
 $('#app-content').insertAdjacentHTML('beforeend',html);
 const paint=()=>{
  const predicate=(filters.find(f=>f[0]===state.filter)||filters[0])[2];
  const matched=items.filter(predicate).filter(x=>(x.title||x.data?.title||x.brief?.title||x.peer||'').toLocaleLowerCase().includes(state.query.toLocaleLowerCase()));
  $('#desk-results').innerHTML=matched.length?`<div class="${kind==='portfolio'?'desk-work-grid':'desk-rows'}">${matched.map(render).join('')}</div>`:items.length?deskEmpty(kind,'검색 결과가 없습니다.','다른 검색어를 입력하거나 상태를 변경해 주세요.'):deskEmpty(kind,title,description,action);
  $$('[data-desk-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.deskFilter===state.filter)));
 };
 $$('[data-desk-filter]').forEach(b=>b.addEventListener('click',()=>{state.filter=b.dataset.deskFilter;paint();}));
 $('#desk-search').addEventListener('input',e=>{state.query=e.target.value;paint();});paint();
}
function deskRow(title,status,meta,action,extra=''){return `<article class="desk-record"><div class="desk-record-main"><span class="desk-status">${esc(status)}</span><h3>${esc(title)}</h3><p>${esc(meta)}</p>${extra}</div><div class="desk-record-action">${action}</div></article>`;}
const inheritedDashboard=dashboard;
dashboard=async function(tab){
 tab=tab||defaultWorkspaceTab();
 if(!['portfolio','requests','inbox','templates','notices','preferences','statistics','conversations','requesthub','member-profile'].includes(tab))return inheritedDashboard(tab);
 if(tab==='requesthub')return dashboard(workspaceRole==='expert'?'inbox':'requests');
 return page('workspace/'+tab,async()=>{
  [dashboardData,user]=await Promise.all([api('/dashboard'),api('/me')]);updateAccount();navigation();
  show(routes[tab]||'내 작업 공간','');workspaceRoot.dataset.ui='list';
  const all=()=>true,link=(label,href)=>`<a class="button primary" href="${href}">${label}</a>`;
  if(tab==='member-profile'){
   deskHeader('프로필 관리','사진과 이름을 설정하세요.');
   const currentPhoto=user.avatar||null;
   $('#app-content').innerHTML=`<form id="member-profile-form" class="member-profile-editor"><div class="member-photo-row"><div class="member-photo-preview" id="member-photo-preview">${currentPhoto?`<img src="${profilePhotoUrl(currentPhoto)}" alt="현재 프로필 사진">`:`<span aria-hidden="true">${esc((user.name||'W').slice(0,1))}</span>`}</div><div class="member-photo-controls"><label for="member-photo">프로필 사진</label><input id="member-photo" name="photo" type="file" accept="image/jpeg,image/png,image/webp"><button type="button" class="text-button" id="member-photo-remove" ${currentPhoto?'':'hidden'}>사진 지우기</button><p class="subtle">JPG, PNG, WebP · 8MB 이하 · 100px 이상</p></div></div><label for="member-name">표시 이름</label><input id="member-name" name="name" value="${esc(user.name||'')}" required minlength="2" maxlength="40" autocomplete="nickname"><p class="subtle">작업과 대화, 의뢰 화면에 표시됩니다.</p><p class="member-profile-privacy">전문가로 공개 작업을 등록하면 이 사진이 공개 프로필에 표시됩니다. 의뢰인 계정의 사진은 다른 사용자에게 공개되지 않습니다.</p><p class="app-error" id="member-profile-error" role="alert"></p><div class="app-actions"><button class="button primary" type="submit">변경 내용 저장</button></div></form>`;
   let avatar=currentPhoto,selectedFile=null,previewObjectUrl=null;
   const preview=$('#member-photo-preview'),remove=$('#member-photo-remove'),file=$('#member-photo');
   const paintPhoto=()=>{const src=selectedFile?previewObjectUrl:avatar?profilePhotoUrl(avatar):'';preview.innerHTML=src?`<img src="${src}" alt="프로필 사진 미리보기">`:`<span aria-hidden="true">${esc(($('#member-name').value||'W').slice(0,1))}</span>`;remove.hidden=!avatar;};
   $('#member-name').addEventListener('input',()=>{if(!avatar)paintPhoto();});
   file.addEventListener('change',()=>{const next=file.files?.[0];if(!next)return;if(next.size>8*1024*1024){file.value='';$('#member-profile-error').textContent='이미지는 8MB 이하로 올려 주세요.';return;}selectedFile=next;avatar='selected';if(previewObjectUrl)URL.revokeObjectURL(previewObjectUrl);previewObjectUrl=URL.createObjectURL(next);preview.innerHTML=`<img src="${previewObjectUrl}" alt="프로필 사진 미리보기">`;remove.hidden=false;$('#member-profile-error').textContent='';});
   remove.addEventListener('click',()=>{selectedFile=null;avatar=null;file.value='';if(previewObjectUrl){URL.revokeObjectURL(previewObjectUrl);previewObjectUrl=null;}paintPhoto();});
   $('#member-profile-form').addEventListener('submit',e=>{e.preventDefault();run(async()=>{let nextAvatar=avatar;if(selectedFile){const form=new FormData();form.append('file',selectedFile);nextAvatar=(await api('/uploads',{method:'POST',body:form})).path;}await api('/profile/basic',{method:'PUT',body:{name:$('#member-name').value.trim(),avatar:nextAvatar}});if(previewObjectUrl){URL.revokeObjectURL(previewObjectUrl);previewObjectUrl=null;}user=await api('/me');updateAccount();navigation();toast('프로필을 저장했습니다.');await dashboard('member-profile');},e.submitter);});
   return;
  }
  if(tab==='portfolio'){
   const items=await api('/my/portfolios'),published=items.filter(x=>x.published).length;
   deskHeader('내 작업물','공개한 작업과 작성 중인 작업을 관리하세요.',link('작업물 등록','#/work/new'));
   $('#app-content').innerHTML=deskStats([['portfolio','전체 작업',items.length,'all'],['portfolio','공개 중',published,'published'],['portfolio','비공개',items.length-published,'hidden']])+await readinessPanel();
   const resume=draftRead('work/new');
   deskList(items,{kind:tab,filters:[['all','전체',all],['published','공개 중',x=>!!x.published],['hidden','비공개',x=>!x.published]],title:'아직 등록한 작업물이 없어요',description:'이미지를 올리거나 기존 포트폴리오 링크를 가져오세요.',action:link(resume?'작성하던 작업 이어가기':'첫 작업물 등록','#/work/new'),render:p=>`<article class="desk-work"><a href="#/work/${p.id}"><img class="desk-work-cover" src="/api/upload-preview/${esc(p.image.split('/').pop())}" alt="${esc(p.title)}" loading="lazy"><div><span class="desk-status">${p.published?'공개 중':'비공개'} · ${esc(categories[p.category])}</span><h3>${esc(p.title)}</h3><p>${p.price?won(p.price)+'부터':'가격 미설정'}</p></div></a><div class="row-actions">${button('수정','edit-work',p.id)}${p.published?button('비공개로 전환','hide-work',p.id):''}</div></article>`});return;
  }
  if(tab==='requests'||tab==='inbox'){
   const client=tab==='requests',items=client?dashboardData.requests:dashboardData.inbox;
   const filters=client?[['all','전체',all],['draft','작성 중',x=>x.status==='draft'],['open','견적 받는 중',x=>x.status==='open'],['selected','전문가 선택',x=>x.status==='selected'],['closed','보류·종료',x=>['paused','closed'].includes(x.status)]]:[['all','전체',all],['waiting','응답 필요',x=>x.status==='invited'&&x.request_status==='open'],['quote','견적 요청',x=>x.status==='quote_requested'&&x.request_status==='open'],['selected','선택된 의뢰',x=>x.status==='selected'],['closed','종료',x=>['closed','paused'].includes(x.request_status)||['declined','expired','not_selected'].includes(x.status)]];
   deskHeader(client?'내 의뢰':'받은 의뢰',client?'전문가의 응답과 견적을 한곳에서 확인하세요.':'내용을 확인하고 작업 가능 여부를 답해주세요.',client?button('의뢰 등록','new-brief','','primary'):'');
   $('#app-content').innerHTML=deskStats(filters.slice(1,4).map(([key,label,pred])=>['request',label,items.filter(pred).length,key]));
   deskList(items,{kind:tab,filters,title:client?'등록한 의뢰가 없어요':'아직 도착한 의뢰가 없어요',description:client?'필요한 작업을 적으면 맞는 전문가에게 견적을 받을 수 있어요.':'공개한 작업과 작업 조건에 맞는 의뢰가 여기에 도착합니다.',action:client?button('의뢰 등록하기','new-brief','','primary'):link('내 작업물 관리','#/workspace/portfolio'),render:r=>{const b=client?r.data:r.brief;return deskRow(b.title,(!client&&r.status==='quoted'?'견적 보냄':stateNames[client?r.status:(r.request_status==='closed'?'closed':r.status)]||r.status),`${categories[b.category]} · 예산 ${b.budget?won(b.budget):'협의'} · ${b.deadline||'일정 협의'}`,button(client?'의뢰 보기':'내용 확인',client?'request':'invite',r.id,'secondary'),client&&r.invites?.length?`<small>연결된 전문가 ${r.invites.length}명 · 받은 견적 ${r.invites.filter(i=>i.quote).length}개</small>`:'');}});return;
  }
  if(tab==='templates'){
   const items=await api('/templates');deskHeader('견적서 보관함','자주 쓰는 작업 범위와 금액을 저장해 두세요.',button('견적서 만들기','template','','primary'));
   deskList(items,{kind:tab,filters:[['all','전체',all]],title:'저장한 견적서가 없어요',description:'자주 보내는 견적을 만들어 두면 의뢰마다 다시 쓰지 않아도 돼요.',action:button('견적서 만들기','template','','primary'),render:t=>deskRow(t.title,'저장한 견적',`${won(t.amount)} · 작업 ${t.days}일 · 수정 ${t.revisions}회`,button('불러오기','copy-template',t.id,'secondary'),`<div class="row-actions">${button('삭제','delete-template',t.id)}</div>`)});return;
  }
  if(tab==='notices'){
   const items=dashboardData.notices,unread=items.filter(n=>!n.read).length;deskHeader('알림',`읽지 않은 알림 ${unread}개`,unread?button('모두 읽음','read-notices','','secondary'):'');
   $('#app-content').innerHTML=`<div class="desk-surface">${items.length?items.map(n=>`<article class="desk-notice ${n.read?'':'is-unread'}">${deskIcon('notice')}<div><p>${esc(n.body)}</p><small>${dates(n.created)}${n.read?'':' · 안 읽음'}</small></div></article>`).join(''):deskEmpty('notice','새 알림이 없어요','의뢰 응답, 새 견적과 메시지를 여기서 알려드려요.')}</div>`;return;
  }
  if(tab==='conversations'){
   const items=await api('/conversations');deskHeader('대화','의뢰별로 메시지와 첨부파일을 주고받으세요.');
   deskList(items,{kind:tab,filters:[['all','전체',all],['unread','안 읽음',x=>!!x.unread]],title:'아직 시작한 대화가 없어요',description:'의뢰가 전문가에게 전달되면 대화가 연결됩니다.',action:link('의뢰 확인',workspaceRole==='expert'?'#/workspace/inbox':'#/workspace/requests'),render:t=>`<a class="desk-conversation" href="#/chat/${t.id}"><span class="desk-avatar">${esc(t.peer.slice(0,1))}</span><div><h3>${esc(t.peer)} <small>${esc(t.title)}</small></h3><p>${esc(t.last||'첫 메시지를 보내세요.')}</p></div><span class="desk-chat-meta">${t.unread?`<b>${t.unread}개 안 읽음</b>`:dates(t.updated)}</span></a>`});return;
  }
  if(tab==='statistics'){
   const x=await api('/my/statistics');deskHeader('작업 통계','내 작업이 발견되고 상담으로 이어진 기록입니다.');
   $('#app-content').innerHTML=`<div class="desk-surface"><div class="desk-metrics">${[['portfolio','작업 노출',x.card_views],['portfolio','프로필 방문',x.profile_views],['request','받은 의뢰',x.received],['chat','응답한 의뢰',x.responded],['quote','보낸 견적',x.quoted],['quote','선택된 견적',x.selected]].map(([icon,label,n])=>`<div>${deskIcon(icon)}<span>${label}<strong>${n}</strong></span></div>`).join('')}</div><p class="desk-footnote">노출·방문은 같은 브라우저의 하루 중복을 제외합니다. 견적 선택은 결제·계약 완료를 뜻하지 않습니다.</p></div>`;return;
  }
  if(tab==='preferences'){
   const status=await api('/admin/status');deskHeader('설정','계정 정보와 업무·알림 설정을 관리하세요.');
   const sections=[['계정','settings',[['account','로그인·연락처','연결 계정, 연락 이메일'],['settings','알림 수신 설정','이메일, 요일과 시간'],['alimtalk','카카오 알림톡','전화번호, 수신 여부']]],['전문가 정보','portfolio',[['profile','이름과 소개','공개 프로필, 의뢰 수신'],['availability','작업 조건','지원 분야, 시작 가능일']]]];
   $('#app-content').innerHTML=`<div class="desk-settings-grid">${sections.map(([label,icon,items])=>`<section class="desk-surface desk-settings"><h3>${deskIcon(icon)}${label}</h3>${items.map(([key,title,desc])=>`<a href="#/workspace/${key}"><div><strong>${title}</strong><span>${desc}</span></div><b aria-hidden="true">›</b></a>`).join('')}</section>`).join('')}</div><div class="desk-account-actions"><button data-action="support">운영 문의 · 계정 삭제 요청</button>${status.admin?'<a href="#/workspace/admin">운영 관리</a>':''}<button data-action="logout">로그아웃</button></div>`;
  }
 });
};
actions.dashboard=v=>dashboard(v||undefined);

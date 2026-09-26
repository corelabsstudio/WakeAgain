'use strict';
const previousRequestDetail=requestDetail;
requestDetail=async function(key,selectedId=null){
 return page('request/'+key,async()=>{
  dashboardData=await api('/dashboard');
  const r=dashboardData.requests.find(x=>x.id===key);
  if(!r)throw Error('의뢰를 찾을 수 없습니다.');
  if(r.status==='draft')return previousRequestDetail(key);
  const b=r.data,progress=await api('/requests/'+key+'/progress');
  let selected=r.invites.find(i=>i.id===selectedId)||r.invites.find(i=>i.status==='selected')||r.invites[0];
  show(b.title,`<div class="request-room"><a href="#/workspace/requests" class="text-button">← 내 의뢰</a><section class="room-summary"><div><strong>${esc(stateNames[r.status]||r.status)}</strong><span>${esc(categories[b.category])} · 예산 ${b.budget?won(b.budget):'협의'} · 희망 완료 ${esc(b.deadline||'협의')}</span></div><details><summary>의뢰 내용 보기</summary><h3>작업 범위</h3><p class="preserve-lines">${esc(b.scope)}</p><h3>준비 자료</h3><p class="preserve-lines">${esc(b.materials||'등록된 자료 설명 없음')}</p>${b.reference?`<p>참고 작업: ${esc(b.reference)}</p>`:''}</details>${progress.reason?`<p>${esc(progress.reason)}</p>`:''}${r.status==='selected'?'<p>전문가를 선택했습니다. 결제나 계약이 자동으로 체결되지는 않습니다.</p>':''}<div class="room-management">${progress.can_release?button('다른 전문가 추천받기','release-target',key):''}${r.status==='open'?button('진행 보류','pause-request',key):''}${r.status==='paused'?button('의뢰 다시 진행','resume-request',key):''}${r.status!=='closed'?button('의뢰 종료','close-request',key):''}<button type="button" class="button secondary" id="room-refresh">응답 새로고침</button></div></section><div class="room-tabs" role="group" aria-label="의뢰 보기"><button type="button" data-room-tab="chat" aria-pressed="true">전문가와 대화 <span>${r.invites.length}</span></button><button type="button" data-room-tab="compare" aria-pressed="false">견적 비교 <span>${r.invites.filter(i=>i.quote).length}</span></button></div><div class="room-body"><aside class="room-experts" aria-label="연결된 전문가"></aside><section class="room-conversation" aria-label="선택한 전문가와 대화"><div class="room-expert-head"></div><div id="room-chat"></div></section></div><section class="room-compare" hidden aria-label="받은 견적 비교"></section></div>`,'내 의뢰');
  const root=$('.request-room'),list=$('.room-experts',root),chat=$('#room-chat',root),head=$('.room-expert-head',root);
  $('#room-refresh',root).onclick=()=>run(()=>requestDetail(key,selected?.id));
  function paintExperts(){list.innerHTML=r.invites.length?r.invites.map(i=>`<button type="button" data-room-expert="${i.id}" aria-pressed="${selected?.id===i.id}"><strong>${esc(i.name)}</strong><span>${esc(stateNames[i.status]||i.status)}</span><b>${i.quote?won(i.quote.amount):'견적 도착 전'}</b></button>`).join(''):'<p>조건에 맞는 전문가를 기다리고 있습니다.</p>';$$('[data-room-expert]',list).forEach(el=>el.onclick=()=>run(()=>selectExpert(el.dataset.roomExpert),el));}
  function quoteActions(i){return `${r.status==='open'&&i.status==='available'?`<button class="button primary" type="button" data-room-quote="${i.id}">정식 견적 요청</button>`:''}${r.status==='open'&&i.status==='quoted'?`<button class="button primary" type="button" data-room-choose="${i.id}">이 전문가 선택</button>`:''}`;}
  function bindQuoteActions(container){
   $$('[data-room-quote]',container).forEach(el=>el.onclick=()=>run(async()=>{flushDraft();await post('/invites/'+el.dataset.roomQuote+'/request-quote');toast('정식 견적을 요청했습니다.');await requestDetail(key,el.dataset.roomQuote);},el));
   $$('[data-room-choose]',container).forEach(el=>el.onclick=()=>{flushDraft();confirmation('이 전문가와 진행할까요?','다른 전문가에게는 선택이 끝났다고 알립니다. 선택만으로 결제나 계약이 체결되지는 않습니다.',async()=>{await post('/invites/'+el.dataset.roomChoose+'/select');await requestDetail(key,el.dataset.roomChoose);});const cancel=$('#app-content [data-close]');if(cancel){cancel.removeAttribute('data-close');cancel.onclick=()=>run(()=>requestDetail(key,el.dataset.roomChoose));}$('#app-content .app-actions').insertAdjacentHTML('afterbegin',`<a class="button secondary" href="#/request/${key}">의뢰로 돌아가기</a>`);});
  }
  let changing=false;
  async function selectExpert(id){
   if(changing||workspaceBusy)return;
   changing=true;
   try{
    flushDraft();if(workspaceDraftFailed)throw Error('작성 중인 메시지를 저장하지 못했습니다. 내용을 복사한 뒤 이동해 주세요.');
    workspaceDraftFlush=null;clearInterval(conversationTimer);
    selected=r.invites.find(i=>i.id===id);paintExperts();
    head.innerHTML=`<div><h2>${esc(selected.name)}</h2><a href="/#/expert/${selected.expert_id}" target="_blank" rel="noopener">포트폴리오 보기 ↗</a></div><p>${esc(nextActions[selected.status]||stateNames[selected.status])}</p>${selected.quote?`<details class="room-quote"><summary>받은 견적 ${won(selected.quote.amount)} · ${selected.quote.days}일 · 수정 ${selected.quote.revisions}회</summary>${quoteSummary(selected.quote)}</details>`:''}<div class="app-actions">${quoteActions(selected)}${selected.status==='selected'?button('계약 진행 여부 확인','agreement',selected.id):''}</div>`;
    bindQuoteActions(head);
    chat.innerHTML='<p role="status">대화를 불러오는 중입니다.</p>';
    await thread(selected.id,chat);
    if(['closed','paused'].includes(r.status)||['declined','expired','not_selected'].includes(selected.status)){
     $$('input,textarea,button', $('#active-form',chat)).forEach(e=>e.disabled=true);
     chat.insertAdjacentHTML('afterbegin','<p class="information-box">현재 대화는 읽기만 가능합니다. 기존 메시지는 아래에서 확인할 수 있습니다.</p>');
    }
   }finally{changing=false;}
  }
  const quotes=r.invites.filter(i=>i.quote),compare=$('.room-compare',root);
  compare.innerHTML=quotes.length?`<h2>같은 기준으로 견적 비교</h2><div class="room-comparison-grid">${quotes.map(i=>`<article><h3>${esc(i.name)}</h3><p>${esc(stateNames[i.status])}</p>${quoteSummary(i.quote)}<div class="app-actions">${quoteActions(i)}<button type="button" class="button secondary" data-room-talk="${i.id}">이 전문가와 대화</button></div></article>`).join('')}</div>`:'<h2>아직 도착한 견적이 없습니다</h2><p>작업 가능 응답이 오면 정식 견적을 요청하세요. 견적 전에도 전문가와 대화할 수 있습니다.</p>';
  bindQuoteActions(compare);
  function switchTab(mode){$('.room-body',root).hidden=mode!=='chat';compare.hidden=mode!=='compare';$$('[data-room-tab]',root).forEach(el=>el.setAttribute('aria-pressed',el.dataset.roomTab===mode));}
  $$('[data-room-tab]',root).forEach(el=>el.onclick=()=>switchTab(el.dataset.roomTab));
  $$('[data-room-talk]',compare).forEach(el=>el.onclick=()=>{switchTab('chat');run(()=>selectExpert(el.dataset.roomTalk));});
  paintExperts();
  if(selected)await selectExpert(selected.id);
  else{head.innerHTML='<h2>전문가 응답을 기다리고 있습니다</h2>';chat.innerHTML=`<p>연결된 전문가가 생기면 이곳에서 견적과 대화를 확인할 수 있습니다.</p>${r.status==='open'?button('연결 다시 확인','rematch',key):''}`;}
 });
};
actions.request=key=>requestDetail(key);

// Customer conversation links also open inside their request room.
const requestRoomChat=thread;
thread=async function(key,embedded=null){
 if(embedded||!user)return requestRoomChat(key,embedded);
 const data=await api('/dashboard');
 const ownerRequest=data.requests.find(r=>r.invites.some(i=>i.id===key));
 if(ownerRequest)return requestDetail(ownerRequest.id,key);
 return requestRoomChat(key);
};
actions.messages=key=>thread(key);

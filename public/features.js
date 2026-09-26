'use strict';
let catalogData=null;
async function catalog(){return catalogData||(catalogData=await api('/catalog'));}
const selectField=(name,label,options,value='',required=false)=>`<div><label for="f-${name}">${esc(label)}</label><select id="f-${name}" name="${name}" ${required?'required':''}><option value="">선택해 주세요</option>${Object.entries(options).map(([k,v])=>`<option value="${esc(k)}" ${value===k?'selected':''}>${esc(v)}</option>`).join('')}</select></div>`;
function questionFields(cat,answers={},required=true){return catalogData.services[cat].questions.map(([k,label,options])=>selectField('answer_'+k,label,options,answers[k]||'',required)).join('');}
function takeAnswers(data){const answers={};for(const key of Object.keys(data)){if(key.startsWith('answer_')){if(data[key])answers[key.slice(7)]=data[key];delete data[key];}}return answers;}
const originalCost=cost;
cost=async function(cat='logo',next=null,answers={}){
 await catalog();const result=Object.keys(answers).length?await post('/cost/'+cat+'/estimate',{answers}):await api('/cost/'+cat);
 const stats=p=>`<div class="price-three"><div><small>최저${p.max_open?' 구간':''}</small><strong>${won(p.min)}</strong></div><div><small>평균${p.max_open?' 약':''}</small><strong>${won(p.average)}</strong></div><div><small>${p.max_open?'높은 구간':'최고'}</small><strong>${won(p.max)}${p.max_open?' 이상':''}</strong></div></div>`;
 show('작업 비용, 기준을 보고 결정하세요',`<p>여기서 확인한 내용은 전문가에게 전달되지 않습니다.</p><label for="cost-category">알아볼 분야</label><select id="cost-category">${Object.entries(categories).map(([k,v])=>`<option value="${k}" ${k===cat?'selected':''}>${v}</option>`).join('')}</select><p>${esc(result.note)}</p>${result.own?`<section class="price-source"><h3>WakeAgain · 동일 조건 견적</h3>${stats(result.own)}<p>${result.own.requests}개 의뢰 · 전문가 ${result.own.experts}명 · 최근 ${result.own.period_days}일</p><small>${esc(result.own.basis)}</small><pre>${esc(result.conditions)}</pre></section>`:result.sources.map(s=>`<section class="price-source"><div class="row-head"><h3>${esc(s.platform)} 공개 안내</h3><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">출처 보기 ↗</a></div>${stats(s)}<p>${esc(s.note)}</p><small>확인 ${esc(s.checked)} · ${s.stale?'90일이 지나 재확인이 필요한 자료입니다.':'원문 안내 기준'} · VAT 포함 여부 미확인</small></section>`).join('')}<details class="scope-questions" ${Object.keys(answers).length?'open':''}><summary>내 작업 조건으로 확인하기</summary><form id="cost-form"><div class="form-grid">${questionFields(cat,answers)}</div><button class="button secondary">이 조건의 통계 확인</button></form><p class="subtle">자체 통계 전환 시험 기준: 동일 조건 의뢰 ${result.threshold}건, 전문가·고객 각각 5명 이상. 현재 ${result.counts.requests}건입니다. 표본이 부족하면 외부 분야별 안내를 표시합니다.</p></details>${result.offers?.length?`<details><summary>등록 전문가의 시작 금액</summary>${result.offers.map(o=>`<div class="cost-row"><b>${esc(o.title)}</b><strong>${won(o.price)}부터</strong><p>${esc(o.scope)}</p></div>`).join('')}</details>`:''}${err}<div class="app-actions"><button class="button secondary" data-close>비용만 확인하기</button><button class="button primary" id="continue-brief">${next?'확인하고 의뢰 전달하기':'의뢰 준비하기 →'}</button></div>`,'COST GUIDE');
 $('#cost-category').disabled=!!next;
 $('#cost-category').addEventListener('change',e=>run(()=>cost(e.target.value,next)));
 $('#cost-form').addEventListener('submit',e=>{e.preventDefault();const data=formData(e.currentTarget);run(()=>cost(cat,next,takeAnswers(data)),e.submitter);});
 $('#continue-brief').addEventListener('click',e=>run(()=>next?next():requireUser(()=>briefForm({category:cat,answers})),e.currentTarget));
};

briefForm=async function(data={},key=null){
 await catalog();const cat=data.category||'logo';
 if(!key&&!data.scope){
  show('의뢰 등록',`<p>필요한 작업을 적고 분야와 조건을 선택해 주세요.</p><form id="active-form"><div class="form-grid">${input('line','어떤 작업이 필요하세요?',data.title||'','text','required minlength="3" maxlength="500" placeholder="예: 새로 여는 카페 로고가 필요해요"')}${catSelect(cat)}</div><div id="guide-questions" class="form-grid">${questionFields(cat,data.answers||{})}${selectField('style','원하는 분위기',catalogData.styles,data.style||'any',true)}</div>${err}<div class="app-actions"><button class="button primary">의뢰 초안 정리하기 →</button></div></form>`,'BRIEF ASSISTANT');
  $('#f-category').addEventListener('change',e=>{$('#guide-questions').innerHTML=questionFields(e.target.value)+selectField('style','원하는 분위기',catalogData.styles,'any',true);});
  bindForm(async d=>{d.answers=takeAnswers(d);const result=await post('/brief-guide',d);await briefForm({...data,...result.brief});});return;
 }
 const scopeNote=category=>category==='website'?'디자인, 실제 제작·배포, 도메인·호스팅, 유지보수 중 필요한 범위를 의뢰서에 적어 주세요.':category==='sign'?'간판은 디자인 파일만 다룹니다. 제작·시공이 필요한지는 별도로 확인해 주세요.':'선택한 조건은 초안에 함께 저장됩니다. 납품 범위를 의뢰서에 적어 주세요.';
 show(key?'의뢰 초안 수정':'의뢰 내용 확인',`<p>자동 정리한 내용을 수정할 수 있습니다. 초안 저장만으로는 전문가에게 전달되지 않습니다.</p><form id="active-form"><div class="form-grid">${input('title','의뢰 제목',data.title||'','text','required minlength="3" maxlength="100"')}${catSelect(cat)}</div><div id="brief-conditions" class="form-grid">${questionFields(cat,data.answers||{})}${selectField('style','원하는 분위기',catalogData.styles,data.style||'any',true)}</div><div class="form-grid">${area('scope','필요한 작업과 납품 범위',data.scope||'','required minlength="20" maxlength="2400"')}${area('materials','준비된 자료와 부족한 자료',data.materials||'','required minlength="5" maxlength="2000" placeholder="상호명과 참고 사진은 준비됐고, 원본 로고는 없습니다."')}${input('budget','지출 가능한 예산 (원)',data.budget||'','number','required min="1" max="100000000"')}${input('deadline','희망 완료일',data.deadline||'','date','required')}${input('reference','참고한 작업',data.reference||'','text','maxlength="200"')}</div><p class="subtle" id="brief-scope-note">${scopeNote(cat)}</p>${err}<div class="app-actions"><button class="button primary">나만 보는 초안 저장 →</button></div></form>`,'REVIEW YOUR BRIEF');
 $('#f-category').addEventListener('change',e=>{$('#brief-conditions').innerHTML=questionFields(e.target.value)+selectField('style','원하는 분위기',catalogData.styles,'any',true);$('#brief-scope-note').textContent=scopeNote(e.target.value);toast('분야를 바꿨습니다. 본문의 작업 내용도 확인해 주세요.');});
 bindForm(async d=>{d.answers=takeAnswers(d);d.budget=Number(d.budget);const r=await api('/requests'+(key?'/'+key:''),{method:key?'PUT':'POST',body:d});toast('의뢰 초안을 저장했습니다.');await requestDetail(r.id);});
};

workForm=async function(key=''){
 if(!user.profile){await dashboard('profile');toast('전문가 소개를 먼저 저장해 주세요.');return;}
 const p=key?(await api('/my/portfolios')).find(x=>x.id===key):{};if(!p)throw Error('작업물을 찾을 수 없습니다.');
 let images=[...(p.images||(p.image?[p.image]:[]))];
 show(key?'작업물 수정':'좋은 작업을 보여주세요',`<section class="import-work"><h3>다른 곳에 올린 내 작업 가져오기</h3><p>공개된 제목·본문·이미지를 초안으로 가져옵니다. 사이트가 제공하는 정보에 따라 요약이나 일부 이미지만 가져올 수 있습니다.</p><label for="import-url">내 작업의 공개 링크</label><input id="import-url" type="url" maxlength="2000" placeholder="https://..."><label class="check"><input id="import-rights" type="checkbox">본인 작업이며 내용과 이미지를 재게시할 권한이 있습니다. 출처 링크가 필수인 자료는 제외합니다.</label><label class="check"><input id="import-replace" type="checkbox">작성 중인 제목·설명·이미지를 가져온 내용으로 교체합니다.</label><button id="import-work" class="button secondary">내 작업 가져오기</button><p id="import-status" role="status"></p></section><form id="active-form"><div class="form-grid">${input('title','작업 제목',p.title||'','text','required minlength="3" maxlength="100"')}${catSelect(p.category||user.profile.category)}<div class="full"><label for="work-images">작업 이미지 · 최대 8장, 장당 8MB</label><input id="work-images" type="file" multiple accept="image/jpeg,image/png,image/webp"><p class="subtle">첫 이미지가 대표 이미지입니다. 앞·뒤 버튼으로 순서를 바꿀 수 있습니다.</p><div id="image-editor" class="image-editor"></div><p id="upload-status" role="status"></p></div>${area('description','작업 설명',p.description||'','required minlength="10" maxlength="3000"')}${area('scope','본인이 수행한 범위·금액에 포함된 항목',p.scope||'','required minlength="5" maxlength="1000"')}${input('price','기본 범위 시작 금액 (선택)',p.price||'','number','min="0" max="100000000"')}</div><label class="check"><input name="published" type="checkbox" ${p.published===0?'':'checked'}>작업 모음에 공개하기</label><label class="check"><input type="checkbox" required>본인 작업이며 이미지와 내용의 공개 권한을 확인했습니다.</label>${err}<div class="app-actions"><button class="button primary" id="save-work">작업물 저장</button>${button('내 작업 목록','dashboard','portfolio')}</div></form>`,'YOUR PORTFOLIO');
 const paint=()=>{$('#image-editor').innerHTML=images.map((path,i)=>`<figure><img src="/api/upload-preview/${esc(path.split('/').pop())}" alt="${i+1}번째 작업 이미지"><figcaption>${i===0?'대표 이미지':(i+1)+'번째 이미지'}</figcaption><div><button type="button" data-image-move="${i}:-1" ${i===0?'disabled':''} aria-label="${i+1}번째 이미지를 앞으로">앞으로</button><button type="button" data-image-move="${i}:1" ${i===images.length-1?'disabled':''} aria-label="${i+1}번째 이미지를 뒤로">뒤로</button><button type="button" data-image-remove="${i}" aria-label="${i+1}번째 이미지 삭제">삭제</button></div></figure>`).join('');};paint();
 $('#image-editor').addEventListener('click',e=>{const move=e.target.dataset.imageMove,remove=e.target.dataset.imageRemove;if(move){const [i,n]=move.split(':').map(Number);[images[i],images[i+n]]=[images[i+n],images[i]];paint();}if(remove!==undefined){images.splice(Number(remove),1);paint();}});
 $('#work-images').addEventListener('change',e=>run(async()=>{
  const files=[...e.target.files];if(files.length+images.length>8)throw Error('이미지는 최대 8장까지 등록할 수 있습니다.');
  $('#save-work').disabled=true;$('#import-work').disabled=true;
  try{for(const f of files){$('#upload-status').textContent=f.name+' 업로드 중…';if(f.size>8*1024*1024)throw Error('각 이미지는 8MB 이하로 올려 주세요.');const form=new FormData();form.append('file',f);images.push((await api('/uploads',{method:'POST',body:form})).path);paint();}$('#upload-status').textContent='업로드했습니다. 저장 전에는 공개되지 않습니다.';}
  finally{$('#save-work').disabled=false;$('#import-work').disabled=false;$('#work-images').value='';}
 },e.target));
 $('#import-work').addEventListener('click',e=>run(async()=>{
  const status=$('#import-status');if(!$('#import-rights').checked)throw Error('본인 작업과 재게시 권한을 먼저 확인해 주세요.');
  if(!$('#import-url').value||!$('#import-url').checkValidity())throw Error('공개 작업 링크를 입력해 주세요.');
  if((images.length||$('#f-title').value||$('#f-description').value)&&!$('#import-replace').checked)throw Error('작성 중인 내용의 교체 여부를 확인해 주세요.');
  $('#save-work').disabled=true;$('#work-images').disabled=true;status.textContent='작업 정보를 가져오는 중입니다…';
  try{const r=await post('/portfolio-import',{url:$('#import-url').value,rights_confirmed:true});$('#f-title').value=r.title;$('#f-description').value=r.description;images=r.images;paint();status.textContent=`이미지 ${images.length}장과 초안을 가져왔습니다. 내용을 확인한 뒤 저장해 주세요. `+r.warnings.join(' ');$('#import-replace').checked=false;}
  catch(ex){status.textContent=ex.message+' 아래에서 직접 등록할 수 있습니다.';}
  finally{$('#save-work').disabled=false;$('#work-images').disabled=false;}
 },e.currentTarget));
 bindForm(async d=>{if(!images.length)throw Error('이미지를 한 장 이상 추가해 주세요.');d.images=images;d.image=images[0];d.price=Number(d.price||0);d.published=!!d.published;await api('/portfolios'+(key?'/'+key:''),{method:key?'PUT':'POST',body:d});await refreshWorks();toast('작업물을 저장했습니다.');await dashboard('portfolio');});
};

const baseDetail=detail;
detail=function(id){baseDetail(id);const p=realWorks.find(p=>p.id===id);if(!p)return;const el=$('.project-large-art');el.innerHTML=`<div class="work-gallery">${p.images.map((src,i)=>`<img src="${esc(src)}" alt="${esc(p.title)} · ${i+1}번째 이미지" loading="${i?'lazy':'eager'}">`).join('')}</div>`;};

const baseQuote=quoteForm;
let quoteTimer=null;
quoteForm=async function(invite='',template=null){
 let draft=null;if(invite)draft=await api('/invites/'+invite+'/quote-draft');
 await baseQuote(invite,template||(draft?{title:draft.title,scope:draft.scope,revisions:draft.revisions,days:draft.days,exclusions:draft.exclusions}:null));
 if(!invite)return;
 const box=document.createElement('section');box.className='information-box';box.innerHTML=`<h3>고객이 요청한 내용</h3><p class="preserve-lines">${esc(draft.brief.scope)}</p><p>예산 ${won(draft.brief.budget)} · 희망 완료일 ${esc(draft.brief.deadline)}</p><p>준비 자료: ${esc(draft.brief.materials)}</p><p class="subtle">의뢰 범위를 초안으로 채웠습니다. 견적 금액은 전문가가 직접 정해 주세요.</p>`;$('#active-form').before(box);
 if(draft.comparable){const check=document.createElement('label');check.className='check';check.innerHTML='<input name="scope_unchanged" type="checkbox">분야별 선택 조건과 같은 범위·수정 횟수로 견적을 냅니다. 익명 비용 통계에 포함합니다.';$('#active-form .app-actions').before(check);}
 $('#template-select')?.addEventListener('change',()=>{if($('#template-select').value){$('#f-title').value=draft.title;$('#f-scope').value=draft.scope+'\n\n저장한 견적서의 포함 범위 (이번 의뢰에 맞게 검토):\n'+$('#f-scope').value;}});
 clearInterval(quoteTimer);const form=$('#active-form');let lastInput=Date.now();form.addEventListener('input',()=>{lastInput=Date.now();});
 quoteTimer=setInterval(()=>{if(!form.isConnected||!form.closest('dialog').open){clearInterval(quoteTimer);return;}if(document.visibilityState==='visible'&&Date.now()-lastInput<90000)post('/invites/'+invite+'/quote-time',{seconds:15}).catch(()=>{});},15000);
};

const baseDashboard=dashboard;
dashboard=async function(tab='requests'){
 if(tab==='availability')return availabilityForm();
 if(tab==='settings')return notificationForm();
 if(tab==='admin')return adminPanel();
 await baseDashboard(tab);if(!user)return;
 $('.app-tabs')?.insertAdjacentHTML('beforeend',`<button data-action="dashboard" data-value="availability">작업 조건</button><button data-action="dashboard" data-value="settings">알림 설정</button>`);
 if(tab==='portfolio'&&user.profile?.accepting&&!(await api('/expert-preferences'))){const note=document.createElement('div');note.className='information-box';note.innerHTML=`<p>작업물은 바로 게시할 수 있습니다. 조건이 맞는 의뢰를 받으려면 시작 가능일과 지원 작업도 알려 주세요.</p>${button('작업 조건 설정','dashboard','availability')}`;$('.app-tabs')?.after(note);}
 const status=await api('/admin/status');if(status.admin)$('.app-tabs')?.insertAdjacentHTML('beforeend','<button data-action="dashboard" data-value="admin">운영 관리</button>');
};

async function availabilityForm(){
 await catalog();const p=await api('/expert-preferences')||{};
 const capabilities=Object.fromEntries(Object.entries(catalogData.services).flatMap(([cat,v])=>Object.entries(v.questions[0][2]).map(([k,label])=>[cat+':'+k,v.label+' · '+label])));
 const checks=(items,name,selected)=>Object.entries(items).map(([k,v])=>`<label class="check"><input type="checkbox" name="${name}" value="${k}" ${selected?.includes(k)?'checked':''}>${esc(v)}</label>`).join('');
 show('어떤 의뢰를 받을 수 있나요?',`<p>일정·지원 작업·스타일이 맞는 의뢰를 우선 전달합니다. 새 의뢰 받기는 ‘내 소개’에서 켜 주세요.</p><form id="active-form"><div class="form-grid">${input('available_from','작업 시작 가능일',p.available_from||new Date().toLocaleDateString('sv-SE'),'date','required')}${input('turnaround_days','통상 작업 기간 (달력일)',p.turnaround_days||'','number','required min="1" max="365"')}${input('capacity','동시에 응대할 의뢰 수',p.capacity||3,'number','required min="1" max="20"')}</div><h3>지원할 수 있는 작업</h3>${checks(capabilities,'capabilities',p.capabilities)}<h3>작업 가능한 분위기</h3>${checks(catalogData.styles,'styles',p.styles)}${err}<div class="app-actions"><button class="button primary">작업 조건 저장</button>${button('작업 공간','dashboard')}</div></form>`,'MATCH PREFERENCES');
 bindForm(async(d,form)=>{const fd=new FormData(form);d.capabilities=fd.getAll('capabilities');d.styles=fd.getAll('styles');d.turnaround_days=Number(d.turnaround_days);d.capacity=Number(d.capacity);await api('/expert-preferences',{method:'PUT',body:d});toast('작업 조건을 저장했습니다.');await dashboard('inbox');});
}

async function notificationForm(){
 const r=await api('/notification-preferences'),p=r.preferences;if(!r.email_ready){show('알림 설정',`<p>사이트 안의 새 의뢰·견적·메시지 알림은 계속 받을 수 있습니다.</p><p>이메일 알림은 준비 중입니다. 카카오 알림톡은 채널 연결 후 사용할 수 있습니다.</p><div class="app-actions">${button('카카오 알림톡','dashboard','alimtalk')}${button('작업 공간','dashboard')}</div>`,'NOTIFICATIONS');return;}const statuses={pending:'발송 대기',sending:'발송 중',sent:'발송됨',failed:'발송 실패',cancelled:'취소됨'};
 show('필요한 시간에 알려드릴게요',`<p>사이트 알림은 바로 도착합니다. 이메일은 선택한 시간과 요일에 발송합니다. 시간은 한국 기준입니다.</p>${r.development?'<div class="information-box">로컬 베타에서는 이메일을 실제 발송하지 않습니다. 아래에서 대기 상태를 확인할 수 있습니다.</div>':''}<form id="active-form"><label class="check"><input type="checkbox" name="email" ${p.email?'checked':''}>의뢰·견적·대화 이메일 알림 받기</label><div class="form-grid">${input('start','이메일 수신 시작 시각',p.start,'number','required min="0" max="23"')}${input('end','이메일 수신 종료 시각',p.end,'number','required min="0" max="23"')}</div><p class="subtle">시작과 종료 시각이 같으면 24시간, 종료 시각이 더 작으면 자정을 넘는 시간대입니다.</p><fieldset><legend>수신 요일</legend>${['월','화','수','목','금','토','일'].map((d,i)=>`<label class="check"><input type="checkbox" name="weekdays" value="${i}" ${p.weekdays.includes(i)?'checked':''}>${d}요일</label>`).join('')}</fieldset>${err}<div class="app-actions"><button class="button primary">알림 설정 저장</button>${button('작업 공간','dashboard')}</div></form><h3>최근 이메일 처리 상태</h3>${r.outbox.length?r.outbox.map(o=>`<article class="dashboard-row"><p>${esc(o.body)}</p><small>${statuses[o.status]} · 시도 ${o.attempts}회 · 예정 ${dates(o.due)}</small></article>`).join(''):'<p>이메일 알림 기록이 없습니다.</p>'}`,'NOTIFICATIONS');
 bindForm(async(d,form)=>{d.email=!!d.email;d.start=Number(d.start);d.end=Number(d.end);d.weekdays=new FormData(form).getAll('weekdays').map(Number);await api('/notification-preferences',{method:'PUT',body:d});toast('알림 설정을 저장했습니다.');await notificationForm();});
}

async function agreementPanel(key){
 const r=await api('/invites/'+key+'/agreement');
 show('계약 진행 여부 확인',`<p>대화 등으로 별도 계약에 합의한 경우에만 확인해 주세요. 이 체크로 계약이나 결제가 체결되지는 않습니다.</p><p>${r.mutual?'양쪽 모두 계약 진행을 확인했습니다.':'아직 양쪽의 확인이 모두 모이지 않았습니다.'}</p><form id="active-form"><label class="check"><input type="checkbox" name="confirmed" ${r.mine?'checked':''}>상대방과 실제 계약 진행에 합의했습니다.</label>${err}<div class="app-actions"><button class="button primary">내 확인 저장</button>${button('작업 공간','dashboard')}</div></form>`);
 bindForm(async d=>{await post('/invites/'+key+'/agreement',{confirmed:!!d.confirmed});await agreementPanel(key);});
}
const baseInvite=inviteDetail,baseRequest=requestDetail;
async function showConditions(b){if(!b)return;await catalog();const labels=catalogData.services[b.category].questions;const text=labels.filter(([k])=>b.answers?.[k]).map(([k,label,options])=>label+': '+options[b.answers[k]]).join('\n');const box=document.createElement('div');box.className='request-summary';box.textContent=text+'\n분위기: '+catalogData.styles[b.style||'any'];$('#app-content .request-summary')?.after(box);}
inviteDetail=async function(key){await baseInvite(key);const i=dashboardData.inbox.find(i=>i.id===key);await showConditions(i?.brief);if(i?.status==='selected')$('#app-content').insertAdjacentHTML('beforeend',button('계약 진행 여부 확인','agreement',key));};
requestDetail=async function(key){await baseRequest(key);const r=dashboardData.requests.find(r=>r.id===key);await showConditions(r?.data);const selected=r?.invites.find(i=>i.status==='selected');if(selected)$('#app-content').insertAdjacentHTML('beforeend',button('계약 진행 여부 확인','agreement',selected.id));};
actions.agreement=agreementPanel;
actions.request=v=>requestDetail(v);actions.invite=v=>inviteDetail(v);
actions['edit-brief']=v=>{const r=dashboardData.requests.find(r=>r.id===v);return briefForm(r.data,v);};
actions['copy-brief']=v=>briefForm(dashboardData.requests.find(r=>r.id===v).data);
actions['submit-request']=async v=>{if(!$('#submit-confirm').checked)throw Error('실제 견적 요청 의사를 확인해 주세요.');const r=dashboardData.requests.find(r=>r.id===v);await cost(r.data.category,async()=>{const result=await post('/requests/'+v+'/submit',{confirmed:true,cost_seen:true});toast(result.matched?result.matched+'명에게 작업 가능 여부를 요청했습니다.':'조건에 맞는 전문가를 기다립니다.');await requestDetail(v);},r.data.answers||{});};

async function adminPanel(){
 const r=await api('/admin'),m=r.metrics;
 const labels={users:'가입 회원',profiles:'전문가 소개 작성',publishers:'공개 작업 등록 회원',draft_clients:'의뢰 초안 작성 고객',submitted_clients:'실제 전달 고객',requests:'전달 의뢰',quoted_requests:'견적 도착 의뢰',selected_requests:'전문가 선택 의뢰',mutual_agreements:'양측 계약 진행 확인'};
 const ratio=(a,b)=>b?Math.round(a/b*100)+'%':'표본 없음';
 const row=(item,kind)=>`<article class="dashboard-row"><h3>${esc(item.title||item.name)}</h3><p class="preserve-lines">${esc(item.reason||item.body)}</p>${button('처리하기','resolve',kind+':'+item.id)}</article>`;
 show('운영 관리',`<h3>누적 이용 현황</h3><div class="metrics-grid">${Object.entries(labels).map(([k,label])=>`<div><small>${label}</small><strong>${m[k]}</strong></div>`).join('')}</div><p>가입 → 공개 등록 ${ratio(m.publishers,m.users)} · 소개 작성 → 공개 등록 ${ratio(m.publishers,m.profiles)}<br>초안 고객 → 실제 전달 ${ratio(m.submitted_clients,m.draft_clients)}<br>견적 도착 → 양측 계약 진행 확인 ${ratio(m.mutual_agreements,m.quoted_requests)}</p><p>견적 작성 중 활동 시간 중앙값: ${m.quote_active_seconds_median===null?'측정 자료 없음':m.quote_active_seconds_median+'초'} (${m.quote_timed_samples}건)</p><p class="subtle">기간이 다른 누적 집계의 단계별 비율입니다. 신규 기능 이전 시간은 제외합니다. 계약 진행은 양측 자기 신고이며 결제·매출·완료 실적이 아닙니다. 견적 작성 시간은 화면이 보이고 최근 90초 내 입력한 구간만 집계합니다.</p><h3>미처리 신고</h3>${r.reports.map(x=>row(x,'report')).join('')||'<p>미처리 신고가 없습니다.</p>'}<h3>미처리 문의</h3>${r.support.map(x=>row(x,'support')).join('')||'<p>미처리 문의가 없습니다.</p>'}<h3>최근 30일 작업 노출</h3>${r.exposures.map(x=>`<p>${esc(x.name)} · ${x.views}회 · 브라우저 ${x.visitors}개</p>`).join('')||'<p>노출 기록이 없습니다.</p>'}<small>작업 카드가 화면에 50% 이상 보인 경우, 브라우저·작업·날짜별 1회 집계합니다. 사람 수나 광고 검증 지표는 아닙니다.</small><h3>이메일 상태</h3>${r.emails.map(x=>`<p>${esc(x.status)}: ${x.n}</p>`).join('')||'<p>발송 기록이 없습니다.</p>'}${button('실패 메일 재시도','retry-emails')}<h3>외부 가격 근거 관리</h3>${r.sources.map(x=>`<article class="dashboard-row"><b>${esc(x.platform)} · ${categories[x.category]}</b><p>확인일 ${esc(x.checked)} · ${x.enabled?'표시 중':'비표시'}</p>${button('근거 수정','price-source',x.id)}</article>`).join('')}<h3>최근 처리 기록</h3>${r.history.map(x=>`<p>${dates(x.created)} · ${esc(x.kind)} · ${esc(x.resolution)}</p>`).join('')||'<p>처리 기록 없음</p>'}<div class="app-actions">${button('새로고침','dashboard','admin')}${button('작업 공간','dashboard')}</div>`,'OPERATIONS');
 actions.resolve=async value=>{const [kind,id]=value.split(':');show('접수 내용 처리',`<form id="active-form">${area('resolution','처리 결과·회원에게 전달할 안내','','required minlength="5" maxlength="1000"')}${kind==='report'?'<label class="check"><input name="hide" type="checkbox">신고된 작업물을 비공개 처리합니다.</label>':''}${err}<div class="app-actions"><button class="button primary">처리 결과 저장</button>${button('취소','dashboard','admin')}</div></form>`);bindForm(async d=>{await post('/admin/resolve',{kind,id,resolution:d.resolution,hide:!!d.hide});await adminPanel();});};
 actions['price-source']=async id=>{const source=r.sources.find(x=>x.id===id);show('공개 가격 근거 수정',`<p>원문을 직접 확인한 뒤 기록합니다. 원문에 없는 최저·평균·최고를 추정해 넣지 마세요.</p><form id="active-form"><div class="form-grid">${input('url','출처 URL',source.url,'url','required')}${input('checked','확인일',source.checked,'date','required')}${input('min','최저 안내값',source.min,'number','required min="0"')}${input('average','평균 안내값',source.average,'number','required min="0"')}${input('max','최고 구간 안내값',source.max,'number','required min="0"')}${area('note','단위·조건·한계',source.note,'required minlength="10" maxlength="1000"')}</div><label class="check"><input name="max_open" type="checkbox" ${source.max_open?'checked':''}>높은 구간이 ‘이상’으로 안내됨 (상한 아님)</label><label class="check"><input name="enabled" type="checkbox" ${source.enabled?'checked':''}>비용 안내에 표시</label>${err}<div class="app-actions"><button class="button primary">가격 근거 저장</button>${button('취소','dashboard','admin')}</div></form>`);bindForm(async d=>{for(const k of ['min','average','max'])d[k]=Number(d[k]);d.max_open=!!d.max_open;d.enabled=!!d.enabled;await api('/admin/price-source',{method:'PUT',body:{...source,...d}});await adminPanel();});};
}

// Measure cards actually seen, independent of ranking. Changing filters does not count again.
let visitor;try{visitor=localStorage.getItem('wa.visitor');if(!/^[a-f0-9]{32}$/.test(visitor||'')){visitor=Array.from(crypto.getRandomValues(new Uint8Array(16)),v=>v.toString(16).padStart(2,'0')).join('');localStorage.setItem('wa.visitor',visitor);}}catch{visitor=null;}
const seenWorks=new Set(),pendingViews=new Set();let viewTimer;
const observer=new IntersectionObserver(entries=>{for(const e of entries){const id=e.target.dataset.project;if(e.isIntersecting&&e.intersectionRatio>=.5&&realWorks.some(p=>p.id===id)&&!seenWorks.has(id)){seenWorks.add(id);pendingViews.add(id);}}clearTimeout(viewTimer);viewTimer=setTimeout(()=>{if(visitor&&pendingViews.size){const ids=[...pendingViews];pendingViews.clear();post('/exposures',{visitor,ids}).catch(()=>ids.forEach(id=>seenWorks.delete(id)));}},500);},{threshold:.5});
const baseRender=render;
render=function(){baseRender();observer.disconnect();$$('#project-grid [data-project]').forEach(el=>observer.observe(el));};

actions['retry-emails']=()=>confirmation('실패한 이메일을 다시 보낼까요?','수신 동의와 시간 설정을 다시 확인한 뒤 발송합니다.',async()=>{const r=await post('/admin/retry-emails');toast(r.queued+'건을 재시도 예약했습니다.');await adminPanel();});
render();

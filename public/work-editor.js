'use strict';
workForm=async function(key=''){
 const route='work/'+(key||'new');
 return page(route,async()=>{
  user=await api('/me');
  if(!key)post('/my/registration-start').catch(()=>{});
  const record=key?(await api('/my/portfolios')).find(p=>p.id===key):null;if(key&&!record)throw Error('작업물을 찾을 수 없습니다.');
  let draft=draftRead(route);
  let work=draft?.work||{title:record?.title||'',category:record?.category||user.profile?.category||'logo',description:record?.description||'',scope:record?.scope||'',price:record?.price||'',images:[...(record?.images||[])],name:user.name,bio:user.profile?.bio||''};
  let step=draft?.step??(key?1:0),method=draft?.method||'direct';
  const stash=()=>draftWrite(route,{work,step,method});
  function sync(){const form=$('#active-form');if(form)for(const name of ['title','category','description','scope','price','name','bio']){const control=form.elements.namedItem(name);if(control)work[name]=control.value;}stash();}
  function frame(title,body){
   show(title,`<ol class="editor-steps" aria-label="등록 진행 단계">${['등록 방법','작업 내용','확인·게시'].map((t,i)=>`<li ${i===step?'aria-current="step"':''}><span>${i+1}</span>${t}</li>`).join('')}</ol><p id="draft-status" class="draft-status" role="status">${draft?'이 기기에 저장한 초안을 불러왔습니다.':'이 기기에 자동 저장됩니다. · 최대 7일 · 로그아웃 시 삭제'}</p>${body}`,'PORTFOLIO');
   workspaceDraftFlush=sync;$('#active-form')?.addEventListener('input',sync);$('#active-form')?.addEventListener('change',sync);
  }
  function paint(){
   $('#image-editor').innerHTML=work.images.map((path,i)=>`<figure><img src="/api/upload-preview/${esc(path.split('/').pop())}" alt="작업 이미지 ${i+1}"><figcaption>${i===0?'대표 이미지':'이미지 '+(i+1)}</figcaption><div><button type="button" data-reorder="${i}:-1" ${!i?'disabled':''} aria-label="이미지 ${i+1} 앞으로">←</button><button type="button" data-reorder="${i}:1" ${i===work.images.length-1?'disabled':''} aria-label="이미지 ${i+1} 뒤로">→</button><button type="button" data-remove="${i}">삭제</button></div></figure>`).join('');
  }
  async function renderStep(){
   if(step===0){
    frame('작업물 등록',`<p>등록 방법을 선택해 주세요.</p><div class="entry-options"><button type="button" id="choose-import">${deskIcon("request")}<strong>링크로 가져오기</strong><p>다른 곳에 공개한 내 작업을 초안으로 가져옵니다.</p><b aria-hidden="true">↗</b></button><button type="button" id="choose-direct">${deskIcon("portfolio")}<strong>직접 등록하기</strong><p>작업 이미지와 설명으로 시작합니다.</p><b aria-hidden="true">↗</b></button></div><p class="subtle">공개 링크라도 사이트에 따라 일부 자료만 가져올 수 있습니다. 게시 전에 내용을 확인합니다.</p>`);
    for(const choice of ['import','direct'])$('#choose-'+choice).addEventListener('click',()=>{method=choice;step=1;stash();renderStep();});return;
   }
   if(step===1){
    frame(key?'작업물 수정':'작업 내용 입력',`${method==='import'?`<section class="import-work"><h3>내 작업 링크</h3><label for="import-url">공개된 작업 주소</label><input type="url" id="import-url" placeholder="https://…" maxlength="2000"><label class="check"><input type="checkbox" id="import-rights">본인 작업이며 이미지와 내용을 다시 게시할 권한이 있습니다. 출처 링크 유지가 필수인 자료는 제외합니다.</label><button class="button secondary" type="button" id="import-work">내용 가져오기</button><p id="import-status" role="status"></p></section>`:''}<form id="active-form"><div class="editor-section"><h3>작업 이미지</h3><label class="upload-drop" for="work-images"><strong>이미지 선택하기 ＋</strong><span>JPG · PNG · WebP / 최대 8장, 장당 8MB</span></label><input id="work-images" type="file" multiple accept="image/jpeg,image/png,image/webp"><div id="image-editor" class="image-editor"></div><p id="upload-status" role="status"></p></div><div class="form-grid">${input('title','작업 제목',work.title,'text','required minlength="3" maxlength="100" placeholder="예: 모루 카페 로고 디자인"')}${catSelect(work.category)}${area('description','작업 설명',work.description,'required minlength="10" maxlength="3000" placeholder="어떤 고객의 어떤 요청을 해결한 작업인가요?"')}${area('scope','직접 맡은 작업 범위',work.scope,'required minlength="5" maxlength="1000" placeholder="예: 로고 시안 2종, 최종 원본 제작"')}${input('price','이 범위의 시작 금액 · 선택',work.price,'number','min="0" max="100000000" placeholder="금액을 정하지 않았다면 비워 두세요"')}</div>${err}<div class="editor-actions"><button type="button" class="button secondary" id="editor-back">등록 방법</button><button class="button primary">확인·게시로 →</button></div></form>`);
    paint();
    $('#editor-back').addEventListener('click',()=>{sync();step=0;stash();renderStep();});
    $('#image-editor').addEventListener('click',e=>{const target=e.target.closest('button');if(!target||workspaceBusy)return;sync();if(target.dataset.reorder){const [i,d]=target.dataset.reorder.split(':').map(Number);[work.images[i],work.images[i+d]]=[work.images[i+d],work.images[i]];}else if(target.dataset.remove!==undefined)work.images.splice(Number(target.dataset.remove),1);paint();stash();});
    $('#work-images').addEventListener('change',e=>run(async()=>{
     const files=[...e.target.files];if(files.length+work.images.length>8)throw Error('이미지는 최대 8장입니다.');
     workspaceBusy=true;$('#active-form button[type="submit"], #active-form .editor-actions .primary').disabled=true;
     try{for(const file of files){$('#upload-status').textContent=file.name+' 업로드 중…';if(file.size>8*1024*1024)throw Error('각 이미지는 8MB 이하로 올려 주세요.');const body=new FormData();body.append('file',file);work.images.push((await api('/uploads',{method:'POST',body})).path);paint();stash();}$('#upload-status').textContent='업로드했습니다. 게시 전에는 공개되지 않습니다.';}
     finally{workspaceBusy=false;$('#active-form .editor-actions .primary').disabled=false;e.target.value='';}
    },e.target));
    $('#import-work')?.addEventListener('click',e=>run(async()=>{
     if(!$('#import-rights').checked)throw Error('재게시 권한을 확인해 주세요.');
     const url=$('#import-url');if(!url.value||!url.checkValidity())throw Error('공개 작업 주소를 확인해 주세요.');sync();
     if((work.title||work.description||work.images.length)&&!confirm('작성한 제목·설명·이미지를 가져온 내용으로 바꿀까요?'))return;
     workspaceBusy=true;$('#import-status').textContent='작업 정보를 가져오는 중입니다…';
     try{const result=await post('/portfolio-import',{url:url.value,rights_confirmed:true});work.title=result.title;work.description=result.description;work.images=result.images;$('#f-title').value=work.title;$('#f-description').value=work.description;paint();stash();$('#import-status').textContent=`이미지 ${work.images.length}장과 초안을 가져왔습니다. `+result.warnings.join(' ');}
     catch(ex){$('#import-status').textContent=ex.message+' 아래에서 직접 입력할 수 있습니다.';}
     finally{workspaceBusy=false;}
    },e.currentTarget));
    rawBindForm(async()=>{if(workspaceBusy)throw Error('업로드가 끝날 때까지 기다려 주세요.');sync();if(!work.images.length)throw Error('작업 이미지를 한 장 이상 올려 주세요.');step=2;stash();await renderStep();});return;
   }
   frame('공개 전에 한 번 확인하세요',`<div class="publish-preview"><img src="/api/upload-preview/${esc(work.images[0]?.split('/').pop()||'')}" alt="대표 이미지 미리보기"><div><small>${categories[work.category]} · 이미지 ${work.images.length}장</small><h3>${esc(work.title)}</h3><p class="preserve-lines">${esc(work.description)}</p><p><strong>작업 범위</strong><br>${esc(work.scope)}</p><p>${Number(work.price)?won(work.price)+'부터':'범위 확인 후 금액 협의'}</p></div></div><form id="active-form">${!user.profile?`<section class="editor-section"><h3>작업에 함께 표시할 소개</h3><p>이름과 소개만 입력하면 첫 작업을 게시할 수 있습니다. 일정은 나중에 설정하세요.</p>${input('name','표시 이름',work.name,'text','required minlength="2" maxlength="40"')}${area('bio','전문가 소개',work.bio,'required minlength="10" maxlength="1000" placeholder="예: 카페와 작은 브랜드의 로고를 디자인합니다."')}</section>`:`<p>게시자: <strong>${esc(user.name)}</strong></p>`}<label class="check"><input type="checkbox" required>본인 작업이며 이미지·내용의 공개 권한을 확인했습니다.</label><p class="subtle">공개하면 바로 작업 모음에 표시됩니다. 이후 수정하거나 비공개로 바꿀 수 있습니다.</p>${err}<div class="editor-actions"><button type="button" class="button secondary" id="editor-edit">내용 수정</button><button class="button secondary" type="submit" name="visibility" value="private">비공개로 저장</button><button class="button primary" type="submit" name="visibility" value="public">${key?'수정 내용 공개':'작업물 공개하기'} →</button></div></form>`);
   $('#editor-edit').addEventListener('click',()=>{sync();step=1;stash();renderStep();});
   rawBindForm(async(d,form,submitter)=>{
    if(workspaceBusy)return;workspaceBusy=true;
    try{sync();if(!user.profile){await api('/profile',{method:'PUT',body:{name:work.name,category:work.category,bio:work.bio,accepting:false}});user=await api('/me');}
    const published=submitter?.value!=='private';
    await api('/portfolios'+(key?'/'+key:''),{method:key?'PUT':'POST',body:{title:work.title,category:work.category,description:work.description,scope:work.scope,price:Number(work.price||0),images:work.images,image:work.images[0],published}});
    draftClear(route);await refreshWorks();enterWorkspace('workspace/portfolio');
    show(published?'작업물을 공개했습니다.':'비공개로 저장했습니다.',`<section class="publish-success"><span>등록 완료</span><h3>${esc(work.title)}</h3><p>${published?'작업 모음에 바로 반영했습니다. 수정도 언제든 가능합니다.':'내 작업물에서 이어 수정하고 공개할 수 있습니다.'}</p><div class="app-actions"><a class="button primary" href="#/workspace/portfolio">내 작업물 보기</a><a class="button secondary" href="#/work/new">다른 작업 등록</a></div></section><section class="next-step"><h3>의뢰를 받을 준비도 해볼까요?</h3><p>시작 가능일과 지원 작업을 설정한 뒤, 내 소개에서 ‘새 의뢰 받기’를 켜 주세요.</p><a class="text-button" href="#/workspace/availability">작업 조건 설정 →</a></section>`);
    }finally{workspaceBusy=false;}
   });
  }
  await renderStep();
 });
};

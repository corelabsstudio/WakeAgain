'use strict';
const beforePortfolioDetail=detail;
detail=function(id){
 beforePortfolioDetail(id);
 const p=works().find(w=>w.id===id);
 if(!p || (p.concept && id!=='website-moru'))return;
 const root=$('#project-content'),layout=$('.project-detail-layout',root),visual=$('.project-large-art',root),info=$('.project-info',root);
 root.classList.add('portfolio-detail');
 const sample=p.concept;
 const desktop=sample?$('.moru-site-preview',visual).outerHTML:null;
 const mobile=sample?$('.case-phone',visual).outerHTML:null;
 const images=sample?[]:(p.images?.length?p.images:[p.image]);
 const slides=sample?[
  {label:'홈페이지 시안',html:desktop,thumb:'assets/concepts/moru-interior.png'},
  {label:'모바일 시안',html:mobile,thumb:'assets/concepts/moru-interior.png'},
  {label:'메뉴 사진',html:'<img src="assets/concepts/moru-coffee.png" alt="메뉴 사진 콘셉트">',thumb:'assets/concepts/moru-coffee.png'}
 ]:images.map((src,i)=>({label:i===0?'대표 이미지':'작업 이미지 '+(i+1),src,thumb:src}));
 visual.innerHTML=`<section class="portfolio-gallery" aria-label="작업 포트폴리오"><div class="portfolio-gallery-head"><h2>포트폴리오</h2><button type="button" data-gallery-expand>크게 보기 ↗</button></div><div class="portfolio-stage" tabindex="0" aria-label="선택한 작업 이미지"></div><div class="portfolio-controls"><button type="button" data-gallery-prev aria-label="이전 작업 이미지">←</button><span role="status" aria-live="polite"></span><button type="button" data-gallery-next aria-label="다음 작업 이미지">→</button></div><div class="portfolio-thumbs">${slides.map((s,i)=>`<button type="button" data-gallery-index="${i}" aria-label="${esc(s.label)} 선택" aria-pressed="false"><img src="${esc(s.thumb)}" alt="" width="96" height="64"><span>${esc(s.label)}</span></button>`).join('')}</div></section>`;
 let index=0;
 const stage=$('.portfolio-stage',visual);
 function paint(){const s=slides[index];stage.innerHTML=s.html||`<img src="${esc(s.src)}" alt="${esc(p.name+' · '+s.label)}">`;stage.scrollTop=0;$('.portfolio-controls [role=status]',visual).textContent=`${s.label} · ${index+1} / ${slides.length}`;$('[data-gallery-prev]',visual).disabled=index===0;$('[data-gallery-next]',visual).disabled=index===slides.length-1;$$('[data-gallery-index]',visual).forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.galleryIndex)===index));}
 $('[data-gallery-prev]',visual).onclick=()=>{if(index>0){index--;paint();}};
 $('[data-gallery-next]',visual).onclick=()=>{if(index<slides.length-1){index++;paint();}};
 $$('[data-gallery-index]',visual).forEach(b=>b.onclick=()=>{index=Number(b.dataset.galleryIndex);paint();});
 stage.addEventListener('keydown',e=>{if(e.key==='ArrowRight'&&index<slides.length-1){e.preventDefault();index++;paint();}if(e.key==='ArrowLeft'&&index>0){e.preventDefault();index--;paint();}});
 $('[data-gallery-expand]',visual).onclick=()=>{
  if(!sample)return openImageViewer(images,p.name,p.description,index);
  const viewer=document.createElement('dialog');viewer.className='portfolio-preview-dialog';viewer.setAttribute('aria-label',slides[index].label+' 크게 보기');
  viewer.innerHTML=`<header><strong>${esc(slides[index].label)} · 콘셉트 예시</strong><button type="button" aria-label="미리보기 닫기">닫기 ×</button></header><div class="portfolio-preview-body">${slides[index].html}</div>`;
  document.body.append(viewer);const previous=document.activeElement;viewer.querySelector('button').onclick=()=>viewer.close();viewer.addEventListener('close',()=>{viewer.remove();previous?.focus({preventScroll:true});});viewer.showModal();
 };
 paint();
 const reference=sample?'moru coffee — 카페 홈페이지 제작 예시':p.name;
 const cta=sample?`data-brief="website" data-reference="${esc(reference)}"`:`data-direct="${esc(p.user_id)}" data-category="${esc(p.category)}" data-reference="${esc(reference)}"`;
 const canRequest=sample||p.accepting;
 info.innerHTML=`<h2>작업 조건</h2><p class="portfolio-price">${sample?'작업 범위 확인 후 견적':p.price?won(p.price)+'부터':'금액 협의'}</p><dl class="portfolio-terms"><div><dt>작업 범위</dt><dd>${sample?'반응형 홈페이지 1페이지 · 4개 구역':esc(p.scope)}</dd></div><div><dt>제작 기간</dt><dd data-work-period>${sample?'영업일 7~10일 (예시)':'일정 확인 후 협의'}</dd></div><div><dt>수정 조건</dt><dd>${sample?'합의한 범위 내 2회 (예시)':'견적서에서 확정'}</dd></div>${!sample?`<div><dt>의뢰 가능 여부</dt><dd>${p.accepting?'새 의뢰를 받고 있습니다':'현재 새 의뢰를 쉬고 있습니다'}</dd></div>`:''}</dl>${sample?'<p class="portfolio-extra">도메인·호스팅 이용료, 촬영, 관리 화면은 별도 협의합니다.</p>':''}<button type="button" class="button primary" ${cta} ${canRequest?'':'disabled'}>${sample?'이런 홈페이지 의뢰하기':canRequest?'이 전문가에게 의뢰하기':'현재 새 의뢰 마감'}</button><p class="example-info">의뢰 내용을 작성한 뒤 전달 전에 확인합니다.</p>${sample?'<p class="portfolio-disclosure">가상 카페의 콘셉트 작업입니다. 사진은 AI로 제작했으며 기간·수정 횟수는 조건 예시입니다.</p>':`<a class="portfolio-expert-link" href="/#/expert/${esc(p.user_id)}">${esc(p.expert_name)} 전문가 소개 →</a>`}`;
 const lower=document.createElement('div');lower.className='portfolio-lower';
 lower.innerHTML=`<section><h2>작업 설명</h2><p class="preserve-lines">${sample?'가상의 카페 moru coffee를 위한 홈페이지 구성입니다. 매장 분위기를 보여주는 첫 화면과 메뉴 소개, 모바일 화면을 제안합니다. 위 갤러리에서 각 시안을 선택하고 크게 볼 수 있습니다.':esc(p.description)}</p>${sample?'<dl class="portfolio-description-spec"><div><dt>구성 범위</dt><dd>매장 소개, 대표 메뉴, 공간 소개, 방문 안내</dd></div><div><dt>전달물 예시</dt><dd>PC·모바일 대응 페이지, 소스 파일, 내용 변경 안내서</dd></div></dl><details><summary>의뢰 전 준비할 자료</summary><p>상호·로고, 사용 가능한 매장·메뉴 사진, 메뉴 가격, 주소·영업시간과 참고 사이트를 준비해 주세요. 사진 촬영이나 문구 작성이 필요하면 의뢰에 함께 적어 주세요.</p></details>':''}</section>${sample?'<section><h2>콘셉트 예시 안내</h2><p>WakeAgain이 제작한 참고 시안입니다. 실제 전문가가 등록한 작업은 해당 전문가의 소개와 다른 포트폴리오가 이 위치에 표시됩니다.</p></section>':`<section class="portfolio-expert"><h2>전문가 소개</h2><h3>${esc(p.expert_name)}</h3><p class="preserve-lines">${esc(p.bio||'전문가 소개를 확인해 주세요.')}</p><a href="/#/expert/${esc(p.user_id)}">전체 프로필 보기 →</a></section><section class="portfolio-related"><h2>같은 전문가의 다른 작업</h2><p role="status">공개 작업을 불러오는 중입니다.</p></section>`}`;
 layout.after(lower);
 const mobileAction=document.createElement('div');mobileAction.className='portfolio-mobile-action';
 mobileAction.innerHTML=`<span>${sample?'웹페이지 제작 예시':p.price?won(p.price)+'부터':'범위 확인 후 견적'}</span><button type="button" class="button primary" ${cta} ${canRequest?'':'disabled'}>${canRequest?'의뢰 시작하기':'새 의뢰 마감'}</button>`;
 root.append(mobileAction);
 if(!sample){
  const related=$('.portfolio-related',lower);
  async function loadRelated(){
   try{
    const expert=await api('/experts/'+encodeURIComponent(p.user_id));if(!lower.isConnected)return;
    if(expert.turnaround_days)$('[data-work-period]',info).textContent=`통상 ${expert.turnaround_days}일 · 시작일 협의`;
    const others=expert.works.filter(w=>w.id!==p.id);
    related.innerHTML=`<h2>같은 전문가의 다른 작업 <small>${others.length}</small></h2>${others.length?`<div class="portfolio-related-grid">${others.map(w=>`<a href="/?work=${encodeURIComponent(w.id)}"><img src="${esc(w.image)}" alt="${esc(w.title)}" width="400" height="300" loading="lazy"><h3>${esc(w.title)}</h3><p>${esc(categories[w.category]||'포트폴리오')}</p></a>`).join('')}</div>`:'<p>아직 다른 공개 작업이 없습니다.</p>'}`;
   }catch{if(lower.isConnected){related.innerHTML='<h2>같은 전문가의 다른 작업</h2><p>작업을 불러오지 못했습니다.</p><button type="button" class="button secondary">다시 불러오기</button>';$('button',related).onclick=loadRelated;}}
  }
  loadRelated();
 }
};

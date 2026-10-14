(() => {
 'use strict';
 const config=window.AffiliateConfig,api=window.Affiliate,main=document.getElementById('main');
 let demo=false,category='전체',query='',linkFilter='all',spaceFilter='all',compare=[],priceFilter='all',timer;
 const safe=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const products=()=>demo?config.demoProducts:api.publicProducts(config).filter(p=>!(p.valueBasis||p.sourceKind==='manual_editorial')||Date.parse(p.expiresAt)>Date.now());
 const price=p=>p.price===null?'판매처에서 가격 확인':Number(p.totalPrice??p.price).toLocaleString('ko-KR')+'원'+((p.valueBasis||p.sourceKind==='manual_editorial')?' · 배송비 포함':' · 판매처 표시값')+' · '+safe(p.priceCheckedAt||'가격 확인일 미등록');
 function mediaURL(value){try{const base=document.querySelector('script[src*="config.js"]').src;const url=new URL(value,base);return ['https:','http:','file:'].includes(url.protocol)?url.href:'';}catch(_){return '';}}
 function message(text){clearTimeout(timer);document.getElementById('message').textContent=text;timer=setTimeout(()=>document.getElementById('message').textContent='',4500);}
 function art(p){
  if(p.imageUsageAllowed&&p.imagePath?.startsWith('/curation/assets/'))return '<div class="product-art original-product-photo"><img class="category-image" src="'+safe(p.imagePath)+'" alt="'+safe(p.name)+'" loading="lazy"></div>';
  if(p.textOnly)return '<div class="product-art text-only-art"><strong>'+safe(p.name)+'</strong><small>상품 사진 없이 소개합니다.</small></div>';
  const figures={tray:'<path d="M60 150l95-35 110 42-99 41z" fill="#89ab9a"/><path d="M60 150v26l106 48v-26z" fill="#719285"/><path d="M166 198l99-41v26l-99 41z" fill="#547b6d"/><path d="M82 153l73-26 83 30-73 28z" fill="#dbe9dc"/><path d="M118 155l40-13 40 16-40 13z" fill="#fafbf5"/>',pad:'<path d="M36 174l154-65 96 48-151 73z" fill="#82949d"/><path d="M36 174v9l99 56v-9z" fill="#607781"/><path d="M135 230l151-73v9l-151 73z" fill="#677f83"/><path d="M56 172l132-56 82 41-135 63z" fill="#bec8cc"/><path d="M95 160l59-26 42 24-57 24z" fill="#eef1ed"/>',stand:'<ellipse cx="161" cy="222" rx="68" ry="18" fill="#b7cbbb"/><path d="M102 212l73-28 43 27-73 29z" fill="#739986"/><path d="M145 202v-93l19-7v92z" fill="#547967"/><path d="M123 93l57-21 12 10v112l-57 21-12-9z" fill="#2c5047"/><path d="M131 101l52-19v100l-52 20z" fill="#ccdbce"/><path d="M140 110l34-12v39l-34 12z" fill="#e1dbee"/>'};
  return '<div class="product-art '+p.kind+'"><svg viewBox="0 0 320 280" role="img" aria-label="'+safe(p.name)+' 직접 만든 개념 일러스트"><ellipse cx="160" cy="215" rx="115" ry="20" fill="#355c4b" opacity=".07"/>'+figures[p.kind]+'</svg><small>개념 일러스트 · 실물 사진 아님</small></div>';
 }
 function disclosure(p){return '<p class="disclosure">'+safe(p.demo?'디자인 데모입니다. 이 상품은 제휴 승인 전이며 수수료가 발생하는 구매 링크가 연결되지 않았습니다.':p.disclosure||'제휴 관계 고지 준비 중 · 링크 비활성')+'</p>';}
 function externalButton(p){const state=api.linkState(p,config);return state.enabled?'<a class="button link-button" data-external="'+safe(p.id)+'" href="'+safe(state.url)+'" rel="sponsored noopener noreferrer">'+safe(p.merchant||'외부 판매처')+'에서 구매하기 ↗</a>':'<button class="button link-button" disabled>'+safe(state.reason)+'</button>';}
 function sourceLink(p){try{const url=new URL(p.sourceUrl);if(url.protocol==='https:'&&!url.username&&!url.password)return '<a class="text-link" href="'+safe(url.href)+'" target="_blank" rel="noopener noreferrer">정보 출처 보기 · 제휴 링크 아님 ↗</a>';}catch(_){}return '<p>출처 링크 등록 전</p>';}
 function empty(){return '<section class="empty"><h2>연결할 상품을 준비하고 있습니다.</h2><p>제휴 프로그램과 상품별 추적 링크를 확인한 뒤 소개하겠습니다.</p>'+(config.published?'<a class="button" href="#guide">제휴 및 구매 안내</a>':'<button data-demo>디자인 데모 살펴보기</button>')+'</section>';}
 function storyShelf(){const items=[['work','작업 공간','일하는 자리를 위한 선택을 살펴보세요.','workspace'],['home','생활 공간','매일 쓰는 공간의 선택을 살펴보세요.','home']];return '<section class="discovery editorial-discovery" aria-label="공간별 둘러보기">'+items.map(([space,title,description,key])=>'<button data-space="'+space+'"><div class="product-art"><img class="category-image" src="'+safe(mediaURL(config.media.categories[key]))+'" alt="'+title+' 풍경" loading="lazy"><small class="brand-image-label">AI 생성 공간 연출 이미지</small></div><div><h3>'+title+' →</h3><p>'+description+'</p></div></button>').join('')+'</section>';}


function shoppingCheckedDate(p) {
 const value=p.infoCheckedAt||p.lastVerifiedAt;
 if(!value||!Number.isFinite(Date.parse(value)))return '확인 시각 미확인';
 return '확인 '+new Date(value).toLocaleString('ko-KR',{timeZone:'Asia/Seoul',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false})+' KST';
}
function shoppingAmount(p) {
 return p.price===null?'판매처에서 가격 확인':Number(p.totalPrice??p.price).toLocaleString('ko-KR')+'원';
}

function shoppingCategoryButtons() {
  const categories = [
    ['전체', '전체'],
    ['식품·생수', '식품·생수'],
    ['생활용품', '생활용품'],
    ['주방용품', '주방용품']
  ];

  return categories.map(function (entry) {
    const value = entry[0];
    const label = entry[1];
    const active = category === value || (value === '전체' && !category);
    return '<button class="category-button' + (active ? ' is-active' : '') + '" type="button" data-category="' + safe(value) + '" aria-pressed="' + String(active) + '">' + safe(label) + '</button>';
  }).join('');
}

function shoppingVisibleProducts() {
  const normalizedQuery = String(query || '').trim().toLocaleLowerCase('ko-KR');

  return products().filter(function (p) {
    if (!demo && p.demo) return false;
    if (category && category !== '전체' && p.category !== category) return false;

    if (normalizedQuery) {
      const searchable = [p.name, p.cardName, p.options, p.coreSpec, p.category]
        .filter(Boolean)
        .join(' ')
        .toLocaleLowerCase('ko-KR');
      if (!searchable.includes(normalizedQuery)) return false;
    }

    if (spaceFilter && spaceFilter !== 'all' && p.space !== spaceFilter) return false;

    if (priceFilter && priceFilter !== 'all') {
      const amount = Number(p.totalPrice != null ? p.totalPrice : p.price);
      if (priceFilter === 'under20' && !(amount < 20000)) return false;
      if (priceFilter === '20to50' && !(amount >= 20000 && amount < 50000)) return false;
      if (priceFilter === 'over50' && !(amount >= 50000)) return false;
    }

    return true;
  });
}

function home() {
  const visibleProducts = shoppingVisibleProducts();
  const cards = visibleProducts.length
    ? visibleProducts.map(card).join('')
    : '<p class="catalog-empty">'+(config.collectionStatus?'현재 조건에 맞는 상품이 없습니다.':'상품 정보를 불러오고 있습니다.')+'</p>';

  return '' +
    '<section class="shopping-home" aria-labelledby="shopping-home-title">' +
      '<div class="shopping-home-heading">' +
        '<div>' +
          '' +
          '<h1 id="shopping-home-title">상품 둘러보기</h1>' +
        '</div>' +
        '<p class="shopping-home-summary">생활에 필요한 상품을 사진·옵션·가격 중심으로 살펴보세요.</p>' +
      '</div>' +
      '<p class="affiliate-notice">이 페이지에는 토스쇼핑 쉐어링크 제휴 상품이 포함되어 있으며, 구매 시 일정액의 수수료를 제공받을 수 있습니다.</p>' +
      '<p class="purchase-guide">상품 상세에서 제휴 판매처로 이동합니다. 구매와 결제는 외부 판매처에서 진행됩니다.</p>' +
      '<form id="home-search" class="home-search" role="search">' +
        '<label class="sr-only" for="home-query">상품 검색</label>' +
        '<input id="home-query" name="query" type="search" value="' + safe(query || '') + '" placeholder="상품명이나 옵션을 검색하세요" autocomplete="off">' +
        '<button type="submit">검색</button>' +
      '</form>' +
      '<nav class="category-nav" aria-label="상품 카테고리">' + shoppingCategoryButtons() + '</nav>' +
    '</section>' +
    '<section id="catalog" class="shopping-catalog" aria-label="상품 목록">' +
      '<div class="catalog-heading">' +
        '<h2>상품 목록</h2>' +
        '<p>상품 사진과 정확한 옵션, 표시 가격을 먼저 비교해 보세요.</p>' +
      '</div>' +
      '<div class="product-grid">' + cards + '</div>' +
      '<p class="catalog-note">표시 가격과 쿠폰·할인·배송 조건은 확인 시점의 정보입니다. 최종 가격과 적용 조건은 외부 판매처의 결제 화면에서 확인하세요. 선정 설명과 단점은 각 상품 상세에서 제공합니다.</p>' +
    '</section>';
}

function card(p) {
  const detailHref = '#product/' + safe(p.id);
  const compared = compare.includes(p.id);

  return '' +
    '<article class="product-card" data-product-id="' + safe(p.id) + '">' +
      '<a class="product-main" href="' + detailHref + '">' +
        art(p) +
        '<div class="product-body">' +
          '<p class="category">' + safe(p.category) + (p.demo ? ' / 디자인 데모' : '') + '</p>' +
          '<h3>' + safe(p.cardName || p.name) + '</h3>' +
          '<p class="price">' + shoppingAmount(p) + '</p><p class="shipping-label">배송비 포함 표시 총액</p>' +
          '<p class="options">' + safe(p.options || p.coreSpec || '옵션 확인 전') + '</p>' +
          '<p class="price-condition">' + safe(p.priceConditions || '가격과 혜택 조건은 결제 전에 확인하세요.') + '</p>' +
          '<p class="checked-date">' + shoppingCheckedDate(p) + '</p>' +
        '</div>' +
      '</a>' +
      disclosure(p) +
      '<div class="card-actions">' +
        '<a class="detail-button" href="' + detailHref + '">상품 보기</a>' +
        '<button class="compare-button" type="button" data-compare="' + safe(p.id) + '" aria-pressed="' + String(compared) + '">' + (compared ? '비교에서 빼기' : '비교에 담기') + '</button>' +
      '</div>' +
    '</article>';
}
 function listing(){const list=products().filter(p=>(spaceFilter==='all'||p.space===spaceFilter)&&(category==='전체'||p.category===category)&&(priceFilter==='all'||(p.price!==null&&((priceFilter==='under20'&&(p.totalPrice??p.price)<20000)||(priceFilter==='20to50'&&(p.totalPrice??p.price)>=20000&&(p.totalPrice??p.price)<50000)||(priceFilter==='over50'&&(p.totalPrice??p.price)>=50000))))&&[p.name,p.category,p.summary,p.options,p.coreSpec].join(' ').toLowerCase().includes(query.toLowerCase())&&(linkFilter==='all'||(linkFilter==='available'&&api.linkState(p,config).enabled)||(linkFilter==='pending'&&!api.linkState(p,config).enabled)));const categories=['전체',...new Set(products().map(p=>p.category))];return '<div class="page-head"><span class="eyebrow">상품 큐레이션</span><h1>배송비까지 따져 골라보기.</h1><p>'+(demo?'데모 데이터입니다. 구매 또는 수익 연결이 없습니다.':'승인된 제휴 상품을 확인한 뒤 연결합니다.')+'</p><label for="search">상품 검색</label><input id="search" type="search" value="'+safe(query)+'" placeholder="상품명 또는 종류" autocomplete="off"></div><details class="filter-panel"'+(window.matchMedia('(min-width:601px)').matches?' open':'')+'><summary>카테고리·연결 상태 필터</summary><div class="filters" role="group" aria-label="카테고리">'+categories.map(c=>'<button data-category="'+safe(c)+'" class="'+(category===c?'active':'')+'" aria-pressed="'+(category===c)+'">'+safe(c)+'</button>').join('')+'</div><label for="link-filter">연결 상태</label><select id="link-filter"><option value="all"'+(linkFilter==='all'?' selected':'')+'>전체</option><option value="available"'+(linkFilter==='available'?' selected':'')+'>판매처 이동 가능</option><option value="pending"'+(linkFilter==='pending'?' selected':'')+'>연결 확인 필요</option></select><label for="price-filter">가격대</label><select id="price-filter"><option value="all"'+(priceFilter==='all'?' selected':'')+'>전체 가격</option><option value="under20"'+(priceFilter==='under20'?' selected':'')+'>2만원 미만</option><option value="20to50"'+(priceFilter==='20to50'?' selected':'')+'>2만–5만원</option><option value="over50"'+(priceFilter==='over50'?' selected':'')+'>5만원 이상</option></select><button data-reset>필터 초기화</button></details><p class="pending-list">'+(spaceFilter==='all'?'':spaceFilter==='work'?'작업 공간 · ':'생활 공간 · ')+'검색 결과 '+list.length+'개</p><section class="catalog-section">'+(list.length?'<div class="cards">'+list.map(card).join('')+'</div>':products().length?'<section class="empty"><h2>검색 결과가 없습니다.</h2><p>검색어를 줄이거나 다른 카테고리를 선택해 보세요.</p><button data-reset>검색 초기화</button></section>':empty())+'</section>';}
 function valueEvidence(p){if(!p.valueBasis)return '';const labels={sales_count:'판매 수량',sales_rank:'판매 순위',official_popularity_rank:'공식 인기 순위'};return '<section class="value-evidence"><h2>가성비를 확인한 기준</h2><p>'+safe(p.valueBasis)+' · '+Number(p.unitPrice).toLocaleString('ko-KR')+'원 / '+safe(p.unit)+'</p><p>상품가 '+Number(p.price).toLocaleString('ko-KR')+'원 + 배송비 '+Number(p.shipping).toLocaleString('ko-KR')+'원 · '+safe(p.options)+'</p><h3>판매·인기 근거</h3><p>'+safe(labels[p.popularity.kind])+' '+safe(p.popularity.value)+' · '+safe(p.popularity.period)+' · 확인 '+safe(p.popularity.checkedAt)+'</p><a class="text-link" href="'+safe(p.popularity.sourceUrl)+'" target="_blank" rel="noopener noreferrer">근거 출처 ↗</a><p>리뷰 누적 수를 판매 수량으로 바꾸지 않습니다. 이 사이트 전체 최저가나 자체 판매 순위를 뜻하지 않습니다.</p><h3>같은 상품의 비교 조건</h3>'+p.comparisons.map(q=>'<p>'+safe(q.option)+' · '+safe(q.quantity)+safe(q.unit)+' · 배송비 포함 '+Number(q.price+q.shipping).toLocaleString('ko-KR')+'원 · 확인 '+safe(q.checkedAt)+' <a class="text-link" href="'+safe(q.sourceUrl)+'" target="_blank" rel="noopener noreferrer">출처 ↗</a></p>').join('')+'<h3>품질·반품 확인</h3><p>'+safe(p.quality.returnSummary)+'</p><p>'+safe(p.quality.riskSummary)+'</p><a class="text-link" href="'+safe(p.quality.sourceUrl)+'" target="_blank" rel="noopener noreferrer">조건 출처 ↗</a></section>';}
 function detailContent(p){return '<div class="breadcrumb"><a href="#catalog">상품 목록</a><span>/</span>'+safe(p.category)+'</div><section class="detail">'+art(p)+'<div class="detail-info"><span class="eyebrow">'+safe(p.category)+(p.demo?' / 디자인 데모':'')+'</span><h1>'+safe(p.name)+'</h1><p class="price">'+price(p)+'</p><p>'+safe(p.summary)+'</p><dl><dt>옵션</dt><dd>'+safe(p.options||'판매처에서 확인')+'</dd><dt>규격·재질</dt><dd>'+safe(p.coreSpec||'확인된 정보 등록 전')+'</dd><dt>판매처</dt><dd>'+safe(p.merchant||'제휴 연결 준비 중')+'</dd><dt>링크 상태</dt><dd>'+safe(api.linkState(p,config).reason)+'</dd></dl>'+disclosure(p)+externalButton(p)+'<button class="compare-button" data-compare="'+p.id+'">'+(compare.includes(p.id)?'비교에서 빼기':'비교에 담기')+'</button><p class="stock-note">가격·재고·주문·배송·교환·반품은 외부 판매처의 조건을 확인하세요. 실제 책임 범위는 연결된 프로그램 조건에 맞춰 안내합니다.</p></div></section><section class="details-grid"><div><h2>선정 이유와 확인할 점</h2><dl><dt>추천 대상</dt><dd>'+safe(p.recommendedFor||'규격·사용 환경 확인 후 안내')+'</dd><dt>맞지 않는 경우</dt><dd>'+safe(p.notFor||'규격·사용 조건 확인 전')+'</dd><dt>선정 근거</dt><dd>'+safe(p.selectionReason||'검토 중 · 제휴 상품 승인 전')+'</dd></dl></div><div><h2>출처와 확인</h2><dl><dt>확인일</dt><dd>'+safe(p.infoCheckedAt||'정보 확인일 등록 전')+'</dd><dt>정보 출처</dt><dd>'+safe(p.sourceName||'조사 자료 확인 전')+'</dd></dl>'+sourceLink(p)+'<p>실물 체험, 평점, 판매량을 확인하지 않은 상태에서 추천 성능이나 후기를 주장하지 않습니다.</p><h3>공식 사양</h3><p>'+safe(p.officialSpecs||'제조사·공식 판매처의 사양 확인 후 등록합니다. 조사 전달값과 공식 사양을 구분합니다.')+'</p></div></section>';}
 function manualEvidence(p){return '<section class="manual-editorial"><span class="eyebrow">WAKEAGAIN · 편집자 설명</span><h2>수량과 쓸 곳부터 따져보세요.</h2><div class="manual-facts"><div><h3>배송비 포함 기준</h3><p class="unit-price">'+Number(p.unitPrice).toLocaleString('ko-KR',{maximumFractionDigits:2})+'원 / '+safe(p.unit)+'</p><p>'+safe(p.shippingNote)+'</p><p class="price-condition">'+safe(p.priceConditions)+'</p></div><div><h3>비교할 때 볼 점</h3><p>'+safe(p.comparisonNote)+'</p></div><div><h3>구매 전 확인할 점</h3><p>'+safe(p.notFor)+'</p><p>실물 체험과 품질·효능 검증을 거친 후기가 아닙니다. 동일 상품의 시장 최저가를 보증하지 않습니다.</p></div></div><p>확인 '+safe(p.infoCheckedAt)+' · 가격·재고 확인은 24시간 동안만 유효하게 취급합니다. 쿠폰, 배송 지역, 결제 시점에 따라 최종 금액이 달라질 수 있습니다.</p><details><summary>판매자가 제공한 원본 상품 이미지</summary><p>아래 자료는 판매자 제공 원본으로, WakeAgain 편집자 설명과 구분합니다. 크롭·합성·번역·문구 삽입을 하지 않았습니다.</p>'+(p.detailImagePaths||[]).map(src=>'<img class="original-detail-image" src="'+safe(src)+'" alt="'+safe(p.name)+' 판매자 제공 상세 이미지" loading="lazy">').join('')+'</details></section>';}
 function detail(p){const content=detailContent(p);return (p.sourceKind==='manual_editorial'?content.replace('<p class="price">'+price(p)+'</p>','<p class="price">'+price(p)+'</p><p class="price-condition">'+safe(p.priceConditions)+'</p>'):content)+(p.sourceKind==='manual_editorial'?manualEvidence(p):valueEvidence(p));}
 function comparison(){const list=api.compareProducts(products(),compare);if(!list.length)return '<div class="page-head"><h1>상품 비교</h1></div><section class="empty"><h2>비교할 상품이 없습니다.</h2><p>목록에서 비교에 담기를 선택하세요. 최대 3개를 함께 볼 수 있습니다.</p><a class="button" href="#catalog">상품 둘러보기</a></section>';const fields=[['종류',p=>p.category],['옵션',p=>p.options||'확인 전'],['가격',price],['판매처',p=>p.merchant||'연결 준비 중'],['링크',p=>api.linkState(p,config).reason]];return '<div class="page-head"><h1>나란히 살펴보기.</h1><p>'+(demo?'디자인 데모 비교입니다. 제휴 상품 또는 구매 가능한 상품이 아닙니다.':'판매처의 최신 정보와 함께 비교하세요.')+'</p></div><div class="compare-scroll"><table class="compare-table"><thead><tr><th scope="col">비교 항목</th>'+list.map(p=>'<th scope="col"><a href="#product/'+p.id+'">'+safe(p.name)+'</a></th>').join('')+'</tr></thead><tbody>'+fields.map(([label,value])=>'<tr><th scope="row">'+label+'</th>'+list.map(p=>'<td>'+safe(value(p))+'</td>').join('')+'</tr>').join('')+'<tr><th scope="row">제휴 고지</th>'+list.map(p=>'<td>'+disclosure(p)+externalButton(p)+'<button class="compare-button" data-compare="'+p.id+'">비교에서 빼기</button></td>').join('')+'</tr></tbody></table></div>';}
 function automationStatus(){const status=config.collectionStatus||{};return '<section class="value-method"><h2>상품 연결 상태</h2><p>자동 수집 '+(status.collectionEnabled?'켜짐':'꺼짐')+' · 자동 게시 '+(status.autoPublish?'켜짐':'꺼짐')+' · API 연결 소스 '+Number(status.connectedSources||0)+'개</p><p>실제 연결 전에는 상품이 자동 검색·게시되지 않습니다. 승인된 자료를 먼저 검증합니다.</p>'+(config.providers||[{id:'naver',reason:'상품·데이터 사용 범위와 발급 링크 확인 대기'},{id:'coupang',reason:'최종 승인 및 API 접근 확인 대기'},{id:'toss',reason:'연동 대상 제외'}]).map(p=>'<p><strong>'+safe(p.id)+'</strong> · '+safe(p.reason)+'</p>').join('')+'</section>';}
 function guide(){return '<section class="value-method"><h2>가성비 선정 기준</h2><p>수동 소개 상품은 판매처 화면에서 옵션·표시 가격·배송 조건·제휴 링크를 확인하고, 구성 수량과 용도, 불편한 점을 직접 정리합니다. 서로 다른 상품의 구성 비교는 동일 SKU 가격 비교와 구분합니다. 동일 SKU의 두 판매처 비교가 없는 상품에는 시장 최저가를 표시하지 않습니다. 리뷰 수는 판매량이 아닙니다. 근거 없는 할인율·최저가·베스트셀러 표시를 만들지 않습니다.</p><p>출처 이용권·이미지 사용권·발급 제휴 링크가 확인되지 않거나 가격·재고 확인 기한이 지나면 공개 대상에서 제외합니다.</p></section>'+automationStatus()+'<div class="page-head"><h1>구매와 제휴 안내.</h1><p>WakeAgain은 상품을 소개하고 비교한 뒤 판매처로 연결하는 사이트입니다.</p></div><div class="guide-grid"><section class="guide-card"><h2>외부 판매처에서 구매</h2><p>상품 정보와 판매처의 최신 가격·재고를 확인한 다음, 발급·검증된 제휴 링크를 통해 판매처로 이동합니다.</p><p>WakeAgain은 고객 주문이나 결제 정보를 수집하지 않습니다. 주문·결제·배송·교환·반품은 판매처의 안내와 연결된 제휴 프로그램 조건을 확인해야 합니다.</p></section><section class="guide-card"><h2>수수료 관계 고지</h2><p>제휴 링크가 활성화된 상품에는 해당 링크를 통한 구매와 운영자의 수수료 관계를 표시합니다. 실제 프로그램에서 요구하는 문구를 상품별로 등록합니다.</p><p>'+(api.publicProducts(config).some(p=>api.linkState(p,config).enabled)?'상품별 고지를 확인한 뒤 연결된 판매처에서 구매하세요.':'현재 판매처로 이동할 수 있는 검증된 제휴 링크가 없습니다.')+' 일반 판매처 URL을 제휴 링크로 표시하지 않습니다.</p></section><section class="guide-card"><h2>링크 상태</h2><p>발급 링크 검증, 승인 판매처 주소, 추적 정보, 마지막 확인 시점 및 가격 정보의 확인 기한을 확인합니다. 만료·품절·확인 전 상태에서는 이동 버튼이 비활성입니다.</p><p>이 검사는 설정값 검증입니다. 실제 판매처 재고나 추적 귀속은 별도 확인이 필요합니다.</p></section><section class="guide-card">'+(config.published?'<h2>상품 정보 표기</h2><p>선정 이유, 확인할 점, 정보 출처와 확인일을 함께 안내합니다. 확인하지 않은 후기·평점·인기 순위를 표시하지 않습니다.</p><p>상품 정보는 확인된 출처를 기준으로 안내합니다.</p>':'<h2>디자인 데모</h2><p>오너클랜 상품 3개는 화면 검수용 데이터입니다. 제휴 승인, 수수료 계약, 판매처 연결 또는 실물 사진 사용 허가가 확인된 상품이 아닙니다.</p><p>기본 목록에는 표시하지 않으며 직접 만든 개념 일러스트만 사용합니다.</p>')+'</section></div>';}
 function render(){let route=location.hash.slice(1)||'home';if(['work','works','portfolio','requests','dashboard','login','account','examples'].includes(route)){history.replaceState(null,'',location.pathname+location.search+'#home');route='home';}let content,title;if(route==='home'){content=home();title='상품 큐레이션';}else if(route==='catalog'){content=listing();title='상품 목록';}else if(route==='compare'){content=comparison();title='상품 비교';}else if(route==='guide'){content=guide();title='이용 안내';}else if(route.startsWith('product/')){const p=products().find(p=>p.id===route.split('/')[1]);if(p){content=detail(p);title=p.name;}}if(!content){content='<section class="empty"><h1>상품을 찾을 수 없습니다.</h1><a class="button" href="#catalog">상품 목록으로</a></section>';title='찾을 수 없음';}main.innerHTML=content;document.getElementById('demo-toggle').hidden=config.published;document.querySelector('footer .tiny').textContent=config.published?'외부 판매처의 최신 거래 조건을 확인하세요. 수수료 관계는 상품별로 안내합니다.':'제휴 프로그램 승인·상품별 추적 링크 확인 전 내부 초안입니다.';document.title='WakeAgain · '+title;document.getElementById('compare-count').textContent=compare.length;const connected=api.publicProducts(config).some(p=>api.linkState(p,config).enabled);document.querySelector('.draft-notice>span').textContent=config.published?(connected?'상품 큐레이션 · 제휴 관계는 상품별 안내':'가성비 큐레이션 · 제휴 연결 대기'):'제휴 큐레이션 · 적용 전 초안 · '+(connected?'승인된 링크 연결 검수 중':'실제 제휴 링크 미연결');}
 function toggleDemo(){if(config.published)return;demo=!demo;category='전체';query='';linkFilter='all';spaceFilter='all';compare=[];document.getElementById('demo-banner').hidden=!demo;document.getElementById('demo-toggle').setAttribute('aria-pressed',String(demo));document.getElementById('demo-toggle').textContent=demo?'데모 닫기':'디자인 데모 보기';render();}
 document.getElementById('demo-toggle').addEventListener('click',toggleDemo);
 main.addEventListener('click',event=>{const external=event.target.closest('[data-external]');if(external){const p=products().find(p=>p.id===external.dataset.external);const state=p&&api.linkState(p,config);if(!state?.enabled){event.preventDefault();render();message('링크 상태가 변경돼 연결을 중단했습니다.');}return;}const button=event.target.closest('button');if(!button)return;if(button.hasAttribute('data-demo'))toggleDemo();else if(button.hasAttribute('data-reset')){query='';category='전체';linkFilter='all';spaceFilter='all';priceFilter='all';render();}else if(button.dataset.budget){priceFilter=button.dataset.budget;spaceFilter='all';category='전체';query='';location.hash='catalog';render();}else if(button.dataset.space){spaceFilter=button.dataset.space;category='전체';query='';if(location.hash!=='#catalog')location.hash='catalog';else render();}else if(button.dataset.category){category=button.dataset.category;if(location.hash!=='#catalog')location.hash='catalog';else render();}else if(button.dataset.compare){const id=button.dataset.compare;if(compare.includes(id))compare=compare.filter(x=>x!==id);else if(compare.length<3)compare.push(id);else{message('최대 3개 상품을 비교할 수 있습니다.');return;}render();}});
 main.addEventListener('change',event=>{if(event.target.id==='price-filter'){priceFilter=event.target.value;render();}else if(event.target.id==='link-filter'){linkFilter=event.target.value;render();}});
 main.addEventListener('input',event=>{if(event.target.id==='search'){query=event.target.value;const caret=event.target.selectionStart;render();const input=document.getElementById('search');input.focus();try{input.setSelectionRange(caret,caret);}catch(_){}}});
 main.addEventListener('submit',event=>{if(event.target.id==='home-search'){event.preventDefault();query=document.getElementById('home-query').value;spaceFilter='all';category='전체';location.hash='catalog';render();}});
 window.addEventListener('hashchange',()=>{render();main.focus({preventScroll:true});window.scrollTo(0,0);});
 async function refreshCatalog(){if(location.protocol==='file:')return;try{const response=await fetch('/api/curation/catalog',{cache:'no-store'});if(!response.ok)return;const payload=await response.json();if(!Array.isArray(payload.products)||!Array.isArray(payload.programs))return;const changed=JSON.stringify(config.products)!==JSON.stringify(payload.products)||JSON.stringify(config.collectionStatus)!==JSON.stringify(payload.status);config.products=payload.products;config.programs=payload.programs;config.collectionStatus=payload.status;config.providers=payload.providers;if(changed)render();}catch(_){/* Keep the last valid snapshot; expiry still disables links and removes offers. */}}
 render();refreshCatalog();if(location.protocol!=='file:')setInterval(refreshCatalog,60000);
})();

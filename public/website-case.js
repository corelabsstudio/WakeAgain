'use strict';
// One editorial sample; real portfolios continue to use their own uploaded data.
const beforeWebsiteCase=detail;
detail=function(id){
 beforeWebsiteCase(id);
 if(id!=='website-moru')return;
 $('#project-title').textContent='카페의 분위기부터 방문 안내까지, 한 페이지에';
 document.title='카페 홈페이지 제작 예시 — WakeAgain';
 $('#project-content .project-subtitle').textContent='웹페이지 제작 · moru coffee · 콘셉트 예시';
 const visual=$('#project-content .project-large-art');
 visual.innerHTML=`<div class="moru-site-preview" aria-label="moru coffee 홈페이지 디자인 시안"><div class="moru-preview-nav"><b>moru<span>coffee</span></b><span>Our story &nbsp; Menu &nbsp; Visit</span></div><div class="moru-photo-hero"><img src="assets/concepts/moru-interior.png" alt="나무 가구와 햇빛이 드는 가상 카페의 매장 사진" width="1536" height="1024"><div><small>A LITTLE PAUSE, EVERY DAY.</small><strong>당신의 하루에,<br>잠깐의 모루.</strong><span>익숙한 골목에서 만나는 새로운 여유</span><p>우리의 공간을 만나보세요 ↗</p></div></div><div class="moru-preview-story"><small>OUR KIND OF DAY</small><h2>좋은 커피와<br>느린 시간을 내어드립니다.</h2><p>분주한 하루에 잠시 놓아두는 작은 쉼표.<br>커피 한 잔의 온도와 창가의 빛을 천천히 즐겨보세요.</p></div><div class="moru-menu-feature"><img src="assets/concepts/moru-coffee.png" alt="원목 테이블 위 라테와 크루아상 콘셉트 사진" width="1536" height="1024" loading="lazy"><div><small>COFFEE & A LITTLE MORE</small><h3>매일의 한 잔,<br>정성껏.</h3><p>고소한 커피와 갓 구운 빵.<br>단순하지만 오래 생각나는 조합.</p><span>메뉴 이야기 ↗</span></div></div><div class="moru-preview-foot"><b>moru coffee</b><span>동네의 속도로, 당신의 취향으로.</span></div></div>`;
 visual.insertAdjacentHTML('beforeend',`
 <div class="website-case">
  <p class="case-caption">가상 카페의 홈페이지 디자인 예시입니다. 매장·메뉴 사진은 AI로 제작했으며 실제 납품 사례가 아닙니다.</p>
  <section class="case-intro"><span class="small-label">이런 홈페이지를 만듭니다</span><h2>사진만 예쁜 페이지에서<br>방문하고 싶은 가게로.</h2><p>처음 방문하는 손님은 메뉴와 가격, 영업시간, 찾아가는 방법을 먼저 확인합니다. 카페의 분위기를 전하면서도 필요한 정보를 쉽게 찾을 수 있도록 구성했습니다.</p></section>
  <section><h2>한 페이지에 담을 내용</h2><div class="case-scope-list">
   <article><h3>첫인상</h3><p>매장 대표 사진과 짧은 소개. 메뉴를 보거나 위치를 확인하는 버튼을 배치합니다.</p></article>
   <article><h3>메뉴</h3><p>대표 메뉴 사진, 이름, 가격과 설명을 정리합니다. 이 예시는 대표 메뉴 6개를 기준으로 합니다.</p></article>
   <article><h3>공간 소개</h3><p>매장 사진과 함께 좌석, 주차, 반려동물 동반 등 방문 전 알아둘 정보를 안내합니다.</p></article>
   <article><h3>오시는 길</h3><p>주소·영업시간·휴무일과 지도 앱 연결, 전화 문의 버튼을 제공합니다.</p></article>
  </div></section>
  <section class="case-mobile-section"><div><span class="small-label">휴대폰에서도 편하게</span><h2>길을 찾는 순간까지<br>짧고 명확하게.</h2><p>작은 화면에서는 내용을 세로로 정리하고, 메뉴와 위치 버튼을 손쉽게 누를 수 있도록 배치합니다.</p><p class="case-caption">모바일 화면 구성 예시입니다.</p></div><div class="case-phone" aria-label="모바일 화면 구성 예시"><div class="case-phone-nav">moru coffee <span>☰</span></div><div class="case-phone-hero"><img src="assets/concepts/moru-interior.png" alt="모바일 첫 화면의 카페 사진" loading="lazy"><span>매일 지나던 길에서</span><strong>잠시 머무는<br>커피 한 잔.</strong><p>오늘의 여유를 모루에서 만나세요.</p></div><div class="case-phone-links"><span>메뉴 보기 ↗</span><span>위치 확인 ↗</span></div><div class="case-phone-menu"><img src="assets/concepts/moru-coffee.png" alt="모바일 메뉴 소개 사진" loading="lazy"><small>OUR COFFEE</small><b>오늘은 어떤 커피인가요?</b><p>아메리카노 <span>4,500</span></p><p>카페라테 <span>5,000</span></p></div><p class="case-phone-note">화면 구성용 가상 메뉴·가격</p></div></section>
  <section><h2>기본 제작 범위</h2><dl class="case-spec"><div><dt>페이지</dt><dd>스크롤형 소개 페이지 1개 · 위 4개 구역</dd></div><div><dt>화면 대응</dt><dd>PC·태블릿·휴대폰 화면에 맞춘 반응형 구현</dd></div><div><dt>기본 설정</dt><dd>페이지 제목·설명, 공유 이미지, 이미지 대체 설명</dd></div><div><dt>연결</dt><dd>전화·지도·기존 SNS 또는 예약 서비스 링크</dd></div><div><dt>전달물</dt><dd>홈페이지 소스 파일과 내용 변경 안내서</dd></div><div><dt>게시 지원</dt><dd>의뢰인 소유 도메인·호스팅 연결 지원</dd></div></dl><p class="case-caption">회원가입, 결제, 자체 예약 시스템, 관리자 편집 화면은 이 예시의 기본 범위에 포함되지 않습니다. 필요한 경우 의뢰 단계에서 별도로 정합니다.</p></section>
  <section><h2>이렇게 진행합니다</h2><ol class="case-process"><li><h3>자료와 작업 범위 확인</h3><p>매장 소개, 메뉴, 사진, 원하는 분위기를 함께 정리합니다.</p></li><li><h3>디자인 확인</h3><p>첫 화면과 모바일 배치를 확인하고 수정 사항을 모읍니다.</p></li><li><h3>제작과 사용 확인</h3><p>페이지를 구현하고 휴대폰 표시, 지도·전화 링크를 확인합니다.</p></li><li><h3>최종 확인과 전달</h3><p>문구와 이미지를 확인한 뒤 파일을 전달하고 게시를 돕습니다.</p></li></ol></section>
  <section><h2>시작 전에 준비해 주세요</h2><ul class="case-preparation"><li>상호·로고와 매장 소개 문구</li><li>사용 권한이 있는 매장·메뉴 사진</li><li>메뉴 가격, 주소, 영업시간, 문의 연락처</li><li>원하는 분위기의 참고 사이트와 필요한 기능</li></ul><p>사진 촬영과 소개 문구 작성이 필요하다면 의뢰에 함께 적어 주세요. 작업 범위와 비용이 달라질 수 있습니다.</p></section>
  <section class="case-faq"><h2>자주 궁금한 내용</h2><details><summary>제작 기간은 얼마나 걸리나요?</summary><p>이 구성은 자료 확정 후 영업일 7~10일을 가정한 예시입니다. 실제 기간은 담당 전문가의 일정과 수정 범위에 따라 견적서에서 확정합니다.</p></details><details><summary>완성 후 메뉴나 사진을 바꿀 수 있나요?</summary><p>소스 파일과 변경 안내서를 전달하는 구성입니다. 직접 로그인해 편집하는 관리 화면이나 정기 수정 서비스가 필요하면 별도 범위로 요청해 주세요.</p></details><details><summary>도메인과 호스팅 비용도 포함되나요?</summary><p>이 예시에는 연결 지원만 포함됩니다. 도메인·호스팅 구매 및 갱신 비용은 사용하는 서비스에 따라 별도로 발생합니다.</p></details><details><summary>수정은 어떻게 진행하나요?</summary><p>이 예시는 합의한 디자인 안에서 의견을 모아 2회 수정하는 조건입니다. 페이지 추가나 방향 변경은 작업 전에 별도로 협의합니다.</p></details></section>
 </div>`);
 const info=$('#project-content .project-info');
 info.innerHTML=`<span class="small-label">웹페이지 제작 예시</span><h2 class="case-order-title">우리 가게를 소개하는<br>첫 홈페이지</h2><p>매장 소개부터 메뉴·방문 안내까지.<br>PC와 휴대폰에서 편하게 보는 한 페이지.</p><dl class="case-order-spec"><div><dt>구성</dt><dd>1페이지 · 4개 구역</dd></div><div><dt>예시 일정</dt><dd>자료 확정 후 영업일 7~10일</dd></div><div><dt>예시 수정</dt><dd>합의한 범위 내 2회</dd></div></dl><p class="case-price-note">금액은 작업 범위 확인 후 견적</p><button class="button primary" data-brief="website" data-reference="moru coffee — 카페 홈페이지 제작 예시">이런 홈페이지 의뢰하기 ↗</button><p class="example-info">원하는 내용으로 의뢰 초안을 작성합니다. 전문가에게 전달하기 전에 검토할 수 있습니다.</p><p class="case-sample-note">콘셉트 예시입니다. 기간·수정 조건은 구성 예시이며 실제 계약 조건이 아닙니다.</p>`;
};

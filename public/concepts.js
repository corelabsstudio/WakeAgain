const categories = {"logo": "로고 디자인", "sign": "간판 디자인", "detail": "상세페이지", "print": "명함·인쇄물", "banner": "배너·SNS", "ppt": "PPT 디자인", "package": "패키지 디자인", "ui": "웹·앱 UI", "website": "웹페이지 제작", "illustration": "캐릭터·일러스트"};
const concepts = [
  {id:'ott',category:'logo',name:'ott. — 일상에 작은 개성을 더하는 로고',brand:'ott.',description:'매일 사용하는 생활용품 브랜드를 가정한 로고 콘셉트입니다. 짧고 둥근 글자와 대비되는 작은 점으로, 패키지에서도 알아보기 쉬운 인상을 만들었습니다.',deliverables:['기본 로고와 단색 버전','브랜드 컬러 가이드','인쇄·웹용 파일'],keywords:'생활용품 브랜드 브랜딩 보라 보라색 심볼 로고'},
  {id:'moru',category:'sign',name:'moru — 골목에서 만나는 카페의 첫인상',brand:'moru coffee',description:'나무 창틀과 밝은 벽에 어울리는 작은 카페의 간판 콘셉트입니다. 금속 소재 위에 간결한 글자를 배치해 매장의 분위기와 자연스럽게 이어지도록 구성했습니다.',deliverables:['외관 적용 시안','간판 디자인 파일','제작 시 확인할 색상·비율 가이드'],keywords:'카페 커피 가게 매장 간판 상호'},
  {id:'still',category:'detail',name:'still — 매일의 루틴을 담은 상세페이지',brand:'still.',description:'스킨케어 상품의 차분한 인상을 살린 상세페이지 콘셉트입니다. 제품 이미지와 짧은 설명을 함께 배치하고, 필요한 정보를 순서대로 읽을 수 있게 구성했습니다.',deliverables:['상세페이지 구성안','PC·모바일용 디자인','이미지 납품 파일'],keywords:'화장품 스킨케어 뷰티 상세페이지 제품 쇼핑몰'},
  {id:'form',category:'logo',name:'form — 형태에서 출발한 브랜드 아이덴티티',brand:'form',description:'가구와 생활 소품 브랜드를 가정한 워드마크입니다. 글자의 선과 바닥선을 연결해 안정적인 형태를 만들고, 작은 인쇄물에서도 쓰기 편한 조합을 제안합니다.',deliverables:['브랜드 워드마크','흑백·컬러 조합','기본 사용 가이드'],keywords:'가구 인테리어 소품 초록 녹색 로고 브랜드'},
  {id:'ondo',category:'detail',name:'ONDO — 한 잔의 여유를 전하는 상품 소개',brand:'ONDO',description:'일상에서 편하게 즐기는 차 브랜드의 상품 소개 콘셉트입니다. 종이와 찻잔의 질감이 보이는 이미지, 충분한 여백과 짧은 문장으로 상품의 분위기를 전달합니다.',deliverables:['상품 소개 구성안','상세페이지 디자인','모바일용 이미지 파일'],keywords:'식품 차 티 tea 패키지 상품 상세페이지'}
];
function artwork(id) {
  if(extraArt[id]) return extraArt[id];
  if (id === 'ott') return '<div class="artwork art-ott"><div class="art-top"><span>OTT. EVERYDAY OBJECTS</span><span>BRAND IDENTITY</span></div><strong class="ott-logo">ott<i>·</i></strong><div class="art-bottom"><span>ordinary things,<br>thoughtfully made.</span><span class="dot-palette"><i></i><i></i><i></i></span></div></div>';
  if (id === 'moru') return '<div class="artwork art-photo"><img src="assets/moru.webp" alt="moru 카페의 금속 간판 콘셉트" loading="lazy"><span class="photo-label">MORU COFFEE / SIGN DESIGN</span></div>';
  if (id === 'still') return '<div class="artwork art-still"><div class="still-page"><span class="still-wordmark">still.</span><h4>조금 더 단순한,<br>매일의 루틴.</h4><p>피부에 닿는 순간부터<br>가볍고 편안하게.</p><span class="page-rule"></span><small>YOUR DAILY ESSENTIALS</small></div><img src="assets/still.webp" alt="스킨케어 제품과 소개 문구를 배치한 상세페이지 콘셉트" loading="lazy"></div>';
  if (id === 'form') return '<div class="artwork art-form"><div class="form-top"><span>FORM & FUNCTION</span><span>IDENTITY STUDY</span></div><div class="form-frame"></div><div class="form-wordmark"><b>form</b></div><div class="form-bottom"><span>Objects for a considered life.</span><span>F / F</span></div></div>';
  return '<div class="artwork art-ondo"><div class="ondo-copy"><b>ONDO</b><span>오늘의 온도,<br>한 잔의 차.</span><small>TEA FOR EVERYDAY</small></div><img src="assets/ondo.webp" alt="차 패키지 사진과 제목으로 구성한 ONDO 상품 소개 콘셉트" loading="lazy"></div>';
}

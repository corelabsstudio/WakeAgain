/**
 * WakeAgain i18n — KO / EN localization.
 * data-i18n="key" · data-i18n-html · data-money-krw · WakeAgainI18n.t / setLang / formatMoney
 */
(function (global) {
  var STORAGE_LANG = "wa_lang";
  var STORAGE_CUR = "wa_currency";

  var STR = {
    ko: {
      "nav.market": "마켓플레이스",
      "nav.home": "홈",
      "nav.buyers": "구매 안내",
      "nav.showcase": "자랑하기",
      "nav.guide": "이용안내",
      "nav.metrics": "숫자로 보기",
      "nav.login": "로그인",
      "nav.app": "앱 설치",
      "nav.list": "내 프로젝트 올리기",
      "nav.list_short": "올리기",
      "nav.site": "사이트",
      "nav.logout": "로그아웃",
      "nav.profile": "내 정보",
      "nav.notif": "알림",
      "nav.fees": "수수료",
      "nav.interest": "관심 등록하기",
      "nav.more_market": "마켓플레이스 보기",
      "nav.account": "내 계정",
      "skip": "본문으로 건너뛰기",
      "doc.title": "WakeAgain — 프로젝트에 두 번째 기회를 주세요.",
      "hero.badge": "잠든 프로젝트 장터",
      "hero.title1": "멈춰버린 프로젝트에",
      "hero.title2": "숨을 불어넣다.",
      "hero.sub": "데모 있는 중단 프로젝트를 사고파는 장터.<br />입찰 → 결제 → 이전 · 등록 무료.",
      "hero.cta_main": "내 프로젝트는 얼마일까?",
      "hero.cta_sub": "30초 무료 · 시작가 힌트",
      "hero.cta_benefit": "",
      "hero.stat_projects": "올라온 프로젝트",
      "hero.stat_interest": "관심 있어요",
      "hero.stat_free": "올리는 비용",
      "hero.stat_free_val": "무료",
      "hero.stats_note": "",
      "live.price": "현재 입찰가",
      "live.time": "남은 시간",
      "live.progress": "시작가 · 입찰자 수",
      "live.ecg": "VITAL · 살아 있음",
      "live.toast": "방금 입찰 · 보기",
      "hub.eyebrow": "원하시는 곳으로",
      "hub.title": "길게 읽지 말고, 갈 곳만 고르세요",
      "hub.market_k": "사기",
      "hub.market_t": "마켓 둘러보기",
      "hub.market_d": "데모·가격 공개 · 입찰 · 결제",
      "hub.sell_k": "팔기",
      "hub.sell_t": "프로젝트 올리기",
      "hub.sell_d": "등록 무료 · 팔리면 수수료 10%",
      "hub.guide_k": "안내",
      "hub.guide_t": "이용·거래 가이드",
      "hub.guide_d": "판매·구매·사기예방법 · 별도 페이지",
      "shots.eyebrow": "앱 화면",
      "shots.title": "글보다 화면이 먼저",
      "shots.lead": "마켓 · 매물 상세 · 올리기. 실제 WakeAgain 화면입니다.",
      "shots.cap1": "마켓 · 가격 공개",
      "shots.cap2": "상세 · 입찰 · 관심",
      "shots.cap3": "올리기 · 등록 무료",
      "problem.title": "세상 밖으로 못 나온 프로젝트들",
      "problem.one": "출시 전에 멈춘 코드가 많습니다. 쓸모없어서가 아니라, 시간·홍보·타이밍이 안 맞았을 때가 많아요.",
      "problem.p1": "매일 수많은 프로젝트가 만들어집니다.",
      "problem.p2": "많은 제품들이 세상 밖으로 나오지 않습니다.",
      "problem.p3": "그들이 쓸모없어서가 아닙니다.",
      "problem.p4": "이는 인생이 변하거나, 시간이 없거나, 마케팅이 일어나지 않았기 때문입니다.",
      "problem.bridge": "그래도 문제는 남습니다. 구체적으로는 이런 상황입니다.",
      "problem.c1_t": "시간은 썼는데 수익은 0",
      "problem.c1_p": "서버·도메인 비용만 나가고 더 하기도 어렵습니다.",
      "problem.c1_p_short": "서버·도메인 비용만 나가고 더 하기도 어렵습니다.",
      "problem.c2_t": "팔 곳이 애매함",
      "problem.c2_p": "커뮤니티 글은 채팅만 오고 가격·이전 절차가 없습니다.",
      "problem.c2_p_short": "커뮤니티 글은 채팅만 오고 가격·이전 절차가 없습니다.",
      "problem.c3_t": "사고 싶어도 비교 불가",
      "problem.c3_p": "아이디어만 있는 것과 돌아가는 데모가 섞여 고르기 어렵습니다.",
      "problem.c3_p_short": "아이디어만 있는 것과 돌아가는 데모가 섞여 고르기 어렵습니다.",
      "buyers.eyebrow": "구매할 때",
      "buyers.title": "0부터 다시 만들기 전에,<br /><span class=\"grad\">초안을 찾으세요</span>.",
      "buyers.lead": "주말 몇 주를 또 쓰기 전에, 데모 있는 초안을 사는 편이 빠를 수 있습니다. 구매자 추가 수수료 없음.",
      "buyers.lead_short": "주말 몇 주를 또 쓰기 전에, 데모 있는 초안을 사는 편이 빠를 수 있습니다. 구매자 추가 수수료 없음.",
      "buyers.safe_badge": "안전결제",
      "buyers.safe_title": "PG 결제 · 확인 후 이전",
      "buyers.safe_body": "낙찰 후 PG 결제 → 확인 후 이전 → 인수. 사는 분은 합의 가격만, 수수료 10%는 판매자.",
      "buyers.safe_s1": "낙찰 후 결제",
      "buyers.safe_s2": "확인 → 이전",
      "buyers.safe_s3": "인수 · 확정",
      "buyers.safe_s4": "판매자 정산",
      "buyers.build_label": "직접 만들기",
      "buyers.build_t": "들인 시간 대비 결과물이 과연 괜찮을까요?",
      "buyers.build_1": "MVP만 잡아도 보통 수 주",
      "buyers.build_2": "배포·결제·디테일에서 또 막힘",
      "buyers.build_3": "기회비용이 “공짜”처럼 안 보임",
      "buyers.buy_label": "WakeAgain에서 사기",
      "buyers.buy_t": "실행 가능한 것부터 시작",
      "buyers.buy_1": "데모·가격·입찰 수 공개",
      "buyers.buy_2": "구매자 수수료 없음 (판매자 10%)",
      "buyers.buy_3": "가격 쓰기 → 결제 → 인수",
      "buyers.why_title": "왜 여기서 사나",
      "buyers.m1_t": "시간 절약",
      "buyers.m1_p": "아이디어만 있는 문서가 아니라, 우선 돌아가는 화면·데모가 있는 매물을 모읍니다. “다시 8~12주”를 아끼는 선택지입니다.",
      "buyers.m2_t": "비교 가능한 가격",
      "buyers.m2_p": "지금 얼마인지, 입찰자가 몇 명인지 사이트에 들어온 누구나 볼 수 있어요. 숨은 DM 호가가 아닙니다.",
      "buyers.m3_t": "구매자 수수료 0",
      "buyers.m3_p": "팔리면 판매자 쪽 10%입니다. 구매자는 합의(낙찰) 가격만. 가격 쓰기·관심 등록도 무료입니다.",
      "buyers.m4_t": "안전결제 절차",
      "buyers.m4_p": "PG 결제 확인 전 이전 금지, 인수 확정(또는 48시간 자동 확정) 후 정산. 신원(Lv)·신고도 함께. 보증·보험은 아니지만 혼자 직거래보다 단계가 분명합니다.",
      "buyers.rank_title": "살수록 보이는 구매자 뱃지",
      "buyers.rank_lead": "구경만 하는 사람과, 실제로 사서 끝낸 사람은 다릅니다. 구매가 <strong>성사될수록</strong> 다른 유저·판매자에게 보이는 배지가 올라갑니다. 「헤비 구매자」는 허세가 아니라 <strong>성사 기록</strong>입니다.",
      "buyers.rank_scout_b": "구매 준비 중",
      "buyers.rank_scout_n": "성사 0건",
      "buyers.rank_scout_p": "관심 등록·입찰 시작. 첫 성사부터 배지가 붙습니다.",
      "buyers.rank_starter_b": "첫 구매 완료",
      "buyers.rank_starter_n": "성사 1건+",
      "buyers.rank_starter_p": "입찰 내역·프로필에 「첫 구매 완료」 배지.",
      "buyers.rank_regular_b": "단골 구매자",
      "buyers.rank_regular_n": "성사 3건+",
      "buyers.rank_regular_p": "성사 건수 공개 · 반복 구매 신호.",
      "buyers.rank_heavy_b": "헤비 구매자",
      "buyers.rank_heavy_n": "성사 5건+",
      "buyers.rank_heavy_p": "강조 배지. 판매자에게 “실제로 사는 사람”으로 보입니다.",
      "buyers.rank_whale_b": "파워 바이어",
      "buyers.rank_whale_n": "성사 10건+",
      "buyers.rank_whale_p": "최고 구매 배지 · 프로필·입찰에서 가장 눈에 띕니다.",
      "buyers.rank_note": "배지는 성사(구매 완료) 횟수 기준 · 미입금 이력이 있으면 주의 표시가 붙을 수 있습니다. 신용 점수·Lv(자격)과 별개이며 보증·보험이 아닙니다.",
      "buyers.note": "통신판매중개 장터 · 결제 → 이전 → 인수. 자세한 내용은 이용약관.",
      "buyers.cta_interest": "관심 등록하기",
      "buyers.cta_market": "마켓 둘러보기",
      "svc.title": "이용 방법",
      "svc.lead": "등록·관심·입찰 무료. 낙찰 후 PG 결제. 안 내면 다음 사람에게 넘어갈 수 있어요.",
      "svc.lead_short": "등록·관심·입찰 무료. 낙찰 후 PG 결제. 안 내면 다음 사람에게 넘어갈 수 있어요.",
      "svc.1_t": "올리기",
      "svc.1_p": "데모·시작가 등록 · 형식 확인 1~2일 · 판매 수수료 10%",
      "svc.1_p_short": "데모·시작가 등록 · 형식 확인 1~2일 · 판매 수수료 10%",
      "svc.2_t": "가격 쓰기",
      "svc.2_p": "공개 가격·남은 시간 보고 입찰 · 낙찰 후 빠르게 결제",
      "svc.2_p_short": "공개 가격·남은 시간 보고 입찰 · 낙찰 후 빠르게 결제",
      "svc.3_t": "확인 후 이전",
      "svc.3_p": "데모 확인 → 결제 확인 뒤 코드·계정 이전 → 인수",
      "svc.3_p_short": "데모 확인 → 결제 확인 뒤 코드·계정 이전 → 인수",
      "svc.m_fee": "올리는 비용",
      "svc.m_free": "무료",
      "svc.m_seller_fee": "팔리면 판매자 수수료",
      "svc.m_review": "검토 (사람 확인)",
      "svc.m_review_v": "1~2일",
      "svc.m_see": "보는 것",
      "svc.m_see_v": "지금 가격 + 시간",
      "svc.m_pay": "이긴 뒤 입금",
      "svc.m_pay_v": "안내 따라 신속",
      "svc.m_skip": "안 내면",
      "svc.m_skip_v": "다음 사람 가능",
      "svc.m_demo": "화면 보여주기",
      "svc.m_demo_v": "중요",
      "svc.m_steps": "넘기는 순서",
      "svc.m_steps_v": "4단계",
      "svc.m_acct": "계정",
      "svc.m_acct_v": "웹·폰 하나",
      "metrics.title": "숫자로 보기",
      "metrics.lead": "수수료·검토·입찰 단위를 한눈에 정리했습니다. 검토 1~2일은 느린 게 아니라, 안전한 거래를 위해 사람이 직접 확인하는 시간입니다.",
      "metrics.inc": "가격 올릴 최소 단위",
      "metrics.inc_v": "+1만 원",
      "metrics.interest": "관심 있어요",
      "metrics.interest_v": "1회",
      "showcase.title": "프로젝트 자랑",
      "showcase.cta": "무료진단 후 자랑하기",
      "showcase.board": "보드 보기",
      "showcase.empty": "아직 자랑이 없어요.",
      "reviews.title": "이용 후기",
      "reviews.loading": "후기를 불러오는 중…",
      "reviews.write": "이용 후기 남기기",
      "why.title": "왜 WakeAgain인가요?",
      "why.lead": "통신판매중개 장터입니다. 품질·사기를 보험처럼 보증하지는 않지만, 거래는 단계로 관리합니다. 책임은 판매자·구매자에게 있습니다.",
      "safe4.kicker": "보증은 안 하지만, 관리는 합니다",
      "safe4.title": "WakeAgain이 거래를 확인하는 4단계",
      "safe4.s1_t": "PG 결제",
      "safe4.s1_d": "낙찰 후 1시간 이내 안전결제",
      "safe4.s2_t": "결제 확인 후 이전",
      "safe4.s2_d": "확인 전 코드·계정 이전 금지",
      "safe4.s3_t": "검수 · 인수",
      "safe4.s3_d": "인수하기 또는 48시간 무이의 시 자동 확정",
      "safe4.s4_t": "정산",
      "safe4.s4_d": "확정 후 판매자 정산 · 판매자 수수료 10%",
      "safe4.foot": "중개자가 보험을 드는 것이 아니라, 단계마다 확인·잠금·신고로 관리합니다.",
      "safe4.legal_title": "법적 고지 (면책)",
      "safe4.legal_1": "통신판매중개자이며 거래 당사자가 아닙니다.",
      "safe4.legal_2": "품질·사기 피해의 1차 책임은 판매자·구매자에게 있습니다.",
      "safe4.legal_3": "형식 검수·신용 점수는 보증·보험이 아닙니다.",
      "safe4.legal_4": "성사·대금·자산 이전을 플랫폼이 보증하지 않습니다.",
      "why.1_t": "신원 확인 · 단계별 신뢰",
      "why.1_p": "가격 쓰기는 이메일 인증만으로 가능합니다. 실명·휴대폰은 낙찰 후 결제·인수 때, 계좌는 판매자 정산 때 받아요. 연락처는 목록에 안 나가요. 예방 절차이지 보증은 아닙니다.",
      "why.2_t": "상태별 시작가 가이드",
      "why.2_p": "「돌아가는 초안」「써 볼 수 있는 제품」처럼 쉬운 상태에 맞춰 시작가를 안내합니다. 운영 검수 후 공개됩니다.",
      "why.2_a": "상태 쉽게 고르는 법 ›",
      "why.3_t": "관심 있는 구매자 연결",
      "why.3_p": "관심 등록·입찰로 의사 있는 이용자를 모읍니다. 초기에는 커뮤니티를 함께 키워 가는 단계입니다.",
      "why.4_t": "이전 체크리스트 안내",
      "why.4_p": "입금 확인 후 코드·도메인·계정 넘기기 순서를 가이드로 안내합니다. (플랫폼이 이전을 대행·보증하지 않습니다.)",
      "list.title": "최근 올라온 매물",
      "list.loading": "불러오는 중…",
      "list.public": "입찰 중 현재가는 사이트에 들어온 모든 사람에게 실시간으로 공개됩니다.",
      "list.all": "전체",
      "list.empty_cat": "해당 카테고리 매물이 없습니다.",
      "list.search_label": "매물 검색",
      "list.search_ph": "키워드 · 제목 · 한 줄 소개",
      "list.search_btn": "검색",
      "list.search_clear": "초기화",
      "list.empty_search": "검색 결과가 없습니다. 다른 키워드를 시도해 보세요.",
      "list.more": "프로젝트 더 보기",
      "list.none": "아직 공개 매물이 없습니다.",
      "list.empty_sample": "해당 카테고리 예시가 없습니다.",
      "list.source_api": "공개 경매 · 현재가는 사이트 방문객 전원에게 실시간 공개 · 4초마다 갱신",
      "list.source_preview": "아직 등록 매물이 없어 예시입니다. 입찰이 붙으면 현재가가 전원에게 공개됩니다.",
      "list.badge_sample": "예시",
      "list.badge_sold": "팔림",
      "list.badge_ended": "끝남",
      "list.badge_live": "입찰 중",
      "list.badge_review": "검토 중",
      "list.badge_wait": "첫 입찰 대기",
      "list.price_now": "지금 가격",
      "list.price_start": "시작 가격",
      "list.price_now_pub": "지금 가격 · 공개",
      "list.price_start_pub": "시작 가격 · 공개",
      "list.price": "가격",
      "list.inquire": "문의",
      "list.cta_bid": "가격 쓰고 보기",
      "list.cta_view": "프로젝트 자세히 보기",
      "list.ended_short": "마감",
      "list.auction_ended": "경매 종료",
      "cta.title": "프로젝트에 두 번째 기회를 주세요.",
      "cta.strong": "멈춘 프로젝트를 다시 살립니다. 등록 무료 · 판매 수수료 10%.",
      "cta.fine": "올리기·관심·가격 쓰기까지는 쉽게. 올리는 건 무료입니다. 대신 팔리면 규칙을 지킵니다 — 빠른 입금, 안 내면 다음 사람, 판매자 수수료 10%. (1시간 자동 타이머는 PG 후)",
      "cta.note": "쉽게 시작 · 거래는 확실하게 · 팔리면 판매자 수수료 10% · 사는 사람은 합의 가격만",
      "footer.brand": "우리는 기술 자산의 가치가 잊혀지는 것을 반대합니다. 모든 코드는 누군가의 소중한 자산이며, 새로운 가능성의 씨앗입니다.",
      "footer.op": "운영 · 코어랩스(CoreLabs)",
      "footer.contact": "문의: corelabs.studio@gmail.com",
      "footer.sla": "영업일 24시간 이내 1차 답변 · 입금·긴급 우선",
      "footer.contact_guide": "문의 · 응답 안내",
      "footer.tagline": "WakeAgain · 쉽게 올리고 쉽게 사고, 거래는 확실하게 · 상호 코어랩스",
      "footer.broker": "본 플랫폼은 통신판매중개자이며, 거래되는 상품의 품질과 내용은 판매자가 책임집니다.",
      "footer.broker_sub": "이용자 간 사기·분쟁의 1차 책임은 당사자에게 있습니다. WakeAgain(코어랩스)은 거래 당사자가 아니며, 성사·대금·자산 이전을 보증하지 않습니다.",
      "footer.terms": "이용약관",
      "footer.privacy": "개인정보처리방침",
      "footer.why": "왜 WakeAgain인가요",
      "footer.visitors_label": "방문자",
      "footer.visitors_today": "오늘",
      "footer.visitors_total": "전체",
      "diag.cta": "무료진단",
      "diag.page_title": "내 프로젝트는 얼마일까?",
      "app.auth_title": "쉽게 시작. 거래는 확실하게.",
      "app.auth_lede": "웹·폰 같은 계정. 누구나 올리고 가격을 쓸 수 있지만, 낙찰되면 안내에 따른 빠른 입금·신원 확인으로 거래를 끝냅니다.",
      "app.login": "로그인",
      "app.register": "가입",
      "app.email": "이메일",
      "app.password": "비밀번호",
      "404.title": "페이지를 찾을 수 없어요",
      "404.home": "홈",
      "404.market": "마켓",
      "common.free": "무료",
      "common.loading": "불러오는 중…",
      "nav.trade": "거래 안내",
      "nav.safety": "사기 예방법",
      "nav.blog": "블로그",
      "hero.stat_went_live": "다시 세상으로 나간 프로젝트",
      "hero.stat_went_live_later": "추후 공개",
    },
    en: {
      "nav.market": "Listings",
      "nav.home": "Home",
      "nav.buyers": "Buying guide",
      "nav.showcase": "Showcase",
      "nav.guide": "How it works",
      "nav.metrics": "By the numbers",
      "nav.blog": "Blog",
      "nav.login": "Log in",
      "nav.app": "Get app",
      "nav.list": "List a project",
      "nav.list_short": "List",
      "nav.site": "Website",
      "nav.logout": "Log out",
      "nav.profile": "Profile",
      "nav.notif": "Alerts",
      "nav.fees": "Fees",
      "nav.interest": "Get deal alerts",
      "nav.more_market": "Browse listings",
      "nav.account": "My account",
      "nav.trade": "How trading works",
      "nav.safety": "Safety",
      "skip": "Skip to content",
      "doc.title": "WakeAgain — Buy & sell abandoned side projects",
      "hero.badge": "Marketplace for abandoned side projects",
      "hero.title1": "Sell the project you",
      "hero.title2": "stopped building.",
      "hero.sub": "Demo-ready SaaS, apps, and tools. Bid, win, pay, handover.<br />Free to list · buyers pay $0 fees.",
      "hero.cta_main": "What's my project worth?",
      "hero.cta_sub": "Free · 30 seconds · starting bid hint",
      "hero.cta_benefit": "",
      "hero.stat_projects": "Listings",
      "hero.stat_interest": "Watchers",
      "hero.stat_free": "To list",
      "hero.stat_free_val": "Free",
      "hero.stat_went_live": "Shipped after sale",
      "hero.stat_went_live_later": "Coming soon",
      "hero.stats_note": "",
      "live.price": "Current bid",
      "live.time": "Time left",
      "live.progress": "Starting bid · bidders",
      "live.ecg": "VITAL · ALIVE",
      "live.toast": "New bid · view",
      "hub.eyebrow": "What do you want to do?",
      "hub.title": "Pick a path",
      "hub.market_k": "Buy",
      "hub.market_t": "Browse listings",
      "hub.market_d": "Live bids, demos, checkout",
      "hub.sell_k": "Sell",
      "hub.sell_t": "List a project",
      "hub.sell_d": "Free to list · 10% success fee",
      "hub.guide_k": "Learn",
      "hub.guide_t": "How it works",
      "hub.guide_d": "Selling, buying, and safety",
      "shots.eyebrow": "Product",
      "shots.title": "Screens first, then details",
      "shots.lead": "Listings · detail · list a project. Real WakeAgain UI.",
      "shots.cap1": "Listings · live bids",
      "shots.cap2": "Detail · bid · watchlist",
      "shots.cap3": "List · free to post",
      "problem.title": "Side projects stuck in the graveyard",
      "problem.one": "Most projects do not die because the idea is bad. They die because life gets busy.",
      "problem.p1": "Countless projects are built every day.",
      "problem.p2": "Many never ship.",
      "problem.p3": "Not because they were worthless.",
      "problem.p4": "Life changed, time ran out, or marketing never happened.",
      "problem.bridge": "The friction is still real:",
      "problem.c1_t": "Months of work. $0 revenue.",
      "problem.c1_p": "Hosting bills keep rolling. Motivation does not.",
      "problem.c1_p_short": "Hosting bills keep rolling. Motivation does not.",
      "problem.c2_t": "No clean place to sell",
      "problem.c2_p": "Threads and Discord get DMs—not a price, not a handover.",
      "problem.c2_p_short": "Threads and Discord get DMs—not a price, not a handover.",
      "problem.c3_t": "Hard to shop",
      "problem.c3_p": "Pitch decks and working demos get mixed. You cannot compare.",
      "problem.c3_p_short": "Pitch decks and working demos get mixed. You cannot compare.",
      "buyers.eyebrow": "Buying",
      "buyers.title": "Before you rebuild from scratch,<br /><span class=\"grad\">buy a head start</span>.",
      "buyers.lead": "Skip the next 8–12 weekends. Buy a demo-ready project. No buyer fees.",
      "buyers.lead_short": "Skip the next 8–12 weekends. Buy a demo-ready project. No buyer fees.",
      "buyers.safe_badge": "Protected checkout",
      "buyers.safe_title": "Pay first, then handover",
      "buyers.safe_body": "Win the auction → pay → seller handovers assets → you confirm. Buyers pay the agreed price; sellers pay 10%.",
      "buyers.safe_s1": "Pay after winning",
      "buyers.safe_s2": "Handover after payment",
      "buyers.safe_s3": "Confirm receipt",
      "buyers.safe_s4": "Seller payout",
      "buyers.build_label": "Build it yourself",
      "buyers.build_t": "Will another month of nights actually ship?",
      "buyers.build_1": "An MVP alone often takes weeks",
      "buyers.build_2": "Deploy, payments, and polish still block you",
      "buyers.build_3": "Opportunity cost rarely feels “free”",
      "buyers.buy_label": "Buy on WakeAgain",
      "buyers.buy_t": "Start from something that already runs",
      "buyers.buy_1": "Demo, bid, and bidder count are public",
      "buyers.buy_2": "$0 buyer fees (seller 10%)",
      "buyers.buy_3": "Bid → pay → confirm",
      "buyers.why_title": "Why buyers use WakeAgain",
      "buyers.m1_t": "Skip the blank repo",
      "buyers.m1_p": "We prioritize listings with a working demo—not idea-only docs. A way to skip another 8–12 weekends.",
      "buyers.m2_t": "Transparent pricing",
      "buyers.m2_p": "Live bid and bidder count are public. No secret DMs.",
      "buyers.m3_t": "$0 buyer fees",
      "buyers.m3_p": "When a deal closes, sellers pay 10%. Buyers pay only the agreed price. Bidding and alerts are free.",
      "buyers.m4_t": "Clear deal steps",
      "buyers.m4_p": "No handover before payment clears. Confirm within 48 hours (or auto-confirm). Not insurance—cleaner than solo DMs.",
      "buyers.rank_title": "Buyer badges that unlock as you close deals",
      "buyers.rank_lead": "Browsers and closers are different. As you <strong>close purchases</strong>, a public badge rises. Track record—not bragging.",
      "buyers.rank_scout_b": "Scout",
      "buyers.rank_scout_n": "0 completed",
      "buyers.rank_scout_p": "Watchlist & first bids. Badge appears after your first close.",
      "buyers.rank_starter_b": "First close",
      "buyers.rank_starter_n": "1+ completed",
      "buyers.rank_starter_p": "Badge on bids & profile.",
      "buyers.rank_regular_b": "Regular",
      "buyers.rank_regular_n": "3+ completed",
      "buyers.rank_regular_p": "Completed count public · repeat-buyer signal.",
      "buyers.rank_heavy_b": "Power buyer",
      "buyers.rank_heavy_n": "5+ completed",
      "buyers.rank_heavy_p": "Highlighted badge. Sellers see you as someone who actually buys.",
      "buyers.rank_whale_b": "Top buyer",
      "buyers.rank_whale_n": "10+ completed",
      "buyers.rank_whale_p": "Top buyer badge · most visible on profile & bids.",
      "buyers.rank_note": "Badges use completed purchases. Payment defaults may add a caution mark. Separate from credit score & Lv — not a guarantee.",
      "buyers.note": "Marketplace · pay → handover → confirm. See Terms for details.",
      "buyers.cta_interest": "Get deal alerts",
      "buyers.cta_market": "Browse listings",
      "svc.title": "How it works",
      "svc.lead": "List, watch, and bid for free. Win → pay on time. Miss the payment window and the next bidder can take it.",
      "svc.lead_short": "List, watch, and bid for free. Win → pay on time. Miss the payment window and the next bidder can take it.",
      "svc.1_t": "List",
      "svc.1_p": "Demo + starting bid · listing review 1–2 days · 10% seller fee",
      "svc.1_p_short": "Demo + starting bid · listing review 1–2 days · 10% seller fee",
      "svc.2_t": "Bid",
      "svc.2_p": "Public bid + timer · pay fast when you win",
      "svc.2_p_short": "Public bid + timer · pay fast when you win",
      "svc.3_t": "Handover",
      "svc.3_p": "Pay clears → assets hand over → you confirm",
      "svc.3_p_short": "Pay clears → assets hand over → you confirm",
      "svc.m_fee": "Listing fee",
      "svc.m_free": "Free",
      "svc.m_seller_fee": "Seller fee when sold",
      "svc.m_review": "Listing review",
      "svc.m_review_v": "1–2 days",
      "svc.m_see": "What you see",
      "svc.m_see_v": "Live bid + timer",
      "svc.m_pay": "After you win",
      "svc.m_pay_v": "Pay by the deadline",
      "svc.m_skip": "If you do not pay",
      "svc.m_skip_v": "Next bidder can win",
      "svc.m_demo": "Show a demo",
      "svc.m_demo_v": "Essential",
      "svc.m_steps": "Handover",
      "svc.m_steps_v": "4 steps",
      "svc.m_acct": "Account",
      "svc.m_acct_v": "Web + phone, one login",
      "metrics.title": "By the numbers",
      "metrics.lead": "Fees, review, and bid steps at a glance. The 1–2 day listing review is a human check so trading stays safer.",
      "metrics.inc": "Minimum bid step",
      "metrics.inc_v": "+$10",
      "metrics.interest": "Deal alerts",
      "metrics.interest_v": "Once",
      "showcase.title": "Project showcase",
      "showcase.cta": "Price check, then showcase",
      "showcase.board": "Open board",
      "showcase.empty": "No showcases yet.",
      "reviews.title": "Reviews",
      "reviews.loading": "Loading reviews…",
      "reviews.write": "Leave a review",
      "why.title": "Why WakeAgain",
      "why.lead": "We are a marketplace, not the seller. We run a clear deal flow—we do not insure quality or fraud. Liability stays with buyers and sellers.",
      "safe4.kicker": "Not insurance—a managed deal flow",
      "safe4.title": "Every deal follows 4 steps",
      "safe4.s1_t": "Checkout",
      "safe4.s1_d": "Pay within 1 hour of winning",
      "safe4.s2_t": "Handover after payment",
      "safe4.s2_d": "No code or accounts until payment clears",
      "safe4.s3_t": "Confirm receipt",
      "safe4.s3_d": "Confirm within 48h, or auto-confirm if no dispute",
      "safe4.s4_t": "Payout",
      "safe4.s4_d": "Seller paid after confirm · 10% seller fee",
      "safe4.foot": "We are not an insurer—we run gates, locks, and reports at each step.",
      "safe4.legal_title": "Legal notice (disclaimer)",
      "safe4.legal_1": "We are a marketplace intermediary, not a party to the deal.",
      "safe4.legal_2": "Primary liability for quality and fraud sits with buyer and seller.",
      "safe4.legal_3": "Format review and site credit are not guarantees or insurance.",
      "safe4.legal_4": "We do not guarantee closing, payment, or asset handover.",
      "why.1_t": "Identity · staged trust",
      "why.1_p": "Bidding needs email verification only. Real name and phone are required after you win (pay/accept); settlement account is for seller payout. Contact stays off public lists. Prevention — not a fraud guarantee.",
      "why.2_t": "Starting bid by status",
      "why.2_p": "Simple states like “working prototype” or “usable product” guide starting bids. Listings go public after review.",
      "why.2_a": "How to pick a status ›",
      "why.3_t": "Connect serious buyers",
      "why.3_p": "Alerts and bids gather people who mean it. Early on, we grow the community together.",
      "why.4_t": "Handover checklist",
      "why.4_p": "After payment clears, we guide code, domain, and account handover order. The platform does not perform or guarantee handovers.",
      "list.title": "Live listings",
      "list.loading": "Loading…",
      "list.public": "Live bids are public—every visitor sees the same price.",
      "list.all": "All",
      "list.search_label": "Search listings",
      "list.search_ph": "Search title, tags, or description",
      "list.search_btn": "Search",
      "list.search_clear": "Clear",
      "list.empty_search": "No matches. Try another keyword.",
      "list.more": "Show more listings",
      "list.none": "No live listings yet.",
      "list.empty_sample": "No samples in this category.",
      "list.source_api": "Live auctions · public prices · updates every 4s",
      "list.source_preview": "No live listings yet — samples shown. Live prices go public once bidding starts.",
      "list.badge_sample": "Sample",
      "list.badge_sold": "Sold",
      "list.badge_ended": "Ended",
      "list.badge_live": "Live",
      "list.badge_review": "Under review",
      "list.badge_wait": "Awaiting first bid",
      "list.price_now": "Current bid",
      "list.price_start": "Starting bid",
      "list.price_now_pub": "Current bid · public",
      "list.price_start_pub": "Starting bid · public",
      "list.price": "Price",
      "list.inquire": "Inquire",
      "list.cta_bid": "Place bid",
      "list.cta_view": "View listing",
      "list.ended_short": "Ended",
      "list.auction_ended": "Auction ended",
      "cta.title": "Give your side project a second life.",
      "cta.strong": "Free to list. 10% only when it sells. Buyers pay $0 fees.",
      "cta.fine": "Free to list. After a sale: pay on time, next bidder if missed, 10% seller fee.",
      "cta.note": "Easy to list · serious when it sells · 10% seller fee · $0 buyer fees",
      "footer.brand": "Code is an asset. Do not let it die in a private repo.",
      "footer.op": "Operated by CoreLabs",
      "footer.contact": "Contact: corelabs.studio@gmail.com",
      "footer.sla": "We reply within 1 business day · payments & urgent issues first",
      "footer.contact_guide": "Contact",
      "footer.tagline": "WakeAgain · free to list · serious when it sells",
      "footer.broker": "WakeAgain is a marketplace intermediary. Sellers are responsible for listing accuracy and asset quality.",
      "footer.broker_sub": "Buyers and sellers own the deal. We do not guarantee completion, payment, or handover.",
      "footer.terms": "Terms",
      "footer.privacy": "Privacy",
      "footer.why": "Why WakeAgain",
      "footer.visitors_label": "Visitors",
      "footer.visitors_today": "Today",
      "footer.visitors_total": "Total",
      "diag.cta": "Free price check",
      "diag.page_title": "What's my project worth?",
      "app.auth_title": "Easy to list. Serious when it sells.",
      "app.auth_lede": "One account for web and mobile. List and bid freely—after you win, payment and identity checks finish the deal.",
      "app.login": "Log in",
      "app.register": "Sign up",
      "app.email": "Email",
      "app.password": "Password",
      "404.title": "Page not found",
      "404.home": "Home",
      "404.market": "Listings",
      "common.free": "Free",
      "common.loading": "Loading…",
    },
  };

  // Merge supplemental dictionaries (i18n-messages.js)
  try {
    var extra = global.WA_I18N_EXTRA;
    if (extra) {
      ["ko", "en"].forEach(function (loc) {
        if (!extra[loc]) return;
        Object.keys(extra[loc]).forEach(function (k) {
          STR[loc][k] = extra[loc][k];
        });
      });
    }
  } catch (e) {}

  var fx = { KRW: 1, USD: 1350, EUR: 1450 };
  var curMeta = {
    KRW: { symbol: "₩", decimals: 0, locale: "ko-KR" },
    USD: { symbol: "$", decimals: 0, locale: "en-US" },
    EUR: { symbol: "€", decimals: 0, locale: "en-US" },
  };

  function detectLang() {
    // Priority: manual save (localStorage) > ?lang= query > browser language > English default
    var saved = localStorage.getItem(STORAGE_LANG);
    if (saved === "ko" || saved === "en") return saved;
    try {
      var q = new URLSearchParams(location.search || "");
      var L = (q.get("lang") || "").toLowerCase();
      if (L === "en" || L === "ko") return L;
    } catch (e) {}
    // Browser: ko / ko-KR → Korean; everything else → English (global-first)
    var nav = "";
    try {
      nav = String(navigator.language || (navigator.languages && navigator.languages[0]) || "").toLowerCase();
    } catch (e2) {
      nav = "";
    }
    if (nav.indexOf("ko") === 0) return "ko";
    return "en";
  }

  function detectCurrency(langHint) {
    // Priority: manual save > language-aware default (global-first: USD unless KO)
    var saved = localStorage.getItem(STORAGE_CUR);
    if (saved && curMeta[saved]) return saved;
    var lang = langHint || detectLang();
    return lang === "ko" ? "KRW" : "USD";
  }

  var state = { lang: detectLang(), currency: "USD" };
  state.currency = detectCurrency(state.lang);

  function t(key, vars) {
    // Never fall back into Korean while the UI is English — that reads as a KR-only product.
    var pack = STR[state.lang] || STR.en;
    var val = pack[key];
    if (val == null && state.lang !== "en" && STR.en[key] != null) val = STR.en[key];
    if (val == null && state.lang === "ko" && STR.ko[key] != null) val = STR.ko[key];
    if (val == null) val = key;
    if (vars && typeof vars === "object") {
      Object.keys(vars).forEach(function (k) {
        val = String(val).split("{" + k + "}").join(String(vars[k]));
      });
    }
    return val;
  }

  function formatMoney(amountKrw) {
    var n = Number(amountKrw);
    if (!isFinite(n)) return "—";
    var code = state.currency || "USD";
    var rate = fx[code] || 1;
    var meta = curMeta[code] || curMeta.USD;
    var shown = code === "KRW" ? n : Math.round(n / rate);
    try {
      return (
        meta.symbol +
        shown.toLocaleString(meta.locale, {
          maximumFractionDigits: meta.decimals,
          minimumFractionDigits: meta.decimals,
        })
      );
    } catch (e) {
      return meta.symbol + String(shown);
    }
  }

  function apply(root) {
    var scope = root || document;
    scope.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (!key) return;
      var val = t(key);
      // Missing key: keep author-provided HTML/text fallback instead of showing raw "proj.foo"
      if (val === key) {
        var hasHtml = el.hasAttribute("data-i18n-html");
        var existing = hasHtml ? (el.innerHTML || "").trim() : (el.textContent || "").trim();
        if (existing && existing !== key) return;
      }
      if (el.hasAttribute("data-i18n-html")) el.innerHTML = val;
      else el.textContent = val;
    });
    scope.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var k = el.getAttribute("data-i18n-placeholder");
      var v = t(k);
      if (v === k) {
        var ph = el.getAttribute("placeholder");
        if (ph && ph !== k) return;
      }
      el.setAttribute("placeholder", v);
    });
    scope.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      var k = el.getAttribute("data-i18n-aria");
      var v = t(k);
      if (v === k) {
        var a = el.getAttribute("aria-label");
        if (a && a !== k) return;
      }
      el.setAttribute("aria-label", v);
    });
    scope.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      var k = el.getAttribute("data-i18n-title");
      var v = t(k);
      if (v === k) {
        var ti = el.getAttribute("title");
        if (ti && ti !== k) return;
      }
      el.setAttribute("title", v);
    });
    document.documentElement.lang = state.lang === "en" ? "en" : "ko";
    document.documentElement.setAttribute("data-wa-lang", state.lang);
    document.documentElement.setAttribute("data-wa-currency", state.currency);
    var titleEl = document.querySelector("title[data-i18n]");
    if (titleEl) {
      document.title = t(titleEl.getAttribute("data-i18n"));
    } else if (
      // do not overwrite app shell / form page titles with marketing home title
      !document.body.classList.contains("app-body") &&
      !document.body.classList.contains("form-body") &&
      STR[state.lang] &&
      STR[state.lang]["doc.title"]
    ) {
      document.title = STR[state.lang]["doc.title"];
    }
    scope.querySelectorAll("[data-lang-switch]").forEach(function (el) {
      if (el.tagName === "SELECT") el.value = state.lang;
      else if (el.getAttribute("data-lang-switch") === state.lang) {
        el.setAttribute("aria-current", "true");
        el.classList.add("is-on");
      } else {
        el.removeAttribute("aria-current");
        el.classList.remove("is-on");
      }
    });
    scope.querySelectorAll("[data-currency-switch]").forEach(function (el) {
      if (el.tagName === "SELECT") el.value = state.currency;
    });
    scope.querySelectorAll("[data-money-krw]").forEach(function (el) {
      el.textContent = formatMoney(el.getAttribute("data-money-krw"));
    });
  }

  function setLang(lang, opts) {
    if (lang !== "ko" && lang !== "en") return;
    opts = opts || {};
    state.lang = lang;
    // Manual language choice always wins and persists
    localStorage.setItem(STORAGE_LANG, lang);
    // Seed display currency only when the user has never chosen one
    if (!localStorage.getItem(STORAGE_CUR)) {
      state.currency = lang === "ko" ? "KRW" : "USD";
    }
    apply(document);
    try {
      var url = new URL(location.href);
      url.searchParams.set("lang", lang);
      history.replaceState(null, "", url.pathname + url.search + url.hash);
    } catch (e) {}
    try {
      document.dispatchEvent(new CustomEvent("wa:langchange", { detail: { lang: lang } }));
    } catch (e) {}
  }

  function setCurrency(code) {
    if (!curMeta[code]) return;
    state.currency = code;
    localStorage.setItem(STORAGE_CUR, code);
    apply(document);
    try {
      document.dispatchEvent(new CustomEvent("wa:currencychange", { detail: { currency: code } }));
    } catch (e) {}
  }

  function ingestConfig(cfg) {
    if (!cfg || !cfg.global) return;
    var g = cfg.global;
    if (g.fx_display_only) {
      Object.keys(g.fx_display_only).forEach(function (k) {
        fx[k] = Number(g.fx_display_only[k]) || fx[k];
      });
    }
  }

  function bindUi(root) {
    var scope = root || document;
    scope.querySelectorAll("[data-lang-switch]").forEach(function (el) {
      if (el.__waLangBound) return;
      el.__waLangBound = true;
      if (el.tagName === "SELECT") {
        el.addEventListener("change", function () {
          setLang(el.value);
        });
      } else {
        el.addEventListener("click", function (e) {
          e.preventDefault();
          setLang(el.getAttribute("data-lang-switch"));
        });
      }
    });
    scope.querySelectorAll("[data-currency-switch]").forEach(function (el) {
      if (el.__waCurBound) return;
      el.__waCurBound = true;
      if (el.tagName === "SELECT") {
        el.addEventListener("change", function () {
          setCurrency(el.value);
        });
      }
    });
  }

  function boot() {
    bindUi(document);
    apply(document);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  global.WakeAgainI18n = {
    t: t,
    apply: apply,
    setLang: setLang,
    setCurrency: setCurrency,
    formatMoney: formatMoney,
    ingestConfig: ingestConfig,
    bindUi: bindUi,
    getLang: function () {
      return state.lang;
    },
    getCurrency: function () {
      return state.currency;
    },
    STR: STR,
  };
})(typeof window !== "undefined" ? window : globalThis);

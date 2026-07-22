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
      "hero.badge": "잠든 프로젝트를 다시 깨우는 곳",
      "hero.title1": "멈춰버린 프로젝트에",
      "hero.title2": "숨을 불어넣다.",
      "hero.sub": "완성되지 못한 코드, 방치된 도메인, 잠자고 있는 API.<br />당신의 “실패한 시도”는 누군가에게 “완벽한 시작”이 됩니다.",
      "hero.cta_main": "내 프로젝트는 얼마일까?",
      "hero.cta_sub": "30초 무료 · 시작가 힌트 + 올리기 준비도",
      "hero.cta_benefit": "30초면 끝 — 내 잠든 프로젝트의 <strong>가격 감</strong>을 잡고, <strong>지금 올릴지·손볼지</strong> 바로 판단하세요.",
      "hero.stat_projects": "올라온 프로젝트",
      "hero.stat_interest": "관심 있어요",
      "hero.stat_free": "올리는 비용",
      "hero.stat_free_val": "무료",
      "hero.stats_note": "실제 숫자만 보여 줍니다",
      "live.price": "현재 입찰가",
      "live.time": "남은 시간",
      "live.progress": "시작가 대비 · 입찰자 5명",
      "live.toast": "방금 입찰 · 보기",
      "problem.title": "세상 밖으로 나오지 못한 프로젝트들",
      "problem.p1": "매일 수많은 프로젝트가 만들어집니다.",
      "problem.p2": "많은 제품들이 세상 밖으로 나오지 않습니다.",
      "problem.p3": "그들이 쓸모없어서가 아닙니다.",
      "problem.p4": "이는 인생이 변하거나, 시간이 없거나, 마케팅이 일어나지 않았기 때문입니다.",
      "problem.bridge": "그래도 문제는 남습니다. 구체적으로는 이런 상황입니다.",
      "problem.c1_t": "시간은 썼는데 수익·유저는 0",
      "problem.c1_p": "사이드 프로젝트 하나에 주말 기준 8~12주를 쓰는 경우가 많습니다. 그런데 출시 후에도 첫 유저 10명을 못 넘기면, 서버·도메인 비용만 매달 나갑니다. “아깝다”와 “더 못 하겠다”가 동시에 남습니다.",
      "problem.c2_t": "팔고 싶은데 장이 없다",
      "problem.c2_p": "커뮤니티·중고 거래에 올리면 문의는 오지만, 가격 기준·데모 검증·이전 절차가 없어 며칠 채팅 끝에 무산되기 쉽습니다. 규모 있는 매각 플랫폼은 큰 딜 위주라 사이드 프로젝트는 문턱이 높습니다.",
      "problem.c3_t": "사고 싶은데, 비교할 수 있는 매물이 없다",
      "problem.c3_p": "0부터 다시 만들면 MVP만 수 주가 기본입니다. 이미 손댄 코드를 사고 싶어도, 아이디어만 있는 매물과 실행 화면이 있는 매물이 뒤섞여 비교가 어렵습니다.",
      "buyers.eyebrow": "구매자라면 · 만들까, 살까?",
      "buyers.title": "0부터 다시 만들기 전에,<br /><span class=\"grad\">이미 숨 쉬는 초안</span>을 보세요.",
      "buyers.lead": "직접 만들 수 있습니다. 다만 주말 몇 주를 또 쓸 거면, 데모가 있는 프로젝트를 사는 편이 더 빠를 수 있어요. 사는 사람 추가 수수료는 없습니다. 합의(낙찰) 가격만 부담합니다.",
      "buyers.safe_badge": "안전결제 · 구매자 보호",
      "buyers.safe_title": "혼자 계좌이체하는 중고 거래가 아닙니다.",
      "buyers.safe_body": "WakeAgain은 낙찰 후 PG 안전결제 → 결제 확인 후에만 이전 → 검수 후 인수하기(또는 이전 후 48시간 내 이의 없으면 자동 확정·정산) 절차를 둡니다. 결제 확인 전 코드·계정 이전 금지. 사는 분은 합의 가격만, 수수료는 판매자 10%.",
      "buyers.safe_s1": "1. 낙찰 후 1시간 이내 PG 결제",
      "buyers.safe_s2": "2. 결제 확인 → 판매자 이전",
      "buyers.safe_s3": "3. 검수 후 인수 · 또는 자동 확정",
      "buyers.safe_s4": "4. 그다음 판매자 정산",
      "buyers.build_label": "직접 만들기",
      "buyers.build_t": "시간은 내 것, 결과도 내 것",
      "buyers.build_1": "MVP만 잡아도 보통 수 주",
      "buyers.build_2": "배포·결제·디테일에서 또 막힘",
      "buyers.build_3": "기회비용이 “공짜”처럼 안 보임",
      "buyers.buy_label": "WakeAgain에서 사기",
      "buyers.buy_t": "화면이 돌아가는 것부터 시작",
      "buyers.buy_1": "데모·지금 가격·입찰자 수 공개",
      "buyers.buy_2": "사는 쪽 추가 수수료 없음",
      "buyers.buy_3": "가격 쓰기 → PG 안전결제 → 검수·인수",
      "buyers.why_title": "왜 여기서 사나",
      "buyers.m1_t": "시간 절약",
      "buyers.m1_p": "아이디어만 있는 문서가 아니라, 우선 돌아가는 화면·데모가 있는 매물을 모읍니다. “다시 8~12주”를 아끼는 선택지입니다.",
      "buyers.m2_t": "비교 가능한 가격",
      "buyers.m2_p": "지금 얼마인지, 입찰자가 몇 명인지 사이트에 들어온 누구나 볼 수 있어요. 숨은 DM 호가가 아닙니다.",
      "buyers.m3_t": "사는 사람 수수료 0",
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
      "buyers.note": "WakeAgain(코어랩스)은 통신판매중개자입니다. 품질·사기를 보험처럼 보증하지 않습니다. 안전결제·구매자 보호는 PG 결제 → 이전 → 인수/자동 확정 절차로 운영합니다.",
      "buyers.cta_interest": "관심 등록하기 (구매)",
      "buyers.cta_market": "마켓 둘러보기",
      "svc.title": "이용 방법",
      "svc.lead": "올리는 건 무료입니다. 관심·가격 쓰기도 가능하고, 낙찰되면 PG 안전결제(기본 1시간 이내)로 진행합니다. 미결제 시 낙찰이 무효될 수 있어요.",
      "svc.1_t": "1. 내 프로젝트 올리기",
      "svc.1_p": "어떻게 만들었는지, 화면(데모), 시작 가격을 적습니다. 올리는 건 무료. 안전한 거래를 위해 사람이 직접 형식 검수하며, 보통 1~2일 안에 게시 허용하면 모두가 볼 수 있게 올라갑니다. (품질·가치 보증 아님)",
      "svc.2_t": "2. 사고 싶으면 가격 쓰기",
      "svc.2_p": "지금 가격과 남은 시간을 보고, “이 금액에 살게요”라고 씁니다. 낙찰되면 안내에 따라 빠르게 입금. 안 보내면 다음 사람에게 넘어갈 수 있어요.",
      "svc.3_t": "3. 확인 후 넘겨주기",
      "svc.3_p": "화면이 돌아가는 것만 우선합니다. 중요한 코드·계정은 돈 확인 후 넘깁니다. 연락 → 약속 → 넘기기 순서예요.",
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
      "cta.strong": "우리는 그 프로젝트들에게 다시 한 번 기회를 줍니다.",
      "cta.fine": "올리기·관심·가격 쓰기까지는 쉽게. 올리는 건 무료입니다. 대신 팔리면 규칙을 지킵니다 — 빠른 입금, 안 내면 다음 사람, 판매자 수수료 10%. (1시간 자동 타이머는 PG 후)",
      "cta.note": "쉽게 시작 · 거래는 확실하게 · 팔리면 판매자 수수료 10% · 사는 사람은 합의 가격만",
      "footer.brand": "우리는 기술 자산의 가치가 잊혀지는 것을 반대합니다. 모든 코드는 누군가의 소중한 자산이며, 새로운 가능성의 씨앗입니다.",
      "footer.op": "운영 · 코어랩스(CoreLabs)",
      "footer.contact": "문의: corelabs.studio@gmail.com",
      "footer.tagline": "WakeAgain · 쉽게 올리고 쉽게 사고, 거래는 확실하게 · 상호 코어랩스",
      "footer.broker": "본 플랫폼은 통신판매중개자이며, 거래되는 상품의 품질과 내용은 판매자가 책임집니다.",
      "footer.broker_sub": "이용자 간 사기·분쟁의 1차 책임은 당사자에게 있습니다. WakeAgain(코어랩스)은 거래 당사자가 아니며, 성사·대금·자산 이전을 보증하지 않습니다.",
      "footer.terms": "이용약관",
      "footer.privacy": "개인정보처리방침",
      "footer.why": "왜 WakeAgain인가요",
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
    },
    en: {
      "nav.market": "Marketplace",
      "nav.buyers": "Buying guide",
      "nav.showcase": "Showcase",
      "nav.guide": "Guide",
      "nav.metrics": "By the numbers",
      "nav.login": "Log in",
      "nav.app": "Get the app",
      "nav.list": "List a project",
      "nav.list_short": "List",
      "nav.site": "Website",
      "nav.logout": "Log out",
      "nav.profile": "Profile",
      "nav.notif": "Alerts",
      "nav.fees": "Fees",
      "nav.interest": "Register interest",
      "nav.more_market": "Browse marketplace",
      "nav.account": "My account",
      "skip": "Skip to content",
      "doc.title": "WakeAgain — Give projects a second chance.",
      "hero.badge": "A second chance for shelved projects",
      "hero.title1": "Breathe life into",
      "hero.title2": "paused projects.",
      "hero.sub": "Unfinished code, idle domains, sleeping APIs.<br />Your “failed attempt” can be someone else’s perfect start.",
      "hero.cta_main": "What’s my project worth?",
      "hero.cta_sub": "30 sec free · start-price hint + list-ready score",
      "hero.cta_benefit": "In 30 seconds: get a feel for the <strong>price</strong>—and know whether to <strong>list now or fix first</strong>.",
      "hero.stat_projects": "Listed projects",
      "hero.stat_interest": "Interests",
      "hero.stat_free": "Listing fee",
      "hero.stat_free_val": "Free",
      "hero.stats_note": "Live counts only — no fake metrics",
      "live.price": "Current bid",
      "live.time": "Time left",
      "live.progress": "vs start price · 5 bidders",
      "live.toast": "New bid · view",
      "problem.title": "Projects that never left the lab",
      "problem.p1": "Countless projects are built every day.",
      "problem.p2": "Many never ship to the world.",
      "problem.p3": "Not because they were worthless.",
      "problem.p4": "Life changed, time ran out, or marketing never happened.",
      "problem.bridge": "Still, the friction remains. Concretely:",
      "problem.c1_t": "Time spent, revenue & users still zero",
      "problem.c1_p": "A side project often eats 8–12 weekends. If you never clear the first 10 users, server and domain bills keep coming. You feel both “what a waste” and “I can’t keep going.”",
      "problem.c2_t": "Want to sell — but no real market",
      "problem.c2_p": "Community posts get chats, but without pricing norms, demo checks, or transfer steps, deals die after days of messages. Big acquisition marketplaces aim at huge deals — side projects don’t fit.",
      "problem.c3_t": "Want to buy — but listings aren’t comparable",
      "problem.c3_p": "Building an MVP from scratch takes weeks. You want working code, but idea-only PDFs and runnable demos are mixed together. Without live price and countdown, you can’t decide whether to buy now.",
      "buyers.eyebrow": "For buyers · Build or buy?",
      "buyers.title": "Before you rebuild from zero,<br /><span class=\"grad\">see a draft that already runs</span>.",
      "buyers.lead": "You can build it yourself. If that means more weekends, buying a demo-ready project may be faster. Buyers pay no platform fee — only the agreed (winning) price.",
      "buyers.safe_badge": "Safe pay · buyer protection",
      "buyers.safe_title": "Not a solo bank-transfer side deal.",
      "buyers.safe_body": "After award: PG safe payment → transfer only after payment is confirmed → inspect then Accept (or auto-confirm within 48h with no dispute). No code/account handoff before payment. Buyers pay the agreed price only; sellers pay 10% fee.",
      "buyers.safe_s1": "1. Pay via PG within 1 hour of award",
      "buyers.safe_s2": "2. Payment confirmed → seller transfers",
      "buyers.safe_s3": "3. Inspect then accept · or auto-confirm",
      "buyers.safe_s4": "4. Then seller settlement",
      "buyers.build_label": "Build it yourself",
      "buyers.build_t": "Your time, your result",
      "buyers.build_1": "An MVP alone often takes weeks",
      "buyers.build_2": "Deploy, payments, and polish still block you",
      "buyers.build_3": "Opportunity cost rarely feels “free”",
      "buyers.buy_label": "Buy on WakeAgain",
      "buyers.buy_t": "Start from something that runs",
      "buyers.buy_1": "Demo, live price, and bidder count are public",
      "buyers.buy_2": "No extra fee for buyers",
      "buyers.buy_3": "Bid → PG safe pay → inspect & accept",
      "buyers.why_title": "Why buy here",
      "buyers.m1_t": "Save time",
      "buyers.m1_p": "We prioritize listings with a working demo—not idea-only docs. A way to skip another 8–12 weekends.",
      "buyers.m2_t": "Comparable prices",
      "buyers.m2_p": "Anyone on the site sees the live price and how many people are bidding. No hidden DM quotes.",
      "buyers.m3_t": "Buyer fee: zero",
      "buyers.m3_p": "When a deal closes, sellers pay 10%. Buyers pay only the agreed price. Bidding and interest are free.",
      "buyers.m4_t": "Safe payment steps",
      "buyers.m4_p": "No transfer before PG payment is confirmed; settle after accept (or 48h auto-confirm). Plus identity levels and reports. Not insurance—clearer steps than solo DMs.",
      "buyers.rank_title": "Buyer badges that grow with each completed buy",
      "buyers.rank_lead": "Browsers and closers are different. As you <strong>complete purchases</strong>, a public badge rises for sellers and other users. “Heavy buyer” is <strong>track record</strong>, not bragging.",
      "buyers.rank_scout_b": "Getting ready",
      "buyers.rank_scout_n": "0 completed",
      "buyers.rank_scout_p": "Watchlist & first bids. Badge appears after your first close.",
      "buyers.rank_starter_b": "First buy done",
      "buyers.rank_starter_n": "1+ completed",
      "buyers.rank_starter_p": "Badge on bids & profile.",
      "buyers.rank_regular_b": "Regular buyer",
      "buyers.rank_regular_n": "3+ completed",
      "buyers.rank_regular_p": "Completed count public · repeat-buyer signal.",
      "buyers.rank_heavy_b": "Heavy buyer",
      "buyers.rank_heavy_n": "5+ completed",
      "buyers.rank_heavy_p": "Highlighted badge. Sellers see you as someone who actually buys.",
      "buyers.rank_whale_b": "Power buyer",
      "buyers.rank_whale_n": "10+ completed",
      "buyers.rank_whale_p": "Top buyer badge · most visible on profile & bids.",
      "buyers.rank_note": "Badges use completed purchases. Payment defaults may add a caution mark. Separate from credit score & Lv — not a guarantee.",
      "buyers.note": "WakeAgain (CoreLabs) is a marketplace intermediary — not an insurer. Safe pay / buyer protection runs as PG payment → transfer → accept or auto-confirm.",
      "buyers.cta_interest": "Register buyer interest",
      "buyers.cta_market": "Browse the market",
      "svc.title": "How it works",
      "svc.lead": "Listing is free. Interest and bidding are free. After award, pay via PG safe checkout (usually within 1 hour)—or the award can be voided.",
      "svc.1_t": "1. List your project",
      "svc.1_p": "Share how it was built, a demo, and a starting price. Listing is free. A person checks format for safer trading—usually public within 1–2 days. Not a quality or value guarantee.",
      "svc.2_t": "2. Bid if you want it",
      "svc.2_p": "See the live price and time left, then say what you’ll pay. Winners deposit quickly per instructions. No deposit, and the next person may take over.",
      "svc.3_t": "3. Verify, then transfer",
      "svc.3_p": "Running demos come first. Critical code and accounts move after payment is confirmed — contact → agree → transfer.",
      "svc.m_fee": "Listing fee",
      "svc.m_free": "Free",
      "svc.m_seller_fee": "Seller fee when sold",
      "svc.m_review": "Review (human check)",
      "svc.m_review_v": "1–2 days",
      "svc.m_see": "What you see",
      "svc.m_see_v": "Live price + timer",
      "svc.m_pay": "After you win",
      "svc.m_pay_v": "Deposit promptly",
      "svc.m_skip": "If you don’t",
      "svc.m_skip_v": "Next bidder may win",
      "svc.m_demo": "Show a demo",
      "svc.m_demo_v": "Essential",
      "svc.m_steps": "Transfer flow",
      "svc.m_steps_v": "4 steps",
      "svc.m_acct": "Account",
      "svc.m_acct_v": "Web + phone, one login",
      "metrics.title": "By the numbers",
      "metrics.lead": "Fees, review, and bid units at a glance. The 1–2 day review isn’t delay for its own sake—a person checks listings so trading stays safer.",
      "metrics.inc": "Minimum bid step",
      "metrics.inc_v": "+₩10,000",
      "metrics.interest": "Interest",
      "metrics.interest_v": "Once",
      "showcase.title": "Project showcase",
      "showcase.cta": "Diagnose, then showcase",
      "showcase.board": "Open board",
      "showcase.empty": "No showcases yet.",
      "reviews.title": "Reviews",
      "reviews.loading": "Loading reviews…",
      "reviews.write": "Leave a review",
      "why.title": "Why WakeAgain?",
      "why.lead": "A marketplace intermediary. We don’t insure quality or fraud—but we manage the deal in clear steps. Liability stays with buyer and seller.",
      "safe4.kicker": "No guarantee — managed process",
      "safe4.title": "4 steps WakeAgain checks on every deal",
      "safe4.s1_t": "PG payment",
      "safe4.s1_d": "Safe checkout within 1 hour of award",
      "safe4.s2_t": "Transfer after payment",
      "safe4.s2_d": "No code/accounts before payment is confirmed",
      "safe4.s3_t": "Inspect · accept",
      "safe4.s3_d": "Accept takeover, or auto-confirm after 48h with no dispute",
      "safe4.s4_t": "Settlement",
      "safe4.s4_d": "Seller paid after confirm · 10% seller fee",
      "safe4.foot": "We’re not an insurer—we manage with gates, locks, and reports at each step.",
      "safe4.legal_title": "Legal notice (disclaimer)",
      "safe4.legal_1": "We are a marketplace intermediary, not a party to the deal.",
      "safe4.legal_2": "Primary liability for quality and fraud sits with buyer and seller.",
      "safe4.legal_3": "Format review and site credit are not guarantees or insurance.",
      "safe4.legal_4": "We do not guarantee closing, payment, or asset transfer.",
      "why.1_t": "Identity · staged trust",
      "why.1_p": "Bidding needs email verification only. Real name and phone are required after you win (pay/accept); settlement account is for seller payout. Contact stays off public lists. Prevention — not a fraud guarantee.",
      "why.2_t": "Start-price by status",
      "why.2_p": "Simple states like “working prototype” or “usable beta” guide starting prices. Listings go public after ops review.",
      "why.2_a": "How to pick a status ›",
      "why.3_t": "Connect interested buyers",
      "why.3_p": "Interest and bids gather people who mean it. Early on, we grow the community together.",
      "why.4_t": "Transfer checklist",
      "why.4_p": "After payment is confirmed, we guide code, domain, and account handoff order. The platform does not perform or guarantee transfers.",
      "list.title": "Latest listings",
      "list.loading": "Loading…",
      "list.public": "Live bid prices are visible to everyone on the site in real time.",
      "list.all": "All",
      "list.empty_cat": "No listings in this category.",
      "list.more": "Show more projects",
      "list.none": "No public listings yet.",
      "list.empty_sample": "No samples in this category.",
      "list.source_api": "Live auction · current price public to every visitor · refreshes every 4s",
      "list.source_preview": "No live listings yet — samples shown. Live prices go public once bidding starts.",
      "list.badge_sample": "Sample",
      "list.badge_sold": "Sold",
      "list.badge_ended": "Ended",
      "list.badge_live": "Bidding",
      "list.badge_review": "In review",
      "list.badge_wait": "Awaiting first bid",
      "list.price_now": "Current",
      "list.price_start": "Start",
      "list.price_now_pub": "Current · public",
      "list.price_start_pub": "Start · public",
      "list.price": "Price",
      "list.inquire": "Inquire",
      "list.cta_bid": "Bid & view",
      "list.cta_view": "View project",
      "list.ended_short": "Ended",
      "list.auction_ended": "Auction ended",
      "cta.title": "Give projects a second chance.",
      "cta.strong": "We give those projects one more shot.",
      "cta.fine": "Listing, interest, and bidding stay easy — listing is free. After a sale, rules apply: prompt deposit, next bidder if missed, 10% seller fee. (1-hour auto timer after PG.)",
      "cta.note": "Easy to start · serious deals · 10% seller fee · buyers pay the agreed price only",
      "footer.brand": "We refuse to let technical assets be forgotten. Every codebase is someone’s hard-won asset — and a seed of new possibility.",
      "footer.op": "Operated by CoreLabs",
      "footer.contact": "Contact: corelabs.studio@gmail.com",
      "footer.tagline": "WakeAgain · easy to list & buy, serious when it sells · CoreLabs",
      "footer.broker": "This platform is an intermediary. Product quality and content are the seller’s responsibility.",
      "footer.broker_sub": "Primary liability for fraud or disputes sits with the parties. WakeAgain (CoreLabs) is not a party to the deal and does not guarantee completion, payment, or asset transfer.",
      "footer.terms": "Terms",
      "footer.privacy": "Privacy",
      "footer.why": "Why WakeAgain",
      "diag.cta": "Free diagnose",
      "diag.page_title": "What’s my project worth?",
      "app.auth_title": "Easy to start. Serious when it sells.",
      "app.auth_lede": "One account on web and mobile. Anyone can list and bid — after award, deposit and identity rules close the deal.",
      "app.login": "Log in",
      "app.register": "Sign up",
      "app.email": "Email",
      "app.password": "Password",
      "404.title": "Page not found",
      "404.home": "Home",
      "404.market": "Market",
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
    var saved = localStorage.getItem(STORAGE_LANG);
    if (saved === "ko" || saved === "en") return saved;
    try {
      var q = new URLSearchParams(location.search || "");
      var L = (q.get("lang") || "").toLowerCase();
      if (L === "en" || L === "ko") return L;
    } catch (e) {}
    var nav = (navigator.language || "ko").toLowerCase();
    if (nav.indexOf("ko") === 0) return "ko";
    return "en";
  }

  function detectCurrency(lang) {
    var saved = localStorage.getItem(STORAGE_CUR);
    if (saved && curMeta[saved]) return saved;
    return lang === "en" ? "USD" : "KRW";
  }

  var state = { lang: detectLang(), currency: "KRW" };
  state.currency = detectCurrency(state.lang);

  function t(key, vars) {
    var pack = STR[state.lang] || STR.ko;
    var val = pack[key];
    if (val == null && STR.en[key] != null) val = STR.en[key];
    if (val == null && STR.ko[key] != null) val = STR.ko[key];
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
    var code = state.currency || "KRW";
    var rate = fx[code] || 1;
    var meta = curMeta[code] || curMeta.KRW;
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
    } else if (STR[state.lang] && STR[state.lang]["doc.title"]) {
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
    localStorage.setItem(STORAGE_LANG, lang);
    if (!localStorage.getItem(STORAGE_CUR) || opts.resetCurrency) {
      state.currency = detectCurrency(lang);
      if (opts.resetCurrency) localStorage.setItem(STORAGE_CUR, state.currency);
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
          setLang(el.value, { resetCurrency: true });
        });
      } else {
        el.addEventListener("click", function (e) {
          e.preventDefault();
          setLang(el.getAttribute("data-lang-switch"), { resetCurrency: true });
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

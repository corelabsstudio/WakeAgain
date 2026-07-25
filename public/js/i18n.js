/**
 * WakeAgain i18n — KO / EN localization.
 * data-i18n="key" · data-i18n-html · data-money-krw · WakeAgainI18n.t / setLang / formatMoney
 */
(function (global) {
  var STORAGE_LANG = "wa_lang";
  var STORAGE_CUR = "wa_currency";

  var STR = {
    ko: {
      "nav.market": "마켓",
      "nav.home": "홈",
      "nav.buyers": "거래 안내",
      "nav.trade": "거래 안내",
      "nav.showcase": "자랑하기",
      "nav.safety": "사기 예방법",
      "nav.guide": "이용안내",
      "nav.metrics": "숫자로 보기",
      "nav.login": "로그인",
      "nav.app": "앱 설치",
      "nav.list": "프로젝트 올리기",
      "nav.list_short": "올리기",
      "nav.site": "사이트",
      "nav.logout": "로그아웃",
      "nav.profile": "내 정보",
      "nav.notif": "알림",
      "nav.fees": "수수료",
      "nav.interest": "관심 등록",
      "nav.more_market": "마켓 보기",
      "nav.account": "내 계정",
      "skip": "본문으로",
      "doc.title": "WakeAgain — 잠든 프로젝트 장터",
      "hero.badge": "잠든 프로젝트 장터",
      "hero.title1": "멈춰버린 프로젝트에",
      "hero.title2": "다시 기회를.",
      "hero.sub": "안 쓴 코드, 멈춘 앱, 잠든 도메인.<br />누군가에겐 그게 바로 시작점이 될 수 있어요.",
      "hero.cta_main": "내 프로젝트는 얼마일까?",
      "hero.cta_sub": "무료 · 시작가 힌트",
      "hero.cta_benefit": "짧게 진단하고, <strong>얼마에 올릴지</strong> · <strong>지금 올릴지</strong> 감을 잡으세요.",
      "hero.stat_projects": "등록 프로젝트",
      "hero.stat_interest": "관심 등록",
      "hero.stat_free": "등록 비용",
      "hero.stat_free_val": "무료",
      "hero.stat_went_live": "다시 세상으로 나간 프로젝트",
      "hero.stat_went_live_later": "추후 공개",
      "hero.stats_note": "등록 무료 · 성사는 쌓이면 공개 · 실제 숫자만",
      "live.price": "지금 가격",
      "live.time": "남은 시간",
      "live.progress": "시작가 대비 · 입찰 5명",
      "live.ecg": "LIVE",
      "live.toast": "방금 입찰",
      "problem.title": "세상 밖으로 못 나온 프로젝트들",
      "problem.p1": "매일 많은 프로젝트가 만들어집니다.",
      "problem.p2": "그중 상당수는 출시 전에 멈춥니다.",
      "problem.p3": "쓸모가 없어서가 아닙니다.",
      "problem.p4": "시간이 없거나, 인생이 바뀌거나, 홍보를 못 한 경우가 많아요.",
      "problem.bridge": "그래서 이런 일이 생깁니다.",
      "problem.c1_t": "시간은 썼는데 수익은 0",
      "problem.c1_p": "주말 몇 달을 썼는데 유저는 거의 없고, 서버·도메인 비용만 나갑니다. 아깝지만 더 하기도 어렵습니다.",
      "problem.c2_t": "팔고 싶은데 곳이 없다",
      "problem.c2_p": "커뮤니티에 올리면 채팅만 오고 가격·데모·이전 절차가 없어 무산되기 쉽습니다.",
      "problem.c3_t": "사고 싶은데 비교가 안 된다",
      "problem.c3_p": "처음부터 만들면 몇 주. 이미 만든 걸 사고 싶어도 아이디어만 있는 것과 돌아가는 게 섞여 있어 고르기 어렵습니다.",
      "buyers.eyebrow": "구매할 때",
      "buyers.title": "처음부터 다시 만들기 전에,<br /><span class=\"grad\">돌아가는 프로젝트</span>를 사세요.",
      "buyers.lead": "직접 만들어도 됩니다. 다만 시간이 더 들면, 데모가 있는 걸 사는 편이 빠를 수 있어요.<br />사는 분 추가 수수료 없음 · 수수료는 판매자 쪽에서 나갑니다.",
      "buyers.safe_badge": "안전결제",
      "buyers.safe_title": "개인 계좌로 직접 보내는 거래가 아닙니다.",
      "buyers.safe_body": "낙찰 후 <strong>PG 결제</strong>로 내고, 확인된 뒤에만 코드·계정을 받습니다. 사는 분은 합의 가격만 냅니다. (수수료 10%는 판매자)",
      "buyers.safe_s1": "1. 낙찰 후 1시간 안에 결제",
      "buyers.safe_s2": "2. 결제 확인 → 이전",
      "buyers.safe_s3": "3. 확인 후 인수 (또는 자동 확정)",
      "buyers.safe_s4": "4. 판매자 정산",
      "buyers.build_label": "직접 만들기",
      "buyers.build_t": "시간·결과가 모두 내 몫",
      "buyers.build_1": "초안만 해도 보통 몇 주",
      "buyers.build_2": "배포·결제에서 또 막힘",
      "buyers.build_3": "들인 시간이 꽤 큼",
      "buyers.buy_label": "WakeAgain에서 사기",
      "buyers.buy_t": "이미 돌아가는 화면부터",
      "buyers.buy_1": "데모·가격·입찰 수 공개",
      "buyers.buy_2": "사는 분 추가 수수료 없음",
      "buyers.buy_3": "가격 쓰기 → 결제 → 인수",
      "buyers.why_title": "여기서 사는 이유",
      "buyers.m1_t": "시간 절약",
      "buyers.m1_p": "데모가 있는 매물 위주. 몇 주 다시 만드는 시간을 아낄 수 있어요.",
      "buyers.m2_t": "가격이 보임",
      "buyers.m2_p": "지금 가격·입찰 수를 누구나 볼 수 있어요.",
      "buyers.m3_t": "사는 분 수수료 0",
      "buyers.m3_p": "사는 분은 합의 가격만. 수수료 10%는 판매자 부담.",
      "buyers.m4_t": "결제 절차",
      "buyers.m4_p": "결제 확인 전엔 이전 없음. 인수 후 정산. 신원 확인·신고도 있어요.",
      "buyers.rank_title": "살수록 커지는 구매 배지",
      "buyers.rank_lead": "사서 끝낸 횟수가 많을수록 배지가 올라갑니다. <strong>성사 기록</strong>으로 남아요.",
      "buyers.rank_scout_b": "준비 중",
      "buyers.rank_scout_n": "성사 0건",
      "buyers.rank_scout_p": "관심 등록·입찰 시작",
      "buyers.rank_starter_b": "첫 구매",
      "buyers.rank_starter_n": "성사 1건+",
      "buyers.rank_starter_p": "첫 구매 배지",
      "buyers.rank_regular_b": "단골",
      "buyers.rank_regular_n": "성사 3건+",
      "buyers.rank_regular_p": "성사 횟수 공개",
      "buyers.rank_heavy_b": "적극 구매",
      "buyers.rank_heavy_n": "성사 5건+",
      "buyers.rank_heavy_p": "눈에 띄는 배지",
      "buyers.rank_whale_b": "파워 구매",
      "buyers.rank_whale_n": "성사 10건+",
      "buyers.rank_whale_p": "가장 잘 보이는 배지",
      "buyers.rank_note": "성사 횟수 기준. 미결제가 있으면 주의 표시가 붙을 수 있어요. 점수·Lv과는 별개입니다.",
      "buyers.note": "통신판매중개 장터입니다. 절차: 결제 → 이전 → 인수. 자세한 내용은 이용약관.",
      "buyers.cta_interest": "관심 등록하기",
      "buyers.cta_market": "마켓 둘러보기",
      "svc.title": "이용 방법",
      "svc.lead": "등록 무료. 관심·입찰도 무료. 낙찰되면 사이트 결제(PG)로 진행합니다. 안 내면 다음 사람에게 넘어갈 수 있어요.",
      "svc.1_t": "1. 올리기",
      "svc.1_p": "데모·시작가를 적고 올립니다. 사람이 형식만 확인한 뒤, 보통 1~2일 안에 공개됩니다.",
      "svc.2_t": "2. 가격 쓰기",
      "svc.2_p": "지금 가격·남은 시간을 보고 금액을 씁니다. 낙찰되면 안내에 따라 빠르게 결제하세요.",
      "svc.3_t": "3. 확인 후 이전",
      "svc.3_p": "화면이 돌아가는지 먼저 확인. 코드·계정은 결제 확인 뒤에만 넘깁니다.",
      "svc.m_fee": "등록 비용",
      "svc.m_free": "무료",
      "svc.m_seller_fee": "팔리면 판매 수수료",
      "svc.m_review": "형식 확인",
      "svc.m_review_v": "1~2일",
      "svc.m_see": "공개 정보",
      "svc.m_see_v": "가격 + 시간",
      "svc.m_pay": "낙찰 후 결제",
      "svc.m_pay_v": "빠르게",
      "svc.m_skip": "미결제 시",
      "svc.m_skip_v": "다음 사람",
      "svc.m_demo": "데모",
      "svc.m_demo_v": "필수에 가깝",
      "svc.m_steps": "이전 순서",
      "svc.m_steps_v": "4단계",
      "svc.m_acct": "계정",
      "svc.m_acct_v": "웹·폰 하나",
      "metrics.title": "숫자로 보기",
      "metrics.lead": "수수료·확인 기간·입찰 단위를 한눈에.",
      "metrics.inc": "입찰 최소 단위",
      "metrics.inc_v": "+1만 원",
      "metrics.interest": "관심 등록",
      "metrics.interest_v": "1회",
      "showcase.title": "프로젝트 자랑",
      "showcase.cta": "진단 후 자랑하기",
      "showcase.board": "보드 보기",
      "showcase.empty": "아직 자랑이 없어요.",
      "reviews.title": "이용 후기",
      "reviews.loading": "불러오는 중…",
      "reviews.write": "후기 남기기",
      "why.title": "왜 WakeAgain인가요?",
      "why.lead": "잠든 프로젝트를 사고파는 장터입니다. 거래는 단계로 진행하고, 책임은 판매자·구매자에게 있어요.",
      "safe4.kicker": "거래 4단계",
      "safe4.title": "이렇게 진행됩니다",
      "safe4.s1_t": "결제",
      "safe4.s1_d": "낙찰 후 사이트 결제(PG)",
      "safe4.s2_t": "결제 확인 후 이전",
      "safe4.s2_d": "확인 전 코드·계정 금지",
      "safe4.s3_t": "확인 · 인수",
      "safe4.s3_d": "인수, 또는 48시간 후 자동 확정",
      "safe4.s4_t": "정산",
      "safe4.s4_d": "확정 후 판매자 정산 · 수수료 10%",
      "safe4.foot": "단계마다 확인·신고로 관리합니다.",
      "safe4.legal_title": "법적 고지",
      "safe4.legal_1": "통신판매중개자이며 거래 당사자가 아닙니다.",
      "safe4.legal_2": "품질·사기 피해의 1차 책임은 판매자·구매자에게 있습니다.",
      "safe4.legal_3": "형식 검수·신용 점수는 보증·보험이 아닙니다.",
      "safe4.legal_4": "성사·대금·자산 이전을 플랫폼이 보증하지 않습니다.",
      "why.1_t": "단계별 확인",
      "why.1_p": "입찰은 이메일 인증으로 시작. 실명·휴대폰은 낙찰 후, 계좌는 정산 때. 연락처는 목록에 안 나가요.",
      "why.2_t": "쉬운 상태·시작가",
      "why.2_p": "「초안」「써 볼 수 있음」처럼 쉬운 말로 상태를 고르고 시작가를 잡습니다.",
      "why.2_a": "상태 고르는 법 ›",
      "why.3_t": "관심 있는 사람 모으기",
      "why.3_p": "관심 등록·입찰로 사고 싶은 사람을 모읍니다.",
      "why.4_t": "이전 순서 안내",
      "why.4_p": "결제 확인 후 코드·도메인·계정 넘기기 순서를 안내합니다. 이전은 당사자끼리 합니다.",
      "list.title": "최근 매물",
      "list.loading": "불러오는 중…",
      "list.public": "지금 가격은 누구나 볼 수 있어요.",
      "list.all": "전체",
      "list.empty_cat": "이 분류에 매물이 없어요.",
      "list.search_label": "검색",
      "list.search_ph": "제목 · 키워드",
      "list.search_btn": "검색",
      "list.search_clear": "지우기",
      "list.empty_search": "검색 결과가 없어요.",
      "list.more": "더 보기",
      "list.none": "아직 공개 매물이 없어요.",
      "list.empty_sample": "이 분류 예시가 없어요.",
      "list.source_api": "공개 경매 · 지금 가격 실시간",
      "list.source_preview": "아직 매물이 없어 예시입니다.",
      "list.badge_sample": "예시",
      "list.badge_sold": "팔림",
      "list.badge_ended": "끝남",
      "list.badge_live": "입찰 중",
      "list.badge_review": "검토 중",
      "list.badge_wait": "입찰 대기",
      "list.price_now": "지금 가격",
      "list.price_start": "시작가",
      "list.price_now_pub": "지금 가격",
      "list.price_start_pub": "시작가",
      "list.price": "가격",
      "list.inquire": "문의",
      "list.cta_bid": "가격 쓰기",
      "list.cta_view": "자세히 보기",
      "list.ended_short": "마감",
      "list.auction_ended": "경매 종료",
      "cta.title": "프로젝트에 다시 기회를.",
      "cta.strong": "멈춘 프로젝트를 다시 살립니다.",
      "cta.fine": "올리기·관심·입찰은 쉽게. 등록 무료. 팔리면 규칙: 빠른 결제, 미결제 시 다음 사람, 판매 수수료 10%.",
      "cta.note": "쉽게 시작 · 팔리면 판매 수수료 10% · 사는 분은 합의 가격만",
      "footer.brand": "잠든 코드도 누군가에겐 자산입니다. 다시 쓰일 기회를 만듭니다.",
      "footer.op": "운영 · 코어랩스(CoreLabs)",
      "footer.contact": "문의: corelabs.studio@gmail.com",
      "footer.tagline": "WakeAgain · 잠든 프로젝트 장터 · CoreLabs",
      "footer.broker": "본 플랫폼은 통신판매중개자이며, 거래되는 상품의 품질과 내용은 판매자가 책임집니다.",
      "footer.broker_sub": "이용자 간 사기·분쟁의 1차 책임은 당사자에게 있습니다. WakeAgain(코어랩스)은 거래 당사자가 아니며, 성사·대금·자산 이전을 보증하지 않습니다.",
      "footer.terms": "이용약관",
      "footer.privacy": "개인정보처리방침",
      "footer.why": "왜 WakeAgain인가요",
      "diag.cta": "무료 진단",
      "diag.page_title": "내 프로젝트는 얼마일까?",
      "app.auth_title": "쉽게 시작하세요.",
      "app.auth_lede": "웹·폰 같은 계정. 올리고 가격 쓰고, 낙찰되면 결제·확인으로 끝냅니다.",
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
      "nav.market": "Market",
      "nav.home": "Home",
      "nav.buyers": "How trading works",
      "nav.trade": "How trading works",
      "nav.showcase": "Showcase",
      "nav.safety": "Avoid scams",
      "nav.guide": "Guide",
      "nav.metrics": "Numbers",
      "nav.login": "Log in",
      "nav.app": "Get app",
      "nav.list": "List project",
      "nav.list_short": "List",
      "nav.site": "Site",
      "nav.logout": "Log out",
      "nav.profile": "Profile",
      "nav.notif": "Alerts",
      "nav.fees": "Fees",
      "nav.interest": "Interest",
      "nav.more_market": "Browse market",
      "nav.account": "Account",
      "skip": "Skip to content",
      "doc.title": "WakeAgain — marketplace for paused projects",
      "hero.badge": "Marketplace for paused projects",
      "hero.title1": "Give paused projects",
      "hero.title2": "another shot.",
      "hero.sub": "Unfinished code, idle apps, sleeping domains.<br />Someone else may need exactly that start.",
      "hero.cta_main": "What’s my project worth?",
      "hero.cta_sub": "Free · start-price hint",
      "hero.cta_benefit": "Quick check: <strong>what to price</strong> and <strong>whether to list now</strong>.",
      "hero.stat_projects": "Listed",
      "hero.stat_interest": "Interest",
      "hero.stat_free": "Listing fee",
      "hero.stat_free_val": "Free",
      "hero.stat_went_live": "Projects back in the world",
      "hero.stat_went_live_later": "Coming later",
      "hero.stats_note": "Free to list · real closes only · count opens later",
      "live.price": "Price now",
      "live.time": "Time left",
      "live.progress": "vs start · 5 bids",
      "live.ecg": "LIVE",
      "live.toast": "New bid",
      "problem.title": "Projects that never shipped",
      "problem.p1": "Lots of projects get built every day.",
      "problem.p2": "Many stop before launch.",
      "problem.p3": "Not because they’re useless.",
      "problem.p4": "Often no time, life changed, or no marketing.",
      "problem.bridge": "So this happens:",
      "problem.c1_t": "Time spent, revenue still zero",
      "problem.c1_p": "Months of weekends, almost no users—and server bills keep coming. Hard to continue.",
      "problem.c2_t": "Want to sell, nowhere to go",
      "problem.c2_p": "Community posts get chats, but no clear price, demo, or handoff—deals die.",
      "problem.c3_t": "Want to buy, hard to compare",
      "problem.c3_p": "Building from zero takes weeks. Idea-only vs running demos are mixed, so choosing is hard.",
      "buyers.eyebrow": "When you buy",
      "buyers.title": "Before you rebuild from zero,<br />buy something that <span class=\"grad\">already runs</span>.",
      "buyers.lead": "You can build it yourself. If that costs more weeks, buying a demo-ready project can be faster.<br />No extra fee for buyers · the fee comes from the seller.",
      "buyers.safe_badge": "Safe pay",
      "buyers.safe_title": "Not a private bank transfer to the seller.",
      "buyers.safe_body": "After you win, pay with <strong>PG</strong>. You get code/accounts only after payment is confirmed. Buyers pay the agreed price only. (Seller pays 10% fee.)",
      "buyers.safe_s1": "1. Pay within 1 hour of winning",
      "buyers.safe_s2": "2. Confirmed → transfer",
      "buyers.safe_s3": "3. Accept (or auto-confirm)",
      "buyers.safe_s4": "4. Seller payout",
      "buyers.build_label": "Build it yourself",
      "buyers.build_t": "Your time, your result",
      "buyers.build_1": "Even a draft often takes weeks",
      "buyers.build_2": "Deploy & payments still block you",
      "buyers.build_3": "Your time is not free",
      "buyers.buy_label": "Buy on WakeAgain",
      "buyers.buy_t": "Start from a running demo",
      "buyers.buy_1": "Demo, price, bid count public",
      "buyers.buy_2": "No extra buyer fee",
      "buyers.buy_3": "Bid → pay → accept",
      "buyers.why_title": "Why buy here",
      "buyers.m1_t": "Save time",
      "buyers.m1_p": "Listings with demos first. Skip weeks of rebuild.",
      "buyers.m2_t": "Prices are public",
      "buyers.m2_p": "Anyone can see live price and bid count.",
      "buyers.m3_t": "Buyer fee: 0",
      "buyers.m3_p": "You pay the agreed price. Sellers pay 10%.",
      "buyers.m4_t": "Payment steps",
      "buyers.m4_p": "No transfer before payment. Settle after accept. ID check & reports too.",
      "buyers.rank_title": "Buyer badges that grow",
      "buyers.rank_lead": "More completed buys → higher badge. It’s a <strong>track record</strong>.",
      "buyers.rank_scout_b": "Getting ready",
      "buyers.rank_scout_n": "0 completed",
      "buyers.rank_scout_p": "Watchlist & bids",
      "buyers.rank_starter_b": "First buy",
      "buyers.rank_starter_n": "1+ completed",
      "buyers.rank_starter_p": "First-buy badge",
      "buyers.rank_regular_b": "Regular",
      "buyers.rank_regular_n": "3+ completed",
      "buyers.rank_regular_p": "Completed count public",
      "buyers.rank_heavy_b": "Active buyer",
      "buyers.rank_heavy_n": "5+ completed",
      "buyers.rank_heavy_p": "Highlighted badge",
      "buyers.rank_whale_b": "Power buyer",
      "buyers.rank_whale_n": "10+ completed",
      "buyers.rank_whale_p": "Most visible badge",
      "buyers.rank_note": "Based on completed buys. Missed payments may add a caution. Separate from score & Lv.",
      "buyers.note": "Marketplace intermediary. Flow: pay → transfer → accept. See Terms for details.",
      "buyers.cta_interest": "Register interest",
      "buyers.cta_market": "Browse market",
      "svc.title": "How it works",
      "svc.lead": "Listing free. Interest & bids free. After you win, pay on-site (PG). Miss payment → next bidder.",
      "svc.1_t": "1. List",
      "svc.1_p": "Add a demo and start price. Free to list. We check format; usually live in 1–2 days.",
      "svc.2_t": "2. Bid",
      "svc.2_p": "See price & time left, write your amount. Winners pay quickly per the guide.",
      "svc.3_t": "3. Check, then transfer",
      "svc.3_p": "Confirm it runs. Code/accounts only after payment is confirmed.",
      "svc.m_fee": "Listing fee",
      "svc.m_free": "Free",
      "svc.m_seller_fee": "Seller fee if sold",
      "svc.m_review": "Format check",
      "svc.m_review_v": "1–2 days",
      "svc.m_see": "What’s public",
      "svc.m_see_v": "Price + timer",
      "svc.m_pay": "Pay after win",
      "svc.m_pay_v": "Promptly",
      "svc.m_skip": "If unpaid",
      "svc.m_skip_v": "Next bidder",
      "svc.m_demo": "Demo",
      "svc.m_demo_v": "Nearly required",
      "svc.m_steps": "Transfer steps",
      "svc.m_steps_v": "4 steps",
      "svc.m_acct": "Account",
      "svc.m_acct_v": "Web + phone",
      "metrics.title": "By the numbers",
      "metrics.lead": "Fees, check time, bid step—at a glance.",
      "metrics.inc": "Min bid step",
      "metrics.inc_v": "+₩10,000",
      "metrics.interest": "Interest",
      "metrics.interest_v": "Once",
      "showcase.title": "Showcase",
      "showcase.cta": "Diagnose, then post",
      "showcase.board": "Board",
      "showcase.empty": "No posts yet.",
      "reviews.title": "Reviews",
      "reviews.loading": "Loading…",
      "reviews.write": "Write a review",
      "why.title": "Why WakeAgain?",
      "why.lead": "A market for paused projects. Deals run in steps; liability stays with buyer and seller.",
      "safe4.kicker": "4 deal steps",
      "safe4.title": "How a deal runs",
      "safe4.s1_t": "Pay",
      "safe4.s1_d": "On-site payment after you win",
      "safe4.s2_t": "Transfer after paid",
      "safe4.s2_d": "No code/accounts before confirm",
      "safe4.s3_t": "Check · accept",
      "safe4.s3_d": "Accept, or auto-confirm in 48h",
      "safe4.s4_t": "Payout",
      "safe4.s4_d": "Seller paid after confirm · 10% fee",
      "safe4.foot": "We manage each step with checks and reports.",
      "safe4.legal_title": "Legal notice",
      "safe4.legal_1": "We are a marketplace intermediary, not a party to the deal.",
      "safe4.legal_2": "Primary liability for quality and fraud sits with buyer and seller.",
      "safe4.legal_3": "Format review and site credit are not guarantees or insurance.",
      "safe4.legal_4": "We do not guarantee closing, payment, or asset transfer.",
      "why.1_t": "Checks in stages",
      "why.1_p": "Bid with email verify. Name/phone after you win; bank for payout. Contact stays off public lists.",
      "why.2_t": "Simple status & start price",
      "why.2_p": "Pick easy states like “draft” or “usable” and set a start price.",
      "why.2_a": "How to pick status ›",
      "why.3_t": "Find interested buyers",
      "why.3_p": "Interest and bids gather people who want it.",
      "why.4_t": "Transfer order",
      "why.4_p": "After payment, we guide code/domain/account handoff. Parties transfer between themselves.",
      "list.title": "Latest listings",
      "list.loading": "Loading…",
      "list.public": "Live prices are public.",
      "list.all": "All",
      "list.search_label": "Search",
      "list.search_ph": "Title · keywords",
      "list.search_btn": "Search",
      "list.search_clear": "Clear",
      "list.empty_search": "No results.",
      "list.more": "Show more",
      "list.none": "No listings yet.",
      "list.empty_sample": "No samples here.",
      "list.source_api": "Live auction · public price",
      "list.source_preview": "No live listings yet — samples shown.",
      "list.badge_sample": "Sample",
      "list.badge_sold": "Sold",
      "list.badge_ended": "Ended",
      "list.badge_live": "Live",
      "list.badge_review": "Review",
      "list.badge_wait": "Waiting",
      "list.price_now": "Now",
      "list.price_start": "Start",
      "list.price_now_pub": "Now",
      "list.price_start_pub": "Start",
      "list.price": "Price",
      "list.inquire": "Ask",
      "list.cta_bid": "Bid",
      "list.cta_view": "View",
      "list.ended_short": "Ended",
      "list.auction_ended": "Auction ended",
      "cta.title": "Another shot for projects.",
      "cta.strong": "We bring paused projects back.",
      "cta.fine": "List, watch, bid easily. Free to list. If it sells: pay fast, next bidder if not, 10% seller fee.",
      "cta.note": "Easy start · 10% seller fee · buyers pay agreed price only",
      "footer.brand": "Paused code is still an asset. We help it get used again.",
      "footer.op": "Operated by CoreLabs",
      "footer.contact": "Contact: corelabs.studio@gmail.com",
      "footer.tagline": "WakeAgain · market for paused projects · CoreLabs",
      "footer.broker": "This platform is an intermediary. Product quality and content are the seller’s responsibility.",
      "footer.broker_sub": "Primary liability for fraud or disputes sits with the parties. WakeAgain (CoreLabs) is not a party to the deal and does not guarantee completion, payment, or asset transfer.",
      "footer.terms": "Terms",
      "footer.privacy": "Privacy",
      "footer.why": "Why WakeAgain",
      "diag.cta": "Free diagnose",
      "diag.page_title": "What’s my project worth?",
      "app.auth_title": "Start easily.",
      "app.auth_lede": "One account on web and phone. List, bid, then pay and finish after you win.",
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

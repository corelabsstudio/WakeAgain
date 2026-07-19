# WakeAgain → Variant Compose 용 정리글

> [variant.com](https://variant.com) Compose에 **섹션별로 나눠 붙여넣기** 하세요.  
> 한 번에 전체를 넣기보다: **① 히어로 → 마음에 드는 톤 선택 → New Chat From Design → ② 다음 섹션** 순서가 좋습니다.

---

## 1) 사이트 한 줄 소개 (Variant에 맨 위 고정)

**제품명:** WakeAgain (브랜드명은 영문만)

**무엇을 하는 사이트인가**  
만들어 두고 홍보를 못 해서 **잠든(방치된) 앱·프로그램·프로토타입**을 **경매로 사고파는** 마켓플레이스입니다.  
판매자는 더 이상 안 키울 프로젝트를 올리고, 구매자는 0부터 만들기 전에 **이미 손댄 베이스**를 입찰로 이어받습니다.

**한 줄 포지션**  
*잠든 프로그램이 다시 경매로 이어지는 곳. Still running.*

**플랫폼**  
웹사이트 + Google Play + Apple App Store (같은 계정·같은 데이터)

**타겟**  
- 판매자: 사이드 프로젝트 정리, 팀 해산 후 코드만 남은 사람, 서버만 꺼 둔 창업자  
- 구매자: 리런칭·개조 재료가 필요한 메이커, 스토리 있는 제품을 이어 키우고 싶은 사람

**톤 (필수)**  
- 신뢰감 · 청결 · 전문적  
- **Soft Dark** (눈에 덜 피로한 어두운 배경, 순흑·순백 풀스크린 금지)  
- 메타포: **바닥에 버려진 컴퓨터/기기, 화면만 아직 살아 있음 (process still running)**  
- AI 보라색 그라데이션 · 네온 · “혁신적인 솔루션” 류 카피 **금지**  
- 이모지 아이콘 금지 (SVG 아이콘)

**원하는 역동감**  
시네마틱 입구(입장 버튼) · 스크롤 등장 · 카드 stagger · 타이머/숫자 카운트 · 히어로 시퀀스  
과한 3D·정신없는 파티클보다는 **의미 있는 모션** (살아 있는 프로세스, 경매 긴박감)

---

## 2) Variant Compose — 전체 프롬프트 (복붙용 영문 권장 버전)

Variant가 영어 프롬프트에 더 잘 반응하는 경우가 많아, **디자인 지시는 영어 + 화면에 넣을 카피는 한글**로 적었습니다.

```text
Design a cinematic marketing landing page for "WakeAgain" — a trustworthy auction marketplace for abandoned / dormant digital products (apps, prototypes, SaaS tools that died because founders couldn't market them).

Brand name appears only in English: WakeAgain.
Body UI language is primarily Korean (use the Korean copy provided below). Short English hooks only: "Still running."

Visual metaphor: an abandoned laptop on the ground, but the program is still running — soft glow, alive process, not scary, not neon cyberpunk.

Style: Soft dark UI, clean, premium trust. Soft charcoal background (#0F1318–#12161C), teal/mint accents (#3D9B8F, #7AF0DC), muted slate text. No purple AI gradients. No pure black or pure white full fields. Eye-friendly, calm but dynamic.

Motion feel: cinematic entrance gate with "Enter site" button, scroll reveals, staggered auction cards, live countdown timers, subtle parallax on the device mockup. High energy but professional (like a high-end product launch, not a party site).

Layout: editorial large display typography, clear hierarchy, marketplace + auction + trust sections.

Include:
0) Full-screen cinematic intro gate before the site
1) Hero with search
2) Live auction stats strip
3) Category filters
4) Live auction cards with current bid + time left + bid CTA
5) Who it's for (sellers / buyers)
6) How it works (3 steps) + safety track
7) Trust & FAQ
8) Final CTA

Use the exact Korean marketing copy below for headlines and body text.
```

---

## 3) 섹션별 카피 (화면에 넣을 문구 · 그대로 사용)

### 0) 시네마틱 인트로 (입구)

| 역할 | 문구 |
|------|------|
| 브랜드 | WakeAgain |
| 상태 | process still running |
| 헤드 | 삭제하지 마세요. |
| 서브 | 잠든 프로그램이 다시 경매로 이어지는 입구입니다. |
| 메인 버튼 | 사이트 들어가기 → |
| 보조 | 바로 본문 보기 |

---

### 1) 네비

| 역할 | 문구 |
|------|------|
| 로고 | WakeAgain |
| 링크 | 경매 · 이용 방법 · 신뢰 · 관심 |
| Primary CTA | 올리기 |

---

### 2) 티커 (선택)

- 진행 중 경매 3  
- 오늘 관심 등록 대기  
- 성사 시만 수수료  
- 데모 있는 건 우선  
- 웹·앱 같은 계정  

---

### 3) 히어로

| 역할 | 문구 |
|------|------|
| Eyebrow | 오픈 준비 중 |
| English hook | Still running. |
| H1 | 삭제하지 마세요. |
| 서브헤드 | 멈춘 앱은, 여기서 경매로 이어집니다. |
| 본문 | 홍보할 힘이 없어 서버만 꺼 둔 툴·프로토타입·출시 후 방치된 제품. 스토리와 데모를 올리면, 이어 키울 사람이 입찰합니다. |
| 검색 placeholder | 예: 타이머, 영수증, SaaS… |
| 검색 버튼 | 찾기 |
| Primary CTA | 프로젝트 올리기 |
| Secondary CTA | 경매 둘러보기 |
| Trust chips | 성사 시만 수수료 · 데모 있는 건 우선 · 웹·앱 같은 계정 |
| 기기 캡션 | 바닥에 둔 기기에서도, 프로그램은 아직 살아 있습니다. |
| 기기 상태 | 실행 중 · 방치 94일 |

---

### 4) 라이브 현황 스트립

| 숫자 | 라벨 |
|------|------|
| 3 | 진행 중 경매 |
| 40 | 오늘 입찰 수(미리보기) |
| ~10% | 성사 시 수수료 |
| 타이머 | 가장 빠른 마감까지 |

---

### 5) 카테고리 필터

전체 · SaaS · 모바일 · 프로토타입 · 출시 후 방치 · 도구·유틸

---

### 6) 경매 섹션

| 역할 | 문구 |
|------|------|
| 키커 | 01 · 경매 |
| H2 | 지금 입찰이 열린 프로젝트 |
| 설명 | 오픈 전 미리보기입니다. 가격과 시간이 보이면, 이미 장은 움직이기 시작한 겁니다. |
| 링크 | 전체 보기 → |

**카드 예시 1 — FocusTimer**  
- 뱃지: 진행 중  
- 태그: SaaS · 베타  
- 한 줄: 집중 타이머. 홍보 없이 3개월 정지. 코드·도메인 포함.  
- 현재 입찰가 / 남은 시간  
- 버튼: 입찰 · 관심  
- 풋: 입찰 12 · 최소 +₩10,000  

**카드 예시 2 — Receiptly**  
- 태그: 모바일 · 프로토타입  
- 한 줄: 경비 영수증 앱. 핵심 화면까지 구현, 스토어 미등록.  
- 풋: 입찰 7 · 즉시구매 ₩1,200,000  

**카드 예시 3 — ShelfNote**  
- 뱃지: 곧 마감  
- 태그: 출시 후 방치  
- 한 줄: 출시 1개월 후 방치. 코드·도메인 양도 가능.  
- 풋: 입찰 21 · 마지막 입찰 방금 전  

---

### 7) 이런 분께

| 역할 | 문구 |
|------|------|
| 키커 | 02 · 대상 |
| H2 | 한쪽은 정리하고, 한쪽은 이어 받습니다. |

**올리시는 분**  
- 제목: 폴더에만 남은 프로젝트  
- 사이드 프로젝트를 정리하고 싶다  
- 팀은 해산됐고, 코드는 남았다  
- 홍보할 힘이 없어서 서버만 꺼 둔 상태다  
- 링크: 프로젝트 올리기 →  

**찾으시는 분**  
- 제목: 0부터 만들기 전, 이미 있는 베이스  
- 이미 손댄 코드를 보고 싶다  
- 리런칭·개조할 재료가 필요하다  
- 스토리가 있는 제품을 이어 키우고 싶다  
- 링크: 관심 구매자 등록 →  

---

### 8) 이용 방법

| 역할 | 문구 |
|------|------|
| 키커 | 03 · 흐름 |
| H2 | 세 단계면 장이 돌아갑니다. |

1. **등록** — 한 줄·스토리·데모·시작가. 실행 흔적이 있으면 더 빨리 열립니다.  
2. **경매** — 현재가와 남은 시간이 공개됩니다. 관심 있는 사람이 입찰합니다.  
3. **이전** — 낙찰 후 자산 이전. 거래가 성사될 때만 수수료가 붙습니다.  

**안전 트랙**  
A 검토(데모·스토리 확인) → B 입찰(가격·시간 공개) → C 합의(연락 채널 확인) → D 이전(자산 인도)

---

### 9) 신뢰

| 역할 | 문구 |
|------|------|
| 키커 | 04 · 신뢰 |
| H2 | 믿을 수 있어야 입찰이 생깁니다. |
| 설명 | 검토 → 입찰 → 이전. 단계를 숨기지 않습니다. |

- **데모 우선** — 실행 흔적 있는 건만 전면  
- **성사 시 수수료** — 등록만으로 과금 없음  
- **웹·앱 동일** — 한 계정으로 이어짐  
- **소스는 성사 후** — 핵심 소스는 낙찰·합의 후 이전  
- **이전 절차** — 연락 확인 → 합의 → 자산 이전  

**FAQ**  
- 입찰은 어떻게 하나요? → 로그인 후 카드의 입찰로 참여. 현재가와 남은 시간 표시.  
- 수수료는 언제 내나요? → 거래 성사 시에만 (목표 약 10%).  
- 사기는 어떻게 막나요? → 데모·스토리 검토, 연락 확인, 성사 후 이전 절차.

---

### 10) 최종 CTA

| 역할 | 문구 |
|------|------|
| 브랜드 | WakeAgain |
| H2 | 폴더에만 있던 그 프로젝트, 아직 값이 있습니다. |
| 본문 | 빈 아이디어가 아니라, 이미 손댄 프로그램을 연결합니다. |
| Primary | 프로젝트 올리기 |
| Secondary | 관심 등록 |

---

### 11) 푸터

WakeAgain · 잠든 프로그램을 다시 경매로  
링크: 경매 · 올리기 · 앱 · 신뢰  
보조: 오픈 준비 중 · wakeagain.com 등록 예정  

---

## 4) Variant에 넣을 때 추천 순서

### Step A — 히어로만 (가장 중요)
Compose에 아래를 붙여넣기:

```text
WakeAgain landing hero only.

Product: auction marketplace for abandoned apps/programs that died from lack of marketing.
Tone: trustworthy, clean, soft dark, cinematic, dynamic but professional.
Metaphor: abandoned computer on the ground, screen still glowing, process still running.

Korean copy:
- Brand: WakeAgain
- Hook: Still running.
- H1: 삭제하지 마세요.
- Sub: 멈춘 앱은, 여기서 경매로 이어집니다.
- Body: 홍보할 힘이 없어 서버만 꺼 둔 툴·프로토타입·출시 후 방치된 제품. 스토리와 데모를 올리면, 이어 키울 사람이 입찰합니다.
- CTAs: 프로젝트 올리기 / 경매 둘러보기
- Search placeholder: 예: 타이머, 영수증, SaaS…
- Trust chips: 성사 시만 수수료 · 데모 있는 건 우선 · 웹·앱 같은 계정
- Caption: 바닥에 둔 기기에서도, 프로그램은 아직 살아 있습니다.

Make it highly dynamic: large display type, scroll energy, soft teal accents, no purple AI look, no neon cyberpunk.
Include abandoned-device visual with live bid price and countdown.
```

→ 스크롤하며 여러 변형 중 **하나 고르기**  
→ **New Chat From Design** 으로 이어가기  

### Step B — 경매 섹션
```text
Continue from selected design system.
Section: Live auctions for WakeAgain.
Korean:
- Title: 지금 입찰이 열린 프로젝트
- Desc: 오픈 전 미리보기입니다. 가격과 시간이 보이면, 이미 장은 움직이기 시작한 겁니다.
Show 3 auction cards with app UI mock thumbnails, current bid, countdown timer, Bid button, interest button.
Featured card "곧 마감". Soft dark, clean, trustworthy, dynamic hover/scroll motion.
Cards: FocusTimer, Receiptly, ShelfNote with the copy provided earlier.
```

### Step C — 대상 / 이용방법 / 신뢰 / CTA
같은 방식으로 섹션 카피만 붙여넣고 **New Chat From Design** 반복.

### Step D — 시네마틱 입구 (선택)
```text
Full-screen cinematic website entrance gate for WakeAgain before the main site.
Korean: 삭제하지 마세요. / 잠든 프로그램이 다시 경매로 이어지는 입구입니다.
Buttons: 사이트 들어가기 → / 바로 본문 보기
Soft dark, teal glow, grid floor, process still running, premium cinematic, not scary.
```

---

## 5) 디자인 제약 체크리스트 (Variant 프롬프트 끝에 항상 붙이기)

```text
Constraints:
- Soft dark only (eye-friendly), not pure black, not pure white
- Teal/mint trust palette, NO purple/pink AI gradients
- No emoji icons
- Brand name English only: WakeAgain
- Most UI text in Korean
- Dynamic / cinematic motion but still clean and trustworthy for a marketplace/auction product
- Mobile responsive
- Large editorial typography
- Auction UI must show: current bid + time remaining + primary bid CTA
```

---

## 6) 피해야 할 카피 (AI 기본값)

- “혁신적인 솔루션”  
- “비즈니스를 한 단계 성장”  
- “All-in-one platform”  
- 근거 없는 “1만 유저” 등 허위 수치  
- 과도한 영문 장문  

---

*파일 위치: 바탕화면 `\WakeAgain\Variant_Compose용_브리프.md`  
*동일 복사본: `projects\WakeAgain\docs\Variant_Compose용_브리프.md` (아래 생성)*

# WakeAgain Design System — MASTER

> 사용자 확정 2026-07-18 · ui-ux-pro-max + 수동 조정  
> **모드:** Soft Dark (눈 피로↓) · **톤:** 신뢰·청결 · **메타포:** 버려진 PC에 아직 돌아가는 프로그램  
> **v3 개선 (2026-07-19):** 디스플레이 타이포 강화 · 바닥 메타포 · 카테고리 스트립 · 경매 태그 · 모바일 sticky CTA · 카피 압축  
> **v4 개선 (2026-07-19):** 히어로 검색 · 티커 · 라이브 현황 · 카테고리 필터 동작 · 입찰 입력 UI · 안전 트랙 · 노이즈 텍스처  
> **v5 모션 (2026-07-19):** 히어로 시퀀스 · 스크롤 progress · stagger · 숫자 카운트업 · 경미 패럴랙스 · 곧마감 pulse · reduced-motion

## Product

| 항목 | 값 |
|------|-----|
| Brand | **WakeAgain** (영문만) |
| 제품 | 홍보 못 해 잠든 앱/프로그램 경매·거래 |
| 채널 | Web + Play + App Store (같은 API) |
| 언어 | 브랜드 영문 · 본문 **한글 위주** · 단순 영어만 최소 |

## Visual Metaphor

- 바닥에 방치된 노트북/기기, **화면만 아직 살아 있음**
- 코드·UI 카드가 희미하게 빛남 (강렬한 네온 금지)
- 캡처 참고: 큰 타이포·여백·에디토리얼 구조 **느낌만** (빨강 풀블리드 금지)

## Pattern

**Marketplace + Auction + Trust**

1. Hero (가치 + List / Browse)
2. Live auctions (입찰가·남은 시간)
3. 이런 분께
4. How it works
5. Trust / Safety
6. CTA

## Style

**Soft UI Evolution · Soft Dark**

- 부드러운 깊이, 낮은 대비 배경, 카드만 살짝 뜸
- 그림자: 소프트 다층 (과한 글로우 금지)
- radius: 12–16px
- motion: 150–300ms, `prefers-reduced-motion` 존중

## Color Tokens (Soft Dark · 눈 피로↓)

| Role | Hex | CSS |
|------|-----|-----|
| Background | `#12161C` | `--bg` |
| Surface | `#1A2029` | `--surface` |
| Surface 2 | `#222A35` | `--surface-2` |
| Border | `#2E3846` | `--border` |
| Text | `#E6EAF0` | `--ink` |
| Muted | `#9AA3B2` | `--muted` |
| Primary | `#3D9B8F` | `--primary` |
| Primary soft | `rgba(61,155,143,0.14)` | `--primary-soft` |
| CTA | `#2F9E8C` | `--cta` |
| On CTA | `#041512` | `--on-cta` |
| Bid / money | `#7AF0DC` → strong `#9EF6E6` | `--bid` / `--bid-strong` |
| Link (본문) | `#6EC4B8` | `--link` (입찰가와 분리) |
| Warning | `#E7B34E` | `--warn` |
| Danger | `#E85D6A` | `--danger` |
| Focus ring | `#5EEAD4` | `--ring` |

**배경 원칙:** 순흑 `#000` · 순백 `#FFF` 전체면 사용 금지.  
본문 대비율 ≥ 4.5:1 (`#E6EAF0` on `#12161C`).

## Typography

| Role | Font | Notes |
|------|------|--------|
| Display / H1 | Figtree 700–800 | 캡처처럼 **크게**, 자간 -0.03em |
| Body | Pretendard / Noto Sans KR | 16–17px, line-height 1.6 |
| Mono (가격·타이머) | ui-monospace | 입찰가·남은 시간 tabular |

## Components

### Auction card
- 썸네일/비주얼 영역 (소프트 그라데이션 목업)
- 제목 · 한 줄
- **현재 입찰가** + **남은 시간**
- CTA: `입찰하기` (primary), secondary `관심`

### Nav
- Logo: WakeAgain
- Links: 경매 · 이용방법 · 신뢰
- Buttons: `관심 등록` · `올리기`

## Motion

- reveal: 18px translateY + fade, 0.5s
- hover card: translateY -2px, 200ms
- timer: no blink spam; subtle opacity only if needed
- reduced-motion: disable transform animations

## Anti-patterns

- AI 퍼플 그라데이션
- 이모지 아이콘
- 강렬 네온 / 순흑 OLED 풀스크린
- 과도한 장식 애니메이션
- 영문 장문 카피

## Stack

HTML + CSS + 기존 FastAPI static (HTML+Tailwind 아님, 커스텀 CSS 토큰)

## Pre-delivery

- [ ] SVG icons only
- [ ] cursor-pointer on clickables
- [ ] hover 150–300ms
- [ ] contrast AA
- [ ] focus visible
- [ ] reduced-motion
- [ ] 375 / 768 / 1024 / 1440

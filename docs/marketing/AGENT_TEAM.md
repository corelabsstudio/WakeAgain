# WakeAgain 마케팅 에이전트 팀 (Harness)

> 빌더 조쉬형 구조: **Context → Template → SOP → 역할 분리 → 사람 승인 후 발행**  
> 한 요청 = **WakeAgain only**. 브랜드 표기는 영문 **WakeAgain**.

---

## 불러오기 / 실행 트리거

- **「웨이크어게인 마케팅」** / **「WakeAgain 마케팅」** / **「웨이크어게인 SEO」** / **「WakeAgain SEO」**
- 스케줄: `docs/marketing/DAILY_SEO_PROMPT.md` 일일 발화
- 제품 개발 이어하기: `BRAND.md` 트리거 (`WakeAgain 이어서` 등)와 **마케팅은 분리** 가능

### 시작 시 읽을 파일 (순서)

1. `docs/marketing/Context/ONE_PAGER.md`
2. 이 파일 (`AGENT_TEAM.md`)
3. `docs/marketing/DAILY_SEO_PROMPT.md` (일일 SEO 시)
4. 필요 시 루트 `BRAND.md` · `copy.md` · `promo/POST_COPY.md`

---

## 역할 (Sub-agents)

| 역할 | 책임 | 산출 | 안 함 |
|------|------|------|--------|
| **Research** | 인디/MVP 방치·수익화 이슈 선별 | 이슈 목록 or `NO_NEWS_TODAY` | 본문 작성, 수익 보장 |
| **SEO Writer** | 풀 SEO 1편 | `public/blog/<slug>.html`, index/sitemap 초안 | 금지 문구, 배포 push |
| **Asset** (선택) | OG·카드 브리프 | `Templates/og-brief.md` | 로고 임의 변형·RoadLog 톤 |
| **Review** | 브랜드·보장 문구·중복 검사 | PASS / FAIL | 새 주장 추가 |
| **Publisher** | 커밋·배포·티스토리 | 라이브 URL | **Review PASS 전 배포 금지** |

---

## 라우팅 규칙

| 의도 | 파이프 |
|------|--------|
| 일일 SEO | Research → SEO Writer → Review → (승인) Publisher |
| 짧은 홍보 3종 | Writer(카피) → Review → 복붙용 출력만 |
| 매물 유도 캠페인 | copy.md CTA + sell/showcase · 허위 매물 금지 |
| RoadLog | **거절·전환** → RoadLog 마케팅 하네스 |
| ReachKit | 본체 마케팅과 분리 |

---

## 일일 SEO 파이프 (기본)

```text
1 Research
   - DAILY_SEO_PROMPT 필터
   - 0건 → NO_NEWS_TODAY 종료
2 SEO Writer
   - public/blog/<slug>.html (Templates/blog.md)
   - blog/index.html · sitemap.xml
3 Review
   - 수익/성사 보장 없음
   - 영문 WakeAgain 표기
   - slug 중복·면책
4 Publisher (사람 승인 권장)
   - git commit/push
   - 티스토리: 토큰 있을 때만 (RoadLog tools 경로)
```

상세: [`DAILY_SEO_PROMPT.md`](./DAILY_SEO_PROMPT.md)

---

## Review 체크리스트 (필수)

- [ ] 수익·성사·매각 보장 문구 없음
- [ ] 브랜드 **WakeAgain** 영문 (사이트 카피에 한글 음차 없음)
- [ ] CTA가 wakeagain.com 허용 경로
- [ ] RoadLog·ReachKit 혼입 없음
- [ ] 뉴스/트렌드 전문 복제 없음
- [ ] slug·제목 중복 없음
- [ ] 면책 문단 있음

---

## 채널 우선순위

| 순위 | 채널 | 자동화 |
|------|------|--------|
| 1 | 사이트 블로그 + sitemap | **기본 파이프** |
| 2 | 매물 등록 CTA | 글·카피 링크 |
| 3 | 지인 DM / 짧은 소셜 | **초안만** |
| — | 커뮤니티 장문 도배 | **안 함** (전략상) |

---

## 완료 보고 포맷

```
PRODUCT: WakeAgain
DATE: YYYY-MM-DD
PIPE: daily-seo | promo-copy | other
RESEARCH: n issues | NO_NEWS_TODAY
FLAGSHIP: url or none
REVIEW: PASS | FAIL (reason)
PUBLISH: pending | done | skipped
TISTORY: url or SKIP_NO_TOKEN
LIVE: ok/fail/n-a
NOTES: ...
```

# WakeAgain 일일 SEO — 3단 에이전트 프롬프트 (Trigger)

> ## ⚠️ 2026-08-15 — push 권한 문제 (해결 전까지 결과물이 유실됨)
>
> 실행 주체는 **Claude Code 클라우드 루틴 "WakeAgain Daily SEO"**(매일 09:15 KST) 하나다.
> 그록 스케줄러와 로컬 `scripts/run_daily_seo_reminder.ps1`은 **둘 다 폐기**됐다.
>
> **알려진 장애:** 클라우드 세션의 GitHub App에 `corelabsstudio/WakeAgain` 에 대한
> `contents: write` 권한이 없어 push가 `403 Resource not accessible by integration`으로
> 막힌다. 브랜치 생성도 같은 403이라 PR 우회도 불가. 루틴 목록에는 "완료됨"으로 찍히지만
> **커밋은 컨테이너와 함께 사라진다.**
>
> 실측 근거: `docs/marketing/logs/*.md` 리포트가 저장소에 들어온 적이 한 번도 없고,
> `public/blog/` 글이 2026-08-11 이후 늘지 않았다.
>
> **이 루틴을 실행하는 세션에게:** 작업 시작 전에 push 권한이 살아 있는지 먼저 확인하고,
> 막혀 있으면 글을 생성하는 데 시간을 쓰지 말고 **권한 문제라고만 보고하고 종료**할 것.
> 권한은 사람이 GitHub 조직 설정에서 부여해야 한다(에이전트가 못 함).

매일 1회(목표: 한국시간 오전 9시 전후) 또는  
**「WakeAgain SEO」/「웨이크어게인 마케팅」** 발화 시 실행한다.

**선행 컨텍스트 (필수 읽기)**  
1. `docs/marketing/Context/ONE_PAGER.md`  
2. `docs/marketing/AGENT_TEAM.md`  
3. 이 파일  

## 제품 범위 (2026-07-31 개정)

- 이 파일은 **WakeAgain 파이프**다. 사이트 표기 브랜드는 영문 **WakeAgain** only.
- 사용자가 **「뉴스 올려」/ 둘 다 / 로드로그+웨이크어게인** 이라고 하면  
  **같은 세션에서 RoadLog SEO 다음(또는 앞)에 이 파이프를 실행해도 된다** (한 제품 제한 폐지).
- 단, **한 페이지·한 카피 안에 WakeAgain과 RoadLog 브랜드를 섞지 않는다.**
- RoadLog만 하면 될 때는 RL 쪽 `news_digest/DAILY_SEO_PROMPT.md`만 쓰면 된다.

---


## 역할 분담 (순서)

| 단계 | 역할 | 종료 조건 |
|------|------|-----------|
| **1** | Research | 이슈 목록 또는 `NO_NEWS_TODAY` |
| **2** | SEO Writer | `public/blog/<slug>.html` + index/sitemap 초안 |
| **3** | Review | PASS / FAIL · FAIL 시 Writer 1회 수정 |
| **4** | Publisher | Review PASS 후 커밋/배포 (사람 승인 권장) |

---

## 절대 규칙 (전 역할 공통)

1. 뉴스/트렌드 **전문 복제 금지**. 요약 + 원문 링크.
2. 수익·성사 **보장 문구 금지**. 응원·실용 톤.
3. 관련 이슈 **0건**이면 `NO_NEWS_TODAY` 보고 후 종료 (억지 양산 금지).
4. 하루 **풀 SEO 포스팅 1편** (가장 임팩트 큰 이슈).
5. 이미 있는 글과 제목/slug 중복 시 스킵.
6. Review PASS 전 git push 금지.

## 롱테일 키워드 (제목+본문에 주제에 맞게)

- 사이드 프로젝트 수익화
- 방치된 앱 처분
- MVP 프로토타입 판매
- 인디해커 수익

## 타겟

사이드/MVP를 만들었지만 유저·수익 없이 방치 중인 인디 메이커, 바이브 코더, 개발자.

---

## 1) Research

웹 검색 예:

- indie hacker abandoned side project
- MVP for sale
- 사이드 프로젝트 실패
- 인디해커 수익
- vibe coding abandoned project

**필터:** 방치·수익화·피벗·코드 자산 관련만.

**출력**

```
RESEARCH_OUT:
- count: N
- items: [{title, source_url, angle, proposed_slug}]
- flagship_candidate: slug or none
- or: NO_NEWS_TODAY
```

`NO_NEWS_TODAY` 이면 전체 파이프 종료.

---

## 2) SEO Writer

콘텐츠 구조 (`Templates/blog.md` · 참고 HTML: `mvp-sell-before-delete.html`):

1. 제목 (클릭+키워드)
2. 이슈 요약 3줄 + 출처 링크
3. 인사이트 (묵히기/삭제 vs 넘기기·현금화)
4. 해결책 + CTA → https://wakeagain.com  
   취지: 두 번째 기회, 무료 매물 등록
5. 면책 문단

작업 파일:

1. `public/blog/<slug>.html` 생성 (`blog.css` 재사용)
2. `public/blog/index.html` 카드 목록 상단 추가
3. `public/sitemap.xml` URL 추가

---

## 3) Review

`AGENT_TEAM.md` 체크리스트 전부 통과 시 PASS.

```
REVIEW_OUT:
- status: PASS | FAIL
- fails: [ ... ]
- fix_instructions: (FAIL일 때만)
```

FAIL → Writer 1회 수정 → 재검수. 2회 FAIL 시 사람 에스컬레이션.

---

## 4) Publisher (Review PASS 후)

```
git add public/blog public/sitemap.xml
git commit -m "content: daily WakeAgain SEO YYYY-MM-DD"
git push origin master
```

(브랜치명이 `main`이면 main 사용.)

### 티스토리 (토큰 있을 때만)

- 블로그: https://onhae126.tistory.com/
- 설정: `C:\Users\hysoo\Projects\RoadLog\.launch\tistory.env` (없으면 SKIP_NO_TOKEN)

```
python C:\Users\hysoo\Projects\RoadLog\tools\tistory_publish\publish.py --file public/blog/<slug>.html --title "..." --tags "WakeAgain,사이드프로젝트,인디해커"
```

라이브 확인 후 보고.

---

## 프로젝트 경로

`C:\Users\hysoo\Projects\WakeAgain` (또는 `projects\WakeAgain`)

## 완료 보고

```
PRODUCT: WakeAgain
DATE: ...
PIPE: daily-seo
RESEARCH: n | NO_NEWS_TODAY
FLAGSHIP: url or none
REVIEW: PASS | FAIL
PUBLISH: pending | done | skipped
TISTORY: url or SKIP_NO_TOKEN
LIVE: ok/fail
NOTES: ...
```

# WakeAgain 일일 SEO — 3단 에이전트 프롬프트 (Trigger)

매일 1회(목표: 한국시간 오전 9시 전후) 또는  
**「WakeAgain SEO」/「웨이크어게인 마케팅」** 발화 시 실행한다.

**선행 컨텍스트 (필수 읽기)**  
1. `docs/marketing/Context/ONE_PAGER.md`  
2. `docs/marketing/AGENT_TEAM.md`  
3. 이 파일  

한 요청 = **WakeAgain only**. RoadLog 콘텐츠 금지.  
사이트 표기 브랜드: 영문 **WakeAgain** only.

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

# 현재 점유 중인 파일 (Claude Code ↔ Cowork 조율용)

Claude Code와 Cowork는 서로의 세션을 볼 수 없다. 이 파일이 유일한 신호다.
규칙 전문은 `CLAUDE.md` 최상단 「동시 작업 규칙」 참조.

## 사용법

1. 파일을 고치기 **전에** 아래 「점유 중」에 한 줄 추가
2. 작업이 끝나면 **그 줄을 지운다** (커밋했든 안 했든)
3. 세션 시작 시 이 파일을 먼저 읽는다. 내가 건드릴 파일이 이미 잡혀 있으면
   그 파일은 피하거나 사용자에게 조율을 요청한다

형식:

```
- [에이전트명] 파일1, 파일2 — 무슨 작업인지 — YYYY-MM-DD HH:MM 시작
```

⚠️ 이건 잠금장치가 아니라 **권고**다. 둘이 동시에 적으면 경합할 수 있다.
확실하게 격리하려면 브랜치를 나누거나 사용자가 순서를 정해준다.

## 점유 중

_(없음)_

> 참고: 소셜/홍보(Reddit·X·Product Hunt)는 **Cowork 담당**으로 분리됨 (2026-08-15).
> Claude Code는 코드만 본다.

## 최근 종료 (참고용 · 3건까지만 남기고 정리)

- [Claude Code] `wakeagain/payments.py`, `wakeagain/db.py`, `wakeagain/api.py`, `public/project.html`, `public/sw.js` — 페이팔 KRW→USD 결제 통화 수정 + SPB 위젯이 폴링에 지워지던 문제 — 2026-08-25 종료
- [Claude Code] `public/js/footer-visitors.js`, `public/blog/**`, `public/guide/index.html`, `public/app/index.html`, `public/sw.js`, `wakeagain/api.py` — 유입경로 Direct 뭉침 수정 + 집계 누락 페이지 부착 — 2026-08-24 종료
- [Claude Code] `public/blog/**`, `public/sitemap.xml` — 일일 SEO 파이프 — 2026-08-23 종료
- [Claude Code] `public/index.html`, `public/assets/world/**` — 홈 스크롤 랜딩(깨어나는 창고) 교체 — 2026-08-21 종료

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

- [Claude Code] `wakeagain/db.py`, `wakeagain/api.py`, `public/admin/index.html`, `public/admin/sw.js` — 위탁 등록(consignor) 필드 — 2026-08-18 종료
- [Claude Code] `wakeagain/db.py`, `wakeagain/api.py`, `public/admin/index.html`, `public/admin/sw.js`, `CLAUDE.md` — 관리자 매물 명의 이전(위탁 인계) — 2026-08-16 종료
- [Claude Code] `wakeagain/db.py`, `wakeagain/api.py`, `public/app/index.html`, `public/app/app.js`, `public/js/i18n-messages.js` — 매물 등록 필수 필드 정책 백엔드·앱폼 — 2026-08-15 종료

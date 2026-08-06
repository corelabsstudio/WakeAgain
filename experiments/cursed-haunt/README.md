# cursed-haunt — 호러 ARG 랜딩

방치된 사이드 프로젝트 → 일기 → 이상현상 → 클라이맥스 → `wakeagain... no signal...`

## 실행

```powershell
cd C:\Users\hysoo\projects\WakeAgain\experiments\cursed-haunt
python -m http.server 4173
```

브라우저: `http://127.0.0.1:4173/`

## 페이즈

| 페이즈 | 내용 |
|--------|------|
| **1** | clean WIP 랜딩 · **일기 찾기** (세션당 경로 1개 / 21종) |
| **2** | 일기 오늘 이후 · **모든 이상현상**(피/감시자/글리치/섬광 등) · P3 트리거 1개 + **세션 힌트 1회** · 1·3·엔딩에서는 발동 안 함 |
| **3** | 클라이맥스 스크린세이버 **1→5 순차** |
| **엔딩** | 정적 → `wakeagain...` / `no signal...` (도메인 링크 없음) |

## 제작자 단축

| 쿼리 | |
|------|--|
| `?diary=1` | 일기 즉시 |
| `?summon=1` | 클라이맥스 1~5 → 엔딩 |
| `?ending=1` | 엔딩만 |
| `?debug=1` | 콘솔 + 크리에이터 배지 |
| `?creator=1` | 프리패스 로컬 기억 |
| `?path=logo` | 일기 발견 경로 강제 |
| `?p3=hold_free` | P3 트리거 강제 |
| `?hintfast=1` | 일기 찾기 힌트 가속 |
| **Shift+Alt+3** | 클라이맥스 프리패스 |

## 디버그 훅

- `window.__hauntStage()` / `__hauntMood()`
- `window.__hauntClimax` — id, mission, showHint(), summon()
- `window.__hauntClimaxSequence` — start / phase / isComplete
- `window.__hauntAnomalies.pool` / `.fire()` / `.flash({force:true})`
- `window.__hauntDiaryStories.current`

## 노트

- 일기 찾기 전: 음산 stage 승격 차단
- P2 진입 시: **탈출 조건 힌트 토스트 1회** + 이후 `탈출 조건` 칩으로 재확인
- WakeAgain 섬광: 전역 쿨다운으로 드묾
- 엔딩: 문구만 (wakeagain.com 링크 없음)

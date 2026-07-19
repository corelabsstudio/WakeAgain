# WakeAgain Typography (ui-ux-pro-max)

**적용일:** 2026-07-19

## 스킬 추천 (검색 결과)

| 이름 | 폰트 | 용도 |
|------|------|------|
| **Korean Modern** (채택 축) | **Noto Sans KR** | 한글 가독성 · 다국어 |
| Friendly SaaS | Plus Jakarta Sans | 영문 SaaS (한글 약함) |
| Modern Professional | Poppins + Open Sans | 영문 법인 톤 |
| Marketplace DS | IBM Plex Sans | 금융 신뢰 (한글 글리프 제한) |

→ **한글 사이트**이므로 **Noto Sans KR + Pretendard Variable** 조합.

## 스택

```
"Pretendard Variable", Pretendard, "Noto Sans KR", system-ui
```

- Pretendard Variable: UI 자간·웨이트 자연스러움 (dynamic subset CDN)
- Noto Sans KR: 한글 커버리지 백업
- Inter 제거 (한글 미지원으로 폴백 깜빡임/깨짐 유발)

## 규칙 (스킬 §5–6)

- body **≥ 16px**
- UI 라벨 **≥ 13px** (`--text-xs`) — 0.65~0.72rem 금지
- line-height body **1.55–1.75**
- weight: **400 / 500 / 600 / 700** only (650·750 합성 금지)
- Windows: `font-smoothing: auto` (antialiased 시 작은 한글 뭉개짐)
- `word-break: keep-all` (한글 단어 중간 줄바꿈 방지)

## 토큰

| Token | Size |
|-------|------|
| --text-xs | 13px |
| --text-sm | 14px |
| --text-base | 16px |

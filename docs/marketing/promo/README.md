# WakeAgain 홍보 이미지

톤: **오픈 초기 · 1인 개발** · 광고보다 “한번 써 보고 피드백 부탁”  
브랜드 표기: 사이트와 동일하게 **WakeAgain** 영문

## 메인 (긴 스크롤)

| 파일 | 규격 | 용도 |
|------|------|------|
| **`wakeagain_promo_long_story.png`** | 1080×~9300 | 카톡·커뮤니티·블로그 첨부 |
| `wakeagain_promo_long_story.jpg` | 동일 (용량↓) | 메신저 전송 |

포함:
- 사연 (여러 시도 → 1인 개발 · 피드백 부탁)
- 스크린샷 (랜딩 · 문제 공감 · 앱 마켓 · 구매 섹션)
- 기능 5가지 (등록 / 경매 / 이전 / 웹·앱 / 신뢰)
- 거래 결과 카드 (등록·경매·이전)
- B2B 한 줄 (팀·스튜디오)
- **등록 무료 · 성사 시 수수료 약 10%** (선착순 VIP 없음)
- CoreLabs 문의

바탕화면: `WakeAgain_홍보이미지\`

## 재생성

```powershell
# 로컬 서버 실행 후
cd C:\Users\hysoo\projects\WakeAgain
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8080
python scripts\capture_promo_shots.py
python scripts\make_promo_long.py
```

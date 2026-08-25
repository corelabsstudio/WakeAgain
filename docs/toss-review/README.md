# 토스페이먼츠 결제경로 심사 자료

**제출물:** `WakeAgain_토스페이먼츠_결제경로.pdf` (13쪽)
가이드 문서(`토스페이먼츠_홈페이지 결제경로 제작 가이드.pdf`) 3페이지의 6단계 순서를 그대로 따랐다.

| 단계 | 슬라이드 | 출처 |
|---|---|---|
| ① 가맹점 정보 | 1쪽 | `make_deck.py`의 `MERCHANT` |
| ② 하단정보 | 2쪽 | 라이브 홈 푸터 |
| ③ 환불규정 | 3~6쪽 | `/legal/refund.html` |
| ④ 로그인·회원가입 | 7~8쪽 | `/app/#login`, `/app/#register` |
| ⑤ 상품선택·구매과정 | 9~11쪽 | 홈 목록 → `/project.html?id=8` → 입찰 폼 |
| ⑥ 카드 결제경로 | 12~13쪽 | 로컬 격리 서버의 낙찰 후 구매자 화면 |

총 13쪽.

## ⑥단계를 라이브에서 못 찍는 이유

라이브 매물 4건이 **전부 운영 계정(`owner_id=30`) 소유**라 자기 매물에는 입찰이 막힌다
(`cannot bid on own project`). 낙찰이 안 되니 결제 화면에 도달할 수 없다.
그래서 `data/`를 복사한 격리 DB로 로컬 서버(`:8099`)를 띄우고
`setup_local_deal.py`로 판매자·구매자·매물·입찰·성사를 만들어 `awaiting_payment`까지 끌고 갔다.
**라이브 DB는 건드리지 않았다.**

## PG 결제창은 자료에 넣지 않는다

해외 채널(PayPal)은 2026-08-25에 통화 버그를 고쳐 실제로 결제창이 뜬다
(`shots/06c_페이팔결제창.png`, 커밋 `97d0924`). 하지만 **토스페이먼츠 심사 자료에는 넣지 않는다** —
심사원이 보는 문서에 페이팔 USD 결제창이 들어가면 맥락이 어긋난다.
6단계는 「낙찰 후 결제 대기 → 결제수단 선택」까지만 싣는다.

국내 카드(토스 채널)는 계약 심사 중이라 아직 결제창이 뜨지 않는다. 이건 **정상 상태**이고
사용자가 더 할 일은 없다(`CLAUDE.md` 「의도적 미완」 참조). 승인 후 결제창까지 담고 싶으면
`capture_payment.py`의 `CLICK_PAY = True`로 두고 다시 돌린다.

## 재생성

```bash
python docs/toss-review/capture_live.py        # ②~⑤ 라이브 캡처
python docs/toss-review/setup_local_deal.py    # 로컬 서버 :8099 필요
python docs/toss-review/capture_payment.py     # ⑥
python docs/toss-review/make_deck.py           # PDF 조립
```

로컬 서버는 반드시 **DB 사본**으로 띄운다:

```bash
DATA_DIR=/tmp/tossdata ADMIN_SECRET=wakeagain-admin-dev python -m uvicorn server:app --port 8099
```

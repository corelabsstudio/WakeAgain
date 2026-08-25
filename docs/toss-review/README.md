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

## ⑥단계를 라이브에서 못 찍는 이유

라이브 매물 4건이 **전부 운영 계정(`owner_id=30`) 소유**라 자기 매물에는 입찰이 막힌다
(`cannot bid on own project`). 낙찰이 안 되니 결제 화면에 도달할 수 없다.
그래서 `data/`를 복사한 격리 DB로 로컬 서버(`:8099`)를 띄우고
`setup_local_deal.py`로 판매자·구매자·매물·입찰·성사를 만들어 `awaiting_payment`까지 끌고 갔다.
**라이브 DB는 건드리지 않았다.**

## ⚠️ PG 결제창 자체는 아직 안 뜬다 (2026-08-25 실측)

`카드로 결제하기` / `PayPal로 결제`를 실제로 눌러 본 결과 둘 다 실패했다.

| 수단 | PortOne 응답 |
|---|---|
| 카드 (토스 채널) | `RECORD_NOT_FOUND: channelKey is not correct.` |
| 페이팔 | `페이팔에서 지원하지 않는 화폐(CURRENCY_KRW)` |

- 카드 쪽은 **토스페이먼츠 계약이 「심사중」이라 채널이 아직 활성이 아닌 것으로 보이나, 확인하지 못했다.**
  PortOne 콘솔에서 카드 채널의 채널키가 실제로 발급·활성 상태인지 확인해야 한다.
  Railway에도 같은 값이 들어가 있으므로(2026-08-15 기록) **라이브도 같은 상태일 가능성이 높다.**
- 페이팔 쪽은 코드 문제다. `payments.py`가 KRW로 결제를 요청하는데 페이팔은 KRW를 받지 않는다.
  통화 변환(USD)이 구현돼야 한다. `CLAUDE.md`의 "PayPal 실결제 한 번도 안 해봄"이 여기서 드러났다.

두 문제 중 하나라도 풀리면 `capture_payment.py`의 `CLICK_PAY = True`로 바꿔 다시 돌리면
결제창까지 캡처된다.

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

# GitHub 방치 레포 아웃리치 — 문구 정본

> 상위 규칙: [`../Context/ONE_PAGER.md`](../Context/ONE_PAGER.md) 금지 메시지 · CTA 우선순위를 그대로 따른다.
> 채널 운영·검색법·오탐 목록은 장기 메모리 `project_wakeagain_github_outreach` 참조.
>
> **마지막 갱신: 2026-08-18** — 가입 요구를 문구에서 제거 (제품이 바뀜)

---

## 0. 왜 문구를 바꿨나

누적 발송 12건 → 응답 2건(동의 1·거절 1) → **가입 전환 0.**

결정적인 건 `hanseulhee/onsuYumYumYum` 사례다. 2026-08-03에 **"넵 그럼 대신 올려주셔도 좋습니다~"까지
받았는데도** 15일째 가입하지 않았다. 즉 병목은 **설득이 아니라 가입 요구**였다. 동의는 공짜지만
계정 생성은 비용이고, 죽은 프로젝트는 주인에게 가치가 0이라 그 비용을 치를 이유가 없다.

2026-08-18에 **위탁 등록(consignor)** 기능을 넣어 가입을 경로에서 뺐다
(`WakeAgain/CLAUDE.md` 「2026-08-18 · 위탁 등록(consignor)」). 문구도 거기 맞춰 바꾼다.

---

## 1. 절대 규칙

| 규칙 | 이유 |
|---|---|
| ❌ **"가입하시면"·"계정을 만드시면"을 쓰지 않는다** | 가입은 더 이상 필요 없다. 이게 이번 변경의 전부다 |
| ❌ 성사·수익·매각 **보장** 표현 금지 | ONE_PAGER 금지 메시지 |
| ❌ 상대에게 양식 작성·정보 수집을 먼저 요구하지 않는다 | README에 있는 내용으로 우리가 쓴다 |
| ✅ **"안 해도 된다"를 명시적으로 쓴다** | 상대가 계산하는 건 이득이 아니라 **드는 품**이다 |
| ✅ 거절 경로를 먼저 열어준다 ("싫으시면 말씀만 주세요") | 압박이 없으면 답장 문턱이 낮아진다 |
| ✅ 아직 성사 0건임을 밝힌다 | 사이트 보면 어차피 드러난다. 정직한 쪽이 낫다 |
| ⚠️ Organization·기여자 다수 레포는 **스코프를 좁혀** 제안 | 공동 소유 동의 문제 회피 (도메인·브랜드만 등) |
| ⚠️ 게시 전 **매 건 사용자 승인**을 받는다 | 남의 공개 레포에 글을 남기는 건 되돌리기 어려운 외부 행위 |

---

## 2. 신규 발송 — 영어 (기본)

제목: `Would you consider handing this project off?`

```
Hi @{owner} — I read in your README:

> {README에서 중단을 밝힌 원문 인용}

Sorry it ended there. I run WakeAgain (https://wakeagain.com), a marketplace for
exactly this case: projects that stopped, but still have something worth reusing —
a domain, a working codebase, historical data, an existing user base.

If you're open to it, I'll list {project} for you. What that costs you:

- No signup. You don't need an account, now or later.
- No forms. Just reply "ok" here and I'll write the listing from your README.
- Listing is free. If it never sells, you spent one comment.
- If it does sell, I'll come back here and we sort out payment then. That's the
  only moment you'd have to do anything.

Being straight with you: we opened last month and haven't closed a sale yet, so
this may well go nowhere. But it costs you nothing to find out.

And if you'd rather I didn't, just say so — I'll close this and won't follow up.
```

**Organization·기여자 다수일 때** 위 `{project}` 문단을 이걸로 교체:

```
Since this is a team repo, I'm not asking about the code — that's yours and it's
open source. I'd only be listing {도메인·브랜드·잔여 자산 등 구체적으로}, and only
if that's yours to hand over.
```

---

## 3. 신규 발송 — 한국어

제목: `이 프로젝트, 넘기실 생각 있으신가요?`

```
안녕하세요 @{owner} 님. README에서 이 부분을 봤습니다.

> {중단을 밝힌 원문 인용}

WakeAgain(https://wakeagain.com)이라는 곳을 운영하고 있습니다. 멈춘 사이드 프로젝트 중에
아직 쓸 만한 게 남아 있는 것 — 도메인, 돌아가는 코드, 쌓인 데이터, 기존 사용자 — 을
다시 연결하는 마켓입니다.

괜찮으시면 {프로젝트}를 제가 대신 올려드리겠습니다. {owner}님이 하실 일은 이렇습니다.

- 가입 안 하셔도 됩니다. 지금도, 나중에도요.
- 양식 작성도 없습니다. 여기 "네" 한 마디만 주시면 README 보고 제가 씁니다.
- 등록은 무료입니다. 안 팔리면 댓글 하나 쓰신 게 전부입니다.
- 팔리면 그때 다시 찾아뵙고 정산 방법만 여쭙겠습니다. 뭔가 하실 일은 그때가 처음입니다.

솔직히 말씀드리면 지난달에 열었고 아직 성사된 거래가 없습니다. 아무 일도 안 일어날 수
있습니다. 다만 확인하는 데 드는 비용은 없습니다.

원치 않으시면 그렇다고만 해주세요. 바로 닫고 다시 연락드리지 않겠습니다.
```

---

## 4. 후속 답글 — 이미 보낸 12건용

### 4-1. 무응답 건 (10건)

한 번만 보낸다. 두 번 이상은 스팸이다.

```
Quick follow-up — one thing changed since I wrote this.

You no longer need an account for any of it. Reply "ok" and I'll do the whole
listing myself; nothing else is needed from you unless it actually sells.

If you're not interested, no reply needed — I won't ping this issue again.
```

### 4-2. 동의했지만 가입 안 한 건 (`onsuYumYumYum#131`) ⭐ 우선순위

우리가 "가입하시면 명의를 넘겨드리겠다"고 **약속했던 건**이라, 그 약속을 정정하는 게 먼저다.

```
seulhyi님, 늦게 소식 전합니다.

전에 "가입하시고 알려주시면 매물 명의를 넘겨드리겠다"고 말씀드렸는데, 그 부분을
정정합니다. 가입하실 필요가 없어졌습니다.

매물은 그대로 공개돼 있고(https://wakeagain.com/project.html?id=8), 이제는 계정
없이도 seulhyi님이 실제 판매자로 기록됩니다. 팔리면 그때 여기로 연락드려서 정산
방법만 여쭙겠습니다. 그때까지 하실 일은 없습니다.

물론 직접 계정 만들어서 가격 조정까지 직접 하고 싶으시면 그것도 가능합니다.
그리고 내리는 게 낫겠다 싶으시면 말씀만 주세요. 바로 내리겠습니다.
```

### 4-3. 거절한 건 (`apex-recoil#19`)

**아무것도 보내지 않는다.** 이미 닫혔고 "no thank you"는 명확한 의사표시다.
재접촉은 스팸이고, 같은 소유자의 다른 레포로 옮겨가는 것도 하지 않는다.

---

## 5. 발송 전 체크리스트

1. `gh api repos/{owner}/{repo} --jq .archived` → `true`면 이슈 생성 불가, 후보에서 제외
2. README **전문을 읽고** 중단 문구가 프로젝트 전체를 뜻하는지 확인
   (라이브러리 deprecation·모노레포 이전·구버전 폴더는 오탐)
3. 기여자 수 확인 → 다수면 §2 스코프 축소 문단 사용
4. 소유자 계정이 최근 활동 중인지 확인 (죽은 계정이면 도달 자체가 안 됨)
5. 본문에 **가입을 요구하는** 표현이 없는지 확인 —
   `가입하시면` / `계정을 만드시면` / `sign up and` / `once you have an account` 검색.
   (부정형 "가입 안 하셔도 됩니다" / "No signup"은 **의도된 표현**이라 그대로 둔다)
6. **사용자에게 최종 본문을 보여주고 승인받은 뒤** 발송
7. 발송 후 메모리에 **결과까지** 기록 (동의 인용·URL·매물 id·약속한 것)

---

## 6. 성과 관측 지표

응답률이 계속 0이면 의심할 순서:

1. **"아직 성사 0건" 문장** — 정직하지만 진입 장벽이 될 수 있다. 빼고 A/B
2. **길이** — `apex-recoil` 거절이 짧았다. 더 짧은 버전 시도
3. **후보 선정** — 문구가 아니라 대상이 틀렸을 수 있다
   → 다음 단계는 「수요 증거」 기반 선정 (이슈에 인수 문의가 달린 레포부터)

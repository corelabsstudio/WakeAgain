# -*- coding: utf-8 -*-
from pathlib import Path
import re

p = Path("public/app/app.js")
s = p.read_text(encoding="utf-8")

exact = {
    "알림을 불러오지 못했습니다.": 't("app.notif_fail", "알림을 불러오지 못했습니다.")',
    "로그인하면 매물 등록·내 매물이 가능합니다. 등록 전 이메일 인증과 실명·휴대폰 확인이 필요합니다.": 't("app.need_login_list", "로그인하면 매물 등록·내 매물이 가능합니다. 등록 전 이메일 인증과 실명·휴대폰 확인이 필요합니다.")',
    "신뢰 Lv3 · 거래 준비 완료. 성사 단계에서 정산 계좌를 사용합니다.": 't("app.banner_l3", "신뢰 Lv3 · 거래 준비 완료. 성사 단계에서 정산 계좌를 사용합니다.")',
    "검토중": 't("app.badge_pending", "검토중")',
    "보류": 't("app.badge_hold", "보류")',
    "반려": 't("app.badge_rejected", "반려")',
    "성사": 't("app.badge_sold", "성사")',
    "종료": 't("app.badge_ended", "종료")',
    "입찰 중": 't("app.badge_live", "입찰 중")',
    "공개": 't("app.badge_open", "공개")',
    "팔린 가격": 't("app.price_sold", "팔린 가격")',
    "지금 가격": 't("app.price_now", "지금 가격")',
    "시작 가격": 't("app.price_start", "시작 가격")',
    "아직 가격 없음": 't("app.bids_none", "아직 가격 없음")',
    "첫 입찰 대기": 't("app.live_wait", "첫 입찰 대기")',
    "검토 중 · 아직 비공개": 't("app.live_pending", "검토 중 · 아직 비공개")',
    "잠깐 보류": 't("app.live_hold", "잠깐 보류")',
    "다시 고쳐 주세요": 't("app.live_reject", "다시 고쳐 주세요")',
    "팔렸어요": 't("app.live_sold", "팔렸어요")',
    "끝났어요": 't("app.live_ended", "끝났어요")',
    "아직 올린 프로젝트가 없습니다.": 't("app.empty_mine", "아직 올린 프로젝트가 없습니다.")',
    "아직 공개 매물이 없습니다. 첫 프로젝트를 올려 보세요.": 't("app.empty_all", "아직 공개 매물이 없습니다. 첫 프로젝트를 올려 보세요.")',
    "불러오기에 실패했습니다.": 't("app.load_fail", "불러오기에 실패했습니다.")',
    "아직 수수료 청구 내역이 없습니다. 매물이 성사되면 여기에 표시됩니다.": 't("app.fees_empty", "아직 수수료 청구 내역이 없습니다. 매물이 성사되면 여기에 표시됩니다.")',
    "확인됨": 't("app.fee_paid", "확인됨")',
    "대기": 't("app.fee_wait", "대기")',
    "입금 확인됨 (운영자)": 't("app.fee_paid_note", "입금 확인됨 (운영자)")',
    "로그인에 실패했습니다.": 't("app.login_fail", "로그인에 실패했습니다.")',
    "이용약관 및 개인정보처리방침에 동의해 주세요.": 't("app.reg_terms_err", "이용약관 및 개인정보처리방침에 동의해 주세요.")',
    "생년월일을 입력해 주세요.": 't("app.reg_birth_err", "생년월일을 입력해 주세요.")',
    "만 14세 미만은 WakeAgain에 가입할 수 없습니다.": 't("app.reg_under14", "만 14세 미만은 WakeAgain에 가입할 수 없습니다.")',
    "생년월일을 다시 확인해 주세요.": 't("app.reg_birth_bad", "생년월일을 다시 확인해 주세요.")',
    "만 14세 이상임을 확인해 주세요.": 't("app.reg_age_check", "만 14세 이상임을 확인해 주세요.")',
    "비밀번호는 8자 이상이어야 합니다.": 't("app.reg_pass_len", "비밀번호는 8자 이상이어야 합니다.")',
    "비밀번호가 서로 다릅니다. 다시 입력해 주세요.": 't("app.reg_pass_match", "비밀번호가 서로 다릅니다. 다시 입력해 주세요.")',
    "가입에 실패했습니다.": 't("app.reg_fail", "가입에 실패했습니다.")',
    "인증 실패": 't("app.verify_fail", "인증 실패")',
    "저장 실패": 't("app.save_fail", "저장 실패")',
    "비밀번호 보기": 't("app.pw_show", "비밀번호 보기")',
    "비밀번호 숨기기": 't("app.pw_hide", "비밀번호 숨기기")',
    "매물 등록에는 로그인 · 이메일 인증 · 실명·휴대폰 · 판매자 공개 정보가 필요합니다.": 't("app.need_gates", "매물 등록에는 로그인 · 이메일 인증 · 실명·휴대폰 · 판매자 공개 정보가 필요합니다.")',
    "변경 완료. 로그인해 주세요.": 't("app.reset_ok", "변경 완료. 로그인해 주세요.")',
    "코드를 발급했습니다.": 't("app.reset_sent", "코드를 발급했습니다.")',
    "새 코드를 발급했습니다.": 't("app.verify_resent", "새 코드를 발급했습니다.")',
    "수수료 10%": 't("app.fee_rate", "수수료 10%")',
    "입금 대기 · 운영자 확인 · corelabs.studio@gmail.com": 't("app.fee_wait_note", "입금 대기 · 운영자 확인") + " · corelabs.studio@gmail.com"',
}

count = 0
for old, new in exact.items():
    quoted = '"' + old + '"'
    if quoted in s:
        s = s.replace(quoted, new)
        count += 1

s = s.replace('0: "Lv0 · 가입"', '0: t("app.lv0", "Lv0 · 가입")')
s = s.replace('1: "Lv1 · 이메일 완료"', '1: t("app.lv1", "Lv1 · 이메일 완료")')
s = s.replace('2: "Lv2 · 인증 완료"', '2: t("app.lv2", "Lv2 · 인증 완료")')
s = s.replace('3: "Lv3 · 거래 준비 완료"', '3: t("app.lv3", "Lv3 · 거래 준비 완료")')
s = re.sub(
    r'"가격 " \+ bids \+ "번 씀"',
    't("app.bids_n", "가격 {n}번 씀", { n: bids })',
    s,
)

if "function money(" not in s:
    s = s.replace(
        "const $ = (id) => document.getElementById(id);",
        """const $ = (id) => document.getElementById(id);
  function money(n) {
    if (window.WakeAgainI18n && window.WakeAgainI18n.formatMoney) return window.WakeAgainI18n.formatMoney(n);
    return "₩" + Number(n).toLocaleString("ko-KR");
  }
""",
    )

s = s.replace(
    '"₩" + Number(f.deal_amount).toLocaleString("ko-KR")',
    'money(f.deal_amount)',
)

if "wa:langchange" not in s:
    if s.rstrip().endswith("})();"):
        s = s.rstrip()[:-5] + """
  document.addEventListener("wa:langchange", function () {
    try {
      if (window.WakeAgainI18n) window.WakeAgainI18n.apply(document);
    } catch (e) {}
    try {
      syncChrome();
    } catch (e) {}
  });
  document.addEventListener("wa:currencychange", function () {
    try {
      if (window.WakeAgainI18n) window.WakeAgainI18n.apply(document);
    } catch (e) {}
  });
})();
"""

p.write_text(s, encoding="utf-8")
print("replaced", count, "len", len(s))

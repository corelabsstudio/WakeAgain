"""SMTP email delivery for verification codes.

Env:
  SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS, SMTP_FROM
  SMTP_TLS=1 (default)
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST", "").strip() and os.environ.get("SMTP_FROM", "").strip())


def send_mail(to: str, subject: str, body: str) -> bool:
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host or not to:
        print("[mailer] skip: SMTP_HOST or recipient missing", flush=True)
        return False
    port = int(os.environ.get("SMTP_PORT", "587") or "587")
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASS", "").strip()
    from_addr = os.environ.get("SMTP_FROM", user or "noreply@wakeagain.local").strip()
    use_tls = os.environ.get("SMTP_TLS", "1").strip() not in {"0", "false", "False"}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        print(f"[mailer] sent to {to!r} subject={subject[:40]!r}", flush=True)
        return True
    except Exception as e:
        print(f"[mailer] FAIL to={to!r}: {type(e).__name__}: {e}", flush=True)
        return False


def send_verification_code(to: str, code: str) -> bool:
    return send_mail(
        to,
        "[WakeAgain] 이메일 인증 코드",
        (
            "WakeAgain 이메일 인증 코드입니다.\n\n"
            f"인증 코드: {code}\n\n"
            "앱/웹의 인증 화면에 위 코드를 입력해 주세요.\n"
            "코드는 약 15분 후 만료됩니다.\n\n"
            "본인이 요청하지 않았다면 이 메일을 무시하세요.\n"
            "— CoreLabs · WakeAgain\n"
        ),
    )


def send_password_reset_code(to: str, code: str) -> bool:
    return send_mail(
        to,
        "[WakeAgain] 비밀번호 재설정 코드",
        (
            "WakeAgain 비밀번호 재설정 코드입니다.\n\n"
            f"재설정 코드: {code}\n\n"
            "앱/웹의 비밀번호 찾기 화면에 입력해 주세요.\n"
            "본인이 요청하지 않았다면 무시하세요.\n"
            "— CoreLabs · WakeAgain\n"
        ),
    )

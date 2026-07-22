"""Email delivery for verification / password-reset codes.

Primary: SMTP (Gmail etc.)
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
  SMTP_TLS=1 (STARTTLS, default on 587)
  SMTP_SSL=1 (implicit SSL, default on 465)
  SMTP_REPLY_TO (optional)

Fallback (HTTPS — works when Railway blocks SMTP ports):
  RESEND_API_KEY  — https://resend.com free tier
  RESEND_FROM     — verified sender

Gmail example:
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=465
  SMTP_SSL=1
  SMTP_USER=you@gmail.com
  SMTP_PASS=<app password>
  SMTP_FROM=WakeAgain <you@gmail.com>
"""
from __future__ import annotations

import json
import os
import smtplib
import socket
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


def smtp_configured() -> bool:
    host = os.environ.get("SMTP_HOST", "").strip()
    from_addr = os.environ.get("SMTP_FROM", "").strip()
    if host and from_addr:
        return True
    if os.environ.get("RESEND_API_KEY", "").strip() and (
        os.environ.get("RESEND_FROM", "").strip() or from_addr
    ):
        return True
    return False


def _bool_env(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip() in {"1", "true", "True", "yes", "YES"}


def _ipv4_connect(host: str, port: int, timeout: float) -> socket.socket:
    """IPv4 only — Railway often returns errno 101 on IPv6 to smtp.gmail.com."""
    last: Exception | None = None
    infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    for _family, socktype, proto, _canon, sockaddr in infos:
        sock = socket.socket(socket.AF_INET, socktype, proto)
        sock.settimeout(timeout)
        try:
            sock.connect(sockaddr)
            return sock
        except OSError as e:
            last = e
            try:
                sock.close()
            except Exception:
                pass
    if last:
        raise last
    raise OSError(f"no IPv4 route to {host}:{port}")


def _send_via_smtp_port(
    to: str,
    msg: EmailMessage,
    *,
    host: str,
    port: int,
    use_ssl: bool,
    use_tls: bool,
    user: str,
    password: str,
    timeout: float,
) -> bool:
    context = ssl.create_default_context()
    raw: socket.socket | None = None
    try:
        raw = _ipv4_connect(host, port, timeout)
        if use_ssl:
            ssock = context.wrap_socket(raw, server_hostname=host)
            raw = None  # ownership transferred
            smtp = smtplib.SMTP_SSL()
            smtp.sock = ssock
            smtp.file = None
            smtp._host = host  # type: ignore[attr-defined]
            try:
                smtp.ehlo()
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
            finally:
                try:
                    smtp.quit()
                except Exception:
                    try:
                        smtp.close()
                    except Exception:
                        pass
        else:
            smtp = smtplib.SMTP()
            smtp.sock = raw
            raw = None
            smtp.file = None
            smtp._host = host  # type: ignore[attr-defined]
            try:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls(context=context)
                    smtp.ehlo()
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
            finally:
                try:
                    smtp.quit()
                except Exception:
                    try:
                        smtp.close()
                    except Exception:
                        pass
        print(f"[mailer] SMTP sent to {to!r} via {host}:{port} ssl={use_ssl}", flush=True)
        return True
    except Exception as e:
        print(
            f"[mailer] SMTP FAIL to={to!r} {host}:{port}: {type(e).__name__}: {e}",
            flush=True,
        )
        if raw is not None:
            try:
                raw.close()
            except Exception:
                pass
        return False


def _send_via_smtp(to: str, msg: EmailMessage) -> bool:
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host:
        return False
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASS", "").strip().replace(" ", "")
    # Keep short: Railway often blocks SMTP entirely; don't stall register for 50s+
    timeout = float(os.environ.get("SMTP_TIMEOUT", "8") or "8")
    pref_port = int(os.environ.get("SMTP_PORT", "465") or "465")
    pref_ssl = _bool_env("SMTP_SSL", "1" if pref_port == 465 else "0") or pref_port == 465
    pref_tls = _bool_env("SMTP_TLS", "0" if pref_ssl else "1")

    # Try preferred, then the other common Gmail port (Railway may block one)
    attempts: list[tuple[int, bool, bool]] = [(pref_port, pref_ssl, pref_tls and not pref_ssl)]
    alt_port, alt_ssl, alt_tls = (587, False, True) if pref_port == 465 else (465, True, False)
    if (alt_port, alt_ssl, alt_tls) not in attempts:
        attempts.append((alt_port, alt_ssl, alt_tls))

    for port, use_ssl, use_tls in attempts:
        if _send_via_smtp_port(
            to,
            msg,
            host=host,
            port=port,
            use_ssl=use_ssl,
            use_tls=use_tls,
            user=user,
            password=password,
            timeout=timeout,
        ):
            return True
    return False


def _send_via_resend(to: str, subject: str, body: str, html: str | None) -> bool:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        return False
    from_addr = (
        os.environ.get("RESEND_FROM", "").strip()
        or os.environ.get("SMTP_FROM", "").strip()
        or "WakeAgain <onboarding@resend.dev>"
    )
    payload: dict = {
        "from": from_addr,
        "to": [to],
        "subject": subject,
        "text": body,
    }
    if html:
        payload["html"] = html
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "WakeAgain/1.0 (+https://wakeagain.com)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            raw = res.read().decode("utf-8", "replace")
        print(f"[mailer] Resend sent to {to!r}: {raw[:120]}", flush=True)
        return True
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "replace")
        print(f"[mailer] Resend FAIL HTTP {e.code}: {err[:300]}", flush=True)
        return False
    except Exception as e:
        print(f"[mailer] Resend FAIL to={to!r}: {type(e).__name__}: {e}", flush=True)
        return False


def send_mail(to: str, subject: str, body: str, *, html: str | None = None) -> bool:
    to = (to or "").strip()
    if not to:
        print("[mailer] skip: recipient missing", flush=True)
        return False

    from_addr = os.environ.get("SMTP_FROM", "").strip() or os.environ.get(
        "SMTP_USER", "noreply@wakeagain.local"
    ).strip()
    reply_to = os.environ.get("SMTP_REPLY_TO", "").strip()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg["Date"] = formatdate(localtime=False)
    msg["Message-ID"] = make_msgid(domain="wakeagain.com")
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    # Prefer Resend (HTTPS) when configured — Railway blocks outbound SMTP ports.
    if os.environ.get("RESEND_API_KEY", "").strip():
        if _send_via_resend(to, subject, body, html):
            return True
    if os.environ.get("SMTP_HOST", "").strip() and _send_via_smtp(to, msg):
        return True

    print(f"[mailer] all transports failed for {to!r}", flush=True)
    return False


def _code_html(title: str, code: str, hint: str) -> str:
    return (
        f"<div style='font-family:system-ui,sans-serif;max-width:480px;margin:0 auto;padding:24px'>"
        f"<h2 style='color:#7c3aed;margin:0 0 12px'>{title}</h2>"
        f"<p style='color:#334155;line-height:1.5'>{hint}</p>"
        f"<p style='font-size:28px;font-weight:700;letter-spacing:0.25em;color:#5b21b6;"
        f"background:#f5f3ff;padding:16px 20px;border-radius:12px;text-align:center'>{code}</p>"
        f"<p style='color:#64748b;font-size:13px'>본인이 요청하지 않았다면 이 메일을 무시하세요.<br/>— CoreLabs · WakeAgain</p>"
        f"</div>"
    )


def send_verification_code(to: str, code: str) -> bool:
    text = (
        "WakeAgain 이메일 인증 코드입니다.\n\n"
        f"인증 코드: {code}\n\n"
        "앱/웹의 인증 화면에 위 코드를 입력해 주세요.\n"
        "코드는 약 30분 후 만료됩니다.\n\n"
        "본인이 요청하지 않았다면 이 메일을 무시하세요.\n"
        "— CoreLabs · WakeAgain\n"
    )
    return send_mail(
        to,
        "[WakeAgain] 이메일 인증 코드",
        text,
        html=_code_html("이메일 인증 코드", code, "앱/웹의 인증 화면에 아래 코드를 입력해 주세요."),
    )


def send_password_reset_code(to: str, code: str) -> bool:
    text = (
        "WakeAgain 비밀번호 재설정 코드입니다.\n\n"
        f"재설정 코드: {code}\n\n"
        "앱/웹의 비밀번호 찾기 화면에 입력해 주세요.\n"
        "코드는 약 30분 후 만료됩니다.\n\n"
        "본인이 요청하지 않았다면 무시하세요.\n"
        "— CoreLabs · WakeAgain\n"
    )
    return send_mail(
        to,
        "[WakeAgain] 비밀번호 재설정 코드",
        text,
        html=_code_html(
            "비밀번호 재설정 코드",
            code,
            "비밀번호 찾기 화면에 아래 코드를 입력한 뒤 새 비밀번호를 설정하세요.",
        ),
    )

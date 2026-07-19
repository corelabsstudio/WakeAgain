# -*- coding: utf-8 -*-
"""Inject i18n scripts + lang switcher into major public HTML pages; wire app shell labels."""
from pathlib import Path
import re

ROOT = Path("public")
SCRIPTS = (
    '  <script src="/js/i18n-messages.js"></script>\n'
    '  <script src="/js/i18n.js"></script>\n'
)
SWITCH = """        <div class="lang-switch" role="group" aria-label="Language">
          <button type="button" class="lang-btn" data-lang-switch="ko" title="한국어">KO</button>
          <button type="button" class="lang-btn" data-lang-switch="en" title="English">EN</button>
        </div>
"""

# pages that should get scripts if missing
PAGES = [
    "index.html",
    "app/index.html",
    "showcase.html",
    "showcase-new.html",
    "diagnose.html",
    "sell.html",
    "buy.html",
    "project.html",
    "get-app.html",
    "review.html",
    "404.html",
    "guide/index.html",
    "guide/status.html",
    "guide/credit.html",
    "guide/dispute.html",
    "guide/demo.html",
]


def ensure_scripts(html: str) -> str:
    if "i18n-messages.js" in html:
        return html
    if 'src="/js/i18n.js"' in html:
        return html.replace(
            '<script src="/js/i18n.js"></script>',
            '<script src="/js/i18n-messages.js"></script>\n  <script src="/js/i18n.js"></script>',
            1,
        )
    # inject before first script
    m = re.search(r"(\s*)<script\s", html)
    if m:
        return html[: m.start()] + "\n" + SCRIPTS + html[m.start() :]
    return html.replace("</body>", SCRIPTS + "</body>")


def ensure_switch(html: str) -> str:
    if "data-lang-switch" in html:
        return html
    # inject before nav-actions primary btn or end of nav-actions
    if "nav-actions" in html:
        return re.sub(
            r'(<div class="nav-actions"[^>]*>\s*)',
            r"\1" + SWITCH,
            html,
            count=1,
        )
    return html


def patch_app_index(html: str) -> str:
    repl = [
        ('>로그인</button>', ' data-i18n="app.login_submit">로그인</button>'),
        ('>비밀번호 찾기</button>', ' data-i18n="app.find_pw">비밀번호 찾기</button>'),
        ('>코드 받기</button>', ' data-i18n="app.reset_code">코드 받기</button>'),
        ('>비밀번호 변경</button>', ' data-i18n="app.reset_save">비밀번호 변경</button>'),
        ('>로그인으로</button>', ' data-i18n="app.reset_back">로그인으로</button>'),
        ('>가입 완료</button>', ' data-i18n="app.reg_submit">가입 완료</button>'),
        ('>표시 이름 (선택)</label>', ' data-i18n="app.reg_name">표시 이름 (선택)</label>'),
        ('>생년월일</label>', ' data-i18n="app.reg_birth">생년월일</label>'),
        ('>비밀번호 (8자 이상)</label>', ' data-i18n="app.reg_pass">비밀번호 (8자 이상)</label>'),
        ('>비밀번호 재입력</label>', ' data-i18n="app.reg_pass2">비밀번호 재입력</label>'),
        ('>이메일 인증</h1>', ' data-i18n="app.verify_title">이메일 인증</h1>'),
        ('>인증 코드</label>', ' data-i18n="app.verify_code">인증 코드</label>'),
        ('>인증 확인</button>', ' data-i18n="app.verify_submit">인증 확인</button>'),
        ('>코드 다시 받기</button>', ' data-i18n="app.verify_resend">코드 다시 받기</button>'),
        ('data-go="list">프로젝트</button>', 'data-go="list" data-i18n="app.tab_projects">프로젝트</button>'),
        ('data-go="new">올리기</button>', 'data-go="new" data-i18n="app.tab_new">올리기</button>'),
        ('data-go="profile">내 정보</button>', 'data-go="profile" data-i18n="app.tab_me">내 정보</button>'),
        ('>올리기 요청하기</button>', ' data-i18n="app.create_submit">올리기 요청하기</button>'),
        (
            'SNS로 빠르게 시작 (카카오 · 구글 · 깃허브)',
            '<span data-i18n="common.sns_label">SNS로 빠르게 시작 (카카오 · 구글 · 깃허브)</span>',
        ),
        (
            '카카오로 계속',
            ' data-i18n="common.kakao">카카오로 계속',
        ),
        (
            'Google로 계속',
            ' data-i18n="common.google">Google로 계속',
        ),
        (
            'GitHub로 계속',
            ' data-i18n="common.github">GitHub로 계속',
        ),
        (
            '또는 이메일',
            '<span data-i18n="common.or_email">또는 이메일</span>',
        ),
    ]
    for a, b in repl:
        if a in html and "data-i18n" not in a:
            # avoid double wrap
            html = html.replace(a, b, 1)
    # fix broken replacements for buttons that already have >
    html = html.replace(' data-i18n="common.kakao">카카오로 계속"', ' data-i18n="common.kakao">카카오로 계속"')
    return html


for rel in PAGES:
    path = ROOT / rel
    if not path.is_file():
        continue
    html = path.read_text(encoding="utf-8")
    orig = html
    html = ensure_scripts(html)
    html = ensure_switch(html)
    if rel == "app/index.html":
        html = patch_app_index(html)
    if html != orig:
        path.write_text(html, encoding="utf-8")
        print("updated", rel)
    else:
        print("skip", rel)

print("done")

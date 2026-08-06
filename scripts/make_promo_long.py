"""Long scroll promo for WakeAgain — same context as RoadLog open-early story."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "marketing" / "promo"
SHOTS = OUT / "shots"
LOGO = ROOT / "public" / "assets" / "logo-mark.png"
FONT = r"C:\Windows\Fonts\malgun.ttf"
FONT_B = r"C:\Windows\Fonts\malgunbd.ttf"

W = 1080
MARGIN = 56
CONTENT_W = W - MARGIN * 2

# Brand purple palette
PURPLE = (167, 139, 250)  # #a78bfa
PURPLE_D = (124, 58, 237)  # #7c3aed
CYAN = (52, 211, 153)  # soft green accent from live UI
BG = (5, 3, 12)


def fnt(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, size)
    except Exception:
        return ImageFont.truetype(FONT, size)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        cur = ""
        for ch in para:
            trial = cur + ch
            tw, _ = text_size(draw, trial, font)
            if tw <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines


def draw_bg(h: int) -> Image.Image:
    img = Image.new("RGB", (W, h), BG)
    px = img.load()
    for y in range(h):
        for x in range(0, W, 3):
            t = y / max(h - 1, 1)
            wave = 0.5 + 0.5 * math.sin((x / W) * 2.8 + t * 3.5)
            r = int(8 + 28 * (1 - t) * wave)
            g = int(4 + 10 * (1 - t) * wave)
            b = int(18 + 40 * (1 - t * 0.6) * wave)
            c = (min(40, r), min(25, g), min(55, b))
            px[x, y] = c
            if x + 1 < W:
                px[x + 1, y] = c
            if x + 2 < W:
                px[x + 2, y] = c
    overlay = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([int(W * 0.35), -160, int(W * 1.15), 480], fill=(124, 58, 237, 40))
    od.ellipse([-220, int(h * 0.4), 320, int(h * 0.62)], fill=(167, 139, 250, 18))
    od.ellipse([int(W * 0.45), int(h * 0.75), int(W * 1.2), int(h * 0.98)], fill=(52, 211, 153, 12))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def rounded_shot(path: Path, max_w: int, crop_top: int = 0) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    if crop_top > 0 and im.height > crop_top + 80:
        im = im.crop((0, crop_top, im.width, im.height))
    ratio = max_w / im.width
    nh = int(im.height * ratio)
    im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=36, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    border = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [1, 1, im.width - 2, im.height - 2],
        radius=36,
        outline=(167, 139, 250, 130),
        width=3,
    )
    return Image.alpha_composite(out, border)


def paste_logo(base: Image.Image, x: int, y: int, size: int = 96) -> None:
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo = logo.resize((size, size), Image.Resampling.LANCZOS)
        base.paste(logo, (x, y), logo)
    else:
        d = ImageDraw.Draw(base)
        d.rounded_rectangle([x, y, x + size, y + size], radius=22, fill=(124, 58, 237, 255))
        d.text((x + 18, y + 28), "WA", font=fnt(28, True), fill=(255, 255, 255, 255))


class Builder:
    def __init__(self) -> None:
        self.parts: list[Image.Image] = []

    def canvas(self, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGBA", (W, height), (0, 0, 0, 0))
        return img, ImageDraw.Draw(img)

    def push(self, img: Image.Image) -> None:
        self.parts.append(img)

    def spacer(self, h: int = 28) -> None:
        self.push(Image.new("RGBA", (W, h), (0, 0, 0, 0)))

    def add_heading(self, eyebrow: str, title: str) -> None:
        h = 150
        img, d = self.canvas(h)
        if eyebrow:
            d.text((MARGIN, 20), eyebrow, font=fnt(24, True), fill=(*PURPLE, 255))
        d.text((MARGIN, 58), title, font=fnt(40, True), fill=(248, 250, 252, 255))
        self.push(img)

    def add_paragraphs(self, text: str, size: int = 28, color=(203, 213, 225, 255), gap: int = 14) -> None:
        probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        font = fnt(size)
        lines = wrap_lines(probe, text, font, CONTENT_W)
        line_h = text_size(probe, "가", font)[1] + gap
        height = max(40, len(lines) * line_h + 20)
        img, d = self.canvas(height)
        y = 0
        for line in lines:
            if line == "":
                y += line_h // 2
                continue
            d.text((MARGIN, y), line, font=font, fill=color)
            y += line_h
        self.push(img)

    def add_shot(self, path: Path, caption: str, crop_top: int = 0, max_w: int | None = None) -> None:
        if not path.exists():
            return
        max_w = max_w or min(CONTENT_W, 780)
        shot = rounded_shot(path, max_w, crop_top=crop_top)
        probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        cf = fnt(24)
        lines = wrap_lines(probe, caption, cf, max_w)
        cap_h = len(lines) * (text_size(probe, "가", cf)[1] + 8) + 16
        total_h = shot.height + cap_h + 40
        img, d = self.canvas(total_h)
        x = (W - shot.width) // 2
        img.paste(shot, (x, 10), shot)
        y = 20 + shot.height
        for line in lines:
            tw, th = text_size(d, line, cf)
            d.text(((W - tw) // 2, y), line, font=cf, fill=(148, 163, 184, 255))
            y += th + 8
        self.push(img)

    def add_feature_list(self, items: list[tuple[str, str]]) -> None:
        probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        title_f, body_f = fnt(28, True), fnt(24)
        rows = []
        for title, body in items:
            blines = wrap_lines(probe, body, body_f, CONTENT_W - 80)
            h = 20 + text_size(probe, title, title_f)[1] + 10
            h += len(blines) * (text_size(probe, "가", body_f)[1] + 6) + 24
            rows.append((title, blines, h))
        total = sum(r[2] for r in rows) + 20
        img, d = self.canvas(total)
        y = 0
        for i, (title, blines, h) in enumerate(rows):
            d.ellipse(
                [MARGIN, y + 8, MARGIN + 44, y + 52],
                fill=(124, 58, 237, 50),
                outline=(*PURPLE, 160),
                width=2,
            )
            num = str(i + 1)
            nw, nh = text_size(d, num, fnt(22, True))
            d.text(
                (MARGIN + (44 - nw) // 2, y + 8 + (44 - nh) // 2 - 2),
                num,
                font=fnt(22, True),
                fill=(*PURPLE, 255),
            )
            d.text((MARGIN + 60, y + 12), title, font=title_f, fill=(248, 250, 252, 255))
            by = y + 12 + text_size(d, title, title_f)[1] + 10
            for line in blines:
                d.text((MARGIN + 60, by), line, font=body_f, fill=(148, 163, 184, 255))
                by += text_size(d, "가", body_f)[1] + 6
            y += h
        self.push(img)

    def add_highlight_box(self, title: str, lines: list[str]) -> None:
        probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        tf, bf = fnt(26, True), fnt(28, True)
        wrapped: list[str] = []
        for line in lines:
            wrapped.extend(wrap_lines(probe, line, bf, CONTENT_W - 64))
        h = 40 + text_size(probe, title, tf)[1] + 18
        h += len(wrapped) * (text_size(probe, "가", bf)[1] + 12) + 40
        img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle(
            [MARGIN - 4, 8, W - MARGIN + 4, h - 8],
            radius=28,
            fill=(124, 58, 237, 36),
            outline=(*PURPLE, 160),
            width=2,
        )
        d.text((MARGIN + 24, 28), title, font=tf, fill=(*PURPLE, 255))
        y = 28 + text_size(d, title, tf)[1] + 18
        for line in wrapped:
            d.text((MARGIN + 24, y), line, font=bf, fill=(248, 250, 252, 255))
            y += text_size(d, "가", bf)[1] + 12
        self.push(img)

    def add_outcome_cards(self) -> None:
        """Trust cards: listing / live bid / transfer — analogous to RoadLog export samples."""
        card_w, card_h = 300, 340
        gap = 24
        total_w = card_w * 3 + gap * 2
        start_x = (W - total_w) // 2
        strip_h = card_h + 90
        img = Image.new("RGBA", (W, strip_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        samples = [
            (
                "등록",
                (124, 58, 237),
                [
                    ("잠든 SaaS 올리기", True),
                    ("데모 링크 · 스토리", False),
                    ("시작가 ₩450,000", False),
                    ("즉시구매 선택", False),
                    ("등록비 ₩0", False),
                    ("검토 후 공개", False),
                ],
            ),
            (
                "경매",
                (16, 185, 129),
                [
                    ("실시간 입찰", True),
                    ("현재가 ₩780,000", False),
                    ("남은 시간 25:10:00", False),
                    ("입찰 단위 +₩1만", False),
                    ("관심 알림", False),
                    ("가격·시간 한눈에", False),
                ],
            ),
            (
                "이전",
                (59, 130, 246),
                [
                    ("확실한 거래", True),
                    ("낙찰 → 합의", False),
                    ("소스·계정 이전", False),
                    ("성사 시 수수료 약 10%", False),
                    ("미성사 시 등록비 0", False),
                    ("신용·레벨 표시", False),
                ],
            ),
        ]

        for i, (label, accent, rows) in enumerate(samples):
            x = start_x + i * (card_w + gap)
            y0 = 8
            ar, ag, ab = accent
            d.rounded_rectangle(
                [x, y0, x + card_w, y0 + card_h],
                radius=18,
                fill=(248, 250, 252, 255),
                outline=(226, 232, 240, 255),
                width=2,
            )
            d.rounded_rectangle([x, y0, x + card_w, y0 + 46], radius=18, fill=(ar, ag, ab, 255))
            d.rectangle([x, y0 + 24, x + card_w, y0 + 46], fill=(ar, ag, ab, 255))
            lf = fnt(22, True)
            lw, lh = text_size(d, label, lf)
            d.text((x + (card_w - lw) // 2, y0 + (46 - lh) // 2), label, font=lf, fill=(255, 255, 255, 255))
            yy = y0 + 62
            for text, is_title in rows:
                if is_title:
                    d.text((x + 18, yy), text, font=fnt(18, True), fill=(15, 23, 42, 255))
                    yy += 32
                    d.line([(x + 18, yy - 8), (x + card_w - 18, yy - 8)], fill=(226, 232, 240, 255), width=1)
                else:
                    d.text((x + 18, yy), text, font=fnt(15), fill=(51, 65, 85, 255))
                    yy += 28

        cap = "결과 흐름 예시 — 폴더에 잠든 프로젝트가 가격 있는 매물로"
        cf = fnt(22)
        cw, _ = text_size(d, cap, cf)
        d.text(((W - cw) // 2, card_h + 28), cap, font=cf, fill=(148, 163, 184, 255))
        self.push(img)

    def build(self) -> Image.Image:
        self.parts.clear()

        # HERO
        hero_h = 460
        hero, d = self.canvas(hero_h)
        paste_logo(hero, (W - 100) // 2, 36, 100)
        d = ImageDraw.Draw(hero)
        badge = "오픈 초기 · 1인 개발"
        bf = fnt(24, True)
        bw, bh = text_size(d, badge, bf)
        bx = (W - bw - 36) // 2
        d.rounded_rectangle(
            [bx, 160, bx + bw + 36, 160 + bh + 18],
            radius=20,
            fill=(124, 58, 237, 40),
            outline=(*PURPLE, 140),
            width=1,
        )
        d.text((bx + 18, 168), badge, font=bf, fill=(*PURPLE, 255))
        t1 = "WakeAgain"
        tw, _ = text_size(d, t1, fnt(60, True))
        d.text(((W - tw) // 2, 220), t1, font=fnt(60, True), fill=(248, 250, 252, 255))
        t2 = "프로젝트에 두 번째 기회를 주세요."
        tw2, _ = text_size(d, t2, fnt(28, True))
        d.text(((W - tw2) // 2, 300), t2, font=fnt(28, True), fill=(*PURPLE, 255))
        t3 = "잠든 앱·프로토타입·SaaS를 경매로 다시 연결합니다."
        for i, line in enumerate(wrap_lines(d, t3, fnt(24), CONTENT_W)):
            twl, thl = text_size(d, line, fnt(24))
            d.text(((W - twl) // 2, 350 + i * (thl + 6)), line, font=fnt(24), fill=(203, 213, 225, 255))
        self.push(hero)
        self.spacer(8)

        # STORY
        self.add_heading("이야기", "왜 만들었는지")
        story = (
            "그동안 여러가지 일을 시도하다가 잘 안되서, "
            "마지막 시도라고 생각하고 1인 개발에 뛰어들었습니다.\n\n"
            "첫 개발이니만큼 사람 모으는 게 쉽지 않네요.\n\n"
            "폴더에만 잠든 프로젝트, 팔고 싶은데 장이 없는 사이드 앱, "
            "사고 싶은데 비교할 매물이 없는 분들을 위해 "
            "WakeAgain을 만들고 있습니다.\n\n"
            "광고처럼 들리기보다, 정말 한번 둘러보시고 "
            "불편한 점·좋은 점 피드백 주시면 너무 감사하겠습니다. "
            "말씀 주신 내용은 바로바로 반영해 볼게요."
        )
        self.add_paragraphs(story, size=28, color=(226, 232, 240, 255), gap=12)
        self.spacer(16)

        # LANDING
        self.add_heading("사이트 미리보기", "WakeAgain은 이렇게 생겼어요")
        self.add_shot(
            SHOTS / "landing_mobile.png",
            "메인 — 실시간 경매 카드 + 「내 프로젝트 올리기」",
            max_w=720,
        )
        self.spacer(8)

        # FEATURES
        self.add_heading("무엇을 할 수 있나요", "핵심 기능")
        self.add_feature_list(
            [
                (
                    "잠든 프로젝트 등록 (판매)",
                    "데모·스토리·시작가·즉시구매가를 카드로 올립니다. 등록 비용 무료. 성사될 때만 수수료 약 10%.",
                ),
                (
                    "실시간 경매·입찰 (구매)",
                    "현재 입찰가와 남은 시간(시:분:초)을 보고 입찰합니다. 가격과 긴급성이 한 화면에 보입니다.",
                ),
                (
                    "검토 후 이전 (신뢰)",
                    "데모·실행 흔적 있는 건을 우선합니다. 낙찰·합의 후 소스를 이전하는 순서로 거래를 확실하게 만듭니다.",
                ),
                (
                    "웹 · 앱 같은 계정",
                    "웹사이트와 스토어 앱에서 같은 계정·데이터로 쓰도록 설계했습니다. (Google Play · App Store 목표)",
                ),
                (
                    "사기 예방 · 신용",
                    "신원 레벨·신용 점수·입금 전 이전 금지 등, “쉽게 올리되 거래는 확실하게”를 원칙으로 합니다.",
                ),
            ]
        )
        self.spacer(12)

        # PROBLEM SHOT
        self.add_heading("공감", "세상 밖으로 나오지 못한 프로젝트들")
        self.add_paragraphs(
            "쓸모없어서가 아닙니다. 인생이 변하거나, 시간이 없거나, 마케팅이 일어나지 않았을 뿐입니다. "
            "우리는 그 프로젝트들에게 다시 한 번 기회를 줍니다.",
            size=26,
            color=(148, 163, 184, 255),
            gap=10,
        )
        self.add_shot(
            SHOTS / "landing_mid.png",
            "문제 공감 섹션 — 팔고 싶은데 장이 없다 / 사고 싶은데 비교가 없다",
            max_w=900,
        )
        self.spacer(10)

        # MARKETPLACE
        self.add_heading("실제 사용 화면", "마켓플레이스")
        self.add_paragraphs(
            "로그인 후 프로젝트 목록에서 매물을 둘러보고, "
            "「내 프로젝트 올리기」로 바로 등록을 시작할 수 있어요.",
            size=26,
            color=(148, 163, 184, 255),
            gap=10,
        )
        self.add_shot(
            SHOTS / "app_shell.png",
            "앱 화면 — 매물 카드 · 검색 · 올리기",
            max_w=720,
        )
        self.spacer(12)

        # OUTCOME FLOW (like export samples)
        self.add_heading("거래 결과", "이렇게 흘러갑니다")
        self.add_paragraphs(
            "등록만 하고 끝이 아니라, 가격이 보이고 입찰이 붙고, "
            "합의 후 이전이 이어지도록 설계했습니다. "
            "“폴더에만 있던 작업”이 “공개 가격이 있는 매물”이 됩니다.",
            size=26,
            color=(148, 163, 184, 255),
            gap=10,
        )
        self.spacer(8)
        self.add_outcome_cards()
        self.spacer(12)

        # BUYER ANGLE + PG
        self.add_heading("사고 싶은 분", "0부터 다시 만들기 전에")
        self.add_shot(
            SHOTS / "landing_features.png",
            "구매자 관점 — 실행 가능한 초안을 찾고, 안전 절차로 인수",
            max_w=900,
        )
        self.spacer(10)

        # B2B
        self.add_heading("팀 · 스튜디오", "B2B 한 줄")
        self.add_highlight_box(
            "팀 단위로도",
            [
                "팀·메이커 스튜디오의 잠든 프로토타입을 매물로 올려 보세요.",
                "인수 쪽에서는 데모 있는 초안을 대시보드처럼 비교·입찰할 수 있습니다.",
            ],
        )
        self.spacer(12)

        # FREE / LOW FRICTION (no VIP)
        self.add_heading("부담 없이 시작", "카드 없이, 올리기부터")
        self.add_highlight_box(
            "등록 무료 · 가입 장벽 낮음",
            [
                "카드 등록 없이 가입 후, 프로젝트 올리기는 무료",
                "거래가 성사될 때만 수수료 약 10% (미성사 시 등록비 0)",
                "구매자 추가 수수료 없음 · 먼저 둘러보고 관심만 남겨도 OK",
            ],
        )
        self.spacer(10)
        self.add_paragraphs(
            "“올리면 바로 돈 내야 하나?” 걱정하지 않으셔도 됩니다. "
            "등록은 무료이고, 성사됐을 때만 수수료가 붙습니다. "
            "먼저 데모·스토리만 올려 보시고, 피드백 주시면 감사하겠습니다.",
            size=26,
            color=(148, 163, 184, 255),
            gap=10,
        )
        self.spacer(24)

        # CTA
        cta_h = 240
        cta, d = self.canvas(cta_h)
        msg = "WakeAgain"
        mf = fnt(44, True)
        mw, mh = text_size(d, msg, mf)
        d.rounded_rectangle(
            [(W - mw) // 2 - 48, 24, (W + mw) // 2 + 48, 24 + mh + 36],
            radius=32,
            fill=(124, 58, 237, 50),
            outline=(*PURPLE, 180),
            width=2,
        )
        d.text(((W - mw) // 2, 42), msg, font=mf, fill=(*PURPLE, 255))
        sub = "프로젝트 올리기 (무료) · 관심 구매자로 시작"
        sw, _ = text_size(d, sub, fnt(24))
        d.text(((W - sw) // 2, 120), sub, font=fnt(24), fill=(203, 213, 225, 255))
        sub2 = "등록 무료 → 성사 시 수수료 약 10% → 피드백 환영"
        sw2, _ = text_size(d, sub2, fnt(22))
        d.text(((W - sw2) // 2, 158), sub2, font=fnt(22), fill=(148, 163, 184, 255))
        foot = "CoreLabs · 1인 개발 · 오픈 초기 · corelabs.studio@gmail.com"
        fw, _ = text_size(d, foot, fnt(20))
        d.text(((W - fw) // 2, 198), foot, font=fnt(20), fill=(100, 116, 139, 255))
        self.push(cta)
        self.spacer(40)

        total_h = sum(p.height for p in self.parts)
        bg = draw_bg(total_h)
        y = 0
        for part in self.parts:
            bg.paste(part, (0, y), part)
            y += part.height
        return bg.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    needed = ["landing_mobile.png", "landing_mid.png", "app_shell.png", "landing_features.png"]
    missing = [n for n in needed if not (SHOTS / n).exists()]
    if missing:
        raise SystemExit(f"missing shots: {missing} — run scripts/capture_promo_shots.py first")

    img = Builder().build()
    png = OUT / "wakeagain_promo_long_story.png"
    jpg = OUT / "wakeagain_promo_long_story.jpg"
    img.save(png, "PNG", optimize=True)
    img.save(jpg, "JPEG", quality=90, optimize=True)
    print("saved", png, img.size)
    print("saved", jpg, jpg.stat().st_size)


if __name__ == "__main__":
    main()

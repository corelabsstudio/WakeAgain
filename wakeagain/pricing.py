"""
Starting bid guidance + product status classification.

Product rules:
- 시작 입찰가는 제품 완성도(상태)에 따라 달라야 한다.
- 상태 라벨은 판매자가 임의로 고르는 게 아니라, 아래 기준에 맞춰 고른다.
- UI 문구는 쉬운 말(진입장벽↓). 내부 key는 영문 고정.
"""
from __future__ import annotations

from typing import Any

# All amounts KRW — keys are stable English codes
STATUS_PRICING: dict[str, dict[str, Any]] = {
    "prototype": {
        "key": "prototype",
        "label": "돌아가는 초안",
        "blurb": "아직 덜 만들었지만, 화면·데모로 ‘돌아가는 것’은 볼 수 있어요. 시작가는 낮게.",
        "suggest": 150_000,
        "min": 50_000,
        "max_soft": 5_000_000,
        "min_increment": 10_000,
        "examples": "예: 화면 몇 장 + 로컬/영상 데모",
        "when": "아이디어를 코드로 확인한 단계. 완성 제품보다 ‘스케치가 돌아감’에 가깝습니다.",
        "criteria_yes": [
            "클릭·실행 가능한 화면이나 데모가 있다 (영상·사진·링크 중 하나)",
            "핵심 기능 일부만 동작해도 된다",
            "스토어·정식 공개 마케팅은 거의 안 했다",
            "유료 결제·실사용 지표는 없거나 아주 적다",
        ],
        "criteria_no": [
            "불특정 다수가 쓰는 공개 서비스가 있다 → 「써 볼 수 있는 제품」 또는 「공개했다가 멈춤」",
            "아이디어·기획서·피그마만 있고 실행물이 없다 → 등록 불가",
        ],
        "demo_expect": "영상, 스테이징 링크, 스크린 몇 장이면 충분합니다.",
    },
    "beta": {
        "key": "beta",
        "label": "써 볼 수 있는 제품",
        "blurb": "남에게 써 보라고 줄 수 있는 형태입니다. 아직 정식 성장 단계는 아니어도 됩니다.",
        "suggest": 400_000,
        "min": 150_000,
        "max_soft": 15_000_000,
        "min_increment": 10_000,
        "examples": "예: 배포 URL, 가입 후 핵심 기능 동작",
        "when": "지인·테스터에게 링크를 줘 볼 수 있는 단계. 본격 런칭·마케팅은 약해도 됩니다.",
        "criteria_yes": [
            "들어가 볼 수 있는 주소 또는 설치 파일이 있다",
            "핵심 기능 1개 이상이 처음부터 끝까지 동작한다",
            "가입·시작 흐름이 있다 (완벽하지 않아도 됨)",
            "소수만 써 봤고, 스토어 공식 런칭·대규모 홍보는 약하다",
        ],
        "criteria_no": [
            "스토어에 정식 공개 후 오래 손 놓음 → 「공개했다가 멈춤」",
            "화면만 있고 실제 기능이 거의 없다 → 「돌아가는 초안」",
        ],
        "demo_expect": "실제로 들어가 볼 수 있는 링크 또는 설치 + 짧은 사용 설명",
    },
    "launched": {
        "key": "launched",
        "label": "공개했다가 멈춤",
        "blurb": "한 번 세상에 나갔거나 나갈 준비가 됐는데, 지금은 운영이 멈춘 상태. 시작가는 조금 높게.",
        "suggest": 800_000,
        "min": 300_000,
        "max_soft": 50_000_000,
        "min_increment": 50_000,
        "examples": "예: 스토어 링크, 과거 사용자, 도메인·브랜드",
        "when": "정식 공개·운영 이력이 있거나, 출시 직후 방치된 ‘잠든 실서비스’.",
        "criteria_yes": [
            "스토어 등록, 공개 도메인, 결제 등 ‘공개’로 볼 수 있는 이력이 있다",
            "과거 사용자·방문·매출 기록이 있을 수 있다 (없어도 공개 이력만으로 가능)",
            "지금은 홍보·업데이트·운영이 거의 없다",
            "코드·도메인·계정 등 넘길 자산이 비교적 분명하다",
        ],
        "criteria_no": [
            "외부에 한 번도 공개한 적 없다 → 「돌아가는 초안」 또는 「써 볼 수 있는 제품」",
            "공개 이력이 불명하고 데모만 있다 → 한 단계 낮게",
        ],
        "demo_expect": "라이브/예전 주소, 스토어 링크, 과거 화면 캡처, 넘길 자산 목록",
    },
    "other": {
        "key": "other",
        "label": "그 외 (도구·코드·자료)",
        "blurb": "완성형 앱/사이트가 아니라 부품·도구·자료에 가깝습니다.",
        "suggest": 200_000,
        "min": 50_000,
        "max_soft": 20_000_000,
        "min_increment": 10_000,
        "examples": "예: 라이브러리, 템플릿, 데이터, 모델 가중치",
        "when": "사용자가 쓰는 ‘서비스’보다 개발 부품·자산에 가깝다.",
        "criteria_yes": [
            "라이브러리, 템플릿, 데이터, 모델, 스크립트 모음 등",
            "일반 앱/사이트 생애주기로 말하기 어렵다",
            "그래도 실행·재현 가능한 파일·코드·문서가 있다",
        ],
        "criteria_no": [
            "명확한 웹/앱 제품이면 → 위 세 단계 중 하나",
            "순수 아이디어·문서 한 장만 → 등록 불가",
        ],
        "demo_expect": "README, 샘플 실행, 사용 예 설명",
    },
}

DEFAULT_STATUS = "prototype"

# Old stored values / typos → key
_STATUS_ALIASES: dict[str, str] = {
    "prototype": "prototype",
    "proto": "prototype",
    "프로토타입": "prototype",
    "돌아가는 초안": "prototype",
    "초안": "prototype",
    "스케치": "prototype",
    "beta": "beta",
    "베타": "beta",
    "써 볼 수 있는 제품": "beta",
    "테스트 중": "beta",
    "launched": "launched",
    "출시됨·방치": "launched",
    "출시됨": "launched",
    "방치": "launched",
    "공개했다가 멈춤": "launched",
    "launch": "launched",
    "other": "other",
    "기타": "other",
    "그 외 (도구·코드·자료)": "other",
    "그 외": "other",
}

CLASSIFICATION_INTRO = {
    "title": "제품 상태 — 쉬운 고르는 법",
    "summary": (
        "어려운 용어 대신, ‘지금 얼마나 만들어졌는지’를 고르면 됩니다. "
        "과장은 신뢰·심사에 불리합니다. "
        "실행물(데모·영상)이 없는 아이디어만 있는 매물은 받지 않습니다."
    ),
    "how_to_choose": [
        "실행물(화면·영상·링크)이 없으면 → 등록하지 마세요.",
        "스토어·정식 공개 후 손 놓았으면 → 「공개했다가 멈춤」.",
        "남에게 써 보라 링크를 줄 수 있으면 → 「써 볼 수 있는 제품」.",
        "부분만 돌아가면 → 「돌아가는 초안」.",
        "앱/사이트가 아니라 코드·자료·도구면 → 「그 외」.",
    ],
    "honesty": "애매하면 한 단계 낮게(초안 쪽) 잡는 것을 권장합니다. 솔직한 상태가 입찰에 유리할 때가 많습니다.",
}


def normalize_status(status: str) -> str:
    s = (status or "").strip()
    if not s:
        return DEFAULT_STATUS
    if s in STATUS_PRICING:
        return s
    if s in _STATUS_ALIASES:
        return _STATUS_ALIASES[s]
    low = s.lower()
    if "proto" in low or "프로토" in s or "초안" in s or "스케치" in s:
        return "prototype"
    if "beta" in low or "베타" in s or "써 볼" in s:
        return "beta"
    if "출시" in s or "방치" in s or "launch" in low or "멈춤" in s or "공개했" in s:
        return "launched"
    if "기타" in s or "other" in low or "도구" in s or "자료" in s:
        return "other"
    return DEFAULT_STATUS


def pricing_for(status: str) -> dict[str, Any]:
    key = normalize_status(status)
    return dict(STATUS_PRICING[key], status=key)


def status_label(status: str | None) -> str:
    key = normalize_status(status or "")
    return STATUS_PRICING[key]["label"]


def _status_public(k: str, v: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": k,
        "label": v["label"],
        "key": v["key"],
        "suggest": v["suggest"],
        "min": v["min"],
        "max_soft": v["max_soft"],
        "min_increment": v["min_increment"],
        "blurb": v["blurb"],
        "examples": v["examples"],
        "when": v.get("when", ""),
        "criteria_yes": list(v.get("criteria_yes") or []),
        "criteria_no": list(v.get("criteria_no") or []),
        "demo_expect": v.get("demo_expect", ""),
    }


def public_policy() -> dict[str, Any]:
    return {
        "currency": "KRW",
        "rule": "시작 입찰가는 제품이 얼마나 만들어졌는지(상태)에 따라 최저·권장가가 다릅니다.",
        "classification": CLASSIFICATION_INTRO,
        "statuses": [_status_public(k, v) for k, v in STATUS_PRICING.items()],
    }


def validate_start_price(status: str, price_start: int | None) -> tuple[int, dict[str, Any]]:
    band = pricing_for(status)
    label = band["label"]
    if price_start is None:
        raise ValueError(
            f"「{label}」 매물은 시작 입찰가가 필요합니다. "
            f"권장 ₩{band['suggest']:,} · 최저 ₩{band['min']:,}"
        )
    price = int(price_start)
    if price < 0:
        raise ValueError("시작가는 0 이상이어야 합니다.")
    if price < int(band["min"]):
        raise ValueError(
            f"「{label}」 상태의 최저 시작가는 ₩{band['min']:,} 입니다. "
            f"(권장 ₩{band['suggest']:,})"
        )
    soft = price > int(band["max_soft"])
    meta: dict[str, Any] = {
        "status": band["status"],
        "label": label,
        "band": {
            "min": band["min"],
            "suggest": band["suggest"],
            "max_soft": band["max_soft"],
            "min_increment": band["min_increment"],
        },
        "suggested_increment": band["min_increment"],
        "soft_cap_warning": soft,
    }
    if soft:
        meta["soft_high_message"] = (
            f"「{label}」 권장 상단(약 ₩{band['max_soft']:,})을 넘겼습니다. "
            "등록은 가능하지만 구매자 설득이 더 필요할 수 있습니다."
        )
    return price, meta

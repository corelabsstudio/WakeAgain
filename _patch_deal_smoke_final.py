# -*- coding: utf-8 -*-
from pathlib import Path
import re

STORY = "자동 테스트용 매물 스토리입니다. 왜 파는지 배경을 충분히 적습니다."
PNG = (
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d763f8cfc000000301010018dd8db00000000049454e44ae426082"
)
HELPER = f'''
def _qa_demo_images(user_id: int) -> list[str]:
    from wakeagain import media as media_mod
    png = bytes.fromhex("{PNG}")
    urls = []
    for i in range(2):
        meta = media_mod.save_demo_image(user_id=int(user_id), raw=png, filename_hint=f"qa{{i}}.png")
        urls.append(meta["url"])
    return urls
'''

EXTRA = f'''
            "demo_images": _qa_demo_images(int(seller["id"])),
            "attest_shots": True,
            "features": [
                "예약과 고객 목록을 한 화면에서 관리한다",
                "알림으로 다음 일정을 놓치지 않게 한다",
                "모바일에서도 간단히 상태 변경이 된다",
            ],
            "audience": "혼자 예약 관리하는 소상공인",
            "works_now": "데모 링크에서 로그인 없이 예약 목록과 상태 변경을 눌러 볼 수 있다.",
            "limits": "결제 연동과 실 SMS 알림은 아직 없고 더미만 동작한다.",
            "acquisition": "made",
            "attest_works": True,
            "attest_features": True,
            "attest_license": True,
            "attest_rights": True,
            "attest_transfer": True,
'''

# deal
p = Path("_deal_flow_test.py")
t = p.read_text(encoding="utf-8")
if "def _qa_demo_images" not in t:
    t = t.replace("from server import app", "from server import app\n" + HELPER)
if "init_db()" not in t:
    t = t.replace(
        "cl = TestClient(app)",
        "cl = TestClient(app)\nfrom wakeagain.db import init_db\ninit_db()",
    )
# lengthen stories
t = re.sub(r'"story":\s*"[^"]+"', f'"story": "{STORY}"', t)
# inject after assets lines in project posts
if "demo_images" not in t:
    t = t.replace('"assets": ["code", "domain"],', '"assets": ["code", "domain"],' + EXTRA)
    t = t.replace('"assets": ["code"],', '"assets": ["code"],' + EXTRA)
# if first inject used seller but second create also seller ok
p.write_text(t, encoding="utf-8")
print("deal", "demo_images" in t, "init_db" in t)

# smoke
p = Path("_smoke_check.py")
t = p.read_text(encoding="utf-8")
if "def _qa_demo_images" not in t:
    t = t.replace("from server import app", "from server import app\n" + HELPER)
if "cl = TestClient(app)" not in t:
    # original has cl = TestClient(app)
    pass
if "init_db()" not in t:
    t = t.replace(
        "cl = TestClient(app)",
        "cl = TestClient(app)\nfrom wakeagain.db import init_db\ninit_db()",
    )
# find successful create payload with attest_works and add fields
# Replace short story
t = t.replace('"story": "스모크 테스트용 스토리입니다."', f'"story": "{STORY}"')

# Inject into create that has attest_works True
old = '''            "attest_works": True,
            "attest_license": True,
            "attest_rights": True,'''
if old in t and "attest_features" not in t:
    t = t.replace(
        old,
        '''            "demo_images": _qa_demo_images(int(uid)),
            "attest_shots": True,
            "features": [
                "예약과 고객 목록을 한 화면에서 관리한다",
                "알림으로 다음 일정을 놓치지 않게 한다",
                "모바일에서도 간단히 상태 변경이 된다",
            ],
            "audience": "혼자 예약 관리하는 소상공인",
            "works_now": "데모 링크에서 로그인 없이 예약 목록과 상태 변경을 눌러 볼 수 있다.",
            "limits": "결제 연동과 실 SMS 알림은 아직 없고 더미만 동작한다.",
            "acquisition": "made",
            "attest_works": True,
            "attest_features": True,
            "attest_license": True,
            "attest_rights": True,
            "attest_transfer": True,''',
    )
# also earlier creates without identity need same for non-attest failure paths? only success path needs full
# Add demo images to other project posts that might succeed - identity blocked one should still fail on identity
# For posts that only have story and assets, add demo images + fields so failure reason is identity not images
for old_assets in ['"assets": ["code"],']:
    # only inject if next 300 chars lack demo_images - do manually once after each assets for non-attest-fail cases
    pass

# Ensure uid exists before use - smoke sets uid from register
if "uid =" not in t and "user" in t:
    # look for register success body user id
    t = t.replace(
        'token = body["token"]',
        'token = body["token"]\n    uid = int((body.get("user") or {}).get("id") or 0)',
        1,
    )

p.write_text(t, encoding="utf-8")
print("smoke", "attest_features" in t, "init_db" in t, "uid =" in t)

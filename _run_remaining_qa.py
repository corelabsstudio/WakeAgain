# -*- coding: utf-8 -*-
import os, re, subprocess, sys, tempfile, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
py = sys.executable

# fix smoke uid
smoke = ROOT / "_smoke_check.py"
t = smoke.read_text(encoding="utf-8")
if "uid = int" not in t:
    t = re.sub(
        r'token = body\["token"\]',
        'token = body["token"]\n    uid = int((body.get("user") or {}).get("id") or 0)',
        t,
        count=1,
    )
    smoke.write_text(t, encoding="utf-8")
    print("smoke uid fixed")

data = Path(tempfile.mkdtemp(prefix="wa_qa_"))
env = os.environ.copy()
env.update(
    {
        "DATA_DIR": str(data),
        "ADMIN_SECRET": "wakeagain-admin-dev",
        "EMAIL_DEV_MODE": "1",
        "APP_SECRET": "qa-local-x",
        "JWT_SECRET": "qa-local-y",
        "AUCTION_SCHEDULER": "0",
    }
)

results = {}
for name in [
    "_test_unit.py",
    "_auction_suite_test.py",
    "_auction_advanced_test.py",
    "_block_user_test.py",
    "_deal_flow_test.py",
    "_smoke_check.py",
]:
    print("\n====", name, "====", flush=True)
    p = subprocess.run(
        [py, str(ROOT / name)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    fails = [ln for ln in out.splitlines() if "[FAIL]" in ln]
    results[name] = {"exit": p.returncode, "fails": fails}
    print("EXIT", p.returncode, "FAILS", len(fails))
    for ln in fails[:12]:
        print(ln)
    for ln in out.splitlines()[-8:]:
        print(ln)

shutil.rmtree(data, ignore_errors=True)
print("\nFINAL", {k: (v["exit"], len(v["fails"])) for k, v in results.items()})
sys.exit(0 if all(v["exit"] == 0 for v in results.values()) else 1)

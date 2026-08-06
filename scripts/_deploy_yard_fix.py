# -*- coding: utf-8 -*-
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

tok_paths = [
    Path(r"C:\Users\hysoo\projects\RoadLog\.launch\railway.token"),
    Path(r"C:\Users\hysoo\projects\WakeAgain\.launch\railway.token"),
]
tok = None
for p in tok_paths:
    if p.exists():
        tok = (
            p.read_text(encoding="utf-8-sig")
            .strip()
            .splitlines()[0]
            .strip()
            .strip('"')
            .strip("'")
        )
        print("token from", p)
        break
if not tok:
    raise SystemExit("no railway token")

E = "2a3b69b2-441f-4369-9582-eaaa8e2c4f39"
S = "32c989b1-4e9b-4057-adab-547bc8e2ebf1"
SHA = subprocess.check_output(
    ["git", "rev-parse", "HEAD"],
    cwd=Path(r"C:\Users\hysoo\projects\WakeAgain"),
    text=True,
).strip()
print("SHA", SHA)


def gql(q, v=None):
    body = json.dumps({"query": q, "variables": v or {}}).encode()
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        data=body,
        headers={
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        return {"http": e.code, "body": e.read().decode("utf-8", "replace")[:900]}


for name, q, v in [
    (
        "deployV2commit",
        """
        mutation($e:String!, $s:String!, $c:String!) {
          serviceInstanceDeployV2(environmentId:$e, serviceId:$s, commitSha:$c)
        }
        """,
        {"e": E, "s": S, "c": SHA},
    ),
    (
        "deployV2",
        """
        mutation($e:String!, $s:String!) {
          serviceInstanceDeployV2(environmentId:$e, serviceId:$s)
        }
        """,
        {"e": E, "s": S},
    ),
]:
    print("==", name)
    r = gql(q, v)
    print(json.dumps(r, ensure_ascii=False)[:700])
    if r.get("data") and not r.get("errors"):
        break

# -*- coding: utf-8 -*-
"""Deploy latest master HEAD to WakeAgain Railway web service."""
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOK_PATHS = [
    ROOT / ".launch" / "railway.token",
    Path(r"C:\Users\hysoo\Projects\RoadLog\.launch\railway.token"),
    Path(r"C:\Users\hysoo\projects\RoadLog\.launch\railway.token"),
]
GQL = "https://backboard.railway.app/graphql/v2"
ENV = "2a3b69b2-441f-4369-9582-eaaa8e2c4f39"
SERVICE = "32c989b1-4e9b-4057-adab-547bc8e2ebf1"


def token() -> str:
    for p in TOK_PATHS:
        if p.is_file():
            t = p.read_text(encoding="utf-8-sig").strip().splitlines()[0].strip()
            t = t.replace("\ufeff", "").strip('"').strip("'")
            if t:
                return t
    raise SystemExit("no railway token")


def gql(tok: str, query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        GQL,
        data=body,
        headers={
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/json",
            "User-Agent": "WakeAgainDeploy/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        return {"http": e.code, "body": e.read().decode("utf-8", "replace")[:900]}


def head_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()


def main() -> None:
    tok = token()
    sha = head_sha()
    print("HEAD", sha)
    attempts = [
        (
            "deployV2+sha",
            """
            mutation($e:String!, $s:String!, $c:String!) {
              serviceInstanceDeployV2(environmentId:$e, serviceId:$s, commitSha:$c)
            }
            """,
            {"e": ENV, "s": SERVICE, "c": sha},
        ),
        (
            "deployV2",
            """
            mutation($e:String!, $s:String!) {
              serviceInstanceDeployV2(environmentId:$e, serviceId:$s)
            }
            """,
            {"e": ENV, "s": SERVICE},
        ),
        (
            "deploy",
            """
            mutation($e:String!, $s:String!) {
              serviceInstanceDeploy(environmentId:$e, serviceId:$s)
            }
            """,
            {"e": ENV, "s": SERVICE},
        ),
    ]
    for name, q, v in attempts:
        r = gql(tok, q, v)
        print("==", name, json.dumps(r, ensure_ascii=False)[:500])


if __name__ == "__main__":
    main()

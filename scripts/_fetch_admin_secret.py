# -*- coding: utf-8 -*-
import json
import urllib.request
from pathlib import Path

tok = (
    Path(r"C:\Users\hysoo\projects\RoadLog\.launch\railway.token")
    .read_text(encoding="utf-8-sig")
    .strip()
    .splitlines()[0]
    .strip()
    .strip('"')
    .strip("'")
)

# shared variables for environment
# https://docs.railway.com/reference/public-api
queries = [
    (
        "variables",
        """
        query($projectId: String!, $environmentId: String!, $serviceId: String) {
          variables(
            projectId: $projectId
            environmentId: $environmentId
            serviceId: $serviceId
          )
        }
        """,
        {
            "projectId": "2977b794-a0a8-42af-8ee5-add128046ae2",
            "environmentId": "2a3b69b2-441f-4369-9582-eaaa8e2c4f39",
            "serviceId": "32c989b1-4e9b-4057-adab-547bc8e2ebf1",
        },
    ),
    (
        "variables no service",
        """
        query($projectId: String!, $environmentId: String!) {
          variables(projectId: $projectId, environmentId: $environmentId)
        }
        """,
        {
            "projectId": "2977b794-a0a8-42af-8ee5-add128046ae2",
            "environmentId": "2a3b69b2-441f-4369-9582-eaaa8e2c4f39",
        },
    ),
]


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
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode())


for name, q, v in queries:
    print("==", name)
    try:
        r = gql(q, v)
        print(json.dumps(r, ensure_ascii=False)[:800])
        data = (r.get("data") or {}).get("variables")
        if isinstance(data, dict):
            admin = data.get("ADMIN_SECRET")
            if admin:
                print("ADMIN_SECRET found len", len(admin), "prefix", admin[:6])
                Path(r"C:\Users\hysoo\projects\WakeAgain\data\_admin_secret_runtime.txt").write_text(
                    admin, encoding="utf-8"
                )
                print("wrote data/_admin_secret_runtime.txt")
    except Exception as e:
        print("err", e)

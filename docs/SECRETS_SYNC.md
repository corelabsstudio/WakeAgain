# Admin / production secrets sync

## Single source of truth

| Layer | Role |
|-------|------|
| **Railway Variables** | Live production truth |
| `.launch/production-secrets.local.txt` | Local mirror of Railway (gitignored) |
| `.env` | Local server — **must match** mirror for `ADMIN_SECRET` / `APP_SECRET` |

Never commit either file.

## Keep them aligned

```powershell
cd C:\Users\hysoo\projects\WakeAgain
python _sync_admin_secrets.py
```

- Probes live admin session with local keys
- If one works: writes **both** files to that key + optional QA user cleanup
- If neither works: prints one-time Railway copy steps

## Deploy rules

```powershell
# normal deploy — does NOT touch secrets
python deploy_railway.py

# push EXISTING secrets to Railway only (refuses to invent ADMIN_SECRET)
python deploy_railway.py --set-vars
```

## If admin UI returns 401

1. Open Railway → WakeAgain → Variables → `ADMIN_SECRET`
2. **Either** paste Railway value into both local files, **or** paste local `production-secrets.local.txt` value into Railway (pick one truth, then match the other)
3. Run `python _sync_admin_secrets.py` again

## Do not

- Run `--set-vars` with empty secrets (old code minted a new key — that path is blocked now)
- Recreate `.env` without the production mirror present
- Paste secrets into chat or git

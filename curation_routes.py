"""Retire matching entry points without deleting stored records or auth settings."""
from fastapi.responses import JSONResponse, RedirectResponse

AUTH_PATHS = ('/api/auth/', '/api/v1/auth/oauth/')
AUTH_READ_PATHS = {'/api/me', '/api/session'}
PUBLIC_FILES = {'/', '/index.html', '/favicon.svg', '/manifest.json', '/sw.js', '/health'}
PUBLIC_PREFIXES = ('/curation/', '/icons/', '/legal/')


def retired_action(path: str, method: str = 'GET') -> str | None:
    if path == '/api/curation/catalog' and method in ('GET','HEAD'):
        return None
    if path in PUBLIC_FILES or path.startswith(PUBLIC_PREFIXES):
        return None
    if path.startswith(AUTH_PATHS) or path in AUTH_READ_PATHS:
        return None
    if path.startswith('/api/') or path.startswith('/uploads/'):
        return 'gone'
    return 'home' if method in ('GET', 'HEAD') else 'gone'


def install(app):
    @app.middleware('http')
    async def retire_matching(request, call_next):
        action = retired_action(request.url.path, request.method)
        if action == 'home':
            return RedirectResponse('/', status_code=307, headers={'Cache-Control': 'no-store'})
        if action == 'gone':
            return JSONResponse(
                {'detail': '작업·견적 서비스 제공이 종료되었습니다.', 'home': '/'},
                status_code=410, headers={'Cache-Control': 'no-store'},
            )
        return await call_next(request)

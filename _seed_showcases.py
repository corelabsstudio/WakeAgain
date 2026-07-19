from wakeagain import db as database

database.init_db()
now = database._now()
samples = [
    (
        "민수",
        "HabitRing",
        "습관 루틴 체크 웹앱 — 주간 리포트",
        "주말에 만들어서 친구 5명에게 써 보게 했습니다. 알림은 아직 없고 체크리스트만 됩니다.",
        "영상 데모 준비 중",
        "beta",
        "webapp",
        350000,
        68,
    ),
    (
        "익명개발자",
        "InvoiceLite",
        "간이 견적서 PDF 생성기",
        "프리랜서용으로 쓰다 멈춘 도구입니다. HTML→PDF 한 방이 핵심입니다.",
        "로컬 실행 README",
        "launched",
        "desktop",
        220000,
        55,
    ),
    (
        "소라",
        "PetWalk Map",
        "산책 경로 공유 모바일 초안",
        "지도 위에 경로를 그리는 화면까지 만들었습니다. 로그인·채팅은 없습니다.",
        "스크린 녹화 2분",
        "prototype",
        "mobile",
        150000,
        42,
    ),
]

with database.db() as conn:
    n = conn.execute("SELECT COUNT(*) AS c FROM showcases").fetchone()["c"]
    if n == 0:
        for s in samples:
            conn.execute(
                """
                INSERT INTO showcases (
                  user_id, author_name, title, one_liner, story, demo,
                  status_key, product_type, price_hint, diag_score,
                  cheer_count, listing_status, created_at
                ) VALUES (NULL,?,?,?,?,?,?,?,?,?,0,'approved',?)
                """,
                (*s, now),
            )
        print("seeded", len(samples))
    else:
        print("already", n)
    for r in conn.execute("SELECT id, title FROM showcases").fetchall():
        print(r["id"], r["title"])

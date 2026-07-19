import sqlite3
from pathlib import Path

c = sqlite3.connect(str(Path(__file__).parent / "data" / "wakeagain.db"))
print([r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])

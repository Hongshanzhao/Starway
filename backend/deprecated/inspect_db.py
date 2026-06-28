import sqlite3, os
from backend.config import SQLITE_DB_PATH
print('db path', SQLITE_DB_PATH)
conn = sqlite3.connect(SQLITE_DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('tables:', cursor.fetchall())
try:
    cursor.execute("PRAGMA table_info(match_history)")
    print('match_history columns:', cursor.fetchall())
except Exception as e:
    print('error table info', e)
conn.close()

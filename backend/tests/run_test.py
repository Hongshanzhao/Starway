import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from db import init_db, get_db

print('cwd', os.getcwd())
init_db()
conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM job")
print('jobs count', cursor.fetchone()[0])
cursor.execute("SELECT * FROM job LIMIT 3")
for row in cursor.fetchall():
    print(dict(row))

# 验证新增的用户表是否存在并可写
try:
    cursor.execute("SELECT count(*) FROM users")
    print('users table exists, count =', cursor.fetchone()[0])
except Exception as e:
    print('users table check error', e)

# 示例插入一个用户
try:
    from werkzeug.security import generate_password_hash
    pw = generate_password_hash('secret')
    cursor.execute("INSERT OR IGNORE INTO users (username, phone, password_hash) VALUES (?,?,?)",
                   ('testuser','13800000000', pw))
    # also ensure an admin account exists
    cursor.execute("INSERT OR IGNORE INTO users (username, phone, password_hash, role) VALUES (?,?,?,?)",
                   ('admin','13811110000', pw, 'admin'))
    conn.commit()
    cursor.execute("SELECT id, username, phone, role FROM users WHERE username=?", ('testuser',))
    user_row = cursor.fetchone()
    print('inserted user', user_row)
    cursor.execute("SELECT id, username, phone, role FROM users WHERE username=?", ('admin',))
    print('inserted admin', cursor.fetchone())
    # 插入一个关联学生记录
    cursor.execute(
        "INSERT INTO student (user_id, name, major, grade) VALUES (?,?,?,?)",
        (user_row['id'], '张三', '计算机', '大三')
    )
    conn.commit()
    cursor.execute("SELECT id, user_id FROM student WHERE user_id=?", (user_row['id'],))
    print('associated student', cursor.fetchone())
except Exception as e:
    print('user insert error', e)

conn.close()

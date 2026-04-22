import sqlite3

conn = sqlite3.connect("lms.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    file_path TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    video_id INTEGER,
    watched INTEGER
)
""")

# default users
conn.execute("INSERT INTO users (username, password, role) VALUES ('faculty1', '123', 'faculty')")
conn.execute("INSERT INTO users (username, password, role) VALUES ('student1', '123', 'student')")

conn.commit()
conn.close()

import sqlite3, shutil
from typing import List, Dict, Optional

_DB_PATH = "school.db"
_CONN: Optional[sqlite3.Connection] = None

def connect(db_path: str = _DB_PATH):
    global _CONN, _DB_PATH
    _DB_PATH = db_path
    if _CONN is None:
        _CONN = sqlite3.connect(_DB_PATH)
        _CONN.execute("PRAGMA foreign_keys = ON;")
    return _CONN

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL CHECK(age >= 0),
        email TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS instructors (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL CHECK(age >= 0),
        email TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS courses (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        instructor_id TEXT,
        FOREIGN KEY(instructor_id) REFERENCES instructors(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS registrations (
        student_id TEXT NOT NULL,
        course_id TEXT NOT NULL,
        PRIMARY KEY (student_id, course_id),
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_students_name   ON students(name);
    CREATE INDEX IF NOT EXISTS idx_instructors_name ON instructors(name);
    CREATE INDEX IF NOT EXISTS idx_courses_name     ON courses(name);
    """)
    conn.commit()


def create_student(sid: str, name: str, age: int, email: str):
    conn = connect()
    conn.execute("INSERT INTO students(id, name, age, email) VALUES(?,?,?,?)",
                 (sid.strip(), name.strip(), int(age), email.strip()))
    conn.commit()

def list_students() -> List[Dict]:
    conn = connect()
    rows = conn.execute("SELECT id, name, age, email FROM students ORDER BY id").fetchall()
    return [{"id": r[0], "name": r[1], "age": r[2], "email": r[3]} for r in rows]

def update_student(sid: str, name: str, age: int, email: str):
    conn = connect()
    conn.execute("UPDATE students SET name=?, age=?, email=? WHERE id=?",
                 (name.strip(), int(age), email.strip(), sid))
    conn.commit()

def delete_student(sid: str):
    conn = connect()
    conn.execute("DELETE FROM students WHERE id=?", (sid,))
    conn.commit()


def create_instructor(iid: str, name: str, age: int, email: str):
    conn = connect()
    conn.execute("INSERT INTO instructors(id, name, age, email) VALUES(?,?,?,?)",
                 (iid.strip(), name.strip(), int(age), email.strip()))
    conn.commit()

def list_instructors() -> List[Dict]:
    conn = connect()
    rows = conn.execute("SELECT id, name, age, email FROM instructors ORDER BY id").fetchall()
    return [{"id": r[0], "name": r[1], "age": r[2], "email": r[3]} for r in rows]

def update_instructor(iid: str, name: str, age: int, email: str):
    conn = connect()
    conn.execute("UPDATE instructors SET name=?, age=?, email=? WHERE id=?",
                 (name.strip(), int(age), email.strip(), iid))
    conn.commit()

def delete_instructor(iid: str):
    conn = connect()
    conn.execute("DELETE FROM instructors WHERE id=?", (iid,))
    conn.commit()


def create_course(cid: str, name: str, instructor_id: Optional[str] = None):
    conn = connect()
    conn.execute("INSERT INTO courses(id, name, instructor_id) VALUES(?,?,?)",
                 (cid.strip(), name.strip(), instructor_id))
    conn.commit()

def list_courses() -> List[Dict]:
    conn = connect()
    rows = conn.execute("""
        SELECT c.id, c.name, c.instructor_id, i.name
        FROM courses c
        LEFT JOIN instructors i ON i.id = c.instructor_id
        ORDER BY c.id
    """).fetchall()
    out = []
    for cid, cname, inst_id, inst_name in rows:
        n = conn.execute("SELECT COUNT(*) FROM registrations WHERE course_id=?", (cid,)).fetchone()[0]
        out.append({
            "id": cid, "name": cname,
            "instructor_id": inst_id,
            "instructor_name": inst_name if inst_name else None,
            "enrolled_count": n
        })
    return out

def update_course(cid: str, name: str, instructor_id: Optional[str]):
    conn = connect()
    conn.execute("UPDATE courses SET name=?, instructor_id=? WHERE id=?",
                 (name.strip(), instructor_id, cid))
    conn.commit()

def delete_course(cid: str):
    conn = connect()
    conn.execute("DELETE FROM courses WHERE id=?", (cid,))
    conn.commit()

def assign_instructor(course_id: str, instructor_id: Optional[str]):
    conn = connect()
    conn.execute("UPDATE courses SET instructor_id=? WHERE id=?", (instructor_id, course_id))
    conn.commit()


def enroll_student(student_id: str, course_id: str):
    conn = connect()
    conn.execute("INSERT OR IGNORE INTO registrations(student_id, course_id) VALUES(?,?)",
                 (student_id, course_id))
    conn.commit()

def list_enrolled(course_id: str) -> List[Dict]:
    conn = connect()
    rows = conn.execute("""
        SELECT s.id, s.name, s.age, s.email
        FROM registrations r
        JOIN students s ON s.id = r.student_id
        WHERE r.course_id=?
        ORDER BY s.id
    """, (course_id,)).fetchall()
    return [{"id": r[0], "name": r[1], "age": r[2], "email": r[3]} for r in rows]

def search_all(q: str) -> Dict[str, List[Dict]]:
    q = f"%{q.lower().strip()}%"
    conn = connect()
    srows = conn.execute("""
        SELECT id, name, age, email FROM students
        WHERE lower(id) LIKE ? OR lower(name) LIKE ? OR lower(email) LIKE ?
        ORDER BY id
    """, (q, q, q)).fetchall()
    irows = conn.execute("""
        SELECT id, name, age, email FROM instructors
        WHERE lower(id) LIKE ? OR lower(name) LIKE ? OR lower(email) LIKE ?
        ORDER BY id
    """, (q, q, q)).fetchall()
    crows = conn.execute("""
        SELECT c.id, c.name, c.instructor_id, i.name
        FROM courses c LEFT JOIN instructors i ON i.id = c.instructor_id
        WHERE lower(c.id) LIKE ? OR lower(c.name) LIKE ?
        ORDER BY c.id
    """, (q, q)).fetchall()

    res = {
        "students": [{"id": r[0], "name": r[1], "age": r[2], "email": r[3]} for r in srows],
        "instructors": [{"id": r[0], "name": r[1], "age": r[2], "email": r[3]} for r in irows],
        "courses": []
    }
    for cid, cname, inst_id, inst_name in crows:
        n = conn.execute("SELECT COUNT(*) FROM registrations WHERE course_id=?", (cid,)).fetchone()[0]
        res["courses"].append({
            "id": cid, "name": cname,
            "instructor_id": inst_id,
            "instructor_name": inst_name if inst_name else None,
            "enrolled_count": n
        })
    return res

def backup_to(path: str):
    conn = connect()
    conn.commit()
    shutil.copyfile(_DB_PATH, path)

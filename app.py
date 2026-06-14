import csv
import io
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "school.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-change-me")


# ---------------- DB ----------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                section TEXT,
                gender TEXT,
                date_of_birth TEXT,
                email TEXT,
                phone TEXT,
                guardian_name TEXT,
                address TEXT,
                pin TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('Present', 'Absent', 'Late')),
                remarks TEXT,
                UNIQUE (student_id, date),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            """
        )


init_db()


# ---------------- Helpers ----------------

def today_iso():
    return date.today().isoformat()


def days_ago_iso(n):
    return (date.today() - timedelta(days=n)).isoformat()


def fetch_classes():
    db = get_db()
    rows = db.execute("SELECT DISTINCT class_name FROM students ORDER BY class_name").fetchall()
    return [r["class_name"] for r in rows]


def fetch_student_by_id(sid):
    return get_db().execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()


def fetch_student_by_roll(roll):
    return get_db().execute("SELECT * FROM students WHERE roll_no=?", (roll,)).fetchone()


def require_teacher():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    return None


def require_student():
    if session.get("role") != "student" or not session.get("student_id"):
        return redirect(url_for("login"))
    return None


@app.context_processor
def inject_user():
    student = None
    if session.get("role") == "student" and session.get("student_id"):
        student = fetch_student_by_id(session["student_id"])
    return {"current_role": session.get("role"), "current_student": student}


# ---------------- Auth ----------------

@app.route("/", methods=["GET"])
def root():
    role = session.get("role")
    if role == "teacher":
        return redirect(url_for("dashboard"))
    if role == "student":
        return redirect(url_for("profile"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    selected = request.values.get("role", "teacher")
    error = None
    if request.method == "POST":
        chosen = request.form.get("role")
        if chosen == "teacher":
            session.clear()
            session["role"] = "teacher"
            return redirect(url_for("dashboard"))
        if chosen == "student":
            roll = (request.form.get("roll_no") or "").strip()
            pin = (request.form.get("pin") or "").strip()
            if not roll:
                error = "Please enter your Roll No."
                selected = "student"
            else:
                student = fetch_student_by_roll(roll)
                if not student:
                    error = "No student found with this Roll No. Please ask your teacher to add you first."
                    selected = "student"
                else:
                    stored = (student["pin"] or "").strip()
                    if stored and pin != stored:
                        error = "Incorrect PIN. Please try again."
                        selected = "student"
                    elif not stored and pin:
                        error = "No PIN has been set for you yet. Leave the PIN field blank or ask your teacher."
                        selected = "student"
                    else:
                        session.clear()
                        session["role"] = "student"
                        session["student_id"] = student["id"]
                        return redirect(url_for("profile"))
    return render_template("login.html", selected=selected, error=error)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- Teacher: Dashboard ----------------

@app.route("/dashboard")
def dashboard():
    redir = require_teacher()
    if redir:
        return redir
    db = get_db()
    total_students = db.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    total_classes = db.execute("SELECT COUNT(DISTINCT class_name) c FROM students").fetchone()["c"]
    today = today_iso()
    counts = db.execute(
        """SELECT
              SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) p,
              SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) a,
              SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END) l
           FROM attendance WHERE date=?""",
        (today,),
    ).fetchone()
    present_today = counts["p"] or 0
    absent_today = counts["a"] or 0
    late_today = counts["l"] or 0

    start = days_ago_iso(6)
    trend_rows = db.execute(
        """SELECT date,
                  SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) p,
                  SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) a,
                  SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END) l
           FROM attendance WHERE date BETWEEN ? AND ?
           GROUP BY date ORDER BY date""",
        (start, today),
    ).fetchall()
    trend_map = {r["date"]: r for r in trend_rows}

    days = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        r = trend_map.get(d)
        p = (r["p"] if r else 0) or 0
        a = (r["a"] if r else 0) or 0
        l = (r["l"] if r else 0) or 0
        days.append({"date": d, "present": p, "absent": a, "late": l, "total": p + a + l})
    trend_max = max([d["total"] for d in days] + [1])

    dist_rows = db.execute(
        "SELECT class_name, COUNT(*) c FROM students GROUP BY class_name ORDER BY class_name"
    ).fetchall()
    dist = [{"class_name": r["class_name"], "count": r["c"]} for r in dist_rows]
    dist_max = max([d["count"] for d in dist] + [1])

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_classes=total_classes,
        present_today=present_today,
        absent_today=absent_today,
        late_today=late_today,
        days=days,
        trend_max=trend_max,
        dist=dist,
        dist_max=dist_max,
    )


# ---------------- Teacher: Students ----------------

@app.route("/students")
def students_list():
    redir = require_teacher()
    if redir:
        return redir
    db = get_db()
    class_filter = request.args.get("class", "All")
    search = (request.args.get("q") or "").strip()
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if class_filter and class_filter != "All":
        query += " AND class_name = ?"
        params.append(class_filter)
    if search:
        query += " AND (name LIKE ? OR roll_no LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    query += " ORDER BY class_name, roll_no"
    students = db.execute(query, params).fetchall()
    return render_template(
        "students_list.html",
        students=students,
        classes=fetch_classes(),
        class_filter=class_filter,
        search=search,
    )


@app.route("/students/add", methods=["GET", "POST"])
def students_add():
    redir = require_teacher()
    if redir:
        return redir
    if request.method == "POST":
        f = request.form
        roll_no = (f.get("roll_no") or "").strip()
        name = (f.get("name") or "").strip()
        class_name = (f.get("class_name") or "").strip()
        pin = (f.get("pin") or "").strip()
        if not roll_no or not name or not class_name:
            flash("Roll No, Name and Class are required.", "error")
        elif not pin:
            flash("Please set a Login PIN for the student.", "error")
        else:
            try:
                db = get_db()
                db.execute(
                    """INSERT INTO students
                       (roll_no, name, class_name, section, gender, date_of_birth,
                        email, phone, guardian_name, address, pin)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        roll_no,
                        name,
                        class_name,
                        (f.get("section") or "").strip(),
                        f.get("gender") or "Male",
                        f.get("date_of_birth") or "",
                        (f.get("email") or "").strip(),
                        (f.get("phone") or "").strip(),
                        (f.get("guardian_name") or "").strip(),
                        (f.get("address") or "").strip(),
                        pin,
                    ),
                )
                db.commit()
                flash(
                    f"Student '{name}' added. They can now log in with Roll No '{roll_no}' and the PIN you set.",
                    "success",
                )
                return redirect(url_for("students_list"))
            except sqlite3.IntegrityError:
                flash("A student with this Roll No already exists.", "error")
    return render_template("students_add.html")


@app.route("/students/<int:sid>/edit", methods=["GET", "POST"])
def students_edit(sid):
    redir = require_teacher()
    if redir:
        return redir
    student = fetch_student_by_id(sid)
    if not student:
        abort(404)
    if request.method == "POST":
        f = request.form
        roll_no = (f.get("roll_no") or "").strip()
        name = (f.get("name") or "").strip()
        class_name = (f.get("class_name") or "").strip()
        if not roll_no or not name or not class_name:
            flash("Roll No, Name and Class are required.", "error")
        else:
            try:
                db = get_db()
                db.execute(
                    """UPDATE students SET
                        roll_no=?, name=?, class_name=?, section=?, gender=?,
                        date_of_birth=?, email=?, phone=?, guardian_name=?,
                        address=?, pin=?
                       WHERE id=?""",
                    (
                        roll_no,
                        name,
                        class_name,
                        (f.get("section") or "").strip(),
                        f.get("gender") or "Male",
                        f.get("date_of_birth") or "",
                        (f.get("email") or "").strip(),
                        (f.get("phone") or "").strip(),
                        (f.get("guardian_name") or "").strip(),
                        (f.get("address") or "").strip(),
                        (f.get("pin") or "").strip() or None,
                        sid,
                    ),
                )
                db.commit()
                flash("Student updated.", "success")
                return redirect(url_for("students_list"))
            except sqlite3.IntegrityError:
                flash("Roll No must be unique.", "error")
        student = dict(student)
        student.update({k: v for k, v in f.items()})
    return render_template("students_edit.html", student=student)


@app.route("/students/<int:sid>/delete", methods=["POST"])
def students_delete(sid):
    redir = require_teacher()
    if redir:
        return redir
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (sid,))
    db.commit()
    flash("Student deleted.", "success")
    return redirect(url_for("students_list"))


# ---------------- Teacher: Attendance ----------------

@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    redir = require_teacher()
    if redir:
        return redir
    att_date = request.values.get("date") or today_iso()
    att_class = request.values.get("class", "All")

    db = get_db()
    if request.method == "POST":
        action = request.form.get("action", "save")
        student_ids = request.form.getlist("student_id")
        if action in ("present_all", "absent_all"):
            forced = "Present" if action == "present_all" else "Absent"
            for sid in student_ids:
                remarks = request.form.get(f"remarks_{sid}", "")
                db.execute(
                    """INSERT INTO attendance (student_id, date, status, remarks)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(student_id, date) DO UPDATE SET
                       status=excluded.status, remarks=excluded.remarks""",
                    (int(sid), att_date, forced, remarks),
                )
            db.commit()
            flash(f"Marked all as {forced}.", "success")
        else:
            saved = 0
            for sid in student_ids:
                status = request.form.get(f"status_{sid}", "Not Marked")
                remarks = request.form.get(f"remarks_{sid}", "")
                if status in ("Present", "Absent", "Late"):
                    db.execute(
                        """INSERT INTO attendance (student_id, date, status, remarks)
                           VALUES (?, ?, ?, ?)
                           ON CONFLICT(student_id, date) DO UPDATE SET
                           status=excluded.status, remarks=excluded.remarks""",
                        (int(sid), att_date, status, remarks),
                    )
                    saved += 1
            db.commit()
            flash(f"Saved attendance for {saved} student(s).", "success")
        return redirect(url_for("attendance", date=att_date, **({"class": att_class} if att_class != "All" else {})))

    query = """
        SELECT s.id, s.roll_no, s.name, s.class_name, s.section,
               COALESCE(a.status, 'Not Marked') AS status,
               COALESCE(a.remarks, '') AS remarks
        FROM students s
        LEFT JOIN attendance a ON a.student_id = s.id AND a.date = ?
        WHERE 1=1
    """
    params = [att_date]
    if att_class != "All":
        query += " AND s.class_name = ?"
        params.append(att_class)
    query += " ORDER BY s.class_name, s.roll_no"
    rows = db.execute(query, params).fetchall()

    return render_template(
        "attendance.html",
        rows=rows,
        att_date=att_date,
        att_class=att_class,
        classes=fetch_classes(),
        today=today_iso(),
    )


# ---------------- Teacher: Reports ----------------

def summary_query(start, end, class_name):
    db = get_db()
    query = """
        SELECT s.id, s.roll_no, s.name, s.class_name, s.section,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) present,
               SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) absent,
               SUM(CASE WHEN a.status='Late' THEN 1 ELSE 0 END) late,
               COUNT(a.id) total
        FROM students s
        LEFT JOIN attendance a ON a.student_id=s.id AND a.date BETWEEN ? AND ?
        WHERE 1=1
    """
    params = [start, end]
    if class_name and class_name != "All":
        query += " AND s.class_name=?"
        params.append(class_name)
    query += " GROUP BY s.id ORDER BY s.class_name, s.roll_no"
    out = []
    for r in db.execute(query, params).fetchall():
        present = r["present"] or 0
        total = r["total"] or 0
        pct = round((present / total) * 100, 1) if total else 0.0
        out.append({
            "id": r["id"], "roll_no": r["roll_no"], "name": r["name"],
            "class_name": r["class_name"], "section": r["section"],
            "present": present, "absent": r["absent"] or 0,
            "late": r["late"] or 0, "total": total, "pct": pct,
        })
    return out


@app.route("/reports")
def reports():
    redir = require_teacher()
    if redir:
        return redir
    start = request.args.get("from") or days_ago_iso(30)
    end = request.args.get("to") or today_iso()
    class_name = request.args.get("class", "All")
    rows = summary_query(start, end, class_name)
    return render_template(
        "reports_summary.html",
        rows=rows, start=start, end=end, class_name=class_name,
        classes=fetch_classes(),
    )


@app.route("/reports/csv")
def reports_csv():
    redir = require_teacher()
    if redir:
        return redir
    start = request.args.get("from") or days_ago_iso(30)
    end = request.args.get("to") or today_iso()
    class_name = request.args.get("class", "All")
    rows = summary_query(start, end, class_name)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Roll No", "Name", "Class", "Section", "Present", "Absent", "Late", "Total Marked", "Attendance %"])
    for r in rows:
        w.writerow([
            r["roll_no"], r["name"], r["class_name"], r["section"] or "",
            r["present"], r["absent"], r["late"], r["total"], f"{r['pct']}%",
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_{start}_{end}.csv"},
    )


@app.route("/reports/history")
def reports_history():
    redir = require_teacher()
    if redir:
        return redir
    db = get_db()
    students = db.execute("SELECT id, roll_no, name, class_name FROM students ORDER BY class_name, roll_no").fetchall()
    sid = request.args.get("student_id", type=int)
    start = request.args.get("from") or days_ago_iso(30)
    end = request.args.get("to") or today_iso()
    history = []
    metrics = None
    if sid:
        history = db.execute(
            "SELECT date, status, remarks FROM attendance WHERE student_id=? AND date BETWEEN ? AND ? ORDER BY date DESC",
            (sid, start, end),
        ).fetchall()
        total = len(history)
        present = sum(1 for h in history if h["status"] == "Present")
        absent = sum(1 for h in history if h["status"] == "Absent")
        late = sum(1 for h in history if h["status"] == "Late")
        pct = round((present / total) * 100, 1) if total else 0.0
        metrics = {"total": total, "present": present, "absent": absent, "late": late, "pct": pct}
    return render_template(
        "reports_history.html",
        students=students, sid=sid, start=start, end=end,
        history=history, metrics=metrics,
    )


# ---------------- Student ----------------

@app.route("/profile")
def profile():
    redir = require_student()
    if redir:
        return redir
    student = fetch_student_by_id(session["student_id"])
    if not student:
        session.clear()
        return redirect(url_for("login"))
    return render_template("profile.html", student=student)


@app.route("/my-attendance")
def my_attendance():
    redir = require_student()
    if redir:
        return redir
    student = fetch_student_by_id(session["student_id"])
    if not student:
        session.clear()
        return redirect(url_for("login"))
    start = request.args.get("from") or days_ago_iso(30)
    end = request.args.get("to") or today_iso()
    db = get_db()
    history = db.execute(
        "SELECT date, status, remarks FROM attendance WHERE student_id=? AND date BETWEEN ? AND ? ORDER BY date DESC",
        (student["id"], start, end),
    ).fetchall()
    total = len(history)
    present = sum(1 for h in history if h["status"] == "Present")
    absent = sum(1 for h in history if h["status"] == "Absent")
    late = sum(1 for h in history if h["status"] == "Late")
    pct = round((present / total) * 100, 1) if total else 0.0
    metrics = {"total": total, "present": present, "absent": absent, "late": late, "pct": pct}
    return render_template(
        "my_attendance.html",
        student=student, start=start, end=end, history=history, metrics=metrics,
    )


@app.route("/my-attendance/csv")
def my_attendance_csv():
    redir = require_student()
    if redir:
        return redir
    student = fetch_student_by_id(session["student_id"])
    if not student:
        return redirect(url_for("login"))
    start = request.args.get("from") or days_ago_iso(30)
    end = request.args.get("to") or today_iso()
    db = get_db()
    history = db.execute(
        "SELECT date, status, remarks FROM attendance WHERE student_id=? AND date BETWEEN ? AND ? ORDER BY date DESC",
        (student["id"], start, end),
    ).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Roll No", "Name", "Class", "Date", "Status", "Remarks"])
    for h in history:
        w.writerow([student["roll_no"], student["name"], student["class_name"], h["date"], h["status"], h["remarks"] or ""])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_{student['roll_no']}_{start}_{end}.csv"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

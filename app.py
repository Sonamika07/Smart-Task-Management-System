
from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import csv
import io
from datetime import datetime, date

app = Flask(__name__)
DB_NAME = "tasks.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            created_at TEXT,
            due_date TEXT
        )
    """)

    columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    ]

    if "due_date" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")

    conn.commit()
    conn.close()


@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")

    conn = get_db()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if status in ["Pending", "In Progress", "Completed"]:
        query += " AND status=?"
        params.append(status)

    if priority in ["Low", "Medium", "High"]:
        query += " AND priority=?"
        params.append(priority)

    query += " ORDER BY id DESC"

    tasks = conn.execute(query, params).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    completed = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='Completed'"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='Pending'"
    ).fetchone()[0]

    progress = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='In Progress'"
    ).fetchone()[0]

    high = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE priority='High'"
    ).fetchone()[0]

    medium = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE priority='Medium'"
    ).fetchone()[0]

    low = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE priority='Low'"
    ).fetchone()[0]

    overdue = conn.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE due_date IS NOT NULL
        AND due_date != ''
        AND due_date < ?
        AND status != 'Completed'
    """, (date.today().isoformat(),)).fetchone()[0]

    conn.close()

    completion_rate = round(
        completed / total * 100, 1
    ) if total else 0

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        progress=progress,
        high=high,
        medium=medium,
        low=low,
        overdue=overdue,
        completion_rate=completion_rate,
        search=search,
        selected_status=status,
        selected_priority=priority,
        today=date.today().isoformat()
    )


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium")
    due_date = request.form.get("due_date", "").strip()

    if title and priority in ["Low", "Medium", "High"]:
        conn = get_db()

        conn.execute("""
            INSERT INTO tasks
            (title, description, priority, status, created_at, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            priority,
            "Pending",
            datetime.now().strftime("%d-%m-%Y %H:%M"),
            due_date if due_date else None
        ))

        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.route("/update/<int:task_id>", methods=["POST"])
def update_task(task_id):
    status = request.form.get("status")
    priority = request.form.get("priority")

    if status in ["Pending", "In Progress", "Completed"] and \
       priority in ["Low", "Medium", "High"]:

        conn = get_db()
        conn.execute("""
            UPDATE tasks
            SET status=?, priority=?
            WHERE id=?
        """, (status, priority, task_id))

        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    conn = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        due_date = request.form.get("due_date", "").strip()

        if title and priority in ["Low", "Medium", "High"]:
            conn.execute("""
                UPDATE tasks
                SET title=?, description=?, priority=?, due_date=?
                WHERE id=?
            """, (
                title,
                description,
                priority,
                due_date if due_date else None,
                task_id
            ))

            conn.commit()

        conn.close()
        return redirect(url_for("index"))

    task = conn.execute(
        "SELECT * FROM tasks WHERE id=?",
        (task_id,)
    ).fetchone()

    conn.close()

    if task is None:
        return redirect(url_for("index"))

    return render_template("edit.html", task=task)


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db()

    conn.execute(
        "DELETE FROM tasks WHERE id=?",
        (task_id,)
    )

    conn.commit()
    overdue = conn.execute("""
    SELECT COUNT(*) FROM tasks
    WHERE due_date IS NOT NULL
    AND due_date != ''
    AND due_date < ?
    AND status != 'Completed'
""", (date.today().isoformat(),)).fetchone()[0]
    conn.close()

    return redirect(url_for("index"))


@app.route("/export")
def export_tasks():
    conn = get_db()
    tasks = conn.execute(
        "SELECT * FROM tasks ORDER BY id DESC"
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Title", "Description",
        "Priority", "Status", "Created At", "Due Date"
    ])

    for task in tasks:
        writer.writerow([
            task["id"],
            task["title"],
            task["description"],
            task["priority"],
            task["status"],
            task["created_at"],
            task["due_date"]
        ])

    memory_file = io.BytesIO(
        output.getvalue().encode("utf-8-sig")
    )
    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype="text/csv",
        as_attachment=True,
        download_name="TaskFlow_Report.csv"
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)


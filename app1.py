from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "tushar123"
DATABASE = 'ask.db'

FACULTY_CREDENTIALS = {
    "faculty1@gmail.com": "password123",
    "faculty2@gmail.com": "pass456"
}

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/faculty/login", methods=["GET", "POST"])
def faculty_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email in FACULTY_CREDENTIALS and FACULTY_CREDENTIALS[email] == password:
            session['faculty_email'] = email
            return redirect(url_for("faculty_dashboard"))
        else:
            error = "Invalid email or password."
            return render_template("faculty_login.html", error=error)

    return render_template("faculty_login.html", error="")

@app.route("/faculty/dashboard")
def faculty_dashboard():
    if 'faculty_email' not in session:
        return redirect(url_for("faculty_login"))
    return render_template("faculty_dashboard.html")


@app.route("/questions")
def questions():
    conn = get_db_connection()
    questions = conn.execute("SELECT rowid, * FROM question").fetchall()
    conn.close()
    return render_template("questions.html", questions=questions)

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")


@app.route("/api/questions", methods=["POST"])
def add_question():
    data = request.get_json()
    title = data.get("title")
    detail = data.get("detail")
    if not title or not detail:
        return jsonify({"success": False, "error": "Title and detail are required"}), 400
    conn = get_db_connection()
    conn.execute("INSERT INTO question (title, detail, likes) VALUES (?, ?, 0)", (title, detail))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 201

@app.route("/api/questions/<int:question_id>/like", methods=["PATCH"])
def like_question(question_id):
    conn = get_db_connection()
    conn.execute("UPDATE question SET likes = likes + 1 WHERE rowid = ?", (question_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 200

@app.route("/api/questions/<int:question_id>/answers", methods=["GET"])
def get_answers(question_id):
    conn = get_db_connection()
    answers = conn.execute("SELECT * FROM answer WHERE question_id = ?", (question_id,)).fetchall()
    conn.close()
    return jsonify([dict(ans) for ans in answers])

@app.route("/api/questions/<int:question_id>/answers", methods=["POST"])
def add_answer(question_id):
    data = request.get_json()
    user_id = data.get("user_id")
    ans = data.get("ans")
    if not user_id or not ans:
        return jsonify({"success": False, "error": "User ID and answer are required"}), 400
    conn = get_db_connection()
    conn.execute("INSERT INTO answer (question_id, user_id, ans) VALUES (?, ?, ?)", (question_id, user_id, ans))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 201

if __name__ == "__main__":
    app.run(debug=True)

import sqlite3
import click
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from functools import wraps

# ------------------ APP CONFIG ------------------

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['DATABASE'] = os.path.join(BASE_DIR, 'feedback.db')

# ------------------ DATABASE ------------------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def ensure_db():
    """Create database automatically on first run (Render free-tier fix)"""
    if not os.path.exists(app.config['DATABASE']):
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.executescript(f.read())
        db.commit()

# ------------------ QUESTIONS ------------------

FEEDBACK_QUESTIONS = {
    'q1': 'Knowledge of the subject.',
    'q2': 'Clarity in explanations.',
    'q3': 'Punctuality in classes.',
    'q4': 'Use of teaching aids.',
    'q5': 'Encouragement of student participation.',
    'q6': 'Relating theory to practical examples.',
    'q7': 'Communication skills.',
    'q8': 'Fairness and respect.',
    'q9': 'Timely feedback.',
    'q10': 'Overall effectiveness.'
}

# ------------------ AUTH DECORATOR ------------------

def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapped
    return decorator

# ------------------ ROUTES ------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    ensure_db()  # 🔥 THIS FIXES THE 500 ERROR

    if request.method == 'POST':
        login_type = request.form.get('login_type')
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()

        if login_type == 'student':
            user = db.execute(
                'SELECT * FROM students WHERE id = ? AND password = ?',
                (username, password)
            ).fetchone()

            if user:
                session['user_id'] = user['id']
                session['name'] = user['name']
                session['class'] = user['class']
                session['role'] = 'student'
                return redirect(url_for('feedback'))

        if login_type == 'faculty':
            user = db.execute(
                'SELECT * FROM faculty WHERE id = ? AND password = ?',
                (username, password)
            ).fetchone()

            if user:
                session['user_id'] = user['id']
                session['name'] = user['name']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))

        flash('Invalid credentials')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/feedback', methods=['GET', 'POST'])
@login_required(role='student')
def feedback():
    db = get_db()
    student_id = session['user_id']

    if request.method == 'POST':
        teacher_id = request.form.get('teacher')
        comments = request.form.get('comments', '')

        existing = db.execute(
            'SELECT id FROM feedback WHERE student_id=? AND teacher_id=?',
            (student_id, teacher_id)
        ).fetchone()

        if existing:
            flash('Feedback already submitted')
            return redirect(url_for('feedback'))

        ratings = [request.form.get(q) for q in FEEDBACK_QUESTIONS]

        db.execute(
            '''INSERT INTO feedback
               (student_id, teacher_id, semester,
                q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,comments)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (student_id, teacher_id, 'Fall 2024', *ratings, comments)
        )
        db.commit()

        flash('Feedback submitted successfully')
        return redirect(url_for('feedback'))

    teachers = db.execute('SELECT * FROM teachers').fetchall()
    return render_template('index.html', teachers=teachers, questions=FEEDBACK_QUESTIONS)

@app.route('/dashboard')
@login_required()
def dashboard():
    if session['role'] == 'student':
        return redirect(url_for('feedback'))

    db = get_db()
    teachers = db.execute('SELECT * FROM teachers').fetchall()
    data = {}

    for t in teachers:
        rows = db.execute(
            'SELECT * FROM feedback WHERE teacher_id=?',
            (t['id'],)
        ).fetchall()

        if not rows:
            continue

        avg = {}
        for q in FEEDBACK_QUESTIONS:
            avg[q] = sum(r[q] for r in rows) / len(rows)

        data[t['id']] = {
            'name': t['name'],
            'responses': len(rows),
            'avg': avg
        }

    return render_template('dashboard.html', data=data, questions=FEEDBACK_QUESTIONS)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------ RENDER ENTRYPOINT ------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

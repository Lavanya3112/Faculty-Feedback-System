import sqlite3
import click
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_very_secret_key'
app.config['DATABASE'] = 'feedback.db'

# --- Database Setup ---

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

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('init-db')
def init_db_command():
    """Clears the existing data and creates new tables."""
    init_db()
    click.echo('Initialized the database.')

# --- Feedback Questions ---

FEEDBACK_QUESTIONS = {
    'q1': 'Knowledge of the subject.',
    'q2': 'Clarity in explanations.',
    'q3': 'Punctuality in classes.',
    'q4': 'Use of teaching aids (PowerPoint, board, labs, etc.).',
    'q5': 'Encouragement of student participation.',
    'q6': 'Ability to relate theory to practical examples.',
    'q7': 'Communication skills (clarity, audibility, language).',
    'q8': 'Fairness and respect towards students.',
    'q9': 'Timeliness of feedback on assignments/tests.',
    'q10': 'Overall teaching effectiveness.'
}

# --- Decorators for access control ---

def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'danger')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return decorated_view
    return decorator

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        
        user = None
        if login_type == 'student':
            user = db.execute('SELECT * FROM students WHERE id = ?', (username,)).fetchone()
            if user and user['password'] == password:
                session['user_id'] = user['id']
                session['name'] = user['name']
                session['class'] = user['class']
                session['role'] = 'student'
                return redirect(url_for('feedback'))
        elif login_type == 'faculty':
            user = db.execute('SELECT * FROM faculty WHERE id = ?', (username,)).fetchone()
            if user and user['password'] == password:
                session['user_id'] = user['id']
                session['name'] = user['name']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))

        flash('Invalid credentials. Please try again.', 'danger')
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
        
        existing_feedback = db.execute(
            'SELECT id FROM feedback WHERE student_id = ? AND teacher_id = ? AND semester = ?',
            (student_id, teacher_id, 'Fall 2024')
        ).fetchone()

        if existing_feedback:
            flash('You have already submitted feedback for this teacher.', 'danger')
            return redirect(url_for('feedback'))

        ratings = {q_id: request.form.get(q_id) for q_id in FEEDBACK_QUESTIONS}
        
        db.execute(
            'INSERT INTO feedback (student_id, teacher_id, semester, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, comments) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (student_id, teacher_id, 'Fall 2024', ratings['q1'], ratings['q2'], ratings['q3'], ratings['q4'], ratings['q5'], ratings['q6'], ratings['q7'], ratings['q8'], ratings['q9'], ratings['q10'], comments)
        )
        db.commit()
        flash('Thank you for your valuable feedback!', 'success')
        return redirect(url_for('feedback'))

    submitted_teachers_query = db.execute(
        'SELECT teacher_id FROM feedback WHERE student_id = ? AND semester = ?',
        (student_id, 'Fall 2024')
    ).fetchall()
    submitted_teacher_ids = [row['teacher_id'] for row in submitted_teachers_query]

    teachers_query = db.execute('SELECT * FROM teachers').fetchall()
    available_teachers = [teacher for teacher in teachers_query if teacher['id'] not in submitted_teacher_ids]

    return render_template('feedback.html', teachers=available_teachers, questions=FEEDBACK_QUESTIONS)


@app.route('/dashboard')
@login_required()
def dashboard():
    if session['role'] == 'student':
        return redirect(url_for('feedback'))
    
    db = get_db()
    teachers = db.execute('SELECT * FROM teachers').fetchall()
    teacher_averages = {}

    for teacher in teachers:
        feedback_details = db.execute(
            """
            SELECT f.*, s.name as student_name 
            FROM feedback f JOIN students s ON f.student_id = s.id 
            WHERE f.teacher_id = ?
            """, (teacher['id'],)
        ).fetchall()
        
        if not feedback_details:
            continue

        num_responses = len(feedback_details)
        avg_ratings = {q_id: 0 for q_id in FEEDBACK_QUESTIONS}
        
        for q_id in FEEDBACK_QUESTIONS:
            total_rating = sum(row[q_id] for row in feedback_details if row[q_id] is not None)
            avg_ratings[q_id] = total_rating / num_responses if num_responses > 0 else 0
        
        overall_avg = sum(avg_ratings.values()) / len(avg_ratings) if avg_ratings else 0

        teacher_averages[teacher['id']] = {
            'name': teacher['name'],
            'num_responses': num_responses,
            'avg_ratings': avg_ratings,
            'overall_avg': overall_avg,
            'feedback_details': feedback_details
        }

    return render_template('dashboard.html', teacher_data=teacher_averages, questions=FEEDBACK_QUESTIONS)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
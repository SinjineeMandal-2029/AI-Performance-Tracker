"""
EduTrack AI — Flask Backend
Run: python app.py
API Base: http://localhost:5000
"""

from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
import mysql.connector
import bcrypt
import os
from datetime import timedelta
from ai_predictor import predict_performance, get_study_suggestions

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')
app.permanent_session_lifetime = timedelta(days=7)
CORS(app, supports_credentials=True)

# ── DATABASE CONFIG ──────────────────────────────────────────────────────────
# Values come from environment variables (set them on Render).
# Locally, if nothing is set, it falls back to your local MySQL.
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'edutrack_db'),
    'charset': 'utf8mb4'
}

def get_db():
    """Get a database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def db_query(query, params=None, fetch=True):
    """Execute a query and return results."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        return result
    finally:
        cursor.close()
        conn.close()

# ── HELPERS ──────────────────────────────────────────────────────────────────
def require_auth(roles=None):
    """Check if user is logged in and optionally verify role."""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            if roles and session.get('role') not in roles:
                return jsonify({'success': False, 'message': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ── PAGE ROUTES ──────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student')
def student_page():
    return render_template('student_dashboard.html')

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role     = data.get('role', '')

    if not all([name, email, password, role]):
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400
    if role not in ('student', 'teacher', 'parent', 'admin'):
        return jsonify({'success': False, 'message': 'Invalid role.'}), 400
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters.'}), 400

    # Check if email exists
    existing = db_query("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return jsonify({'success': False, 'message': 'An account with this email already exists.'}), 409

    # Hash password
    pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Insert user
    user_id = db_query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (name, email, pwd_hash, role), fetch=False
    )

    # Create role-specific record
    if role == 'student':
        student_id = f"CS{2021}{user_id:04d}"
        db_query(
            "INSERT INTO students (user_id, student_id, semester, department) VALUES (%s, %s, 1, 'General')",
            (user_id, student_id), fetch=False
        )
    elif role == 'teacher':
        emp_id = f"EMP{user_id:04d}"
        db_query(
            "INSERT INTO teachers (user_id, employee_id, department) VALUES (%s, %s, 'General')",
            (user_id, emp_id), fetch=False
        )

    return jsonify({'success': True, 'message': 'Account created successfully!'})


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role     = data.get('role', '')

    users = db_query("SELECT * FROM users WHERE email = %s AND role = %s", (email, role))
    if not users:
        return jsonify({'success': False, 'message': 'Invalid credentials or role mismatch.'}), 401

    user = users[0]
    if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

    session.permanent = True
    session['user_id'] = user['id']
    session['role']    = user['role']
    session['name']    = user['name']
    session['email']   = user['email']

    return jsonify({'success': True, 'role': user['role'], 'name': user['name']})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/auth/me', methods=['GET'])
@require_auth()
def me():
    return jsonify({
        'success': True,
        'user_id': session['user_id'],
        'role': session['role'],
        'name': session['name'],
        'email': session['email']
    })


# ── STUDENT ROUTES ────────────────────────────────────────────────────────────
@app.route('/api/student/dashboard', methods=['GET'])
@require_auth(['student'])
def student_dashboard():
    try:
        user_id = session['user_id']

        # Get student record
        student = db_query(
            "SELECT * FROM students WHERE user_id = %s",
            (user_id,)
        )

        if not student:
            return jsonify({
                'success': False,
                'message': 'Student record not found.'
            }), 404

        student = student[0]
        sid = student['id']

        # Get grades
        grades = db_query("""
            SELECT s.name AS subject,
                   g.exam_type,
                   g.marks_obtained,
                   g.max_marks,
                   g.date
            FROM grades g
            JOIN subjects s ON g.subject_id = s.id
            WHERE g.student_id = %s
            ORDER BY g.date DESC
        """, (sid,))

        # Attendance
        attend = db_query("""
            SELECT s.name AS subject,
                   COUNT(*) AS total,
                   SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS present
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.student_id = %s
            GROUP BY s.name
        """, (sid,))

        # Assignments
        pending = db_query("""
            SELECT a.title,
                   s.name AS subject,
                   a.due_date,
                   COALESCE(sub.status, 'pending') AS status
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            LEFT JOIN submissions sub
                ON sub.assignment_id = a.id
                AND sub.student_id = %s
            WHERE s.id IN (
                SELECT subject_id
                FROM enrollments
                WHERE student_id = %s
            )
            ORDER BY a.due_date ASC
        """, (sid, sid))

        # ===== SAFE GPA =====
        if grades:
            scores = []
            for g in grades:
                if g['max_marks']:
                    score = (float(g['marks_obtained']) / float(g['max_marks'])) * 100
                    scores.append(score)

            avg = sum(scores) / len(scores) if scores else 0
            gpa = round((avg / 100) * 10, 1)
        else:
            gpa = 0.0

        # ===== SAFE ATTENDANCE =====
        total_attend = sum(a['total'] for a in attend) if attend else 0
        present_attend = sum(a['present'] for a in attend) if attend else 0
        attend_pct = round((present_attend / total_attend) * 100) if total_attend else 0

        # ===== SAFE AI =====
        try:
            predictions = predict_performance(sid, grades, attend)
            if not isinstance(predictions, dict):
                predictions = {
                    "predicted_gpa": gpa,
                    "confidence": 85
                }
        except Exception as e:
            print("Prediction error:", e)
            predictions = {
                "predicted_gpa": gpa,
                "confidence": 85
            }

        try:
            suggestions = get_study_suggestions(grades, attend)
            if not isinstance(suggestions, list):
                suggestions = [
                    "Focus on weaker subjects",
                    "Maintain regular attendance"
                ]
        except Exception as e:
            print("Suggestion error:", e)
            suggestions = [
                "Focus on weaker subjects",
                "Maintain regular attendance"
            ]

        return jsonify({
            'success': True,
            'student': {
                'name': session['name'],
                'email': session['email'],
                'student_id': student['student_id'],
                'semester': student['semester'],
                'department': student['department']
            },
            'stats': {
                'gpa': gpa,
                'attendance_pct': f"{attend_pct}%",
                'pending_assignments': len(pending)
            },
            'grades': grades,
            'attendance': attend,
            'assignments': pending,
            'predictions': predictions,
            'suggestions': suggestions
        })

    except Exception as e:
        print("STUDENT DASHBOARD ERROR:", e)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    
# ── TEACHER ROUTES ────────────────────────────────────────────────────────────
@app.route('/api/teacher/students', methods=['GET'])
@require_auth(['teacher'])
def teacher_students():
    user_id = session['user_id']
    teacher = db_query("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
    if not teacher:
        return jsonify({'success': False}), 404
    tid = teacher[0]['id']

    students = db_query("""
        SELECT u.name, s.student_id, sub.name AS subject,
               COALESCE(ROUND(AVG(g.marks_obtained/g.max_marks*100),1), 0) AS avg_pct,
               COALESCE(ROUND(
                   SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) /
                   NULLIF(COUNT(a.id),0) * 100
               ,0), 0) AS attend_pct
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN enrollments e ON e.student_id = s.id
        JOIN subjects sub ON sub.id = e.subject_id AND sub.teacher_id = %s
        LEFT JOIN grades g ON g.student_id = s.id AND g.subject_id = sub.id
        LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = sub.id
        GROUP BY s.id, sub.id
    """, (tid,))

    return jsonify({'success': True, 'students': students})


@app.route('/api/teacher/grades', methods=['POST'])
@require_auth(['teacher'])
def add_grade():
    data = request.get_json()
    student_id = data.get('student_id')
    subject_id = data.get('subject_id')
    exam_type  = data.get('exam_type')
    marks      = data.get('marks_obtained')
    max_marks  = data.get('max_marks')
    date       = data.get('date')

    db_query("""
        INSERT INTO grades (student_id, subject_id, exam_type, marks_obtained, max_marks, date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (student_id, subject_id, exam_type, marks, max_marks, date), fetch=False)

    return jsonify({'success': True, 'message': 'Grade added successfully.'})


@app.route('/api/teacher/attendance', methods=['POST'])
@require_auth(['teacher'])
def mark_attendance():
    data = request.get_json()
    records = data.get('records', [])  # [{student_id, subject_id, date, status}]

    for rec in records:
        db_query("""
            INSERT INTO attendance (student_id, subject_id, date, status)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """, (rec['student_id'], rec['subject_id'], rec['date'], rec['status']), fetch=False)

    return jsonify({'success': True, 'message': f'{len(records)} attendance records saved.'})


@app.route('/api/teacher/assignments', methods=['GET', 'POST'])
@require_auth(['teacher'])
def teacher_assignments():
    user_id = session['user_id']
    teacher = db_query("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
    if not teacher:
        return jsonify({'success': False}), 404
    tid = teacher[0]['id']

    if request.method == 'GET':
        assignments = db_query("""
            SELECT a.*, s.name AS subject_name
            FROM assignments a JOIN subjects s ON a.subject_id = s.id
            WHERE s.teacher_id = %s ORDER BY a.due_date ASC
        """, (tid,))
        return jsonify({'success': True, 'assignments': assignments})

    # POST
    data = request.get_json()
    db_query("""
        INSERT INTO assignments (subject_id, title, description, due_date, max_marks)
        VALUES (%s, %s, %s, %s, %s)
    """, (data['subject_id'], data['title'], data.get('description',''), data['due_date'], data['max_marks']), fetch=False)
    return jsonify({'success': True, 'message': 'Assignment posted successfully.'})


# ── PARENT ROUTES ─────────────────────────────────────────────────────────────
@app.route('/api/parent/children', methods=['GET'])
@require_auth(['parent'])
def parent_children():
    user_id = session['user_id']
    children = db_query("""
        SELECT u.name, s.student_id, s.semester, s.department
        FROM parent_student ps
        JOIN users u ON ps.student_user_id = u.id
        JOIN students s ON s.user_id = u.id
        WHERE ps.parent_user_id = %s
    """, (user_id,))
    return jsonify({'success': True, 'children': children})


@app.route('/api/parent/child/<int:student_user_id>', methods=['GET'])
@require_auth(['parent'])
def parent_child_dashboard(student_user_id):
    user_id = session['user_id']

    # Verify parent-child relationship
    rel = db_query(
        "SELECT 1 FROM parent_student WHERE parent_user_id = %s AND student_user_id = %s",
        (user_id, student_user_id)
    )
    if not rel:
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    student = db_query("SELECT * FROM students WHERE user_id = %s", (student_user_id,))
    if not student:
        return jsonify({'success': False}), 404
    sid = student[0]['id']

    grades = db_query("""
        SELECT s.name AS subject, g.exam_type, g.marks_obtained, g.max_marks, g.date
        FROM grades g JOIN subjects s ON g.subject_id = s.id
        WHERE g.student_id = %s ORDER BY g.date DESC LIMIT 20
    """, (sid,))

    attend = db_query("""
        SELECT s.name AS subject,
               COUNT(*) AS total,
               SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) AS present
        FROM attendance a JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id = %s GROUP BY s.name
    """, (sid,))

    predictions = predict_performance(sid, grades, attend)
    suggestions = get_study_suggestions(grades, attend)
    child_user = db_query("SELECT name FROM users WHERE id = %s", (student_user_id,))

    return jsonify({
        'success': True,
        'child': {
            'name': child_user[0]['name'] if child_user else 'N/A',
            'student_id': student[0]['student_id'],
            'semester': student[0]['semester']
        },
        'grades': grades,
        'attendance': attend,
        'predictions': predictions,
        'suggestions': suggestions
    })


# ── ADMIN ROUTES ──────────────────────────────────────────────────────────────
@app.route('/api/admin/users', methods=['GET'])
@require_auth(['admin'])
def admin_users():
    role = request.args.get('role')
    if role:
        users = db_query("SELECT id, name, email, role, created_at FROM users WHERE role = %s ORDER BY created_at DESC", (role,))
    else:
        users = db_query("SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC")
    return jsonify({'success': True, 'users': users})


@app.route('/api/admin/users', methods=['POST'])
@require_auth(['admin'])
def admin_create_user():
    data = request.get_json()
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', 'TempPass123!')
    role     = data.get('role', 'student')

    existing = db_query("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return jsonify({'success': False, 'message': 'Email already exists.'}), 409

    pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = db_query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (name, email, pwd_hash, role), fetch=False
    )
    return jsonify({'success': True, 'user_id': user_id, 'message': 'User created.'})


@app.route('/api/admin/users/<int:uid>', methods=['DELETE'])
@require_auth(['admin'])
def admin_delete_user(uid):
    if uid == session['user_id']:
        return jsonify({'success': False, 'message': 'Cannot delete your own account.'}), 400
    db_query("DELETE FROM users WHERE id = %s", (uid,), fetch=False)
    return jsonify({'success': True, 'message': 'User removed.'})


@app.route('/api/admin/stats', methods=['GET'])
@require_auth(['admin'])
def admin_stats():
    counts = db_query("""
        SELECT role, COUNT(*) AS count
        FROM users GROUP BY role
    """)
    stats = {r['role']: r['count'] for r in counts}
    return jsonify({'success': True, 'stats': stats})


# ── AI ROUTES ─────────────────────────────────────────────────────────────────
@app.route('/api/ai/predict/<int:student_id>', methods=['GET'])
@require_auth(['student', 'teacher', 'parent', 'admin'])
def ai_predict(student_id):
    grades = db_query("""
        SELECT s.name AS subject, g.marks_obtained, g.max_marks, g.exam_type
        FROM grades g JOIN subjects s ON g.subject_id = s.id
        WHERE g.student_id = %s
    """, (student_id,))

    attend = db_query("""
        SELECT s.name AS subject, COUNT(*) AS total,
               SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) AS present
        FROM attendance a JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id = %s GROUP BY s.name
    """, (student_id,))

    predictions = predict_performance(student_id, grades, attend)
    suggestions = get_study_suggestions(grades, attend)

    return jsonify({'success': True, 'predictions': predictions, 'suggestions': suggestions})


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run()
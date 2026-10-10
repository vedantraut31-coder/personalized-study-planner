
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
from pathlib import Path
import os, uuid, json, re, math
from sqlalchemy import or_, cast, String, func

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_FOLDER = INSTANCE_DIR / "uploads"
INSTANCE_DIR.mkdir(exist_ok=True)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "study-planner-r-secret-key-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(INSTANCE_DIR / "study_planner.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

DEFAULT_SUBJECTS = ["Python", "DBMS", "Operating System", "Computer Networks", "Software Engineering"]
TYPE_OPTIONS = ["Theory", "Practical", "Both"]
PRIORITY_LABELS = {1: "Low", 2: "Normal", 3: "Medium", 4: "High", 5: "Critical"}
PRIORITY_SCORE = {"Low": 1, "Medium": 3, "High": 5, "Critical": 7}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    password = db.Column(String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(String(120), nullable=False)
    details = db.Column(String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class UserRecovery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    recovery_answer = db.Column(String(255), nullable=False)

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    college_start = db.Column(String(5), default="09:00")
    college_end = db.Column(String(5), default="16:00")
    gym_start = db.Column(String(5), default="")
    gym_end = db.Column(String(5), default="")
    meditation_start = db.Column(String(5), default="")
    meditation_minutes = db.Column(db.Integer, default=15)
    morning_start = db.Column(String(5), default="06:00")
    morning_end = db.Column(String(5), default="08:30")
    evening_start = db.Column(String(5), default="17:00")
    evening_end = db.Column(String(5), default="22:30")
    max_study_hours = db.Column(db.Float, default=4.0)
    exam_date = db.Column(String(20), default="")
    subjects_json = db.Column(db.Text, default="{}")
    interests = db.Column(db.Text, default="")
    wake_time = db.Column(String(5), default="06:00")
    sleep_time = db.Column(String(5), default="23:00")
    study_days = db.Column(db.Text, default="Mon,Tue,Wed,Thu,Fri,Sat,Sun")
    session_minutes = db.Column(db.Integer, default=45)
    break_minutes = db.Column(db.Integer, default=15)
    preferred_slot = db.Column(String(20), default="Balanced")
    commute_minutes = db.Column(db.Integer, default=0)
    theory_weight = db.Column(db.Integer, default=3)
    practical_weight = db.Column(db.Integer, default=3)
    learning_style = db.Column(String(100), default="Mixed")
    goal = db.Column(String(150), default="Exam preparation")
    target_score = db.Column(db.Integer, default=80)
    hobbies = db.Column(db.Text, default="")
    other_commitments = db.Column(db.Text, default="")

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    subject = db.Column(String(100), nullable=False)
    title = db.Column(String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class PDFNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    subject = db.Column(String(100), nullable=False)
    title = db.Column(String(200), nullable=False)
    filename = db.Column(String(300), nullable=False)
    original_filename = db.Column(String(300), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class PYQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    unit = db.Column(String(50), nullable=False)
    question = db.Column(db.Text, nullable=False)
    marks = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(String(50), nullable=False)

class PYQPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    subject = db.Column(String(100), nullable=False)
    title = db.Column(String(200), nullable=False)
    filename = db.Column(String(300), nullable=False)
    original_filename = db.Column(String(300), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    subject = db.Column(String(100), nullable=False)
    task = db.Column(String(200), nullable=False)
    due_date = db.Column(String(20), nullable=False)
    priority = db.Column(String(50), nullable=False)
    status = db.Column(String(50), default="Pending", nullable=False)

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(String(20), nullable=False)
    day_name = db.Column(String(20), default="")
    subject = db.Column(String(100), nullable=False)
    subject_type = db.Column(String(50), default="Theory")
    priority = db.Column(db.Integer, default=3)
    start_time = db.Column(String(20), nullable=False)
    end_time = db.Column(String(20), nullable=False)
    activity = db.Column(String(150), nullable=False)
    focus_score = db.Column(db.Float, default=0.0)
    block_type = db.Column(String(50), default="Study")
    reason = db.Column(String(255), default="")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def parse_time(value):
    try:
        return datetime.strptime(value, "%H:%M")
    except (TypeError, ValueError):
        return None

def time_to_minutes(value):
    t = parse_time(value)
    return t.hour * 60 + t.minute if t else None

def fmt_minutes(total):
    total %= 24 * 60
    return datetime(2000, 1, 1, total // 60, total % 60).strftime("%I:%M %p")

def overlap(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end

def free_windows(start_s, end_s, fixed):
    start = time_to_minutes(start_s)
    end = time_to_minutes(end_s)
    if start is None or end is None or end <= start:
        return []
    fixed_ranges = []
    for fs, fe, label in fixed:
        a, b = time_to_minutes(fs), time_to_minutes(fe)
        if a is not None and b is not None and b > a and overlap(start, end, a, b):
            fixed_ranges.append((max(start, a), min(end, b), label))
    fixed_ranges.sort()
    windows = []
    cursor = start
    for a, b, _ in fixed_ranges:
        if cursor < a:
            windows.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < end:
        windows.append((cursor, end))
    return windows

def normalize_json(raw):
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}

def allowed_file(filename):
    return bool(filename and "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"])

def save_pdf(file, prefix):
    original = secure_filename(file.filename or "")
    if not original or not allowed_file(original):
        raise ValueError("Only PDF files are allowed.")
    header = file.stream.read(5)
    file.stream.seek(0)
    if header != b"%PDF-":
        raise ValueError("The selected file is not a valid PDF.")
    unique = f"{current_user.id}_{prefix}_{uuid.uuid4().hex}_{original}"
    path = Path(app.config["UPLOAD_FOLDER"]) / unique
    file.save(path)
    return unique, original, path

def get_preferences():
    pref = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.session.add(pref)
        db.session.commit()
    return pref

def log_activity(action, details=""):
    try:
        uid = current_user.id if current_user.is_authenticated else None
    except Exception:
        uid = None
    db.session.add(ActivityLog(user_id=uid, action=action, details=details[:500]))
    db.session.commit()

def admin_required(view):
    from functools import wraps
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not getattr(current_user, "is_admin", False):
            flash("Admin access required.")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped

def active_subjects():
    """Return subjects currently enabled by the administrator."""
    return [x.name for x in Subject.query.filter_by(is_active=True).order_by(Subject.name.asc()).all()]

def ensure_subjects():
    """Seed the original subjects without overwriting admin changes."""
    existing = {x.name for x in Subject.query.all()}
    added = False
    for name in DEFAULT_SUBJECTS:
        if name not in existing:
            db.session.add(Subject(name=name, is_active=True))
            added = True
    if added:
        db.session.commit()

def valid_subject(name):
    return Subject.query.filter_by(name=name, is_active=True).first() is not None

def visible_note_query():
    return Note.query.filter(Note.user_id.in_([current_user.id] + ([u.id for u in User.query.filter_by(is_admin=True).all()] if User.query.count() else [])))

def visible_pdf_query():
    return PDFNote.query.filter(PDFNote.user_id.in_([current_user.id] + ([u.id for u in User.query.filter_by(is_admin=True).all()] if User.query.count() else [])))

def visible_pyq_pdf_query():
    return PYQPDF.query.filter(PYQPDF.user_id.in_([current_user.id] + ([u.id for u in User.query.filter_by(is_admin=True).all()] if User.query.count() else [])))

# -------------------- HOME / AUTH --------------------

@app.route("/")
def home():
    return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        recovery = request.form.get("recovery_answer", "").strip().lower()
        if not name or not email or len(password) < 6 or not recovery:
            flash("Name, email, a 6+ character password and recovery answer are required.")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for("register"))
        user = User(name=name, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.flush()
        db.session.add(UserRecovery(user_id=user.id, recovery_answer=generate_password_hash(recovery)))
        db.session.add(UserPreference(user_id=user.id))
        db.session.commit()
        log_activity("Student registered", f"{name} created an account")
        flash("Account created successfully. You can now login.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            log_activity("Login", f"User {user.name} logged in")
            return redirect(url_for("admin_dashboard" if user.is_admin else "dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip().lower()
        recovery = request.form.get("recovery_answer", "").strip().lower()
        new_password = request.form.get("new_password", "")
        user = User.query.filter_by(email=email).first()
        if not user or user.name.strip().lower() != name:
            flash("Email and registered name do not match.")
            return redirect(url_for("forgot_password"))
        rec = UserRecovery.query.filter_by(user_id=user.id).first()
        valid = False
        if rec:
            valid = check_password_hash(rec.recovery_answer, recovery)
        else:
            # Compatibility with users created by the original project.
            valid = name == user.name.strip().lower()
        if not valid:
            flash("Recovery answer is incorrect.")
            return redirect(url_for("forgot_password"))
        if len(new_password) < 6:
            flash("New password must contain at least 6 characters.")
            return redirect(url_for("forgot_password"))
        user.password = generate_password_hash(new_password)
        if not rec:
            db.session.add(UserRecovery(user_id=user.id, recovery_answer=generate_password_hash(recovery)))
        db.session.commit()
        flash("Password reset successfully. Please login.")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.route("/logout")
@login_required
def logout():
    log_activity("Logout", "User logged out")
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))

# -------------------- DASHBOARD --------------------

@app.route("/dashboard")
@login_required
def dashboard():
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, status="Completed").count()
    notes_count = visible_note_query().count()
    pdf_count = visible_pdf_query().count()
    pyq_pdf_count = visible_pyq_pdf_query().count()
    pyq_count = PYQ.query.count()
    pending = Task.query.filter_by(user_id=current_user.id, status="Pending").order_by(Task.due_date.asc()).limit(4).all()
    progress_percent = round(completed_tasks / total_tasks * 100) if total_tasks else 0
    plan_sessions = StudyPlan.query.filter_by(user_id=current_user.id).count()
    return render_template("dashboard.html", total_tasks=total_tasks, completed_tasks=completed_tasks,
                           notes_count=notes_count, pdf_count=pdf_count, pyq_count=pyq_count,
                           pyq_pdf_count=pyq_pdf_count, pending=pending,
                           progress_percent=progress_percent, plan_sessions=plan_sessions)

# -------------------- SEARCH --------------------

@app.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    notes, pdfs, tasks, pyqs, pyq_pdfs = [], [], [], [], []
    if q:
        like = f"%{q}%"
        notes = Note.query.filter(Note.user_id == current_user.id,
                                  or_(Note.title.ilike(like), Note.subject.ilike(like), Note.content.ilike(like))).all()
        pdfs = visible_pdf_query().filter(
                                    or_(PDFNote.title.ilike(like), PDFNote.subject.ilike(like),
                                           PDFNote.original_filename.ilike(like))).all()
        tasks = Task.query.filter(Task.user_id == current_user.id,
                                  or_(Task.task.ilike(like), Task.subject.ilike(like), Task.priority.ilike(like))).all()
        pyqs = PYQ.query.filter(or_(PYQ.question.ilike(like), PYQ.subject.ilike(like),
                                       PYQ.unit.ilike(like), cast(PYQ.year, String).ilike(like))).all()
        pyq_pdfs = visible_pyq_pdf_query().filter(
                                       or_(PYQPDF.title.ilike(like), PYQPDF.subject.ilike(like),
                                              PYQPDF.original_filename.ilike(like))).all()
    return render_template("search.html", q=q, notes=notes, pdfs=pdfs, tasks=tasks, pyqs=pyqs, pyq_pdfs=pyq_pdfs)

# -------------------- NOTES --------------------

@app.route("/notes")
@login_required
def notes():
    notes_list = visible_note_query().order_by(Note.created_at.desc()).all()
    pdf_list = visible_pdf_query().order_by(PDFNote.uploaded_at.desc()).all()
    return render_template("notes.html", notes=notes_list, pdfs=pdf_list)

@app.route("/add-note", methods=["GET", "POST"])
@login_required
def add_note():
    if request.method == "POST":
        subject, title, content = [request.form.get(x, "").strip() for x in ("subject", "title", "content")]
        if not subject or not title or not content:
            flash("Please fill all fields.")
            return redirect(url_for("add_note"))
        if not valid_subject(subject):
            flash("Please select an active subject.")
            return redirect(url_for("add_note"))
        db.session.add(Note(user_id=current_user.id, subject=subject, title=title, content=content))
        db.session.commit()
        log_activity("Note added", f"{title} ({subject})")
        flash("Note added successfully.")
        return redirect(url_for("notes"))
    return render_template("add_note.html", subjects=active_subjects())

@app.route("/delete-note/<int:id>")
@login_required
def delete_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id != current_user.id:
        flash("Unauthorized action.")
    else:
        db.session.delete(note)
        db.session.commit()
        flash("Note deleted.")
    return redirect(url_for("notes"))

@app.route("/add-pdf-note", methods=["GET", "POST"])
@login_required
def add_pdf_note():
    if request.method == "GET":
        return render_template("add_pdf_note.html", subjects=active_subjects())
    subject = request.form.get("subject", "").strip()
    title = request.form.get("title", "").strip()
    file = request.files.get("pdf_file")
    if not subject or not title or not file or not file.filename:
        flash("Subject, title and PDF are required.")
        return redirect(url_for("add_pdf_note"))
    if not valid_subject(subject):
        flash("Please select an active subject.")
        return redirect(url_for("add_pdf_note"))
    try:
        unique, original, _ = save_pdf(file, "note")
        db.session.add(PDFNote(user_id=current_user.id, subject=subject, title=title,
                               filename=unique, original_filename=original))
        db.session.commit()
        log_activity("Study PDF uploaded", f"{title} ({subject})")
        flash("Study PDF uploaded successfully.")
    except ValueError as e:
        flash(str(e))
    except Exception:
        db.session.rollback()
        flash("PDF upload failed. Please try again.")
    return redirect(url_for("notes"))

@app.route("/pdf/<int:id>")
@login_required
def view_pdf(id):
    pdf = PDFNote.query.get_or_404(id)
    allowed_owners = {current_user.id} | {u.id for u in User.query.filter_by(is_admin=True).all()}
    if pdf.user_id not in allowed_owners:
        flash("Unauthorized action.")
        return redirect(url_for("notes"))
    path = Path(app.config["UPLOAD_FOLDER"]) / pdf.filename
    if not path.is_file():
        flash("PDF file was not found.")
        return redirect(url_for("notes"))
    return send_from_directory(app.config["UPLOAD_FOLDER"], pdf.filename, as_attachment=False, mimetype="application/pdf")

@app.route("/delete-pdf/<int:id>")
@login_required
def delete_pdf(id):
    pdf = PDFNote.query.get_or_404(id)
    if pdf.user_id != current_user.id:
        flash("Unauthorized action.")
        return redirect(url_for("notes"))
    path = Path(app.config["UPLOAD_FOLDER"]) / pdf.filename
    try:
        if path.exists(): path.unlink()
        db.session.delete(pdf)
        db.session.commit()
        flash("PDF deleted.")
    except Exception:
        db.session.rollback()
        flash("Could not delete PDF.")
    return redirect(url_for("notes"))

# -------------------- PYQs + PYQ PDF --------------------

@app.route("/pyqs")
@login_required
def pyqs():
    subject = request.args.get("subject", "").strip()
    keyword = request.args.get("q", "").strip()
    query = PYQ.query
    if subject:
        query = query.filter_by(subject=subject)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(PYQ.question.ilike(like), PYQ.subject.ilike(like), PYQ.unit.ilike(like)))
    pyq_list = query.order_by(PYQ.year.desc()).all()
    subjects = active_subjects()
    pyq_pdfs = visible_pyq_pdf_query().order_by(PYQPDF.uploaded_at.desc()).all()
    return render_template("pyqs.html", pyqs=pyq_list, subjects=subjects, selected_subject=subject,
                           keyword=keyword, pyq_pdfs=pyq_pdfs)

@app.route("/add-pyq-pdf", methods=["GET", "POST"])
@login_required
def add_pyq_pdf():
    if request.method == "GET":
        return render_template("add_pyq_pdf.html", subjects=active_subjects())
    subject = request.form.get("subject", "").strip()
    title = request.form.get("title", "").strip()
    year_raw = request.form.get("year", "").strip()
    file = request.files.get("pdf_file")
    if not subject or not title or not file or not file.filename:
        flash("Subject, title and PDF are required.")
        return redirect(url_for("add_pyq_pdf"))
    if not valid_subject(subject):
        flash("Please select an active subject.")
        return redirect(url_for("add_pyq_pdf"))
    try:
        year = int(year_raw) if year_raw else None
        unique, original, _ = save_pdf(file, "pyq")
        db.session.add(PYQPDF(user_id=current_user.id, subject=subject, title=title,
                              filename=unique, original_filename=original, year=year))
        db.session.commit()
        log_activity("PYQ PDF uploaded", f"{title} ({subject})")
        flash("PYQ PDF uploaded successfully.")
    except ValueError as e:
        flash(str(e))
    except Exception:
        db.session.rollback()
        flash("PYQ PDF upload failed.")
    return redirect(url_for("pyqs"))

@app.route("/pyq-pdf/<int:id>")
@login_required
def view_pyq_pdf(id):
    pdf = PYQPDF.query.get_or_404(id)
    allowed_owners = {current_user.id} | {u.id for u in User.query.filter_by(is_admin=True).all()}
    if pdf.user_id not in allowed_owners:
        flash("Unauthorized action.")
        return redirect(url_for("pyqs"))
    path = Path(app.config["UPLOAD_FOLDER"]) / pdf.filename
    if not path.is_file():
        flash("PDF file was not found.")
        return redirect(url_for("pyqs"))
    return send_from_directory(app.config["UPLOAD_FOLDER"], pdf.filename, as_attachment=False, mimetype="application/pdf")

@app.route("/delete-pyq-pdf/<int:id>")
@login_required
def delete_pyq_pdf(id):
    pdf = PYQPDF.query.get_or_404(id)
    if pdf.user_id != current_user.id:
        flash("Unauthorized action.")
        return redirect(url_for("pyqs"))
    path = Path(app.config["UPLOAD_FOLDER"]) / pdf.filename
    try:
        if path.exists(): path.unlink()
        db.session.delete(pdf)
        db.session.commit()
        flash("PYQ PDF deleted.")
    except Exception:
        db.session.rollback()
        flash("Could not delete PYQ PDF.")
    return redirect(url_for("pyqs"))

# -------------------- TASKS --------------------

@app.route("/tasks")
@login_required
def tasks():
    task_list = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc()).all()
    return render_template("tasks.html", tasks=task_list)

@app.route("/add-task", methods=["GET", "POST"])
@login_required
def add_task():
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        task_name = request.form.get("task", "").strip()
        due_date = request.form.get("due_date", "").strip()
        priority = request.form.get("priority", "").strip()
        if not all([subject, task_name, due_date, priority]):
            flash("Please fill all fields.")
            return redirect(url_for("add_task"))
        db.session.add(Task(user_id=current_user.id, subject=subject, task=task_name,
                            due_date=due_date, priority=priority, status="Pending"))
        db.session.commit()
        log_activity("Task added", f"{task_name} ({subject})")
        flash("Task added successfully.")
        return redirect(url_for("tasks"))
    return render_template("add_task.html", subjects=active_subjects())

@app.route("/complete-task/<int:id>")
@login_required
def complete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash("Unauthorized action.")
    else:
        task.status = "Completed"
        db.session.commit()
        log_activity("Task completed", f"{task.task} ({task.subject})")
        flash("Task marked completed.")
    return redirect(url_for("tasks"))

@app.route("/delete-task/<int:id>")
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash("Unauthorized action.")
    else:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted.")
    return redirect(url_for("tasks"))

# -------------------- AI-STYLE PERSONALIZED SCHEDULER --------------------

def parse_block_ranges(text):
    """Parse optional blocked times like '12:30-13:30, 21:00-21:30'."""
    result = []
    for part in (text or "").split(","):
        m = re.match(r"\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*", part)
        if m:
            a, b = time_to_minutes(m.group(1)), time_to_minutes(m.group(2))
            if a is not None and b is not None and b > a:
                result.append((m.group(1), m.group(2), "Personal commitment"))
    return result

def subject_score(subject, config, today, exam, pref=None):
    """Explainable adaptive AI scoring model.
    Inputs: priority, interest, difficulty, subject type, exam urgency,
    pending-task urgency, theory/practical preference and recent task completion.
    """
    c = config.get(subject, {})
    priority = int(c.get("priority", 3))
    interest = int(c.get("interest", 3))
    difficulty = int(c.get("difficulty", 3))
    kind = c.get("type", "Theory")
    score = priority * 3.2 + interest * 2.4 + difficulty * 1.8

    if pref:
        type_weight = pref.practical_weight if kind == "Practical" else pref.theory_weight
        score += type_weight * 1.4
        if pref.preferred_slot == "Morning":
            score += 0.4
        elif pref.preferred_slot == "Evening":
            score += 0.2

    if kind == "Practical":
        score += 0.8
    elif kind == "Both":
        score += 1.1

    if exam:
        days = max(1, (exam - today).days)
        score += max(0, 14 - days) * 1.7

    pending = Task.query.filter_by(user_id=current_user.id, subject=subject, status="Pending").all()
    for task in pending:
        try:
            due = datetime.strptime(task.due_date, "%Y-%m-%d").date()
            days_left = (due - today).days
            score += max(0, 10 - days_left) * 1.1 + PRIORITY_SCORE.get(task.priority, 1)
        except ValueError:
            pass

    completed = Task.query.filter_by(user_id=current_user.id, subject=subject, status="Completed").count()
    total = Task.query.filter_by(user_id=current_user.id, subject=subject).count()
    if total:
        # Slightly boost subjects where the student has unfinished/low completion history.
        completion_rate = completed / total
        score += (1 - completion_rate) * 2.0
    return score

def activity_for(subject, config, session_index, learning_style="Mixed"):
    kind = config.get(subject, {}).get("type", "Theory")
    style = (learning_style or "Mixed").lower()
    if kind == "Practical":
        activities = ["Practical / Coding", "Lab Problem Solving", "Implementation Practice", "PYQ + Practical Problems"]
    elif kind == "Both":
        activities = ["Concept + Notes", "PYQ Practice", "Practical / Coding", "Revision + Active Recall"]
    else:
        activities = ["Concept + Notes", "PYQ Practice", "Active Recall + Revision", "Important Questions"]

    if "visual" in style:
        activities = ["Diagrams + Concept Map", "Visual Notes + Recall", "PYQ + Marking Scheme", "Revision + Flashcards"]
    elif "practice" in style:
        activities = ["Problem Solving", "PYQ Practice", "Timed Practice", "Error Review"]
    elif "video" in style:
        activities = ["Lecture/Video + Notes", "Video Recap + Recall", "PYQ Practice", "Revision"]
    return activities[session_index % len(activities)]

def build_plan(user_id, selected_subjects, max_hours, exam_date, pref, config):
    today = date.today()
    exam = None
    try:
        exam = datetime.strptime(exam_date, "%Y-%m-%d").date() if exam_date else None
    except ValueError:
        pass

    # Plan horizon: up to 14 days, ending at exam date when supplied.
    days = min(14, max(1, (exam - today).days + 1 if exam and exam >= today else 7))
    allowed_days = set((pref.study_days or "Mon,Tue,Wed,Thu,Fri,Sat,Sun").split(","))
    day_map = {0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}

    fixed = []
    if pref.college_start and pref.college_end:
        fixed.append((pref.college_start, pref.college_end, "College"))
        if pref.commute_minutes:
            s = time_to_minutes(pref.college_start)
            e = time_to_minutes(pref.college_end)
            if s is not None and e is not None:
                cs = max(0, s - pref.commute_minutes)
                ce = min(1439, e + pref.commute_minutes)
                fixed.append((datetime(2000,1,1,cs//60,cs%60).strftime("%H:%M"),
                              datetime(2000,1,1,ce//60,ce%60).strftime("%H:%M"), "College commute"))
    if pref.gym_start and pref.gym_end:
        fixed.append((pref.gym_start, pref.gym_end, "Gym"))
    if pref.meditation_start:
        mins = max(5, int(pref.meditation_minutes or 15))
        st = time_to_minutes(pref.meditation_start)
        if st is not None:
            fixed.append((datetime(2000,1,1,st//60,st%60).strftime("%H:%M"),
                          datetime(2000,1,1,(st+mins)//60%24,(st+mins)%60).strftime("%H:%M"), "Meditation"))
    fixed.extend(parse_block_ranges(pref.other_commitments))

    blocks = []
    assigned = {s: 0 for s in selected_subjects}
    session_len = max(25, min(120, int(pref.session_minutes or 45)))
    break_len = max(5, min(45, int(pref.break_minutes or 15)))

    for day_offset in range(days):
        d = today + timedelta(days=day_offset)
        if day_map[d.weekday()] not in allowed_days:
            continue

        windows = []
        ranges = []
        # Preferred slot changes the order, not the student's available time.
        if pref.preferred_slot == "Morning":
            ranges = [(pref.morning_start,pref.morning_end),(pref.evening_start,pref.evening_end)]
        elif pref.preferred_slot == "Evening":
            ranges = [(pref.evening_start,pref.evening_end),(pref.morning_start,pref.morning_end)]
        else:
            ranges = [(pref.morning_start,pref.morning_end),(pref.evening_start,pref.evening_end)]
        for a,b in ranges:
            windows.extend(free_windows(a,b,fixed))
        windows = sorted(set((a,b) for a,b in windows if b-a >= session_len))
        remaining = max(0.5, float(max_hours))
        session_no = 0

        while windows and remaining * 60 >= session_len:
            best = None
            for idx,(ws,we) in enumerate(windows):
                cursor = ws
                while cursor + session_len <= we:
                    eligible = sorted(
                        selected_subjects,
                        key=lambda sub: subject_score(sub, config, d, exam, pref) / (1 + assigned[sub] / 90.0),
                        reverse=True
                    )
                    if not eligible:
                        break
                    sub = eligible[0]
                    best = (idx, cursor, sub)
                    break
                if best: break
            if not best: break

            idx, cursor, subject = best
            end = cursor + session_len
            c = config.get(subject, {})
            score = subject_score(subject, config, d, exam, pref)
            reason_parts = [
                f"Priority {c.get('priority',3)}/5",
                f"Interest {c.get('interest',3)}/5",
                f"Difficulty {c.get('difficulty',3)}/5",
                f"{c.get('type','Theory')} weight {pref.practical_weight if c.get('type')=='Practical' else pref.theory_weight}/5"
            ]
            if exam:
                reason_parts.append(f"{max(0,(exam-d).days)} days to exam")
            if pref.target_score:
                reason_parts.append(f"Target {pref.target_score}%")
            blocks.append(StudyPlan(
                user_id=user_id, date=d.strftime("%Y-%m-%d"), day_name=d.strftime("%A"),
                subject=subject, subject_type=c.get("type","Theory"), priority=int(c.get("priority",3)),
                start_time=fmt_minutes(cursor), end_time=fmt_minutes(end),
                activity=activity_for(subject, config, session_no, pref.learning_style),
                focus_score=round(score,2), block_type="Study", reason=" • ".join(reason_parts)
            ))
            assigned[subject] += session_len
            remaining -= session_len / 60.0
            session_no += 1

            # Replace the used window with the remaining portion after the break.
            ws,we = windows[idx]
            new_start = cursor + session_len + break_len
            windows.pop(idx)
            if new_start < we and we - new_start >= session_len:
                windows.append((new_start,we))
                windows.sort()

    return blocks

@app.route("/study-plan", methods=["GET", "POST"])
@login_required
def study_plan():
    pref = get_preferences()
    config = normalize_json(pref.subjects_json)
    if request.method == "POST":
        selected = [x for x in request.form.getlist("subjects") if valid_subject(x)]
        if not selected:
            flash("Select at least one subject.")
            return redirect(url_for("study_plan"))
        try:
            max_hours = float(request.form.get("max_study_hours", 4))
            max_hours = min(12, max(1, max_hours))
        except ValueError:
            max_hours = 4
        exam_date = request.form.get("exam_date", "").strip()
        # Fixed schedule and available windows.
        pref.college_start = request.form.get("college_start", "09:00")
        pref.college_end = request.form.get("college_end", "16:00")
        pref.gym_start = request.form.get("gym_start", "").strip()
        pref.gym_end = request.form.get("gym_end", "").strip()
        pref.meditation_start = request.form.get("meditation_start", "").strip()
        try:
            pref.meditation_minutes = max(5, min(120, int(request.form.get("meditation_minutes", 15))))
        except ValueError:
            pref.meditation_minutes = 15
        pref.morning_start = request.form.get("morning_start", "06:00")
        pref.morning_end = request.form.get("morning_end", "08:30")
        pref.evening_start = request.form.get("evening_start", "17:00")
        pref.evening_end = request.form.get("evening_end", "22:30")
        pref.max_study_hours = max_hours
        pref.exam_date = exam_date
        pref.interests = request.form.get("interests", "").strip()
        pref.wake_time = request.form.get("wake_time", "06:00")
        pref.sleep_time = request.form.get("sleep_time", "23:00")
        pref.study_days = ",".join(request.form.getlist("study_days")) or "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
        try:
            pref.session_minutes = max(25, min(120, int(request.form.get("session_minutes", 45))))
        except ValueError: pref.session_minutes = 45
        try:
            pref.break_minutes = max(5, min(45, int(request.form.get("break_minutes", 15))))
        except ValueError: pref.break_minutes = 15
        pref.preferred_slot = request.form.get("preferred_slot", "Balanced")
        try: pref.commute_minutes = max(0, min(180, int(request.form.get("commute_minutes", 0))))
        except ValueError: pref.commute_minutes = 0
        try: pref.theory_weight = max(1, min(5, int(request.form.get("theory_weight", 3))))
        except ValueError: pref.theory_weight = 3
        try: pref.practical_weight = max(1, min(5, int(request.form.get("practical_weight", 3))))
        except ValueError: pref.practical_weight = 3
        pref.learning_style = request.form.get("learning_style", "Mixed")
        pref.goal = request.form.get("goal", "Exam preparation").strip()
        try: pref.target_score = max(1, min(100, int(request.form.get("target_score", 80))))
        except ValueError: pref.target_score = 80
        pref.hobbies = request.form.get("hobbies", "").strip()
        pref.other_commitments = request.form.get("other_commitments", "").strip()
        config = {}
        for s in active_subjects():
            if s in selected:
                try: pr = max(1, min(5, int(request.form.get(f"priority_{s}", 3))))
                except ValueError: pr = 3
                try: intr = max(1, min(5, int(request.form.get(f"interest_{s}", 3))))
                except ValueError: intr = 3
                try: diff = max(1, min(5, int(request.form.get(f"difficulty_{s}", 3))))
                except ValueError: diff = 3
                config[s] = {
                    "type": request.form.get(f"type_{s}", "Theory"),
                    "priority": pr, "interest": intr, "difficulty": diff
                }
        pref.subjects_json = json.dumps(config)
        StudyPlan.query.filter_by(user_id=current_user.id).delete()
        blocks = build_plan(current_user.id, selected, max_hours, exam_date, pref, config)
        db.session.add_all(blocks)
        db.session.commit()
        log_activity("AI schedule generated", f"{len(blocks)} sessions; goal={pref.goal}; target={pref.target_score}%")
        flash(f"AI-personalized schedule generated with {len(blocks)} study sessions.")
        return redirect(url_for("study_plan"))
    plans = StudyPlan.query.filter_by(user_id=current_user.id).order_by(StudyPlan.date.asc(), StudyPlan.start_time.asc()).all()
    return render_template("study_plan.html", plans=plans, pref=pref, config=config, subjects=active_subjects())

@app.route("/clear-plan", methods=["POST"])
@login_required
def clear_plan():
    StudyPlan.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Study plan cleared.")
    return redirect(url_for("study_plan"))


# -------------------- ADMIN PANEL --------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user = User.query.filter_by(email=email, is_admin=True).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            log_activity("Admin login", f"Admin {user.name} logged in")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.")
    return render_template("admin_login.html")

@app.route("/admin")
@admin_required
def admin_dashboard():
    students = User.query.filter_by(is_admin=False).order_by(User.name.asc()).all()
    total_students = len(students)
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status="Completed").count()
    total_notes = Note.query.count()
    total_pdfs = PDFNote.query.count()
    total_pyqs = PYQ.query.count()
    active_subject_count = Subject.query.filter_by(is_active=True).count()
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(30).all()
    progress = []
    for student in students:
        total = Task.query.filter_by(user_id=student.id).count()
        done = Task.query.filter_by(user_id=student.id, status="Completed").count()
        plan_count = StudyPlan.query.filter_by(user_id=student.id).count()
        percent = round(done / total * 100) if total else 0
        progress.append({"student":student, "total":total, "done":done, "percent":percent, "plan_count":plan_count})
    return render_template("admin_dashboard.html", students=students, progress=progress,
                           total_students=total_students, total_tasks=total_tasks,
                           completed_tasks=completed_tasks, total_notes=total_notes,
                           total_pdfs=total_pdfs, total_pyqs=total_pyqs, logs=recent_logs,
                           active_subject_count=active_subject_count)

@app.route("/admin/student/<int:user_id>")
@admin_required
def admin_student(user_id):
    student = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    tasks = Task.query.filter_by(user_id=student.id).order_by(Task.due_date.asc()).all()
    plans = StudyPlan.query.filter_by(user_id=student.id).order_by(StudyPlan.date.asc(), StudyPlan.start_time.asc()).limit(60).all()
    notes = Note.query.filter_by(user_id=student.id).order_by(Note.created_at.desc()).limit(20).all()
    return render_template("admin_student.html", student=student, tasks=tasks, plans=plans, notes=notes)

@app.route("/admin/add-note", methods=["GET","POST"])
@admin_required
def admin_add_note():
    if request.method == "POST":
        subject=request.form.get("subject","").strip()
        title=request.form.get("title","").strip()
        content=request.form.get("content","").strip()
        if not subject or not title or not content:
            flash("Subject, title and content are required.")
            return redirect(url_for("admin_add_note"))
        if not valid_subject(subject):
            flash("Please select an active subject.")
            return redirect(url_for("admin_add_note"))
        db.session.add(Note(user_id=current_user.id, subject=subject, title=title, content=content))
        db.session.commit()
        log_activity("Admin added global note", f"{title} ({subject})")
        flash("Note added for students.")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_add_note.html", subjects=active_subjects())

@app.route("/admin/add-pdf", methods=["GET","POST"])
@admin_required
def admin_add_pdf():
    if request.method == "POST":
        subject=request.form.get("subject","").strip()
        title=request.form.get("title","").strip()
        file=request.files.get("pdf_file")
        if not subject or not title or not file or not file.filename:
            flash("Subject, title and PDF are required.")
            return redirect(url_for("admin_add_pdf"))
        if not valid_subject(subject):
            flash("Please select an active subject.")
            return redirect(url_for("admin_add_pdf"))
        try:
            unique, original, _ = save_pdf(file, "admin")
            db.session.add(PDFNote(user_id=current_user.id, subject=subject, title=title,
                                   filename=unique, original_filename=original))
            db.session.commit()
            log_activity("Admin added global PDF", f"{title} ({subject})")
            flash("Study PDF added for students.")
        except ValueError as e: flash(str(e))
        except Exception:
            db.session.rollback()
            flash("PDF upload failed.")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_add_pdf.html", subjects=active_subjects())

@app.route("/admin/add-pyq", methods=["GET","POST"])
@admin_required
def admin_add_pyq():
    if request.method == "POST":
        subject=request.form.get("subject","").strip()
        question=request.form.get("question","").strip()
        unit=request.form.get("unit","").strip()
        try:
            year=int(request.form.get("year","0"))
            marks=int(request.form.get("marks","0"))
        except ValueError:
            year=0; marks=0
        difficulty=request.form.get("difficulty","Medium").strip()
        if not all([subject,question,unit,year,marks]):
            flash("Please fill all PYQ fields.")
            return redirect(url_for("admin_add_pyq"))
        if not valid_subject(subject):
            flash("Please select an active subject.")
            return redirect(url_for("admin_add_pyq"))
        db.session.add(PYQ(subject=subject,year=year,unit=unit,question=question,marks=marks,difficulty=difficulty))
        db.session.commit()
        log_activity("Admin added PYQ", f"{subject} {year}")
        flash("PYQ added for all students.")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_add_pyq.html", subjects=active_subjects())

@app.route("/admin/delete-pyq/<int:id>", methods=["POST"])
@admin_required
def admin_delete_pyq(id):
    pyq=PYQ.query.get_or_404(id)
    db.session.delete(pyq); db.session.commit()
    log_activity("Admin deleted PYQ", f"{pyq.subject} {pyq.year}")
    flash("PYQ deleted.")
    return redirect(url_for("admin_dashboard"))

# -------------------- ADMIN SUBJECT MANAGEMENT --------------------

@app.route("/admin/subjects", methods=["GET", "POST"])
@admin_required
def admin_subjects():
    if request.method == "POST":
        name = " ".join(request.form.get("name", "").strip().split())
        if not name:
            flash("Enter a subject name.")
            return redirect(url_for("admin_subjects"))
        if len(name) > 100:
            flash("Subject name is too long.")
            return redirect(url_for("admin_subjects"))
        subject = Subject.query.filter(func.lower(Subject.name) == name.lower()).first()
        if subject:
            if subject.is_active:
                flash("That subject already exists.")
            else:
                subject.is_active = True
                db.session.commit()
                log_activity("Subject restored", name)
                flash(f"{name} is active again.")
            return redirect(url_for("admin_subjects"))
        db.session.add(Subject(name=name, is_active=True))
        db.session.commit()
        log_activity("Subject added", name)
        flash(f"{name} added successfully.")
        return redirect(url_for("admin_subjects"))
    subjects = Subject.query.order_by(Subject.is_active.desc(), Subject.name.asc()).all()
    return render_template("admin_subjects.html", subjects=subjects)

@app.route("/admin/subjects/<int:id>/remove", methods=["POST"])
@admin_required
def admin_remove_subject(id):
    subject = Subject.query.get_or_404(id)
    if not subject.is_active:
        flash("Subject is already inactive.")
        return redirect(url_for("admin_subjects"))
    # Soft-disable so existing notes, PDFs, PYQs, tasks and plans are preserved.
    subject.is_active = False
    db.session.commit()
    log_activity("Subject removed", f"{subject.name} disabled from new entries")
    flash(f"{subject.name} removed from active subject lists. Existing material was preserved.")
    return redirect(url_for("admin_subjects"))

@app.route("/admin/subjects/<int:id>/restore", methods=["POST"])
@admin_required
def admin_restore_subject(id):
    subject = Subject.query.get_or_404(id)
    subject.is_active = True
    db.session.commit()
    log_activity("Subject restored", subject.name)
    flash(f"{subject.name} restored.")
    return redirect(url_for("admin_subjects"))

# -------------------- DB SEED + ERROR HANDLING --------------------

@app.errorhandler(413)
def too_large(_):
    flash("PDF is too large. Maximum allowed size is 15 MB.")
    return redirect(url_for("notes"))

def ensure_legacy_schema():
    """Idempotent SQLite migration for databases made by older project versions."""
    from sqlalchemy import text
    with db.engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(study_plan)")).fetchall()
        columns = {row[1] for row in rows}
        additions = {
            "day_name": "VARCHAR(20) DEFAULT ''",
            "subject_type": "VARCHAR(50) DEFAULT 'Theory'",
            "priority": "INTEGER DEFAULT 3",
            "focus_score": "FLOAT DEFAULT 0.0",
            "block_type": "VARCHAR(50) DEFAULT 'Study'",
            "reason": "VARCHAR(255) DEFAULT ''",
        }
        for column, definition in additions.items():
            if column not in columns:
                conn.execute(text(f"ALTER TABLE study_plan ADD COLUMN {column} {definition}"))
        conn.execute(text(
            "UPDATE study_plan SET day_name = CASE strftime('%w', date) "
            "WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday' "
            "WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday' "
            "WHEN '6' THEN 'Saturday' ELSE '' END WHERE day_name IS NULL OR day_name = ''"
        ))
        conn.execute(text("UPDATE study_plan SET subject_type='Theory' WHERE subject_type IS NULL OR subject_type=''"))
        conn.execute(text("UPDATE study_plan SET priority=3 WHERE priority IS NULL"))
        conn.execute(text("UPDATE study_plan SET focus_score=0.0 WHERE focus_score IS NULL"))
        conn.execute(text("UPDATE study_plan SET block_type='Study' WHERE block_type IS NULL OR block_type=''"))
        conn.execute(text("UPDATE study_plan SET reason='' WHERE reason IS NULL"))

        # User/admin and preference migrations for older databases.
        urows = conn.execute(text("PRAGMA table_info(user)")).fetchall()
        ucols = {row[1] for row in urows}
        if "is_admin" not in ucols:
            conn.execute(text("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"))

        prows = conn.execute(text("PRAGMA table_info(user_preference)")).fetchall()
        pcols = {row[1] for row in prows}
        pref_additions = {
            "wake_time":"VARCHAR(5) DEFAULT '06:00'", "sleep_time":"VARCHAR(5) DEFAULT '23:00'",
            "study_days":"TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'", "session_minutes":"INTEGER DEFAULT 45",
            "break_minutes":"INTEGER DEFAULT 15", "preferred_slot":"VARCHAR(20) DEFAULT 'Balanced'",
            "commute_minutes":"INTEGER DEFAULT 0", "theory_weight":"INTEGER DEFAULT 3",
            "practical_weight":"INTEGER DEFAULT 3", "learning_style":"VARCHAR(100) DEFAULT 'Mixed'",
            "goal":"VARCHAR(150) DEFAULT 'Exam preparation'", "target_score":"INTEGER DEFAULT 80",
            "hobbies":"TEXT DEFAULT ''", "other_commitments":"TEXT DEFAULT ''"
        }
        for column, definition in pref_additions.items():
            if column not in pcols:
                conn.execute(text(f"ALTER TABLE user_preference ADD COLUMN {column} {definition}"))

def ensure_default_admin():
    email = os.environ.get("STUDY_ADMIN_EMAIL", "admin@studyplanner.local").strip().lower()
    password = os.environ.get("STUDY_ADMIN_PASSWORD", "Admin@123")
    admin = User.query.filter_by(email=email).first()
    if not admin:
        admin = User(name="Study Planner Admin", email=email,
                     password=generate_password_hash(password), is_admin=True)
        db.session.add(admin)
        db.session.commit()
    elif not admin.is_admin:
        admin.is_admin = True
        db.session.commit()

def add_sample_pyqs():
    if PYQ.query.count():
        return
    samples = [
        PYQ(subject="Python", year=2025, unit="Unit 1", question="Explain the basic features of Python.", marks=5, difficulty="Easy"),
        PYQ(subject="Python", year=2024, unit="Unit 2", question="Explain object oriented programming in Python.", marks=10, difficulty="Medium"),
        PYQ(subject="DBMS", year=2025, unit="Unit 3", question="Explain normalization with suitable examples.", marks=10, difficulty="Hard"),
        PYQ(subject="DBMS", year=2024, unit="Unit 2", question="Explain different types of database keys.", marks=5, difficulty="Medium"),
        PYQ(subject="Operating System", year=2025, unit="Unit 2", question="Explain process scheduling algorithms.", marks=10, difficulty="Hard"),
        PYQ(subject="Computer Networks", year=2025, unit="Unit 4", question="Explain the TCP/IP model.", marks=10, difficulty="Medium"),
        PYQ(subject="Software Engineering", year=2024, unit="Unit 1", question="Explain the software development life cycle.", marks=10, difficulty="Easy")
    ]
    db.session.add_all(samples)
    db.session.commit()

with app.app_context():
    db.create_all()
    ensure_legacy_schema()
    ensure_subjects()
    ensure_default_admin()
    add_sample_pyqs()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

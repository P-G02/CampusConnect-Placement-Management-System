"""
CampusConnect — Flask Application
===================================
Role-based login for Student and Company users.
Auth backed by PostgreSQL placement_management database.
"""

import os
import re
import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
import psycopg2
import psycopg2.extras
from werkzeug.security import check_password_hash, generate_password_hash

SEEDED_STUDENT_IDS = {
    'S1001', 'S1002', 'S1003', 'S1004', 'S1005', 'S1006',
    'S1007', 'S1008', 'S1009', 'S1010', 'S1011', 'S1012'
}

# ─────────────────────────── App Setup ───────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "campusconnect-dev-secret-change-in-production-2024"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ─────────────────────────── DB Config ───────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",   "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5432)),
    "dbname":   os.environ.get("DB_NAME",   "placement_management"),
    "user":     os.environ.get("DB_USER",   "postgres"),
    "password": os.environ.get("DB_PASS",   "Pass@123"),
}

def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

# ─────────────────────── Auth Decorators ─────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login"))
            if session.get("role") != role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated
    return decorator
 
# ─────────────────────── Context Processor ───────────────────────
def is_demo_user():
    return bool(session.get("is_demo", False) or session.get("email", "").lower().startswith("demo."))

@app.context_processor
def inject_demo_context():
    return {
        "is_demo_user": is_demo_user(),
        "seeded_student_ids": SEEDED_STUDENT_IDS,
    }

# ─────────────────────── Helpers ─────────────────────────────────
def validate_student_form(form):
    """Validate student create/update form fields. Returns (errors_list, cleaned_data)."""
    errors = []
    data = {}

    sid   = form.get("student_id", "").strip().upper()
    name  = form.get("student_name", "").strip()
    email = form.get("student_email", "").strip().lower()
    phone = form.get("student_phone", "").strip()
    dept  = form.get("dept_id", "").strip()
    cgpa_raw = form.get("cgpa", "").strip()
    grad_raw = form.get("graduation_yr", "").strip()

    if not sid:
        errors.append("Student ID is required.")
    elif not re.match(r"^[A-Z]\d{4,5}$", sid):
        errors.append("Student ID must be a letter followed by 4–5 digits (e.g. S1001).")

    if not name:
        errors.append("Student name is required.")
    elif len(name) > 50:
        errors.append("Student name must be at most 50 characters.")

    if email:
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            errors.append("Invalid email address format.")
        elif len(email) > 50:
            errors.append("Email must be at most 50 characters.")

    if phone and len(phone) > 15:
        errors.append("Phone number must be at most 15 characters.")

    if not dept:
        errors.append("Department is required.")

    try:
        cgpa = float(cgpa_raw)
        if cgpa <= 0 or cgpa > 10:
            errors.append("CGPA must be between 0.01 and 10.00.")
    except ValueError:
        errors.append("CGPA must be a number.")
        cgpa = None

    try:
        grad = int(grad_raw)
        if grad < 2000 or grad > 2040:
            errors.append("Graduation year must be between 2000 and 2040.")
    except ValueError:
        errors.append("Graduation year must be a valid integer.")
        grad = None

    data = {
        "student_id":    sid,
        "student_name":  name,
        "student_email": email or None,
        "student_phone": phone or None,
        "dept_id":       dept,
        "cgpa":          cgpa,
        "graduation_yr": grad,
    }
    return errors, data


def validate_company_form(form):
    """Validate company create/update form fields. Returns (errors_list, cleaned_data)."""
    errors = []

    cid   = form.get("company_id", "").strip().upper()
    name  = form.get("company_name", "").strip()
    email = form.get("company_email", "").strip().lower()
    phone = form.get("company_phone", "").strip()
    locn  = form.get("company_locn", "").strip()

    if not cid:
        errors.append("Company ID is required.")
    elif not re.match(r"^C\d{5}$", cid):
        errors.append("Company ID must be 'C' followed by exactly 5 digits (e.g. C10001).")

    if not name:
        errors.append("Company name is required.")
    elif len(name) > 50:
        errors.append("Company name must be at most 50 characters.")

    if email:
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            errors.append("Invalid email address format.")
        elif len(email) > 50:
            errors.append("Email must be at most 50 characters.")

    if phone and len(phone) > 15:
        errors.append("Phone must be at most 15 characters.")

    if locn and len(locn) > 50:
        errors.append("Location must be at most 50 characters.")

    data = {
        "company_id":    cid,
        "company_name":  name,
        "company_email": email or None,
        "company_phone": phone or None,
        "company_locn":  locn or None,
    }
    return errors, data


def validate_opportunity_form(form):
    """Validate opportunity create/update form fields. Returns (errors_list, cleaned_data)."""
    errors = []

    title = form.get("opp_title", "").strip()
    opp_type = form.get("opp_type", "").strip().upper()
    opp_locn = form.get("opp_locn", "").strip()
    package_raw = form.get("package", "").strip()
    stipend_raw = form.get("stipend", "").strip()
    min_cgpa_raw = form.get("min_cgpa", "").strip()
    deadline_raw = form.get("deadline", "").strip()
    openings_raw = form.get("openings", "").strip()

    if not title:
        errors.append("Job title is required.")
    elif len(title) > 50:
        errors.append("Job title must be at most 50 characters.")

    if not opp_type:
        errors.append("Opportunity type is required.")
    elif opp_type not in ("JOB", "INTERNSHIP"):
        errors.append("Opportunity type must be either 'JOB' or 'INTERNSHIP'.")

    if opp_locn and len(opp_locn) > 50:
        errors.append("Location must be at most 50 characters.")

    openings = None
    if not openings_raw:
        errors.append("Number of openings is required.")
    else:
        try:
            openings = int(openings_raw)
            if openings <= 0:
                errors.append("Number of openings must be a positive integer greater than zero.")
        except (ValueError, TypeError):
            errors.append("Number of openings must be a valid integer.")

    package = None
    if package_raw:
        try:
            package = float(package_raw)
            if package < 0:
                errors.append("Package cannot be negative.")
        except ValueError:
            errors.append("Package must be a valid number.")

    stipend = None
    if stipend_raw:
        try:
            stipend = float(stipend_raw)
            if stipend < 0:
                errors.append("Stipend cannot be negative.")
        except ValueError:
            errors.append("Stipend must be a valid number.")

    min_cgpa = None
    if not min_cgpa_raw:
        errors.append("Minimum CGPA is required.")
    else:
        try:
            min_cgpa = float(min_cgpa_raw)
            # PostgreSQL constraint: check (((min_cgpa > 7.5) and (min_cgpa <= 10.0)))
            if min_cgpa <= 7.5 or min_cgpa > 10.0:
                errors.append("Minimum CGPA must be greater than 7.5 and at most 10.0.")
        except ValueError:
            errors.append("Minimum CGPA must be a valid number.")

    deadline = None
    if not deadline_raw:
        errors.append("Application deadline is required.")
    else:
        try:
            deadline = datetime.datetime.strptime(deadline_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Deadline must be in valid YYYY-MM-DD format.")

    data = {
        "opp_title": title,
        "opp_type":  opp_type,
        "opp_locn":  opp_locn or None,
        "package":   package,
        "stipend":   stipend,
        "min_cgpa":  min_cgpa,
        "deadline":  deadline,
        "openings":  openings,
    }
    return errors, data


# ──────────────────────────── Routes ─────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        role = session.get("role")
        if role == "STUDENT":
            return redirect(url_for("student_dashboard"))
        elif role == "COMPANY":
            return redirect(url_for("company_dashboard"))
        elif role == "ADMINISTRATOR":
            return redirect(url_for("admin_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        role = session.get("role")
        if role == "STUDENT":
            return redirect(url_for("student_dashboard"))
        elif role == "COMPANY":
            return redirect(url_for("company_dashboard"))
        elif role == "ADMINISTRATOR":
            return redirect(url_for("admin_dashboard"))

    if request.method == "GET":
        return render_template("login.html")

    email      = request.form.get("email", "").lower().strip()
    password   = request.form.get("password", "")
    role_input = request.form.get("role", "").upper().strip()

    if not email or not password or not role_input:
        flash("All fields are required.", "error")
        return render_template("login.html", prefill_email=email, prefill_role=role_input)

    if role_input not in ("STUDENT", "COMPANY", "ADMINISTRATOR"):
        flash("Invalid role selected.", "error")
        return render_template("login.html", prefill_email=email)

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            """
            SELECT user_id, email, password_hash, role, is_active,
                   student_id, company_id
            FROM   users
            WHERE  email = %s
            """,
            (email,)
        )
        user = cur.fetchone()

        AUTH_ERROR = "Invalid email, password, or role. Please try again."

        if user is None or not user["is_active"]:
            flash(AUTH_ERROR if user is None else
                  "Your account is inactive. Contact support.", "error")
            return render_template("login.html", prefill_email=email, prefill_role=role_input)

        if not check_password_hash(user["password_hash"], password):
            flash(AUTH_ERROR, "error")
            return render_template("login.html", prefill_email=email, prefill_role=role_input)

        if user["role"] != role_input:
            flash(AUTH_ERROR, "error")
            return render_template("login.html", prefill_email=email, prefill_role=role_input)

        session.clear()
        session["user_id"]    = user["user_id"]
        session["email"]      = user["email"]
        session["role"]       = user["role"]
        session["student_id"] = user["student_id"]
        session["company_id"] = user["company_id"]
        session["is_demo"]    = (user["email"].lower().startswith("demo.") or user["email"].lower() in ("demo.student@campusconnect.local", "demo.company@campusconnect.local"))

        if user["role"] == "STUDENT" and user["student_id"]:
            cur.execute("SELECT student_name FROM student WHERE student_id = %s",
                        (user["student_id"],))
            row = cur.fetchone()
            session["display_name"] = row["student_name"] if row else email
        elif user["role"] == "COMPANY" and user["company_id"]:
            cur.execute("SELECT company_name FROM company WHERE company_id = %s",
                        (user["company_id"],))
            row = cur.fetchone()
            session["display_name"] = row["company_name"] if row else email
        else:
            session["display_name"] = email

        # Redirect to appropriate dashboard based on role
        if user["role"] == "ADMINISTRATOR":
            return redirect(url_for("admin_dashboard"))
        elif user["role"] == "STUDENT":
            return redirect(url_for("student_dashboard"))
        else:  # COMPANY
            return redirect(url_for("company_dashboard"))

    except psycopg2.Error as e:
        app.logger.error("DB error during login: %s", e)
        flash("A database error occurred. Please try again.", "error")
        return render_template("login.html", prefill_email=email, prefill_role=role_input)
    finally:
        if conn:
            conn.close()


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ────────────────────── Student Dashboard ────────────────────────

@app.route("/student/dashboard")
@role_required("STUDENT")
def student_dashboard():
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        is_demo = session.get("is_demo", False) or session.get("email", "").lower().startswith("demo.")

        # Allow authorized demo workflow to view dashboard as another student
        view_as = request.args.get("view_as", "").strip().upper()
        if is_demo:
            if view_as == "RESET":
                session.pop("demo_view_student_id", None)
            elif view_as:
                cur.execute("SELECT student_id FROM student WHERE student_id = %s", (view_as,))
                if cur.fetchone():
                    session["demo_view_student_id"] = view_as

        active_student_id = session.get("demo_view_student_id") if (is_demo and session.get("demo_view_student_id")) else session.get("student_id")

        cur.execute(
            """
            SELECT s.*, d.dept_name
            FROM   student s
            JOIN   department d ON s.dept_id = d.dept_id
            WHERE  s.student_id = %s
            """,
            (active_student_id,)
        )
        student = cur.fetchone()

        # Fallback to session student if selected demo student was deleted/not found
        if not student:
            active_student_id = session.get("student_id")
            session.pop("demo_view_student_id", None)
            cur.execute(
                """
                SELECT s.*, d.dept_name
                FROM   student s
                JOIN   department d ON s.dept_id = d.dept_id
                WHERE  s.student_id = %s
                """,
                (active_student_id,)
            )
            student = cur.fetchone()

        cur.execute(
            """
            SELECT sk.skill_name
            FROM   student_skill ss
            JOIN   skill sk ON ss.skill_id = sk.skill_id
            WHERE  ss.student_id = %s
            ORDER  BY sk.skill_name
            """,
            (active_student_id,)
        )
        skills = [r["skill_name"] for r in cur.fetchall()]

        cur.execute(
            """
            SELECT a.appl_id, a.appl_date,
                   o.opp_id, o.opp_title, o.opp_type, o.opp_locn,
                   c.company_name,
                   COALESCE(i.status, 'PENDING') AS interview_status,
                   i.interview_date, i.interview_rd
            FROM   application a
            JOIN   opportunity o  ON a.opp_id    = o.opp_id
            JOIN   company     c  ON o.company_id = c.company_id
            LEFT JOIN interview i ON i.appl_id   = a.appl_id
            WHERE  a.student_id = %s
            ORDER  BY a.appl_date DESC, a.appl_id DESC
            """,
            (active_student_id,)
        )
        applications = cur.fetchall()
        applied_opp_ids = {a["opp_id"] for a in applications if a.get("opp_id")}

        cur.execute(
            """
            SELECT p.*, c.company_name, o.opp_title
            FROM   placement p
            JOIN   company     c ON p.company_id = c.company_id
            JOIN   opportunity o ON p.opp_id     = o.opp_id
            WHERE  p.student_id = %s
            """,
            (active_student_id,)
        )
        placement = cur.fetchone()

        student_cgpa = student["cgpa"] if student and student["cgpa"] is not None else 0
        cur.execute(
            """
            SELECT o.*, c.company_name
            FROM   opportunity o
            JOIN   company c ON o.company_id = c.company_id
            WHERE  o.min_cgpa <= %s
              AND  o.deadline >= CURRENT_DATE
            ORDER  BY o.deadline ASC
            LIMIT  15
            """,
            (student_cgpa,)
        )
        opportunities = cur.fetchall()

        all_students = []
        all_opportunities = []
        if is_demo:
            cur.execute("SELECT student_id, student_name, cgpa FROM student ORDER BY student_name")
            all_students = cur.fetchall()

            cur.execute(
                """
                SELECT o.opp_id, o.opp_title, o.opp_type, o.min_cgpa, o.deadline, c.company_name
                FROM   opportunity o
                JOIN   company c ON o.company_id = c.company_id
                WHERE  o.deadline >= CURRENT_DATE
                ORDER  BY c.company_name, o.opp_title
                """
            )
            all_opportunities = cur.fetchall()

        return render_template(
            "student_dashboard.html",
            student=student,
            skills=skills,
            applications=applications,
            applied_opp_ids=applied_opp_ids,
            placement=placement,
            opportunities=opportunities,
            all_students=all_students,
            all_opportunities=all_opportunities,
            active_student_id=active_student_id,
        )

    except psycopg2.Error as e:
        app.logger.error("DB error on student dashboard: %s", e)
        flash("Error loading dashboard data.", "error")
        return render_template("student_dashboard.html",
                               student=None, skills=[], applications=[],
                               applied_opp_ids=set(), placement=None,
                               opportunities=[], all_students=[], all_opportunities=[])
    finally:
        if conn:
            conn.close()


# ────────────────────── Apply for Job Route ────────────────────────

@app.route("/apply", methods=["POST"])
@login_required
def apply_job():
    """
    Apply for a job/opportunity.
    - Parameterized SQL INSERT into application table.
    - Validates student_id, opp_id, prevents duplicate applications.
    - Authorized demo workflow allows authorized demo users to apply on behalf of any student.
    - Ordinary students can only apply for themselves.
    """
    is_demo = session.get("is_demo", False) or session.get("email", "").lower().startswith("demo.")
    target_student_id = request.form.get("student_id", "").strip().upper()
    opp_id = request.form.get("opp_id", "").strip().upper()
    redirect_to = request.form.get("redirect_to") or url_for("student_dashboard")

    # Security check: ordinary non-demo students can ONLY apply for themselves
    if session.get("role") == "STUDENT" and not is_demo:
        if target_student_id != session.get("student_id"):
            flash("You do not have permission to apply on behalf of other students.", "error")
            return redirect(redirect_to)
    elif session.get("role") == "COMPANY" and not is_demo:
        flash("Company accounts cannot submit applications on behalf of students.", "error")
        return redirect(redirect_to)

    if not target_student_id or not opp_id:
        flash("Both Student ID and Opportunity ID are required to apply.", "error")
        return redirect(redirect_to)

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        # Validate student exists
        cur.execute(
            "SELECT student_id, student_name, cgpa FROM student WHERE student_id = %s",
            (target_student_id,)
        )
        student = cur.fetchone()
        if not student:
            flash(f"Student '{target_student_id}' does not exist.", "error")
            return redirect(redirect_to)

        # Validate opportunity exists
        cur.execute(
            """
            SELECT o.opp_id, o.opp_title, o.opp_type, o.min_cgpa, o.deadline, c.company_name
            FROM   opportunity o
            JOIN   company c ON o.company_id = c.company_id
            WHERE  o.opp_id = %s
            """,
            (opp_id,)
        )
        opp = cur.fetchone()
        if not opp:
            flash(f"Opportunity '{opp_id}' does not exist.", "error")
            return redirect(redirect_to)

        # Check deadline
        if opp["deadline"] and opp["deadline"] < datetime.date.today():
            flash(f"Application closed: The deadline for '{opp['opp_title']}' was {opp['deadline']}.", "error")
            return redirect(redirect_to)

        # Prevent duplicate applications
        cur.execute(
            "SELECT appl_id, appl_date FROM application WHERE student_id = %s AND opp_id = %s",
            (target_student_id, opp_id)
        )
        existing = cur.fetchone()
        if existing:
            flash(
                f"{student['student_name']} has already applied for {opp['opp_title']} at {opp['company_name']} "
                f"on {existing['appl_date']} (Application ID: {existing['appl_id']}). Duplicate applications are not allowed.",
                "warning"
            )
            return redirect(redirect_to)

        # Check CGPA constraint / requirement
        if student["cgpa"] is not None and opp["min_cgpa"] is not None:
            if float(student["cgpa"]) < float(opp["min_cgpa"]):
                flash(
                    f"Eligibility warning: {student['student_name']}'s CGPA ({student['cgpa']}) is below the minimum required {opp['min_cgpa']} for {opp['opp_title']}.",
                    "error"
                )
                return redirect(redirect_to)

        # Generate next appl_id safely
        cur.execute(
            """
            SELECT appl_id
            FROM   application
            WHERE  appl_id ~ '^AP[0-9]+$'
            ORDER  BY CAST(SUBSTRING(appl_id FROM 3) AS INTEGER) DESC
            LIMIT  1
            FOR UPDATE
            """
        )
        last_appl = cur.fetchone()
        if last_appl:
            next_num = int(last_appl["appl_id"][2:]) + 1
        else:
            next_num = 10001
        new_appl_id = f"AP{next_num}"

        # Insert application into PostgreSQL application table
        cur.execute(
            """
            INSERT INTO application (appl_id, student_id, opp_id, appl_date)
            VALUES (%s, %s, %s, CURRENT_DATE)
            """,
            (new_appl_id, target_student_id, opp_id)
        )
        conn.commit()

        # In demo workflow, keep the view on the applied student so they immediately see it
        if is_demo:
            session["demo_view_student_id"] = target_student_id

        flash(
            f"Application {new_appl_id} submitted successfully! {student['student_name']} is now applied for {opp['opp_title']} at {opp['company_name']}.",
            "success"
        )
        return redirect(redirect_to)

    except psycopg2.Error as e:
        app.logger.error("DB error applying for job: %s", e)
        if conn:
            conn.rollback()
        flash("A database error occurred while submitting the application.", "error")
        return redirect(redirect_to)
    finally:
        if conn:
            conn.close()


# ────────────────────── Company Dashboard ────────────────────────

@app.route("/company/dashboard")
@role_required("COMPANY")
def company_dashboard():
    company_id = session.get("company_id")
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT * FROM company WHERE company_id = %s", (company_id,))
        company = cur.fetchone()

        cur.execute(
            """
            SELECT o.*,
                   COUNT(DISTINCT a.appl_id) AS applicant_count
            FROM   opportunity o
            LEFT JOIN application a ON a.opp_id = o.opp_id
            WHERE  o.company_id = %s
            GROUP  BY o.opp_id
            ORDER  BY o.deadline ASC
            """,
            (company_id,)
        )
        opportunities = cur.fetchall()

        cur.execute(
            """
            SELECT a.appl_id, a.appl_date, a.student_id,
                   s.student_name, s.student_email, s.cgpa,
                   d.dept_name,
                   o.opp_id, o.opp_title, o.opp_type,
                   COALESCE(i.status, 'PENDING') AS interview_status,
                   i.interview_id, i.interview_date, i.interview_rd
            FROM   application a
            JOIN   student    s  ON a.student_id  = s.student_id
            JOIN   department d  ON s.dept_id     = d.dept_id
            JOIN   opportunity o ON a.opp_id      = o.opp_id
            LEFT JOIN interview i ON i.appl_id    = a.appl_id
            WHERE  o.company_id = %s
            ORDER  BY a.appl_date DESC
            """,
            (company_id,)
        )
        applications = cur.fetchall()

        cur.execute(
            """
            SELECT p.*, s.student_name, s.student_email, o.opp_title
            FROM   placement p
            JOIN   student     s ON p.student_id = s.student_id
            JOIN   opportunity o ON p.opp_id     = o.opp_id
            WHERE  p.company_id = %s
            ORDER  BY p.plm_date DESC
            """,
            (company_id,)
        )
        placements = cur.fetchall()

        return render_template(
            "company_dashboard.html",
            company=company,
            opportunities=opportunities,
            applications=applications,
            placements=placements,
        )

    except psycopg2.Error as e:
        app.logger.error("DB error on company dashboard: %s", e)
        flash("Error loading dashboard data.", "error")
        return render_template("company_dashboard.html",
                               company=None, opportunities=[], applications=[], placements=[])
    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════════
#  STUDENT MANAGEMENT  (all 12 students, CRUD)
# ══════════════════════════════════════════════════════════════════

@app.route("/manage/students")
@login_required
def manage_students():
    """List ALL students from DB. Strictly restricted to Administrators."""
    is_demo = is_demo_user()
    if session.get("role") != "ADMINISTRATOR" and not is_demo:
        flash("Access denied: Only administrators can access student management.", "danger")
        return redirect(url_for("student_dashboard" if session.get("role") == "STUDENT" else "company_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        # Search / filter
        search = request.args.get("q", "").strip()
        dept_filter = request.args.get("dept", "").strip()

        query = """
            SELECT s.student_id, s.student_name, s.student_email,
                   s.student_phone, s.cgpa, s.graduation_yr,
                   d.dept_name, s.dept_id,
                   COUNT(DISTINCT a.appl_id) AS app_count,
                   COUNT(DISTINCT p.plm_id) AS plm_count,
                   STRING_AGG(DISTINCT sk.skill_name, ', ' ORDER BY sk.skill_name) AS skill_names
            FROM   student s
            JOIN   department d ON s.dept_id = d.dept_id
            LEFT JOIN student_skill ss ON s.student_id = ss.student_id
            LEFT JOIN skill sk ON ss.skill_id = sk.skill_id
            LEFT JOIN application a ON s.student_id = a.student_id
            LEFT JOIN placement   p ON s.student_id = p.student_id
            WHERE  1=1
        """
        params = []
        if search:
            query += " AND (LOWER(s.student_name) LIKE %s OR LOWER(s.student_email) LIKE %s OR s.student_id LIKE %s OR LOWER(sk.skill_name) LIKE %s)"
            like = f"%{search.lower()}%"
            params.extend([like, like, like.upper(), like])
        if dept_filter:
            query += " AND s.dept_id = %s"
            params.append(dept_filter)

        query += " GROUP BY s.student_id, d.dept_name ORDER BY s.student_id"
        cur.execute(query, params)
        students = cur.fetchall()

        cur.execute("SELECT dept_id, dept_name FROM department ORDER BY dept_name")
        departments = cur.fetchall()

        return render_template(
            "manage_students.html",
            students=students,
            departments=departments,
            search=search,
            dept_filter=dept_filter,
            total=len(students),
        )
    except psycopg2.Error as e:
        app.logger.error("DB error listing students: %s", e)
        flash("Error loading student list.", "error")
        return render_template("manage_students.html",
                               students=[], departments=[], search="", dept_filter="", total=0)
    finally:
        if conn:
            conn.close()


@app.route("/manage/students/new", methods=["GET", "POST"])
@login_required
def student_new():
    """Create a new student record. Restricted to ADMINISTRATOR or authorized demo workflow."""
    is_demo = is_demo_user()
    if session.get("role") == "STUDENT" and not is_demo:
        flash("You do not have permission to create student records.", "error")
        return redirect(url_for("student_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("SELECT dept_id, dept_name FROM department ORDER BY dept_name")
        departments = cur.fetchall()

        cur.execute("SELECT skill_id, skill_name FROM skill ORDER BY skill_name")
        skills = cur.fetchall()

        if request.method == "GET":
            return render_template(
                "student_form.html",
                departments=departments,
                student=None,
                action="create",
                skills=skills,
                selected_skill_ids=[]
            )

        selected_skill_ids = request.form.getlist("skills")
        errors, data = validate_student_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "student_form.html",
                departments=departments,
                student=request.form,
                action="create",
                skills=skills,
                selected_skill_ids=selected_skill_ids
            )

        # Duplicate ID check
        cur.execute("SELECT 1 FROM student WHERE student_id = %s", (data["student_id"],))
        if cur.fetchone():
            flash(f"Student ID {data['student_id']} already exists.", "error")
            return render_template(
                "student_form.html",
                departments=departments,
                student=request.form,
                action="create",
                skills=skills,
                selected_skill_ids=selected_skill_ids
            )

        # Duplicate email check
        if data["student_email"]:
            cur.execute("SELECT 1 FROM student WHERE student_email = %s", (data["student_email"],))
            if cur.fetchone():
                flash("That email is already registered to another student.", "error")
                return render_template(
                    "student_form.html",
                    departments=departments,
                    student=request.form,
                    action="create",
                    skills=skills,
                    selected_skill_ids=selected_skill_ids
                )

        cur.execute(
            """
            INSERT INTO student
                (student_id, student_name, student_email, student_phone,
                 dept_id, cgpa, graduation_yr)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (data["student_id"], data["student_name"], data["student_email"],
             data["student_phone"], data["dept_id"], data["cgpa"], data["graduation_yr"])
        )

        # Insert selected skills
        if selected_skill_ids:
            cur.execute("SELECT skill_id FROM skill WHERE skill_id = ANY(%s)", (selected_skill_ids,))
            valid_skill_ids = {r["skill_id"] for r in cur.fetchall()}
            for s_id in valid_skill_ids:
                cur.execute(
                    "INSERT INTO student_skill (student_id, skill_id) VALUES (%s, %s)",
                    (data["student_id"], s_id)
                )

        # ── Create a linked users login account so this student can log in ──
        # Use student email as login; default password = Student@1234
        # Skip gracefully if a users row already exists for this email or student_id.
        login_email = data["student_email"] or f"{data['student_id'].lower()}@campusconnect.local"
        cur.execute("SELECT user_id FROM users WHERE email = %s", (login_email,))
        existing_user = cur.fetchone()
        login_created = False
        if not existing_user:
            cur.execute("SELECT user_id FROM users WHERE student_id = %s", (data["student_id"],))
            existing_by_sid = cur.fetchone()
            if not existing_by_sid:
                default_password = "Student@1234"
                pw_hash = generate_password_hash(default_password)
                cur.execute(
                    """
                    INSERT INTO users (email, password_hash, role, student_id, is_active)
                    VALUES (%s, %s, 'STUDENT', %s, TRUE)
                    """,
                    (login_email, pw_hash, data["student_id"])
                )
                login_created = True

        conn.commit()
        if login_created:
            flash(
                f"Student {data['student_name']} ({data['student_id']}) created. "
                f"Login — email: {login_email} • password: Student@1234 • role: Student",
                "success"
            )
        else:
            flash(f"Student {data['student_name']} ({data['student_id']}) created successfully.", "success")
        return redirect(url_for("manage_students"))

    except psycopg2.Error as e:
        app.logger.error("DB error creating student: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while creating student.", "error")
        return redirect(url_for("manage_students"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/students/<student_id>/edit", methods=["GET", "POST"])
@login_required
def student_edit(student_id):
    """
    Edit a student record.
    A STUDENT user can only edit their own record.
    ADMINISTRATOR can edit any student record.
    COMPANY users cannot edit student records (unless demo user).
    """
    is_demo = is_demo_user()

    # Authorization check
    if session.get("role") == "STUDENT" and not is_demo and session.get("student_id") != student_id:
        flash("You can only edit your own student record.", "error")
        return redirect(url_for("student_dashboard"))
    if session.get("role") == "COMPANY":
        flash("Companies do not have permission to edit student records.", "error")
        return redirect(url_for("company_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT dept_id, dept_name FROM department ORDER BY dept_name")
        departments = cur.fetchall()

        cur.execute("SELECT skill_id, skill_name FROM skill ORDER BY skill_name")
        skills = cur.fetchall()

        cur.execute("SELECT * FROM student WHERE student_id = %s", (student_id,))
        student = cur.fetchone()
        if not student:
            flash(f"Student {student_id} not found.", "error")
            return redirect(url_for("manage_students"))

        if request.method == "GET":
            cur.execute("SELECT skill_id FROM student_skill WHERE student_id = %s", (student_id,))
            selected_skill_ids = [r["skill_id"] for r in cur.fetchall()]
            return render_template(
                "student_form.html",
                departments=departments,
                student=student,
                action="edit",
                skills=skills,
                selected_skill_ids=selected_skill_ids
            )

        selected_skill_ids = request.form.getlist("skills")
        errors, data = validate_student_form(request.form)
        # On edit, student_id must match the URL param (prevent ID change)
        if data.get("student_id") != student_id:
            errors.append("Student ID cannot be changed.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "student_form.html",
                departments=departments,
                student=request.form,
                action="edit",
                skills=skills,
                selected_skill_ids=selected_skill_ids
            )

        # Duplicate email check (exclude self)
        if data["student_email"]:
            cur.execute(
                "SELECT 1 FROM student WHERE student_email = %s AND student_id != %s",
                (data["student_email"], student_id)
            )
            if cur.fetchone():
                flash("That email is already registered to another student.", "error")
                return render_template(
                    "student_form.html",
                    departments=departments,
                    student=request.form,
                    action="edit",
                    skills=skills,
                    selected_skill_ids=selected_skill_ids
                )

        cur.execute(
            """
            UPDATE student
               SET student_name  = %s,
                   student_email = %s,
                   student_phone = %s,
                   dept_id       = %s,
                   cgpa          = %s,
                   graduation_yr = %s
             WHERE student_id = %s
            """,
            (data["student_name"], data["student_email"], data["student_phone"],
             data["dept_id"], data["cgpa"], data["graduation_yr"], student_id)
        )

        # Sync skills: add newly selected, remove unselected
        new_skill_set = set(selected_skill_ids)
        if new_skill_set:
            cur.execute("SELECT skill_id FROM skill WHERE skill_id = ANY(%s)", (list(new_skill_set),))
            valid_new_skills = {r["skill_id"] for r in cur.fetchall()}
        else:
            valid_new_skills = set()

        cur.execute("SELECT skill_id FROM student_skill WHERE student_id = %s", (student_id,))
        existing_skills = {r["skill_id"] for r in cur.fetchall()}

        to_remove = existing_skills - valid_new_skills
        to_add = valid_new_skills - existing_skills

        for s_id in to_remove:
            cur.execute(
                "DELETE FROM student_skill WHERE student_id = %s AND skill_id = %s",
                (student_id, s_id)
            )
        for s_id in to_add:
            cur.execute(
                "INSERT INTO student_skill (student_id, skill_id) VALUES (%s, %s)",
                (student_id, s_id)
            )

        conn.commit()

        # Refresh display_name in session if the student edited their own record
        if session.get("role") == "STUDENT" and session.get("student_id") == student_id:
            session["display_name"] = data["student_name"]

        flash(f"Student {data['student_name']} updated successfully.", "success")
        if session.get("role") == "STUDENT" and not is_demo:
            return redirect(url_for("student_dashboard"))
        return redirect(url_for("student_detail", student_id=student_id))

    except psycopg2.Error as e:
        app.logger.error("DB error editing student: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while updating student.", "error")
        return redirect(url_for("manage_students"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/students/<student_id>/delete", methods=["POST"])
@login_required
def student_delete(student_id):
    """
    Delete a student record.
    - Baseline sample students (S1001-S1012) are protected from deletion.
    - Authorized demo workflow and student self-deletion permitted.
    - Dependencies in interview, application, placement, student_skill, users
      are checked and safely cleaned up in order only upon explicit confirmation.
    """
    is_demo = session.get("is_demo", False) or session.get("email", "").lower().startswith("demo.")

    # Authorization check
    if session.get("role") == "STUDENT" and session.get("student_id") != student_id:
        flash("You can only delete your own student record.", "error")
        return redirect(url_for("student_dashboard"))
    if session.get("role") == "COMPANY":
        flash("Companies do not have permission to delete student records.", "error")
        return redirect(url_for("company_dashboard"))

    # Protect baseline sample students
    if student_id in SEEDED_STUDENT_IDS:
        flash(f"Cannot delete baseline student {student_id}. Pre-seeded demonstration records are protected.", "error")
        if session.get("role") == "ADMINISTRATOR":
            return redirect(url_for("manage_students"))
        return redirect(url_for("student_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT student_id, student_name FROM student WHERE student_id = %s", (student_id,))
        student = cur.fetchone()
        if not student:
            flash(f"Student {student_id} not found.", "error")
            return redirect(url_for("manage_students"))
        student_name = student["student_name"]

        # Check child dependencies
        cur.execute("SELECT COUNT(*) AS n FROM application WHERE student_id = %s", (student_id,))
        num_apps = cur.fetchone()["n"]

        cur.execute(
            """
            SELECT COUNT(*) AS n
            FROM   interview i
            JOIN   application a ON i.appl_id = a.appl_id
            WHERE  a.student_id = %s
            """,
            (student_id,)
        )
        num_interviews = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM placement WHERE student_id = %s", (student_id,))
        num_placements = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM student_skill WHERE student_id = %s", (student_id,))
        num_skills = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM users WHERE student_id = %s", (student_id,))
        num_users = cur.fetchone()["n"]

        total_deps = num_apps + num_interviews + num_placements + num_skills + num_users
        confirm_cleanup = request.form.get("confirm_cleanup") in ("1", "true", "yes", True)

        if total_deps > 0 and not confirm_cleanup:
            dep_details = []
            if num_apps: dep_details.append(f"{num_apps} application(s)")
            if num_interviews: dep_details.append(f"{num_interviews} interview(s)")
            if num_placements: dep_details.append(f"{num_placements} placement(s)")
            if num_skills: dep_details.append(f"{num_skills} skill(s)")
            if num_users: dep_details.append(f"{num_users} linked user account(s)")
            deps_summary = ", ".join(dep_details)

            flash(
                f"Cannot delete {student_name} ({student_id}): Associated records exist ({deps_summary}). "
                f"Please confirm removal of associated test records.",
                "warning"
            )
            session["pending_delete_student_id"] = student_id
            session["pending_delete_deps"] = deps_summary
            return redirect(url_for("manage_students"))

        # Explicit confirmation given or no dependencies: delete in strict FK order
        # 1. Interviews
        cur.execute(
            """
            DELETE FROM interview
            WHERE  appl_id IN (SELECT appl_id FROM application WHERE student_id = %s)
            """,
            (student_id,)
        )
        # 2. Applications
        cur.execute("DELETE FROM application WHERE student_id = %s", (student_id,))
        # 3. Placements
        cur.execute("DELETE FROM placement WHERE student_id = %s", (student_id,))
        # 4. Student skills
        cur.execute("DELETE FROM student_skill WHERE student_id = %s", (student_id,))
        # 5. Linked user record
        cur.execute("DELETE FROM users WHERE student_id = %s", (student_id,))
        # 6. Student record
        cur.execute("DELETE FROM student WHERE student_id = %s", (student_id,))
        conn.commit()

        # Clear session pending state
        if session.get("pending_delete_student_id") == student_id:
            session.pop("pending_delete_student_id", None)
            session.pop("pending_delete_deps", None)

        if session.get("demo_view_student_id") == student_id:
            session.pop("demo_view_student_id", None)

        if total_deps > 0:
            flash(
                f"Student {student_name} ({student_id}) and {total_deps} associated test record(s) were successfully deleted.",
                "success"
            )
        else:
            flash(f"Student {student_name} ({student_id}) was successfully deleted.", "success")

        # If logged in as this student and deleted self (and not in demo mode), log out
        if session.get("student_id") == student_id and not is_demo:
            session.clear()
            flash("Your student record was deleted. You have been logged out.", "info")
            return redirect(url_for("login"))

        return redirect(url_for("manage_students"))

    except psycopg2.Error as e:
        app.logger.error("DB error deleting student: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while deleting student.", "error")
        return redirect(url_for("manage_students"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/students/cancel-delete", methods=["GET", "POST"])
@login_required
def cancel_pending_delete():
    session.pop("pending_delete_student_id", None)
    session.pop("pending_delete_deps", None)
    return redirect(url_for("manage_students"))


@app.route("/manage/students/<student_id>")
@login_required
def student_detail(student_id):
    """View a single student's full profile, skills, and application history."""
    if session.get("role") == "STUDENT" and session.get("student_id") != student_id:
        flash("You can only view your own student profile.", "warning")
        return redirect(url_for("student_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        # If Company, verify this student has applied to one of their opportunities
        if session.get("role") == "COMPANY":
            cur.execute(
                """
                SELECT 1 FROM application a
                JOIN opportunity o ON a.opp_id = o.opp_id
                WHERE a.student_id = %s AND o.company_id = %s
                """,
                (student_id, session.get("company_id"))
            )
            if not cur.fetchone():
                flash("You can only review students who have applied to your opportunities.", "warning")
                return redirect(url_for("company_dashboard"))

        cur.execute(
            """
            SELECT s.*, d.dept_name
            FROM   student s
            JOIN   department d ON s.dept_id = d.dept_id
            WHERE  s.student_id = %s
            """,
            (student_id,)
        )
        student = cur.fetchone()
        if not student:
            flash(f"Student {student_id} not found.", "error")
            if session.get("role") == "COMPANY":
                return redirect(url_for("company_dashboard"))
            elif session.get("role") == "STUDENT":
                return redirect(url_for("student_dashboard"))
            return redirect(url_for("manage_students"))

        cur.execute(
            """
            SELECT sk.skill_name
            FROM   student_skill ss
            JOIN   skill sk ON ss.skill_id = sk.skill_id
            WHERE  ss.student_id = %s
            ORDER  BY sk.skill_name
            """,
            (student_id,)
        )
        skills = [r["skill_name"] for r in cur.fetchall()]

        cur.execute(
            """
            SELECT a.appl_id, a.appl_date,
                   o.opp_id, o.opp_title, o.opp_type,
                   c.company_name,
                   COALESCE(i.status, 'PENDING') AS interview_status,
                   i.interview_rd
            FROM   application a
            JOIN   opportunity o  ON a.opp_id    = o.opp_id
            JOIN   company     c  ON o.company_id = c.company_id
            LEFT JOIN interview i ON i.appl_id   = a.appl_id
            WHERE  a.student_id = %s
            ORDER  BY a.appl_date DESC, a.appl_id DESC
            """,
            (student_id,)
        )
        applications = cur.fetchall()
        applied_opp_ids = {a["opp_id"] for a in applications if a.get("opp_id")}

        cur.execute(
            """
            SELECT p.*, c.company_name, o.opp_title
            FROM   placement p
            JOIN   company     c ON p.company_id = c.company_id
            JOIN   opportunity o ON p.opp_id     = o.opp_id
            WHERE  p.student_id = %s
            """,
            (student_id,)
        )
        placement = cur.fetchone()

        # Fetch active opportunities for Apply action
        cur.execute(
            """
            SELECT o.*, c.company_name
            FROM   opportunity o
            JOIN   company c ON o.company_id = c.company_id
            WHERE  o.deadline >= CURRENT_DATE
            ORDER  BY o.deadline ASC
            """
        )
        available_opportunities = cur.fetchall()

        # Check total dependencies
        cur.execute("SELECT COUNT(*) AS n FROM application WHERE student_id = %s", (student_id,))
        num_apps = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM placement WHERE student_id = %s", (student_id,))
        num_plm = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM student_skill WHERE student_id = %s", (student_id,))
        num_skl = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM users WHERE student_id = %s", (student_id,))
        num_usr = cur.fetchone()["n"]
        total_deps = num_apps + num_plm + num_skl + num_usr

        return render_template(
            "student_detail.html",
            student=student,
            skills=skills,
            applications=applications,
            applied_opp_ids=applied_opp_ids,
            placement=placement,
            available_opportunities=available_opportunities,
            total_deps=total_deps,
            is_seeded=student_id in SEEDED_STUDENT_IDS,
        )
    except psycopg2.Error as e:
        app.logger.error("DB error on student detail: %s", e)
        flash("Error loading student details.", "error")
        return redirect(url_for("manage_students"))
    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════════
#  COMPANY MANAGEMENT  (all 10 companies, CRUD)
# ══════════════════════════════════════════════════════════════════

@app.route("/manage/companies")
@login_required
def manage_companies():
    """List ALL companies from DB. Strictly restricted to Administrators."""
    is_demo = is_demo_user()
    if session.get("role") != "ADMINISTRATOR" and not is_demo:
        flash("Access denied: Only administrators can access company management.", "danger")
        return redirect(url_for("student_dashboard" if session.get("role") == "STUDENT" else "company_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        search = request.args.get("q", "").strip()
        locn_filter = request.args.get("locn", "").strip()

        query = """
            SELECT c.*,
                   COUNT(DISTINCT o.opp_id) AS posting_count,
                   COUNT(DISTINCT p.plm_id) AS placement_count
            FROM   company c
            LEFT JOIN opportunity o ON o.company_id = c.company_id
            LEFT JOIN placement   p ON p.company_id = c.company_id
            WHERE  1=1
        """
        params = []
        if search:
            query += " AND (LOWER(c.company_name) LIKE %s OR LOWER(c.company_email) LIKE %s OR c.company_id LIKE %s)"
            like = f"%{search.lower()}%"
            params.extend([like, like, like.upper()])
        if locn_filter:
            query += " AND c.company_locn = %s"
            params.append(locn_filter)

        query += " GROUP BY c.company_id ORDER BY c.company_id"
        cur.execute(query, params)
        companies = cur.fetchall()

        # Distinct locations for filter dropdown
        cur.execute("SELECT DISTINCT company_locn FROM company WHERE company_locn IS NOT NULL ORDER BY company_locn")
        locations = [r["company_locn"] for r in cur.fetchall()]

        return render_template(
            "manage_companies.html",
            companies=companies,
            locations=locations,
            search=search,
            locn_filter=locn_filter,
            total=len(companies),
        )
    except psycopg2.Error as e:
        app.logger.error("DB error listing companies: %s", e)
        flash("Error loading company list.", "error")
        return render_template("manage_companies.html",
                               companies=[], locations=[], search="", locn_filter="", total=0)
    finally:
        if conn:
            conn.close()


@app.route("/manage/companies/new", methods=["GET", "POST"])
@login_required
def company_new():
    """Create a new company record."""
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        if request.method == "GET":
            return render_template("company_form.html", company=None, action="create")

        errors, data = validate_company_form(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("company_form.html", company=request.form, action="create")

        cur.execute("SELECT 1 FROM company WHERE company_id = %s", (data["company_id"],))
        if cur.fetchone():
            flash(f"Company ID {data['company_id']} already exists.", "error")
            return render_template("company_form.html", company=request.form, action="create")

        cur.execute(
            """
            INSERT INTO company
                (company_id, company_name, company_email, company_phone, company_locn)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (data["company_id"], data["company_name"], data["company_email"],
             data["company_phone"], data["company_locn"])
        )
        conn.commit()
        flash(f"Company {data['company_name']} ({data['company_id']}) created.", "success")
        return redirect(url_for("manage_companies"))

    except psycopg2.Error as e:
        app.logger.error("DB error creating company: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while creating company.", "error")
        return redirect(url_for("manage_companies"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/companies/<company_id>/edit", methods=["GET", "POST"])
@login_required
def company_edit(company_id):
    """
    Edit a company record.
    A COMPANY user can only edit their own record.
    ADMINISTRATOR can edit any company record.
    STUDENT is denied access.
    """
    if session["role"] == "STUDENT":
        flash("Students do not have permission to edit company records.", "error")
        return redirect(url_for("student_dashboard"))

    if session["role"] == "COMPANY" and session.get("company_id") != company_id:
        flash("You can only edit your own company record.", "error")
        return redirect(url_for("company_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT * FROM company WHERE company_id = %s", (company_id,))
        company = cur.fetchone()
        if not company:
            flash(f"Company {company_id} not found.", "error")
            return redirect(url_for("company_dashboard" if session["role"] == "COMPANY" else "manage_companies"))

        if request.method == "GET":
            return render_template("company_form.html", company=company, action="edit")

        errors, data = validate_company_form(request.form)
        if data["company_id"] != company_id:
            errors.append("Company ID cannot be changed.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("company_form.html", company=request.form, action="edit")

        cur.execute(
            """
            UPDATE company
               SET company_name  = %s,
                   company_email = %s,
                   company_phone = %s,
                   company_locn  = %s
             WHERE company_id = %s
            """,
            (data["company_name"], data["company_email"],
             data["company_phone"], data["company_locn"], company_id)
        )
        conn.commit()

        if session["role"] == "COMPANY" and session.get("company_id") == company_id:
            session["display_name"] = data["company_name"]

        flash(f"Company {data['company_name']} updated successfully.", "success")
        if session["role"] == "COMPANY":
            return redirect(url_for("company_detail", company_id=company_id))
        return redirect(url_for("manage_companies"))

    except psycopg2.Error as e:
        app.logger.error("DB error editing company: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while updating company.", "error")
        if session["role"] == "COMPANY":
            return redirect(url_for("company_dashboard"))
        return redirect(url_for("manage_companies"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/companies/<company_id>/delete", methods=["POST"])
@login_required
def company_delete(company_id):
    """
    Delete a company record.
    A COMPANY user can only delete their own record.
    ADMINISTRATOR can delete companies without child dependencies.
    STUDENT is denied access.
    """
    if session["role"] == "STUDENT":
        flash("Students do not have permission to delete company records.", "error")
        return redirect(url_for("student_dashboard"))

    if session["role"] == "COMPANY" and session.get("company_id") != company_id:
        flash("You can only delete your own company record.", "error")
        return redirect(url_for("company_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) AS n FROM opportunity WHERE company_id = %s", (company_id,))
        if cur.fetchone()["n"] > 0:
            flash(f"Cannot delete company {company_id}: it has active job postings.", "error")
            return redirect(url_for("manage_companies"))

        cur.execute("SELECT COUNT(*) AS n FROM placement WHERE company_id = %s", (company_id,))
        if cur.fetchone()["n"] > 0:
            flash(f"Cannot delete company {company_id}: it has placement records.", "error")
            return redirect(url_for("manage_companies"))

        cur.execute("SELECT company_name FROM company WHERE company_id = %s", (company_id,))
        row = cur.fetchone()
        if not row:
            flash(f"Company {company_id} not found.", "error")
            return redirect(url_for("manage_companies"))

        name = row["company_name"]
        cur.execute("DELETE FROM company WHERE company_id = %s", (company_id,))
        conn.commit()

        flash(f"Company {name} ({company_id}) deleted.", "info")

        if session["role"] == "COMPANY" and session.get("company_id") == company_id:
            session.clear()
            flash("Your company record was deleted. You have been logged out.", "info")
            return redirect(url_for("login"))

        return redirect(url_for("manage_companies"))

    except psycopg2.Error as e:
        app.logger.error("DB error deleting company: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while deleting company.", "error")
        return redirect(url_for("manage_companies"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/companies/<company_id>")
@login_required
def company_detail(company_id):
    """View a single company's full profile, its postings, and applicants."""
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT * FROM company WHERE company_id = %s", (company_id,))
        company = cur.fetchone()
        if not company:
            flash(f"Company {company_id} not found.", "error")
            return redirect(url_for("manage_companies"))

        cur.execute(
            """
            SELECT o.*,
                   COUNT(DISTINCT a.appl_id) AS applicant_count
            FROM   opportunity o
            LEFT JOIN application a ON a.opp_id = o.opp_id
            WHERE  o.company_id = %s
            GROUP  BY o.opp_id
            ORDER  BY o.deadline ASC
            """,
            (company_id,)
        )
        opportunities = cur.fetchall()

        cur.execute(
            """
            SELECT p.*, s.student_name, o.opp_title
            FROM   placement p
            JOIN   student     s ON p.student_id = s.student_id
            JOIN   opportunity o ON p.opp_id     = o.opp_id
            WHERE  p.company_id = %s
            ORDER  BY p.plm_date DESC
            """,
            (company_id,)
        )
        placements = cur.fetchall()

        # Support optional selected opportunity to view applicants inline
        opp_id = request.args.get("opp_id", "").strip().upper()
        selected_opp = None
        selected_opp_applicants = []
        if opp_id:
            for opp in opportunities:
                if opp["opp_id"] == opp_id:
                    selected_opp = opp
                    break
            if selected_opp:
                cur.execute(
                    """
                    SELECT a.appl_id, a.appl_date,
                           s.student_id, s.student_name, s.student_email, s.student_phone, s.cgpa,
                           d.dept_name,
                           COALESCE(i.status, 'PENDING') AS interview_status,
                           i.interview_date, i.interview_rd
                    FROM   application a
                    JOIN   student     s ON a.student_id = s.student_id
                    LEFT JOIN department d ON s.dept_id    = d.dept_id
                    LEFT JOIN interview  i ON i.appl_id   = a.appl_id
                    WHERE  a.opp_id = %s
                    ORDER  BY a.appl_date DESC, a.appl_id DESC
                    """,
                    (opp_id,)
                )
                selected_opp_applicants = cur.fetchall()

        return render_template(
            "company_detail.html",
            company=company,
            opportunities=opportunities,
            placements=placements,
            selected_opp=selected_opp,
            selected_opp_applicants=selected_opp_applicants,
        )
    except psycopg2.Error as e:
        app.logger.error("DB error on company detail: %s", e)
        flash("Error loading company details.", "error")
        return redirect(url_for("manage_companies"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/opportunities/<opp_id>/applicants")
@login_required
def opportunity_applicants(opp_id):
    """
    View applicants for a specific opportunity.
    Shows student details, application status, and interview info.
    Authorization:
    - STUDENT: Allowed
    - Demo users: Allowed
    - COMPANY: Allowed ONLY for opportunities belonging to their linked company
    """
    opp_id = (opp_id or "").strip().upper()
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        # Fetch opportunity details and company info
        cur.execute(
            """
            SELECT o.*,
                   c.company_name, c.company_locn, c.company_email, c.company_phone
            FROM   opportunity o
            JOIN   company     c ON o.company_id = c.company_id
            WHERE  o.opp_id = %s
            """,
            (opp_id,)
        )
        opportunity = cur.fetchone()
        if not opportunity:
            flash(f"Opportunity {opp_id} not found.", "error")
            return redirect(url_for("company_dashboard" if session.get("role") == "COMPANY" else "student_dashboard" if session.get("role") == "STUDENT" else "manage_opportunities"))

        # Role-based privacy restriction: Students can NEVER view applicant lists
        if session.get("role") == "STUDENT":
            flash("Access denied: Students cannot view applicant lists.", "danger")
            return redirect(url_for("student_dashboard"))

        # Companies can ONLY view their own applicants
        if session.get("role") == "COMPANY":
            if opportunity["company_id"] != session.get("company_id"):
                flash("You only have permission to view applicants for your company's opportunities.", "error")
                return redirect(url_for("company_dashboard"))

        # Fetch other opportunities from same company for quick switcher navigation
        cur.execute(
            """
            SELECT o.opp_id, o.opp_title, o.opp_type, o.opp_locn, o.deadline,
                   COUNT(DISTINCT a.appl_id) AS applicant_count
            FROM   opportunity o
            LEFT JOIN application a ON a.opp_id = o.opp_id
            WHERE  o.company_id = %s
            GROUP  BY o.opp_id
            ORDER  BY o.deadline ASC
            """,
            (opportunity["company_id"],)
        )
        company_opportunities = cur.fetchall()

        # Fetch real applicants for this specific opportunity
        cur.execute(
            """
            SELECT a.appl_id, a.appl_date,
                   s.student_id, s.student_name, s.student_email, s.student_phone,
                   s.cgpa, s.graduation_yr,
                   d.dept_name,
                   COALESCE(i.status, 'PENDING') AS interview_status,
                   i.interview_date, i.interview_rd, i.interview_id
            FROM   application a
            JOIN   student     s ON a.student_id = s.student_id
            LEFT JOIN department d ON s.dept_id    = d.dept_id
            LEFT JOIN interview  i ON i.appl_id   = a.appl_id
            WHERE  a.opp_id = %s
            ORDER  BY a.appl_date DESC, a.appl_id DESC
            """,
            (opp_id,)
        )
        applicants = cur.fetchall()

        return render_template(
            "opportunity_applicants.html",
            opportunity=opportunity,
            company_opportunities=company_opportunities,
            applicants=applicants,
        )
    except psycopg2.Error as e:
        app.logger.error("DB error on opportunity applicants: %s", e)
        flash("Error loading applicant records.", "error")
        return redirect(url_for("manage_companies"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/opportunities/<opp_id>/edit", methods=["GET", "POST"])
@login_required
def opportunity_edit(opp_id):
    """
    Edit a job/internship posting and manage openings.
    - Protected by company role authorization with strict server-side ownership verification.
    - Company can ONLY edit postings belonging to their own company_id.
    - Administrator can edit any posting for platform oversight.
    - Students are denied access.
    - Updates existing database row; never inserts duplicates.
    - Validates positive openings, CGPA bounds, and other fields.
    - Preserves all existing applications, interviews, selections, and placements.
    - Warns gracefully if openings reduced below applicants or selected candidates.
    """
    opp_id = (opp_id or "").strip().upper()
    is_demo = is_demo_user()
    role = session.get("role")

    # 1. Access restriction: Students can NEVER edit postings
    if role == "STUDENT":
        flash("Access denied: Students cannot edit job postings.", "danger")
        return redirect(url_for("student_dashboard"))

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        # 2. Fetch target opportunity with company info
        cur.execute(
            """
            SELECT o.*, c.company_name
            FROM   opportunity o
            JOIN   company c ON o.company_id = c.company_id
            WHERE  o.opp_id = %s
            """,
            (opp_id,)
        )
        opp = cur.fetchone()
        if not opp:
            flash(f"Opportunity {opp_id} not found.", "error")
            return redirect(url_for("company_dashboard" if role == "COMPANY" else "manage_opportunities"))

        # 3. Ownership verification: Companies can ONLY edit their own postings
        if role == "COMPANY" and not is_demo:
            if opp["company_id"] != session.get("company_id"):
                flash("Unauthorized: You do not have permission to edit another company's posting.", "danger")
                return redirect(url_for("company_dashboard"))

        # 4. Fetch pipeline statistics for safety context
        cur.execute("SELECT COUNT(*) AS n FROM application WHERE opp_id = %s", (opp_id,))
        applicant_count = cur.fetchone()["n"]

        cur.execute(
            """
            SELECT COUNT(*) AS n
            FROM   interview i
            JOIN   application a ON i.appl_id = a.appl_id
            WHERE  a.opp_id = %s
            """,
            (opp_id,)
        )
        interview_count = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM placement WHERE opp_id = %s", (opp_id,))
        placed_count = cur.fetchone()["n"]

        stats = {
            "applicants": applicant_count,
            "interviews": interview_count,
            "placed": placed_count,
        }

        # ── GET: render pre-filled edit form ──
        if request.method == "GET":
            return render_template(
                "opportunity_form.html",
                opportunity=opp,
                stats=stats,
                action="edit"
            )

        # ── POST: validate and save updates ──
        errors, data = validate_opportunity_form(request.form)
        if errors:
            for err in errors:
                flash(err, "error")
            # Re-render with user input preserved
            merged_opp = dict(opp)
            merged_opp.update(request.form)
            return render_template(
                "opportunity_form.html",
                opportunity=merged_opp,
                stats=stats,
                action="edit"
            )

        # Safety & business rules check regarding openings:
        # Editing openings must NOT alter or delete existing applications or placements.
        openings_val = data["openings"]
        warning_notes = []
        if openings_val < placed_count:
            warning_notes.append(
                f"Number of openings ({openings_val}) is fewer than candidates already placed ({placed_count}). "
                "All existing placement records and selected students remain intact."
            )
        elif openings_val < applicant_count:
            warning_notes.append(
                f"Number of openings ({openings_val}) is fewer than current applicants ({applicant_count}). "
                f"All {applicant_count} applications remain active in the pipeline."
            )

        # Parameterized UPDATE: modifies existing row only; does NOT insert duplicates
        cur.execute(
            """
            UPDATE opportunity
            SET    opp_title = %s,
                   opp_type  = %s,
                   opp_locn  = %s,
                   stipend   = %s,
                   package   = %s,
                   min_cgpa  = %s,
                   deadline  = %s,
                   openings  = %s
            WHERE  opp_id    = %s
            """,
            (
                data["opp_title"],
                data["opp_type"],
                data["opp_locn"],
                data["stipend"],
                data["package"],
                data["min_cgpa"],
                data["deadline"],
                data["openings"],
                opp_id,
            )
        )
        conn.commit()

        if warning_notes:
            flash(
                f"Job posting '{data['opp_title']}' ({opp_id}) updated successfully. " + " ".join(warning_notes),
                "warning"
            )
        else:
            flash(
                f"Job posting '{data['opp_title']}' ({opp_id}) updated successfully. Openings set to {openings_val}.",
                "success"
            )

        if role == "COMPANY":
            return redirect(url_for("company_dashboard"))
        return redirect(url_for("manage_opportunities"))

    except psycopg2.Error as e:
        app.logger.error("DB error updating opportunity %s: %s", opp_id, e)
        if conn:
            conn.rollback()
        flash("Database error while saving changes to job posting.", "error")
        return redirect(url_for("opportunity_edit", opp_id=opp_id))
    finally:
        if conn:
            conn.close()


# ────────────────── Company Application Management ───────────────

@app.route("/manage/applications/<appl_id>/status", methods=["POST"])
@login_required
def application_set_status(appl_id):
    """
    Update an application's status (IN_PROCESS, REJECTED, CLEARED, PENDING).
    Enforces that COMPANY users only manage their own company's applications.
    """
    is_demo = is_demo_user()
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("""
            SELECT a.appl_id, a.student_id, a.opp_id, o.company_id, o.package, s.student_name, o.opp_title
            FROM application a
            JOIN opportunity o ON a.opp_id = o.opp_id
            JOIN student s ON a.student_id = s.student_id
            WHERE a.appl_id = %s
        """, (appl_id,))
        app_row = cur.fetchone()
        if not app_row:
            flash(f"Application {appl_id} not found.", "error")
            return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

        # Role authorization
        if session.get("role") == "STUDENT":
            flash("Unauthorized action.", "danger")
            return redirect(url_for("student_dashboard"))

        if session.get("role") == "COMPANY":
            if app_row["company_id"] != session.get("company_id"):
                flash("Unauthorized: You can only manage applications for your own company's opportunities.", "danger")
                return redirect(url_for("company_dashboard"))

        status_val = (request.form.get("status") or request.form.get("outcome") or "").strip().upper()
        if status_val not in ["IN_PROCESS", "REJECTED", "CLEARED", "PENDING"]:
            flash(f"Invalid status value: {status_val}", "error")
            return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

        # Update or create interview record
        cur.execute("SELECT interview_id, interview_rd FROM interview WHERE appl_id = %s", (appl_id,))
        existing_int = cur.fetchone()
        if existing_int:
            cur.execute(
                "UPDATE interview SET status = %s WHERE interview_id = %s",
                (status_val, existing_int["interview_id"])
            )
        else:
            cur.execute("""
                SELECT interview_id FROM interview 
                WHERE interview_id ~ '^IN[0-9]+$' 
                ORDER BY CAST(SUBSTRING(interview_id FROM 3) AS INTEGER) DESC 
                LIMIT 1
            """)
            last_int = cur.fetchone()
            next_num = (int(last_int["interview_id"][2:]) + 1) if last_int else 10001
            new_int_id = f"IN{next_num}"
            cur.execute(
                "INSERT INTO interview (interview_id, appl_id, interview_rd, status) VALUES (%s, %s, %s, %s)",
                (new_int_id, appl_id, 1, status_val)
            )

        # Handle placement record sync
        if status_val == "CLEARED":
            cur.execute("SELECT plm_id FROM placement WHERE student_id = %s AND opp_id = %s", (app_row["student_id"], app_row["opp_id"]))
            existing_plm = cur.fetchone()
            if existing_plm:
                cur.execute(
                    "UPDATE placement SET package = %s, plm_date = CURRENT_DATE WHERE plm_id = %s",
                    (app_row["package"], existing_plm["plm_id"])
                )
            else:
                cur.execute("""
                    SELECT plm_id FROM placement 
                    WHERE plm_id ~ '^PL[0-9]+$' 
                    ORDER BY CAST(SUBSTRING(plm_id FROM 3) AS INTEGER) DESC 
                    LIMIT 1
                """)
                last_plm = cur.fetchone()
                next_num = (int(last_plm["plm_id"][2:]) + 1) if last_plm else 10001
                new_plm_id = f"PL{next_num}"
                cur.execute(
                    """
                    INSERT INTO placement (plm_id, student_id, company_id, opp_id, package, plm_date)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
                    """,
                    (new_plm_id, app_row["student_id"], app_row["company_id"], app_row["opp_id"], app_row["package"])
                )
        elif status_val == "REJECTED":
            cur.execute("DELETE FROM placement WHERE student_id = %s AND opp_id = %s", (app_row["student_id"], app_row["opp_id"]))

        conn.commit()
        status_labels = {
            "IN_PROCESS": "kept In Process",
            "REJECTED": "marked as Rejected",
            "CLEARED": "accepted and placed",
            "PENDING": "reset to Pending"
        }
        flash(f"Application for {app_row['student_name']} was {status_labels.get(status_val, status_val)}.", "success")
        return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

    except psycopg2.Error as e:
        app.logger.error("DB error updating application status: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while updating application status.", "error")
        return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/applications/<appl_id>/schedule-interview", methods=["POST"])
@login_required
def application_schedule_interview(appl_id):
    """
    Schedule an interview for a specific application.
    Enforces company ownership and validates dates and rounds.
    """
    is_demo = is_demo_user()
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("""
            SELECT a.appl_id, a.student_id, a.opp_id, o.company_id, s.student_name, o.opp_title
            FROM application a
            JOIN opportunity o ON a.opp_id = o.opp_id
            JOIN student s ON a.student_id = s.student_id
            WHERE a.appl_id = %s
        """, (appl_id,))
        app_row = cur.fetchone()
        if not app_row:
            flash(f"Application {appl_id} not found.", "error")
            return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

        # Role authorization
        if session.get("role") == "STUDENT":
            flash("Unauthorized action.", "danger")
            return redirect(url_for("student_dashboard"))

        if session.get("role") == "COMPANY":
            if app_row["company_id"] != session.get("company_id"):
                flash("Unauthorized: You can only schedule interviews for your own company's opportunities.", "danger")
                return redirect(url_for("company_dashboard"))

        # Form fields
        date_str = request.form.get("interview_date", "").strip()
        time_str = request.form.get("interview_time", "").strip() or "10:00"
        rd_str = request.form.get("interview_rd", "").strip() or "1"

        if not date_str:
            flash("Interview date is required.", "error")
            return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

        try:
            interview_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                interview_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "error")
                return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

        try:
            interview_rd = int(rd_str)
            if interview_rd < 1:
                raise ValueError
        except ValueError:
            flash("Interview round must be a positive number.", "error")
            return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

        # Upsert into interview
        cur.execute("SELECT interview_id FROM interview WHERE appl_id = %s", (appl_id,))
        existing_int = cur.fetchone()
        if existing_int:
            cur.execute(
                """
                UPDATE interview 
                SET interview_date = %s, interview_rd = %s, status = 'SCHEDULED'
                WHERE interview_id = %s
                """,
                (interview_dt, interview_rd, existing_int["interview_id"])
            )
        else:
            cur.execute("""
                SELECT interview_id FROM interview 
                WHERE interview_id ~ '^IN[0-9]+$' 
                ORDER BY CAST(SUBSTRING(interview_id FROM 3) AS INTEGER) DESC 
                LIMIT 1
            """)
            last_int = cur.fetchone()
            next_num = (int(last_int["interview_id"][2:]) + 1) if last_int else 10001
            new_int_id = f"IN{next_num}"
            cur.execute(
                """
                INSERT INTO interview (interview_id, appl_id, interview_date, interview_rd, status)
                VALUES (%s, %s, %s, %s, 'SCHEDULED')
                """,
                (new_int_id, appl_id, interview_dt, interview_rd)
            )

        conn.commit()
        formatted_dt = interview_dt.strftime("%d %b %Y at %I:%M %p")
        flash(f"Round {interview_rd} interview scheduled for {app_row['student_name']} on {formatted_dt}.", "success")
        return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

    except psycopg2.Error as e:
        app.logger.error("DB error scheduling interview: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while scheduling interview.", "error")
        return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/applications/<appl_id>/select", methods=["POST"])
@login_required
def application_select_candidate(appl_id):
    """
    Accept/select candidate: sets interview status to CLEARED and records placement.
    Enforces company ownership and prevents duplicate placements.
    """
    is_demo = is_demo_user()
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("""
            SELECT a.appl_id, a.student_id, a.opp_id, o.company_id, o.package, s.student_name, o.opp_title
            FROM application a
            JOIN opportunity o ON a.opp_id = o.opp_id
            JOIN student s ON a.student_id = s.student_id
            WHERE a.appl_id = %s
        """, (appl_id,))
        app_row = cur.fetchone()
        if not app_row:
            flash(f"Application {appl_id} not found.", "error")
            return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

        # Role authorization
        if session.get("role") == "STUDENT":
            flash("Unauthorized action.", "danger")
            return redirect(url_for("student_dashboard"))

        if session.get("role") == "COMPANY":
            if app_row["company_id"] != session.get("company_id"):
                flash("Unauthorized: You can only select candidates for your own company's opportunities.", "danger")
                return redirect(url_for("company_dashboard"))

        # Custom package or fallback to opp package
        pkg_input = request.form.get("package", "").strip()
        if pkg_input:
            try:
                package_val = float(pkg_input)
            except ValueError:
                package_val = app_row["package"]
        else:
            package_val = app_row["package"]

        # Update interview status to CLEARED
        cur.execute("SELECT interview_id, interview_rd FROM interview WHERE appl_id = %s", (appl_id,))
        existing_int = cur.fetchone()
        if existing_int:
            cur.execute(
                "UPDATE interview SET status = 'CLEARED' WHERE interview_id = %s",
                (existing_int["interview_id"],)
            )
        else:
            cur.execute("""
                SELECT interview_id FROM interview 
                WHERE interview_id ~ '^IN[0-9]+$' 
                ORDER BY CAST(SUBSTRING(interview_id FROM 3) AS INTEGER) DESC 
                LIMIT 1
            """)
            last_int = cur.fetchone()
            next_num = (int(last_int["interview_id"][2:]) + 1) if last_int else 10001
            new_int_id = f"IN{next_num}"
            cur.execute(
                "INSERT INTO interview (interview_id, appl_id, interview_rd, status) VALUES (%s, %s, %s, 'CLEARED')",
                (new_int_id, appl_id, 1)
            )

        # Upsert placement
        cur.execute("SELECT plm_id FROM placement WHERE student_id = %s AND opp_id = %s", (app_row["student_id"], app_row["opp_id"]))
        existing_plm = cur.fetchone()
        if existing_plm:
            cur.execute(
                "UPDATE placement SET package = %s, plm_date = CURRENT_DATE WHERE plm_id = %s",
                (package_val, existing_plm["plm_id"])
            )
            plm_id = existing_plm["plm_id"]
        else:
            cur.execute("""
                SELECT plm_id FROM placement 
                WHERE plm_id ~ '^PL[0-9]+$' 
                ORDER BY CAST(SUBSTRING(plm_id FROM 3) AS INTEGER) DESC 
                LIMIT 1
            """)
            last_plm = cur.fetchone()
            next_num = (int(last_plm["plm_id"][2:]) + 1) if last_plm else 10001
            new_plm_id = f"PL{next_num}"
            cur.execute(
                """
                INSERT INTO placement (plm_id, student_id, company_id, opp_id, package, plm_date)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
                """,
                (new_plm_id, app_row["student_id"], app_row["company_id"], app_row["opp_id"], package_val)
            )
            plm_id = new_plm_id

        conn.commit()
        flash(f"Candidate {app_row['student_name']} successfully selected! Placement record {plm_id} created.", "success")
        return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))

    except psycopg2.Error as e:
        app.logger.error("DB error selecting candidate: %s", e)
        if conn:
            conn.rollback()
        flash("Database error while recording candidate selection.", "error")
        return redirect(request.form.get("redirect_to") or url_for("company_dashboard"))
    finally:
        if conn:
            conn.close()


@app.route("/manage/applications/<appl_id>/outcome", methods=["POST"])
@login_required
def application_record_outcome(appl_id):
    """
    Record interview outcome (CLEARED, REJECTED, SCHEDULED, IN_PROCESS).
    """
    outcome = (request.form.get("outcome") or request.form.get("status") or "").strip().upper()
    if outcome == "CLEARED":
        return application_select_candidate(appl_id)
    elif outcome == "SCHEDULED":
        return application_schedule_interview(appl_id)
    else:
        return application_set_status(appl_id)


# ────────────────────── Admin Dashboard & Management ─────────────

@app.route("/admin/dashboard")
@role_required("ADMINISTRATOR")
def admin_dashboard():
    """Administrator dashboard — overview with links to manage students,
    companies, and opportunities."""
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) AS cnt FROM student")
        student_count = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM company")
        company_count = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM opportunity")
        opp_count = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM application")
        app_count = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM placement")
        placement_count = cur.fetchone()["cnt"]

        cur.execute("""
            SELECT sk.skill_name, COUNT(ss.student_id) AS student_count
            FROM skill sk
            LEFT JOIN student_skill ss ON sk.skill_id = ss.skill_id
            GROUP BY sk.skill_id, sk.skill_name
            ORDER BY student_count DESC, sk.skill_name
            LIMIT 6;
        """)
        top_skills = cur.fetchall()

        return render_template(
            "admin_dashboard.html",
            student_count=student_count,
            company_count=company_count,
            opp_count=opp_count,
            app_count=app_count,
            placement_count=placement_count,
            top_skills=top_skills,
        )
    except psycopg2.Error as e:
        app.logger.error("DB error on admin dashboard: %s", e)
        flash("Error loading dashboard data.", "error")
        return render_template("admin_dashboard.html",
                               student_count=0, company_count=0,
                               opp_count=0, app_count=0, placement_count=0,
                               top_skills=[])
    finally:
        if conn:
            conn.close()


@app.route("/manage/opportunities")
@role_required("ADMINISTRATOR")
def manage_opportunities():
    """List all opportunities across all companies for administrator oversight."""
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("""
            SELECT o.*, c.company_name, COUNT(DISTINCT a.appl_id) AS applicant_count
            FROM opportunity o
            JOIN company c ON o.company_id = c.company_id
            LEFT JOIN application a ON o.opp_id = a.opp_id
            GROUP BY o.opp_id, c.company_name
            ORDER BY o.opp_id
        """)
        opportunities = cur.fetchall()

        return render_template("manage_opportunities.html", opportunities=opportunities)
    except psycopg2.Error as e:
        app.logger.error("DB error listing opportunities: %s", e)
        flash("Error loading opportunities list.", "error")
        return render_template("manage_opportunities.html", opportunities=[])
    finally:
        if conn:
            conn.close()


@app.route("/manage/applications")
@role_required("ADMINISTRATOR")
def manage_applications():
    """List all student applications across all opportunities for administrator oversight."""
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("""
            SELECT a.appl_id, a.appl_date, a.opp_id,
                   s.student_id, s.student_name, s.cgpa,
                   d.dept_name,
                   c.company_name, o.opp_title, o.opp_type,
                   COALESCE(i.status, 'PENDING') AS interview_status,
                   i.interview_date, i.interview_rd
            FROM application a
            JOIN student s ON a.student_id = s.student_id
            JOIN department d ON s.dept_id = d.dept_id
            JOIN opportunity o ON a.opp_id = o.opp_id
            JOIN company c ON o.company_id = c.company_id
            LEFT JOIN interview i ON i.appl_id = a.appl_id
            ORDER BY a.appl_date DESC, a.appl_id DESC
        """)
        applications = cur.fetchall()

        return render_template("manage_applications.html", applications=applications)
    except psycopg2.Error as e:
        app.logger.error("DB error listing applications: %s", e)
        flash("Error loading applications list.", "error")
        return render_template("manage_applications.html", applications=[])
    finally:
        if conn:
            conn.close()


@app.route("/manage/interviews-placements")
@role_required("ADMINISTRATOR")
def manage_interviews_placements():
    """List all interviews and placements for administrator oversight."""
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("""
            SELECT i.*, a.student_id, s.student_name, o.opp_title, c.company_name
            FROM interview i
            JOIN application a ON i.appl_id = a.appl_id
            JOIN student s ON a.student_id = s.student_id
            JOIN opportunity o ON a.opp_id = o.opp_id
            JOIN company c ON o.company_id = c.company_id
            ORDER BY i.interview_date DESC NULLS LAST
        """)
        interviews = cur.fetchall()

        cur.execute("""
            SELECT p.*, s.student_name, s.student_email, c.company_name, o.opp_title
            FROM placement p
            JOIN student s ON p.student_id = s.student_id
            JOIN company c ON p.company_id = c.company_id
            JOIN opportunity o ON p.opp_id = o.opp_id
            ORDER BY p.plm_date DESC
        """)
        placements = cur.fetchall()

        return render_template(
            "manage_interviews_placements.html",
            interviews=interviews,
            placements=placements
        )
    except psycopg2.Error as e:
        app.logger.error("DB error listing interviews/placements: %s", e)
        flash("Error loading pipeline data.", "error")
        return render_template("manage_interviews_placements.html", interviews=[], placements=[])
    finally:
        if conn:
            conn.close()


# ────────────────────── Compatibility API Routes ─────────────────

@app.get("/api/health")
def api_health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return jsonify({"ok": True, "database": "PostgreSQL"})
    except Exception as e:
        app.logger.exception("Database health check failed: %s", e)
        return jsonify({"ok": False, "error": "Cannot connect to PostgreSQL."}), 503

@app.get("/api/departments")
def api_departments():
    if not session.get("user_id"):
        return jsonify({"error": "Authentication required"}), 401
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT dept_id, dept_name FROM department ORDER BY dept_id")
        rows = cur.fetchall()
        conn.close()
        return jsonify({
            "source": "PostgreSQL",
            "count": len(rows),
            "departments": [{"dept_id": row["dept_id"], "dept_name": row["dept_name"]} for row in rows],
        })
    except Exception as e:
        app.logger.exception("Could not load department records: %s", e)
        return jsonify({"error": "Could not load departments."}), 503

@app.post("/api/login")
def api_login():
    data = request.get_json() or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    role_input = data.get("role", "").upper().strip()
    if not email or not password or not role_input:
        return jsonify({"error": "Invalid input"}), 400
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, email, password_hash, role, is_active, student_id, company_id FROM users WHERE email = %s",
            (email,)
        )
        user = cur.fetchone()
        if not user or not user["is_active"] or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid credentials"}), 401
        if user["role"] != role_input:
            return jsonify({"error": "Role mismatch"}), 403
        session.clear()
        session["user_id"] = user["user_id"]
        session["email"] = user["email"]
        session["role"] = user["role"]
        session["student_id"] = user["student_id"]
        session["company_id"] = user["company_id"]
        return jsonify({"message": "Logged in", "user_id": user["user_id"], "role": user["role"]})
    except Exception as e:
        app.logger.exception("Login failed: %s", e)
        return jsonify({"error": "Login failed"}), 500
    finally:
        if conn:
            conn.close()

@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.get("/api/me")
def api_me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT email, role, created_at FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"user_id": user_id, "email": row["email"], "role": row["role"], "created_at": row["created_at"].isoformat() if row["created_at"] else None})
    except Exception as e:
        app.logger.exception("Failed to fetch user: %s", e)
        return jsonify({"error": "Failed to fetch user"}), 500
    finally:
        if conn:
            conn.close()


# ─────────────────────────── Run ─────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

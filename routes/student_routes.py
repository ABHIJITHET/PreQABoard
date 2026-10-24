from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory
)

from database.db_connection import get_connection

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from ai.openai_client import ai_generate

# ======================= (ADDED) ===========================
import os
from datetime import date

# (ADDED) repeated questions helpers
import re
import json
from difflib import SequenceMatcher

from utils.pdf_text import extract_pdf_text
# ===========================================================


# ===========================================================
# STUDENT BLUEPRINT
# ===========================================================

student_bp = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


# ======================= (ADDED) ===========================
# UPLOAD FOLDERS (same structure as your project)
QUESTION_PAPER_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "question_papers")
STUDY_MATERIAL_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "study_materials")
SYLLABUS_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "syllabus")

# (ADDED) for answer keys download in student module
ANSWER_KEY_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "answer_keys")
# ===========================================================


# ======================= (ADDED) ===========================
def student_required():
    return "student_id" in session


def auto_upgrade_semester_if_needed(cursor, student):
    """
    Auto-upgrade semester based on semester.end_date entered by HOD.
    Uses existing semester table (no new table).

    student dict must contain: student_id, course_id, semester_id
    Returns: (new_semester_id, upgraded_bool)
    """

    cursor.execute("""
        SELECT
            semester_number,
            end_date
        FROM semester
        WHERE semester_id = %s
          AND course_id = %s
        LIMIT 1
    """, (
        student["semester_id"],
        student["course_id"]
    ))
    sem = cursor.fetchone()

    if not sem:
        return student["semester_id"], False

    if not sem["end_date"]:
        return student["semester_id"], False

    if date.today() <= sem["end_date"]:
        return student["semester_id"], False

    next_semester_number = sem["semester_number"] + 1

    cursor.execute("""
        SELECT semester_id
        FROM semester
        WHERE course_id = %s
          AND semester_number = %s
          AND status = 'Active'
        LIMIT 1
    """, (
        student["course_id"],
        next_semester_number
    ))
    next_sem = cursor.fetchone()

    if not next_sem:
        return student["semester_id"], False

    next_semester_id = next_sem["semester_id"]

    cursor.execute("""
        UPDATE student
        SET
            semester_id = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE student_id = %s
    """, (
        next_semester_id,
        student["student_id"]
    ))

    student["semester_id"] = next_semester_id
    return next_semester_id, True
# ===========================================================


# ======================= (ADDED) ===========================
# REPEATED QUESTIONS HELPERS
def _normalize_question(q: str) -> str:
    q = (q or "").strip().lower()
    q = re.sub(r"\b\d+\s*marks?\b", " ", q, flags=re.I)
    q = re.sub(r"\(\s*\d+\s*marks?\s*\)", " ", q, flags=re.I)
    q = re.sub(r"\bor\b", " ", q, flags=re.I)
    q = re.sub(r"[^a-z0-9\s]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def _looks_like_question(s: str) -> bool:
    if not s:
        return False
    if s.endswith("?"):
        return True
    return bool(re.search(
        r"\b(define|explain|describe|discuss|write|derive|prove|compare|differentiate|"
        r"algorithm|advantages|disadvantages|what|why|how|short note|architecture|threats|"
        r"security|life\s*cycle|gateway|fog|coap|mqtt|anomaly)\b",
        s,
        flags=re.I
    ))


def _extract_candidate_questions(text: str):
    """
    Extract question-like sentences from question paper text.
    Handles multi-line questions by joining lines until next question-number line.
    """
    if not text:
        return []

    text = text.replace("\u00a0", " ")
    lines = [ln.strip() for ln in re.split(r"[\r\n]+", text) if (ln or "").strip()]

    skip_words = [
        "university", "time", "hours", "instructions", "note",
        "maximum marks", "model question paper", "department",
        "section", "part a", "part b", "part c", "answer all",
        "choose", "internal choice"
    ]

    # Common question numbering patterns
    start_re = re.compile(
        r"^\s*(?:Q\.?\s*)?(?:QUESTION\s*)?\d+\s*[\).:-]\s*|^\s*QUESTION\s*\d+\s*[:.-]?\s*",
        flags=re.I
    )

    # Sometimes sub-questions like (a), (b)
    sub_re = re.compile(r"^\s*\(?[a-d]\)?\s*[\).:-]\s*", flags=re.I)

    questions = []
    current = ""

    def _should_skip(line: str) -> bool:
        if not line:
            return True
        upper = line.upper()
        if any(w.upper() in upper for w in skip_words):
            return True
        if len(line) < 8:
            return True
        if re.fullmatch(r"[-_]{3,}", line):
            return True
        if line.strip().upper() in ("OR", "AND", "******"):
            return True
        return False

    def _push_current():
        nonlocal current
        if not current:
            return
        cleaned = current.strip()
        cleaned = re.sub(r"\(\s*\d+\s*marks?\s*\)", "", cleaned, flags=re.I).strip()
        cleaned = re.sub(r"\b\d+\s*marks?\b", "", cleaned, flags=re.I).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if 12 <= len(cleaned) <= 420 and _looks_like_question(cleaned):
            questions.append(cleaned)
        current = ""

    for line in lines:
        if _should_skip(line):
            continue

        # If new question starts
        if start_re.search(line):
            _push_current()
            line2 = start_re.sub("", line).strip()
            line2 = sub_re.sub("", line2).strip()
            current = line2
            continue

        # If sub-question starts while we already are in a question, treat as new question too
        if sub_re.search(line) and current:
            _push_current()
            line2 = sub_re.sub("", line).strip()
            current = line2
            continue

        # Continuation line
        if current:
            # Avoid appending obvious headers
            if not _should_skip(line):
                current = (current + " " + line).strip()
        else:
            # Sometimes PDF extraction loses numbering; treat standalone question-like lines
            if 12 <= len(line) <= 260 and _looks_like_question(line):
                questions.append(line)

    _push_current()

    # Deduplicate by normalized form
    uniq = []
    seen = set()
    for q in questions:
        n = _normalize_question(q)
        if len(n) < 12:
            continue
        if n in seen:
            continue
        seen.add(n)
        uniq.append(q)

    return uniq


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # quick containment boost for near-equal questions
    if len(a) >= 18 and len(b) >= 18 and (a in b or b in a):
        return 0.93
    return SequenceMatcher(None, a, b).ratio()


def _cluster_questions(question_items, threshold_short=0.90, threshold_long=0.84):
    """
    question_items: list of dicts:
      { "paper_id": int, "question": str, "norm": str }

    returns clusters: list of dicts:
      {
        "rep_norm": str,
        "rep_text": str,
        "paper_ids": set(int),
        "variants": [str]
      }
    """
    clusters = []

    for item in question_items:
        norm = item["norm"]
        qtext = item["question"]
        pid = item["paper_id"]

        placed = False
        for c in clusters:
            base = c["rep_norm"]
            min_len = min(len(base), len(norm))
            thr = threshold_short if min_len < 60 else threshold_long

            sim = _similarity(base, norm)
            if sim >= thr:
                c["paper_ids"].add(pid)
                if len(c["variants"]) < 6 and qtext not in c["variants"]:
                    c["variants"].append(qtext)
                placed = True
                break

        if not placed:
            clusters.append({
                "rep_norm": norm,
                "rep_text": qtext,
                "paper_ids": {pid},
                "variants": [qtext]
            })

    return clusters


def _importance_score(rep_text: str, paper_count: int) -> float:
    t = (rep_text or "").lower()
    score = (paper_count * 10.0) + (min(len(rep_text or ""), 260) / 60.0)

    keyword_boost = [
        "architecture", "reference", "security", "threat", "fog", "gateway",
        "coap", "mqtt", "anomaly", "life cycle", "stream", "advantages",
        "compare", "differentiate", "explain", "describe", "discuss"
    ]
    for kw in keyword_boost:
        if kw in t:
            score += 1.2

    # Prefer full/meaningful questions
    if "write short note" in t:
        score -= 0.5

    return score
# ===========================================================


# ===========================================================
# 1. STUDENT REGISTRATION
# ===========================================================

@student_bp.route("/register", methods=["GET", "POST"])
def register():

    # =======================================================
    # GET - SHOW REGISTRATION PAGE
    # =======================================================

    if request.method == "GET":

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            # ------------------------------------------------
            # GET ACTIVE DEPARTMENTS
            # ------------------------------------------------

            cursor.execute("""
                SELECT
                    department_id,
                    department_name
                FROM department
                WHERE status = 'Active'
                ORDER BY department_name
            """)

            departments = cursor.fetchall()


            # ------------------------------------------------
            # GET ACTIVE COURSES
            # ------------------------------------------------

            cursor.execute("""
                SELECT
                    course_id,
                    department_id,
                    course_name
                FROM course
                WHERE status = 'Active'
                ORDER BY course_name
            """)

            courses = cursor.fetchall()


            # ------------------------------------------------
            # GET ACTIVE SEMESTERS
            # ------------------------------------------------

            cursor.execute("""
                SELECT
                    semester_id,
                    course_id,
                    semester_number
                FROM semester
                WHERE status = 'Active'
                ORDER BY
                    course_id,
                    semester_number
            """)

            semesters = cursor.fetchall()


            # ------------------------------------------------
            # SHOW REGISTRATION PAGE
            # ------------------------------------------------

            return render_template(
                "login/student_register.html",
                departments=departments,
                courses=courses,
                semesters=semesters
            )


        except Exception as e:

            return f"""
                <h2>Database Error</h2>
                <p>{e}</p>
            """


        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()


    # =======================================================
    # POST - GET FORM DATA
    # =======================================================

    department_id = request.form.get(
        "department_id"
    )

    course_id = request.form.get(
        "course_id"
    )

    semester_id = request.form.get(
        "semester_id"
    )

    register_number = request.form.get(
        "register_number",
        ""
    ).strip()

    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # =======================================================
    # VALIDATE REQUIRED FIELDS
    # =======================================================

    if (
        not department_id
        or not course_id
        or not semester_id
        or not register_number
        or not full_name
        or not email
        or not username
        or not password
        or not confirm_password
    ):

        flash(
            "All required fields must be filled.",
            "error"
        )

        return redirect(
            url_for("student.register")
        )


    # =======================================================
    # CHECK PASSWORD
    # =======================================================

    if password != confirm_password:

        flash(
            "Passwords do not match.",
            "error"
        )

        return redirect(
            url_for("student.register")
        )


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()


        # ===================================================
        # VERIFY DEPARTMENT
        # ===================================================

        cursor.execute("""
            SELECT
                department_id
            FROM department
            WHERE department_id = %s
              AND status = 'Active'
        """, (
            department_id,
        ))

        valid_department = cursor.fetchone()


        if not valid_department:

            flash(
                "Invalid department selected.",
                "error"
            )

            return redirect(
                url_for("student.register")
            )


        # ===================================================
        # VERIFY COURSE BELONGS TO DEPARTMENT
        # ===================================================

        cursor.execute("""
            SELECT
                course_id
            FROM course
            WHERE course_id = %s
              AND department_id = %s
              AND status = 'Active'
        """, (
            course_id,
            department_id
        ))

        valid_course = cursor.fetchone()


        if not valid_course:

            flash(
                "Invalid course selected for the department.",
                "error"
            )

            return redirect(
                url_for("student.register")
            )


        # ===================================================
        # VERIFY SEMESTER BELONGS TO COURSE
        # ===================================================

        cursor.execute("""
            SELECT
                semester_id
            FROM semester
            WHERE semester_id = %s
              AND course_id = %s
              AND status = 'Active'
        """, (
            semester_id,
            course_id
        ))

        valid_semester = cursor.fetchone()


        if not valid_semester:

            flash(
                "Invalid semester selected for the course.",
                "error"
            )

            return redirect(
                url_for("student.register")
            )


        # ===================================================
        # CHECK REGISTER NUMBER
        # ===================================================

        cursor.execute("""
            SELECT
                student_id
            FROM student
            WHERE register_number = %s
        """, (
            register_number,
        ))

        if cursor.fetchone():

            flash(
                "Register number already exists.",
                "error"
            )

            return redirect(
                url_for("student.register")
            )


        # ===================================================
        # CHECK EMAIL
        # ===================================================

        cursor.execute("""
            SELECT
                student_id
            FROM student
            WHERE email = %s
        """, (
            email,
        ))

        if cursor.fetchone():

            flash(
                "Email address is already registered.",
                "error"
            )

            return redirect(
                url_for("student.register")
            )


        # ===================================================
        # CHECK USERNAME
        # ===================================================

        cursor.execute("""
            SELECT
                student_id
            FROM student
            WHERE username = %s
        """, (
            username,
        ))

        if cursor.fetchone():

            flash(
                "Username is already taken.",
                "error"
            )

            return redirect(
                url_for("student.register")
            )


        # ===================================================
        # HASH PASSWORD
        # ===================================================

        hashed_password = generate_password_hash(
            password
        )


        # ===================================================
        # INSERT STUDENT
        #
        # approval_status -> Pending
        # account_status  -> Pending
        # ===================================================

        cursor.execute("""
            INSERT INTO student
            (
                department_id,
                course_id,
                semester_id,
                register_number,
                full_name,
                email,
                phone,
                username,
                password,
                approval_status,
                account_status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'Pending',
                'Pending'
            )
        """, (
            department_id,
            course_id,
            semester_id,
            register_number,
            full_name,
            email,
            phone,
            username,
            hashed_password
        ))


        # ===================================================
        # COMMIT
        # ===================================================

        connection.commit()


        # ===================================================
        # SUCCESS
        # ===================================================

        flash(
            "Registration successful. "
            "Your account is waiting for approval.",
            "success"
        )


        return redirect(
            url_for("student.login")
        )


    except Exception as e:

        if connection:
            connection.rollback()

        return f"""
            <h2>Database Error</h2>
            <p>{e}</p>
        """


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 2. STUDENT LOGIN
# ===========================================================

@student_bp.route("/login", methods=["GET", "POST"])
def login():

    # =======================================================
    # GET
    # =======================================================

    if request.method == "GET":

        return render_template(
            "login/student_login.html"
        )


    # =======================================================
    # POST
    # =======================================================

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )


    # =======================================================
    # VALIDATE
    # =======================================================

    if not username or not password:

        flash(
            "Please enter username and password.",
            "error"
        )

        return redirect(
            url_for("student.login")
        )


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()


        # ===================================================
        # FIND STUDENT
        # ===================================================

        cursor.execute("""
            SELECT
                student_id,
                department_id,
                course_id,
                semester_id,
                register_number,
                full_name,
                email,
                phone,
                username,
                password,
                approval_status,
                account_status
            FROM student
            WHERE username = %s
        """, (
            username,
        ))

        student = cursor.fetchone()


        # ===================================================
        # USERNAME CHECK
        # ===================================================

        if not student:

            flash(
                "Invalid username or password.",
                "error"
            )

            return redirect(
                url_for("student.login")
            )


        # ===================================================
        # PASSWORD CHECK
        # ===================================================

        if not check_password_hash(
            student["password"],
            password
        ):

            flash(
                "Invalid username or password.",
                "error"
            )

            return redirect(
                url_for("student.login")
            )


        # ===================================================
        # APPROVAL STATUS
        # ===================================================

        if student["approval_status"] == "Pending":

            flash(
                "Your account is waiting for HOD approval.",
                "error"
            )

            return redirect(
                url_for("student.login")
            )


        if student["approval_status"] == "Rejected":

            flash(
                "Your registration has been rejected by the HOD.",
                "error"
            )

            return redirect(
                url_for("student.login")
            )


        # ===================================================
        # ACCOUNT STATUS
        # ===================================================

        if student["account_status"] == "Inactive":

            flash(
                "Your student account is inactive.",
                "error"
            )

            return redirect(
                url_for("student.login")
            )


        # ===================================================
        # ACCOUNT MUST BE ACTIVE
        # =======================================================

        if student["account_status"] != "Active":

            flash(
                "Your account is not active.",
                "error"
            )

            return redirect(
                url_for("student.login")
            )


        # ======================= (ADDED) ===================
        # AUTO UPGRADE SEMESTER BASED ON semester.end_date
        new_semester_id, upgraded = auto_upgrade_semester_if_needed(cursor, student)
        if upgraded:
            connection.commit()
        # ===================================================


        # ===================================================
        # CREATE SESSION
        # ===================================================

        session.clear()


        session["student_id"] = (
            student["student_id"]
        )

        session["student_username"] = (
            student["username"]
        )

        session["student_name"] = (
            student["full_name"]
        )

        session["student_register_number"] = (
            student["register_number"]
        )

        session["student_department_id"] = (
            student["department_id"]
        )

        session["student_course_id"] = (
            student["course_id"]
        )

        session["student_semester_id"] = (
            student["semester_id"]
        )

        session["role"] = "student"


        # ===================================================
        # LOGIN SUCCESS
        # ===================================================

        flash(
            "Login successful.",
            "success"
        )


        # ===================================================
        # REDIRECT TO DASHBOARD (EDITED)
        # ===================================================

        return redirect(
            url_for("student.dashboard")
        )


    except Exception as e:

        return f"""
            <h2>Database Error</h2>
            <p>{e}</p>
        """


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 2.1 STUDENT DASHBOARD (ADDED)
# ===========================================================

@student_bp.route("/dashboard")
def dashboard():

    if "student_id" not in session:

        flash(
            "Please login to continue.",
            "error"
        )

        return redirect(
            url_for("student.login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ======================= (ADDED) ===================
        # AUTO UPGRADE AGAIN ON DASHBOARD
        temp_student = {
            "student_id": session["student_id"],
            "course_id": session["student_course_id"],
            "semester_id": session["student_semester_id"]
        }

        new_semester_id, upgraded = auto_upgrade_semester_if_needed(cursor, temp_student)
        if upgraded:
            connection.commit()
            session["student_semester_id"] = new_semester_id
        # ===================================================

        # ---------------------------------------------------
        # STUDENT INFO (includes semester dates)
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                st.student_id,
                st.register_number,
                st.full_name,
                st.email,
                st.phone,
                c.course_name,
                sem.semester_number,
                sem.start_date,
                sem.end_date
            FROM student st
            INNER JOIN course c
                ON st.course_id = c.course_id
            INNER JOIN semester sem
                ON st.semester_id = sem.semester_id
            WHERE st.student_id = %s
        """, (
            session["student_id"],
        ))

        student = cursor.fetchone()

        # ---------------------------------------------------
        # SUBJECTS FOR STUDENT COURSE + SEMESTER
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                subject_id,
                subject_code,
                subject_name
            FROM subject
            WHERE course_id = %s
              AND semester_id = %s
              AND status = 'Active'
            ORDER BY subject_name
        """, (
            session["student_course_id"],
            session["student_semester_id"]
        ))

        subjects = cursor.fetchall()

        return render_template(
            "student/dashboard.html",
            student=student,
            subjects=subjects
        )

    except Exception as e:

        return f"""
            <h2>Database Error</h2>
            <p>{e}</p>
        """

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 4) STUDENT - SYLLABUS LIST
# ===========================================================

@student_bp.route("/syllabus")
def syllabus():

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                s.syllabus_id,
                s.title,
                s.file_name,
                s.file_path,
                s.uploaded_at,
                ay.academic_year_name
            FROM syllabus s
            INNER JOIN academic_year ay
                ON s.academic_year_id = ay.academic_year_id
            WHERE s.status = 'Active'
              AND s.department_id = %s
              AND s.course_id = %s
            ORDER BY s.uploaded_at DESC
        """, (
            session["student_department_id"],
            session["student_course_id"]
        ))

        syllabi = cursor.fetchall()

        return render_template(
            "student/syllabus.html",
            syllabi=syllabi
        )

    except Exception as e:
        return f"Database Error: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@student_bp.route("/syllabus/download/<int:syllabus_id>")
def download_syllabus(syllabus_id):

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                syllabus_id,
                file_name,
                file_path
            FROM syllabus
            WHERE syllabus_id = %s
              AND status = 'Active'
              AND department_id = %s
              AND course_id = %s
        """, (
            syllabus_id,
            session["student_department_id"],
            session["student_course_id"]
        ))

        row = cursor.fetchone()
        if not row:
            return "Syllabus not found or not authorized."

        filename = os.path.basename(row["file_path"])
        actual_file = os.path.join(SYLLABUS_UPLOAD_FOLDER, filename)

        if not os.path.exists(actual_file):
            return "Syllabus file not found on server."

        return send_from_directory(
            SYLLABUS_UPLOAD_FOLDER,
            filename,
            as_attachment=True,
            download_name=row["file_name"]
        )

    except Exception as e:
        return f"Error downloading syllabus: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ===========================================================
# 5) STUDENT - QUESTION PAPERS
# ===========================================================

@student_bp.route("/question-papers")
def question_papers():

    if not student_required():
        return redirect(url_for("student.login"))

    subject_id = request.args.get("subject_id", "").strip()
    academic_year_id = request.args.get("academic_year_id", "").strip()
    exam_type_id = request.args.get("exam_type_id", "").strip()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # subjects for student course+semester
        cursor.execute("""
            SELECT subject_id, subject_code, subject_name
            FROM subject
            WHERE course_id=%s AND semester_id=%s AND status='Active'
            ORDER BY subject_name
        """, (session["student_course_id"], session["student_semester_id"]))
        subjects = cursor.fetchall()

        # academic years
        cursor.execute("""
            SELECT academic_year_id, academic_year_name, status
            FROM academic_year
            ORDER BY start_date DESC
        """)
        academic_years = cursor.fetchall()

        # exam types
        cursor.execute("""
            SELECT exam_type_id, exam_type_name
            FROM exam_type
            WHERE status='Active'
            ORDER BY exam_type_name
        """)
        exam_types = cursor.fetchall()

        query = """
            SELECT
                qp.question_paper_id,
                qp.title,
                qp.file_name,
                qp.upload_date,
                ay.academic_year_name,
                et.exam_type_name,
                s.subject_id,
                s.subject_code,
                s.subject_name
            FROM question_paper qp
            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id
            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id
            INNER JOIN academic_year ay
                ON qp.academic_year_id = ay.academic_year_id
            INNER JOIN exam_type et
                ON qp.exam_type_id = et.exam_type_id
            WHERE qp.approved_by_hod = 1
              AND s.course_id = %s
              AND s.semester_id = %s
        """
        params = [session["student_course_id"], session["student_semester_id"]]

        if subject_id:
            query += " AND s.subject_id = %s "
            params.append(subject_id)

        if academic_year_id:
            query += " AND qp.academic_year_id = %s "
            params.append(academic_year_id)

        if exam_type_id:
            query += " AND qp.exam_type_id = %s "
            params.append(exam_type_id)

        query += " ORDER BY qp.upload_date DESC "

        cursor.execute(query, tuple(params))
        papers = cursor.fetchall()

        return render_template(
            "student/search_question_papers.html",
            subjects=subjects,
            academic_years=academic_years,
            exam_types=exam_types,
            papers=papers,
            selected_subject_id=subject_id,
            selected_academic_year_id=academic_year_id,
            selected_exam_type_id=exam_type_id
        )

    except Exception as e:
        return f"Database Error: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@student_bp.route("/question-papers/download/<int:question_paper_id>")
def download_question_paper(question_paper_id):

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                qp.question_paper_id,
                qp.file_name
            FROM question_paper qp
            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id
            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id
            WHERE qp.question_paper_id = %s
              AND qp.approved_by_hod = 1
              AND s.course_id = %s
              AND s.semester_id = %s
        """, (
            question_paper_id,
            session["student_course_id"],
            session["student_semester_id"]
        ))

        row = cursor.fetchone()
        if not row:
            return "Question paper not found or not authorized."

        filename = os.path.basename(row["file_name"])
        actual_file = os.path.join(QUESTION_PAPER_UPLOAD_FOLDER, filename)

        if not os.path.exists(actual_file):
            return "Question paper file not found on server."

        return send_from_directory(
            QUESTION_PAPER_UPLOAD_FOLDER,
            filename,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return f"Error downloading question paper: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ===========================================================
# 6) STUDENT - STUDY MATERIALS
# ===========================================================

@student_bp.route("/study-materials")
def study_materials():

    if not student_required():
        return redirect(url_for("student.login"))

    subject_id = request.args.get("subject_id", "").strip()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # subjects for filter dropdown
        cursor.execute("""
            SELECT subject_id, subject_code, subject_name
            FROM subject
            WHERE course_id=%s AND semester_id=%s AND status='Active'
            ORDER BY subject_name
        """, (session["student_course_id"], session["student_semester_id"]))
        subjects = cursor.fetchall()

        query = """
            SELECT
                sm.study_material_id,
                sm.title,
                sm.file_name,
                sm.upload_date,
                s.subject_id,
                s.subject_code,
                s.subject_name
            FROM study_material sm
            INNER JOIN teacher_subject_assignment tsa
                ON sm.assignment_id = tsa.assignment_id
            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id
            WHERE sm.approved_by_hod = 1
              AND s.course_id = %s
              AND s.semester_id = %s
        """
        params = [session["student_course_id"], session["student_semester_id"]]

        if subject_id:
            query += " AND s.subject_id = %s "
            params.append(subject_id)

        query += " ORDER BY sm.upload_date DESC "

        cursor.execute(query, tuple(params))
        materials = cursor.fetchall()

        return render_template(
            "student/study_materials.html",
            subjects=subjects,
            materials=materials,
            selected_subject_id=subject_id
        )

    except Exception as e:
        return f"Database Error: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@student_bp.route("/study-materials/download/<int:study_material_id>")
def download_study_material(study_material_id):

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                sm.study_material_id,
                sm.file_name
            FROM study_material sm
            INNER JOIN teacher_subject_assignment tsa
                ON sm.assignment_id = tsa.assignment_id
            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id
            WHERE sm.study_material_id = %s
              AND sm.approved_by_hod = 1
              AND s.course_id = %s
              AND s.semester_id = %s
        """, (
            study_material_id,
            session["student_course_id"],
            session["student_semester_id"]
        ))

        row = cursor.fetchone()
        if not row:
            return "Study material not found or not authorized."

        filename = os.path.basename(row["file_name"])
        actual_file = os.path.join(STUDY_MATERIAL_UPLOAD_FOLDER, filename)

        if not os.path.exists(actual_file):
            return "Study material file not found on server."

        return send_from_directory(
            STUDY_MATERIAL_UPLOAD_FOLDER,
            filename,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return f"Error downloading study material: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ===========================================================
# 7) STUDENT - DOUBTS (POST + VIEW)
# ===========================================================

@student_bp.route("/doubts")
def my_doubts():

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                d.doubt_id,
                d.doubt_title,
                d.doubt_description,
                d.created_at,
                s.subject_code,
                s.subject_name,
                (
                    SELECT COUNT(*)
                    FROM teacher_reply tr
                    WHERE tr.doubt_id = d.doubt_id
                ) AS reply_count
            FROM student_doubt d
            INNER JOIN subject s
                ON d.subject_id = s.subject_id
            WHERE d.student_id = %s
            ORDER BY d.created_at DESC
        """, (session["student_id"],))

        doubts = cursor.fetchall()

        return render_template(
            "student/my_doubts.html",
            doubts=doubts
        )

    except Exception as e:
        return f"Database Error: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@student_bp.route("/doubts/post", methods=["GET", "POST"])
def post_doubt():

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # subjects list
        cursor.execute("""
            SELECT subject_id, subject_code, subject_name
            FROM subject
            WHERE course_id=%s AND semester_id=%s AND status='Active'
            ORDER BY subject_name
        """, (session["student_course_id"], session["student_semester_id"]))
        subjects = cursor.fetchall()

        if request.method == "GET":
            return render_template(
                "student/post_doubt.html",
                subjects=subjects
            )

        subject_id = request.form.get("subject_id")
        doubt_title = request.form.get("doubt_title", "").strip()
        doubt_description = request.form.get("doubt_description", "").strip()

        if not subject_id or not doubt_description:
            return render_template(
                "student/post_doubt.html",
                subjects=subjects,
                error="Subject and doubt description are required."
            )

        # verify subject belongs to this student course+semester
        cursor.execute("""
            SELECT subject_id, subject_code, subject_name
            FROM subject
            WHERE subject_id=%s
              AND course_id=%s
              AND semester_id=%s
              AND status='Active'
        """, (subject_id, session["student_course_id"], session["student_semester_id"]))
        subject_row = cursor.fetchone()

        if not subject_row:
            return render_template(
                "student/post_doubt.html",
                subjects=subjects,
                error="Invalid subject selection."
            )

        # ------------------------------
        # INSERT DOUBT
        # ------------------------------
        cursor.execute("""
            INSERT INTO student_doubt
            (student_id, subject_id, doubt_title, doubt_description)
            VALUES (%s, %s, %s, %s)
        """, (
            session["student_id"],
            subject_id,
            doubt_title,
            doubt_description
        ))

        doubt_id = cursor.lastrowid
        connection.commit()

        # ------------------------------
        # (ADDED) AUTO AI REPLY
        # ------------------------------
        ai_reply_text = None
        model_used = "gpt-4o-mini"

        try:
            # Fetch latest active syllabus extracted text for this student course+dept
            cursor.execute("""
                SELECT extracted_text
                FROM syllabus
                WHERE status='Active'
                  AND department_id=%s
                  AND course_id=%s
                ORDER BY uploaded_at DESC
                LIMIT 1
            """, (
                session["student_department_id"],
                session["student_course_id"]
            ))
            syl = cursor.fetchone()

            syllabus_text = (syl["extracted_text"] if syl and syl.get("extracted_text") else "")
            syllabus_text = syllabus_text.strip()

            # Keep context limited (avoid token overflow)
            if len(syllabus_text) > 12000:
                syllabus_text = syllabus_text[:12000]

            system_text = (
                "You are an exam-oriented academic assistant for a college question bank system.\n"
                "Answer the student's doubt clearly and correctly.\n"
                "Use ONLY the syllabus context given below. If the doubt is not covered in the syllabus, say:\n"
                "\"Not covered in the syllabus.\"\n"
                "Do not invent topics outside the syllabus.\n\n"
                "SYLLABUS CONTEXT:\n"
                f"{syllabus_text if syllabus_text else '[No syllabus text available]'}"
            )

            user_text = (
                f"Subject: {subject_row['subject_code']} - {subject_row['subject_name']}\n"
                f"Doubt Title: {doubt_title}\n"
                f"Doubt: {doubt_description}"
            )

            ai_reply_text = ai_generate(system_text, user_text, model=model_used)

            if ai_reply_text:
                cursor.execute("""
                    INSERT INTO ai_doubt_reply (doubt_id, reply, model)
                    VALUES (%s, %s, %s)
                """, (doubt_id, ai_reply_text, model_used))
                connection.commit()

        except Exception:
            # If AI fails, we still keep the doubt saved
            if connection:
                connection.rollback()

        flash("Doubt posted successfully.", "success")

        # Redirect to view page so student immediately sees AI reply + teacher replies
        return redirect(url_for("student.view_doubt", doubt_id=doubt_id))

    except Exception as e:
        if connection:
            connection.rollback()
        return f"Database Error: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@student_bp.route("/doubts/view/<int:doubt_id>")
def view_doubt(doubt_id):

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                d.doubt_id,
                d.doubt_title,
                d.doubt_description,
                d.created_at,
                s.subject_code,
                s.subject_name
            FROM student_doubt d
            INNER JOIN subject s
                ON d.subject_id = s.subject_id
            WHERE d.doubt_id = %s
              AND d.student_id = %s
        """, (doubt_id, session["student_id"]))

        doubt = cursor.fetchone()
        if not doubt:
            return "Doubt not found or not authorized."

        # (ADDED) AI reply
        cursor.execute("""
            SELECT reply, model, created_at
            FROM ai_doubt_reply
            WHERE doubt_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (doubt_id,))
        ai_reply = cursor.fetchone()

        # Teacher replies
        cursor.execute("""
            SELECT
                tr.reply_id,
                tr.reply,
                tr.replied_at,
                t.full_name AS teacher_name,
                t.employee_id
            FROM teacher_reply tr
            INNER JOIN teacher t
                ON tr.teacher_id = t.teacher_id
            WHERE tr.doubt_id = %s
            ORDER BY tr.replied_at ASC
        """, (doubt_id,))

        replies = cursor.fetchall()

        return render_template(
            "student/view_doubt.html",
            doubt=doubt,
            replies=replies,
            ai_reply=ai_reply
        )

    except Exception as e:
        return f"Database Error: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ===========================================================
# ======================= (ADDED ROUTES) =====================
# PROFILE / TEACHER ANSWERS / AI CHAT / REPEATED QUESTIONS /
# QUESTION PAPER VIEW
# ===========================================================

@student_bp.route("/profile")
def profile():

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                st.student_id,
                st.register_number,
                st.full_name,
                st.email,
                st.phone,
                st.username,
                st.approval_status,
                st.account_status,
                d.department_name,
                c.course_name,
                sem.semester_number
            FROM student st
            INNER JOIN department d
                ON st.department_id = d.department_id
            INNER JOIN course c
                ON st.course_id = c.course_id
            INNER JOIN semester sem
                ON st.semester_id = sem.semester_id
            WHERE st.student_id = %s
        """, (session["student_id"],))

        student = cursor.fetchone()

        return render_template(
            "student/profile.html",
            student=student
        )

    except Exception as e:
        return render_template(
            "student/profile.html",
            student=None,
            error=f"Database Error: {e}"
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@student_bp.route("/teacher-answers")
def teacher_answers():

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                ak.answer_key_id,
                ak.file_name,
                ak.upload_date,

                qp.title AS paper_title,

                ay.academic_year_name,
                et.exam_type_name,

                s.subject_code,
                s.subject_name

            FROM answer_key ak

            INNER JOIN question_paper qp
                ON ak.question_paper_id = qp.question_paper_id

            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN academic_year ay
                ON qp.academic_year_id = ay.academic_year_id

            INNER JOIN exam_type et
                ON qp.exam_type_id = et.exam_type_id

            WHERE qp.approved_by_hod = 1
              AND s.course_id = %s
              AND s.semester_id = %s

            ORDER BY ak.upload_date DESC
        """, (
            session["student_course_id"],
            session["student_semester_id"]
        ))

        answer_keys = cursor.fetchall()

        return render_template(
            "student/teacher_answers.html",
            answer_keys=answer_keys
        )

    except Exception as e:
        return render_template(
            "student/teacher_answers.html",
            answer_keys=[],
            error=f"Database Error: {e}"
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@student_bp.route("/teacher-answers/download/<int:answer_key_id>")
def download_teacher_answer(answer_key_id):

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                ak.answer_key_id,
                ak.file_name
            FROM answer_key ak

            INNER JOIN question_paper qp
                ON ak.question_paper_id = qp.question_paper_id

            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            WHERE ak.answer_key_id = %s
              AND qp.approved_by_hod = 1
              AND s.course_id = %s
              AND s.semester_id = %s
        """, (
            answer_key_id,
            session["student_course_id"],
            session["student_semester_id"]
        ))

        row = cursor.fetchone()
        if not row:
            return "Answer key not found or not authorized."

        filename = os.path.basename(row["file_name"])
        actual_file = os.path.join(ANSWER_KEY_UPLOAD_FOLDER, filename)

        if not os.path.exists(actual_file):
            return "Answer key file not found on server."

        return send_from_directory(
            ANSWER_KEY_UPLOAD_FOLDER,
            filename,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return f"Error downloading answer key: {e}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ===========================================================
# AI CHAT (STUDENT) - USING OPENAI API KEY
# ===========================================================

@student_bp.route("/ai-chat", methods=["GET", "POST"])
def ai_chat():

    if not student_required():
        return redirect(url_for("student.login"))

    # Clear chat
    if request.args.get("clear") == "1":
        session.pop("ai_chat_messages", None)
        return redirect(url_for("student.ai_chat"))

    if "ai_chat_messages" not in session:
        session["ai_chat_messages"] = []

    if request.method == "POST":

        msg = request.form.get("message", "").strip()

        if msg:

            # Add student message to session history
            messages = session["ai_chat_messages"]
            messages.append({
                "role": "student",
                "content": msg
            })

            # Build syllabus-based context (optional but recommended)
            connection = None
            cursor = None

            syllabus_text = ""

            try:
                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute("""
                    SELECT extracted_text
                    FROM syllabus
                    WHERE status='Active'
                      AND department_id=%s
                      AND course_id=%s
                    ORDER BY uploaded_at DESC
                    LIMIT 1
                """, (
                    session["student_department_id"],
                    session["student_course_id"]
                ))

                syl = cursor.fetchone()
                syllabus_text = (syl["extracted_text"] if syl and syl.get("extracted_text") else "").strip()

            except Exception:
                syllabus_text = ""

            finally:
                if cursor:
                    cursor.close()
                if connection:
                    connection.close()

            # Limit context size
            if len(syllabus_text) > 12000:
                syllabus_text = syllabus_text[:12000]

            system_text = (
                "You are an exam-oriented academic assistant for a college system.\n"
                "Use ONLY the syllabus context provided below.\n"
                "If the student's question is not covered in the syllabus, say: \"Not covered in the syllabus.\"\n\n"
                "SYLLABUS CONTEXT:\n"
                f"{syllabus_text if syllabus_text else '[No syllabus text available]'}"
            )

            # Use last few messages as conversation context
            last_msgs = messages[-10:]
            conversation = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in last_msgs])

            user_text = (
                "Continue the conversation and answer the last STUDENT message.\n\n"
                f"{conversation}"
            )

            try:
                reply = ai_generate(system_text, user_text, model="gpt-4o-mini")
            except Exception as e:
                reply = f"AI Error: {e}"

            messages.append({
                "role": "assistant",
                "content": reply
            })

            session["ai_chat_messages"] = messages
            session.modified = True

    return render_template(
        "student/ai_chat.html",
        messages=session.get("ai_chat_messages", [])
    )


# ===========================================================
# (UPDATED) REPEATED QUESTIONS + IMPORTANT QUESTIONS (AI + PDF EXTRACTION)
# ===========================================================

@student_bp.route("/repeated-questions", methods=["GET", "POST"])
def repeated_questions():

    if not student_required():
        return redirect(url_for("student.login"))

    selected_subject_id = ""
    groups = []
    important_questions = []
    ai_output = ""
    used_papers = 0

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT subject_id, subject_code, subject_name
            FROM subject
            WHERE course_id=%s AND semester_id=%s AND status='Active'
            ORDER BY subject_name
        """, (
            session["student_course_id"],
            session["student_semester_id"]
        ))
        subjects = cursor.fetchall()

        if request.method == "GET":
            subject_id = request.args.get("subject_id", "").strip()
            return render_template(
                "student/repeated_questions.html",
                subjects=subjects,
                selected_subject_id=subject_id,
                groups=[],
                important_questions=[],
                ai_output="",
                used_papers=0
            )

        # POST
        selected_subject_id = (request.form.get("subject_id") or "").strip()
        limit_papers = int((request.form.get("limit_papers") or "8").strip() or 8)
        if limit_papers < 1:
            limit_papers = 1
        if limit_papers > 15:
            limit_papers = 15

        if not selected_subject_id:
            return render_template(
                "student/repeated_questions.html",
                subjects=subjects,
                selected_subject_id="",
                groups=[],
                important_questions=[],
                ai_output="",
                used_papers=0,
                error="Please select a subject."
            )

        # verify subject belongs to this student course+semester
        cursor.execute("""
            SELECT subject_id, subject_code, subject_name
            FROM subject
            WHERE subject_id=%s
              AND course_id=%s
              AND semester_id=%s
              AND status='Active'
        """, (
            selected_subject_id,
            session["student_course_id"],
            session["student_semester_id"]
        ))
        subject_row = cursor.fetchone()

        if not subject_row:
            return render_template(
                "student/repeated_questions.html",
                subjects=subjects,
                selected_subject_id=selected_subject_id,
                groups=[],
                important_questions=[],
                ai_output="",
                used_papers=0,
                error="Invalid subject selection."
            )

        # fetch approved papers for this subject (latest N)
        cursor.execute("""
            SELECT
                qp.question_paper_id,
                qp.title,
                qp.file_name,
                qp.upload_date,
                qp.extracted_text,
                qp.extraction_status
            FROM question_paper qp
            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id
            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id
            WHERE s.subject_id = %s
              AND s.course_id = %s
              AND s.semester_id = %s
              AND qp.approved_by_hod = 1
            ORDER BY qp.upload_date DESC
            LIMIT %s
        """, (
            selected_subject_id,
            session["student_course_id"],
            session["student_semester_id"],
            limit_papers
        ))

        papers = cursor.fetchall() or []
        used_papers = len(papers)

        if used_papers == 0:
            return render_template(
                "student/repeated_questions.html",
                subjects=subjects,
                selected_subject_id=selected_subject_id,
                groups=[],
                important_questions=[],
                ai_output="",
                used_papers=0,
                error="No approved question papers found for this subject."
            )

        # ---------------------------------------------------
        # Ensure extracted_text exists; extract on-demand (cache into DB)
        # Build question_items list: [{paper_id, question, norm}]
        # ---------------------------------------------------
        question_items = []
        extracted_ok = 0

        for p in papers:
            text = (p.get("extracted_text") or "").strip()
            status = (p.get("extraction_status") or "").strip()

            if (not text) or (status != "Done"):
                filename = os.path.basename(p.get("file_name") or "")
                pdf_path = os.path.join(QUESTION_PAPER_UPLOAD_FOLDER, filename)

                extracted = ""
                st = "Failed"

                if filename and os.path.exists(pdf_path):
                    try:
                        extracted = extract_pdf_text(pdf_path) or ""
                        st = "Done" if len(extracted.strip()) > 50 else "Failed"
                    except Exception:
                        extracted = ""
                        st = "Failed"

                # cache into DB
                cursor.execute("""
                    UPDATE question_paper
                    SET
                        extracted_text = %s,
                        extraction_status = %s,
                        extracted_at = NOW()
                    WHERE question_paper_id = %s
                """, (
                    extracted,
                    st,
                    p["question_paper_id"]
                ))
                connection.commit()

                text = extracted if st == "Done" else ""
                status = st

            if status == "Done" and len(text.strip()) > 50:
                extracted_ok += 1

            # Extract candidate questions from this paper
            paper_questions = _extract_candidate_questions(text)

            # Avoid duplicates within same paper
            seen_norms = set()
            for q in paper_questions:
                n = _normalize_question(q)
                if len(n) < 12:
                    continue
                if n in seen_norms:
                    continue
                seen_norms.add(n)
                question_items.append({
                    "paper_id": p["question_paper_id"],
                    "question": q,
                    "norm": n
                })

        if extracted_ok == 0 or len(question_items) == 0:
            return render_template(
                "student/repeated_questions.html",
                subjects=subjects,
                selected_subject_id=selected_subject_id,
                groups=[],
                important_questions=[],
                ai_output="No readable text could be extracted from the selected PDFs. If your PDFs are scanned images, please upload text-based PDFs.",
                used_papers=used_papers,
                error="Text extraction failed for the selected papers."
            )

        # ---------------------------------------------------
        # Cluster similar questions (fuzzy) and count per-paper occurrence
        # ---------------------------------------------------
        clusters = _cluster_questions(question_items)

        # Prepare repeated list (repeated across papers, not within same paper)
        repeated_list = []
        all_cluster_list = []

        for c in clusters:
            paper_count = len(c["paper_ids"])
            rep_text = c["rep_text"]
            all_cluster_list.append({
                "question": rep_text,
                "count": paper_count
            })
            if paper_count >= 2:
                repeated_list.append({
                    "question": rep_text,
                    "count": paper_count
                })

        repeated_list.sort(key=lambda x: (-x["count"], x["question"]))
        all_cluster_list.sort(key=lambda x: (-x["count"], x["question"]))

        # build groups by count for UI
        by_count = {}
        for item in repeated_list:
            by_count.setdefault(item["count"], []).append(item["question"])

        groups = []
        for count in sorted(by_count.keys(), reverse=True):
            groups.append({
                "title": f"Repeated {count} times",
                "questions": by_count[count][:25]
            })

        # ---------------------------------------------------
        # Important questions: pick top candidates (includes repeated + some single-appearance high-value)
        # ---------------------------------------------------
        scored = []
        for item in all_cluster_list:
            scored.append((
                _importance_score(item["question"], item["count"]),
                item["question"]
            ))
        scored.sort(key=lambda x: x[0], reverse=True)

        # Top 15 candidates, then limit to 10 for display
        important_candidates = []
        seen_imp = set()
        for _, q in scored:
            n = _normalize_question(q)
            if n in seen_imp:
                continue
            seen_imp.add(n)
            important_candidates.append(q)
            if len(important_candidates) >= 15:
                break

        important_questions = important_candidates[:10]

        # ---------------------------------------------------
        # Syllabus context (prefer same semester, else fallback course)
        # ---------------------------------------------------
        syllabus_text = ""

        try:
            cursor.execute("""
                SELECT extracted_text
                FROM syllabus
                WHERE status='Active'
                  AND extraction_status='Done'
                  AND department_id=%s
                  AND course_id=%s
                  AND semester_id=%s
                ORDER BY uploaded_at DESC
                LIMIT 1
            """, (
                session["student_department_id"],
                session["student_course_id"],
                session["student_semester_id"]
            ))
            syl = cursor.fetchone()

            if not syl:
                cursor.execute("""
                    SELECT extracted_text
                    FROM syllabus
                    WHERE status='Active'
                      AND extraction_status='Done'
                      AND department_id=%s
                      AND course_id=%s
                    ORDER BY uploaded_at DESC
                    LIMIT 1
                """, (
                    session["student_department_id"],
                    session["student_course_id"]
                ))
                syl = cursor.fetchone()

            syllabus_text = (syl["extracted_text"] if syl and syl.get("extracted_text") else "").strip()

        except Exception:
            syllabus_text = ""

        if len(syllabus_text) > 8000:
            syllabus_text = syllabus_text[:8000]

        # ---------------------------------------------------
        # AI formatting (Repeated + Important) - DO NOT invent questions
        # ---------------------------------------------------
        system_text = (
            "You are an exam-oriented academic assistant.\n"
            "You will receive:\n"
            "1) a list of repeated questions with counts (count = number of papers it appeared in)\n"
            "2) a list of important-question candidates\n"
            "Use ONLY these lists. Do NOT add new questions.\n"
            "Output format strictly:\n"
            "REPEATED QUESTIONS:\n"
            "1. <question> (x<count>)\n"
            "...\n"
            "\n"
            "IMPORTANT QUESTIONS:\n"
            "1. <question>\n"
            "...\n"
            "\n"
            "If repeated list is empty, write: REPEATED QUESTIONS: None\n"
            "Keep questions concise but do not change meaning.\n\n"
            "SYLLABUS CONTEXT (optional relevance filter):\n"
            f"{syllabus_text if syllabus_text else '[No syllabus text available]'}"
        )

        user_text = (
            f"Subject: {subject_row['subject_code']} - {subject_row['subject_name']}\n"
            f"Used Papers: {used_papers}\n\n"
            "Repeated questions (JSON):\n"
            + json.dumps(repeated_list[:30], ensure_ascii=False, indent=2)
            + "\n\n"
            "Important question candidates (JSON):\n"
            + json.dumps(important_candidates[:15], ensure_ascii=False, indent=2)
        )

        try:
            ai_output = ai_generate(system_text, user_text, model="gpt-4o-mini")
        except Exception as e:
            ai_output = f"AI Error: {e}"

        if not repeated_list:
            # still show something if no repeats
            if not ai_output or ai_output.startswith("AI Error"):
                ai_output = "REPEATED QUESTIONS:\nNone\n\nIMPORTANT QUESTIONS:\n" + "\n".join(
                    [f"{i+1}. {q}" for i, q in enumerate(important_questions)]
                )

        return render_template(
            "student/repeated_questions.html",
            subjects=subjects,
            selected_subject_id=selected_subject_id,
            groups=groups,
            important_questions=important_questions,
            ai_output=ai_output,
            used_papers=used_papers
        )

    except Exception as e:
        return render_template(
            "student/repeated_questions.html",
            subjects=[],
            selected_subject_id=selected_subject_id,
            groups=[],
            important_questions=[],
            ai_output="",
            used_papers=0,
            error=f"Database Error: {e}"
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@student_bp.route("/question-papers/view/<int:question_paper_id>")
def question_paper_view(question_paper_id):

    if not student_required():
        return redirect(url_for("student.login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                qp.question_paper_id,
                qp.title,
                qp.file_name,
                qp.upload_date,
                ay.academic_year_name,
                et.exam_type_name,
                s.subject_code,
                s.subject_name
            FROM question_paper qp
            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id
            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id
            INNER JOIN academic_year ay
                ON qp.academic_year_id = ay.academic_year_id
            INNER JOIN exam_type et
                ON qp.exam_type_id = et.exam_type_id
            WHERE qp.question_paper_id = %s
              AND qp.approved_by_hod = 1
              AND s.course_id = %s
              AND s.semester_id = %s
        """, (
            question_paper_id,
            session["student_course_id"],
            session["student_semester_id"]
        ))

        paper = cursor.fetchone()
        if not paper:
            return render_template(
                "student/question_paper_view.html",
                paper=None,
                answer_keys=[],
                error="Question paper not found or not authorized."
            )

        cursor.execute("""
            SELECT
                answer_key_id,
                file_name,
                upload_date
            FROM answer_key
            WHERE question_paper_id = %s
            ORDER BY upload_date DESC
        """, (question_paper_id,))
        answer_keys = cursor.fetchall()

        return render_template(
            "student/question_paper_view.html",
            paper=paper,
            answer_keys=answer_keys
        )

    except Exception as e:
        return render_template(
            "student/question_paper_view.html",
            paper=None,
            answer_keys=[],
            error=f"Database Error: {e}"
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# ===========================================================
# ===================== (END ADDED ROUTES) ===================
# ===========================================================


# ===========================================================
# 3. STUDENT LOGOUT
# ===========================================================

@student_bp.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("student.login")
    )
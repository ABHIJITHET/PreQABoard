from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request
)

from database.db_connection import get_connection

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from werkzeug.utils import secure_filename

import os


teacher_bp = Blueprint(
    "teacher",
    __name__
)


# ===========================================================
# COMMON TEACHER LOGIN CHECK
# ===========================================================

def teacher_required():

    if "teacher_id" not in session:

        return redirect(
            url_for("auth.teacher_login")
        )

    return None


# ===========================================================
# 1. TEACHER DASHBOARD
# ===========================================================

@teacher_bp.route("/teacher/dashboard")
def dashboard():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET TEACHER DETAILS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT
                teacher_id,
                employee_id,
                full_name,
                email,
                phone,
                username,
                department_id,
                account_status,
                created_at

            FROM teacher

            WHERE teacher_id = %s
            """,
            (teacher_id,)
        )

        teacher = cursor.fetchone()

        if not teacher:

            session.clear()

            return redirect(
                url_for("auth.teacher_login")
            )

        # ---------------------------------------------------
        # COUNT ACTIVE SUBJECTS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total

            FROM teacher_subject_assignment

            WHERE teacher_id = %s
              AND status = 'Active'
            """,
            (teacher_id,)
        )

        result = cursor.fetchone()

        total_subjects = result["total"]

        # ---------------------------------------------------
        # COUNT QUESTION PAPERS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total

            FROM question_paper

            WHERE uploaded_by = %s
            """,
            (teacher_id,)
        )

        result = cursor.fetchone()

        total_question_papers = result["total"]

        # ---------------------------------------------------
        # COUNT STUDY MATERIALS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total

            FROM study_material

            WHERE uploaded_by = %s
            """,
            (teacher_id,)
        )

        result = cursor.fetchone()

        total_study_materials = result["total"]

        # ---------------------------------------------------
        # COUNT ANSWER KEYS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total

            FROM answer_key

            WHERE uploaded_by = %s
            """,
            (teacher_id,)
        )

        result = cursor.fetchone()

        total_answer_keys = result["total"]

        # ---------------------------------------------------
        # COUNT STUDENT DOUBTS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(DISTINCT sd.doubt_id) AS total

            FROM student_doubt sd

            INNER JOIN teacher_subject_assignment tsa
                ON sd.subject_id = tsa.subject_id

            WHERE tsa.teacher_id = %s
              AND tsa.status = 'Active'
            """,
            (teacher_id,)
        )

        result = cursor.fetchone()

        total_doubts = result["total"]

        return render_template(
            "teacher/dashboard.html",
            teacher=teacher,
            total_subjects=total_subjects,
            total_question_papers=total_question_papers,
            total_study_materials=total_study_materials,
            total_answer_keys=total_answer_keys,
            total_doubts=total_doubts
        )

    except Exception as e:

        return render_template(
            "teacher/dashboard.html",
            teacher=None,
            total_subjects=0,
            total_question_papers=0,
            total_study_materials=0,
            total_answer_keys=0,
            total_doubts=0,
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 2. TEACHER PROFILE
# ===========================================================

@teacher_bp.route("/teacher/profile")
def profile():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                t.teacher_id,
                t.employee_id,
                t.full_name,
                t.email,
                t.phone,
                t.username,
                t.account_status,
                t.created_at,
                d.department_name

            FROM teacher t

            LEFT JOIN department d
                ON t.department_id = d.department_id

            WHERE t.teacher_id = %s
            """,
            (teacher_id,)
        )

        teacher = cursor.fetchone()

        if not teacher:

            session.clear()

            return redirect(
                url_for("auth.teacher_login")
            )

        return render_template(
            "teacher/profile.html",
            teacher=teacher
        )

    except Exception as e:

        return render_template(
            "teacher/profile.html",
            teacher=None,
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 3. TEACHER CHANGE PASSWORD
# ===========================================================

@teacher_bp.route(
    "/teacher/change-password",
    methods=["GET", "POST"]
)
def change_password():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if (
            not current_password
            or not new_password
            or not confirm_password
        ):

            return render_template(
                "teacher/change_password.html",
                error="Please fill in all fields."
            )

        if new_password != confirm_password:

            return render_template(
                "teacher/change_password.html",
                error="New passwords do not match."
            )

        if current_password == new_password:

            return render_template(
                "teacher/change_password.html",
                error=(
                    "New password must be different "
                    "from your current password."
                )
            )

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT password

                FROM teacher

                WHERE teacher_id = %s
                """,
                (teacher_id,)
            )

            teacher = cursor.fetchone()

            if not teacher:

                session.clear()

                return redirect(
                    url_for("auth.teacher_login")
                )

            stored_password = teacher["password"]

            if not check_password_hash(
                stored_password,
                current_password
            ):

                return render_template(
                    "teacher/change_password.html",
                    error="Current password is incorrect."
                )

            hashed_password = generate_password_hash(
                new_password
            )

            cursor.execute(
                """
                UPDATE teacher

                SET password = %s

                WHERE teacher_id = %s
                """,
                (
                    hashed_password,
                    teacher_id
                )
            )

            connection.commit()

            return render_template(
                "teacher/change_password.html",
                success="Password changed successfully."
            )

        except Exception as e:

            if connection:
                connection.rollback()

            return render_template(
                "teacher/change_password.html",
                error=f"Database Error: {e}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "teacher/change_password.html"
    )


# ===========================================================
# 4. TEACHER MY SUBJECTS
# ===========================================================

@teacher_bp.route("/teacher/my-subjects")
def my_subjects():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                tsa.assignment_id,
                s.subject_id,
                s.subject_code,
                s.subject_name,
                s.credits,
                c.course_name,
                sem.semester_number,
                ay.academic_year_name,
                tsa.assigned_date

            FROM teacher_subject_assignment tsa

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            INNER JOIN academic_year ay
                ON tsa.academic_year_id = ay.academic_year_id

            WHERE tsa.teacher_id = %s
              AND tsa.status = 'Active'

            ORDER BY
                sem.semester_number,
                s.subject_name
            """,
            (teacher_id,)
        )

        subjects = cursor.fetchall()

        return render_template(
            "teacher/my_subjects.html",
            subjects=subjects
        )

    except Exception as e:

        return render_template(
            "teacher/my_subjects.html",
            subjects=[],
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 5. TEACHER UPLOAD QUESTION PAPER
# ===========================================================

@teacher_bp.route(
    "/teacher/upload-question-paper",
    methods=["GET", "POST"]
)
def upload_question_paper():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET ASSIGNED SUBJECTS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT
                tsa.assignment_id,
                s.subject_code,
                s.subject_name,
                c.course_name,
                sem.semester_number,
                ay.academic_year_name

            FROM teacher_subject_assignment tsa

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            INNER JOIN academic_year ay
                ON tsa.academic_year_id = ay.academic_year_id

            WHERE tsa.teacher_id = %s
              AND tsa.status = 'Active'

            ORDER BY s.subject_name
            """,
            (teacher_id,)
        )

        assignments = cursor.fetchall()

        # ---------------------------------------------------
        # GET ACTIVE EXAM TYPES
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT
                exam_type_id,
                exam_type_name

            FROM exam_type

            WHERE status = 'Active'

            ORDER BY exam_type_name
            """
        )

        exam_types = cursor.fetchall()

        # ---------------------------------------------------
        # POST
        # ---------------------------------------------------

        if request.method == "POST":

            assignment_id = request.form.get(
                "assignment_id"
            )

            exam_type_id = request.form.get(
                "exam_type_id"
            )

            title = request.form.get(
                "title",
                ""
            ).strip()

            file = request.files.get(
                "question_paper"
            )

            if (
                not assignment_id
                or not exam_type_id
                or not title
                or not file
                or not file.filename
            ):

                return render_template(
                    "teacher/upload_question_paper.html",
                    assignments=assignments,
                    exam_types=exam_types,
                    error=(
                        "Please fill in all fields "
                        "and select a PDF."
                    )
                )

            if not file.filename.lower().endswith(".pdf"):

                return render_template(
                    "teacher/upload_question_paper.html",
                    assignments=assignments,
                    exam_types=exam_types,
                    error="Only PDF files are allowed."
                )

            # ------------------------------------------------
            # VERIFY ASSIGNMENT
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    assignment_id,
                    academic_year_id

                FROM teacher_subject_assignment

                WHERE assignment_id = %s
                  AND teacher_id = %s
                  AND status = 'Active'
                """,
                (
                    assignment_id,
                    teacher_id
                )
            )

            assignment = cursor.fetchone()

            if not assignment:

                return render_template(
                    "teacher/upload_question_paper.html",
                    assignments=assignments,
                    exam_types=exam_types,
                    error="Invalid subject assignment."
                )

            # ------------------------------------------------
            # CREATE FOLDER
            # ------------------------------------------------

            upload_folder = os.path.join(
                "uploads",
                "question_papers"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            filename = secure_filename(
                file.filename
            )

            filename = (
                f"teacher_{teacher_id}_"
                f"{filename}"
            )

            file_path = os.path.join(
                upload_folder,
                filename
            )

            file.save(file_path)

            # ------------------------------------------------
            # INSERT DATABASE
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO question_paper (
                    assignment_id,
                    exam_type_id,
                    title,
                    academic_year_id,
                    file_name,
                    uploaded_by,
                    approved_by_hod
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE
                )
                """,
                (
                    assignment_id,
                    exam_type_id,
                    title,
                    assignment["academic_year_id"],
                    filename,
                    teacher_id
                )
            )

            connection.commit()

            return render_template(
                "teacher/upload_question_paper.html",
                assignments=assignments,
                exam_types=exam_types,
                success=(
                    "Question paper uploaded successfully. "
                    "It is waiting for HOD approval."
                )
            )

        return render_template(
            "teacher/upload_question_paper.html",
            assignments=assignments,
            exam_types=exam_types
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return render_template(
            "teacher/upload_question_paper.html",
            assignments=[],
            exam_types=[],
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 6. TEACHER MY QUESTION PAPERS
# ===========================================================

@teacher_bp.route("/teacher/my-question-papers")
def my_question_papers():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                qp.question_paper_id,
                qp.title,
                qp.file_name,
                qp.upload_date,
                qp.approved_by_hod,

                s.subject_code,
                s.subject_name,

                et.exam_type_name,

                ay.academic_year_name

            FROM question_paper qp

            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN exam_type et
                ON qp.exam_type_id = et.exam_type_id

            INNER JOIN academic_year ay
                ON qp.academic_year_id = ay.academic_year_id

            WHERE qp.uploaded_by = %s

            ORDER BY qp.upload_date DESC
            """,
            (teacher_id,)
        )

        question_papers = cursor.fetchall()

        return render_template(
            "teacher/my_question_papers.html",
            question_papers=question_papers
        )

    except Exception as e:

        return render_template(
            "teacher/my_question_papers.html",
            question_papers=[],
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 7. TEACHER UPLOAD ANSWER KEY
# ===========================================================

@teacher_bp.route(
    "/teacher/upload-answer-key",
    methods=["GET", "POST"]
)
def upload_answer_key():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET TEACHER'S QUESTION PAPERS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT
                qp.question_paper_id,
                qp.title,
                qp.file_name,

                s.subject_code,
                s.subject_name,

                et.exam_type_name

            FROM question_paper qp

            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN exam_type et
                ON qp.exam_type_id = et.exam_type_id

            WHERE qp.uploaded_by = %s

            ORDER BY qp.upload_date DESC
            """,
            (teacher_id,)
        )

        question_papers = cursor.fetchall()

        # ---------------------------------------------------
        # POST
        # ---------------------------------------------------

        if request.method == "POST":

            question_paper_id = request.form.get(
                "question_paper_id"
            )

            file = request.files.get(
                "answer_key"
            )

            if (
                not question_paper_id
                or not file
                or not file.filename
            ):

                return render_template(
                    "teacher/upload_answer_key.html",
                    question_papers=question_papers,
                    error=(
                        "Please select a question paper "
                        "and choose a PDF answer key."
                    )
                )

            if not file.filename.lower().endswith(".pdf"):

                return render_template(
                    "teacher/upload_answer_key.html",
                    question_papers=question_papers,
                    error="Only PDF files are allowed."
                )

            # ------------------------------------------------
            # VERIFY QUESTION PAPER
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    question_paper_id

                FROM question_paper

                WHERE question_paper_id = %s
                  AND uploaded_by = %s
                """,
                (
                    question_paper_id,
                    teacher_id
                )
            )

            question_paper = cursor.fetchone()

            if not question_paper:

                return render_template(
                    "teacher/upload_answer_key.html",
                    question_papers=question_papers,
                    error="Invalid question paper."
                )

            # ------------------------------------------------
            # CREATE FOLDER
            # ------------------------------------------------

            upload_folder = os.path.join(
                "uploads",
                "answer_keys"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            filename = secure_filename(
                file.filename
            )

            filename = (
                f"teacher_{teacher_id}_"
                f"{filename}"
            )

            file_path = os.path.join(
                upload_folder,
                filename
            )

            file.save(file_path)

            # ------------------------------------------------
            # INSERT ANSWER KEY
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO answer_key (
                    question_paper_id,
                    file_name,
                    uploaded_by
                )

                VALUES (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    question_paper_id,
                    filename,
                    teacher_id
                )
            )

            connection.commit()

            return render_template(
                "teacher/upload_answer_key.html",
                question_papers=question_papers,
                success="Answer key uploaded successfully."
            )

        return render_template(
            "teacher/upload_answer_key.html",
            question_papers=question_papers
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return render_template(
            "teacher/upload_answer_key.html",
            question_papers=[],
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 8. TEACHER UPLOAD STUDY MATERIAL
# ===========================================================

@teacher_bp.route(
    "/teacher/upload-study-material",
    methods=["GET", "POST"]
)
def upload_study_material():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET ASSIGNED SUBJECTS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT
                tsa.assignment_id,
                s.subject_code,
                s.subject_name,
                c.course_name,
                sem.semester_number,
                ay.academic_year_name

            FROM teacher_subject_assignment tsa

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            INNER JOIN academic_year ay
                ON tsa.academic_year_id = ay.academic_year_id

            WHERE tsa.teacher_id = %s
              AND tsa.status = 'Active'

            ORDER BY s.subject_name
            """,
            (teacher_id,)
        )

        assignments = cursor.fetchall()

        # ---------------------------------------------------
        # POST
        # ---------------------------------------------------

        if request.method == "POST":

            assignment_id = request.form.get(
                "assignment_id"
            )

            title = request.form.get(
                "title",
                ""
            ).strip()

            file = request.files.get(
                "study_material"
            )

            if (
                not assignment_id
                or not title
                or not file
                or not file.filename
            ):

                return render_template(
                    "teacher/upload_material.html",
                    assignments=assignments,
                    error=(
                        "Please fill in all fields "
                        "and select a PDF."
                    )
                )

            if not file.filename.lower().endswith(".pdf"):

                return render_template(
                    "teacher/upload_material.html",
                    assignments=assignments,
                    error="Only PDF files are allowed."
                )

            # ------------------------------------------------
            # VERIFY ASSIGNMENT
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    assignment_id

                FROM teacher_subject_assignment

                WHERE assignment_id = %s
                  AND teacher_id = %s
                  AND status = 'Active'
                """,
                (
                    assignment_id,
                    teacher_id
                )
            )

            assignment = cursor.fetchone()

            if not assignment:

                return render_template(
                    "teacher/upload_material.html",
                    assignments=assignments,
                    error="Invalid subject assignment."
                )

            # ------------------------------------------------
            # CREATE FOLDER
            # ------------------------------------------------

            upload_folder = os.path.join(
                "uploads",
                "study_materials"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            filename = secure_filename(
                file.filename
            )

            filename = (
                f"teacher_{teacher_id}_"
                f"{filename}"
            )

            file_path = os.path.join(
                upload_folder,
                filename
            )

            file.save(file_path)

            # ------------------------------------------------
            # INSERT DATABASE
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO study_material (
                    assignment_id,
                    title,
                    file_name,
                    uploaded_by,
                    approved_by_hod
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE
                )
                """,
                (
                    assignment_id,
                    title,
                    filename,
                    teacher_id
                )
            )

            connection.commit()

            return render_template(
                "teacher/upload_material.html",
                assignments=assignments,
                success=(
                    "Study material uploaded successfully. "
                    "It is waiting for HOD approval."
                )
            )

        return render_template(
            "teacher/upload_material.html",
            assignments=assignments
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return render_template(
            "teacher/upload_material.html",
            assignments=[],
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 9. TEACHER MY MATERIALS
# ===========================================================

@teacher_bp.route("/teacher/my-materials")
def my_materials():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                sm.study_material_id,
                sm.title,
                sm.file_name,
                sm.upload_date,
                sm.approved_by_hod,

                s.subject_code,
                s.subject_name,

                c.course_name,

                sem.semester_number

            FROM study_material sm

            INNER JOIN teacher_subject_assignment tsa
                ON sm.assignment_id = tsa.assignment_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            WHERE sm.uploaded_by = %s

            ORDER BY sm.upload_date DESC
            """,
            (teacher_id,)
        )

        study_materials = cursor.fetchall()

        return render_template(
            "teacher/my_materials.html",
            study_materials=study_materials
        )

    except Exception as e:

        return render_template(
            "teacher/my_materials.html",
            study_materials=[],
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 10. TEACHER STUDENT DOUBTS
# ===========================================================

@teacher_bp.route("/teacher/doubt-list")
def doubt_list():

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT DISTINCT
                sd.doubt_id,
                sd.doubt_title,
                sd.doubt_description,
                sd.created_at,

                s.subject_id,
                s.subject_code,
                s.subject_name,

                st.register_number,
                st.full_name AS student_name

            FROM student_doubt sd

            INNER JOIN subject s
                ON sd.subject_id = s.subject_id

            INNER JOIN student st
                ON sd.student_id = st.student_id

            INNER JOIN teacher_subject_assignment tsa
                ON sd.subject_id = tsa.subject_id

            WHERE tsa.teacher_id = %s
              AND tsa.status = 'Active'

            ORDER BY sd.created_at DESC
            """,
            (teacher_id,)
        )

        doubts = cursor.fetchall()

        return render_template(
            "teacher/doubt_list.html",
            doubts=doubts
        )

    except Exception as e:

        return render_template(
            "teacher/doubt_list.html",
            doubts=[],
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# 11. TEACHER REPLY TO STUDENT DOUBT
# ===========================================================

@teacher_bp.route(
    "/teacher/student-doubts/reply/<int:doubt_id>",
    methods=["GET", "POST"]
)
def reply_doubt(doubt_id):

    login_check = teacher_required()

    if login_check:
        return login_check

    teacher_id = session.get("teacher_id")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET DOUBT
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT DISTINCT
                sd.doubt_id,
                sd.doubt_title,
                sd.doubt_description,
                sd.created_at,

                s.subject_code,
                s.subject_name,

                st.register_number,
                st.full_name AS student_name

            FROM student_doubt sd

            INNER JOIN subject s
                ON sd.subject_id = s.subject_id

            INNER JOIN student st
                ON sd.student_id = st.student_id

            INNER JOIN teacher_subject_assignment tsa
                ON sd.subject_id = tsa.subject_id

            WHERE sd.doubt_id = %s
              AND tsa.teacher_id = %s
              AND tsa.status = 'Active'
            """,
            (
                doubt_id,
                teacher_id
            )
        )

        doubt = cursor.fetchone()

        if not doubt:

            return render_template(
                "teacher/reply_doubt.html",
                doubt=None,
                error=(
                    "Doubt not found or you are not "
                    "assigned to this subject."
                )
            )

        # ---------------------------------------------------
        # POST REPLY
        # ---------------------------------------------------

        if request.method == "POST":

            reply = request.form.get(
                "reply",
                ""
            ).strip()

            if not reply:

                return render_template(
                    "teacher/reply_doubt.html",
                    doubt=doubt,
                    error="Please enter your reply."
                )

            # ------------------------------------------------
            # INSERT REPLY
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO teacher_reply (
                    doubt_id,
                    teacher_id,
                    reply
                )

                VALUES (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    doubt_id,
                    teacher_id,
                    reply
                )
            )

            connection.commit()

            return redirect(
                url_for(
                    "teacher.doubt_list"
                )
            )

        return render_template(
            "teacher/reply_doubt.html",
            doubt=doubt
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return render_template(
            "teacher/reply_doubt.html",
            doubt=None,
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# TEACHER LOGOUT
# ===========================================================

@teacher_bp.route("/teacher/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.teacher_login")
    )
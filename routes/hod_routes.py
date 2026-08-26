from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)

from database.db_connection import get_connection

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from werkzeug.utils import secure_filename

import os
import uuid


# ===========================================================
# HOD BLUEPRINT
# ===========================================================

hod_bp = Blueprint(
    "hod",
    __name__,
    url_prefix="/hod"
)


# ===========================================================
# SYLLABUS UPLOAD CONFIGURATION
# ===========================================================

SYLLABUS_UPLOAD_FOLDER = os.path.join(
    "uploads",
    "syllabus"
)

ALLOWED_SYLLABUS_EXTENSIONS = {
    "pdf"
}


def allowed_syllabus_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_SYLLABUS_EXTENSIONS
    )


# ===========================================================
# HOD DASHBOARD
# ===========================================================

@hod_bp.route("/dashboard")
def dashboard():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET DEPARTMENT
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                department_name
            FROM department
            WHERE department_id = %s
        """, (
            session["hod_department_id"],
        ))

        department = cursor.fetchone()

        # ---------------------------------------------------
        # COUNT TEACHERS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(DISTINCT teacher_id) AS total
            FROM teacher
            WHERE department_id = %s
        """, (
            session["hod_department_id"],
        ))

        teacher_result = cursor.fetchone()

        # ---------------------------------------------------
        # COUNT STUDENTS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total
            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            WHERE c.department_id = %s
        """, (
            session["hod_department_id"],
        ))

        student_result = cursor.fetchone()

        # ---------------------------------------------------
        # COUNT SUBJECTS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total
            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            WHERE c.department_id = %s
        """, (
            session["hod_department_id"],
        ))

        subject_result = cursor.fetchone()

        # ---------------------------------------------------
        # COUNT PENDING STUDENT APPROVALS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total
            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            WHERE c.department_id = %s
              AND st.account_status = 'Pending'
        """, (
            session["hod_department_id"],
        ))

        pending_student_result = cursor.fetchone()

        # ---------------------------------------------------
        # RENDER DASHBOARD
        # ---------------------------------------------------

        return render_template(
            "hod/dashboard.html",

            hod_name=session.get(
                "hod_name"
            ),

            department=department,

            total_teachers=teacher_result["total"],

            total_students=student_result["total"],

            total_subjects=subject_result["total"],

            pending_student_approvals=
                pending_student_result["total"]
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# HOD LOGOUT
# ===========================================================

@hod_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.hod_login")
    )


# ===========================================================
# VIEW STUDENTS
# ===========================================================

@hod_bp.route("/students")
def students():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

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
                st.account_status,
                st.created_at,

                c.course_name,

                sem.semester_number

            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            INNER JOIN semester sem
                ON st.semester_id = sem.semester_id

            WHERE c.department_id = %s

            ORDER BY
                CASE
                    WHEN st.account_status = 'Pending'
                        THEN 1

                    WHEN st.account_status = 'Active'
                        THEN 2

                    WHEN st.account_status = 'Inactive'
                        THEN 3

                    ELSE 4
                END,

                c.course_name,

                sem.semester_number,

                st.full_name

        """, (
            session["hod_department_id"],
        ))

        students = cursor.fetchall()

        return render_template(
            "hod/students.html",
            students=students
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# STUDENT APPROVALS
# ===========================================================

@hod_bp.route("/student-approvals")
def student_approvals():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

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
                st.account_status,
                st.created_at,

                c.course_id,
                c.course_name,

                sem.semester_id,
                sem.semester_number

            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            INNER JOIN semester sem
                ON st.semester_id = sem.semester_id

            WHERE c.department_id = %s

            ORDER BY

                CASE
                    WHEN st.account_status = 'Pending'
                        THEN 1

                    WHEN st.account_status = 'Active'
                        THEN 2

                    WHEN st.account_status = 'Inactive'
                        THEN 3

                    ELSE 4
                END,

                c.course_name,

                sem.semester_number,

                st.full_name

        """, (
            session["hod_department_id"],
        ))

        students = cursor.fetchall()

        # ---------------------------------------------------
        # COUNT PENDING
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total

            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            WHERE c.department_id = %s
              AND st.account_status = 'Pending'

        """, (
            session["hod_department_id"],
        ))

        pending_result = cursor.fetchone()

        # ---------------------------------------------------
        # COUNT APPROVED
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total

            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            WHERE c.department_id = %s
              AND st.account_status = 'Active'

        """, (
            session["hod_department_id"],
        ))

        approved_result = cursor.fetchone()

        # ---------------------------------------------------
        # COUNT REJECTED
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS total

            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            WHERE c.department_id = %s
              AND st.account_status = 'Inactive'

        """, (
            session["hod_department_id"],
        ))

        rejected_result = cursor.fetchone()

        return render_template(
            "hod/student_approvals.html",

            students=students,

            pending_students=
                pending_result["total"],

            approved_students=
                approved_result["total"],

            rejected_students=
                rejected_result["total"]
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# APPROVE STUDENT
# ===========================================================

@hod_bp.route(
    "/student-approvals/approve/<int:student_id>",
    methods=["POST"]
)
def approve_student(student_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            SET
                st.account_status = 'Active'

            WHERE st.student_id = %s
              AND c.department_id = %s
              AND st.account_status = 'Pending'

        """, (
            student_id,
            session["hod_department_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.student_approvals")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error approving student: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# REJECT STUDENT
# ===========================================================

@hod_bp.route(
    "/student-approvals/reject/<int:student_id>",
    methods=["POST"]
)
def reject_student(student_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            SET
                st.account_status = 'Inactive'

            WHERE st.student_id = %s
              AND c.department_id = %s
              AND st.account_status = 'Pending'

        """, (
            student_id,
            session["hod_department_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.student_approvals")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error rejecting student: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# CHANGE STUDENT STATUS
# ===========================================================

@hod_bp.route(
    "/student-approvals/status/<int:student_id>",
    methods=["POST"]
)
def change_student_status(student_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    status = request.form.get("status")

    if status not in [
        "Active",
        "Inactive"
    ]:

        return "Invalid student status."

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            SET
                st.account_status = %s

            WHERE st.student_id = %s
              AND c.department_id = %s

        """, (
            status,
            student_id,
            session["hod_department_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.student_approvals")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error changing student status: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# MANAGE TEACHERS
# ===========================================================

@hod_bp.route("/manage-teachers")
def manage_teachers():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    hod_department_id = session.get(
        "hod_department_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                teacher_id,
                employee_id,
                full_name,
                email,
                phone,
                username,
                department_id,
                account_status,
                created_at,
                updated_at

            FROM teacher

            WHERE department_id = %s

            ORDER BY created_at DESC

        """, (
            hod_department_id,
        ))

        teachers = cursor.fetchall()

        return render_template(
            "hod/manage_teachers.html",
            teachers=teachers
        )

    except Exception as e:

        return render_template(
            "hod/manage_teachers.html",
            teachers=[],
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# APPROVE TEACHER
# ===========================================================

@hod_bp.route(
    "/manage-teachers/approve/<int:teacher_id>",
    methods=["POST"]
)
def approve_teacher(teacher_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    hod_department_id = session.get(
        "hod_department_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE teacher

            SET
                account_status = 'Active'

            WHERE teacher_id = %s
              AND department_id = %s
              AND account_status = 'Pending'

        """, (
            teacher_id,
            hod_department_id
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_teachers")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error approving teacher: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# REJECT TEACHER
# ===========================================================

@hod_bp.route(
    "/manage-teachers/reject/<int:teacher_id>",
    methods=["POST"]
)
def reject_teacher(teacher_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    hod_department_id = session.get(
        "hod_department_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE teacher

            SET
                account_status = 'Inactive'

            WHERE teacher_id = %s
              AND department_id = %s
              AND account_status = 'Pending'

        """, (
            teacher_id,
            hod_department_id
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_teachers")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error rejecting teacher: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# CHANGE TEACHER STATUS
# ===========================================================

@hod_bp.route(
    "/manage-teachers/status/<int:teacher_id>",
    methods=["POST"]
)
def change_teacher_status(teacher_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    hod_department_id = session.get(
        "hod_department_id"
    )

    new_status = request.form.get("status")

    if new_status not in [
        "Active",
        "Inactive"
    ]:

        return "Invalid status."

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE teacher

            SET
                account_status = %s

            WHERE teacher_id = %s
              AND department_id = %s

        """, (
            new_status,
            teacher_id,
            hod_department_id
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_teachers")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error changing teacher status: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# DELETE TEACHER
# ===========================================================

@hod_bp.route(
    "/manage-teachers/delete/<int:teacher_id>",
    methods=["POST"]
)
def delete_teacher(teacher_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    hod_department_id = session.get(
        "hod_department_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM teacher

            WHERE teacher_id = %s
              AND department_id = %s

        """, (
            teacher_id,
            hod_department_id
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_teachers")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error deleting teacher: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# EDIT TEACHER
# ===========================================================

@hod_bp.route(
    "/manage-teachers/edit/<int:teacher_id>",
    methods=["GET", "POST"]
)
def edit_teacher(teacher_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    hod_department_id = session.get(
        "hod_department_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                teacher_id,
                employee_id,
                full_name,
                email,
                phone,
                username,
                account_status

            FROM teacher

            WHERE teacher_id = %s
              AND department_id = %s

        """, (
            teacher_id,
            hod_department_id
        ))

        teacher = cursor.fetchone()

        if not teacher:
            return "Teacher not found."

        if request.method == "POST":

            employee_id = request.form.get("employee_id")
            full_name = request.form.get("full_name")
            email = request.form.get("email")
            phone = request.form.get("phone")
            username = request.form.get("username")

            cursor.execute("""
                UPDATE teacher

                SET
                    employee_id = %s,
                    full_name = %s,
                    email = %s,
                    phone = %s,
                    username = %s

                WHERE teacher_id = %s
                  AND department_id = %s

            """, (
                employee_id,
                full_name,
                email,
                phone,
                username,
                teacher_id,
                hod_department_id
            ))

            connection.commit()

            return redirect(
                url_for("hod.manage_teachers")
            )

        return render_template(
            "hod/edit_teacher.html",
            teacher=teacher
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error editing teacher: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# TEACHER SUBJECT ASSIGNMENTS
# ===========================================================

@hod_bp.route("/teacher-assignments")
def teacher_assignments():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                teacher_id,
                employee_id,
                full_name

            FROM teacher

            WHERE department_id = %s
              AND account_status = 'Active'

            ORDER BY full_name

        """, (
            session["hod_department_id"],
        ))

        teachers = cursor.fetchall()

        cursor.execute("""
            SELECT
                s.subject_id,
                s.subject_code,
                s.subject_name,
                c.course_name,
                sem.semester_number

            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            WHERE c.department_id = %s
              AND s.status = 'Active'

            ORDER BY
                c.course_name,
                sem.semester_number,
                s.subject_name

        """, (
            session["hod_department_id"],
        ))

        subjects = cursor.fetchall()

        cursor.execute("""
            SELECT
                tsa.assignment_id,

                t.teacher_id,
                t.employee_id,
                t.full_name AS teacher_name,

                s.subject_id,
                s.subject_code,
                s.subject_name,

                c.course_name,

                sem.semester_number,

                ay.academic_year_name,

                tsa.status

            FROM teacher_subject_assignment tsa

            INNER JOIN teacher t
                ON tsa.teacher_id = t.teacher_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            INNER JOIN academic_year ay
                ON tsa.academic_year_id = ay.academic_year_id

            WHERE c.department_id = %s

            ORDER BY
                t.full_name,
                c.course_name,
                sem.semester_number,
                s.subject_name

        """, (
            session["hod_department_id"],
        ))

        assignments = cursor.fetchall()

        return render_template(
            "hod/teacher_assignments.html",
            teachers=teachers,
            subjects=subjects,
            assignments=assignments
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADD TEACHER SUBJECT ASSIGNMENT
# ===========================================================

@hod_bp.route(
    "/teacher-assignments/add",
    methods=["POST"]
)
def add_teacher_assignment():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    teacher_id = request.form.get("teacher_id")
    subject_id = request.form.get("subject_id")

    if not teacher_id or not subject_id:
        return "Teacher and subject are required."

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                academic_year_id

            FROM academic_year

            WHERE status = 'Current'

            ORDER BY start_date DESC

            LIMIT 1

        """)

        current_year = cursor.fetchone()

        if not current_year:

            return (
                "No current academic year is available. "
                "Please contact the administrator."
            )

        academic_year_id = current_year["academic_year_id"]

        cursor.execute("""
            SELECT
                teacher_id

            FROM teacher

            WHERE teacher_id = %s
              AND department_id = %s
              AND account_status = 'Active'

        """, (
            teacher_id,
            session["hod_department_id"]
        ))

        teacher = cursor.fetchone()

        if not teacher:

            return (
                "Invalid teacher or teacher does not "
                "belong to your department."
            )

        cursor.execute("""
            SELECT
                s.subject_id

            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            WHERE s.subject_id = %s
              AND c.department_id = %s
              AND s.status = 'Active'

        """, (
            subject_id,
            session["hod_department_id"]
        ))

        subject = cursor.fetchone()

        if not subject:

            return (
                "Invalid subject or subject does not "
                "belong to your department."
            )

        cursor.execute("""
            SELECT
                assignment_id

            FROM teacher_subject_assignment

            WHERE teacher_id = %s
              AND subject_id = %s
              AND academic_year_id = %s

        """, (
            teacher_id,
            subject_id,
            academic_year_id
        ))

        existing_assignment = cursor.fetchone()

        if existing_assignment:

            return (
                "This teacher is already assigned to this "
                "subject for the current academic year."
            )

        cursor.execute("""
            INSERT INTO teacher_subject_assignment
            (
                teacher_id,
                subject_id,
                academic_year_id,
                assigned_by_hod,
                status
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                'Active'
            )

        """, (
            teacher_id,
            subject_id,
            academic_year_id,
            session["hod_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.teacher_assignments")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# EDIT TEACHER SUBJECT ASSIGNMENT
# ===========================================================

@hod_bp.route(
    "/teacher-assignments/edit/<int:assignment_id>",
    methods=["GET", "POST"]
)
def edit_teacher_assignment(assignment_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                tsa.assignment_id,
                tsa.teacher_id,
                tsa.subject_id,
                tsa.academic_year_id,
                tsa.status

            FROM teacher_subject_assignment tsa

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            WHERE tsa.assignment_id = %s
              AND c.department_id = %s

        """, (
            assignment_id,
            session["hod_department_id"]
        ))

        assignment = cursor.fetchone()

        if not assignment:

            return (
                "Teacher assignment not found or it does "
                "not belong to your department."
            )

        cursor.execute("""
            SELECT
                teacher_id,
                employee_id,
                full_name

            FROM teacher

            WHERE department_id = %s
              AND account_status = 'Active'

            ORDER BY full_name

        """, (
            session["hod_department_id"],
        ))

        teachers = cursor.fetchall()

        cursor.execute("""
            SELECT
                s.subject_id,
                s.subject_code,
                s.subject_name,
                c.course_name,
                sem.semester_number

            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            WHERE c.department_id = %s
              AND s.status = 'Active'

            ORDER BY
                c.course_name,
                sem.semester_number,
                s.subject_name

        """, (
            session["hod_department_id"],
        ))

        subjects = cursor.fetchall()

        if request.method == "POST":

            teacher_id = request.form.get("teacher_id")
            subject_id = request.form.get("subject_id")

            if not teacher_id or not subject_id:

                return "Teacher and subject are required."

            cursor.execute("""
                SELECT
                    teacher_id

                FROM teacher

                WHERE teacher_id = %s
                  AND department_id = %s
                  AND account_status = 'Active'

            """, (
                teacher_id,
                session["hod_department_id"]
            ))

            valid_teacher = cursor.fetchone()

            if not valid_teacher:

                return (
                    "Invalid teacher or teacher does not "
                    "belong to your department."
                )

            cursor.execute("""
                SELECT
                    s.subject_id

                FROM subject s

                INNER JOIN course c
                    ON s.course_id = c.course_id

                WHERE s.subject_id = %s
                  AND c.department_id = %s
                  AND s.status = 'Active'

            """, (
                subject_id,
                session["hod_department_id"]
            ))

            valid_subject = cursor.fetchone()

            if not valid_subject:

                return (
                    "Invalid subject or subject does not "
                    "belong to your department."
                )

            cursor.execute("""
                SELECT
                    assignment_id

                FROM teacher_subject_assignment

                WHERE teacher_id = %s
                  AND subject_id = %s
                  AND academic_year_id = %s
                  AND assignment_id != %s

            """, (
                teacher_id,
                subject_id,
                assignment["academic_year_id"],
                assignment_id
            ))

            duplicate = cursor.fetchone()

            if duplicate:

                return (
                    "This teacher is already assigned to "
                    "this subject for this academic year."
                )

            cursor.execute("""
                UPDATE teacher_subject_assignment

                SET
                    teacher_id = %s,
                    subject_id = %s

                WHERE assignment_id = %s

            """, (
                teacher_id,
                subject_id,
                assignment_id
            ))

            connection.commit()

            return redirect(
                url_for("hod.teacher_assignments")
            )

        return render_template(
            "hod/edit_teacher_assignment.html",
            assignment=assignment,
            teachers=teachers,
            subjects=subjects
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error editing teacher assignment: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# DELETE TEACHER SUBJECT ASSIGNMENT
# ===========================================================

@hod_bp.route(
    "/teacher-assignments/delete/<int:assignment_id>",
    methods=["POST"]
)
def delete_teacher_assignment(assignment_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                tsa.assignment_id

            FROM teacher_subject_assignment tsa

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            WHERE tsa.assignment_id = %s
              AND c.department_id = %s

        """, (
            assignment_id,
            session["hod_department_id"]
        ))

        assignment = cursor.fetchone()

        if not assignment:

            return (
                "Assignment not found or it does "
                "not belong to your department."
            )

        cursor.execute("""
            SELECT
                question_paper_id

            FROM question_paper

            WHERE assignment_id = %s

            LIMIT 1

        """, (
            assignment_id,
        ))

        if cursor.fetchone():

            return (
                "This assignment cannot be deleted because "
                "question papers are already linked to it. "
                "Deactivate the assignment instead."
            )

        cursor.execute("""
            SELECT
                study_material_id

            FROM study_material

            WHERE assignment_id = %s

            LIMIT 1

        """, (
            assignment_id,
        ))

        if cursor.fetchone():

            return (
                "This assignment cannot be deleted because "
                "study materials are already linked to it. "
                "Deactivate the assignment instead."
            )

        cursor.execute("""
            DELETE FROM teacher_subject_assignment

            WHERE assignment_id = %s

        """, (
            assignment_id,
        ))

        connection.commit()

        return redirect(
            url_for("hod.teacher_assignments")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error deleting teacher assignment: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# CHANGE TEACHER ASSIGNMENT STATUS
# ===========================================================

@hod_bp.route(
    "/teacher-assignments/status/<int:assignment_id>",
    methods=["POST"]
)
def change_assignment_status(assignment_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    status = request.form.get("status")

    if status not in [
        "Active",
        "Inactive"
    ]:

        return "Invalid assignment status."

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE teacher_subject_assignment tsa

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            SET
                tsa.status = %s

            WHERE tsa.assignment_id = %s
              AND c.department_id = %s

        """, (
            status,
            assignment_id,
            session["hod_department_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.teacher_assignments")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error changing assignment status: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# APPROVE QUESTION PAPERS
# ===========================================================

@hod_bp.route("/approve-papers")
def approve_papers():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

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
                qp.approved_by_hod,

                t.full_name AS teacher_name,
                t.employee_id,

                s.subject_code,
                s.subject_name,

                c.course_name,

                sem.semester_number,

                ay.academic_year_name,

                et.exam_type_name

            FROM question_paper qp

            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id

            INNER JOIN teacher t
                ON tsa.teacher_id = t.teacher_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            INNER JOIN academic_year ay
                ON qp.academic_year_id = ay.academic_year_id

            INNER JOIN exam_type et
                ON qp.exam_type_id = et.exam_type_id

            WHERE c.department_id = %s

            ORDER BY
                qp.upload_date DESC

        """, (
            session["hod_department_id"],
        ))

        papers = cursor.fetchall()

        return render_template(
            "hod/approve_papers.html",
            papers=papers
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# APPROVE QUESTION PAPER
# ===========================================================

@hod_bp.route(
    "/approve-question-paper/<int:question_paper_id>",
    methods=["POST"]
)
def approve_question_paper(question_paper_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE question_paper qp

            INNER JOIN teacher_subject_assignment tsa
                ON qp.assignment_id = tsa.assignment_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            SET
                qp.approved_by_hod = 1

            WHERE qp.question_paper_id = %s
              AND c.department_id = %s
              AND qp.approved_by_hod = 0

        """, (
            question_paper_id,
            session["hod_department_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.approve_papers")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error approving question paper: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# APPROVE STUDY MATERIALS
# ===========================================================

@hod_bp.route("/approve-materials")
def approve_materials():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                sm.study_material_id,
                sm.title,
                sm.file_name,
                sm.upload_date,
                sm.approved_by_hod,

                t.full_name AS teacher_name,
                t.employee_id,

                s.subject_code,
                s.subject_name,

                c.course_name,

                sem.semester_number,

                ay.academic_year_name

            FROM study_material sm

            INNER JOIN teacher_subject_assignment tsa
                ON sm.assignment_id = tsa.assignment_id

            INNER JOIN teacher t
                ON tsa.teacher_id = t.teacher_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            INNER JOIN academic_year ay
                ON tsa.academic_year_id = ay.academic_year_id

            WHERE c.department_id = %s

            ORDER BY
                sm.upload_date DESC

        """, (
            session["hod_department_id"],
        ))

        materials = cursor.fetchall()

        return render_template(
            "hod/approve_materials.html",
            materials=materials
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# APPROVE STUDY MATERIAL
# ===========================================================

@hod_bp.route(
    "/approve-study-material/<int:study_material_id>",
    methods=["POST"]
)
def approve_study_material(study_material_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE study_material sm

            INNER JOIN teacher_subject_assignment tsa
                ON sm.assignment_id = tsa.assignment_id

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            SET
                sm.approved_by_hod = 1

            WHERE sm.study_material_id = %s
              AND c.department_id = %s
              AND sm.approved_by_hod = 0

        """, (
            study_material_id,
            session["hod_department_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.approve_materials")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error approving study material: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# MANAGE SUBJECTS
# ===========================================================

@hod_bp.route("/subjects")
def manage_subjects():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                course_id,
                course_name

            FROM course

            WHERE department_id = %s

            ORDER BY course_name

        """, (
            session["hod_department_id"],
        ))

        courses = cursor.fetchall()

        cursor.execute("""
            SELECT
                semester_id,
                semester_number

            FROM semester

            ORDER BY semester_number

        """)

        semesters = cursor.fetchall()

        cursor.execute("""
            SELECT
                s.subject_id,
                s.subject_code,
                s.subject_name,
                s.credits,
                s.status,
                s.created_at,

                c.course_name,
                sem.semester_number

            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            WHERE c.department_id = %s

            ORDER BY
                c.course_name,
                sem.semester_number,
                s.subject_name

        """, (
            session["hod_department_id"],
        ))

        subjects = cursor.fetchall()

        return render_template(
            "hod/manage_subject.html",
            courses=courses,
            semesters=semesters,
            subjects=subjects
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADD SUBJECT
# ===========================================================

@hod_bp.route(
    "/subjects/add",
    methods=["POST"]
)
def add_subject():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    course_id = request.form.get("course_id")
    semester_id = request.form.get("semester_id")
    subject_code = request.form.get("subject_code")
    subject_name = request.form.get("subject_name")
    credits = request.form.get("credits")

    if (
        not course_id
        or not semester_id
        or not subject_code
        or not subject_name
        or not credits
    ):

        return "All subject fields are required."

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                course_id

            FROM course

            WHERE course_id = %s
              AND department_id = %s

        """, (
            course_id,
            session["hod_department_id"]
        ))

        if not cursor.fetchone():
            return "Invalid course."

        cursor.execute("""
            SELECT
                semester_id

            FROM semester

            WHERE semester_id = %s

        """, (
            semester_id,
        ))

        if not cursor.fetchone():
            return "Invalid semester."

        cursor.execute("""
            SELECT
                s.subject_id

            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            WHERE s.subject_code = %s
              AND c.department_id = %s

        """, (
            subject_code,
            session["hod_department_id"]
        ))

        if cursor.fetchone():

            return (
                "This subject code already exists "
                "in your department."
            )

        cursor.execute("""
            INSERT INTO subject
            (
                course_id,
                semester_id,
                subject_code,
                subject_name,
                credits,
                status
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                'Active'
            )

        """, (
            course_id,
            semester_id,
            subject_code,
            subject_name,
            credits
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_subjects")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# CHANGE SUBJECT STATUS
# ===========================================================

@hod_bp.route(
    "/subjects/status/<int:subject_id>",
    methods=["POST"]
)
def change_subject_status(subject_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    status = request.form.get("status")

    if status not in [
        "Active",
        "Inactive"
    ]:

        return "Invalid subject status."

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            SET
                s.status = %s

            WHERE s.subject_id = %s
              AND c.department_id = %s

        """, (
            status,
            subject_id,
            session["hod_department_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_subjects")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error changing subject status: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# EDIT SUBJECT
# ===========================================================

@hod_bp.route(
    "/subjects/edit/<int:subject_id>",
    methods=["GET", "POST"]
)
def edit_subject(subject_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                s.subject_id,
                s.course_id,
                s.semester_id,
                s.subject_code,
                s.subject_name,
                s.credits,
                s.status

            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            WHERE s.subject_id = %s
              AND c.department_id = %s

        """, (
            subject_id,
            session["hod_department_id"]
        ))

        subject = cursor.fetchone()

        if not subject:
            return "Subject not found."

        cursor.execute("""
            SELECT
                course_id,
                course_name

            FROM course

            WHERE department_id = %s

            ORDER BY course_name

        """, (
            session["hod_department_id"],
        ))

        courses = cursor.fetchall()

        cursor.execute("""
            SELECT
                semester_id,
                semester_number

            FROM semester

            ORDER BY semester_number

        """)

        semesters = cursor.fetchall()

        if request.method == "POST":

            course_id = request.form.get("course_id")
            semester_id = request.form.get("semester_id")
            subject_code = request.form.get("subject_code")
            subject_name = request.form.get("subject_name")
            credits = request.form.get("credits")

            if (
                not course_id
                or not semester_id
                or not subject_code
                or not subject_name
                or not credits
            ):

                return "All subject fields are required."

            cursor.execute("""
                SELECT
                    course_id

                FROM course

                WHERE course_id = %s
                  AND department_id = %s

            """, (
                course_id,
                session["hod_department_id"]
            ))

            if not cursor.fetchone():
                return "Invalid course."

            cursor.execute("""
                SELECT
                    semester_id

                FROM semester

                WHERE semester_id = %s

            """, (
                semester_id,
            ))

            if not cursor.fetchone():
                return "Invalid semester."

            cursor.execute("""
                SELECT
                    s.subject_id

                FROM subject s

                INNER JOIN course c
                    ON s.course_id = c.course_id

                WHERE s.subject_code = %s
                  AND c.department_id = %s
                  AND s.subject_id != %s

            """, (
                subject_code,
                session["hod_department_id"],
                subject_id
            ))

            if cursor.fetchone():

                return (
                    "This subject code already exists "
                    "in your department."
                )

            cursor.execute("""
                UPDATE subject s

                INNER JOIN course c
                    ON s.course_id = c.course_id

                SET
                    s.course_id = %s,
                    s.semester_id = %s,
                    s.subject_code = %s,
                    s.subject_name = %s,
                    s.credits = %s

                WHERE s.subject_id = %s
                  AND c.department_id = %s

            """, (
                course_id,
                semester_id,
                subject_code,
                subject_name,
                credits,
                subject_id,
                session["hod_department_id"]
            ))

            connection.commit()

            return redirect(
                url_for("hod.manage_subjects")
            )

        return render_template(
            "hod/edit_subject.html",
            subject=subject,
            courses=courses,
            semesters=semesters
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error editing subject: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# DELETE SUBJECT
# ===========================================================

@hod_bp.route(
    "/subjects/delete/<int:subject_id>",
    methods=["POST"]
)
def delete_subject(subject_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                s.subject_id,
                s.subject_name

            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            WHERE s.subject_id = %s
              AND c.department_id = %s

        """, (
            subject_id,
            session["hod_department_id"]
        ))

        subject = cursor.fetchone()

        if not subject:
            return "Subject not found."

        cursor.execute("""
            SELECT
                assignment_id

            FROM teacher_subject_assignment

            WHERE subject_id = %s

            LIMIT 1

        """, (
            subject_id,
        ))

        if cursor.fetchone():

            return (
                "This subject cannot be deleted because "
                "it is already assigned to a teacher. "
                "Deactivate the subject instead."
            )

        cursor.execute("""
            DELETE FROM subject

            WHERE subject_id = %s

        """, (
            subject_id,
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_subjects")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error deleting subject: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# HOD SYLLABUS MANAGEMENT
# ===========================================================


# ===========================================================
# VIEW / MANAGE SYLLABI
# ===========================================================

@hod_bp.route("/syllabus")
def manage_syllabus():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                s.syllabus_id,
                s.department_id,
                s.title,
                s.file_name,
                s.file_path,
                s.status,
                s.uploaded_by_hod,
                s.uploaded_at,

                d.department_name,

                h.full_name AS hod_name

            FROM syllabus s

            INNER JOIN department d
                ON s.department_id = d.department_id

            LEFT JOIN hod h
                ON s.uploaded_by_hod = h.hod_id

            WHERE s.department_id = %s

            ORDER BY
                s.uploaded_at DESC

        """, (
            session["hod_department_id"],
        ))

        syllabi = cursor.fetchall()

        cursor.execute("""
            SELECT
                department_name

            FROM department

            WHERE department_id = %s

        """, (
            session["hod_department_id"],
        ))

        department = cursor.fetchone()

        return render_template(
            "hod/syllabus.html",
            syllabi=syllabi,
            department=department
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# IMPORTANT:
# SYLLABUS ENDPOINT ALIAS
#
# Your dashboard can use:
#
#     url_for("hod.syllabus")
#
# Existing Python code can still use:
#
#     url_for("hod.manage_syllabus")
#
# Both point to the same page.
# ===========================================================

hod_bp.add_url_rule(
    "/syllabus",
    endpoint="syllabus",
    view_func=manage_syllabus
)


# ===========================================================
# UPLOAD SYLLABUS PDF
# ===========================================================

@hod_bp.route(
    "/syllabus/upload",
    methods=["POST"]
)
def upload_syllabus():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    title = request.form.get(
        "title",
        ""
    ).strip()

    syllabus_file = request.files.get(
        "syllabus_file"
    )

    # -------------------------------------------------------
    # VALIDATE TITLE
    # -------------------------------------------------------

    if not title:

        return render_template(
            "hod/syllabus.html",
            syllabi=[],
            error="Syllabus title is required."
        )

    # -------------------------------------------------------
    # VALIDATE FILE
    # -------------------------------------------------------

    if not syllabus_file:

        return render_template(
            "hod/syllabus.html",
            syllabi=[],
            error="Please select a PDF file."
        )

    if syllabus_file.filename == "":

        return render_template(
            "hod/syllabus.html",
            syllabi=[],
            error="Please select a PDF file."
        )

    if not allowed_syllabus_file(
        syllabus_file.filename
    ):

        return render_template(
            "hod/syllabus.html",
            syllabi=[],
            error="Only PDF files are allowed."
        )

    connection = None
    cursor = None
    file_path = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET HOD DEPARTMENT
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                department_id

            FROM hod

            WHERE hod_id = %s

        """, (
            session["hod_id"],
        ))

        hod = cursor.fetchone()

        if not hod:

            return "HOD account not found."

        hod_department_id = hod[
            "department_id"
        ]

        # ---------------------------------------------------
        # SECURITY:
        # NEVER TAKE DEPARTMENT ID FROM FORM.
        # ALWAYS USE HOD'S OWN DEPARTMENT.
        # ---------------------------------------------------

        original_filename = secure_filename(
            syllabus_file.filename
        )

        if not original_filename:

            return "Invalid file name."

        # ---------------------------------------------------
        # CREATE UPLOAD DIRECTORY
        # ---------------------------------------------------

        upload_folder = os.path.join(
            os.getcwd(),
            SYLLABUS_UPLOAD_FOLDER
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        # ---------------------------------------------------
        # GENERATE UNIQUE FILE NAME
        # ---------------------------------------------------

        unique_filename = (
            str(uuid.uuid4())
            + "_"
            + original_filename
        )

        file_path = os.path.join(
            upload_folder,
            unique_filename
        )

        # ---------------------------------------------------
        # SAVE FILE
        # ---------------------------------------------------

        syllabus_file.save(
            file_path
        )

        # ---------------------------------------------------
        # DATABASE PATH
        # ---------------------------------------------------

        database_file_path = os.path.join(
            "syllabus",
            unique_filename
        ).replace("\\", "/")

        # ---------------------------------------------------
        # INSERT SYLLABUS
        # ---------------------------------------------------

        cursor.execute("""
            INSERT INTO syllabus
            (
                department_id,
                title,
                file_name,
                file_path,
                status,
                uploaded_by_hod
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                'Active',
                %s
            )

        """, (
            hod_department_id,
            title,
            original_filename,
            database_file_path,
            session["hod_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_syllabus")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        # ---------------------------------------------------
        # REMOVE FILE IF DATABASE INSERT FAILED
        # ---------------------------------------------------

        try:

            if (
                file_path
                and os.path.exists(file_path)
            ):

                os.remove(file_path)

        except Exception:
            pass

        return f"Error uploading syllabus: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# VIEW SYLLABUS PDF
# ===========================================================

@hod_bp.route(
    "/syllabus/view/<int:syllabus_id>"
)
def view_syllabus(syllabus_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

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
              AND department_id = %s

        """, (
            syllabus_id,
            session["hod_department_id"]
        ))

        syllabus = cursor.fetchone()

        if not syllabus:

            return (
                "Syllabus not found or you are not "
                "authorized to view it."
            )

        stored_file_path = syllabus[
            "file_path"
        ]

        filename = os.path.basename(
            stored_file_path
        )

        upload_folder = os.path.join(
            os.getcwd(),
            SYLLABUS_UPLOAD_FOLDER
        )

        actual_file = os.path.join(
            upload_folder,
            filename
        )

        if not os.path.exists(actual_file):

            return (
                "Syllabus PDF file was not found "
                "on the server."
            )

        return send_from_directory(
            upload_folder,
            filename,
            as_attachment=False
        )

    except Exception as e:

        return f"Error viewing syllabus: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# DOWNLOAD SYLLABUS PDF
# ===========================================================

@hod_bp.route(
    "/syllabus/download/<int:syllabus_id>"
)
def download_syllabus(syllabus_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

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
              AND department_id = %s

        """, (
            syllabus_id,
            session["hod_department_id"]
        ))

        syllabus = cursor.fetchone()

        if not syllabus:

            return (
                "Syllabus not found or you are not "
                "authorized to download it."
            )

        filename = os.path.basename(
            syllabus["file_path"]
        )

        upload_folder = os.path.join(
            os.getcwd(),
            SYLLABUS_UPLOAD_FOLDER
        )

        actual_file = os.path.join(
            upload_folder,
            filename
        )

        if not os.path.exists(actual_file):

            return "Syllabus PDF file was not found."

        return send_from_directory(
            upload_folder,
            filename,
            as_attachment=True,
            download_name=syllabus["file_name"]
        )

    except Exception as e:

        return f"Error downloading syllabus: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ACTIVATE / DEACTIVATE SYLLABUS
# ===========================================================

@hod_bp.route(
    "/syllabus/status/<int:syllabus_id>",
    methods=["POST"]
)
def change_syllabus_status(syllabus_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    status = request.form.get(
        "status"
    )

    if status not in [
        "Active",
        "Inactive"
    ]:

        return "Invalid syllabus status."

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE syllabus

            SET
                status = %s

            WHERE syllabus_id = %s
              AND department_id = %s

        """, (
            status,
            syllabus_id,
            session["hod_department_id"]
        ))

        connection.commit()

        return redirect(
            url_for("hod.manage_syllabus")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error changing syllabus status: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# DELETE SYLLABUS
# ===========================================================

@hod_bp.route(
    "/syllabus/delete/<int:syllabus_id>",
    methods=["POST"]
)
def delete_syllabus(syllabus_id):

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET SYLLABUS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                syllabus_id,
                file_path

            FROM syllabus

            WHERE syllabus_id = %s
              AND department_id = %s

        """, (
            syllabus_id,
            session["hod_department_id"]
        ))

        syllabus = cursor.fetchone()

        if not syllabus:

            return (
                "Syllabus not found or you are not "
                "authorized to delete it."
            )

        # ---------------------------------------------------
        # DELETE DATABASE RECORD
        # ---------------------------------------------------

        cursor.execute("""
            DELETE FROM syllabus

            WHERE syllabus_id = %s
              AND department_id = %s

        """, (
            syllabus_id,
            session["hod_department_id"]
        ))

        connection.commit()

        # ---------------------------------------------------
        # DELETE PDF FILE
        # ---------------------------------------------------

        if syllabus["file_path"]:

            filename = os.path.basename(
                syllabus["file_path"]
            )

            upload_folder = os.path.join(
                os.getcwd(),
                SYLLABUS_UPLOAD_FOLDER
            )

            actual_file = os.path.join(
                upload_folder,
                filename
            )

            if os.path.exists(actual_file):

                os.remove(
                    actual_file
                )

        return redirect(
            url_for("hod.manage_syllabus")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return f"Error deleting syllabus: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# HOD PROFILE
# ===========================================================

@hod_bp.route("/profile")
def profile():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                h.hod_id,
                h.full_name,
                h.email,
                h.phone,
                h.username,
                h.account_status,
                h.created_at,
                d.department_name

            FROM hod h

            INNER JOIN department d
                ON h.department_id = d.department_id

            WHERE h.hod_id = %s

        """, (
            session["hod_id"],
        ))

        hod = cursor.fetchone()

        if not hod:
            return "HOD profile not found."

        return render_template(
            "hod/profile.html",
            hod=hod
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# HOD CHANGE PASSWORD
# ===========================================================

@hod_bp.route(
    "/change-password",
    methods=["GET", "POST"]
)
def change_password():

    if "hod_id" not in session:
        return redirect(
            url_for("auth.hod_login")
        )

    # -------------------------------------------------------
    # GET
    # -------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "hod/change_password.html"
        )

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
            "hod/change_password.html",
            error="All password fields are required."
        )

    if new_password != confirm_password:

        return render_template(
            "hod/change_password.html",
            error=(
                "New password and confirm password "
                "do not match."
            )
        )

    if len(new_password) < 6:

        return render_template(
            "hod/change_password.html",
            error=(
                "New password must contain at least "
                "6 characters."
            )
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                password

            FROM hod

            WHERE hod_id = %s

        """, (
            session["hod_id"],
        ))

        hod = cursor.fetchone()

        if not hod:

            return render_template(
                "hod/change_password.html",
                error="HOD account not found."
            )

        stored_password = hod["password"]

        if not check_password_hash(
            stored_password,
            current_password
        ):

            return render_template(
                "hod/change_password.html",
                error="Current password is incorrect."
            )

        if check_password_hash(
            stored_password,
            new_password
        ):

            return render_template(
                "hod/change_password.html",
                error=(
                    "New password must be different "
                    "from the current password."
                )
            )

        hashed_password = generate_password_hash(
            new_password
        )

        cursor.execute("""
            UPDATE hod

            SET
                password = %s

            WHERE hod_id = %s

        """, (
            hashed_password,
            session["hod_id"]
        ))

        connection.commit()

        return render_template(
            "hod/change_password.html",
            success="Password changed successfully."
        )

    except Exception as e:

        if connection:
            connection.rollback()

        return render_template(
            "hod/change_password.html",
            error=f"Database Error: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
from flask import Blueprint, render_template, session, redirect, url_for

from database.db_connection import get_connection


# ===========================================================
# HOD BLUEPRINT
# ===========================================================

hod_bp = Blueprint(
    "hod",
    __name__,
    url_prefix="/hod"
)


# ===========================================================
# HOD DASHBOARD
# ===========================================================

@hod_bp.route("/dashboard")
def dashboard():

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # Get department name
        # ---------------------------------------------------

        cursor.execute("""
            SELECT department_name
            FROM department
            WHERE department_id = %s
        """, (
            session["hod_department_id"],
        ))

        department = cursor.fetchone()

        # ---------------------------------------------------
        # Count teachers in HOD's department
        # ---------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM teacher t
            INNER JOIN teacher_subject_assignment tsa
                ON t.teacher_id = tsa.teacher_id
            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id
            WHERE s.course_id IN (
                SELECT course_id
                FROM course
                WHERE department_id = %s
            )
        """, (
            session["hod_department_id"],
        ))

        teacher_result = cursor.fetchone()

        # ---------------------------------------------------
        # Count students in HOD's department
        # ---------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM student st
            INNER JOIN course c
                ON st.course_id = c.course_id
            WHERE c.department_id = %s
        """, (
            session["hod_department_id"],
        ))

        student_result = cursor.fetchone()

        # ---------------------------------------------------
        # Count subjects in HOD's department
        # ---------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM subject s
            INNER JOIN course c
                ON s.course_id = c.course_id
            WHERE c.department_id = %s
        """, (
            session["hod_department_id"],
        ))

        subject_result = cursor.fetchone()

        cursor.close()
        connection.close()

        return render_template(
            "hod/dashboard.html",
            hod_name=session.get("hod_name"),
            department=department,
            total_teachers=teacher_result["total"],
            total_students=student_result["total"],
            total_subjects=subject_result["total"]
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# HOD LOGOUT
# ===========================================================

@hod_bp.route("/logout")
def logout():

    # Remove HOD session
    session.clear()

    return redirect(
        url_for("auth.hod_login")
    )


# ===========================================================
# VIEW STUDENTS
# ===========================================================

@hod_bp.route("/students")
def students():

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # Get students belonging to HOD's department
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                st.student_id,
                st.register_number,
                st.full_name,
                st.email,
                st.phone,
                st.account_status,
                c.course_name,
                sem.semester_number
            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            INNER JOIN semester sem
                ON st.semester_id = sem.semester_id

            WHERE c.department_id = %s

            ORDER BY
                c.course_name,
                sem.semester_number,
                st.full_name
        """, (
            session["hod_department_id"],
        ))

        students = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "hod/students.html",
            students=students
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# APPROVE STUDENTS
# ===========================================================

@hod_bp.route("/approve-students")
def approve_students():

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Get pending students belonging to HOD's department
        cursor.execute("""
            SELECT
                st.student_id,
                st.register_number,
                st.full_name,
                st.email,
                st.phone,
                st.account_status,
                c.course_name,
                sem.semester_number
            FROM student st

            INNER JOIN course c
                ON st.course_id = c.course_id

            INNER JOIN semester sem
                ON st.semester_id = sem.semester_id

            WHERE c.department_id = %s
              AND st.account_status = 'Pending'

            ORDER BY st.full_name
        """, (
            session["hod_department_id"],
        ))

        students = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "hod/approve_students.html",
            students=students
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# APPROVE STUDENT
# ===========================================================

@hod_bp.route(
    "/approve-student/<int:student_id>",
    methods=["POST"]
)
def approve_student(student_id):

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Make sure the student belongs to this HOD's department
        cursor.execute("""
            UPDATE student st
            INNER JOIN course c
                ON st.course_id = c.course_id

            SET st.account_status = 'Active'

            WHERE st.student_id = %s
              AND c.department_id = %s
              AND st.account_status = 'Pending'
        """, (
            student_id,
            session["hod_department_id"]
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.approve_students")
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# REJECT STUDENT
# ===========================================================

@hod_bp.route(
    "/reject-student/<int:student_id>",
    methods=["POST"]
)
def reject_student(student_id):

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Make sure the student belongs to this HOD's department
        cursor.execute("""
            UPDATE student st
            INNER JOIN course c
                ON st.course_id = c.course_id

            SET st.account_status = 'Inactive'

            WHERE st.student_id = %s
              AND c.department_id = %s
              AND st.account_status = 'Pending'
        """, (
            student_id,
            session["hod_department_id"]
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.approve_students")
        )

    except Exception as e:

        return f"Database Error: {e}"
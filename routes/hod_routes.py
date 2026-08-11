from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for
)

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
            SELECT COUNT(DISTINCT t.teacher_id) AS total
            FROM teacher t

            WHERE t.department_id = %s
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
        return redirect(url_for("auth.hod_login"))

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

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

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

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

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

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

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


# ===========================================================
# MANAGE TEACHERS
# ===========================================================

@hod_bp.route("/teachers")
def teachers():

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

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
                account_status,
                created_at

            FROM teacher

            WHERE department_id = %s

            ORDER BY full_name

        """, (
            session["hod_department_id"],
        ))

        teachers = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "hod/manage_teachers.html",
            teachers=teachers
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# CHANGE TEACHER STATUS
# ===========================================================

@hod_bp.route(
    "/teachers/status/<int:teacher_id>",
    methods=["POST"]
)
def change_teacher_status(teacher_id):

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    status = request.form.get("status")

    allowed_statuses = [
        "Pending",
        "Active",
        "Inactive"
    ]

    if status not in allowed_statuses:
        return "Invalid teacher status."

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE teacher

            SET account_status = %s

            WHERE teacher_id = %s
              AND department_id = %s

        """, (
            status,
            teacher_id,
            session["hod_department_id"]
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.teachers")
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# TEACHER SUBJECT ASSIGNMENT
# ===========================================================

@hod_bp.route("/teacher-assignments")
def teacher_assignments():

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET ACTIVE TEACHERS
        # ---------------------------------------------------

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

        # ---------------------------------------------------
        # GET ACTIVE SUBJECTS
        # ---------------------------------------------------

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

        # ---------------------------------------------------
        # GET ACADEMIC YEARS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                academic_year_id,
                academic_year_name

            FROM academic_year

            ORDER BY start_date DESC

        """)

        academic_years = cursor.fetchall()

        # ---------------------------------------------------
        # GET CURRENT ASSIGNMENTS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                tsa.assignment_id,

                t.teacher_id,
                t.employee_id,
                t.full_name AS teacher_name,

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
                ay.start_date DESC,
                c.course_name,
                sem.semester_number

        """, (
            session["hod_department_id"],
        ))

        assignments = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "hod/teacher_assignments.html",
            teachers=teachers,
            subjects=subjects,
            academic_years=academic_years,
            assignments=assignments
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# ADD TEACHER SUBJECT ASSIGNMENT
# ===========================================================

@hod_bp.route(
    "/teacher-assignments/add",
    methods=["POST"]
)
def add_teacher_assignment():

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    teacher_id = request.form.get("teacher_id")
    subject_id = request.form.get("subject_id")
    academic_year_id = request.form.get("academic_year_id")

    if not teacher_id or not subject_id or not academic_year_id:
        return "All assignment fields are required."

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # CHECK TEACHER
        # ---------------------------------------------------

        cursor.execute("""
            SELECT teacher_id

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

            cursor.close()
            connection.close()

            return "Invalid teacher or teacher does not belong to your department."

        # ---------------------------------------------------
        # CHECK SUBJECT
        # ---------------------------------------------------

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

            cursor.close()
            connection.close()

            return "Invalid subject or subject does not belong to your department."

        # ---------------------------------------------------
        # CHECK ACADEMIC YEAR
        # ---------------------------------------------------

        cursor.execute("""
            SELECT academic_year_id

            FROM academic_year

            WHERE academic_year_id = %s

        """, (
            academic_year_id,
        ))

        academic_year = cursor.fetchone()

        if not academic_year:

            cursor.close()
            connection.close()

            return "Invalid academic year."

        # ---------------------------------------------------
        # CHECK DUPLICATE ASSIGNMENT
        # ---------------------------------------------------

        cursor.execute("""
            SELECT assignment_id

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

            cursor.close()
            connection.close()

            return "This teacher is already assigned to this subject for this academic year."

        # ---------------------------------------------------
        # CREATE ASSIGNMENT
        # ---------------------------------------------------

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

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.teacher_assignments")
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# CHANGE TEACHER ASSIGNMENT STATUS
# ===========================================================

@hod_bp.route(
    "/teacher-assignments/status/<int:assignment_id>",
    methods=["POST"]
)
def change_assignment_status(assignment_id):

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    status = request.form.get("status")

    if status not in [
        "Active",
        "Inactive"
    ]:
        return "Invalid assignment status."

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE teacher_subject_assignment tsa

            INNER JOIN subject s
                ON tsa.subject_id = s.subject_id

            INNER JOIN course c
                ON s.course_id = c.course_id

            SET tsa.status = %s

            WHERE tsa.assignment_id = %s
              AND c.department_id = %s

        """, (
            status,
            assignment_id,
            session["hod_department_id"]
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.teacher_assignments")
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# APPROVE QUESTION PAPERS - VIEW PAGE
# ===========================================================

@hod_bp.route("/approve-papers")
def approve_papers():

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

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

            ORDER BY qp.upload_date DESC

        """, (
            session["hod_department_id"],
        ))

        papers = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "hod/approve_papers.html",
            papers=papers
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# APPROVE QUESTION PAPER
# ===========================================================

@hod_bp.route(
    "/approve-question-paper/<int:question_paper_id>",
    methods=["POST"]
)
def approve_question_paper(question_paper_id):

    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

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

            SET qp.approved_by_hod = 1

            WHERE qp.question_paper_id = %s
              AND c.department_id = %s
              AND qp.approved_by_hod = 0

        """, (
            question_paper_id,
            session["hod_department_id"]
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.approve_papers")
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# APPROVE STUDY MATERIALS - VIEW PAGE
# ===========================================================

@hod_bp.route("/approve-materials")
def approve_materials():

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

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

            ORDER BY sm.upload_date DESC

        """, (
            session["hod_department_id"],
        ))

        materials = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "hod/approve_materials.html",
            materials=materials
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# APPROVE STUDY MATERIAL
# ===========================================================

@hod_bp.route(
    "/approve-study-material/<int:study_material_id>",
    methods=["POST"]
)
def approve_study_material(study_material_id):

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

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

            SET sm.approved_by_hod = 1

            WHERE sm.study_material_id = %s
              AND c.department_id = %s
              AND sm.approved_by_hod = 0

        """, (
            study_material_id,
            session["hod_department_id"]
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.approve_materials")
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# MANAGE SUBJECTS
# ===========================================================

@hod_bp.route("/subjects")
def manage_subjects():

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET COURSES
        # ---------------------------------------------------

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

        # ---------------------------------------------------
        # GET SEMESTERS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                semester_id,
                semester_number

            FROM semester

            ORDER BY semester_number

        """)

        semesters = cursor.fetchall()

        # ---------------------------------------------------
        # GET SUBJECTS
        # ---------------------------------------------------

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

        cursor.close()
        connection.close()

        return render_template(
            "hod/manage_subject.html",
            courses=courses,
            semesters=semesters,
            subjects=subjects
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# ADD SUBJECT
# ===========================================================

@hod_bp.route(
    "/subjects/add",
    methods=["POST"]
)
def add_subject():

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    course_id = request.form.get("course_id")
    semester_id = request.form.get("semester_id")
    subject_code = request.form.get("subject_code")
    subject_name = request.form.get("subject_name")
    credits = request.form.get("credits")

    # Check required fields
    if not course_id or not semester_id or not subject_code or not subject_name or not credits:
        return "All subject fields are required."

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # VERIFY COURSE BELONGS TO HOD'S DEPARTMENT
        # ---------------------------------------------------

        cursor.execute("""
            SELECT course_id
            FROM course
            WHERE course_id = %s
              AND department_id = %s
        """, (
            course_id,
            session["hod_department_id"]
        ))

        course = cursor.fetchone()

        if not course:

            cursor.close()
            connection.close()

            return "Invalid course or course does not belong to your department."

        # ---------------------------------------------------
        # VERIFY SEMESTER EXISTS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT semester_id
            FROM semester
            WHERE semester_id = %s
        """, (
            semester_id,
        ))

        semester = cursor.fetchone()

        if not semester:

            cursor.close()
            connection.close()

            return "Invalid semester."

        # ---------------------------------------------------
        # CHECK DUPLICATE SUBJECT CODE
        # ---------------------------------------------------

        cursor.execute("""
            SELECT s.subject_id
            FROM subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            WHERE s.subject_code = %s
              AND c.department_id = %s
        """, (
            subject_code,
            session["hod_department_id"]
        ))

        existing_subject = cursor.fetchone()

        if existing_subject:

            cursor.close()
            connection.close()

            return "This subject code already exists in your department."

        # ---------------------------------------------------
        # ADD SUBJECT
        # ---------------------------------------------------

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

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.manage_subjects")
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# CHANGE SUBJECT STATUS
# ===========================================================

@hod_bp.route(
    "/subjects/status/<int:subject_id>",
    methods=["POST"]
)
def change_subject_status(subject_id):

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    status = request.form.get("status")

    # Only these two statuses are allowed
    if status not in ["Active", "Inactive"]:
        return "Invalid subject status."

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Change status only if the subject
        # belongs to this HOD's department
        cursor.execute("""
            UPDATE subject s

            INNER JOIN course c
                ON s.course_id = c.course_id

            SET s.status = %s

            WHERE s.subject_id = %s
              AND c.department_id = %s

        """, (
            status,
            subject_id,
            session["hod_department_id"]
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.manage_subjects")
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# EDIT SUBJECT
# ===========================================================

@hod_bp.route(
    "/subjects/edit/<int:subject_id>",
    methods=["GET", "POST"]
)
def edit_subject(subject_id):

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # GET SUBJECT
        # ---------------------------------------------------

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

            cursor.close()
            connection.close()

            return "Subject not found or it does not belong to your department."

        # ---------------------------------------------------
        # GET COURSES
        # ---------------------------------------------------

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

        # ---------------------------------------------------
        # GET SEMESTERS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                semester_id,
                semester_number

            FROM semester

            ORDER BY semester_number

        """)

        semesters = cursor.fetchall()

        # ---------------------------------------------------
        # UPDATE SUBJECT
        # ---------------------------------------------------

        if request.method == "POST":

            course_id = request.form.get("course_id")
            semester_id = request.form.get("semester_id")
            subject_code = request.form.get("subject_code")
            subject_name = request.form.get("subject_name")
            credits = request.form.get("credits")

            if not course_id or not semester_id or not subject_code or not subject_name or not credits:

                cursor.close()
                connection.close()

                return "All subject fields are required."

            # -----------------------------------------------
            # VERIFY COURSE
            # -----------------------------------------------

            cursor.execute("""
                SELECT course_id

                FROM course

                WHERE course_id = %s
                  AND department_id = %s

            """, (
                course_id,
                session["hod_department_id"]
            ))

            valid_course = cursor.fetchone()

            if not valid_course:

                cursor.close()
                connection.close()

                return "Invalid course."

            # -----------------------------------------------
            # VERIFY SEMESTER
            # -----------------------------------------------

            cursor.execute("""
                SELECT semester_id

                FROM semester

                WHERE semester_id = %s

            """, (
                semester_id,
            ))

            valid_semester = cursor.fetchone()

            if not valid_semester:

                cursor.close()
                connection.close()

                return "Invalid semester."

            # -----------------------------------------------
            # CHECK DUPLICATE SUBJECT CODE
            # -----------------------------------------------

            cursor.execute("""
                SELECT s.subject_id

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

            duplicate = cursor.fetchone()

            if duplicate:

                cursor.close()
                connection.close()

                return "This subject code already exists in your department."

            # -----------------------------------------------
            # UPDATE SUBJECT
            # -----------------------------------------------

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

            cursor.close()
            connection.close()

            return redirect(
                url_for("hod.manage_subjects")
            )

        cursor.close()
        connection.close()

        return render_template(
            "hod/edit_subject.html",
            subject=subject,
            courses=courses,
            semesters=semesters
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# DELETE SUBJECT
# ===========================================================

@hod_bp.route(
    "/subjects/delete/<int:subject_id>",
    methods=["POST"]
)
def delete_subject(subject_id):

    # Check whether HOD is logged in
    if "hod_id" not in session:
        return redirect(url_for("auth.hod_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # CHECK WHETHER SUBJECT BELONGS TO HOD'S DEPARTMENT
        # ---------------------------------------------------

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

            cursor.close()
            connection.close()

            return "Subject not found or it does not belong to your department."

        # ---------------------------------------------------
        # CHECK TEACHER ASSIGNMENTS
        # ---------------------------------------------------

        cursor.execute("""
            SELECT assignment_id

            FROM teacher_subject_assignment

            WHERE subject_id = %s

            LIMIT 1

        """, (
            subject_id,
        ))

        teacher_assignment = cursor.fetchone()

        if teacher_assignment:

            cursor.close()
            connection.close()

            return (
                "This subject cannot be deleted because "
                "it is already assigned to a teacher. "
                "Deactivate the subject instead."
            )

        # ---------------------------------------------------
        # DELETE SUBJECT
        # ---------------------------------------------------

        cursor.execute("""
            DELETE FROM subject

            WHERE subject_id = %s

        """, (
            subject_id,
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("hod.manage_subjects")
        )

    except Exception as e:

        return f"Database Error: {e}"
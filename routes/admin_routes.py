from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request
)

from database.db_connection import get_connection

from werkzeug.security import generate_password_hash


# ===========================================================
# ADMIN BLUEPRINT
# ===========================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ===========================================================
# ADMIN LOGIN CHECK
# ===========================================================

def admin_required():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    return None


# ===========================================================
# ADMIN DASHBOARD
# ===========================================================

@admin_bp.route("/dashboard")
def dashboard():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ===================================================
        # TOTAL DEPARTMENTS
        # ===================================================

        cursor.execute("""
            SELECT COUNT(*) AS total_departments
            FROM department
        """)

        total_departments = cursor.fetchone()["total_departments"]


        # ===================================================
        # TOTAL STUDENTS
        # ===================================================

        cursor.execute("""
            SELECT COUNT(*) AS total_students
            FROM student
        """)

        total_students = cursor.fetchone()["total_students"]


        # ===================================================
        # TOTAL TEACHERS
        # ===================================================

        cursor.execute("""
            SELECT COUNT(*) AS total_teachers
            FROM teacher
        """)

        total_teachers = cursor.fetchone()["total_teachers"]


        # ===================================================
        # TOTAL HODS
        # ===================================================

        cursor.execute("""
            SELECT COUNT(*) AS total_hods
            FROM hod
        """)

        total_hods = cursor.fetchone()["total_hods"]


        # ===================================================
        # TOTAL COURSES
        # ===================================================

        cursor.execute("""
            SELECT COUNT(*) AS total_courses
            FROM course
        """)

        total_courses = cursor.fetchone()["total_courses"]


        # ===================================================
        # DEPARTMENT-WISE SUMMARY
        #
        # Department
        #     |
        #     +---- Courses
        #              |
        #              +---- Students
        #
        # Department
        #     |
        #     +---- Teachers
        #
        # Department
        #     |
        #     +---- HOD
        # ===================================================

        cursor.execute("""
            SELECT

                d.department_id,

                d.department_name,

                COUNT(DISTINCT s.student_id)
                    AS student_count,

                COUNT(DISTINCT t.teacher_id)
                    AS teacher_count,

                MAX(h.full_name)
                    AS hod_name

            FROM department d

            LEFT JOIN course c
                ON d.department_id = c.department_id

            LEFT JOIN student s
                ON c.course_id = s.course_id

            LEFT JOIN teacher t
                ON d.department_id = t.department_id

            LEFT JOIN hod h
                ON d.department_id = h.department_id
                AND h.account_status = 'Active'

            GROUP BY
                d.department_id,
                d.department_name

            ORDER BY
                d.department_name
        """)

        department_summary = cursor.fetchall()


        # ===================================================
        # GET ALL DEPARTMENTS
        # ===================================================

        cursor.execute("""
            SELECT
                department_id,
                department_name,
                status
            FROM department
            ORDER BY department_name
        """)

        departments = cursor.fetchall()


        # ===================================================
        # RENDER DASHBOARD
        # ===================================================

        return render_template(
            "admin/dashboard.html",

            username=session.get("admin_username"),

            departments=departments,

            department_summary=department_summary,

            total_departments=total_departments,

            total_students=total_students,

            total_teachers=total_teachers,

            total_hods=total_hods,

            total_courses=total_courses
        )


    except Exception as e:

        return f"Database Error: {e}"


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADMIN LOGOUT
# ===========================================================

@admin_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.admin_login")
    )


# ===========================================================
# DEPARTMENT MANAGEMENT
# ===========================================================

@admin_bp.route("/departments")
def departments():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                department_id,
                department_name,
                status,
                created_at
            FROM department
            ORDER BY department_name
        """)

        departments = cursor.fetchall()

        return render_template(
            "admin/manage_department.html",
            departments=departments
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADD DEPARTMENT
# ===========================================================

@admin_bp.route(
    "/departments/add",
    methods=["POST"]
)
def add_department():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    department_name = request.form.get(
        "department_name",
        ""
    ).strip()

    if not department_name:
        return redirect(
            url_for("admin.departments")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO department
            (
                department_name
            )
            VALUES (%s)
        """, (
            department_name,
        ))

        connection.commit()

        return redirect(
            url_for("admin.departments")
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
# DELETE DEPARTMENT
# ===========================================================

@admin_bp.route(
    "/departments/delete/<int:department_id>",
    methods=["POST"]
)
def delete_department(department_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM department
            WHERE department_id = %s
        """, (
            department_id,
        ))

        connection.commit()

        return redirect(
            url_for("admin.departments")
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
# COURSE MANAGEMENT
# ===========================================================

@admin_bp.route("/courses")
def courses():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                c.course_id,
                c.department_id,
                c.course_name,
                c.duration_years,
                c.status,
                c.created_at,
                c.updated_at,
                d.department_name

            FROM course c

            INNER JOIN department d
                ON c.department_id = d.department_id

            ORDER BY c.course_id
        """)

        courses = cursor.fetchall()


        cursor.execute("""
            SELECT
                department_id,
                department_name

            FROM department

            ORDER BY department_name
        """)

        departments = cursor.fetchall()


        return render_template(
            "admin/manage_course.html",
            courses=courses,
            departments=departments
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADD COURSE
# ===========================================================

@admin_bp.route(
    "/courses/add",
    methods=["POST"]
)
def add_course():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    department_id = request.form.get(
        "department_id"
    )

    course_name = request.form.get(
        "course_name",
        ""
    ).strip()

    duration_years = request.form.get(
        "duration_years"
    )

    if (
        not department_id
        or not course_name
        or not duration_years
    ):
        return "All course fields are required."


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO course
            (
                department_id,
                course_name,
                duration_years
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
        """, (
            department_id,
            course_name,
            duration_years
        ))

        connection.commit()

        return redirect(
            url_for("admin.courses")
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
# EDIT COURSE
# ===========================================================

@admin_bp.route(
    "/courses/edit/<int:course_id>",
    methods=["GET", "POST"]
)
def edit_course(course_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        if request.method == "POST":

            department_id = request.form.get(
                "department_id"
            )

            course_name = request.form.get(
                "course_name",
                ""
            ).strip()

            duration_years = request.form.get(
                "duration_years"
            )

            if (
                not department_id
                or not course_name
                or not duration_years
            ):
                return "All course fields are required."


            cursor.execute("""
                UPDATE course

                SET
                    department_id = %s,
                    course_name = %s,
                    duration_years = %s

                WHERE course_id = %s
            """, (
                department_id,
                course_name,
                duration_years,
                course_id
            ))

            connection.commit()

            return redirect(
                url_for("admin.courses")
            )


        cursor.execute("""
            SELECT
                course_id,
                department_id,
                course_name,
                duration_years,
                status,
                created_at,
                updated_at

            FROM course

            WHERE course_id = %s
        """, (
            course_id,
        ))

        course = cursor.fetchone()


        if not course:
            return "Course not found."


        cursor.execute("""
            SELECT
                department_id,
                department_name

            FROM department

            ORDER BY department_name
        """)

        departments = cursor.fetchall()


        return render_template(
            "admin/edit_course.html",
            course=course,
            departments=departments
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
# DELETE COURSE
# ===========================================================

@admin_bp.route(
    "/courses/delete/<int:course_id>",
    methods=["POST"]
)
def delete_course(course_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM course
            WHERE course_id = %s
        """, (
            course_id,
        ))

        connection.commit()

        return redirect(
            url_for("admin.courses")
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
# ACADEMIC YEAR MANAGEMENT
# ===========================================================

@admin_bp.route("/academic-years")
def academic_years():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                academic_year_id,
                academic_year_name,
                start_date,
                end_date,
                status,
                created_at,
                updated_at

            FROM academic_year

            ORDER BY start_date DESC
        """)

        academic_years = cursor.fetchall()

        return render_template(
            "admin/manage_academic_year.html",
            academic_years=academic_years
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADD ACADEMIC YEAR
# ===========================================================

@admin_bp.route(
    "/academic-years/add",
    methods=["POST"]
)
def add_academic_year():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    academic_year_name = request.form.get(
        "academic_year_name",
        ""
    ).strip()

    start_date = request.form.get(
        "start_date"
    )

    end_date = request.form.get(
        "end_date"
    )

    if (
        not academic_year_name
        or not start_date
        or not end_date
    ):
        return "All academic year fields are required."


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO academic_year
            (
                academic_year_name,
                start_date,
                end_date
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
        """, (
            academic_year_name,
            start_date,
            end_date
        ))

        connection.commit()

        return redirect(
            url_for("admin.academic_years")
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
# EDIT ACADEMIC YEAR
# ===========================================================

@admin_bp.route(
    "/academic-years/edit/<int:academic_year_id>",
    methods=["GET", "POST"]
)
def edit_academic_year(academic_year_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        if request.method == "POST":

            academic_year_name = request.form.get(
                "academic_year_name",
                ""
            ).strip()

            start_date = request.form.get(
                "start_date"
            )

            end_date = request.form.get(
                "end_date"
            )

            status = request.form.get(
                "status"
            )

            allowed_statuses = [
                "Current",
                "Completed",
                "Upcoming"
            ]

            if (
                not academic_year_name
                or not start_date
                or not end_date
                or status not in allowed_statuses
            ):
                return "Invalid academic year information."


            cursor.execute("""
                UPDATE academic_year

                SET
                    academic_year_name = %s,
                    start_date = %s,
                    end_date = %s,
                    status = %s

                WHERE academic_year_id = %s
            """, (
                academic_year_name,
                start_date,
                end_date,
                status,
                academic_year_id
            ))

            connection.commit()

            return redirect(
                url_for("admin.academic_years")
            )


        cursor.execute("""
            SELECT
                academic_year_id,
                academic_year_name,
                start_date,
                end_date,
                status,
                created_at,
                updated_at

            FROM academic_year

            WHERE academic_year_id = %s
        """, (
            academic_year_id,
        ))

        academic_year = cursor.fetchone()


        if not academic_year:
            return "Academic year not found."


        return render_template(
            "admin/edit_academic_year.html",
            academic_year=academic_year
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
# DELETE ACADEMIC YEAR
# ===========================================================

@admin_bp.route(
    "/academic-years/delete/<int:academic_year_id>",
    methods=["POST"]
)
def delete_academic_year(academic_year_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM academic_year
            WHERE academic_year_id = %s
        """, (
            academic_year_id,
        ))

        connection.commit()

        return redirect(
            url_for("admin.academic_years")
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
# CHANGE ACADEMIC YEAR STATUS
# ===========================================================

@admin_bp.route(
    "/academic-years/status/<int:academic_year_id>",
    methods=["POST"]
)
def change_academic_year_status(academic_year_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    status = request.form.get("status")

    allowed_statuses = [
        "Current",
        "Completed",
        "Upcoming"
    ]

    if status not in allowed_statuses:
        return "Invalid academic year status."


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE academic_year

            SET
                status = %s

            WHERE academic_year_id = %s
        """, (
            status,
            academic_year_id
        ))

        connection.commit()

        return redirect(
            url_for("admin.academic_years")
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
# EXAM TYPE MANAGEMENT
# ===========================================================

@admin_bp.route("/exam-types")
def exam_types():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                exam_type_id,
                exam_type_name,
                status,
                created_at

            FROM exam_type

            ORDER BY exam_type_name
        """)

        exam_types = cursor.fetchall()

        return render_template(
            "admin/manage_exam_type.html",
            exam_types=exam_types
        )

    except Exception as e:

        return f"Database Error: {e}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADD EXAM TYPE
# ===========================================================

@admin_bp.route(
    "/exam-types/add",
    methods=["POST"]
)
def add_exam_type():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    exam_type_name = request.form.get(
        "exam_type_name",
        ""
    ).strip()

    if not exam_type_name:
        return redirect(
            url_for("admin.exam_types")
        )


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO exam_type
            (
                exam_type_name
            )
            VALUES (%s)
        """, (
            exam_type_name,
        ))

        connection.commit()

        return redirect(
            url_for("admin.exam_types")
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
# EDIT EXAM TYPE
# ===========================================================

@admin_bp.route(
    "/exam-types/edit/<int:exam_type_id>",
    methods=["GET", "POST"]
)
def edit_exam_type(exam_type_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        if request.method == "POST":

            exam_type_name = request.form.get(
                "exam_type_name",
                ""
            ).strip()

            status = request.form.get(
                "status",
                ""
            )

            allowed_statuses = [
                "Active",
                "Inactive"
            ]

            if (
                not exam_type_name
                or status not in allowed_statuses
            ):
                return "Invalid exam type information."


            cursor.execute("""
                UPDATE exam_type

                SET
                    exam_type_name = %s,
                    status = %s

                WHERE exam_type_id = %s
            """, (
                exam_type_name,
                status,
                exam_type_id
            ))

            connection.commit()

            return redirect(
                url_for("admin.exam_types")
            )


        cursor.execute("""
            SELECT
                exam_type_id,
                exam_type_name,
                status,
                created_at

            FROM exam_type

            WHERE exam_type_id = %s
        """, (
            exam_type_id,
        ))

        exam_type = cursor.fetchone()


        if not exam_type:
            return "Exam type not found."


        return render_template(
            "admin/edit_exam_type.html",
            exam_type=exam_type
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
# DELETE EXAM TYPE
# ===========================================================

@admin_bp.route(
    "/exam-types/delete/<int:exam_type_id>",
    methods=["POST"]
)
def delete_exam_type(exam_type_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM exam_type

            WHERE exam_type_id = %s
        """, (
            exam_type_id,
        ))

        connection.commit()

        return redirect(
            url_for("admin.exam_types")
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
# CHANGE EXAM TYPE STATUS
# ===========================================================

@admin_bp.route(
    "/exam-types/status/<int:exam_type_id>",
    methods=["POST"]
)
def change_exam_type_status(exam_type_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    status = request.form.get("status")

    allowed_statuses = [
        "Active",
        "Inactive"
    ]

    if status not in allowed_statuses:
        return "Invalid exam type status."


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE exam_type

            SET
                status = %s

            WHERE exam_type_id = %s
        """, (
            status,
            exam_type_id
        ))

        connection.commit()

        return redirect(
            url_for("admin.exam_types")
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
# SEMESTER MANAGEMENT
# ===========================================================

@admin_bp.route("/semesters")
def semesters():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                s.semester_id,
                s.course_id,
                s.semester_number,
                s.status,
                s.created_at,
                s.updated_at,
                c.course_name

            FROM semester s

            INNER JOIN course c
                ON s.course_id = c.course_id

            ORDER BY
                c.course_name,
                s.semester_number
        """)

        semesters = cursor.fetchall()


        cursor.execute("""
            SELECT
                course_id,
                course_name

            FROM course

            ORDER BY course_name
        """)

        courses = cursor.fetchall()


        return render_template(
            "admin/manage_semester.html",
            semesters=semesters,
            courses=courses
        )


    except Exception as e:

        return f"Database Error: {e}"


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADD SEMESTER
# ===========================================================

@admin_bp.route(
    "/semesters/add",
    methods=["POST"]
)
def add_semester():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    course_id = request.form.get(
        "course_id"
    )

    semester_number = request.form.get(
        "semester_number"
    )

    if (
        not course_id
        or not semester_number
    ):
        return "All semester fields are required."


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO semester
            (
                course_id,
                semester_number
            )
            VALUES
            (
                %s,
                %s
            )
        """, (
            course_id,
            semester_number
        ))

        connection.commit()

        return redirect(
            url_for("admin.semesters")
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
# EDIT SEMESTER
# ===========================================================

@admin_bp.route(
    "/semesters/edit/<int:semester_id>",
    methods=["GET", "POST"]
)
def edit_semester(semester_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        if request.method == "POST":

            course_id = request.form.get(
                "course_id"
            )

            semester_number = request.form.get(
                "semester_number"
            )

            if (
                not course_id
                or not semester_number
            ):
                return "All semester fields are required."


            cursor.execute("""
                UPDATE semester

                SET
                    course_id = %s,
                    semester_number = %s

                WHERE semester_id = %s
            """, (
                course_id,
                semester_number,
                semester_id
            ))

            connection.commit()

            return redirect(
                url_for("admin.semesters")
            )


        cursor.execute("""
            SELECT
                semester_id,
                course_id,
                semester_number,
                status,
                created_at,
                updated_at

            FROM semester

            WHERE semester_id = %s
        """, (
            semester_id,
        ))

        semester = cursor.fetchone()


        if not semester:
            return "Semester not found."


        cursor.execute("""
            SELECT
                course_id,
                course_name

            FROM course

            ORDER BY course_name
        """)

        courses = cursor.fetchall()


        return render_template(
            "admin/edit_semester.html",
            semester=semester,
            courses=courses
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
# DELETE SEMESTER
# ===========================================================

@admin_bp.route(
    "/semesters/delete/<int:semester_id>",
    methods=["POST"]
)
def delete_semester(semester_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM semester

            WHERE semester_id = %s
        """, (
            semester_id,
        ))

        connection.commit()

        return redirect(
            url_for("admin.semesters")
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
# CHANGE SEMESTER STATUS
# ===========================================================

@admin_bp.route(
    "/semesters/status/<int:semester_id>",
    methods=["POST"]
)
def change_semester_status(semester_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    status = request.form.get(
        "status"
    )

    allowed_statuses = [
        "Active",
        "Inactive"
    ]

    if status not in allowed_statuses:
        return "Invalid semester status."


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE semester

            SET
                status = %s

            WHERE semester_id = %s
        """, (
            status,
            semester_id
        ))

        connection.commit()

        return redirect(
            url_for("admin.semesters")
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
# HOD ACCOUNT MANAGEMENT
# ===========================================================

@admin_bp.route("/hod-accounts")
def hod_accounts():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                h.hod_id,
                h.department_id,
                h.employee_id,
                h.full_name,
                h.email,
                h.phone,
                h.username,
                h.account_status,
                h.created_at,
                h.updated_at,
                d.department_name

            FROM hod h

            INNER JOIN department d
                ON h.department_id = d.department_id

            ORDER BY h.hod_id
        """)

        hods = cursor.fetchall()


        cursor.execute("""
            SELECT
                department_id,
                department_name

            FROM department

            WHERE status = 'Active'

            ORDER BY department_name
        """)

        departments = cursor.fetchall()


        return render_template(
            "admin/manage_hod.html",
            hods=hods,
            departments=departments
        )


    except Exception as e:

        return f"Database Error: {e}"


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# ADD HOD
# ===========================================================

@admin_bp.route(
    "/hod-accounts/add",
    methods=["POST"]
)
def add_hod():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    department_id = request.form.get(
        "department_id"
    )

    employee_id = request.form.get(
        "employee_id",
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


    if (
        not department_id
        or not employee_id
        or not full_name
        or not email
        or not username
        or not password
    ):
        return "All required HOD fields are required."


    hashed_password = generate_password_hash(
        password
    )


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO hod
            (
                department_id,
                employee_id,
                full_name,
                email,
                phone,
                username,
                password,
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
                'Pending'
            )
        """, (
            department_id,
            employee_id,
            full_name,
            email,
            phone,
            username,
            hashed_password
        ))

        connection.commit()

        return redirect(
            url_for("admin.hod_accounts")
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
# EDIT HOD
# ===========================================================

@admin_bp.route(
    "/hod-accounts/edit/<int:hod_id>",
    methods=["GET", "POST"]
)
def edit_hod(hod_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        if request.method == "POST":

            department_id = request.form.get(
                "department_id"
            )

            employee_id = request.form.get(
                "employee_id",
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


            if (
                not department_id
                or not employee_id
                or not full_name
                or not email
                or not username
            ):
                return "All required HOD fields are required."


            cursor.execute("""
                UPDATE hod

                SET
                    department_id = %s,
                    employee_id = %s,
                    full_name = %s,
                    email = %s,
                    phone = %s,
                    username = %s

                WHERE hod_id = %s
            """, (
                department_id,
                employee_id,
                full_name,
                email,
                phone,
                username,
                hod_id
            ))

            connection.commit()

            return redirect(
                url_for("admin.hod_accounts")
            )


        cursor.execute("""
            SELECT
                hod_id,
                department_id,
                employee_id,
                full_name,
                email,
                phone,
                username,
                account_status,
                created_at,
                updated_at

            FROM hod

            WHERE hod_id = %s
        """, (
            hod_id,
        ))

        hod = cursor.fetchone()


        if not hod:
            return "HOD account not found."


        cursor.execute("""
            SELECT
                department_id,
                department_name

            FROM department

            WHERE status = 'Active'

            ORDER BY department_name
        """)

        departments = cursor.fetchall()


        return render_template(
            "admin/edit_hod.html",
            hod=hod,
            departments=departments
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
# DELETE HOD
# ===========================================================

@admin_bp.route(
    "/hod-accounts/delete/<int:hod_id>",
    methods=["POST"]
)
def delete_hod(hod_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM hod

            WHERE hod_id = %s
        """, (
            hod_id,
        ))

        connection.commit()

        return redirect(
            url_for("admin.hod_accounts")
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
# CHANGE HOD STATUS
# ===========================================================

@admin_bp.route(
    "/hod-accounts/status/<int:hod_id>",
    methods=["POST"]
)
def change_hod_status(hod_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    account_status = request.form.get(
        "account_status"
    )

    allowed_statuses = [
        "Pending",
        "Active",
        "Inactive"
    ]

    if account_status not in allowed_statuses:
        return "Invalid HOD account status."


    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE hod

            SET
                account_status = %s

            WHERE hod_id = %s
        """, (
            account_status,
            hod_id
        ))

        connection.commit()

        return redirect(
            url_for("admin.hod_accounts")
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
# ALL STUDENTS
# ===========================================================

@admin_bp.route("/students")
def all_students():

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                s.student_id,
                s.register_number,
                s.full_name,
                s.email,
                s.phone,
                s.username,
                s.account_status,
                s.created_at,

                c.course_id,
                c.course_name,

                sem.semester_id,
                sem.semester_number,

                d.department_id,
                d.department_name

            FROM student s

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            INNER JOIN department d
                ON c.department_id = d.department_id

            ORDER BY
                d.department_name,
                c.course_name,
                sem.semester_number,
                s.full_name
        """)

        students = cursor.fetchall()


        return render_template(
            "admin/students.html",
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
# DEPARTMENT-WISE STUDENTS
# ===========================================================

@admin_bp.route(
    "/departments/<int:department_id>/students"
)
def department_students(department_id):

    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()


        # ===================================================
        # GET DEPARTMENT
        # ===================================================

        cursor.execute("""
            SELECT
                department_id,
                department_name,
                status

            FROM department

            WHERE department_id = %s
        """, (
            department_id,
        ))

        department = cursor.fetchone()


        if not department:
            return "Department not found."


        # ===================================================
        # GET STUDENTS
        # ===================================================

        cursor.execute("""
            SELECT
                s.student_id,
                s.register_number,
                s.full_name,
                s.email,
                s.phone,
                s.username,
                s.account_status,
                s.created_at,

                c.course_id,
                c.course_name,

                sem.semester_id,
                sem.semester_number

            FROM student s

            INNER JOIN course c
                ON s.course_id = c.course_id

            INNER JOIN semester sem
                ON s.semester_id = sem.semester_id

            WHERE c.department_id = %s

            ORDER BY
                c.course_name,
                sem.semester_number,
                s.full_name
        """, (
            department_id,
        ))

        students = cursor.fetchall()


        return render_template(
            "admin/department_students.html",
            department=department,
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
# ALL TEACHERS
# ===========================================================

@admin_bp.route("/teachers")
def all_teachers():

    if "admin_id" not in session:
        return redirect(
            url_for("auth.admin_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                t.teacher_id,
                t.employee_id,
                t.full_name,
                t.email,
                t.phone,
                t.username,
                t.account_status,
                t.created_at,

                t.department_id,

                d.department_name

            FROM teacher t

            LEFT JOIN department d
                ON t.department_id = d.department_id

            ORDER BY
                d.department_name,
                t.full_name
        """)

        teachers = cursor.fetchall()

        return render_template(
            "admin/teachers.html",
            teachers=teachers
        )


    except Exception as e:

        return f"Database Error: {e}"


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# DEPARTMENT-WISE TEACHERS
# ===========================================================

@admin_bp.route(
    "/departments/<int:department_id>/teachers"
)
def department_teachers(department_id):

    if "admin_id" not in session:
        return redirect(
            url_for("auth.admin_login")
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ===================================================
        # GET DEPARTMENT
        # ===================================================

        cursor.execute("""
            SELECT
                department_id,
                department_name,
                status
            FROM department
            WHERE department_id = %s
        """, (
            department_id,
        ))

        department = cursor.fetchone()

        if not department:
            return "Department not found."


        # ===================================================
        # GET TEACHERS
        # ===================================================
        #
        # IMPORTANT:
        # teacher.department_id must match
        # department.department_id
        #
        # Example:
        # teacher.department_id = 6
        # department.department_id = 6
        #
        # ===================================================

        cursor.execute("""
            SELECT
                t.teacher_id,
                t.employee_id,
                t.full_name,
                t.email,
                t.phone,
                t.username,
                t.account_status,
                t.created_at,
                t.department_id,

                d.department_id AS joined_department_id,
                d.department_name

            FROM teacher t

            LEFT JOIN department d
                ON t.department_id = d.department_id

            WHERE t.department_id = %s

            ORDER BY
                t.full_name ASC
        """, (
            department_id,
        ))

        teachers = cursor.fetchall()


        # ===================================================
        # DEBUG
        # ===================================================

        print()
        print("==========================================")
        print("DEPARTMENT-WISE TEACHER DEBUG")
        print("==========================================")

        print(
            "Requested Department ID:",
            department_id
        )

        print(
            "Department:",
            department
        )

        print(
            "Number of Teachers:",
            len(teachers)
        )

        for teacher in teachers:

            print(
                "Teacher ID:",
                teacher["teacher_id"]
            )

            print(
                "Employee ID:",
                teacher["employee_id"]
            )

            print(
                "Name:",
                teacher["full_name"]
            )

            print(
                "Teacher Department ID:",
                teacher["department_id"]
            )

            print(
                "Department Name:",
                teacher["department_name"]
            )

            print("------------------------------------------")

        print("==========================================")
        print()


        # ===================================================
        # RENDER PAGE
        # ===================================================

        return render_template(
            "admin/department_teachers.html",

            department=department,

            teachers=teachers
        )


    except Exception as e:

        print()
        print("==========================================")
        print("DEPARTMENT TEACHER ERROR")
        print("==========================================")
        print(repr(e))
        print("==========================================")
        print()

        return f"Database Error: {e}"


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request
)

from database.db_connection import get_connection


# ===========================================================
# ADMIN BLUEPRINT
# ===========================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ===========================================================
# ADMIN DASHBOARD
# ===========================================================

@admin_bp.route("/dashboard")
def dashboard():

    # Check whether admin is logged in
    if "admin_id" not in session:

        return redirect(url_for("auth.admin_login"))

    return render_template(
        "admin/dashboard.html",
        username=session.get("admin_username")
    )


# ===========================================================
# ADMIN LOGOUT
# ===========================================================

@admin_bp.route("/logout")
def logout():

    # Remove all session information
    session.clear()

    return redirect(url_for("auth.admin_login"))


# ===========================================================
# DEPARTMENT MANAGEMENT
# ===========================================================

@admin_bp.route("/departments")
def departments():

    # Check whether admin is logged in
    if "admin_id" not in session:

        return redirect(url_for("auth.admin_login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            department_id,
            department_name,
            created_at
        FROM department
        ORDER BY department_name
    """)

    departments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin/manage_department.html",
        departments=departments
    )


# ===========================================================
# ADD DEPARTMENT
# ===========================================================

@admin_bp.route("/departments/add", methods=["POST"])
def add_department():

    # Check whether admin is logged in
    if "admin_id" not in session:

        return redirect(url_for("auth.admin_login"))

    department_name = request.form.get(
        "department_name",
        ""
    ).strip()

    # Do not allow empty department names
    if not department_name:

        return redirect(
            url_for("admin.departments")
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO department (department_name)
            VALUES (%s)
            """,
            (department_name,)
        )

        connection.commit()

    except Exception:

        connection.rollback()

    finally:

        cursor.close()
        connection.close()

    return redirect(
        url_for("admin.departments")
    )


# ===========================================================
# DELETE DEPARTMENT
# ===========================================================

@admin_bp.route(
    "/departments/delete/<int:department_id>",
    methods=["POST"]
)
def delete_department(department_id):

    # Check whether admin is logged in
    if "admin_id" not in session:

        return redirect(url_for("auth.admin_login"))

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM department
            WHERE department_id = %s
            """,
            (department_id,)
        )

        connection.commit()

    except Exception:

        connection.rollback()

    finally:

        cursor.close()
        connection.close()

    return redirect(
        url_for("admin.departments")
    )


# ===========================================================
# COURSE MANAGEMENT
# ===========================================================

@admin_bp.route("/courses")
def courses():

    # Check whether admin is logged in
    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                c.course_id,
                c.course_name,
                c.duration_years,
                c.created_at,
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

        cursor.close()
        connection.close()

        return render_template(
            "admin/manage_course.html",
            courses=courses,
            departments=departments
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# ADD COURSE
# ===========================================================

@admin_bp.route("/courses/add", methods=["POST"])
def add_course():

    # Check whether admin is logged in
    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    department_id = request.form.get("department_id")
    course_name = request.form.get("course_name")
    duration_years = request.form.get("duration_years")

    if not department_id or not course_name or not duration_years:
        return "All course fields are required."

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
            VALUES (%s, %s, %s)
        """, (
            department_id,
            course_name,
            duration_years
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("admin.courses"))

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# EDIT COURSE
# ===========================================================

@admin_bp.route("/courses/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):

    # Check whether admin is logged in
    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # ---------------------------------------------------
        # POST = Save updated course
        # ---------------------------------------------------

        if request.method == "POST":

            department_id = request.form.get("department_id")
            course_name = request.form.get("course_name")
            duration_years = request.form.get("duration_years")

            if not department_id or not course_name or not duration_years:
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

            cursor.close()
            connection.close()

            return redirect(url_for("admin.courses"))

        # ---------------------------------------------------
        # GET = Display course for editing
        # ---------------------------------------------------

        cursor.execute("""
            SELECT
                course_id,
                department_id,
                course_name,
                duration_years
            FROM course
            WHERE course_id = %s
        """, (course_id,))

        course = cursor.fetchone()

        cursor.execute("""
            SELECT
                department_id,
                department_name
            FROM department
            ORDER BY department_name
        """)

        departments = cursor.fetchall()

        cursor.close()
        connection.close()

        if not course:
            return "Course not found."

        return render_template(
            "admin/edit_course.html",
            course=course,
            departments=departments
        )

    except Exception as e:

        return f"Database Error: {e}"


# ===========================================================
# DELETE COURSE
# ===========================================================

@admin_bp.route(
    "/courses/delete/<int:course_id>",
    methods=["POST"]
)
def delete_course(course_id):

    # Check whether admin is logged in
    if "admin_id" not in session:
        return redirect(url_for("auth.admin_login"))

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM course
            WHERE course_id = %s
        """, (course_id,))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("admin.courses"))

    except Exception as e:

        return f"Database Error: {e}"
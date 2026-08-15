from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from database.db_connection import get_connection

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)


auth_bp = Blueprint("auth", __name__)


# ===========================================================
# ADMIN LOGIN - DEBUG VERSION
# ===========================================================

@auth_bp.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            print("\n========================================")
            print("ADMIN LOGIN DEBUG")
            print("========================================")
            print("Username entered:", repr(username))

            # ---------------------------------------------------
            # FIND ADMIN ACCOUNT
            # ---------------------------------------------------

            cursor.execute(
                """
                SELECT
                    admin_id,
                    username,
                    password,
                    status
                FROM admin
                WHERE username = %s
                """,
                (username,)
            )

            admin = cursor.fetchone()

            print("Admin found:", admin is not None)

            # ---------------------------------------------------
            # ADMIN NOT FOUND
            # ---------------------------------------------------

            if not admin:

                print("RESULT: ADMIN USERNAME NOT FOUND")

                # Get ALL admin accounts visible to Flask
                cursor.execute(
                    """
                    SELECT
                        admin_id,
                        username,
                        status
                    FROM admin
                    """
                )

                all_admins = cursor.fetchall()

                print("----------------------------------------")
                print("ALL ADMIN ACCOUNTS IN DATABASE:")
                print(all_admins)
                print("----------------------------------------")

                return render_template(
                    "login/admin_login.html",
                    error="DEBUG: Admin username not found"
                )

            # ---------------------------------------------------
            # ADMIN FOUND
            # ---------------------------------------------------

            print(
                "Admin ID:",
                admin["admin_id"]
            )

            print(
                "Database username:",
                repr(admin["username"])
            )

            print(
                "Admin status:",
                repr(admin["status"])
            )

            # ---------------------------------------------------
            # CHECK ADMIN STATUS
            # ---------------------------------------------------

            if admin["status"] != "Active":

                print(
                    "RESULT: ADMIN ACCOUNT NOT ACTIVE"
                )

                return render_template(
                    "login/admin_login.html",
                    error="DEBUG: Admin account is not Active"
                )

            # ---------------------------------------------------
            # GET PASSWORD HASH
            # ---------------------------------------------------

            stored_password = admin["password"]

            if not stored_password:

                print(
                    "RESULT: PASSWORD HASH IS EMPTY"
                )

                return render_template(
                    "login/admin_login.html",
                    error="DEBUG: Admin password is empty"
                )

            print(
                "Password hash exists: YES"
            )

            print(
                "Password hash method:",
                stored_password.split("$")[0]
            )

            # ---------------------------------------------------
            # CHECK PASSWORD
            # ---------------------------------------------------

            try:

                password_correct = check_password_hash(
                    stored_password,
                    password
                )

                print(
                    "Password check result:",
                    password_correct
                )

            except Exception as password_error:

                print(
                    "PASSWORD HASH ERROR:",
                    repr(password_error)
                )

                return render_template(
                    "login/admin_login.html",
                    error=(
                        "DEBUG: Password hash error: "
                        + str(password_error)
                    )
                )

            # ---------------------------------------------------
            # LOGIN SUCCESS
            # ---------------------------------------------------

            if password_correct:

                print(
                    "RESULT: PASSWORD CORRECT"
                )

                print(
                    "ADMIN LOGIN SUCCESS"
                )

                print(
                    "========================================\n"
                )

                # Clear old session
                session.clear()

                # Create admin session
                session["admin_id"] = (
                    admin["admin_id"]
                )

                session["admin_username"] = (
                    admin["username"]
                )

                session["role"] = "admin"

                return redirect(
                    url_for("admin.dashboard")
                )

            # ---------------------------------------------------
            # PASSWORD WRONG
            # ---------------------------------------------------

            print(
                "RESULT: PASSWORD DOES NOT MATCH"
            )

            print(
                "========================================\n"
            )

            return render_template(
                "login/admin_login.html",
                error="DEBUG: Password does not match database"
            )

        except Exception as e:

            print("\n========================================")
            print("ADMIN LOGIN DATABASE ERROR")
            print(repr(e))
            print("========================================\n")

            return render_template(
                "login/admin_login.html",
                error=f"DEBUG DATABASE ERROR: {e}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "login/admin_login.html"
    )


# ===========================================================
# HOD LOGIN
# ===========================================================

@auth_bp.route(
    "/hod/login",
    methods=["GET", "POST"]
)
def hod_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM hod
                WHERE username = %s
                """,
                (username,)
            )

            hod = cursor.fetchone()

            if hod:

                # ------------------------------------------------
                # CHECK HOD ACCOUNT STATUS
                # ------------------------------------------------

                if hod["account_status"] != "Active":

                    return render_template(
                        "login/hod_login.html",
                        error="Your HOD account is not active."
                    )

                # ------------------------------------------------
                # CHECK PASSWORD
                # ------------------------------------------------

                stored_password = hod["password"]

                if check_password_hash(
                    stored_password,
                    password
                ):

                    session["hod_id"] = (
                        hod["hod_id"]
                    )

                    session["hod_username"] = (
                        hod["username"]
                    )

                    session["hod_name"] = (
                        hod["full_name"]
                    )

                    session["hod_department_id"] = (
                        hod["department_id"]
                    )

                    session["role"] = "hod"

                    return redirect(
                        url_for("hod.dashboard")
                    )

            return render_template(
                "login/hod_login.html",
                error="Invalid username or password"
            )

        except Exception as e:

            return render_template(
                "login/hod_login.html",
                error=f"Database Error: {e}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "login/hod_login.html"
    )


# ===========================================================
# TEACHER REGISTRATION
# ===========================================================

@auth_bp.route(
    "/teacher/register",
    methods=["GET", "POST"]
)
def teacher_register():

    if request.method == "POST":

        employee_id = request.form.get(
            "employee_id"
        )

        department_id = request.form.get(
            "department_id"
        )

        full_name = request.form.get(
            "full_name"
        )

        email = request.form.get(
            "email"
        )

        phone = request.form.get(
            "phone"
        )

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        confirm_password = request.form.get(
            "confirm_password"
        )

        # =======================================================
        # CHECK REQUIRED FIELDS
        # =======================================================

        if (
            not employee_id
            or not department_id
            or not full_name
            or not email
            or not username
            or not password
        ):

            return render_template(
                "login/teacher_register.html",
                error="Please fill in all required fields."
            )

        # =======================================================
        # CHECK PASSWORD MATCH
        # =======================================================

        if password != confirm_password:

            return render_template(
                "login/teacher_register.html",
                error="Passwords do not match."
            )

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            # ===================================================
            # CHECK EMPLOYEE ID
            # ===================================================

            cursor.execute(
                """
                SELECT teacher_id
                FROM teacher
                WHERE employee_id = %s
                """,
                (employee_id,)
            )

            existing_employee = cursor.fetchone()

            if existing_employee:

                return render_template(
                    "login/teacher_register.html",
                    error="Employee ID already registered."
                )

            # ===================================================
            # CHECK EMAIL
            # ===================================================

            cursor.execute(
                """
                SELECT teacher_id
                FROM teacher
                WHERE email = %s
                """,
                (email,)
            )

            existing_email = cursor.fetchone()

            if existing_email:

                return render_template(
                    "login/teacher_register.html",
                    error="Email already registered."
                )

            # ===================================================
            # CHECK USERNAME
            # ===================================================

            cursor.execute(
                """
                SELECT teacher_id
                FROM teacher
                WHERE username = %s
                """,
                (username,)
            )

            existing_username = cursor.fetchone()

            if existing_username:

                return render_template(
                    "login/teacher_register.html",
                    error="Username already registered."
                )

            # ===================================================
            # CHECK DEPARTMENT
            # ===================================================

            cursor.execute(
                """
                SELECT department_id
                FROM department
                WHERE department_id = %s
                  AND status = 'Active'
                """,
                (department_id,)
            )

            department = cursor.fetchone()

            if not department:

                return render_template(
                    "login/teacher_register.html",
                    error="Selected department is not available."
                )

            # ===================================================
            # HASH PASSWORD
            # ===================================================

            hashed_password = generate_password_hash(
                password
            )

            # ===================================================
            # CREATE TEACHER ACCOUNT
            # ===================================================

            cursor.execute(
                """
                INSERT INTO teacher (
                    department_id,
                    employee_id,
                    full_name,
                    email,
                    phone,
                    username,
                    password,
                    account_status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'Pending'
                )
                """,
                (
                    department_id,
                    employee_id,
                    full_name,
                    email,
                    phone,
                    username,
                    hashed_password
                )
            )

            connection.commit()

            return render_template(
                "login/teacher_register.html",
                success=(
                    "Registration successful. "
                    "Your account is waiting for Admin approval."
                )
            )

        except Exception as e:

            if connection:
                connection.rollback()

            return render_template(
                "login/teacher_register.html",
                error=f"Registration failed: {e}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    # =======================================================
    # GET ACTIVE DEPARTMENTS
    # =======================================================

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                department_id,
                department_name
            FROM department
            WHERE status = 'Active'
            ORDER BY department_name
            """
        )

        departments = cursor.fetchall()

        return render_template(
            "login/teacher_register.html",
            departments=departments
        )

    except Exception as e:

        return render_template(
            "login/teacher_register.html",
            error=f"Unable to load departments: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ===========================================================
# TEACHER LOGIN
# ===========================================================

@auth_bp.route(
    "/teacher/login",
    methods=["GET", "POST"]
)
def teacher_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    teacher_id,
                    employee_id,
                    full_name,
                    email,
                    phone,
                    username,
                    password,
                    department_id,
                    account_status
                FROM teacher
                WHERE username = %s
                """,
                (username,)
            )

            teacher = cursor.fetchone()

            if teacher:

                # ------------------------------------------------
                # CHECK ACCOUNT STATUS
                # ------------------------------------------------

                if teacher["account_status"] != "Active":

                    return render_template(
                        "login/teacher_login.html",
                        error=(
                            "Your teacher account is not active. "
                            "Please wait for Admin approval."
                        )
                    )

                # ------------------------------------------------
                # CHECK PASSWORD
                # ------------------------------------------------

                stored_password = teacher["password"]

                if check_password_hash(
                    stored_password,
                    password
                ):

                    # ============================================
                    # CREATE TEACHER SESSION
                    # ============================================

                    session["teacher_id"] = (
                        teacher["teacher_id"]
                    )

                    session["teacher_username"] = (
                        teacher["username"]
                    )

                    session["teacher_name"] = (
                        teacher["full_name"]
                    )

                    session["teacher_department_id"] = (
                        teacher["department_id"]
                    )

                    session["role"] = "teacher"

                    # ============================================
                    # GO TO TEACHER DASHBOARD
                    # ============================================

                    return redirect(
                        url_for("teacher.dashboard")
                    )

            # ===================================================
            # INVALID LOGIN
            # ===================================================

            return render_template(
                "login/teacher_login.html",
                error="Invalid username or password"
            )

        except Exception as e:

            return render_template(
                "login/teacher_login.html",
                error=f"Database Error: {e}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "login/teacher_login.html"
    )
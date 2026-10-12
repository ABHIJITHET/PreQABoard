from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from database.db_connection import get_connection

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ===========================================================
# STUDENT BLUEPRINT
# ===========================================================

student_bp = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


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
        # department_id  -> selected department
        # course_id      -> selected course
        # semester_id    -> selected semester
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


        # ===================================================
        # LOGIN SUCCESS
        # ===================================================

        flash(
            "Login successful.",
            "success"
        )


        # ===================================================
        # TEMPORARY REDIRECT
        #
        # Until dashboard is created.
        # ===================================================

        return redirect(
            url_for("student.login")
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


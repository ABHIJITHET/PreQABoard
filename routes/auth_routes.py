from flask import Blueprint, render_template, request, redirect, url_for, session
from database.db_connection import get_connection
from werkzeug.security import check_password_hash


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM admin
            WHERE username = %s
            """,
            (username,)
        )

        admin = cursor.fetchone()

        cursor.close()
        connection.close()

        if admin:

            stored_password = admin["password"]

            if check_password_hash(stored_password, password):

                session["admin_id"] = admin["admin_id"]
                session["admin_username"] = admin["username"]
                session["role"] = "admin"

                return redirect(url_for("admin.dashboard"))

        return render_template(
            "login/admin_login.html",
            error="Invalid username or password"
        )

    return render_template("login/admin_login.html")


# ===========================================================
# HOD LOGIN
# ===========================================================

@auth_bp.route("/hod/login", methods=["GET", "POST"])
def hod_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

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

        cursor.close()
        connection.close()

        if hod:

            # Check whether HOD account is active
            if hod["account_status"] != "Active":

                return render_template(
                    "login/hod_login.html",
                    error="Your HOD account is not active."
                )

            stored_password = hod["password"]

            if check_password_hash(
                stored_password,
                password
            ):

                # Create HOD session
                session["hod_id"] = hod["hod_id"]
                session["hod_username"] = hod["username"]
                session["hod_name"] = hod["full_name"]
                session["hod_department_id"] = hod["department_id"]
                session["role"] = "hod"

                return redirect(
                    url_for("hod.dashboard")
                )

        return render_template(
            "login/hod_login.html",
            error="Invalid username or password"
        )

    return render_template(
        "login/hod_login.html"
    )
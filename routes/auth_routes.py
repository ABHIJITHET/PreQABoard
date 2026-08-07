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
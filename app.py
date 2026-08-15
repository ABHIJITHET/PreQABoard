from flask import Flask

from config import Config
from database.db_connection import get_connection

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.hod_routes import hod_bp
from routes.teacher_routes import teacher_bp


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)


    # ===========================================================
    # PREVENT BROWSER CACHING
    # ===========================================================

    @app.after_request
    def add_no_cache_headers(response):

        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, "
            "post-check=0, pre-check=0, max-age=0"
        )

        response.headers["Pragma"] = "no-cache"

        response.headers["Expires"] = "0"


        # -------------------------------------------------------
        # PREVENT BACK/FORWARD CACHE
        # -------------------------------------------------------

        if response.content_type == "text/html; charset=utf-8":

            html = response.get_data(as_text=True)

            reload_script = """
<script>
window.addEventListener("pageshow", function (event) {

    const navigation =
        performance.getEntriesByType("navigation")[0];

    if (
        event.persisted ||
        (navigation && navigation.type === "back_forward")
    ) {
        window.location.reload();
    }

});
</script>
"""

            if "</body>" in html.lower():

                html = html.replace(
                    "</body>",
                    reload_script + "</body>"
                )

                response.set_data(html)

        return response


    # ===========================================================
    # REGISTER BLUEPRINTS
    # ===========================================================

    # Authentication routes
    app.register_blueprint(auth_bp)

    # Admin routes
    app.register_blueprint(admin_bp)

    # HOD routes
    app.register_blueprint(hod_bp)

    # Teacher routes
    app.register_blueprint(teacher_bp)


    # ===========================================================
    # HOME PAGE
    # ===========================================================

    @app.route("/")
    def home():

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT COUNT(*) AS total FROM department"
            )

            result = cursor.fetchone()

            cursor.close()
            connection.close()

            return f"""
                <h1>Welcome to PreQABoard</h1>

                <p>Flask is working successfully.</p>

                <p>MySQL is connected successfully.</p>

                <p>Total Departments: {result['total']}</p>

                <br>

                <a href="/admin/login">
                    Admin Login
                </a>

                <br><br>

                <a href="/hod/login">
                    HOD Login
                </a>

                <br><br>

                <a href="/teacher/login">
                    Teacher Login
                </a>
            """

        except Exception as e:

            return f"""
                <h1>Database Connection Failed</h1>

                <p>{e}</p>
            """


    return app


app = create_app()


if __name__ == "__main__":

    app.run(debug=True)
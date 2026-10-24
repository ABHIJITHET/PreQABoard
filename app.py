from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template

from config import Config
from database.db_connection import get_connection

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.hod_routes import hod_bp
from routes.teacher_routes import teacher_bp
from routes.student_routes import student_bp


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

    # -----------------------------------------------------------
    # Authentication routes
    # -----------------------------------------------------------

    app.register_blueprint(auth_bp)


    # -----------------------------------------------------------
    # Admin routes
    # -----------------------------------------------------------

    app.register_blueprint(admin_bp)


    # -----------------------------------------------------------
    # HOD routes
    # -----------------------------------------------------------

    app.register_blueprint(hod_bp)


    # -----------------------------------------------------------
    # Teacher routes
    # -----------------------------------------------------------

    app.register_blueprint(teacher_bp)


    # -----------------------------------------------------------
    # Student routes
    # -----------------------------------------------------------

    app.register_blueprint(student_bp)


    # ===========================================================
    # HOME PAGE
    # ===========================================================

    @app.route("/")
    def home():

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()


            # ---------------------------------------------------
            # GET TOTAL DEPARTMENTS
            # ---------------------------------------------------

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM department
                """
            )

            result = cursor.fetchone()

            total_departments = result["total"]


            # ---------------------------------------------------
            # HOME PAGE (TEMPLATE)
            # ---------------------------------------------------

            return render_template(
                "home.html",
                total_departments=total_departments
            )


        except Exception as e:

            return f"""
                <!DOCTYPE html>

                <html lang="en">

                <head>

                    <meta charset="UTF-8">

                    <title>Database Error</title>

                </head>


                <body>

                    <h1>
                        Database Connection Failed
                    </h1>

                    <p>
                        {e}
                    </p>

                </body>

                </html>
            """


        finally:

            if cursor:

                cursor.close()

            if connection:

                connection.close()


    # ===========================================================
    # PRINT REGISTERED ROUTES
    # ===========================================================

    print("\n==============================================")
    print("        PREQABOARD REGISTERED ROUTES")
    print("==============================================")

    for rule in app.url_map.iter_rules():

        print(
            f"{rule.methods}  ->  {rule}"
        )

    print("==============================================\n")


    # ===========================================================
    # RETURN APPLICATION
    # ===========================================================

    return app


# ===========================================================
# CREATE APPLICATION
# ===========================================================

app = create_app()


# ===========================================================
# RUN APPLICATION
# ===========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
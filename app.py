from flask import Flask
from config import Config
from database.db_connection import get_connection
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    @app.route("/")
    def home():
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM department")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return f"""
                <h1>Welcome to PreQABoard</h1>
                <p>Flask is working successfully.</p>
                <p>MySQL is connected successfully.</p>
                <p>Total Departments: {result['total']}</p>
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
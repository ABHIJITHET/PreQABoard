from database.db_connection import get_connection
from werkzeug.security import generate_password_hash


# ===========================================================
# RESET ADMIN PASSWORD
# ===========================================================

def reset_admin_password():

    username = "admin"

    new_password = "admin123"


    connection = None
    cursor = None

    try:

        # ---------------------------------------------------
        # CONNECT TO DATABASE
        # ---------------------------------------------------

        connection = get_connection()

        cursor = connection.cursor()


        # ---------------------------------------------------
        # CHECK WHETHER ADMIN EXISTS
        # ---------------------------------------------------

        cursor.execute(
            """
            SELECT admin_id, username
            FROM admin
            WHERE username = %s
            """,
            (username,)
        )

        admin = cursor.fetchone()


        if not admin:

            print()
            print("ERROR: Admin account not found.")
            print()
            return


        # ---------------------------------------------------
        # CREATE PASSWORD HASH
        # ---------------------------------------------------

        hashed_password = generate_password_hash(
            new_password
        )


        # ---------------------------------------------------
        # UPDATE ADMIN PASSWORD
        # ---------------------------------------------------

        cursor.execute(
            """
            UPDATE admin
            SET password = %s
            WHERE username = %s
            """,
            (
                hashed_password,
                username
            )
        )


        connection.commit()


        print()
        print("==========================================")
        print(" ADMIN PASSWORD RESET SUCCESSFULLY")
        print("==========================================")
        print()
        print("Username :", username)
        print("Password :", new_password)
        print()
        print("You can now login as Admin.")
        print()


    except Exception as e:

        if connection:

            connection.rollback()

        print()
        print("==========================================")
        print(" ERROR RESETTING ADMIN PASSWORD")
        print("==========================================")
        print()
        print(e)
        print()


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# ===========================================================
# RUN SCRIPT
# ===========================================================

if __name__ == "__main__":

    reset_admin_password()
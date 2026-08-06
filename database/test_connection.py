#Test Database Connection

from db_connection import get_connection
try:
    connection = get_connection()
    print("Database Connected Successfully")
    connection.close()
except Exception as e:
    print("Connection Failed")
    print(e)
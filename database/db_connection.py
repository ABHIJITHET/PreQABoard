import pymysql
from config import Config


def get_connection():
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=int(Config.MYSQL_PORT),
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )

        return connection

    except pymysql.MySQLError as e:
        print("MYSQL CONNECTION ERROR:", repr(e))
        raise
import time

import mysql.connector
from mysql.connector import Error


def test_connection():
    try:
        start_time = time.time()
        print(start_time)
        connection = mysql.connector.connect(
            host="rtg-automotive-db.c14oos6givty.eu-west-2.rds.amazonaws.com",
            database="rtg_automotive",
            user="admin",
            password="password",
            connection_timeout=10,
        )

        if connection.is_connected():
            print("Connection successful!")
            db_info = connection.get_server_info()
            print("Connected to MySQL Server version:", db_info)

    except Error as e:
        print("Error while connecting to MySQL:", e)

    finally:
        if connection.is_connected():
            connection.close()
            print("MySQL connection is closed.")


if __name__ == "__main__":
    test_connection()

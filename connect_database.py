import os
import time

import mysql.connector
from aws_utils import iam, rds
from mysql.connector import Error

iam.get_aws_credentials(os.environ)

rds_handler = rds.RDSHandler()
rds_instance = rds_handler.get_rds_instance_by_identifier("rtg-automotive-db")
rds_endpoint = rds_instance["Endpoint"]


def test_connection():
    try:
        start_time = time.time()
        print(start_time)
        connection = mysql.connector.connect(
            host=rds_endpoint,
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

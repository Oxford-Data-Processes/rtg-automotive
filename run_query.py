import os
import signal
import time

import mysql.connector
from aws_utils import iam, rds
from mysql.connector import Error

iam.get_aws_credentials(os.environ)

rds_handler = rds.RDSHandler()
rds_instance = rds_handler.get_rds_instance_by_identifier("rtg-automotive-db")
rds_endpoint = rds_instance["Endpoint"]


# Function to handle keyboard interrupt
def signal_handler(sig, frame):
    print("Keyboard interrupt received. Exiting...")
    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection is closed.")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


def run_query(query):
    global connection
    connection = None
    try:
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

            cursor = connection.cursor()
            start_time = time.time()  # Start timer
            cursor.execute(query)
            results = cursor.fetchall()
            end_time = time.time()  # End timer

            # Print the results of the query
            for row in results:
                print(row)

            # Print the time taken for the query
            print(f"Query executed in {end_time - start_time:.2f} seconds.")

    except Error as e:
        print("Error while connecting to MySQL:", e)

    finally:
        if connection and connection.is_connected():
            connection.close()
            print("MySQL connection is closed.")


query = """
SELECT DISTINCT(ebay_store) FROM store s ;
"""

# query = """
# CREATE TABLE ebay AS (
# SELECT
#     ts.item_id,
#     ps.custom_label,
#     ps.quantity,
#     ps.quantity_delta,
#     ts.ebay_store,
#     ps.supplier
# FROM
#     supplier_stock_ranked ps
# LEFT JOIN
#     store_filtered ts ON ps.custom_label = ts.custom_label
# );"""

if __name__ == "__main__":
    run_query(query)

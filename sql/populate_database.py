import mysql.connector
from mysql.connector import Error

def copy_tables(source_config, destination_config, tables):
    """
    Copy specified tables from source database to destination database.
    
    :param source_config: Dictionary containing connection details for source database
    :param destination_config: Dictionary containing connection details for destination database
    :param tables: List of table names to copy
    """
    try:
        # Connect to source database
        source_connection = mysql.connector.connect(**source_config)
        source_cursor = source_connection.cursor()

        # Connect to destination database
        dest_connection = mysql.connector.connect(**destination_config)
        dest_cursor = dest_connection.cursor()

        for table in tables:
            # Get column names first
            source_cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns = [column[0] for column in source_cursor.fetchall()]

            # Prepare insert statement
            insert_stmt = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s' for _ in columns])})"

            # Fetch and insert data in smaller chunks
            batch_size = 1000  # Adjust this value as needed
            source_cursor.execute(f"SELECT * FROM {table}")
            while True:
                rows = source_cursor.fetchmany(batch_size)
                if not rows:
                    break
                dest_cursor.executemany(insert_stmt, rows)
                dest_connection.commit()
                print(f"Copied {len(rows)} rows to {table} table.")

    except Error as e:
        print(f"Error: {e}")

    finally:
        if 'source_connection' in locals() and source_connection.is_connected():
            source_cursor.close()
            source_connection.close()
        if 'dest_connection' in locals() and dest_connection.is_connected():
            dest_cursor.close()
            dest_connection.close()

# Usage example:
if __name__ == "__main__":
    source_config = {
        'host': 'rtg-automotive-db.c14oos6givty.eu-west-2.rds.amazonaws.com',
        'user': 'admin',
        'password': 'password',
        'database': 'rtg_automotive',
        'port': '3306'
    }
    destination_config = {
        'host': 'rtg-automotive-db.cniy2omsilgp.eu-west-2.rds.amazonaws.com',
        'user': 'admin',
        'password': 'password',
        'database': 'rtg_automotive',
        'port': '3306'
    }

    tables_to_copy = ['store', 'product']

    copy_tables(source_config, destination_config, tables_to_copy)
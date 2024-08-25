import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Optional, Any

def create_mysql_engine(user: str, password: str, host: str, port: str, database: str) -> Engine:
    """
    Create and return a SQLAlchemy engine for MySQL connection.

    Args:
    user (str): MySQL username
    password (str): MySQL password
    host (str): MySQL host address
    port (str): MySQL port number
    database (str): MySQL database name

    Returns:
    sqlalchemy.engine.base.Engine: SQLAlchemy engine object
    """
    return create_engine(
        f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    )

def read_from_mysql(table_name: str, engine: Engine, chunk_size: int = 10000) -> pd.DataFrame:
    """
    Read data from a MySQL table using the provided SQLAlchemy engine in chunks.

    Args:
    table_name (str): Name of the table to read from
    engine (sqlalchemy.engine.base.Engine): SQLAlchemy engine object for MySQL connection
    chunk_size (int): Number of rows to read per chunk (default: 10000)

    Returns:
    pandas.DataFrame: DataFrame containing the data from the specified table
    """
    chunks: List[pd.DataFrame] = []
    with engine.connect() as connection:
        for chunk in pd.read_sql_table(table_name, connection, chunksize=chunk_size):
            chunks.append(chunk)

    return pd.concat(chunks, ignore_index=True)

def append_mysql_table(df: pd.DataFrame, table_name: str, engine: Engine, chunk_size: int = 10000) -> None:
    """
    Append data to a MySQL table using the provided SQLAlchemy engine in chunks.

    Args:
    df (pandas.DataFrame): DataFrame containing the data to append
    table_name (str): Name of the table to append to
    engine (sqlalchemy.engine.base.Engine): SQLAlchemy engine object for MySQL connection
    chunk_size (int): Number of rows to append per chunk (default: 10000)
    """
    try:
        with engine.begin() as connection:
            # Upload data in chunks
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i : i + chunk_size]
                chunk.to_sql(
                    table_name, con=connection, if_exists='append', index=False
                )
                print(
                    f"Appended chunk {i//chunk_size + 1} of {(len(df)-1)//chunk_size + 1}"
                )
    except SQLAlchemyError as e:
        print(f"Error: {e}")
        raise

def execute_query(engine: Engine, query: str, params: Optional[Dict[str, Any]] = None) -> List[tuple]:
    """
    Execute a SQL query using the provided SQLAlchemy engine.

    Args:
    engine (sqlalchemy.engine.base.Engine): SQLAlchemy engine object for MySQL connection
    query (str): SQL query to execute
    params (dict, optional): Parameters for the SQL query

    Returns:
    list: List of tuples containing the query results
    """
    with engine.connect() as connection:
        result = connection.execute(query, params)
        return result.fetchall()

def update_mysql_table(df: pd.DataFrame, table_name: str, engine: Engine, primary_key: str, chunk_size: int = 10000) -> None:
    """
    Update existing records in a MySQL table using the provided SQLAlchemy engine in chunks.

    Args:
    df (pandas.DataFrame): DataFrame containing the data to update
    table_name (str): Name of the table to update
    engine (sqlalchemy.engine.base.Engine): SQLAlchemy engine object for MySQL connection
    primary_key (str): Name of the primary key column
    chunk_size (int): Number of rows to update per chunk (default: 10000)
    """
    try:
        with engine.begin() as connection:
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i : i + chunk_size]
                for _, row in chunk.iterrows():
                    update_query = f"UPDATE {table_name} SET "
                    update_query += ", ".join([f"{col} = %s" for col in df.columns if col != primary_key])
                    update_query += f" WHERE {primary_key} = %s"
                    
                    values = [row[col] for col in df.columns if col != primary_key] + [row[primary_key]]
                    connection.execute(update_query, values)
                
                print(f"Updated chunk {i//chunk_size + 1} of {(len(df)-1)//chunk_size + 1}")
    except SQLAlchemyError as e:
        print(f"Error: {e}")
        raise
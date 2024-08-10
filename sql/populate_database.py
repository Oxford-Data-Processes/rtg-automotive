import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


def create_mysql_engine(user, password, host, port, database):
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


def get_store_data():
    csv_files = [f for f in os.listdir("store_data") if f.endswith(".csv")]
    dfs = []
    for file in csv_files:
        store_name = file.split(".")[0]  # Get store name from file name
        df = pd.read_csv(os.path.join("store_data", file))
        df["store"] = store_name
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def upload_dataframe_to_mysql(df, table_name, engine, chunk_size=10000):
    try:
        with engine.begin() as connection:
            # Create table if it doesn't exist
            df.head(0).to_sql(
                table_name, con=connection, if_exists="replace", index=False
            )

            # Upload data in chunks
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i : i + chunk_size]
                chunk.to_sql(
                    table_name, con=connection, if_exists="append", index=False
                )
                print(
                    f"Uploaded chunk {i//chunk_size + 1} of {(len(df)-1)//chunk_size + 1}"
                )
    except SQLAlchemyError as e:
        print(f"Error: {e}")
        connection.rollback()


def main():
    # Create MySQL engine
    engine = create_mysql_engine(
        "admin",
        "password",
        "rtg-automotive-db.c14oos6givty.eu-west-2.rds.amazonaws.com",
        "3306",
        "rtg_automotive",
    )

    # Process and upload product data
    product = pd.read_csv("product_df.csv")
    upload_dataframe_to_mysql(product, "product", engine)

    # Process and upload store data
    store_df = get_store_data()
    store_df = store_df.copy().iloc[:, :5]
    store_df.dropna(subset=["item_id"], inplace=True)
    store_df["item_id"] = store_df["item_id"].astype(int)
    store_df.drop_duplicates(subset=["item_id", "store"], inplace=True)

    upload_dataframe_to_mysql(store_df, "store", engine)


if __name__ == "__main__":
    main()

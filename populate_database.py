import pandas as pd
from sqlalchemy import create_engine


def write_csv_to_table(csv_file, table_name, config):
    # Read the CSV file
    df = pd.read_csv(csv_file)

    # Create a SQLAlchemy engine
    engine = create_engine(
        f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    )

    chunk_size = 10000
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i : i + chunk_size]
        if i == 0:
            # Replace the table with the first chunk
            chunk.to_sql(table_name, engine, if_exists="replace", index=False)
        else:
            # Append subsequent chunks
            chunk.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Wrote chunk {i//chunk_size + 1} of {(len(df)-1)//chunk_size + 1}")

    engine.dispose()


if __name__ == "__main__":

    config = {
        "host": "rtg-automotive-db.cniy2omsilgp.eu-west-2.rds.amazonaws.com",
        "user": "admin",
        "password": "password",
        "database": "rtg_automotive",
        "port": "3306",
    }

    # write_csv_to_table("data/tables/store.csv", "store", config)
    write_csv_to_table("data/tables/supplier_stock.csv", "supplier_stock", config)
    write_csv_to_table("data/tables/product.csv", "product", config)

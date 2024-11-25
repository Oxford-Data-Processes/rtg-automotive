import os
from pathlib import Path

import pandas as pd
from aws_utils import iam, rds
from sqlalchemy import create_engine

iam.get_aws_credentials(os.environ)
rds_handler = rds.RDSHandler()
rds_instance = rds_handler.get_rds_instance_by_identifier("rtg-automotive-db")
rds_endpoint = rds_instance["Endpoint"]


def write_dataframe_to_mysql(df, table_name):
    try:
        # Create a SQLAlchemy engine
        engine = create_engine(
            f"mysql+mysqlconnector://admin:password@{rds_endpoint}/rtg_automotive"
        )
        # Write the dataframe to the MySQL table
        df.to_sql(
            table_name, con=engine, if_exists="append", index=False, chunksize=10000
        )
        print(f"Data inserted into {table_name} successfully.")

    except Exception as e:
        print("Error while connecting to MySQL:", e)


def read_excel_sheets(file_path, sheet_names):
    excel = pd.ExcelFile(file_path)
    return {sheet: pd.read_excel(excel, sheet_name=sheet) for sheet in sheet_names}


def process_dataframe(df):
    df = df.iloc[:, :4]
    df.columns = ["custom_label", "part_number", "supplier", "quantity"]
    df.dropna(subset=["part_number", "supplier", "quantity"], inplace=True)
    df["part_number"] = df["part_number"].astype(str)
    df["quantity"] = df["quantity"].astype(int)
    return df


def main():
    DATE = "2024-10-08"
    excel_file = Path(
        f"/Users/chrislittle/Dropbox/#Speedsheet/stock_master/{DATE.replace('-','_')}/Stock Feed Master.xlsx"
    )
    sheet_names = ["Direct", "FPS"]

    dfs = read_excel_sheets(excel_file, sheet_names)

    processed_dfs = [process_dataframe(df) for df in dfs.values()]
    df_stock = pd.concat(processed_dfs)
    df_stock["updated_date"] = DATE

    df_stock.drop_duplicates(
        subset=["part_number", "supplier"], keep="first", inplace=True
    )

    supplier_to_filter = "APE"
    df_stock = df_stock[df_stock["supplier"] == supplier_to_filter]
    df_stock["custom_label"] = df_stock["custom_label"].str.upper().str.strip()
    df_stock.dropna(subset=["supplier"], inplace=True)

    write_dataframe_to_mysql(df_stock, "supplier_stock")


if __name__ == "__main__":
    main()

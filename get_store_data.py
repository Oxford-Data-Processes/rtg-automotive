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
        engine = create_engine(
            f"mysql+mysqlconnector://admin:password@{rds_endpoint}/rtg_automotive"
        )
        df.to_sql(
            table_name, con=engine, if_exists="append", index=False, chunksize=10000
        )
        print(f"Data inserted into {table_name} successfully.")

    except Exception as e:
        print("Error while connecting to MySQL:", e)


def process_dataframe(df):
    df = df.iloc[:, :12]
    df.columns = [
        "item_id",
        "brand",
        "custom_label",
        "current_quantity",
        "title",
        "current_price",
        "prefix",
        "uk_rtg",
        "fps_wds_dir",
        "payment_profile_name",
        "shipping_profile_name",
        "return_profile_name",
    ]
    df["supplier"] = df["prefix"].fillna("").astype(str)
    df["supplier"] = df.apply(determine_supplier, axis=1)
    return df


def determine_supplier(row):
    if row["uk_rtg"] == "RTG":
        return "RTG"
    return row["supplier"].split("-")[-1] if row["supplier"] else "RTG"


def read_excel_files(directory):
    dfs = {}
    for file in [f for f in directory.glob("*.xlsx") if not f.name.startswith("~$")]:
        ebay_store = file.stem.split(" ")[0]
        combined_df = process_excel_file(file, ebay_store)
        dfs[ebay_store] = combined_df
    return dfs


def process_excel_file(file, ebay_store):
    excel = pd.ExcelFile(file)
    combined_dfs = []

    for sheet in excel.sheet_names:
        sheet_df = process_dataframe(excel.parse(sheet))
        sheet_df["ebay_store"] = (
            ebay_store + "_" + sheet if len(excel.sheet_names) > 1 else ebay_store
        )
        combined_dfs.append(sheet_df)

    combined_df = pd.concat(combined_dfs, ignore_index=True)
    return combined_df


def handle_store_selection(store_selection):
    data_dir = Path("/Users/chrislittle/Dropbox/#Speedsheet/store_database/")
    if store_selection == "All":
        dfs = read_excel_files(data_dir)
        df_store = pd.concat(dfs.values(), ignore_index=True)
    else:
        df_store = process_excel_file(
            data_dir / f"{store_selection} Database SpeedSheet.xlsx", store_selection
        )
    return df_store


def upload_data(df_store):
    chunk_size = 100000
    for start in range(0, df_store.shape[0], chunk_size):
        end = start + chunk_size
        chunk = df_store.iloc[start:end]
        write_dataframe_to_mysql(chunk, "store")


def main():
    store_selection = input("Enter the eBay store (or 'All' for all stores): ").strip()
    df_store = handle_store_selection(store_selection)
    df_store.drop_duplicates(
        subset=["item_id", "custom_label", "ebay_store"], inplace=True
    )
    df_store["custom_label"] = df_store["custom_label"].str.upper().str.strip()

    print(df_store.head())

    upload_data(df_store)


main()

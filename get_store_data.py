import pandas as pd
from pathlib import Path
import os
from sqlalchemy import create_engine


def write_dataframe_to_mysql(df, table_name):
    try:
        engine = create_engine(
            "mysql+mysqlconnector://admin:password@rtg-automotive-mysql.c14oos6givty.eu-west-2.rds.amazonaws.com/rtg_automotive"
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
    sheet_dfs = [process_dataframe(excel.parse(sheet)) for sheet in excel.sheet_names]
    combined_df = pd.concat(sheet_dfs, ignore_index=True)
    combined_df["ebay_store"] = ebay_store
    print(f"Ebay store: {ebay_store}")
    print(combined_df.head())
    return combined_df


def handle_store_selection(store_selection):
    if store_selection == "All":
        data_dir = Path(
            f"/Users/chrislittle/Dropbox/#Speedsheet/store_database/Database SpeedSheet.xlsx"
        )
        dfs = read_excel_files(data_dir)
        df_store = pd.concat(dfs.values(), ignore_index=True)
    else:
        data_dir = Path(f"/Users/chrislittle/Dropbox/#Speedsheet/store_database/")
        df_store = pd.read_excel(
            data_dir / f"{store_selection} Database SpeedSheet.xlsx"
        )
        df_store = process_dataframe(df_store)
        df_store["ebay_store"] = store_selection
        print(f"Ebay store: {store_selection}")
        print(df_store.head())
    return df_store


def upload_supplier_data(df_store, ebay_stores):
    for ebay_store in ebay_stores:
        for supplier in df_store["supplier"].unique():
            supplier_df = df_store[df_store["supplier"] == supplier]
            supplier_ebay_df = supplier_df[supplier_df["ebay_store"] == ebay_store]
            if not supplier_ebay_df.empty:
                write_dataframe_to_mysql(supplier_ebay_df, "store")


def main():
    store_selection = input("Enter the eBay store (or 'All' for all stores): ").strip()
    df_store = handle_store_selection(store_selection)
    df_store.drop_duplicates(
        subset=["item_id", "custom_label", "ebay_store"], inplace=True
    )
    df_store["custom_label"] = df_store["custom_label"].str.upper().str.strip()
    ebay_stores = (
        df_store["ebay_store"].unique()
        if store_selection == "All"
        else [store_selection]
    )

    upload_supplier_data(df_store, ebay_stores)


main()

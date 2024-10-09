import pandas as pd
from pathlib import Path
import os
import boto3
from io import BytesIO


def write_parquet_to_s3(df, bucket, key):
    buffer = BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ["AWS_SESSION_TOKEN"],
        region_name="eu-west-2",
    )
    buffer.seek(0)
    s3.upload_fileobj(buffer, bucket, key)


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


def get_bucket_name():
    aws_account_id = os.environ["AWS_ACCOUNT_ID"]
    return f"rtg-automotive-bucket-{aws_account_id}"


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


def upload_supplier_data(df_store, ebay_stores, bucket_name):
    for ebay_store in ebay_stores:
        for supplier in df_store["supplier"].unique():
            supplier_df = df_store[df_store["supplier"] == supplier]
            supplier_ebay_df = supplier_df[supplier_df["ebay_store"] == ebay_store]
            if not supplier_ebay_df.empty:
                key = f"store/ebay_store={ebay_store}/supplier={supplier}/data.parquet"
                write_parquet_to_s3(supplier_ebay_df, bucket_name, key)


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

    bucket_name = get_bucket_name()
    upload_supplier_data(df_store, ebay_stores, bucket_name)


main()

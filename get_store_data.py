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
    df["supplier"] = df.apply(
        lambda row: (
            "RTG"
            if row["uk_rtg"] == "RTG"
            else (row["supplier"].split("-")[-1] if row["supplier"] else "RTG")
        ),
        axis=1,
    )
    return df


def read_excel_files(directory):
    dfs = {}
    for file in [f for f in directory.glob("*.xlsx") if not f.name.startswith("~$")]:
        ebay_store = file.stem.split(" ")[0]
        excel = pd.ExcelFile(file)
        sheet_dfs = [
            process_dataframe(excel.parse(sheet)) for sheet in excel.sheet_names
        ]
        combined_df = pd.concat(sheet_dfs, ignore_index=True)
        combined_df["ebay_store"] = ebay_store
        dfs[ebay_store] = combined_df

        print(f"Ebay store: {ebay_store}")
        print(combined_df.head())
    return dfs


def main():
    data_dir = Path("data/store_database")
    dfs = read_excel_files(data_dir)
    df_store = pd.concat(dfs.values(), ignore_index=True)
    df_store.drop_duplicates(
        subset=["item_id", "custom_label", "ebay_store"], inplace=True
    )
    df_store["custom_label"] = df_store["custom_label"].str.upper().str.strip()

    aws_account_id = os.environ["AWS_ACCOUNT_ID"]
    bucket_name = f"rtg-automotive-bucket-{aws_account_id}"

    for ebay_store in df_store["ebay_store"].unique():
        for supplier in df_store["supplier"].unique():
            supplier_df = df_store[df_store["supplier"] == supplier]
            supplier_ebay_df = supplier_df[supplier_df["ebay_store"] == ebay_store]
            if not supplier_ebay_df.empty:
                key = f"store/ebay_store={ebay_store}/supplier={supplier}/data.parquet"
                write_parquet_to_s3(supplier_ebay_df, bucket_name, key)


if __name__ == "__main__":
    main()

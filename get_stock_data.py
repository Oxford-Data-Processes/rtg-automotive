import pandas as pd
from pathlib import Path
import os
import datetime
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


def read_excel_sheets(file_path, sheet_names):
    excel = pd.ExcelFile(file_path)
    return {sheet: pd.read_excel(excel, sheet_name=sheet) for sheet in sheet_names}


def process_dataframe(df):
    df = df.iloc[:, :4]
    df.columns = ["custom_label", "part_number", "supplier", "quantity"]
    df["part_number"] = df["part_number"].astype(str)
    return df


def main():
    excel_file = Path("data/supplier_stock/Stock Feed Master.xlsx")
    sheet_names = ["Direct", "FPS"]

    dfs = read_excel_sheets(excel_file, sheet_names)

    processed_dfs = [process_dataframe(df) for df in dfs.values()]
    df_stock = pd.concat(processed_dfs)
    updated_date = datetime.datetime.now() - datetime.timedelta(days=1)

    df_stock["year"] = updated_date.year
    df_stock["month"] = updated_date.month
    df_stock["day"] = updated_date.day
    df_stock["updated_date"] = updated_date.strftime("%Y-%m-%d")

    df_stock.drop_duplicates(
        subset=["part_number", "supplier"], keep="first", inplace=True
    )

    df_stock["custom_label"] = df_stock["custom_label"].str.upper().str.strip()

    remove_labels = pd.read_csv("data/tables/remove_custom_labels.csv")[
        "custom_label"
    ].tolist()
    remove_labels = [label.upper().strip() for label in remove_labels]
    df_stock = df_stock[~df_stock["custom_label"].isin(remove_labels)]

    aws_account_id = os.environ["AWS_ACCOUNT_ID"]
    bucket_name = f"rtg-automotive-bucket-{aws_account_id}"

    for supplier in df_stock["supplier"].unique():
        supplier_df = df_stock[df_stock["supplier"] == supplier]
        key = f"supplier_stock/supplier={supplier}/year={updated_date.year}/month={updated_date.month}/day={updated_date.day}/data.parquet"

        write_parquet_to_s3(supplier_df, bucket_name, key)

    df_product = df_stock.copy()[["custom_label", "part_number", "supplier"]]
    write_parquet_to_s3(df_product, bucket_name, "product/data.parquet")


if __name__ == "__main__":
    main()

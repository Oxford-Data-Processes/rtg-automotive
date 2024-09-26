import json
import boto3
import logging
import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
import os
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def process_numerical(x):
    if not isinstance(x, (int, float)):
        return 0
    elif x <= 0:
        return 0
    elif x > 10:
        return 10
    else:
        return x


CONFIG = {
    "APE": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: 0 if x == "No" else (10 if x == "YES" else 0),
    },
    "BET": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
    "BGA": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
    "COM": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": process_numerical,
    },
    "FAI": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
    "FEB": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": process_numerical,
    },
    "FIR": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: 10 if x == "Y" else 0,
    },
    "FPS": {
        "code_column_number": 1,
        "stock_column_number": 4,
        "process_func": process_numerical,
    },
    "JUR": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
    "KLA": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: x,
    },
    "KYB": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: 10 if x == "Y" else 0,
    },
    "MOT": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": process_numerical,
    },
    "RFX": {
        "code_column_number": 1,
        "stock_column_number": 4,
        "process_func": process_numerical,
    },
    "ROL": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": lambda x: 10 if x == "In Stock" else 0,
    },
    "RTG": {
        "code_column_number": 1,
    },
    "SMP": {
        "code_column_number": 1,
        "stock_column_number": 1,
        "process_func": lambda _: 10,
    },
    "ELR": {
        "code_column_number": 1,
        "stock_column_number": 4,
        "process_func": process_numerical,
    },
}


def read_excel_from_s3(bucket_name: str, object_key: str) -> list[dict]:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ["AWS_SESSION_TOKEN"],
    )
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    excel_data = response["Body"].read()
    workbook = openpyxl.load_workbook(BytesIO(excel_data))
    sheet = workbook.active

    data = []
    headers = [cell.value for cell in sheet[1]]

    for row in sheet.iter_rows(min_row=2, values_only=True):
        row_data = {headers[i]: row[i] for i in range(len(headers))}
        data.append(row_data)

    return data


def process_stock_feed(
    stock_feed_data: list[dict], config_key: str, config, processed_date: str
):
    config_data = config[config_key]

    code_column_index = config_data["code_column_number"] - 1
    stock_column_index = config_data["stock_column_number"] - 1

    output = []

    for row in stock_feed_data:
        part_number = str(row[list(row.keys())[code_column_index]])
        quantity = int(row[list(row.keys())[stock_column_index]])

        output.append(
            {
                "part_number": part_number,
                "supplier": config_key,
                "quantity": quantity,
                "updated_date": processed_date,
            }
        )

    return output


def write_to_s3_parquet(
    data: list[dict],
    bucket_name: str,
    file_name: str,
    schema: list[tuple[str, pa.DataType]],
) -> None:
    table = pa.Table.from_pylist(data, schema=pa.schema(schema))

    buffer = BytesIO()
    pq.write_table(table, buffer)
    s3_client = boto3.client("s3")
    buffer.seek(0)
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=buffer.getvalue())


def get_stock_feed_schema():
    return [
        ("part_number", pa.string()),
        ("supplier", pa.string()),
        ("quantity", pa.int32()),
        ("updated_date", pa.string()),
    ]


def extract_s3_info(event):
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_key = event["Records"][0]["s3"]["object"]["key"]
    return bucket_name, object_key


def process_current_date_and_supplier(object_key):
    current_date = datetime.now().strftime("%Y-%m-%d")
    year, month, day = current_date.split("-")
    supplier = object_key.split("_")[0]
    return current_date, year, month, day, supplier


def create_s3_file_name(supplier, year, month, day):
    return f"supplier_stock/supplier={supplier}/year={year}/month={month}/day={day}/data.parquet"


def lambda_handler(event, context):
    aws_account_id = os.environ["AWS_ACCOUNT_ID"]
    rtg_automotive_bucket = f"rtg-automotive-bucket-{aws_account_id}"
    stock_feed_schema = get_stock_feed_schema()

    logger.info(f"Received event: {json.dumps(event)}")

    bucket_name, object_key = extract_s3_info(event)

    try:
        logger.info(f"Reading file from path {object_key}")
        excel_data = read_excel_from_s3(bucket_name, object_key)
        logger.info(f"First 5 rows of Excel data: {excel_data[:5]}")

        current_date, year, month, day, supplier = process_current_date_and_supplier(
            object_key
        )

        output = process_stock_feed(excel_data, supplier, CONFIG, current_date)
        logger.info(f"First 5 rows of output data: {output[:5]}")

        file_name = create_s3_file_name(supplier, year, month, day)
        write_to_s3_parquet(output, rtg_automotive_bucket, file_name, stock_feed_schema)

        logger.info(f"File read successfully in path {object_key}")

        return {"statusCode": 200, "body": json.dumps("File processed successfully!")}
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise

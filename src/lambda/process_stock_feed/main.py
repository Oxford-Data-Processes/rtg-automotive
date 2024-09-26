import json
import boto3
import logging
import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO


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
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)

    # Read the bytes from the response
    excel_data = response["Body"].read()

    # Load the Excel file into openpyxl
    workbook = openpyxl.load_workbook(BytesIO(excel_data))

    # Select the active worksheet (or specify a sheet name)
    sheet = workbook.active

    # Process the data into a list of dictionaries
    data = []
    headers = [
        cell.value for cell in sheet[1]
    ]  # Assuming the first row contains headers

    for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header row
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


def lambda_handler(event, context):
    rtg_automotive_bucket = "rtg-automotive-bucket-654654324108"

    stock_feed_schema = [
        ("part_number", pa.string()),
        ("supplier", pa.string()),
        ("quantity", pa.int32()),
        ("updated_date", pa.string()),
    ]

    logger.info(f"Received event: {json.dumps(event)}")

    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_key = event["Records"][0]["s3"]["object"]["key"]

    try:
        logger.info(f"Reading file from path {object_key}")
        excel_data = read_excel_from_s3(bucket_name, object_key)
        logger.info(f"First 5 rows of Excel data: {[item for item in excel_data[:5]]}")
        output = process_stock_feed(excel_data, "APE", CONFIG, "2024-05-01")
        logger.info(f"First 5 rows of output data: {[item for item in output[:5]]}")
        write_to_s3_parquet(
            output, rtg_automotive_bucket, "stock_feed_test.parquet", stock_feed_schema
        )

        logger.info(f"File read successfully in path {object_key}")

        return {"statusCode": 200, "body": json.dumps("File processed successfully!")}
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise e

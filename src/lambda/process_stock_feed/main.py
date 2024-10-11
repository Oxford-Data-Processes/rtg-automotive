import json
import boto3
import logging
import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
import os
import urllib.parse
from datetime import datetime
import time
import pytz

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
        "header_row_number": 1,
        "process_func": lambda x: 0 if x == "No" else (10 if x == "YES" else 0),
    },
    "BET": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
    "BGA": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
    "COM": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
    "FAI": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "header_row_number": 5,
        "process_func": process_numerical,
    },
    "FEB": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
    "FIR": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "header_row_number": 1,
        "process_func": lambda x: 10 if x == "Y" else 0,
    },
    "FPS": {
        "code_column_number": 1,
        "stock_column_number": 4,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
    "JUR": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
    "KLA": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "header_row_number": 1,
        "process_func": lambda x: x,
    },
    "KYB": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "header_row_number": 1,
        "process_func": lambda x: 10 if x == "Y" else 0,
    },
    "MOT": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
    "RFX": {
        "code_column_number": 1,
        "stock_column_number": 4,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
    "ROL": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "header_row_number": 1,
        "process_func": lambda x: 10 if x == "In Stock" else 0,
    },
    "RTG": {
        "code_column_number": 1,
        "header_row_number": 1,
    },
    "SMP": {
        "code_column_number": 1,
        "stock_column_number": 1,
        "header_row_number": 1,
        "process_func": lambda _: 10,
    },
    "ELR": {
        "code_column_number": 1,
        "stock_column_number": 4,
        "header_row_number": 1,
        "process_func": process_numerical,
    },
}


def read_excel_from_s3(
    bucket_name: str, object_key: str, header_row_number: int
) -> list[dict]:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ["AWS_SESSION_TOKEN"],
        region_name=os.environ["AWS_REGION"],
    )
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    excel_data = response["Body"].read()
    workbook = openpyxl.load_workbook(BytesIO(excel_data))
    sheet = workbook.active

    data = []
    headers = [cell.value for cell in sheet[header_row_number]]

    for row in sheet.iter_rows(min_row=header_row_number + 1, values_only=True):
        row_data = {headers[i]: row[i] for i in range(len(headers))}
        data.append(row_data)

    return data


def fetch_rtg_custom_labels(rtg_automotive_bucket) -> list:
    query = """SELECT DISTINCT(custom_label) FROM "rtg_automotive"."store" WHERE ebay_store = 'RTG' AND supplier = 'RTG';"""
    athena_client = boto3.client("athena", region_name=os.environ["AWS_REGION"])

    # Start the query execution
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": "rtg_automotive"},
        ResultConfiguration={
            "OutputLocation": f"s3://{rtg_automotive_bucket}/athena-results/"  # Temporary output location
        },
        WorkGroup="rtg-automotive-workgroup",
    )

    query_execution_id = response["QueryExecutionId"]

    # Wait for the query to complete
    while True:
        query_status = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        status = query_status["QueryExecution"]["Status"]["State"]

        if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break

        time.sleep(1)  # Wait before checking the status again

    # If the query succeeded, get the results
    if status == "SUCCEEDED":
        custom_labels = []
        next_token = None

        # Paginate through results
        while True:
            # Prepare the parameters for get_query_results
            params = {"QueryExecutionId": query_execution_id}
            if next_token:
                params["NextToken"] = next_token

            results = athena_client.get_query_results(**params)
            # Extract the custom labels from the results
            custom_labels.extend(
                row["Data"][0]["VarCharValue"]
                for row in results["ResultSet"]["Rows"][1:]
            )  # Skip header row

            next_token = results.get("NextToken")
            if not next_token:
                break

        return custom_labels
    else:
        raise Exception(f"Query failed with status: {status}")


def process_stock_feed(
    stock_feed_data: list[dict],
    config_key: str,
    config,
    processed_date: str,
    rtg_automotive_bucket: str,
):
    config_data = config[config_key]
    code_column_index = config_data["code_column_number"] - 1

    if config_key == "RTG":
        custom_labels = fetch_rtg_custom_labels(rtg_automotive_bucket)
        logger.info(f"Custom labels length: {len(custom_labels)}")
        return process_rtg_stock_feed(
            stock_feed_data,
            custom_labels,
            code_column_index,
            config_key,
            processed_date,
        )
    else:
        stock_column_index = config_data["stock_column_number"] - 1
        return process_other_stock_feed(
            stock_feed_data,
            config_data,
            code_column_index,
            stock_column_index,
            config_key,
            processed_date,
        )


def process_rtg_stock_feed(
    stock_feed_data: list[dict],
    custom_labels: list,
    code_column_index: int,
    config_key: str,
    processed_date: str,
) -> list[dict]:
    output = []
    row_index = list(stock_feed_data[0].keys())[code_column_index]
    part_numbers = [
        row[row_index].upper().strip() for row in stock_feed_data if row[row_index]
    ]
    logger.info(f"Is PS56 in part_numbers: {'PS56' in part_numbers}")
    logger.info(f"Is PS56 in custom_labels: {'PS56' in custom_labels}")
    for custom_label in custom_labels:
        quantity = 0 if custom_label in part_numbers else 20
        output.append(
            {
                "part_number": custom_label,
                "supplier": config_key,
                "quantity": quantity,
                "updated_date": processed_date,
            }
        )
    return output


def process_other_stock_feed(
    stock_feed_data: list[dict],
    config_data: dict,
    code_column_index: int,
    stock_column_index: int,
    config_key: str,
    processed_date: str,
) -> list[dict]:
    output = []
    row_index = list(stock_feed_data[0].keys())[stock_column_index]
    for row in stock_feed_data:
        part_number = str(row[list(row.keys())[code_column_index]])
        quantity = config_data["process_func"](row[row_index])

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
    s3_client = boto3.client(
        "s3", region_name=os.environ["AWS_REGION"]
    )  # Ensure the region is specified
    buffer.seek(0)
    logger.info(f"Writing to S3 path {bucket_name}/{file_name}")
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
    year = object_key.split("/")[1].split("=")[1]
    month = object_key.split("/")[2].split("=")[1]
    day = object_key.split("/")[3].split("=")[1]
    supplier = object_key.split("/")[4].split("_")[0]
    return year, month, day, supplier


def create_s3_file_name(supplier, year, month, day):
    return f"supplier_stock/supplier={supplier}/year={year}/month={month}/day={day}/data.parquet"


def send_sns_notification(message, AWS_ACCOUNT_ID):
    sns_client = boto3.client("sns", region_name=os.environ["AWS_REGION"])
    topic_arn = (
        f"arn:aws:sns:eu-west-2:{AWS_ACCOUNT_ID}:rtg-automotive-stock-notifications"
    )
    sns_client.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject="Stock Feed Processed",
    )


def read_excel_data(bucket_name, object_key, header_row_number):
    logger.info(f"Reading file from path {object_key}")
    excel_data = read_excel_from_s3(bucket_name, object_key, header_row_number)
    logger.info(f"First 5 rows of Excel data: {excel_data[:5]}")
    return excel_data


def process_stock_data(excel_data, supplier, current_date, rtg_automotive_bucket):
    output = process_stock_feed(
        excel_data, supplier, CONFIG, current_date, rtg_automotive_bucket
    )
    logger.info(f"First 5 rows of output data: {output[:5]}")
    return output


def write_output_to_s3(output, bucket_name, file_name):
    stock_feed_schema = get_stock_feed_schema()
    write_to_s3_parquet(output, bucket_name, file_name, stock_feed_schema)


def send_success_notification(supplier, AWS_ACCOUNT_ID):
    time_stamp = datetime.now(pytz.timezone("Europe/London")).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    message = f"Stock feed processed successfully for {supplier} at {time_stamp}"
    send_sns_notification(message, AWS_ACCOUNT_ID)
    logger.info(message)


def create_success_response():
    return {"statusCode": 200, "body": json.dumps("File processed successfully!")}


def send_failure_notification(supplier, AWS_ACCOUNT_ID):
    time_stamp = datetime.now(pytz.timezone("Europe/London")).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    message = f"Stock feed processing failed for {supplier} at {time_stamp}"
    send_sns_notification(message, AWS_ACCOUNT_ID)
    logger.info(message)


def lambda_handler(event, context):
    AWS_ACCOUNT_ID = "654654324108"
    rtg_automotive_bucket = f"rtg-automotive-bucket-{AWS_ACCOUNT_ID}"
    logger.info(f"RTG Automotive bucket: {rtg_automotive_bucket}")
    logger.info(f"Received event: {json.dumps(event)}")

    bucket_name, object_key = extract_s3_info(event)
    object_key = urllib.parse.unquote(object_key)
    year, month, day, supplier = process_current_date_and_supplier(object_key)
    current_date = f"{year}-{month}-{day}"

    # try:
    logger.info(f"Object key: {object_key}")
    excel_data = read_excel_data(
        bucket_name, object_key, CONFIG[supplier]["header_row_number"]
    )

    output = process_stock_data(
        excel_data, supplier, current_date, rtg_automotive_bucket
    )
    file_name = create_s3_file_name(supplier, year, month, day)
    write_output_to_s3(output, rtg_automotive_bucket, file_name)

    send_success_notification(supplier, AWS_ACCOUNT_ID)
    return create_success_response()
    # except Exception as e:
    #     logger.error(f"Error processing file: {str(e)}")
    #     send_failure_notification(supplier, AWS_ACCOUNT_ID)
    #     raise e

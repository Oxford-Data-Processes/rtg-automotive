import json
import logging
import openpyxl
import os
import urllib.parse
import time
import pytz
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from io import BytesIO
from aws_utils import athena, sns, iam, s3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

aws_credentials = iam.AWSCredentials(
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID_ADMIN"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY_ADMIN"],
    stage="dev",
)

aws_credentials.get_aws_credentials()

AWS_REGION = "eu-west-2"


def process_numerical(x):
    return max(0, min(x, 10)) if isinstance(x, (int, float)) and x > 0 else 0


def create_function(func_str):
    return eval(func_str) if func_str.startswith("lambda") else globals().get(func_str)


def get_config_from_s3(bucket_name, object_key):

    s3_handler = s3.S3Handler(
        os.environ["AWS_ACCESS_KEY_ID"],
        os.environ["AWS_SECRET_ACCESS_KEY"],
        os.environ["AWS_SESSION_TOKEN"],
        AWS_REGION,
    )
    config = s3_handler.load_json_from_s3(bucket_name, object_key)

    for key, value in config.items():
        if "process_func" in value:
            value["process_func"] = create_function(value["process_func"])

    return config


def read_excel_from_s3(
    bucket_name: str, object_key: str, header_row_number: int
) -> list[dict]:
    s3_handler = s3.S3Handler(
        os.environ["AWS_ACCESS_KEY_ID"],
        os.environ["AWS_SECRET_ACCESS_KEY"],
        os.environ["AWS_SESSION_TOKEN"],
        AWS_REGION,
    )
    excel_data = s3_handler.load_excel_from_s3(bucket_name, object_key)
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
    athena_handler = athena.AthenaHandler(
        database="rtg_automotive",
        workgroup="rtg-automotive-workgroup",
        output_bucket=rtg_automotive_bucket,
    )
    csv_data = athena_handler.run_query(query)
    custom_labels = csv_data[1:]
    return custom_labels


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
    s3_handler = s3.S3Handler(
        os.environ["AWS_ACCESS_KEY_ID"],
        os.environ["AWS_SECRET_ACCESS_KEY"],
        os.environ["AWS_SESSION_TOKEN"],
        AWS_REGION,
    )

    transformed_data = []
    for item in data:
        transformed_item = item.copy()
        if (
            isinstance(transformed_item["part_number"], list)
            and transformed_item["part_number"]
        ):
            transformed_item["part_number"] = transformed_item["part_number"][0]
        transformed_data.append(transformed_item)

    table = pa.Table.from_pylist(transformed_data, schema=pa.schema(schema))

    buffer = BytesIO()
    pq.write_table(table, buffer)

    buffer.seek(0)
    logger.info(f"Writing to S3 path {bucket_name}/{file_name}")
    s3_handler.upload_parquet_to_s3(bucket_name, file_name, buffer.getvalue())


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


def send_sns_notification(message):
    topic_name = "rtg-automotive-stock-notifications"
    sns_handler = sns.SNSHandler(topic_name)
    sns_handler.send_notification(message, "Stock Feed Processed")


def read_excel_data(bucket_name, object_key, header_row_number):
    logger.info(f"Reading file from path {object_key}")
    excel_data = read_excel_from_s3(bucket_name, object_key, header_row_number)
    logger.info(f"First 5 rows of Excel data: {excel_data[:5]}")
    return excel_data


def process_stock_data(
    excel_data, supplier, current_date, rtg_automotive_bucket, config
):
    output = process_stock_feed(
        excel_data, supplier, config, current_date, rtg_automotive_bucket
    )
    logger.info(f"First 5 rows of output data: {output[:5]}")
    return output


def write_output_to_s3(output, bucket_name, file_name):
    stock_feed_schema = get_stock_feed_schema()
    write_to_s3_parquet(output, bucket_name, file_name, stock_feed_schema)


def send_success_notification(supplier):
    time_stamp = datetime.now(pytz.timezone("Europe/London")).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    message = f"Stock feed processed successfully for {supplier} at {time_stamp}"
    send_sns_notification(message)
    logger.info(message)


def create_success_response():
    return {"statusCode": 200, "body": json.dumps("File processed successfully!")}


def send_failure_notification(supplier):
    time_stamp = datetime.now(pytz.timezone("Europe/London")).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    message = f"Stock feed processing failed for {supplier} at {time_stamp}"
    send_sns_notification(message)
    logger.info(message)


def lambda_handler(event, context):
    AWS_ACCOUNT_ID = "654654324108"

    rtg_automotive_bucket = f"rtg-automotive-bucket-{AWS_ACCOUNT_ID}"
    config = get_config_from_s3(
        rtg_automotive_bucket, "config/process_stock_feed_config.json"
    )

    logger.info(f"RTG Automotive bucket: {rtg_automotive_bucket}")
    logger.info(f"Received event: {json.dumps(event)}")

    bucket_name, object_key = extract_s3_info(event)
    object_key = urllib.parse.unquote(object_key)
    year, month, day, supplier = process_current_date_and_supplier(object_key)
    current_date = f"{year}-{month}-{day}"

    try:
        logger.info(f"Object key: {object_key}")
        excel_data = read_excel_data(
            bucket_name, object_key, config[supplier]["header_row_number"]
        )

        output = process_stock_data(
            excel_data, supplier, current_date, rtg_automotive_bucket, config
        )
        file_name = create_s3_file_name(supplier, year, month, day)
        write_output_to_s3(output, rtg_automotive_bucket, file_name)

        send_success_notification(supplier)
        return create_success_response()
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        send_failure_notification(supplier)
        raise e

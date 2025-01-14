import json
import logging
import os
import urllib.parse
from datetime import datetime
from io import BytesIO

import openpyxl
import pandas as pd
import pytz
import requests
from aws_utils import api_gateway, iam, logs, s3, sns
from process_functions import create_function

logger = logging.getLogger()
logger.setLevel(logging.INFO)


iam.get_aws_credentials(os.environ)

api_gateway_handler = api_gateway.APIGatewayHandler()
api_id = api_gateway_handler.search_api_by_name("rtg-automotive-api")

STAGE_LOWER = os.environ["STAGE"].lower()

LAMBDA_HOST = (
    f"https://{api_id}.execute-api.eu-west-2.amazonaws.com/{STAGE_LOWER}/items/"
)


def get_helper_table(table_name: str):
    s3_handler = s3.S3Handler()
    bucket_name = f"rtg-automotive-bucket-{os.environ['AWS_ACCOUNT_ID']}"

    folders = s3_handler.list_objects(bucket_name, f"{table_name}/")
    folder_paths = [
        (folder["Key"].split("/")[-2], folder["Key"])
        for folder in folders
        if folder["Key"].endswith(".parquet")
    ]
    latest_file = sorted(folder_paths, key=lambda x: x[0], reverse=True)[0][1]
    table_data = s3_handler.load_parquet_from_s3(bucket_name, latest_file)
    df = pd.read_parquet(BytesIO(table_data))
    table_dictionary = [
        {col: row[col] for col in df.columns} for _, row in df.iterrows()
    ]
    logger.info(f"Helper table as dictionary: {table_dictionary[:5]}")

    return table_dictionary


def get_part_number_mapping(supplier: str) -> dict:
    items = get_helper_table("supplier_stock")

    logger.info(f"Items: {items[:5]}")

    unique_items = {(item["custom_label"], item["part_number"]): item for item in items}

    return {
        part_number: custom_label
        for (custom_label, part_number), item in unique_items.items()
    }


def get_config_from_s3(bucket_name, object_key):
    s3_handler = s3.S3Handler()
    config = s3_handler.load_json_from_s3(bucket_name, object_key)

    for key, value in config.items():
        if "process_func" in value:
            value["process_func"] = create_function(value["process_func"])

    return config


def read_excel_from_s3(
    bucket_name: str, object_key: str, header_row_number: int
) -> list[dict]:
    s3_handler = s3.S3Handler()
    excel_data = s3_handler.load_excel_from_s3(bucket_name, object_key)
    workbook = openpyxl.load_workbook(BytesIO(excel_data))
    sheet = workbook.active

    data = []
    headers = [cell.value for cell in sheet[header_row_number]]

    for row in sheet.iter_rows(min_row=header_row_number + 1, values_only=True):
        row_data = {headers[i]: row[i] for i in range(len(headers))}
        data.append(row_data)

    return data


def fetch_rtg_custom_labels() -> list:
    items = get_helper_table("store")
    custom_labels = list(set(item["custom_label"] for item in items))
    return custom_labels


def add_items_to_supplier_stock(items) -> list:
    chunk_size = 100

    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        response = requests.post(
            f"{LAMBDA_HOST}?table_name=supplier_stock&type=append",
            headers={"Content-Type": "application/json"},
            json={"items": chunk},
        )
        if response.status_code != 200:
            logger.error(f"Failed to add items: {response.text}")


def process_stock_feed(
    stock_feed_data: list[dict],
    config_key: str,
    config,
    processed_date: str,
):
    config_data = config[config_key]
    code_column_index = config_data["code_column_number"] - 1

    if config_key == "RTG":
        custom_labels = fetch_rtg_custom_labels()
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


def extract_s3_info(event):
    bucket_name = event["detail"]["bucket"]
    object_key = event["detail"]["object_key"]
    return bucket_name, object_key


def process_current_date_and_supplier(object_key):
    year = object_key.split("/")[1].split("=")[1]
    month = object_key.split("/")[2].split("=")[1]
    day = object_key.split("/")[3].split("=")[1]
    supplier = object_key.split("/")[4].split("_")[0]
    return year, month, day, supplier


def send_sns_notification(message):
    topic_name = "rtg-automotive-lambda-notifications"
    sns_handler = sns.SNSHandler(topic_name)
    sns_handler.send_notification(message, "PROCESS_FINISHED")


def read_excel_data(bucket_name, object_key, header_row_number):
    logger.info(f"Reading file from path {object_key}")
    excel_data = read_excel_from_s3(bucket_name, object_key, header_row_number)
    logger.info(f"First 5 rows of Excel data: {excel_data[:5]}")
    return excel_data


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
    project = "rtg-automotive"
    aws_account_id = os.environ["AWS_ACCOUNT_ID"]
    project_bucket_name = f"{project}-bucket-{aws_account_id}"
    config = get_config_from_s3(
        project_bucket_name, "config/process_stock_feed_config.json"
    )

    logger.info(f"RTG Automotive bucket: {project_bucket_name}")
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

        output = process_stock_feed(excel_data, supplier, config, current_date)

        logger.info(f"Output before mapping: {output[:5]}")

        part_number_mapping = get_part_number_mapping(supplier)

        logger.info("Part number mapping received successfully")

        output = [
            {**item, "custom_label": part_number_mapping[item["part_number"]]}
            for item in output
            if item.get("part_number") is not None
            and part_number_mapping.get(item["part_number"]) is not None
        ]

        logger.info(f"Output: {output[:5]}")

        add_items_to_supplier_stock(output)
        logger.info(f"Added {len(output)} items to supplier stock")
        logs_handler = logs.LogsHandler()
        logs_handler.log_action(
            f"rtg-automotive-bucket-{os.environ['AWS_ACCOUNT_ID']}",
            "frontend",
            f"PROCESSED | stock_feed_supplier={supplier} | number_of_items={len(output)}",
            "admin",
        )

        send_success_notification(supplier)
        return create_success_response()
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        send_failure_notification(supplier)
        raise e

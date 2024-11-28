import json
import logging
import os
import uuid
from datetime import datetime

import pandas as pd
import pytz
from aws_utils import iam, rds, s3, sns
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iam.get_aws_credentials(os.environ)


def send_sns_notification(message):
    topic_name = "rtg-automotive-lambda-notifications"
    sns_handler = sns.SNSHandler(topic_name)
    sns_handler.send_notification(message, "EBAY_TABLE_GENERATED")


def create_database_session() -> sessionmaker:
    rds_handler = rds.RDSHandler()
    rds_instance = rds_handler.get_rds_instance_by_identifier("rtg-automotive-db")
    rds_endpoint = rds_instance["Endpoint"]
    engine = create_engine(
        f"mysql+mysqlconnector://admin:password@{rds_endpoint}/rtg_automotive"
    )
    return sessionmaker(bind=engine)


def execute_query(session, query):
    logger.info(f"Executing query: {query}")
    try:
        if query.strip():
            result = session.execute(text(query))
            session.commit()

            if query.strip().upper().startswith("SELECT"):
                return result.fetchall()
            else:
                return None
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        session.rollback()
        raise e


def get_paginated_ebay_data(session, batch_size=100000):
    # Get total count
    count_result = execute_query(session, "SELECT COUNT(*) FROM ebay")
    total_records = count_result[0][0]

    # Fetch data in batches
    for offset in range(0, total_records, batch_size):
        query = f"SELECT * FROM ebay LIMIT {batch_size} OFFSET {offset}"
        yield query, offset, total_records


def lambda_handler(event, context):
    current_timestamp = datetime.now(pytz.timezone("Europe/London")).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    current_directory = os.path.dirname(os.path.abspath(__file__))

    session = create_database_session()()
    with open(os.path.join(current_directory, "generate_ebay_table.sql"), "r") as file:
        query = file.read()

    execute_query(session, query)

    s3_handler = s3.S3Handler()
    bucket_name = f"rtg-automotive-bucket-{os.environ['AWS_ACCOUNT_ID']}"

    file_count = 0
    for query, offset, total_records in get_paginated_ebay_data(session):
        result = execute_query(session, query)

        df = pd.DataFrame(
            result,
            columns=[
                "item_id",
                "custom_label",
                "quantity",
                "quantity_delta",
                "updated_date",
                "ebay_store",
                "supplier",
            ],
        )

        df["last_updated_timestamp"] = current_timestamp

        # Generate unique filename using UUID
        filename = f"ebay/table/{current_timestamp}/{uuid.uuid4()}.parquet"

        logger.info(
            f"Processing batch {file_count + 1}: records {offset} to {min(offset + 100000, total_records)}"
        )
        logger.info(f"Dataframe shape: {df.shape}")
        logger.info(f"Uploading to: {filename}")

        s3_handler.upload_parquet_to_s3(
            bucket_name,
            filename,
            df.to_parquet(),
        )
        file_count += 1

    session.close()

    time_stamp = datetime.now(pytz.timezone("Europe/London")).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    message = f"Ebay table generated and {file_count} parquet files uploaded successfully at {time_stamp}"
    send_sns_notification(message)

    logger.info("Query finished")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": "Query executed successfully!", "files_generated": file_count}
        ),
    }

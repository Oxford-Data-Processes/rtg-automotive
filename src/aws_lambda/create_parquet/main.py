import logging
import os
import uuid
from datetime import datetime

import pandas as pd
from aws_utils import iam, logs, rds, s3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iam.get_aws_credentials(os.environ)


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


def get_paginated_data(session, table_name: str, batch_size=100000):
    count_result = execute_query(session, f"SELECT COUNT(*) FROM {table_name}")
    total_records = count_result[0][0]
    for offset in range(0, total_records, batch_size):
        query = f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}"
        yield query, offset, total_records


def create_parquet_files_from_table(table_name: str) -> None:
    session = create_database_session()()
    s3_handler = s3.S3Handler()
    bucket_name = f"rtg-automotive-bucket-{os.environ['AWS_ACCOUNT_ID']}"
    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    file_count = 0

    for query, offset, total_records in get_paginated_data(session, table_name):
        result = execute_query(session, query)
        df = pd.DataFrame(result)
        filename = f"{table_name}/{current_timestamp}/{uuid.uuid4()}.parquet"
        logger.info(
            f"Processing batch {file_count + 1}: records {offset} to {min(offset + 100000, total_records)}"
        )
        logger.info(f"Dataframe shape: {df.shape}")
        logger.info(f"Uploading to: {filename}")
        s3_handler.upload_parquet_to_s3(bucket_name, filename, df.to_parquet())
        file_count += 1

    session.close()
    logger.info(f"{file_count} parquet files uploaded for {table_name}")


def lambda_handler(event, context):
    table_name = event.get("table_name")
    create_parquet_files_from_table(table_name)
    logs_handler = logs.LogsHandler()
    logs_handler.log_action(
        f"rtg-automotive-bucket-{os.environ['AWS_ACCOUNT_ID']}",
        "frontend",
        f"TABLE {table_name} GENERATED",
        "admin",
    )
    return {"statusCode": 200, "body": "Helper tables generated successfully"}

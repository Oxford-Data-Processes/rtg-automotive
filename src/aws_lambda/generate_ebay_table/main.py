import json
import logging
import os
from datetime import datetime

import pandas as pd
import pytz
from aws_utils import iam, rds, s3, sns
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iam.get_aws_credentials(os.environ)
rds_handler = rds.RDSHandler()
rds_instance = rds_handler.get_rds_instance_by_identifier("rtg-automotive-db")
rds_endpoint = rds_instance["Endpoint"]


def send_sns_notification(message):
    topic_name = "rtg-automotive-lambda-notifications"
    sns_handler = sns.SNSHandler(topic_name)
    sns_handler.send_notification(message, "EBAY_TABLE_GENERATED")


def create_database_session() -> sessionmaker:
    engine = create_engine(
        f"mysql+mysqlconnector://admin:password@{rds_endpoint}/rtg_automotive"
    )
    return sessionmaker(bind=engine)


def execute_query(session, query):
    logger.info(f"Executing query: {query}")
    try:
        if query.strip():  # Check if the query is not empty
            result = session.execute(text(query))  # Execute the query
            session.commit()  # Commit the transaction after executing the query

            # Check if the query is a SELECT statement
            if query.strip().upper().startswith("SELECT"):
                return (
                    result.fetchall()
                )  # Return the fetched results for SELECT queries
            else:
                return None  # For non-SELECT queries, return None
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        session.rollback()  # Rollback in case of error
        raise e


def lambda_handler(event, context):
    iam.get_aws_credentials(os.environ)
    current_directory = os.path.dirname(os.path.abspath(__file__))

    session = create_database_session()()
    with open(os.path.join(current_directory, "generate_ebay_table.sql"), "r") as file:
        query = file.read()

    execute_query(session, query)

    # Fetch data from the ebay table
    fetch_query = (
        "SELECT * FROM ebay"  # Query to select all data from the temporary ebay table
    )
    result = execute_query(session, fetch_query)
    print(result)
    session.close()

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
    logger.info(f"Dataframe shape: {df.shape}")
    logger.info(f"Dataframe head: {df.head()}")

    s3_handler = s3.S3Handler()

    s3_handler.upload_parquet_to_s3(
        f"rtg-automotive-bucket-{os.environ['AWS_ACCOUNT_ID']}",
        "ebay/table/data.parquet",
        df.to_parquet(),
    )

    time_stamp = datetime.now(pytz.timezone("Europe/London")).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    message = f"Ebay table generated and data uploaded successfully at {time_stamp}"
    send_sns_notification(message)

    return {"statusCode": 200, "body": json.dumps("Query executed successfully!")}

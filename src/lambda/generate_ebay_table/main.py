import json
import logging
import os
from aws_utils import athena, iam

logger = logging.getLogger()
logger.setLevel(logging.INFO)

aws_credentials = iam.AWSCredentials(
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID_ADMIN"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY_ADMIN"],
    stage="dev",
)

aws_credentials.get_aws_credentials()


def lambda_handler(event, context):
    AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]
    rtg_automotive_bucket = f"rtg-automotive-{AWS_ACCOUNT_ID}"
    athena_handler = athena.AthenaHandler(
        database="rtg_automotive",
        workgroup="rtg-automotive-workgroup",
        output_bucket=rtg_automotive_bucket,
    )

    current_directory = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(current_directory, "generate_ebay_table.sql"), "r") as file:
        query = file.read()

    logger.info(f"Query: {query}")
    results = athena_handler.run_query(query)

    if len(results) > 0:
        logger.info(f"Query results - columns: {results[0]} values: {results[1:6]}")
    else:
        logger.error(f"Query failed: {query}")
        raise Exception(f"Query failed: {query}")
    return {"statusCode": 200, "body": json.dumps("Query executed successfully!")}

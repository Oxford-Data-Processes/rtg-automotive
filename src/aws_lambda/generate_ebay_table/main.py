import json
import logging
import os
from aws_utils import athena, iam
from aws_lambda.api.models.pydantic_models import PROJECT
logger = logging.getLogger()
logger.setLevel(logging.INFO)

iam.get_aws_credentials(os.environ)


def lambda_handler(event, context):
    project_bucket_name = f"{PROJECT}-bucket-{os.environ["AWS_ACCOUNT_ID"]}"
    athena_handler = athena.AthenaHandler(
        database=PROJECT,
        workgroup=f"{PROJECT}-workgroup",
        output_bucket=project_bucket_name,
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

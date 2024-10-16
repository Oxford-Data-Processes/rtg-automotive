import json
import logging
import os
from aws_utils import athena

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


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

    if results["ResultSet"]["Rows"]:
        logger.info(f"Query results: {results['ResultSet']['Rows'][:5]}")
    else:
        logger.error(
            f"Query failed with status: {results['ResultSet']['Status']['State']}"
        )
        raise Exception(
            f"Query failed with status: {results['ResultSet']['Status']['State']}"
        )
    return {"statusCode": 200, "body": json.dumps("Query executed successfully!")}

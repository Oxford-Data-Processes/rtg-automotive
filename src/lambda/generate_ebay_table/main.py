import json
import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # Initialize a session using Boto3
    session = boto3.Session()
    athena_client = session.client("athena")

    # Define the query
    query = "SELECT * FROM supplier_stock LIMIT 10"

    # Define the parameters for the query execution
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": "rtg_automotive"},
        WorkGroup="rtg-automotive-workgroup",
    )

    # Log the query execution ID
    query_execution_id = response["QueryExecutionId"]
    logger.info(f"Started query with execution ID: {query_execution_id}")

    return {"statusCode": 200, "body": json.dumps("Query executed successfully!")}

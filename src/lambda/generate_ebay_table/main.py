import json
import boto3
import logging
import os

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # Initialize a session using Boto3
    session = boto3.Session()
    athena_client = session.client("athena")

    current_directory = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(current_directory, "generate_ebay_table.sql"), "r") as file:
        query = file.read()

    # Define the parameters for the query execution
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": "rtg_automotive"},
        WorkGroup="rtg-automotive-workgroup",
    )

    logger.info(f"Query: {query}")
    query_execution_id = response["QueryExecutionId"]
    # Wait for the query to complete
    while True:
        query_status = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        status = query_status["QueryExecution"]["Status"]["State"]
        if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break

    if status == "SUCCEEDED":
        # Get the results
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        logger.info(f"Query results: {results['ResultSet']['Rows'][:5]}")
    else:
        logger.error(f"Query failed with status: {status}")

    return {"statusCode": 200, "body": json.dumps("Query executed successfully!")}

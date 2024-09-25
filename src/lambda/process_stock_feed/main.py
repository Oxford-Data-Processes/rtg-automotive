import json
import boto3
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # Initialize a boto3 client for S3
    s3_client = boto3.client("s3")

    # Log the received event
    logger.info(f"Received event: {json.dumps(event)}")

    # Extract bucket name and object key from the event
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_key = event["Records"][0]["s3"]["object"]["key"]

    # Process the file (for example, read it and print its content)
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_content = response["Body"].read().decode("utf-8")
        logger.info(f"File content from {object_key}: {file_content}")

        # You can add further processing logic here

        return {"statusCode": 200, "body": json.dumps("File processed successfully!")}
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error processing file: {str(e)}"),
        }

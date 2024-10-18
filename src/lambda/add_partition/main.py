import json
import logging
import os
from aws_utils import glue, iam, s3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iam_instance = iam.IAM(stage=os.environ["STAGE"])
iam.AWSCredentials.get_aws_credentials(
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID_ADMIN"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY_ADMIN"],
    iam_instance=iam_instance,
)


def lambda_handler(event, context):

    glue_handler = glue.GlueHandler()
    logger.info(f"Received event: {json.dumps(event)}")

    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_key = event["Records"][0]["s3"]["object"]["key"]
    records = event.get("Records", [])

    if records:
        object_key = records[0]["s3"]["object"]["key"]
        partition_values, paths, _ = s3.S3Utils.extract_partition_values(object_key)

    database_name = "rtg_automotive"
    table_name = paths[0]

    if table_name in ["supplier_stock", "store"]:
        try:
            glue_handler.add_partition_to_glue(
                database_name,
                table_name,
                bucket_name,
                partition_values,
            )
            response = {
                "statusCode": 200,
                "body": json.dumps(
                    f"Partition added for {table_name} and values {partition_values.keys()}"
                ),
            }
            return response
        except Exception as e:
            logger.error(f"Error adding partition: {e}")
            raise e
    else:
        return {"statusCode": 200, "body": json.dumps("Not a partitionable table")}

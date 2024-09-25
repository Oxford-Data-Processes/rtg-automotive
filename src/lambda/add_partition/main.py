import json
import boto3
import logging
from datetime import datetime
import os


def add_partition_to_glue(
    glue_client, database_name, table_name, bucket_name, partition_values, logger
):

    current_time = datetime.now().isoformat() + "Z"

    response = glue_client.get_table(
        DatabaseName=database_name,
        Name=table_name,
        CatalogId=os.environ["AWS_ACCOUNT_ID"],
    )
    paths = [
        column["Name"] for column in response["Table"]["StorageDescriptor"]["Columns"]
    ]

    partition_input = {
        "Values": [
            partition_values.get("supplier"),
            partition_values.get("year"),
            partition_values.get("month"),
            partition_values.get("day"),
        ],
        "LastAccessTime": current_time,
        "StorageDescriptor": {
            "Columns": [],
            "Location": f"s3://{bucket_name}/{table_name}/supplier={partition_values.get('supplier')}/year={partition_values.get('year')}/month={partition_values.get('month')}/day={partition_values.get('day')}/",
            "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
            "Compressed": True,
            "NumberOfBuckets": -1,
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                "Parameters": {"paths": ",".join(paths)},
            },
            "BucketColumns": [],
            "SortColumns": [],
            "Parameters": {
                "sizeKey": "19420",
                "objectCount": "1",
                "recordCount": "1",
                "averageRecordSize": "19420",
                "compressionType": "SNAPPY",
                "classification": "parquet",
                "typeOfData": "file",
            },
            "StoredAsSubDirectories": False,
        },
        "Parameters": {},
    }

    try:
        glue_client.create_partition(
            DatabaseName=database_name,
            TableName=table_name,
            PartitionInput=partition_input,
        )
        return {"statusCode": 200, "body": json.dumps("Partition added successfully!")}
    except Exception as e:
        logger.error(f"Error adding partition: {str(e)}")
        raise


def extract_partition_values(object_key):
    partition_values = {}
    parts = object_key.split("/")

    for part in parts:
        if "%" in part:
            part = part.replace("%3D", "=")
        if "=" in part:
            key, value = part.split("=")
            partition_values[key] = value

    return partition_values


def get_table_name(object_key):
    return object_key.split("/")[0]


def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    glue_client = boto3.client("glue")
    logger.info(f"Received event: {json.dumps(event)}")

    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_key = event["Records"][0]["s3"]["object"]["key"]
    records = event.get("Records", [])

    if records:
        object_key = records[0]["s3"]["object"]["key"]
        partition_values = extract_partition_values(object_key)

    database_name = "rtg_automotive"
    table_name = get_table_name(object_key)

    if table_name in ["supplier_stock", "store"]:
        response = add_partition_to_glue(
            glue_client,
            database_name,
            table_name,
            bucket_name,
            partition_values,
            logger,
        )
        return response

    return {"statusCode": 200, "body": json.dumps("No partition added!")}

import boto3
import streamlit as st
import os
import time
from io import BytesIO
import pandas as pd
from typing import List, Tuple
import io
import zipfile
import re

# Initialize S3 and SQS clients
s3_client = boto3.client("s3", region_name="eu-west-2")
sqs_client = boto3.client("sqs", region_name="eu-west-2")
AWS_ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")
STAGE = os.environ.get("STAGE")  # Use get to avoid KeyError if STAGE is not set
PROJECT_NAME = "rtg-automotive"


def zip_dataframes(dataframes: List[Tuple[pd.DataFrame, str]]) -> io.BytesIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for df, name in dataframes:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            zip_file.writestr(f"{name}.csv", csv_buffer.getvalue())
    return zip_buffer


def create_ebay_dataframe(ebay_df: pd.DataFrame) -> pd.DataFrame:
    ebay_df = ebay_df[ebay_df["quantity_delta"] != 0]

    # Drop rows with null item_id
    ebay_df = ebay_df.dropna(subset=["item_id"])

    ebay_df = ebay_df.rename(
        columns={
            "custom_label": "CustomLabel",
            "item_id": "ItemID",
            "ebay_store": "Store",
            "quantity": "Quantity",
        }
    )
    ebay_df["Action"] = "Revise"
    ebay_df["SiteID"] = "UK"
    ebay_df["Currency"] = "GBP"
    ebay_df = ebay_df[
        [
            "Action",
            "ItemID",
            "SiteID",
            "Currency",
            "Quantity",
            "Store",
        ]
    ]
    ebay_df["Quantity"] = ebay_df["Quantity"].astype(int)
    ebay_df["ItemID"] = ebay_df["ItemID"].astype(int)
    return ebay_df


def get_last_csv_from_s3(bucket_name, prefix):
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    csv_files = [
        obj for obj in response.get("Contents", []) if obj["Key"].endswith(".csv")
    ]
    csv_files.sort(key=lambda x: x["LastModified"], reverse=True)
    return csv_files[0]["Key"] if csv_files else None


def receive_sqs_messages(queue_url, max_messages=10):
    response = sqs_client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=max_messages, WaitTimeSeconds=20
    )
    return response.get("Messages", [])

def extract_datetime_from_sns_message(message):
    # Regular expression to find the datetime in the message
    match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", message)
    return match.group(0) if match else None

def get_all_sqs_messages(queue_url):
    sqs_client = boto3.client("sqs", region_name="eu-west-2")
    all_messages = []
    while True:
        # Receive messages from the SQS queue
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5,
            MessageAttributeNames=["All"],
        )

        # Check if there are any messages
        messages = response.get("Messages", [])
        if not messages:
            break  # Exit the loop if no more messages

        for message in messages:
            timestamp = extract_datetime_from_sns_message(message["Body"])
            message_body = message["Body"]
            all_messages.append({"timestamp": timestamp, "message": message_body})

    all_messages.sort(key=lambda x: x["timestamp"])

    return all_messages


def upload_file_to_s3(file, bucket_name, date):
    year = date.split("-")[0]
    month = date.split("-")[1]
    day = date.split("-")[2]
    s3_client.put_object(
        Bucket=bucket_name,
        Key=f"stock_feed/year={year}/month={month}/day={day}/{file.name.replace(" ","_")}",
        Body=file.getvalue(),
    )
    st.success(f"File {file.name} uploaded successfully to S3.")


def trigger_generate_ebay_table_lambda():
    lambda_client = boto3.client("lambda", region_name="eu-west-2")
    try:
        response = lambda_client.invoke(
            FunctionName=f"arn:aws:lambda:eu-west-2:{AWS_ACCOUNT_ID}:function:rtg-automotive-{STAGE}-generate-ebay-table",
            InvocationType="RequestResponse",
        )
        time.sleep(2)
        return True
    except Exception as e:
        st.error(f"Error triggering Lambda: {str(e)}")
        return False


def load_csv_from_s3(bucket_name, csv_key):
    csv_object = s3_client.get_object(Bucket=bucket_name, Key=csv_key)
    csv_data = csv_object["Body"].read()
    df = pd.read_csv(BytesIO(csv_data))
    return df


def main():
    st.title("eBay Store Upload Generator")
    sqs_queue_url = f"https://sqs.eu-west-2.amazonaws.com/{AWS_ACCOUNT_ID}/{PROJECT_NAME}-sqs-queue"
    stock_feed_bucket_name = f"{PROJECT_NAME}-stock-feed-bucket-{AWS_ACCOUNT_ID}"
    project_bucket_name = f"{PROJECT_NAME}-bucket-{AWS_ACCOUNT_ID}"

    uploaded_files = st.file_uploader(
        "Upload Excel files", type=["xlsx"], accept_multiple_files=True
    )

    date = st.date_input("Select a date", value=pd.Timestamp.now().date()).strftime(
        "%Y-%m-%d"
    )

    if st.button("Upload Files to S3") and date:
        if uploaded_files:
            for uploaded_file in uploaded_files:
                upload_file_to_s3(uploaded_file, stock_feed_bucket_name, date)
            time.sleep(len(uploaded_files) * 4)
            messages = get_all_sqs_messages(sqs_queue_url)[-len(uploaded_files):]
            for message in messages:
                st.write(message)
        else:
            st.warning("Please upload at least one file first.")

    if st.button("Generate eBay Store Upload Files"):
        if trigger_generate_ebay_table_lambda():
            last_csv_key = get_last_csv_from_s3(project_bucket_name, "athena-results/")
            if last_csv_key:
                df = load_csv_from_s3(project_bucket_name, last_csv_key)
                st.write("Raw eBay Table:")
                st.dataframe(df)
                ebay_df = create_ebay_dataframe(df)
                stores = list(ebay_df["Store"].unique())
                ebay_dfs = [
                    (ebay_df[ebay_df["Store"] == store].drop(columns=["Store"]), store)
                    for store in stores
                ]

                zip_buffer = zip_dataframes(ebay_dfs)

                st.download_button(
                    label="Download eBay Upload Files",
                    data=zip_buffer.getvalue(),
                    file_name="ebay_upload_files.zip",
                    mime="application/zip",
                )

            else:
                st.warning("No CSV file found in the specified S3 path.")


if __name__ == "__main__":
    main()

import boto3
import streamlit as st
import os
import time
from io import BytesIO

AWS_ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")
sqs_client = boto3.client("sqs", region_name="eu-west-2")
s3_client = boto3.client("s3")


def receive_sqs_messages(queue_url):
    response = sqs_client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=5
    )
    return response.get("Messages", [])


def display_all_sqs_messages(queue_url):
    end_time = time.time() + 30  # 30 seconds from now
    while time.time() < end_time:
        messages = receive_sqs_messages(queue_url)
        if messages:
            for message in messages:
                st.write(f"Message: {message['Body']}")


def upload_file_to_s3(file):
    bucket_name = f"rtg-automotive-stock-feed-bucket-{AWS_ACCOUNT_ID}"
    s3_client.put_object(
        Bucket=bucket_name, Key=f"stock_feed/{file.name}", Body=file.getvalue()
    )
    st.success(f"File {file.name} uploaded successfully to S3.")


st.title("SQS Message Reader App")

sqs_queue_url = (
    f"https://sqs.eu-west-2.amazonaws.com/{AWS_ACCOUNT_ID}/rtg-automotive-sqs-queue"
)

uploaded_files = st.file_uploader(
    "Upload Excel files", type=["xlsx"], accept_multiple_files=True
)

# New upload button
if st.button("Upload Files to S3"):
    if uploaded_files:
        for uploaded_file in uploaded_files:
            upload_file_to_s3(uploaded_file)
            display_all_sqs_messages(sqs_queue_url)
    else:
        st.warning("Please upload at least one file first.")

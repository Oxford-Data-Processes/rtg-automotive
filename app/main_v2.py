import boto3
import streamlit as st
import os
import time
from io import BytesIO

AWS_ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")
sqs_client = boto3.client("sqs", region_name="eu-west-2")
s3_client = boto3.client("s3")


def receive_sqs_messages(queue_url, max_messages=10):
    response = sqs_client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=max_messages, WaitTimeSeconds=20
    )
    return response.get("Messages", [])


def display_last_n_sqs_messages(queue_url, n):
    messages = receive_sqs_messages(queue_url, max_messages=n)
    if messages:
        for message in messages:
            st.write(f"Message: {message['Body']}")
            # Optionally delete the message after processing
            sqs_client.delete_message(
                QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
            )


def upload_file_to_s3(file):
    bucket_name = f"rtg-automotive-stock-feed-bucket-{AWS_ACCOUNT_ID}"
    s3_client.put_object(
        Bucket=bucket_name, Key=f"stock_feed/{file.name}", Body=file.getvalue()
    )
    st.success(f"File {file.name} uploaded successfully to S3.")


st.title("SQS Message Reader App")

sqs_queue_url = f"https://sqs.eu-west-2.amazonaws.com/{AWS_ACCOUNT_ID}/rtg-automotive-sqs-queue.fifo"

uploaded_files = st.file_uploader(
    "Upload Excel files", type=["xlsx"], accept_multiple_files=True
)

# New upload button
if st.button("Upload Files to S3"):
    if uploaded_files:
        for uploaded_file in uploaded_files:
            upload_file_to_s3(uploaded_file)

        time.sleep(len(uploaded_files) * 2)
        st.success("All files uploaded. You can now check for messages.")
    else:
        st.warning("Please upload at least one file first.")

# Button to get messages from SQS
if st.button("Get Messages from SQS"):
    display_last_n_sqs_messages(sqs_queue_url, len(uploaded_files))

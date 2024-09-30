import boto3
import streamlit as st
import os
import time

AWS_ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")
sqs_client = boto3.client("sqs", region_name="eu-west-2")


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
        else:
            st.write("No new messages.")
        time.sleep(1)


st.title("SQS Message Reader App")

sqs_queue_url = (
    f"https://sqs.eu-west-2.amazonaws.com/{AWS_ACCOUNT_ID}/rtg-automotive-sqs-queue"
)

if st.button("Read All Messages from SQS for 30 seconds"):
    display_all_sqs_messages(sqs_queue_url)

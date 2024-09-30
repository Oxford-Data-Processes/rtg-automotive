import boto3
import streamlit as st

# Create an SNS client
sns_client = boto3.client("sns", region_name="eu-west-2")
sqs_client = boto3.client("sqs", region_name="eu-west-2")


# Function to subscribe the SQS queue to the SNS topic
def subscribe_sqs_to_sns(sqs_queue_url, topic_arn):
    response = sns_client.subscribe(
        TopicArn=topic_arn, Protocol="sqs", Endpoint=sqs_queue_url
    )
    return response


# Function to receive messages from the SQS queue
def receive_sqs_messages(queue_url):
    response = sqs_client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=5
    )
    return response.get("Messages", [])


# Function to display the latest message from SQS
def display_sqs_messages(queue_url):
    messages = receive_sqs_messages(queue_url)
    if messages:
        for message in messages:
            st.write(f"Message: {message['Body']}")
            # Optionally delete the message after processing
            sqs_client.delete_message(
                QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
            )
    else:
        st.write("No new messages.")


# Streamlit UI
st.title("SNS to SQS Subscription App")

# Replace with your actual SQS queue URL
sqs_queue_url = (
    "https://sqs.eu-west-2.amazonaws.com/654654324108/rtg-automotive-sqs-queue"
)

if st.button("Subscribe SQS to SNS Topic"):
    topic_arn = "arn:aws:sns:eu-west-2:654654324108:rtg-automotive-stock-notifications"
    response = subscribe_sqs_to_sns(sqs_queue_url, topic_arn)
    st.success("SQS subscribed to SNS topic!")

display_sqs_messages(sqs_queue_url)

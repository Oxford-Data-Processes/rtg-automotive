import boto3
import os
import re


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


# Example usage
AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]
sqs_queue_url = (
    f"https://sqs.eu-west-2.amazonaws.com/{AWS_ACCOUNT_ID}/rtg-automotive-sqs-queue"
)
all_messages = get_all_sqs_messages(sqs_queue_url)
print(all_messages)

# AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]


# def get_last_n_sqs_messages(queue_url, max_messages=10):
#     sqs_client = boto3.client("sqs", region_name="eu-west-2")
#     messages = []

#     # Receive messages from the SQS queue
#     response = sqs_client.receive_message(
#         QueueUrl=queue_url,
#         MaxNumberOfMessages=max_messages,
#         WaitTimeSeconds=5,
#         MessageAttributeNames=["All"],
#     )

#     # Ensure we retrieve exactly N messages
#     if "Messages" in response:
#         for message in response["Messages"]:
#             # Check if 'Attributes' exists in the message
#             timestamp = message.get("Attributes", {}).get("SentTimestamp", None)
#             messages.append(message["Body"])

#     return messages[:max_messages]  # Return exactly N messages


# # Example usage
# sqs_queue_url = (
#     f"https://sqs.eu-west-2.amazonaws.com/{AWS_ACCOUNT_ID}/rtg-automotive-sqs-queue"
# )
# last_10_messages = get_last_n_sqs_messages(sqs_queue_url, 10)
# print(last_10_messages)

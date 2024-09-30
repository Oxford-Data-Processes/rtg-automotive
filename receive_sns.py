import boto3
import json
import os


AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]


def get_last_10_sqs_messages(queue_url):
    sqs_client = boto3.client("sqs", region_name="eu-west-2")
    messages = []

    # Receive messages from the SQS queue
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=5,
        MessageAttributeNames=["All"],
    )

    for message in response.get("Messages", []):
        # Check if 'Attributes' exists in the message
        timestamp = message.get("Attributes", {}).get("SentTimestamp", None)
        messages.append(
            {
                "body": message["Body"],
                "timestamp": timestamp,
            }
        )

    return messages


# Example usage
sqs_queue_url = (
    f"https://sqs.eu-west-2.amazonaws.com/{AWS_ACCOUNT_ID}/rtg-automotive-sqs-queue"
)
last_10_messages = get_last_10_sqs_messages(sqs_queue_url)
print(json.dumps(last_10_messages, indent=2))

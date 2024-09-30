import boto3

# Create an SNS client
sns_client = boto3.client("sns", region_name="eu-west-2")  # e.g., 'us-east-1'

# Define the message and the topic ARN
message = "Your notification message here"
topic_arn = (
    "arn:aws:sns:eu-west-2:654654324108:stock-notifications"  # Updated topic ARN
)

# Send the notification
response = sns_client.publish(
    TopicArn=topic_arn, Message=message, Subject="Your Subject Here"
)

# Print the response
print(response)

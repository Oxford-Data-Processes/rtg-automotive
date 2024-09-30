import boto3
import streamlit as st

# Create an SNS client
sns_client = boto3.client("sns", region_name="eu-west-2")


# Function to subscribe to the SNS topic
def subscribe_to_sns(topic_arn, protocol="email"):
    response = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol=protocol,
        Endpoint="your_email@example.com",  # Replace with the email address to receive notifications
    )
    return response


# Function to display the latest message from SNS
def display_sns_message():
    # Retrieve the subscriptions for the SNS topic
    response = sns_client.list_subscriptions_by_topic(
        TopicArn="arn:aws:sns:eu-west-2:654654324108:rtg-automotive-stock-notifications"
    )

    if response["Subscriptions"]:
        latest_subscription = response["Subscriptions"][-1]
        st.write(
            f"Latest SNS message for subscription {latest_subscription['SubscriptionArn']} will be displayed here."
        )
        # Instead of getting the message from subscription attributes, we will display the subscription ARN
        st.write(f"Subscription ARN: {latest_subscription['SubscriptionArn']}")
    else:
        st.write("No subscriptions found.")


# Streamlit UI
st.title("SNS Subscription App")

if st.button("Subscribe to SNS Topic"):
    topic_arn = "arn:aws:sns:eu-west-2:654654324108:rtg-automotive-stock-notifications"  # Updated topic ARN
    response = subscribe_to_sns(topic_arn)

    st.success("Subscribed to SNS topic! Check your email for confirmation.")
display_sns_message()

import boto3
import streamlit as st

# Create an SNS client
sns_client = boto3.client("sns", region_name="eu-west-2")


# Function to subscribe to the SNS topic
def subscribe_to_sns(topic_arn):
    response = sns_client.subscribe(TopicArn=topic_arn)
    return response


# Function to display the latest message from SNS
def display_sns_message():
    # This is a placeholder for the actual message retrieval logic
    # In a real application, you would implement a way to fetch the latest message
    st.write("Latest SNS message will be displayed here.")


# Streamlit UI
st.title("SNS Subscription App")

if st.button("Subscribe to SNS Topic"):
    topic_arn = (
        "arn:aws:sns:eu-west-2:654654324108:stock-notifications"  # Updated topic ARN
    )
    response = subscribe_to_sns(topic_arn)
    st.success("Subscribed to SNS topic! Check your email for confirmation.")

display_sns_message()

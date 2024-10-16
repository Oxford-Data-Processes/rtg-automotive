# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

# Set environment variable
ENV AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
ENV AWS_ACCESS_KEY_ID_ADMIN=${AWS_ACCESS_KEY_ID_ADMIN}
ENV AWS_SECRET_ACCESS_KEY_ADMIN=${AWS_SECRET_ACCESS_KEY_ADMIN}

# Install git
RUN yum install -y git

# Copy the requirements file
COPY requirements.txt ./

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the function code
COPY . ./

# Command to run the Lambda function
CMD ["main.lambda_handler"]
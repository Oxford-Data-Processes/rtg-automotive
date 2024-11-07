# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

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
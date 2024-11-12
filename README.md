# rtg-automotive

Start up:

python -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt

Bash:

bash src/bash/docker.sh {example-lambda-function-name}

Checks:

pre-commit run --all-files

mypy {path_to_file_or_directory} --explicit-package-bases

TO DO:

Create RDS database with ACID transactions. Use RDS as app backend.

Create API backend that works with RDS database.

Daily Pipeline steps:

1. Stock Feed xlsx files are uploaded to AWS S3 bucket using Streamlit frontend.
2. process_stock_feed Lambda function is triggered for each file to read the xlsx files from S3, use Athena to query store tables, process the data and send as parquet files to supplier_stock S3 locations.
3. add_partition Lambda function is triggered to update the AWS Glue catalog with new partitions for supplier_stock table and generate SNS notification when process is complete to update the frontend.
4. SNS notification is used to trigger the next step. Inside a generate_ebay_table Lambda, generate eBay table using Athena query that combines/manipulates/transforms data from supplier_stock and store tables. Write outputs to ebay folder in S3.
5. Generate SNS notification when process is complete to update the frontend.


Manual update steps:

- Weekly update of store table.


curl -X GET "http://localhost:8000/items/?table_name=supplier_stock&filters=%7B%22part_number%22%3A%22ABR101%22%7D&limit=5"
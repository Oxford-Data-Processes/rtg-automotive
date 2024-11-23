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

********

Get API ID programmatically, add to AWS utils.
Use pydantic to validate data coming in and going out of API.
Add the ability for users to undo database operations based on an ID. For every operation there is an equivalent inverse operation. Delete flag, version number, last_operation_id (linked to logs with operation type and query), log table (parquet in athena) keeps copy of old values (previous versions) and operation_id and operation data.
Create mechanism for reducing size of tables.
Implement daily database backups (kept for up to 30 days) with mysqldump.

Add functionality to frontend to update the tables (Group by store).
Clean up code and write any modules/utils that I can re-use for other projects.
Add unit tests for API inside Lambda function, mock the database.
Add real integration test for API without mocking within dev environment.
Add frontend tests using mocked API.
Add end to end tests that work within dev environment only.

Daily Pipeline steps:

1. Stock Feed xlsx files are uploaded to AWS S3 bucket using Streamlit frontend.
2. process_stock_feed Lambda function is triggered for each file to read the xlsx files from S3, process the data and write to RDS database.
4. Inside a generate_ebay_table Lambda, triggered by a published event from the frontend, generate eBay table using SQL query that combines/manipulates/transforms data from supplier_stock and store tables. Write result to ebay table in RDS database.
5. Generate SNS notification when process is complete to update the frontend.


Manual update steps:

- Weekly update of store table.


curl -X GET "http://localhost:8000/items/?table_name=supplier_stock&filters=%7B%22part_number%22%3A%22ABR101%22%7D&limit=5"
curl -X GET "http://localhost:8000/items/?table_name=supplier_stock&filters=%7B%22custom_label%22%3A%22UKD-APE-ABR101%22%7D&limit=5"
curl -X GET "http://localhost:8000/items/?table_name=supplier_stock&filters=%7B%22updated_date%22%3A%222024-11-21%22%7D&limit=5"
curl -X GET "http://localhost:8000/items/?table_name=store&limit=5"
curl -X GET "http://localhost:8000/items/?table_name=ebay&limit=5"
curl -X GET "http://localhost:8000/items/?table_name=supplier_stock&filters=%7B%22supplier%22%3A%22APE%22%7D&columns=custom_label,part_number&limit=10000"


curl -X GET "https://tsybspea31.execute-api.eu-west-2.amazonaws.com/dev/items/?table_name=supplier_stock&filters=%7B%22supplier%22%3A%22APE%22%7D&columns=custom_label,part_number&limit=10000"




curl -X GET "https://tsybspea31.execute-api.eu-west-2.amazonaws.com/dev/items/?table_name=supplier_stock&filters=%7B%22part_number%22%3A%22ABR101%22%7D&limit=5"

curl -X GET "https://tsybspea31.execute-api.eu-west-2.amazonaws.com/dev/items/?table_name=supplier_stock&filters=%7B%22part_number%22%3A%22ABR101%22%7D&limit=5"


jdbc:mysql://rtg-automotive-db.c14oos6givty.eu-west-2.rds.amazonaws.com:3306

curl -X POST "http://localhost:8000/items/?table_name=supplier_stock&type=append" \
-H "Content-Type: application/json" \
-d '{
    "items": [
        {
            "custom_label": "ABR101",
            "part_number": "ABR101",
            "supplier": "SupplierA",
            "quantity": 10,
            "updated_date": "2023-10-01"
        },
        {
            "custom_label": "XYZ202",
            "part_number": "XYZ202",
            "supplier": "SupplierB",
            "quantity": 5,
            "updated_date": "2023-10-01"
        }
    ]
}'


curl -X POST "https://tsybspea31.execute-api.eu-west-2.amazonaws.com/dev/items/?table_name=supplier_stock&type=append" \
-H "Content-Type: application/json" \
-d '{
    "items": [
        {
            "custom_label": "XYZ205",
            "part_number": "XYZ202",
            "supplier": "SupplierB",
            "quantity": 5,
            "updated_date": "2023-10-20"
        }
    ]
}'

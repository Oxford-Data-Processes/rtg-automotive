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
2. process_stock_feed Lambda function is triggered for each file to read the xlsx files from S3, process the data and write to RDS database.
4. Inside a generate_ebay_table Lambda, triggered by a published event from the frontend, generate eBay table using SQL query that combines/manipulates/transforms data from supplier_stock and store tables. Write result to ebay table in RDS database.
5. Generate SNS notification when process is complete to update the frontend.


Manual update steps:

- Weekly update of store table.


curl -X GET "http://localhost:8000/items/?table_name=supplier_stock&filters=%7B%22part_number%22%3A%22ABR101%22%7D&limit=5"
curl -X GET "http://localhost:8000/items/?table_name=supplier_stock&filters=%7B%22custom_label%22%3A%22UKD-APE-ABR101%22%7D&limit=5"
curl -X GET "http://localhost:8000/items/?table_name=store&limit=5"


curl -X GET "https://tsybspea31.execute-api.eu-west-2.amazonaws.com/dev/items/?table_name=supplier_stock&filters=%7B%22part_number%22%3A%22ABR101%22%7D&limit=5"



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

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

Create RDS database which is a replica of the S3 data, but with ACID transactions. Use RDS as app backend.

Add feature lets user upload an Excel (list ) of custom_labels to update or inspect

Updating pricing, when they end, lots of edits of data

Ability to add a new supplier and a new rule and a new SF

give each function a different name (4 options)

Bulk Item Uploader for Store Database - Update, append, delete 

Stock Feed Master uploader (Deleting custom_labels in stock master and in Ebay Store)

Bulk delete of custom labels -> create csv upload for ebay for item ids -> remove from stock master

Add a new feature that actually

Some item ids are not active, function for replacing the item id when eBay updates item ids every couple of weeks Phil changes them manually.

(provide user the ability update the store but only change item ids, swapping old ones for new ones)

Just replacing price, or just replacing category. First column is current item_id then other columns are the ones that are changing.

Update function: Philip doesn't display exact quantities - update functions require store 

Daily Pipeline steps:

1. Stock Feed xlsx files are uploaded to AWS S3 bucket using Streamlit frontend.
2. process_stock_feed Lambda function is triggered for each file to read the xlsx files from S3, use Athena to query store and product tables, process the data and send as parquet files to supplier_stock S3 locations.
3. add_partition Lambda function is triggered to update the AWS Glue catalog with new partitions for supplier_stock table and generate SNS notification when process is complete to update the frontend.
4. SNS notification is used to trigger the next step. Inside a generate_ebay_table Lambda, generate eBay table using Athena query that combines/manipulates/transforms data from supplier_stock, product and store tables. Write outputs to ebay folder in S3.
5. Generate SNS notification when process is complete to update the frontend.


Manual update steps:

- Weekly update of store table.
- Monthly update of product table.

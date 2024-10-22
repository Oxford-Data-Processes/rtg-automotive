# rtg-automotive

TO DO:

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



Design:

Tables:

Table: product

Description: Table that contains mapping of part_number and supplier to custom_label. Small table and mainly static. Refreshed monthly, then parquet file is recreated.
Location: Single data.parquet file inside product folder of AWS rtg-automotive S3 bucket. Versioned. Versions older than 1 month are deleted.

Columns:
- custom_label: text
- part_number: text
- supplier: text

Read frequency: Daily
Write frequency: Monthly
Read throughput minimum (MB/s): 10
Write throughput minimum (MB/s): 0.1
Type (Append-only, Overwrite, Upsert): Overwrite
Estimated size (MB): 7


Table: store

Description: Table that contains details of each store. Mainly static, very large table. Partitioned by store and supplier. Updated weekly. Reads of entire table are daily.
Location: Several data.parquet files inside store/ebay_store={ebay_store}/supplier={supplier} folders of AWS rtg-automotive S3 bucket. Versioned. Versions older than 1 month are deleted.

Columns:
- item_id: bigint
- custom_label: text
- title: text
- current_price: double
- prefix: text
- uk_rtg: text
- fps_wds_dir: text
- payment_profile_name: text
- shipping_profile_name: text
- return_profile_name: text
- supplier: text
- ebay_store: text

Read frequency: Daily
Write frequency: Weekly
Read throughput minimum (MB/s): 100
Write throughput minimum (MB/s): 0.1
Type (Append-only, Overwrite, Upsert): Upsert
Estimated size (MB): 1,270

Table: supplier_stock

Description: Table that contains historical stock data for each supplier. Updated daily. Partitioned by supplier and updated_date. Data is added daily.
Location: data.parquet files inside supplier_stock/supplier={supplier}/year={year}/month={month}/day={day} folders of AWS rtg-automotive S3 bucket. Data with updated_date older than 1 month is deleted.

Columns:
- custom_label
- part_number
- supplier
- quantity
- year
- month
- day
- updated_date

Read frequency: Daily
Write frequency: Daily
Read throughput minimum (MB/s): 100
Write throughput minimum (MB/s): 10
Type (Append-only, Overwrite, Upsert): Append-only
Estimated size (MB): 22 (appended daily)

Table: ebay

Description: Table that contains details of each ebay listing. Partitioned by ebay_store. Updated daily. Large table, overwrites are daily.
Location: data.parquet files inside ebay/ebay_store={ebay_store} folder of AWS rtg-automotive S3 bucket. Versioned. Versions older than 1 month are deleted.

Columns:
- item_id
- quantity_delta
- quantity
- custom_label
- supplier_store
- ebay_store

Read frequency: Daily
Write frequency: Daily
Read throughput minimum (MB/s): 100
Write throughput minimum (MB/s): 100
Type (Append-only, Overwrite, Upsert): Overwrite
Estimated size (MB): 276

---

Preparation steps:
1. Create a store parquet files inside AWS S3 bucket.
2. Create a product parquet files inside S3.
3. Create initial supplier_stock parquet files inside S3.

Daily Pipeline steps:

1. Stock Feed xlsx files are uploaded to AWS S3 bucket using Streamlit frontend.
2. process_stock_feed Lambda function is triggered for each file to read the xlsx files from S3, use Athena to query store and product tables, process the data and send as parquet files to supplier_stock S3 locations.
3. add_partition Lambda function is triggered to update the AWS Glue catalog with new partitions for supplier_stock table and generate SNS notification when process is complete to update the frontend.
4. SNS notification is used to trigger the next step. Inside a generate_ebay_table Lambda, generate eBay table using Athena query that combines/manipulates/transforms data from supplier_stock, product and store tables. Write outputs to ebay folder in S3.
5. Generate SNS notification when process is complete to update the frontend.


Manual update steps:

- Weekly update of store table.
- Monthly update of product table.


Commands:


# Serverless local invoke

npm install -g serverless
npm install serverless-python-requirements
serverless requirements install --stage dev
serverless invoke local --function process-stock-feed --stage dev --data "$(cat test_events/putStockFeed.json)"

# Serverless deploy

serverless deploy --stage dev

# Docker local run

docker buildx build --no-cache --build-arg AWS_ACCOUNT_ID=654654324108 --build-arg AWS_REGION=eu-west-2 -t process-stock-feed src/lambda/process_stock_feed
docker buildx build --build-arg AWS_ACCOUNT_ID=654654324108 --build-arg AWS_REGION=eu-west-2 -t process-stock-feed src/lambda/process_stock_feed

docker run -p 9000:8080 \
  -e AWS_ACCESS_KEY_ID_ADMIN \
  -e AWS_SECRET_ACCESS_KEY_ADMIN \
  -e AWS_REGION=eu-west-2 \
  process-stock-feed

curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @test_events/putStockFeed.json



# Docker Build

# If repository does not exist
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 654654324108.dkr.ecr.eu-west-2.amazonaws.com
aws ecr create-repository --repository-name process-stock-feed --region eu-west-2

docker buildx build --platform linux/amd64 -t process-stock-feed .
docker tag process-stock-feed:latest 654654324108.dkr.ecr.eu-west-2.amazonaws.com/process-stock-feed:latest
docker push 654654324108.dkr.ecr.eu-west-2.amazonaws.com/process-stock-feed:latest

docker run -p 9000:8080 \


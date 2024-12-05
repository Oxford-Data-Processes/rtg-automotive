module "process_stock_feed_lambda_eventbridge" {
  source               = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/eventbridge"
  lambda_function_name = "process-stock-feed-lambda"
  event_pattern = jsonencode({
    "source" : ["com.oxforddataprocesses"],
    "detail-type" : ["S3PutObject"]
  })
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  project        = var.project
}

module "generate_ebay_table_lambda_eventbridge" {
  source               = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/eventbridge"
  lambda_function_name = "generate-ebay-table-lambda"
  event_pattern = jsonencode({
    "source" : ["com.oxforddataprocesses"],
    "detail-type" : ["RtgAutomotiveGenerateEbayTable"]
  })
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  project        = var.project
}

module "run_sql_query_lambda_eventbridge" {
  source               = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/eventbridge"
  lambda_function_name = "run-sql-query-lambda"
  event_pattern = jsonencode({
    "source" : ["com.oxforddataprocesses"],
    "detail-type" : ["RtgAutomotiveRunSQLQuery"]
  })
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  project        = var.project
}


module "create_parquet_lambda_eventbridge" {
  source               = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/eventbridge"
  lambda_function_name = "create-parquet-lambda"
  event_pattern = jsonencode({
    "source" : ["com.oxforddataprocesses"],
    "detail-type" : ["RtgAutomotiveCreateParquet"]
  })
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  project        = var.project
}

module "s3_event_router_lambda" {
  source                      = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/s3_event_router_lambda"
  aws_account_id              = var.aws_account_id
  aws_region                  = var.aws_region
  stage                       = var.stage
  project                     = var.project
  aws_access_key_id_admin     = var.aws_access_key_id_admin
  aws_secret_access_key_admin = var.aws_secret_access_key_admin
  version_number              = var.version_number
}

module "process_stock_feed" {
  source                      = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/lambda"
  lambda_function_name        = "${var.project}-process-stock-feed-lambda"
  aws_account_id              = var.aws_account_id
  aws_region                  = var.aws_region
  stage                       = var.stage
  aws_access_key_id_admin     = var.aws_access_key_id_admin
  aws_secret_access_key_admin = var.aws_secret_access_key_admin
  version_number              = var.version_number
}

module "generate_ebay_table" {
  source                      = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/lambda"
  lambda_function_name        = "${var.project}-generate-ebay-table-lambda"
  aws_account_id              = var.aws_account_id
  aws_region                  = var.aws_region
  stage                       = var.stage
  aws_access_key_id_admin     = var.aws_access_key_id_admin
  aws_secret_access_key_admin = var.aws_secret_access_key_admin
  version_number              = var.version_number
}

module "run_sql_query" {
  source                      = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/lambda"
  lambda_function_name        = "${var.project}-run-sql-query-lambda"
  aws_account_id              = var.aws_account_id
  aws_region                  = var.aws_region
  stage                       = var.stage
  aws_access_key_id_admin     = var.aws_access_key_id_admin
  aws_secret_access_key_admin = var.aws_secret_access_key_admin
  version_number              = var.version_number
}

module "create_parquet" {
  source                      = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/lambda"
  lambda_function_name        = "${var.project}-create-parquet-lambda"
  aws_account_id              = var.aws_account_id
  aws_region                  = var.aws_region
  stage                       = var.stage
  aws_access_key_id_admin     = var.aws_access_key_id_admin
  aws_secret_access_key_admin = var.aws_secret_access_key_admin
  version_number              = var.version_number
}

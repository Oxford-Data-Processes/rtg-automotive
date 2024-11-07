locals {
  columns_data = jsondecode(file("../src/aws_lambda/api/models/glue_schemas.json"))

  rtg_automotive_supplier_stock_columns       = local.columns_data.rtg_automotive_supplier_stock.columns
  rtg_automotive_supplier_stock_partition_keys = local.columns_data.rtg_automotive_supplier_stock.partition_keys

  rtg_automotive_product_columns              = local.columns_data.rtg_automotive_product.columns
  rtg_automotive_product_partition_keys      = local.columns_data.rtg_automotive_product.partition_keys

  rtg_automotive_store_columns                = local.columns_data.rtg_automotive_store.columns
  rtg_automotive_store_partition_keys         = local.columns_data.rtg_automotive_store.partition_keys
}

resource "aws_glue_catalog_database" "rtg_automotive" {
  name = "rtg_automotive"
}

resource "aws_athena_workgroup" "project_workgroup" {
  name = "${var.project}-workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.project}-bucket-${var.aws_account_id}/athena_results/"
    }
  }
}

module "rtg_automotive_supplier_stock" {
  source         = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/glue_table"
  database_name  = aws_glue_catalog_database.rtg_automotive.name
  table_name     = "supplier_stock"
  aws_account_id = var.aws_account_id
  project        = var.project
  columns        = local.rtg_automotive_supplier_stock_columns
  partition_keys = local.rtg_automotive_supplier_stock_partition_keys
}

module "rtg_automotive_product" {
  source         = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/glue_table"
  database_name  = aws_glue_catalog_database.rtg_automotive.name
  table_name     = "product"
  aws_account_id = var.aws_account_id
  project        = var.project
  columns        = local.rtg_automotive_product_columns
  partition_keys = local.rtg_automotive_product_partition_keys

}

module "rtg_automotive_store" {
  source         = "git::https://github.com/Oxford-Data-Processes/terraform.git//modules/glue_table"
  database_name  = aws_glue_catalog_database.rtg_automotive.name
  table_name     = "store"
  aws_account_id = var.aws_account_id
  project        = var.project
  columns        = local.rtg_automotive_store_columns
  partition_keys = local.rtg_automotive_store_partition_keys
}

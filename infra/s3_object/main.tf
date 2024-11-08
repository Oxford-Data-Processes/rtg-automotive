locals {
  process_stock_feed_config_path = "${path.module}/../../data/process_stock_feed_config.json"
  process_stock_feed_config_hash = filemd5(
    "${path.module}/../../data/process_stock_feed_config.json"
  )
}

resource "aws_s3_object" "process_stock_feed_config" {
  bucket = "${var.project}-bucket-${var.aws_account_id}"
  key    = "config/process_stock_feed_config.json"
  source = local.process_stock_feed_config_path

  etag = local.process_stock_feed_config_hash

  lifecycle {
    create_before_destroy = true
  }
}

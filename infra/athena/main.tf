resource "aws_athena_database" "rtg_automotive" {
  name   = "rtg_automotive"
  bucket = aws_s3_bucket.project_bucket.bucket
}

resource "aws_athena_table" "supplier_stock" {
  name          = "supplier_stock"
  database_name = aws_athena_database.rtg_automotive.name

  bucket = aws_s3_bucket.project_bucket.bucket

  table_type = "EXTERNAL_TABLE"

  columns {
    name = "custom_label"
    type = "string"
  }

  columns {
    name = "part_number"
    type = "string"
  }

  columns {
    name = "supplier"
    type = "string"
  }

  columns {
    name = "quantity"
    type = "int"
  }

  columns {
    name = "year"
    type = "int"
  }

  columns {
    name = "month"
    type = "int"
  }

  columns {
    name = "day"
    type = "int"
  }

  columns {
    name = "updated_date"
    type = "string"
  }

  partitioned_by = ["supplier", "updated_date"]

  location = "s3://${aws_s3_bucket.project_bucket.bucket}/supplier_stock/"
}
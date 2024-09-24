resource "aws_athena_database" "rtg_automotive" {
  name   = "rtg_automotive"
  bucket = module.s3_bucket.project_bucket.bucket
}

resource "aws_athena_table" "supplier_stock" {
  name          = "supplier_stock"
  database_name = aws_athena_database.rtg_automotive.name

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

  partitioned_by = ["supplier", "year", "month", "day"]

  location = "s3://${module.s3_bucket.project_bucket.bucket}/supplier_stock/"

  permissions {
    principal = "athena.amazonaws.com"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      module.s3_bucket.project_bucket.arn,
      "${module.s3_bucket.project_bucket.arn}/supplier_stock/*"
    ]
  }
}

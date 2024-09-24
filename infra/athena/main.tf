resource "aws_glue_catalog_database" "rtg_automotive" {
  name = "rtg_automotive"
}

resource "aws_glue_catalog_table" "supplier_stock" {
  database_name = aws_glue_catalog_database.rtg_automotive.name
  name          = "supplier_stock"

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

  partition_keys {
    name = "supplier"
    type = "string"
  }

  partition_keys {
    name = "year"
    type = "int"
  }

  partition_keys {
    name = "month"
    type = "int"
  }

  partition_keys {
    name = "day"
    type = "int"
  }

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

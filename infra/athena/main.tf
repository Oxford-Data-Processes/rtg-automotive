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

  column {
    name = "part_number"
    type = "string"
  }

  column {
    name = "supplier"
    type = "string"
  }

  column {
    name = "quantity"
    type = "int"
  }

  column {
    name = "year"
    type = "int"
  }

  column {
    name = "month"
    type = "int"
  }

  column {
    name = "day"
    type = "int"
  }

  column {
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

  storage_descriptor {
    location = "s3://${module.s3_bucket.project_bucket.bucket}/supplier_stock/"
  }
}

resource "aws_glue_catalog_database" "rtg_automotive" {
  name = "rtg_automotive"
}

resource "aws_glue_catalog_table" "supplier_stock" {
  database_name = aws_glue_catalog_database.rtg_automotive.name
  name          = "supplier_stock"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL              = "TRUE"
    "parquet.compression" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${var.project}-bucket-${var.aws_account_id}/supplier_stock/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "supplier_stock"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"

      parameters = {
        "serialization.format" = 1
      }
    }

    columns {
      name = "custom_label"
      type = "string"
    }

    columns {
      name = "part_number"
      type = "string"
    }

    columns {
      name = "quantity"
      type = "int"
    }

    columns {
      name = "updated_date"
      type = "string"
    }
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
}
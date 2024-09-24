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


resource "aws_glue_catalog_table" "product" {
  database_name = aws_glue_catalog_database.rtg_automotive.name
  name          = "product"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL              = "TRUE"
    "parquet.compression" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${var.project}-bucket-${var.aws_account_id}/product/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "product"
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
      name = "supplier"
      type = "string"
    }

  }

}



resource "aws_glue_catalog_table" "store" {
  database_name = aws_glue_catalog_database.rtg_automotive.name
  name          = "store"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL              = "TRUE"
    "parquet.compression" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${var.project}-bucket-${var.aws_account_id}/store/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "store"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"

      parameters = {
        "serialization.format" = 1
      }
    }

    columns {
      name = "item_id"
      type = "bigint"
    }

    columns {
      name = "custom_label"
      type = "string"
    }

    columns {
      name = "title"
      type = "string"
    }

    columns {
      name = "current_price"
      type = "double"
    }

    columns {
      name = "prefix"
      type = "string"
    }

    columns {
      name = "uk_rtg"
      type = "string"
    }

    columns {
      name = "fps_wds_dir"
      type = "string"
    }

    columns {
      name = "payment_profile_name"
      type = "string"
    }

    columns {
      name = "shipping_profile_name"
      type = "string"
    }

    columns {
      name = "return_profile_name"
      type = "string"
    }

    columns {
      name = "supplier"
      type = "string"
    }

    columns {
      name = "ebay_store"
      type = "string"
    }
    
  }
  
}

resource "aws_athena_workgroup" "rtg_automotive_workgroup" {
  name = "${var.project}-workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.project}-bucket-${var.aws_account_id}/athena-results/"
    }
  }
}

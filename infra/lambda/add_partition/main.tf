locals {
  service_name = "add-partition"
}
resource "aws_iam_role" "lambda_iam" {
  force_detach_policies = true
  name                  = "${var.project}-${local.service_name}-lambda-role"
  assume_role_policy    = data.aws_iam_policy_document.assume_role_lambda.json
  path                  = "/${var.project}/${local.service_name}/"
}

resource "aws_iam_policy" "inline_policy" {
  name   = "${var.project}-${local.service_name}-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.project}-bucket-name",
          "arn:aws:s3:::${var.project}-bucket-name/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetTable",
          "glue:GetTables",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:GetPartition",
          "glue:CreatePartition",
          "glue:DeletePartition"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "sns:Publish"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_iam_to_policy_attachment" {
  policy_arn = aws_iam_policy.inline_policy.arn
  role       = aws_iam_role.lambda_iam.name
}

resource "aws_lambda_function" "add_partition" {
  function_name = "${var.project}-${local.service_name}"
}

resource "aws_lambda_event_source_mapping" "s3_trigger" {
  event_source_arn = "arn:aws:s3:::${var.project}-bucket-name"
  function_name    = aws_lambda_function.add_partition.arn
  starting_position = "LATEST"
  enabled          = true
  filter {
    key {
      prefix = [
        "supplier_stock/",
        "store/"
      ]
      suffix = ".parquet"
    }
  }
}

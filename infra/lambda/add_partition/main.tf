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
  policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_iam_role_policy_attachment" "lambda_iam_to_policy_attachment" {
  policy_arn = aws_iam_policy.inline_policy.arn
  role       = aws_iam_role.lambda_iam.name
}

resource "aws_lambda_event_source_mapping" "s3_trigger" {
  event_source_arn = "arn:aws:s3:::${var.project}-bucket-${var.aws_account_id}"
  function_name = "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:${var.project}-dev-${local.service_name}"
  starting_position = "LATEST"

  batch_size = 1

  filter {
    key {
      filter_rules {
        name  = "prefix"
        value = "supplier_stock/"
      }
      filter_rules {
        name  = "suffix"
        value = ".parquet"
      }
    }
  }
}

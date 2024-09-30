data "aws_iam_policy_document" "assume_role_lambda" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }
  }
}

data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
      "glue:CreatePartition",
      "glue:GetDatabase",
      "glue:GetTable",
      "glue:GetPartitions",
      "sns:Publish"  // Added permission for SNS Publish
    ]
    resources = [
      "arn:aws:s3:::${var.project}-bucket-${var.aws_account_id}",
      "arn:aws:s3:::${var.project}-bucket-${var.aws_account_id}/*",
      "arn:aws:glue:${var.aws_region}:${var.aws_account_id}:catalog",
      "arn:aws:glue:${var.aws_region}:${var.aws_account_id}:database/*",
      "arn:aws:glue:${var.aws_region}:${var.aws_account_id}:table/*",
      "arn:aws:sns:${var.aws_region}:${var.aws_account_id}:${var.project}-stock-notifications.fifo"  // Added resource for SNS
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

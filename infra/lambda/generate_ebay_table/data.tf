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
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.project}-bucket-${var.aws_account_id}",
      "arn:aws:s3:::${var.project}-bucket-${var.aws_account_id}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "glue:CreatePartition",
      "glue:GetDatabase",
      "glue:GetTable",
      "glue:GetPartitions"
    ]
    resources = [
      "arn:aws:glue:${var.aws_region}:${var.aws_account_id}:catalog",
      "arn:aws:glue:${var.aws_region}:${var.aws_account_id}:database/*",
      "arn:aws:glue:${var.aws_region}:${var.aws_account_id}:table/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "athena:StartQueryExecution"  // Added permission for Athena
    ]
    resources = [
      "arn:aws:athena:${var.aws_region}:${var.aws_account_id}:workgroup/*"  // Added resource for Athena
    ]
  }
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

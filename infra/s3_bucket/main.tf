locals {
  service = "rtg-automotive"
}


resource "aws_s3_bucket" "project_bucket" {
  bucket = "${var.project}-bucket-${var.aws_account_id}"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "delete-old-objects"
    enabled = true

    expiration {
      days = 30
    }
  }
}

data "aws_iam_policy_document" "project_bucket_policy" {
  statement {
    actions = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      "${aws_s3_bucket.project_bucket.arn}",
      "${aws_s3_bucket.project_bucket.arn}/*"
    ]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
  statement {
    actions = ["s3:GetBucketLocation", "s3:ListBucket", "s3:GetObject", "s3:PutObject"]
    resources = [
      "${aws_s3_bucket.project_bucket.arn}",
      "${aws_s3_bucket.project_bucket.arn}/*"
    ]
    principals {
      type        = "Service"
      identifiers = ["athena.amazonaws.com"]
    }
  }
}

resource "aws_s3_bucket_policy" "project_bucket_policy" {
  bucket = aws_s3_bucket.project_bucket.bucket

  policy = data.aws_iam_policy_document.project_bucket_policy.json
}

resource "aws_s3_bucket_public_access_block" "project_bucket_public_access_block" {
  bucket = aws_s3_bucket.project_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}


resource "aws_s3_bucket" "stock_feed_bucket" {
  bucket = "${local.service}-stock-feed-bucket-${var.aws_account_id}"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "delete-old-objects"
    enabled = true

    expiration {
      days = 30
    }
  }
}

data "aws_iam_policy_document" "stock_feed_bucket_policy" {
  statement {
    actions = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      "${aws_s3_bucket.stock_feed_bucket.arn}",
      "${aws_s3_bucket.stock_feed_bucket.arn}/*"
    ]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
  statement {
    actions = ["s3:GetBucketLocation", "s3:ListBucket", "s3:GetObject", "s3:PutObject"]
    resources = [
      "${aws_s3_bucket.stock_feed_bucket.arn}",
      "${aws_s3_bucket.stock_feed_bucket.arn}/*"
    ]
    principals {
      type        = "Service"
      identifiers = ["athena.amazonaws.com"]
    }
  }
}

resource "aws_s3_bucket_policy" "stock_feed_bucket_policy" {
  bucket = aws_s3_bucket.stock_feed_bucket.bucket

  policy = data.aws_iam_policy_document.stock_feed_bucket_policy.json
}

resource "aws_s3_bucket_public_access_block" "stock_feed_bucket_public_access_block" {
  bucket = aws_s3_bucket.stock_feed_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}
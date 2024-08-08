terraform {
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }

  required_version = ">= 1.1.0"
}

provider "aws" {
  profile = "speedsheet-management"
  region  = "eu-west-2"
}

# Test resource: DynamoDB table
resource "aws_dynamodb_table" "test_table" {
  name         = "${var.project}-test-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name        = "${var.project} Test Table"
    Environment = "Test"
    Project     = var.project
  }
}

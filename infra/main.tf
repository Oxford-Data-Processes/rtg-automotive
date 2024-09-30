terraform {
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.68"
    }
  }

  required_version = ">= 1.9.0"
}

provider "aws" {
  region = "eu-west-2"
}

module "s3_bucket" {
  aws_account_id = var.aws_account_id
  project        = var.project
  stage          = var.stage
  aws_region     = var.aws_region
  source         = "./s3_bucket"
}

module "athena" {
  aws_account_id = var.aws_account_id
  project        = var.project
  stage          = var.stage
  source         = "./athena"
}

module "add_partition" {
  aws_account_id = var.aws_account_id
  project        = var.project
  stage          = var.stage
  aws_region     = var.aws_region
  source         = "./lambda/add_partition"
}

module "process_stock_feed" {
  aws_account_id = var.aws_account_id
  project        = var.project
  stage          = var.stage
  aws_region     = var.aws_region
  source         = "./lambda/process_stock_feed"
}

module "generate_ebay_table" {
  aws_account_id = var.aws_account_id
  project        = var.project
  stage          = var.stage
  aws_region     = var.aws_region
  source         = "./lambda/generate_ebay_table"
}

module "sns" {
  aws_account_id = var.aws_account_id
  project        = var.project
  stage          = var.stage
  aws_region     = var.aws_region
  source         = "./sns"
}
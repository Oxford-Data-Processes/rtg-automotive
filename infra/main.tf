terraform {
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
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
  source         = "./s3_bucket"
}


module "lambda" {
  aws_account_id              = var.aws_account_id
  aws_region                  = var.aws_region
  stage                       = var.stage
  project                     = var.project
  aws_access_key_id_admin     = var.aws_access_key_id_admin
  aws_secret_access_key_admin = var.aws_secret_access_key_admin
  version_number              = var.version_number
  source                      = "./lambda"
}

module "sqs" {
  aws_account_id = var.aws_account_id
  project        = var.project
  stage          = var.stage
  aws_region     = var.aws_region
  source         = "./sqs"
}
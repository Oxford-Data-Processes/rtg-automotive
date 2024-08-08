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

resource "aws_db_instance" "rtg_automotive_db" {
  identifier           = "${var.project}-db"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  storage_type         = "gp2"
  db_name              = "rtg_automotive"
  username             = "rtg_admin"
  password             = "rtg_password_123!"  # Note: Use a more secure password in production
  parameter_group_name = "default.mysql8.0"
  skip_final_snapshot  = true

  tags = {
    Name    = "${var.project}-db"
    Project = var.project
  }
}

output "database_endpoint" {
  description = "The connection endpoint for the database"
  value       = aws_db_instance.rtg_automotive_db.endpoint
}

output "database_name" {
  description = "The name of the database"
  value       = aws_db_instance.rtg_automotive_db.db_name
}

output "database_username" {
  description = "The master username for the database"
  value       = aws_db_instance.rtg_automotive_db.username
}

# Note: Never output the database password in a real-world scenario
# This is just for demonstration purposes
output "database_password" {
  description = "The master password for the database"
  value       = aws_db_instance.rtg_automotive_db.password
  sensitive   = true
}


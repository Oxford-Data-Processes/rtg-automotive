# variables.tf
variable "db_name" {
  description = "The name of the database"
  type        = string
  default     = "mydatabase"
}

variable "db_username" {
  description = "The database admin username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "The database admin password"
  type        = string
  default     = "password"
  sensitive   = true
}

variable "db_instance_class" {
  description = "The instance type of the RDS instance"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "The allocated storage in GBs"
  type        = number
  default     = 20
}

variable "vpc_id" {
  description = "The VPC ID where the RDS instance will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "The Subnet IDs for the RDS instance"
  type        = list(string)
}

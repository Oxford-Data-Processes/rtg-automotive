resource "aws_db_instance" "project_db" {
  identifier              = "${var.project}-mysql"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"
  allocated_storage       = 20
  storage_type           = "gp2"
  username               = "admin"
  password               = "password"
  db_name                = "${var.project}_db"
  skip_final_snapshot    = true
  publicly_accessible     = false
  availability_zone      = "eu-west-2b"
  tags = {
    Name = "${var.project}-mysql"
  }
}

resource "aws_db_subnet_group" "project_db_subnet_group" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = [
    "subnet-0f2a9c6c74c625597",
    "subnet-0a935a31921a0ae59",
    "subnet-0dcbe5315e9a423fb"
  ]

  tags = {
    Name = "${var.project}-db-subnet-group"
  }
}

resource "aws_db_parameter_group" "project_db_parameter_group" {
  name   = "${var.project}-db-parameter-group"
  family = "mysql8.0"

  parameter {
    name  = "max_connections"
    value = "150"
  }
}

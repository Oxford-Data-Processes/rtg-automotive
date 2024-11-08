# Start Generation Here
resource "aws_db_instance" "default" {
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
  tags = {
    Name = "${var.project}-mysql"
  }
}

resource "aws_db_subnet_group" "default" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.project}-db-subnet-group"
  }
}

resource "aws_db_parameter_group" "default" {
  name   = "${var.project}-db-parameter-group"
  family = "mysql8.0"

  parameter {
    name  = "max_connections"
    value = "150"
  }
}

resource "aws_vpc" "project_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project}-vpc"
  }
}

resource "aws_security_group" "project_db_sg" {
  name   = "${var.project}-db-sg"
  vpc_id = aws_vpc.project_vpc.id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-db-sg"
  }
}

resource "aws_db_instance" "project_db" {
  identifier             = "${var.project}-mysql"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_type           = "gp2"
  username               = "admin"
  password               = "password"
  db_name                = "rtg_automotive"
  skip_final_snapshot    = true
  publicly_accessible    = true
  availability_zone      = "eu-west-2b"
  vpc_security_group_ids = [aws_security_group.project_db_sg.id]
}

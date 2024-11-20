resource "aws_vpc" "project_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project}-vpc"
  }
}

resource "aws_subnet" "project_subnet_a" {
  vpc_id            = aws_vpc.project_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-west-2a"

  tags = {
    Name = "${var.project}-subnet-a"
  }
}

resource "aws_subnet" "project_subnet_b" {
  vpc_id            = aws_vpc.project_vpc.id
  cidr_block        = "10.0.3.0/24" // Changed from 10.0.2.0/24 to avoid conflict
  availability_zone = "eu-west-2b"

  tags = {
    Name = "${var.project}-subnet-b"
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

resource "aws_db_subnet_group" "project_db_subnet_group" {
  name = "${var.project}-db-subnet-group"
  subnet_ids = [
    aws_subnet.project_subnet_a.id,
    aws_subnet.project_subnet_b.id
  ]

  tags = {
    Name = "${var.project}-db-subnet-group"
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
  vpc_security_group_ids = [aws_security_group.project_db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.project_db_subnet_group.name

  tags = {
    Name = "${var.project}-db"
  }
}

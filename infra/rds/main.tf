resource "aws_security_group" "rds_sg" {
  name        = "${var.project}-rds-sg"
  description = "Allow MySQL access from any IP"

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
    Name    = "${var.project}-rds-sg"
    Project = var.project
  }
}

resource "aws_db_instance" "rtg_automotive_db" {
  identifier           = "${var.project}-db"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  storage_type         = "gp2"
  username             = "admin"
  password             = "password"
  parameter_group_name = "default.mysql8.0"
  skip_final_snapshot  = true
  publicly_accessible  = true

  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  tags = {
    Name    = "${var.project}-db"
    Project = var.project
  }
}

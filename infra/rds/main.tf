
resource "aws_db_instance" "project_db" {
  identifier              = "${var.project}-mysql"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"
  allocated_storage       = 20
  storage_type           = "gp2"
  username               = "admin"
  password               = "password"
  db_name                = "rtg_automotive"
  skip_final_snapshot    = true
  publicly_accessible     = false
  availability_zone      = "eu-west-2b"
  vpc_security_group_ids  = [aws_security_group.project_db_sg.id]
}

resource "aws_security_group" "project_db_sg" {
  name        = "${var.project}-db-sg"
  vpc_id      = "vpc-00a7294c2ecfc4ffa" 

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

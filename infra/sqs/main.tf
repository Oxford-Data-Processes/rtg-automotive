resource "aws_sqs_queue" "sqs_queue" {
  name                      = "${var.project}-sqs-queue"
  delay_seconds             = 0
  max_message_size          = 262144  # Maximum message size in bytes (256 KB)
  message_retention_seconds = 345600  # Message retention period (4 days)
  receive_wait_time_seconds = 0        # Long polling wait time
}

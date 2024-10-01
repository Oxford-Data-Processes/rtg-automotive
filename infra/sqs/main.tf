resource "aws_sqs_queue" "sqs_queue" {
  name                      = "${var.project}-sqs-queue"
  delay_seconds             = 0
  max_message_size          = 262144  # Maximum message size in bytes (256 KB)
  message_retention_seconds = 345600  # Message retention period (4 days)
  receive_wait_time_seconds = 0        # Long polling wait time
}

resource "aws_sns_topic" "stock_notifications" {
  name = "${var.project}-stock-notifications"
}

resource "aws_sns_topic_subscription" "sqs_subscription" {
  topic_arn = aws_sns_topic.stock_notifications.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.sqs_queue.arn

  # Optional: Set the raw message delivery to true if you want the message to be delivered as-is
  raw_message_delivery = true
}

# Data resource for the SQS queue policy
data "aws_iam_policy_document" "sqs_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    actions   = ["SQS:SendMessage"]
    resources = [aws_sqs_queue.sqs_queue.arn]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.stock_notifications.arn]
    }
  }
}

# Policy to allow SNS to send messages to the SQS queue
resource "aws_sqs_queue_policy" "sqs_queue_policy" {
  queue_url = aws_sqs_queue.sqs_queue.id
  policy    = data.aws_iam_policy_document.sqs_policy.json
}

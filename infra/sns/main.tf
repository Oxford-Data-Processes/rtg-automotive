resource "aws_sns_topic" "stock_notifications" {
  name = "${var.project}-stock-notifications"
  display_name = "Stock Notifications"
}

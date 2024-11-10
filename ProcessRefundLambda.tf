# Create the Lambda Function for Processing Refunds
# Create a Lambda function that processes refund requests and updates the Refunds table in DynamoDB.

resource "aws_lambda_function" "refund_processor" {
  function_name = "${var.project_name}-RefundProcessor"
  handler       = "refund_processor.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_execution_role.arn
  filename      = "lambda_files/refund_processor.zip" # Path to the zipped Lambda code

  environment {
    variables = {
      REFUND_TABLE     = aws_dynamodb_table.refunds.name
      AUDIT_TABLE      = aws_dynamodb_table.payment_audit_trail.name
      ELAVON_API_URL   = var.elavon_api_url   # Elavon API URL for refund
      ELAVON_API_TOKEN = var.elavon_api_token # Elavon API Token for authentication
    }
  }
}

# CloudWatch log group for Lambda
resource "aws_cloudwatch_log_group" "refund_processor_logs" {
  name              = "/aws/lambda/${aws_lambda_function.refund_processor.function_name}"
  retention_in_days = 30 # Set retention period for logs (e.g., 30 days)
}


# IAM Role for Lambda execution with necessary permissions
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-RefundProcessorRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  tags = var.tags
}

# Attach a policy to allow access to DynamoDB
resource "aws_iam_role_policy" "lambda_execution_policy" {
  name = "dynamodb-access-policy"
  role = aws_iam_role.lambda_execution_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ]
        Resource = [
          aws_dynamodb_table.refunds.arn,
          aws_dynamodb_table.payment_audit_trail.arn
        ]
      },
    ]
  })
}
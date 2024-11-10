import json
import boto3
import logging
import os
from botocore.exceptions import ClientError
import time
import uuid

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
audit_table = dynamodb.Table(os.environ['AUDIT_TABLE'])
s3_bucket = os.environ['S3_BUCKET']

def lambda_handler(event, context):
    try:
        # Extract refund details from the event (assumes event contains refund data)
        transaction_id = event['transaction_id']
        refund_amount = event['refund_amount']
        currency = event['currency']
        refund_details = event['refund_details']  # Assuming detailed data comes in this field
        
        # Prepare backup data (could be expanded with more fields as needed)
        backup_data = {
            'TransactionID': transaction_id,
            'RefundAmount': refund_amount,
            'Currency': currency,
            'RefundDetails': refund_details,
            'Timestamp': int(time.time())
        }
        
        # Generate a unique backup file name (UUID)
        backup_filename = f"{transaction_id}_refund_backup_{str(uuid.uuid4())}.json"
        
        # Upload backup data to S3
        upload_to_s3(backup_filename, backup_data)

        # Log the backup operation in DynamoDB (Audit Trail)
        log_backup_audit_trail(transaction_id, refund_amount, currency, "SUCCESS", backup_filename)

        logger.info(f"Refund backup processed successfully for transaction ID {transaction_id}")
        return {
            'statusCode': 200,
            'body': json.dumps('Refund backup processed successfully')
        }
    except Exception as e:
        logger.error(f"Error processing refund backup: {str(e)}")
        log_backup_audit_trail(transaction_id, refund_amount, currency, "FAILED", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing refund backup')
        }

def upload_to_s3(filename, data):
    try:
        s3.put_object(
            Bucket=s3_bucket,
            Key=filename,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        logger.info(f"Backup successfully uploaded to S3 with filename {filename}")
    except ClientError as e:
        logger.error(f"Error uploading backup to S3: {e}")
        raise

def log_backup_audit_trail(transaction_id, amount, currency, status, details):
    try:
        audit_table.put_item(
            Item={
                'TransactionID': transaction_id,
                'Action': 'BACKUP',
                'Amount': amount,
                'Currency': currency,
                'Status': status,
                'Details': details,
                'Timestamp': int(time.time())  # Timestamp for audit trail
            }
        )
        logger.info(f"Audit trail logged for backup of transaction {transaction_id}")
    except ClientError as e:
        logger.error(f"Error logging audit trail to DynamoDB: {e}")
        raise

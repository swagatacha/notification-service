import json
import boto3
import csv
import os
import tempfile
from lib.notification_template_processing import process_request

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        print("Event Received: ", json.dumps(event))

        # S3 Bucket & File Info
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']

        print(f"Triggered for Bucket: {bucket_name}, File: {file_key}")

        # Download file from S3 to /tmp in Lambda
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            s3_client.download_fileobj(bucket_name, file_key, tmp_file)
            tmp_file_path = tmp_file.name

        print(f"File downloaded at {tmp_file_path}")

        # Process File
        process_request(tmp_file_path)

        return {
            'statusCode': 200,
            'body': json.dumps('Template Processed Successfully')
        }

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error occurred')
        }

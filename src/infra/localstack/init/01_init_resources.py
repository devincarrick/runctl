import boto3
import os
from typing import Any, Dict

def get_localstack_client(service_name: str) -> Any:
    """Create a boto3 client for LocalStack service.
    
    Args:
        service_name: The AWS service name to connect to
        
    Returns:
        boto3.client: Configured boto3 client
    """
    return boto3.client(
        service_name,
        endpoint_url="http://localhost:4566",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

def init_s3() -> None:
    """Initialize S3 buckets."""
    s3 = get_localstack_client('s3')
    buckets = ['runctl-raw-data', 'runctl-processed-data', 'runctl-summaries']
    
    for bucket in buckets:
        try:
            s3.create_bucket(Bucket=bucket)
            print(f"Created S3 bucket: {bucket}")
        except Exception as e:
            print(f"Error creating bucket {bucket}: {str(e)}")

def init_dynamodb() -> None:
    """Initialize DynamoDB tables."""
    dynamodb = get_localstack_client('dynamodb')
    
    table_name = 'runctl-workouts'
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'workout_id', 'KeyType': 'HASH'},
                {'AttributeName': 'date', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'workout_id', 'AttributeType': 'S'},
                {'AttributeName': 'date', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"Created DynamoDB table: {table_name}")
    except Exception as e:
        print(f"Error creating table {table_name}: {str(e)}")

def main() -> None:
    """Initialize all LocalStack resources."""
    print("Starting LocalStack resource initialization...")
    init_s3()
    init_dynamodb()
    print("LocalStack resource initialization complete.")

if __name__ == "__main__":
    main()
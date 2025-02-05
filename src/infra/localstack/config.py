from typing import Dict, Any, Optional
from dataclasses import dataclass
import boto3
import os
from pathlib import Path

@dataclass
class LocalStackConfig:
    """Configuration for LocalStack services."""
    endpoint_url: str = "http://localhost:4566"
    region_name: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    
    def get_client(self, service_name: str) -> Any:
        """Create a boto3 client for the specified service.
        
        Args:
            service_name: Name of the AWS service (e.g., 's3', 'dynamodb')
            
        Returns:
            boto3.client: Configured boto3 client for the service
        """
        return boto3.client(
            service_name,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )

def setup_localstack_resources() -> None:
    """Initialize required AWS resources in LocalStack environment."""
    config = LocalStackConfig()
    
    # Initialize S3
    s3 = config.get_client('s3')
    _create_s3_buckets(s3)
    
    # Initialize DynamoDB
    dynamodb = config.get_client('dynamodb')
    _create_dynamodb_tables(dynamodb)
    
    return config

def _create_s3_buckets(s3_client: Any) -> None:
    """Create required S3 buckets if they don't exist.
    
    Args:
        s3_client: Boto3 S3 client
    """
    buckets = [
        'runctl-raw-data',
        'runctl-processed-data',
        'runctl-summaries'
    ]
    
    for bucket in buckets:
        try:
            s3_client.create_bucket(Bucket=bucket)
            print(f"Created S3 bucket: {bucket}")
        except s3_client.exceptions.BucketAlreadyExists:
            print(f"Bucket already exists: {bucket}")

def _create_dynamodb_tables(dynamodb_client: Any) -> None:
    """Create required DynamoDB tables if they don't exist.
    
    Args:
        dynamodb_client: Boto3 DynamoDB client
    """
    tables = {
        'runctl-workouts': {
            'AttributeDefinitions': [
                {'AttributeName': 'workout_id', 'AttributeType': 'S'},
                {'AttributeName': 'date', 'AttributeType': 'S'}
            ],
            'KeySchema': [
                {'AttributeName': 'workout_id', 'KeyType': 'HASH'},
                {'AttributeName': 'date', 'KeyType': 'RANGE'}
            ],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
    }
    
    for table_name, table_def in tables.items():
        try:
            dynamodb_client.create_table(
                TableName=table_name,
                **table_def
            )
            print(f"Created DynamoDB table: {table_name}")
        except dynamodb_client.exceptions.ResourceInUseException:
            print(f"Table already exists: {table_name}")
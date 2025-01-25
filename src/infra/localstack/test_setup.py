from typing import Any, Dict, List
import boto3
import json
from datetime import datetime

def get_localstack_client(service_name: str) -> Any:
    """Create a boto3 client for LocalStack service."""
    return boto3.client(
        service_name,
        endpoint_url="http://localhost:4566",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

def test_s3() -> None:
    """Test S3 functionality."""
    print("\nTesting S3...")
    s3 = get_localstack_client('s3')
    
    # List buckets
    buckets = s3.list_buckets()['Buckets']
    print(f"Found {len(buckets)} buckets:")
    for bucket in buckets:
        print(f"- {bucket['Name']}")
    
    # Test upload
    test_bucket = 'runctl-raw-data'
    test_data = b"Test data for S3"
    try:
        s3.put_object(
            Bucket=test_bucket,
            Key='test.txt',
            Body=test_data
        )
        print(f"Successfully uploaded test file to {test_bucket}")
        
        # Verify upload
        response = s3.get_object(Bucket=test_bucket, Key='test.txt')
        content = response['Body'].read()
        assert content == test_data
        print("Successfully verified upload content")
    except Exception as e:
        print(f"Error testing S3: {str(e)}")

def test_dynamodb() -> None:
    """Test DynamoDB functionality."""
    print("\nTesting DynamoDB...")
    dynamodb = get_localstack_client('dynamodb')
    
    # List tables
    tables = dynamodb.list_tables()['TableNames']
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"- {table}")
    
    # Test item operations
    table_name = 'runctl-workouts'
    test_item = {
        'workout_id': {'S': 'test-workout-1'},
        'date': {'S': datetime.now().isoformat()},
        'type': {'S': 'run'},
        'duration': {'N': '3600'},
        'distance': {'N': '10000'}
    }
    
    try:
        # Put item
        dynamodb.put_item(
            TableName=table_name,
            Item=test_item
        )
        print(f"Successfully inserted test item into {table_name}")
        
        # Get item
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                'workout_id': {'S': 'test-workout-1'},
                'date': test_item['date']
            }
        )
        assert 'Item' in response
        print("Successfully verified item retrieval")
    except Exception as e:
        print(f"Error testing DynamoDB: {str(e)}")

def test_health() -> None:
    """Test LocalStack health."""
    print("\nTesting LocalStack health...")
    import requests
    
    try:
        response = requests.get('http://localhost:4566/_localstack/health')
        health_data = response.json()
        print("LocalStack health status:")
        print(json.dumps(health_data, indent=2))
    except Exception as e:
        print(f"Error checking health: {str(e)}")

def main() -> None:
    """Run all tests."""
    print("Starting LocalStack integration tests...")
    
    # Run tests
    test_health()
    test_s3()
    test_dynamodb()
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()
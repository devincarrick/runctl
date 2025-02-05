import pytest
import boto3
from src.infra.localstack.config import LocalStackConfig, setup_localstack_resources

@pytest.fixture(scope="module")
def localstack_setup():
    """Set up LocalStack resources for testing."""
    config = LocalStackConfig()
    setup_localstack_resources()
    return config

def test_localstack_s3_bucket_creation(localstack_setup):
    """Test S3 bucket creation in LocalStack."""
    config = LocalStackConfig()
    s3 = config.get_client('s3')
    
    # List buckets and verify they exist
    response = s3.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response['Buckets']]
    
    assert 'runctl-raw-data' in bucket_names
    assert 'runctl-processed-data' in bucket_names
    assert 'runctl-summaries' in bucket_names

def test_localstack_dynamodb_table_creation(localstack_setup):
    """Test DynamoDB table creation in LocalStack."""
    config = LocalStackConfig()
    dynamodb = config.get_client('dynamodb')
    
    # List tables and verify they exist
    response = dynamodb.list_tables()
    assert 'runctl-workouts' in response['TableNames']
    
    # Verify table structure
    table_desc = dynamodb.describe_table(TableName='runctl-workouts')
    schema = table_desc['Table']['KeySchema']
    
    assert len(schema) == 2
    assert schema[0]['AttributeName'] == 'workout_id'
    assert schema[0]['KeyType'] == 'HASH'
    assert schema[1]['AttributeName'] == 'date'
    assert schema[1]['KeyType'] == 'RANGE'

def test_localstack_s3_bucket_reuse(localstack_setup):
    """Test S3 bucket creation when buckets already exist."""
    config = LocalStackConfig()
    s3 = config.get_client('s3')
    
    # Try to create buckets again
    from src.infra.localstack.config import _create_s3_buckets
    _create_s3_buckets(s3)  # Should handle existing buckets gracefully
    
    # Verify buckets still exist
    response = s3.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response['Buckets']]
    
    assert 'runctl-raw-data' in bucket_names
    assert 'runctl-processed-data' in bucket_names
    assert 'runctl-summaries' in bucket_names

def test_localstack_dynamodb_table_reuse(localstack_setup):
    """Test DynamoDB table creation when tables already exist."""
    config = LocalStackConfig()
    dynamodb = config.get_client('dynamodb')
    
    # Try to create tables again
    from src.infra.localstack.config import _create_dynamodb_tables
    _create_dynamodb_tables(dynamodb)  # Should handle existing tables gracefully
    
    # Verify table still exists and structure is unchanged
    table_desc = dynamodb.describe_table(TableName='runctl-workouts')
    schema = table_desc['Table']['KeySchema']
    
    assert len(schema) == 2
    assert schema[0]['AttributeName'] == 'workout_id'
    assert schema[1]['AttributeName'] == 'date'

def test_localstack_config_custom_values():
    """Test LocalStack configuration with custom values."""
    custom_config = LocalStackConfig(
        endpoint_url="http://localhost:4567",
        region_name="us-west-2",
        aws_access_key_id="custom",
        aws_secret_access_key="custom"
    )
    
    s3 = custom_config.get_client('s3')
    assert s3.meta.endpoint_url == "http://localhost:4567"
    assert s3.meta.region_name == "us-west-2"

def test_localstack_s3_bucket_operations(localstack_setup):
    """Test S3 bucket operations in LocalStack."""
    config = LocalStackConfig()
    s3 = config.get_client('s3')
    
    # Test bucket operations
    bucket_name = 'runctl-raw-data'
    test_key = 'test/file.txt'
    test_content = b'test content'
    
    # Upload a test file
    s3.put_object(Bucket=bucket_name, Key=test_key, Body=test_content)
    
    # Get the file back
    response = s3.get_object(Bucket=bucket_name, Key=test_key)
    assert response['Body'].read() == test_content
    
    # List objects
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix='test/')
    assert len(response['Contents']) == 1
    assert response['Contents'][0]['Key'] == test_key

def test_localstack_dynamodb_table_operations(localstack_setup):
    """Test DynamoDB table operations in LocalStack."""
    config = LocalStackConfig()
    dynamodb = config.get_client('dynamodb')
    
    # Test table operations
    table_name = 'runctl-workouts'
    test_item = {
        'workout_id': {'S': 'test-workout'},
        'date': {'S': '2024-02-05'},
        'distance': {'N': '1000'},
        'power': {'N': '200'}
    }
    
    # Put an item
    dynamodb.put_item(
        TableName=table_name,
        Item=test_item
    )
    
    # Get the item back
    response = dynamodb.get_item(
        TableName=table_name,
        Key={
            'workout_id': {'S': 'test-workout'},
            'date': {'S': '2024-02-05'}
        }
    )
    assert response['Item'] == test_item

def test_localstack_resource_cleanup(localstack_setup):
    """Test resource cleanup in LocalStack."""
    config = LocalStackConfig()
    s3 = config.get_client('s3')
    dynamodb = config.get_client('dynamodb')
    
    # Clean up test data in S3
    bucket_name = 'runctl-raw-data'
    
    # List and delete all test files
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix='test/')
    if 'Contents' in response:
        for obj in response['Contents']:
            s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
    
    # Add and delete a new test file
    test_key = 'test/cleanup.txt'
    s3.put_object(Bucket=bucket_name, Key=test_key, Body=b'test')
    s3.delete_object(Bucket=bucket_name, Key=test_key)
    
    # Verify all test objects are gone
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix='test/')
    assert 'Contents' not in response or len(response['Contents']) == 0
    
    # Clean up test data in DynamoDB
    table_name = 'runctl-workouts'
    test_item = {
        'workout_id': {'S': 'cleanup-test'},
        'date': {'S': '2024-02-05'}
    }
    
    dynamodb.put_item(TableName=table_name, Item=test_item)
    dynamodb.delete_item(
        TableName=table_name,
        Key={
            'workout_id': {'S': 'cleanup-test'},
            'date': {'S': '2024-02-05'}
        }
    )
    
    # Verify item is gone
    response = dynamodb.get_item(
        TableName=table_name,
        Key={
            'workout_id': {'S': 'cleanup-test'},
            'date': {'S': '2024-02-05'}
        }
    )
    assert 'Item' not in response 
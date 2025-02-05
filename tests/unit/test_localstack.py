import pytest
from pytest_mock import MockerFixture
from botocore.exceptions import ClientError
from src.infra.localstack.config import LocalStackConfig, setup_localstack_resources

def test_localstack_config_initialization() -> None:
    """Test LocalStack configuration initialization with default values."""
    config = LocalStackConfig()
    assert config.endpoint_url == "http://localhost:4566"
    assert config.region_name == "us-east-1"
    assert config.aws_access_key_id == "test"
    assert config.aws_secret_access_key == "test"

def test_get_client(mocker: MockerFixture) -> None:
    """Test client creation with correct configuration."""
    mock_boto3 = mocker.patch('src.infra.localstack.config.boto3')
    config = LocalStackConfig()
    
    config.get_client('s3')
    
    mock_boto3.client.assert_called_once_with(
        's3',
        endpoint_url=config.endpoint_url,
        region_name=config.region_name,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key
    )

def test_create_s3_buckets(mocker: MockerFixture) -> None:
    """Test S3 bucket creation."""
    mock_s3 = mocker.Mock()
    mock_s3.exceptions.BucketAlreadyExists = ClientError
    
    # Test successful creation
    from src.infra.localstack.config import _create_s3_buckets
    _create_s3_buckets(mock_s3)
    
    # Verify all required buckets were attempted to be created
    assert mock_s3.create_bucket.call_count == 3
    mock_s3.create_bucket.assert_any_call(Bucket='runctl-raw-data')
    mock_s3.create_bucket.assert_any_call(Bucket='runctl-processed-data')
    mock_s3.create_bucket.assert_any_call(Bucket='runctl-summaries')

def test_create_s3_buckets_already_exists(mocker: MockerFixture) -> None:
    """Test S3 bucket creation when buckets already exist."""
    mock_s3 = mocker.Mock()
    mock_s3.exceptions.BucketAlreadyExists = ClientError
    mock_s3.create_bucket.side_effect = ClientError(
        {'Error': {'Code': 'BucketAlreadyExists', 'Message': 'Bucket already exists'}},
        'CreateBucket'
    )
    
    from src.infra.localstack.config import _create_s3_buckets
    _create_s3_buckets(mock_s3)  # Should not raise exception

def test_create_dynamodb_tables(mocker: MockerFixture) -> None:
    """Test DynamoDB table creation."""
    mock_dynamodb = mocker.Mock()
    mock_dynamodb.exceptions.ResourceInUseException = ClientError
    
    from src.infra.localstack.config import _create_dynamodb_tables
    _create_dynamodb_tables(mock_dynamodb)
    
    # Verify table creation was attempted with correct parameters
    mock_dynamodb.create_table.assert_called_once()
    call_args = mock_dynamodb.create_table.call_args[1]
    assert call_args['TableName'] == 'runctl-workouts'
    assert len(call_args['AttributeDefinitions']) == 2
    assert len(call_args['KeySchema']) == 2

def test_setup_localstack_resources(mocker: MockerFixture) -> None:
    """Test complete LocalStack resource setup."""
    # Mock all service clients
    mock_config = mocker.patch('src.infra.localstack.config.LocalStackConfig')
    mock_config_instance = mock_config.return_value
    
    mock_s3 = mocker.Mock()
    mock_dynamodb = mocker.Mock()
    
    mock_config_instance.get_client.side_effect = [mock_s3, mock_dynamodb]
    
    # Run setup
    config = setup_localstack_resources()
    
    # Verify all services were initialized
    assert mock_config_instance.get_client.call_count == 2
    mock_config_instance.get_client.assert_any_call('s3')
    mock_config_instance.get_client.assert_any_call('dynamodb')
    assert config == mock_config_instance

def test_create_dynamodb_tables_already_exists(mocker: MockerFixture) -> None:
    """Test DynamoDB table creation when tables already exist."""
    mock_dynamodb = mocker.Mock()
    mock_dynamodb.exceptions.ResourceInUseException = ClientError
    mock_dynamodb.create_table.side_effect = ClientError(
        {'Error': {'Code': 'ResourceInUseException', 'Message': 'Table already exists'}},
        'CreateTable'
    )
    
    from src.infra.localstack.config import _create_dynamodb_tables
    _create_dynamodb_tables(mock_dynamodb)  # Should not raise exception 
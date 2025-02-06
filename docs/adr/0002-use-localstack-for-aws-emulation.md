# ADR-0002: Use LocalStack for AWS Emulation

## Status
Accepted

## Context
Development and testing require AWS services, but we need to:
- Avoid AWS costs during development
- Work offline
- Have consistent test environments
- Enable fast feedback loops

## Decision
Use LocalStack with Docker Compose for local AWS service emulation:
- S3 for data storage
- DynamoDB for metadata
- Lambda for serverless functions

Implementation:
```yaml
version: "3.8"
services:
  localstack:
    image: localstack/localstack:2.3.2
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,dynamodb,lambda
      - DEFAULT_REGION=us-east-1
```

## Consequences
### Positive
- No AWS costs during development
- Consistent development environment
- Fast feedback loop
- Reliable testing environment

### Negative
- Some AWS services not perfectly emulated
- Additional Docker overhead
- Learning curve for LocalStack
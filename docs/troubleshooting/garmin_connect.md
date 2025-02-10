# Garmin Connect Integration Troubleshooting Guide

This guide helps you troubleshoot common issues with the Garmin Connect integration using the garth library.

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [Data Retrieval Issues](#data-retrieval-issues)
3. [Rate Limiting](#rate-limiting)
4. [Common Errors](#common-errors)
5. [Best Practices](#best-practices)

## Authentication Issues

### Invalid Credentials

**Symptom**: Authentication fails with "Invalid credentials" error.

**Solution**:

1. Verify your Garmin Connect email and password in `.env`
2. Ensure credentials are correctly formatted
3. Check for special characters in password
4. Try logging in to Garmin Connect website directly

### Token Persistence

**Symptom**: Frequent re-authentication requests.

**Solution**:

1. Check file permissions for token storage
2. Clear stored tokens and re-authenticate
3. Verify token storage path exists
4. Check disk space

### SSO Issues

**Symptom**: SSO authentication loop or timeout.

**Solution**:

1. Clear browser cookies and cache
2. Try with a different browser
3. Check network connectivity
4. Verify Garmin Connect service status

## Data Retrieval Issues

### Missing Data

**Symptom**: Some data points are missing or null.

**Solution**:

1. Verify data exists for the requested date
2. Check device sync status in Garmin Connect
3. Ensure device supports the metric
4. Try retrieving data for a different date

### Invalid Date Range

**Symptom**: Error when requesting data for a date range.

**Solution**:

1. Verify start date is before end date
2. Check date format (YYYY-MM-DD)
3. Ensure dates are within valid range
4. Try smaller date ranges

### Data Format Issues

**Symptom**: Data validation errors or parsing failures.

**Solution**:

1. Check API response format
2. Verify Pydantic model matches response
3. Update models if API changed
4. Check for null values

## Rate Limiting

### API Quota Exceeded

**Symptom**: HTTP 429 "Too Many Requests" error.

**Solution**:

1. Implement exponential backoff
2. Add delays between requests
3. Cache frequently accessed data
4. Monitor request frequency

### Best Practices

1. Implement rate limiting:

   ```python
   from time import sleep

   # Add delay between requests
   sleep(1)  # 1 second delay
   ```

2. Use caching:

   ```python
   # Cache data for an hour
   CACHE_TTL = 3600
   ```

3. Handle rate limits:
   ```python
   if response.status_code == 429:
       retry_after = int(response.headers.get('Retry-After', 60))
       sleep(retry_after)
   ```

## Common Errors

### Network Errors

**Symptom**: Connection timeouts or network failures.

**Solution**:

1. Check internet connection
2. Verify API endpoint is accessible
3. Check firewall settings
4. Implement retry mechanism

Example retry implementation:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_data_with_retry():
    return await client.get_data()
```

### Data Validation Errors

**Symptom**: Pydantic validation errors.

**Solution**:

1. Check response data structure
2. Update model definitions
3. Handle optional fields
4. Add debug logging

Example debug logging:

```python
import logging

logging.debug(f"Raw response: {response.json()}")
```

### Authentication Errors

**Symptom**: Token expired or invalid.

**Solution**:

1. Force token refresh
2. Clear stored tokens
3. Re-authenticate
4. Check token expiration

Example token refresh:

```python
if token_expired:
    await client.refresh_token()
```

## Best Practices

### Error Handling

1. Always use try-except blocks:

```python
try:
    data = await client.get_sleep_data(date)
except Exception as e:
    logging.error(f"Failed to get sleep data: {e}")
    raise
```

2. Add context to errors:

```python
from contextlib import contextmanager

@contextmanager
def error_context(operation):
    try:
        yield
    except Exception as e:
        raise Exception(f"Failed during {operation}: {e}")
```

### Logging

1. Use structured logging:

```python
logging.info("Fetching data", extra={
    "date": date.isoformat(),
    "endpoint": "sleep",
    "user_id": user_id
})
```

2. Include request IDs:

```python
import uuid

request_id = str(uuid.uuid4())
logging.info("API request", extra={"request_id": request_id})
```

### Performance

1. Use async/await properly:

```python
async def get_multiple_days():
    tasks = [client.get_sleep_data(date) for date in dates]
    return await asyncio.gather(*tasks)
```

2. Implement caching:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_data(date):
    return client.get_data(date)
```

## Additional Resources

1. [Garmin Connect API Documentation](https://connect.garmin.com/api-docs)
2. [garth Library Documentation](https://github.com/matin/garth)
3. [Pydantic Documentation](https://docs.pydantic.dev)
4. [aiohttp Documentation](https://docs.aiohttp.org)

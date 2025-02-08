# Garmin Connect API Integration

## Overview

This document outlines the requirements and process for integrating with the Garmin Connect API for accessing sleep and recovery data.

## API Access Requirements

### 1. Developer Program Registration

- Register at: https://www.garmin.com/en-US/forms/health-api/
- Required information:
  - Company/Organization details
  - Project description
  - Intended API usage
  - Expected API call volume
  - Contact information

### 2. API Credentials

After approval, Garmin provides:

- Consumer Key
- Consumer Secret
- Access to official API documentation
- Development support resources

### 3. Environment Configuration

Required environment variables:

```env
GARMIN_CONSUMER_KEY=your_consumer_key
GARMIN_CONSUMER_SECRET=your_consumer_secret
GARMIN_API_BASE_URL=https://api.garmin.com
```

## API Endpoints

### Sleep Data

- Endpoint: `wellness-api/wellness/dailySleepData/{date}`
- Data includes:
  - Sleep stages (deep, light, REM, awake)
  - Sleep score
  - SpO2 measurements
  - Sleep-related stress levels

### Recovery Data

1. Stress Data

   - Endpoint: `wellness-api/wellness/dailyStress/{date}`
   - Provides stress levels and durations

2. Body Battery
   - Endpoint: `wellness-api/wellness/dailyBodyBattery/{date}`
   - Energy levels and recovery metrics

## Implementation Notes

### Authentication

- Uses OAuth2 authentication flow
- Tokens expire after 1 hour by default
- Implement proper token refresh mechanism

### Best Practices

1. Rate Limiting

   - Implement rate limiting in client
   - Cache frequently accessed data
   - Use bulk endpoints when available

2. Error Handling

   - Handle API-specific error codes
   - Implement retry logic for transient failures
   - Log detailed error information

3. Data Validation
   - Use Pydantic models for response validation
   - Handle missing or null values gracefully
   - Validate date ranges and parameters

## Development Workflow

1. Local Development

   - Use environment variables for configuration
   - Run tests with mock responses
   - Validate API responses against models

2. Testing

   - Unit tests with mock responses
   - Integration tests with API (when available)
   - Test rate limiting and error scenarios

3. Production Deployment
   - Secure credential management
   - Monitor API usage and limits
   - Implement proper logging and monitoring

## Migration from Web Scraping

Current implementation uses web scraping, which should be replaced with official API access:

1. Update authentication to use OAuth2
2. Replace endpoint URLs with official API endpoints
3. Update response parsing to match official API format
4. Implement proper rate limiting
5. Add OAuth token management

## Resources

- [Garmin Health API Documentation](https://developer.garmin.com/health-api/overview/)
- [OAuth2 Implementation Guide](https://developer.garmin.com/health-api/oauth2/)
- [API Best Practices](https://developer.garmin.com/health-api/best-practices/)

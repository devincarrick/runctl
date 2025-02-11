# RunCTL Alert Documentation

## Alert Rules

### API Performance Alerts

1. **High API Latency**

   - Condition: Average latency > 2s over 5 minutes
   - Severity: Warning
   - Response:
     1. Check Grafana dashboard for affected endpoints
     2. Verify Garmin API status
     3. Check for rate limiting issues
     4. Review recent code changes
     5. Consider scaling cache if needed

2. **High Error Rate**

   - Condition: Error rate > 5% over 5 minutes
   - Severity: Critical
   - Response:
     1. Check error logs for patterns
     2. Verify Garmin API status
     3. Check authentication status
     4. Review rate limits
     5. Consider circuit breaking if persistent

3. **Low Rate Limit**
   - Condition: Remaining rate limit < 10
   - Severity: Warning
   - Response:
     1. Review current API usage patterns
     2. Check for stuck or looping requests
     3. Consider implementing backoff
     4. Adjust cache TTLs if needed

### Cache Performance Alerts

1. **High Cache Miss Rate**

   - Condition: Miss rate > 20% over 10 minutes
   - Severity: Warning
   - Response:
     1. Review cache key patterns
     2. Check TTL settings
     3. Verify data consistency
     4. Consider prewarming cache
     5. Adjust cache strategy if needed

2. **High Cache Latency**

   - Condition: Average latency > 100ms
   - Severity: Warning
   - Response:
     1. Check Redis server load
     2. Review value sizes
     3. Check network latency
     4. Consider Redis configuration tuning

3. **Large Cache Values**
   - Condition: Average value size > 256KB
   - Severity: Warning
   - Response:
     1. Review data structure
     2. Consider compression settings
     3. Evaluate data normalization
     4. Check for redundant data

### System Health Alerts

1. **Component Down**

   - Condition: Component not responding
   - Severity: Critical
   - Response:
     1. Check component logs
     2. Verify network connectivity
     3. Check resource usage
     4. Attempt restart if necessary
     5. Review recent changes

2. **High Retry Rate**
   - Condition: Multiple retries over 5 minutes
   - Severity: Warning
   - Response:
     1. Check error patterns
     2. Review retry settings
     3. Verify external dependencies
     4. Consider circuit breaking

## Notification Channels

### Email Alerts

- Recipients: Configured via `MONITORING_ALERT_EMAIL_ADDRESSES`
- Frequency: Every 5 minutes
- Used for: All alerts

### Slack Critical Channel

- Channel: #runctl-alerts
- Mentions: @here + oncall users
- Frequency: Every 5 minutes
- Used for: Critical severity alerts

### Slack Warnings Channel

- Channel: #runctl-alerts
- Frequency: Every 15 minutes
- Used for: Warning severity alerts

## Alert Severity Levels

### Critical

- Immediate action required
- Service affecting
- Notify oncall immediately
- Examples:
  - Component down
  - High error rate
  - Authentication failures

### Warning

- Investigation required
- Potential service impact
- Review during business hours
- Examples:
  - High latency
  - Cache performance issues
  - Rate limit warnings

## Response Procedures

1. **Initial Assessment**

   - Check Grafana dashboards
   - Review recent changes
   - Identify affected components
   - Determine impact scope

2. **Investigation**

   - Review relevant logs
   - Check metrics history
   - Analyze error patterns
   - Verify external dependencies

3. **Mitigation**

   - Apply immediate fixes if possible
   - Implement workarounds if needed
   - Document actions taken
   - Update team on progress

4. **Resolution**

   - Verify service recovery
   - Document root cause
   - Plan permanent fixes
   - Update runbooks if needed

5. **Follow-up**
   - Conduct post-mortem if needed
   - Update alert thresholds if necessary
   - Implement preventive measures
   - Review and improve documentation

## Testing Procedures

1. **Alert Rule Testing**

   - Test each alert rule individually
   - Verify notification delivery
   - Check alert resolution
   - Validate silence procedures

2. **Notification Testing**

   - Test each notification channel
   - Verify message formatting
   - Check mention functionality
   - Validate frequency limits

3. **Integration Testing**
   - Test end-to-end alert flow
   - Verify dashboard links
   - Check runbook references
   - Validate escalation paths

"""Tests for alert rules and notification channels."""
import json
import os
from pathlib import Path
from typing import Dict, Any
import pytest
from prometheus_client import Counter, Gauge, Histogram
from pydantic import SecretStr

from src.infra.monitoring.metrics import MetricsRegistry
from src.infra.monitoring.config import MonitoringConfig, HealthCheckConfig, MetricsConfig, AlertThresholds


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON content
    """
    with open(file_path, 'r') as f:
        return json.load(f)


class TestAlertRules:
    """Test suite for alert rules."""
    
    @pytest.fixture
    def alert_rules(self) -> Dict[str, Any]:
        """Load alert rules configuration."""
        rules_path = Path(__file__).parent.parent / 'grafana/alert_rules.json'
        return load_json_file(str(rules_path))
    
    @pytest.fixture
    def metrics(self) -> MetricsRegistry:
        """Create metrics registry for testing."""
        return MetricsRegistry()
    
    def test_alert_rules_structure(self, alert_rules: Dict[str, Any]) -> None:
        """Test alert rules JSON structure."""
        assert 'groups' in alert_rules
        assert len(alert_rules['groups']) > 0
        
        for group in alert_rules['groups']:
            assert 'name' in group
            assert 'rules' in group
            assert len(group['rules']) > 0
            
            for rule in group['rules']:
                assert 'name' in rule
                assert 'condition' in rule
                assert 'for' in rule
                assert 'labels' in rule
                assert 'annotations' in rule
                assert 'severity' in rule['labels']
                assert 'summary' in rule['annotations']
                assert 'description' in rule['annotations']
    
    def test_api_latency_alert(self, metrics: MetricsRegistry) -> None:
        """Test API latency alert condition."""
        # Simulate high latency
        metrics.api_latency.labels(endpoint='sleep').observe(3.0)
        metrics.api_latency.labels(endpoint='sleep').observe(2.5)
        
        # In a real environment, this would trigger the alert
        # Here we just verify the metric exists
        assert metrics.api_latency._metrics
    
    def test_error_rate_alert(self, metrics: MetricsRegistry) -> None:
        """Test error rate alert condition."""
        # Simulate high error rate
        for _ in range(10):
            metrics.api_requests.labels(endpoint='sleep').inc()
        
        metrics.api_errors.labels(
            endpoint='sleep',
            error_type='timeout'
        ).inc()
        
        # Verify metrics exist
        assert metrics.api_requests._metrics
        assert metrics.api_errors._metrics
    
    def test_rate_limit_alert(self, metrics: MetricsRegistry) -> None:
        """Test rate limit alert condition."""
        # Simulate low rate limit
        metrics.rate_limit_remaining.labels(endpoint='sleep').set(5)
        
        # Verify metric exists
        assert metrics.rate_limit_remaining._metrics


class TestNotificationChannels:
    """Test suite for notification channels."""
    
    @pytest.fixture
    def notification_config(self) -> Dict[str, Any]:
        """Load notification configuration."""
        config_path = Path(__file__).parent.parent / 'grafana/notification_channels.json'
        return load_json_file(str(config_path))
    
    @pytest.fixture
    def monitoring_config(self) -> MonitoringConfig:
        """Create monitoring configuration for testing."""
        return MonitoringConfig(
            metrics=MetricsConfig(),
            health_checks=HealthCheckConfig(
                api_key=SecretStr("test_api_key")
            ),
            alert_thresholds=AlertThresholds()
        )
    
    def test_notification_channels_structure(
        self,
        notification_config: Dict[str, Any]
    ) -> None:
        """Test notification channels JSON structure."""
        assert 'notifications' in notification_config
        assert len(notification_config['notifications']) > 0
        
        for channel in notification_config['notifications']:
            assert 'name' in channel
            assert 'type' in channel
            assert 'settings' in channel
            assert 'frequency' in channel
            assert 'conditions' in channel
    
    def test_email_channel_config(
        self,
        notification_config: Dict[str, Any]
    ) -> None:
        """Test email notification channel configuration."""
        email_channel = next(
            (c for c in notification_config['notifications'] if c['type'] == 'email'),
            None
        )
        assert email_channel is not None
        assert 'addresses' in email_channel['settings']
        assert email_channel['frequency'] == '5m'
    
    def test_slack_channels_config(
        self,
        notification_config: Dict[str, Any]
    ) -> None:
        """Test Slack notification channels configuration."""
        slack_channels = [
            c for c in notification_config['notifications']
            if c['type'] == 'slack'
        ]
        assert len(slack_channels) == 2  # Critical and Warning channels
        
        for channel in slack_channels:
            assert 'url' in channel['settings']
            assert 'recipient' in channel['settings']
            assert channel['settings']['recipient'] == '#runctl-alerts'
    
    def test_alert_thresholds_config(
        self,
        monitoring_config: MonitoringConfig
    ) -> None:
        """Test alert threshold configuration."""
        assert monitoring_config.alert_thresholds.error_rate == 0.05
        assert monitoring_config.alert_thresholds.cache_miss_rate == 0.20
        assert monitoring_config.alert_thresholds.api_latency_seconds == 2.0
        assert monitoring_config.alert_thresholds.rate_limit_buffer == 0.80 
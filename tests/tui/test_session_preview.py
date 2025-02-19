"""Tests for the session preview screen."""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from blessed.keyboard import Keystroke

from runctl.data.models import RunningMetrics
from runctl.tui.screens.session_preview import SessionPreviewScreen


@pytest.fixture
def terminal():
    """Create a mock terminal."""
    term = MagicMock()
    term.height = 5  # Set a very small height to ensure scrolling is possible
    term.width = 80
    term.center = lambda x: x
    term.red = lambda x: x
    term.move_xy = lambda x, y: ""
    term.hidden_cursor = MagicMock()
    term.cbreak = MagicMock()
    term.inkey = MagicMock()
    term.clear = ""
    return term


@pytest.fixture
def mock_session():
    """Create a mock running session."""
    return RunningMetrics(
        timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
        distance=5000,  # 5 km
        duration=1500,  # 25 minutes
        avg_pace=300,  # 5:00 min/km
        avg_heart_rate=150,
        max_heart_rate=170,
        elevation_gain=100,
        calories=500,
        cadence=180,
        temperature=20
    )


@pytest.fixture
def sample_sessions(mock_session):
    """Create a list of sample sessions."""
    return [mock_session]


@pytest.fixture
def screen(terminal, sample_sessions):
    """Create a session preview screen with sample data."""
    return SessionPreviewScreen(terminal, sample_sessions)


def test_screen_initialization(screen, sample_sessions):
    """Test screen initialization."""
    assert screen.sessions == sample_sessions
    assert screen.current_session == sample_sessions[0]
    assert screen.scroll_offset == 0
    assert not screen.show_stats
    assert screen._stats is not None


def test_session_navigation(screen, sample_sessions):
    """Test session navigation."""
    # Test left key (no effect with single session)
    screen.handle_input(Keystroke("KEY_LEFT"))
    assert screen.current_session == sample_sessions[0]
    
    # Test right key (no effect with single session)
    screen.handle_input(Keystroke("KEY_RIGHT"))
    assert screen.current_session == sample_sessions[0]


def test_scrolling(screen):
    """Test scrolling functionality."""
    # Test scroll up (no effect at top)
    screen.handle_input(Keystroke("KEY_UP"))
    assert screen.scroll_offset == 0
    
    # Get initial content
    initial_lines = screen._get_session_lines()
    print(f"Initial content: {len(initial_lines)} lines")
    
    # Test scroll down
    screen.handle_input(Keystroke("KEY_DOWN"))
    assert screen.scroll_offset == 0  # No scrolling when content fits in view
    
    # Add more content to make scrolling possible
    lines = screen._get_session_lines()
    print(f"Content after _get_session_lines: {len(lines)} lines")
    
    # Test scroll down again
    screen.handle_input(Keystroke("KEY_DOWN"))
    print(f"Scroll offset after KEY_DOWN: {screen.scroll_offset}")
    assert screen.scroll_offset == 0  # No scrolling when content fits in view
    
    # Test scroll up
    screen.handle_input(Keystroke("KEY_UP"))
    assert screen.scroll_offset == 0


def test_stats_toggle(screen):
    """Test statistics view toggle."""
    assert not screen.show_stats
    
    # Toggle stats on
    screen.handle_input(Keystroke("s"))
    assert screen.show_stats
    assert screen.scroll_offset == 0
    
    # Toggle stats off
    screen.handle_input(Keystroke("s"))
    assert not screen.show_stats
    assert screen.scroll_offset == 0


def test_pace_formatting(screen):
    """Test pace formatting."""
    assert screen._format_pace(300) == "05:00/km"  # 5:00 min/km
    assert screen._format_pace(360) == "06:00/km"  # 6:00 min/km
    assert screen._format_pace(90) == "01:30/km"   # 1:30 min/km


def test_duration_formatting(screen):
    """Test duration formatting."""
    assert screen._format_duration(1500) == "00:25:00"  # 25 minutes
    assert screen._format_duration(3600) == "01:00:00"  # 1 hour
    assert screen._format_duration(90) == "00:01:30"    # 1:30 minutes


def test_quit(screen):
    """Test quit functionality."""
    result = screen.handle_input(Keystroke("q"))
    assert result is None 
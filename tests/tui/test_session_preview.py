"""Tests for the session preview screen."""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from blessed import Terminal
from blessed.keyboard import Keystroke

from runctl.data.models import RunningMetrics, RunningSession
from runctl.tui.screens.session_preview import SessionPreviewScreen


@pytest.fixture
def terminal():
    """Create a mock terminal."""
    term = MagicMock(spec=Terminal)
    term.height = 40
    term.width = 80
    term.clear = '\033[2J'
    term.move = MagicMock(return_value='')
    term.reverse = MagicMock(side_effect=lambda x: x)
    term.bold = MagicMock(side_effect=lambda x: x)
    term.hidden_cursor = MagicMock()
    term.cbreak = MagicMock()
    term.fullscreen = MagicMock()
    return term


@pytest.fixture
def sample_sessions():
    """Create sample running sessions for testing."""
    sessions = []
    
    # Basic session
    basic_metrics = RunningMetrics(
        timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
        distance=5000,
        duration=1500,
        avg_pace=300,
        avg_heart_rate=145,
        max_heart_rate=165,
        cadence=175
    )
    sessions.append(RunningSession(
        id="RUN_1",
        metrics=basic_metrics,
        tags=['easy', 'morning'],
        equipment='Nike Pegasus'
    ))
    
    # Stryd session
    stryd_metrics = RunningMetrics(
        timestamp=datetime(2024, 2, 19, 9, 30, tzinfo=timezone.utc),
        distance=10000,
        duration=3000,
        avg_pace=300,
        power=250,
        form_power=50,
        air_power=10,
        ground_time=220,
        vertical_oscillation=6.5,
        cadence=180,
        elevation=100
    )
    sessions.append(RunningSession(
        id="STRYD_1",
        metrics=stryd_metrics
    ))
    
    return sessions


@pytest.fixture
def screen(terminal, sample_sessions):
    """Create a session preview screen with sample data."""
    return SessionPreviewScreen(terminal, sample_sessions)


def test_screen_initialization(screen, sample_sessions):
    """Test screen initialization."""
    assert screen.current_session_idx == 0
    assert screen.scroll_offset == 0
    assert screen.current_session == sample_sessions[0]


def test_session_navigation(screen):
    """Test navigation between sessions."""
    key_right = MagicMock(spec=Keystroke)
    key_right.name = 'KEY_RIGHT'
    key_left = MagicMock(spec=Keystroke)
    key_left.name = 'KEY_LEFT'
    
    # Move to next session
    assert screen.handle_input(key_right)
    assert screen.current_session_idx == 1
    
    # Move back
    assert screen.handle_input(key_left)
    assert screen.current_session_idx == 0
    
    # Can't move left past start
    assert screen.handle_input(key_left)
    assert screen.current_session_idx == 0
    
    # Move to end and try to go further
    assert screen.handle_input(key_right)
    assert screen.current_session_idx == 1
    assert screen.handle_input(key_right)
    assert screen.current_session_idx == 1


def test_scrolling(screen):
    """Test content scrolling."""
    key_down = MagicMock(spec=Keystroke)
    key_down.name = 'KEY_DOWN'
    key_up = MagicMock(spec=Keystroke)
    key_up.name = 'KEY_UP'
    
    # Scroll down
    assert screen.handle_input(key_down)
    assert screen.scroll_offset == 1
    
    # Scroll up
    assert screen.handle_input(key_up)
    assert screen.scroll_offset == 0
    
    # Can't scroll up past top
    assert screen.handle_input(key_up)
    assert screen.scroll_offset == 0


def test_pace_formatting(screen):
    """Test pace formatting."""
    assert screen._format_pace(300) == "5:00/km"
    assert screen._format_pace(90) == "1:30/km"
    assert screen._format_pace(65) == "1:05/km"


def test_quit(screen):
    """Test quit functionality."""
    key_q = MagicMock(spec=Keystroke)
    key_q.name = 'q'
    assert not screen.handle_input(key_q)  # Should return False to exit 
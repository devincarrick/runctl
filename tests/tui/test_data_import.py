"""Tests for the data import screen."""
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from blessed import Terminal
from blessed.keyboard import Keystroke

from runctl.tui.screens.data_import import DataImportScreen


@pytest.fixture
def terminal():
    """Create a mock terminal."""
    term = MagicMock(spec=Terminal)
    term.height = 24
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
def mock_session():
    """Create a mock running session."""
    metrics = MagicMock()
    metrics.timestamp = datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc)
    metrics.distance = 5000
    metrics.duration = 1500
    metrics.avg_pace = 300
    
    session = MagicMock()
    session.metrics = metrics
    session.id = "TEST_1"
    return session


@pytest.fixture
def screen(terminal):
    """Create a data import screen with a mock terminal."""
    screen = DataImportScreen(terminal)
    # Mock file list for navigation tests
    screen.file_list = [Path(f"file{i}.csv") for i in range(5)]
    return screen


def test_screen_initialization(screen):
    """Test screen initialization."""
    assert screen.format_type == 'standard'
    assert screen.selected_index == 0
    assert screen.scroll_offset == 0
    assert screen.preview_data is None


def test_handle_navigation_keys(screen):
    """Test handling of navigation keys."""
    # Test up/down navigation
    key_down = MagicMock(spec=Keystroke)
    key_down.name = 'KEY_DOWN'
    key_up = MagicMock(spec=Keystroke)
    key_up.name = 'KEY_UP'
    
    # Move down
    assert screen.handle_input(key_down)
    assert screen.selected_index == 1
    
    # Move up
    assert screen.handle_input(key_up)
    assert screen.selected_index == 0
    
    # Can't move up past start
    assert screen.handle_input(key_up)
    assert screen.selected_index == 0
    
    # Move to end
    for _ in range(5):
        screen.handle_input(key_down)
    assert screen.selected_index == 4


def test_format_cycling(screen):
    """Test cycling through file formats."""
    key_f = MagicMock(spec=Keystroke)
    key_f.name = 'f'
    
    assert screen.format_type == 'standard'
    
    # Cycle through formats
    assert screen.handle_input(key_f)
    assert screen.format_type == 'raw_workout'
    
    assert screen.handle_input(key_f)
    assert screen.format_type == 'stryd'
    
    assert screen.handle_input(key_f)
    assert screen.format_type == 'standard'


@patch('runctl.tui.screens.data_import.CSVParser')
def test_file_preview(mock_parser, screen, tmp_path, mock_session):
    """Test file preview functionality."""
    # Create a test file
    test_file = tmp_path / "test.csv"
    test_file.touch()
    
    # Set up mock parser
    mock_parser.return_value.parse.return_value = [mock_session]
    
    # Preview file
    screen.preview_file(test_file)
    
    # Verify parser was called correctly
    mock_parser.assert_called_once_with(test_file, format_type='standard')
    assert len(screen.preview_data) == 1
    assert "Loaded 1 sessions" in screen.status_message


@patch('runctl.tui.screens.data_import.SessionPreviewScreen')
def test_detailed_view(mock_preview_screen, screen, mock_session):
    """Test detailed view functionality."""
    # Try to view details without preview data
    screen.preview_data = None
    key_v = MagicMock(spec=Keystroke)
    key_v.name = 'v'
    assert screen.handle_input(key_v)
    mock_preview_screen.assert_not_called()
    
    # View details with preview data
    screen.preview_data = [mock_session]
    assert screen.handle_input(key_v)
    mock_preview_screen.assert_called_once_with(screen.terminal, screen.preview_data)
    mock_preview_screen.return_value.run.assert_called_once()


def test_quit(screen):
    """Test quit functionality."""
    key_q = MagicMock(spec=Keystroke)
    key_q.name = 'q'
    assert not screen.handle_input(key_q)  # Should return False to exit 
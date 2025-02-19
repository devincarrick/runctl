"""Tests for the main TUI application."""
import signal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from blessed import Terminal
from blessed.keyboard import Keystroke

from runctl.tui import RunCTLApp


@pytest.fixture
def app():
    """Create a RunCTLApp instance for testing."""
    return RunCTLApp()


def test_app_initialization(app):
    """Test that RunCTLApp initializes correctly."""
    assert isinstance(app.term, Terminal)
    assert not app.running
    assert app.layout is not None
    assert app.nav is not None


def test_signal_handling(app):
    """Test signal handler setup and functionality."""
    # Test that signal handlers are set up
    assert signal.getsignal(signal.SIGINT) == app._handle_interrupt
    assert signal.getsignal(signal.SIGTERM) == app._handle_interrupt
    
    # Test interrupt handling
    app.running = True
    app._handle_interrupt(signal.SIGINT, None)
    assert not app.running


@patch('builtins.print')
def test_cleanup(mock_print, app):
    """Test terminal cleanup."""
    app._cleanup()
    
    # Check that terminal state is reset
    assert mock_print.call_count == 2
    mock_print.assert_any_call(app.term.normal_cursor, end='')
    mock_print.assert_any_call(app.term.normal, end='')


@patch('builtins.print')
def test_component_drawing(mock_print, app):
    """Test UI component drawing."""
    # Mock terminal properties
    type(app.term).height = PropertyMock(return_value=24)
    type(app.term).width = PropertyMock(return_value=80)
    
    # Test header drawing
    app._draw_component('header')
    mock_print.assert_called_with(app.term.black_on_white(app.term.center('RunCTL')))
    
    # Test footer drawing
    mock_print.reset_mock()
    app._draw_component('footer')
    mock_print.assert_called_with(app.term.black_on_white(
        app.term.center('Press ESC to exit | ? for help')))


@patch('builtins.print')
def test_ui_drawing(mock_print, app):
    """Test complete UI drawing."""
    # Mock terminal properties
    type(app.term).height = PropertyMock(return_value=24)
    type(app.term).width = PropertyMock(return_value=80)
    
    app._draw_ui()
    assert mock_print.call_count > 0
    mock_print.assert_any_call(app.term.clear)


def test_run_exit_handling(app):
    """Test application exit handling."""
    # Mock terminal properties
    type(app.term).height = PropertyMock(return_value=24)
    type(app.term).width = PropertyMock(return_value=80)
    
    # Mock terminal context managers
    mock_context = MagicMock(__enter__=MagicMock(), __exit__=MagicMock())
    app.term.fullscreen = MagicMock(return_value=mock_context)
    app.term.hidden_cursor = MagicMock(return_value=mock_context)
    app.term.cbreak = MagicMock(return_value=mock_context)
    
    # Mock inkey to simulate normal input
    app.term.inkey = MagicMock(return_value=Keystroke('', '', False))
    
    # Set up a side effect to stop the app after a few iterations
    original_draw_ui = app._draw_ui
    draw_count = 0
    def mock_draw_ui():
        nonlocal draw_count
        draw_count += 1
        if draw_count >= 3:  # Stop after 3 iterations
            app.running = False
        original_draw_ui()
    
    app._draw_ui = mock_draw_ui
    
    # Run the application
    exit_code = app.run()
    
    # Check that the application exited cleanly
    assert exit_code == 0
    assert not app.running
    assert draw_count >= 3  # Ensure we went through the loop


def test_run_error_handling(app):
    """Test error handling during application run."""
    # Mock terminal to raise an exception
    app.term.fullscreen = MagicMock(side_effect=Exception("Test error"))
    
    # Run the application
    exit_code = app.run()
    
    # Check that the error was handled
    assert exit_code == 1
    assert not app.running 
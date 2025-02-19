"""Tests for the TUI navigation system."""
from unittest.mock import MagicMock
import pytest
from blessed import Terminal

from runctl.tui.navigation import MenuItem, NavigationManager


class MockKeystroke:
    """Mock keystroke for testing."""
    def __init__(self, code, is_sequence=False):
        self.code = code
        self.is_sequence = is_sequence

    def __str__(self):
        return self.code


@pytest.fixture
def term():
    """Create a blessed Terminal instance for testing."""
    mock_term = MagicMock(spec=Terminal)
    mock_term.height = 24
    mock_term.width = 80
    return mock_term


@pytest.fixture
def nav(term):
    """Create a NavigationManager instance for testing."""
    return NavigationManager(term)


def test_navigation_initialization(nav):
    """Test that NavigationManager initializes with correct default values."""
    assert nav.current_menu == 'main'
    assert nav.selected_index == 0
    
    # Test main menu items
    menu_items = nav.get_menu_items()
    assert len(menu_items) == 4
    
    # Test menu item properties
    dashboard = menu_items[0]
    assert dashboard.id == 'dashboard'
    assert dashboard.label == 'Dashboard'
    assert dashboard.shortcut == 'd'


def test_navigation_key_handling(nav):
    """Test keyboard navigation handling."""
    # Test arrow key navigation
    assert nav.selected_index == 0
    
    # Create arrow key keystrokes
    down_key = MockKeystroke('\x1b[B', is_sequence=True)
    up_key = MockKeystroke('\x1b[A', is_sequence=True)
    
    # Move down
    nav.handle_input(down_key)
    assert nav.selected_index == 1
    
    # Move down again
    nav.handle_input(down_key)
    assert nav.selected_index == 2
    
    # Move up
    nav.handle_input(up_key)
    assert nav.selected_index == 1
    
    # Test bounds
    # Try to move up past first item
    nav.selected_index = 0
    nav.handle_input(up_key)
    assert nav.selected_index == 0
    
    # Try to move down past last item
    nav.selected_index = 3
    nav.handle_input(down_key)
    assert nav.selected_index == 3


def test_shortcut_handling(nav):
    """Test shortcut key handling."""
    # Test dashboard shortcut
    nav.handle_input(MockKeystroke('d'))
    assert nav.selected_index == 0
    
    # Test activities shortcut
    nav.handle_input(MockKeystroke('a'))
    assert nav.selected_index == 1
    
    # Test analytics shortcut
    nav.handle_input(MockKeystroke('n'))
    assert nav.selected_index == 2
    
    # Test settings shortcut
    nav.handle_input(MockKeystroke('s'))
    assert nav.selected_index == 3
    
    # Test invalid shortcut
    original_index = nav.selected_index
    nav.handle_input(MockKeystroke('x'))
    assert nav.selected_index == original_index


def test_menu_item_handlers():
    """Test MenuItem handler functionality."""
    handler_called = False
    
    def test_handler():
        nonlocal handler_called
        handler_called = True
    
    item = MenuItem('test', 'Test', 't', test_handler)
    
    # Test handler execution
    assert not handler_called
    if item.handler:
        item.handler()
    assert handler_called 
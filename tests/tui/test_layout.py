"""Tests for the TUI layout management system."""
import pytest
from blessed import Terminal

from runctl.tui.layout import LayoutManager, Rect


@pytest.fixture
def term():
    """Create a blessed Terminal instance for testing."""
    return Terminal()


@pytest.fixture
def layout(term):
    """Create a LayoutManager instance for testing."""
    return LayoutManager(term)


def test_rect_contains():
    """Test the Rect.contains method."""
    rect = Rect(x=1, y=2, width=10, height=5)
    
    # Test points inside the rectangle
    assert rect.contains(1, 2)  # Top-left corner
    assert rect.contains(10, 6)  # Bottom-right corner
    assert rect.contains(5, 4)  # Middle point
    
    # Test points outside the rectangle
    assert not rect.contains(0, 2)  # Left of rect
    assert not rect.contains(1, 1)  # Above rect
    assert not rect.contains(11, 6)  # Right of rect
    assert not rect.contains(5, 7)  # Below rect


def test_layout_initialization(layout):
    """Test that LayoutManager initializes with correct default values."""
    assert layout._header_height == 1
    assert layout._footer_height == 1
    assert layout._sidebar_width == 20


def test_layout_component_bounds(layout):
    """Test that component bounds are calculated correctly."""
    # Force terminal size for testing
    layout.term.height = 24
    layout.term.width = 80
    
    # Get component bounds
    header = layout.get_component_bounds('header')
    footer = layout.get_component_bounds('footer')
    sidebar = layout.get_component_bounds('sidebar')
    main = layout.get_component_bounds('main')
    
    # Test header
    assert header.x == 0
    assert header.y == 0
    assert header.width == 80
    assert header.height == 1
    
    # Test footer
    assert footer.x == 0
    assert footer.y == 23  # height - footer_height
    assert footer.width == 80
    assert footer.height == 1
    
    # Test sidebar
    assert sidebar.x == 0
    assert sidebar.y == 1  # header_height
    assert sidebar.width == 20
    assert sidebar.height == 22  # height - header - footer
    
    # Test main area
    assert main.x == 21  # sidebar_width + 1
    assert main.y == 1  # header_height
    assert main.width == 59  # width - sidebar - 1
    assert main.height == 22  # height - header - footer


def test_component_at(layout):
    """Test that component_at returns correct component names."""
    # Force terminal size for testing
    layout.term.height = 24
    layout.term.width = 80
    
    # Test header area
    assert layout.component_at(0, 0) == 'header'
    assert layout.component_at(79, 0) == 'header'
    
    # Test footer area
    assert layout.component_at(0, 23) == 'footer'
    assert layout.component_at(79, 23) == 'footer'
    
    # Test sidebar area
    assert layout.component_at(0, 1) == 'sidebar'
    assert layout.component_at(19, 22) == 'sidebar'
    
    # Test main area
    assert layout.component_at(21, 1) == 'main'
    assert layout.component_at(79, 22) == 'main'
    
    # Test points outside any component
    assert layout.component_at(100, 100) is None 
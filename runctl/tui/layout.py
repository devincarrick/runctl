"""
Layout management for the RunCTL TUI.

This module provides layout management functionality for organizing UI components.
"""
from dataclasses import dataclass
from typing import Optional

from blessed import Terminal


@dataclass
class Rect:
    """Rectangle representing a UI component's bounds."""
    x: int
    y: int
    width: int
    height: int

    def contains(self, x: int, y: int) -> bool:
        """Check if the given coordinates are within this rectangle."""
        return (self.x <= x < self.x + self.width and
                self.y <= y < self.y + self.height)


class LayoutManager:
    """Manages the layout of UI components."""

    def __init__(self, term: Terminal):
        """Initialize the layout manager.
        
        Args:
            term: The blessed Terminal instance
        """
        self.term = term
        self._header_height = 1
        self._footer_height = 1
        self._sidebar_width = 20
        self._update_layout()

    def _update_layout(self) -> None:
        """Update layout calculations based on current terminal size."""
        self.header = Rect(0, 0, self.term.width, self._header_height)
        
        content_y = self._header_height
        content_height = self.term.height - self._header_height - self._footer_height
        
        self.sidebar = Rect(0, content_y, self._sidebar_width, content_height)
        
        main_x = self._sidebar_width + 1
        main_width = self.term.width - main_x
        self.main = Rect(main_x, content_y, main_width, content_height)
        
        self.footer = Rect(0, self.term.height - self._footer_height,
                          self.term.width, self._footer_height)

    def get_component_bounds(self, component: str) -> Rect:
        """Get the bounds for a specific component.
        
        Args:
            component: The component name ('header', 'sidebar', 'main', or 'footer')
            
        Returns:
            Rect: The bounds of the requested component
        """
        self._update_layout()  # Ensure layout is current
        return getattr(self, component)

    def component_at(self, x: int, y: int) -> Optional[str]:
        """Determine which component is at the given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Optional[str]: The component name at the coordinates, or None if none
        """
        for component in ['header', 'sidebar', 'main', 'footer']:
            bounds = getattr(self, component)
            if bounds.contains(x, y):
                return component
        return None 
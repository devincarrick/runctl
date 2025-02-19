"""
Navigation system for the RunCTL TUI.

This module provides navigation and input handling functionality.
"""
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from blessed import Terminal
from blessed.keyboard import Keystroke

__all__ = ["Screen"]


@dataclass
class MenuItem:
    """Represents a menu item in the navigation system."""
    id: str
    label: str
    shortcut: Optional[str] = None
    handler: Optional[Callable[[], None]] = None


class Screen(ABC):
    """Base class for TUI screens."""
    
    def __init__(self, term: Terminal) -> None:
        """Initialize the screen.
        
        Args:
            term: Terminal instance
        """
        self.term = term
    
    @abstractmethod
    def render(self) -> None:
        """Render the screen."""
        pass
    
    @abstractmethod
    def handle_input(self, key: Keystroke) -> Optional["Screen"]:
        """Handle user input.
        
        Args:
            key: The pressed key
            
        Returns:
            The next screen to display, or None to stay on current screen
        """
        pass
    
    def run(self) -> None:
        """Run the screen's main loop."""
        with self.term.hidden_cursor(), self.term.cbreak():
            current_screen = self
            
            while current_screen:
                current_screen.render()
                key = self.term.inkey()
                current_screen = current_screen.handle_input(key)


class NavigationManager:
    """Manages navigation and input handling."""

    def __init__(self, term: Terminal):
        """Initialize the navigation manager.
        
        Args:
            term: The blessed Terminal instance
        """
        self.term = term
        self.current_menu = 'main'
        self.selected_index = 0
        self._setup_menus()

    def _setup_menus(self) -> None:
        """Set up the navigation menus."""
        self.menus: Dict[str, List[MenuItem]] = {
            'main': [
                MenuItem('dashboard', 'Dashboard', 'd'),
                MenuItem('activities', 'Activities', 'a'),
                MenuItem('analytics', 'Analytics', 'n'),
                MenuItem('settings', 'Settings', 's'),
            ]
        }

    def handle_input(self, key: Keystroke) -> bool:
        """Handle keyboard input.
        
        Args:
            key: The keystroke to handle
            
        Returns:
            bool: True if the input was handled, False otherwise
        """
        print(f"Debug: key={key}, code={key.code}, is_sequence={key.is_sequence}", file=sys.stderr)
        
        if not key:
            return False

        menu = self.menus.get(self.current_menu, [])
        if not menu:
            return False
        
        if key.is_sequence:
            if key.code == '\x1b[A':  # Up arrow
                self.selected_index = max(0, self.selected_index - 1)
                print(f"Debug: Moved up to index {self.selected_index}", file=sys.stderr)
                return True
            elif key.code == '\x1b[B':  # Down arrow
                self.selected_index = min(len(menu) - 1, self.selected_index + 1)
                print(f"Debug: Moved down to index {self.selected_index}", file=sys.stderr)
                return True
            elif key.code == '\r':  # Enter
                if 0 <= self.selected_index < len(menu):
                    item = menu[self.selected_index]
                    if item.handler:
                        item.handler()
                    return True
        else:
            # For non-sequence keys, use the key itself as the input
            key_char = str(key).lower()
            # Check shortcuts
            for i, item in enumerate(menu):
                if item.shortcut and key_char == item.shortcut:
                    self.selected_index = i
                    if item.handler:
                        item.handler()
                    return True

        return False

    def get_menu_items(self) -> List[MenuItem]:
        """Get the items for the current menu.
        
        Returns:
            List[MenuItem]: The current menu items
        """
        return self.menus.get(self.current_menu, []) 
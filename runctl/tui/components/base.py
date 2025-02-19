"""Base components for the TUI."""
from abc import ABC, abstractmethod

from blessed import Terminal
from blessed.keyboard import Keystroke


class Screen(ABC):
    """Base class for TUI screens."""

    def __init__(self, terminal: Terminal):
        """Initialize the screen.
        
        Args:
            terminal: Blessed Terminal instance
        """
        self.terminal = terminal

    @abstractmethod
    def handle_input(self, key: Keystroke) -> bool:
        """Handle user input.
        
        Args:
            key: The pressed key
            
        Returns:
            bool: True if the screen should continue, False to exit
        """
        pass

    @abstractmethod
    def render(self) -> None:
        """Render the screen."""
        pass

    def run(self) -> None:
        """Run the screen's main loop."""
        with self.terminal.fullscreen(), self.terminal.cbreak():
            while True:
                self.render()
                key = self.terminal.inkey()
                if not self.handle_input(key):
                    break 
"""
RunCTL TUI Application.

This module implements the main Terminal User Interface for RunCTL using the blessed library.
"""
import signal
import sys
from typing import Optional

from blessed import Terminal

from .layout import LayoutManager
from .navigation import NavigationManager


class RunCTLApp:
    """Main TUI application class for RunCTL."""

    def __init__(self):
        """Initialize the RunCTL TUI application."""
        self.term = Terminal()
        self.running = False
        self.layout = LayoutManager(self.term)
        self.nav = NavigationManager(self.term)
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum: int, frame: Optional[object]) -> None:
        """Handle interrupt signals gracefully."""
        self.running = False

    def _cleanup(self) -> None:
        """Clean up terminal state."""
        print(self.term.normal_cursor, end='')
        print(self.term.normal, end='')

    def _draw_component(self, name: str) -> None:
        """Draw a UI component.
        
        Args:
            name: Component name ('header', 'sidebar', 'main', or 'footer')
        """
        bounds = self.layout.get_component_bounds(name)
        with self.term.location(bounds.x, bounds.y):
            if name == 'header':
                print(self.term.black_on_white(self.term.center('RunCTL')))
            elif name == 'footer':
                print(self.term.black_on_white(
                    self.term.center('Press ESC to exit | ? for help')))
            elif name == 'sidebar':
                print(self.term.bold('Navigation'))
                for i, item in enumerate(self.nav.get_menu_items()):
                    prefix = '└── ' if i == len(self.nav.get_menu_items()) - 1 else '├── '
                    if i == self.nav.selected_index:
                        print(self.term.reverse(f'{prefix}{item.label}'))
                    else:
                        print(f'{prefix}{item.label}')
            elif name == 'main':
                menu_items = self.nav.get_menu_items()
                if 0 <= self.nav.selected_index < len(menu_items):
                    current_item = menu_items[self.nav.selected_index]
                    print(self.term.bold(current_item.label))
                    print()
                    print(f'Selected: {current_item.id}')
                    if current_item.shortcut:
                        print(f'Shortcut: {current_item.shortcut}')

    def _draw_ui(self) -> None:
        """Draw the complete UI."""
        print(self.term.clear)
        for component in ['header', 'sidebar', 'main', 'footer']:
            self._draw_component(component)

    def run(self) -> int:
        """Run the application main loop.
        
        Returns:
            int: Exit code (0 for success, non-zero for errors)
        """
        try:
            with self.term.fullscreen(), self.term.hidden_cursor(), self.term.cbreak():
                self.running = True
                while self.running:
                    self._draw_ui()
                    
                    # Handle input
                    key = self.term.inkey(timeout=0.1)
                    if key.is_sequence and key.name == 'KEY_ESCAPE':
                        self.running = False
                    else:
                        self.nav.handle_input(key)

            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        finally:
            self._cleanup()


def main() -> int:
    """Entry point for the RunCTL TUI application."""
    app = RunCTLApp()
    return app.run()


if __name__ == '__main__':
    sys.exit(main()) 
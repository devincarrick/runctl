"""Data import screen for RunCTL."""
from pathlib import Path
from typing import Callable, Optional

from blessed import Terminal
from blessed.keyboard import Keystroke

from ...data.csv_parser import CSVParser
from ...data.models import RunningSession
from ..components.base import Screen
from .session_preview import SessionPreviewScreen


class DataImportScreen(Screen):
    """Screen for importing running data from CSV files."""

    def __init__(self, terminal: Terminal):
        """Initialize the data import screen.
        
        Args:
            terminal: Blessed Terminal instance
        """
        super().__init__(terminal)
        self.current_path = Path.cwd()
        self.file_list = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.preview_data: Optional[list[RunningSession]] = None
        self.format_type = 'standard'
        self.status_message = ''
        self.refresh_file_list()

    def refresh_file_list(self) -> None:
        """Refresh the list of CSV files in the current directory."""
        try:
            self.file_list = sorted(
                [f for f in self.current_path.glob('*.csv') if f.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
        except Exception as e:
            self.status_message = f"Error reading directory: {e}"
            self.file_list = []

    def handle_input(self, key: Keystroke) -> bool:
        """Handle user input.
        
        Args:
            key: The pressed key
            
        Returns:
            bool: True if the screen should continue, False to exit
        """
        if key.name == 'KEY_UP':
            if self.file_list:
                self.selected_index = max(0, self.selected_index - 1)
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
        elif key.name == 'KEY_DOWN':
            if self.file_list:
                self.selected_index = min(len(self.file_list) - 1, self.selected_index + 1)
                visible_lines = self.terminal.height - 8  # Account for header and footer
                if self.selected_index >= self.scroll_offset + visible_lines:
                    self.scroll_offset = self.selected_index - visible_lines + 1
        elif key.name == 'KEY_LEFT':
            # Go up one directory
            self.current_path = self.current_path.parent
            self.refresh_file_list()
            self.selected_index = 0
            self.scroll_offset = 0
        elif key.name == 'KEY_RIGHT' or key.name == 'KEY_ENTER':
            # Enter directory or select file
            if self.file_list:
                selected_file = self.file_list[self.selected_index]
                if selected_file.is_dir():
                    self.current_path = selected_file
                    self.refresh_file_list()
                    self.selected_index = 0
                    self.scroll_offset = 0
                else:
                    self.preview_file(selected_file)
        elif key.name == 'f':
            # Toggle format type
            formats = ['standard', 'raw_workout', 'stryd']
            current_idx = formats.index(self.format_type)
            self.format_type = formats[(current_idx + 1) % len(formats)]
            if self.preview_data:  # Refresh preview with new format
                self.preview_file(self.file_list[self.selected_index])
        elif key.name == 'v' and self.preview_data:
            # View detailed preview
            preview_screen = SessionPreviewScreen(self.terminal, self.preview_data)
            preview_screen.run()
            self.render()  # Re-render after returning
        elif key.name == 'q':
            return False
        
        return True

    def preview_file(self, file_path: Path) -> None:
        """Preview the selected CSV file.
        
        Args:
            file_path: Path to the CSV file to preview
        """
        try:
            parser = CSVParser(file_path, format_type=self.format_type)
            self.preview_data = list(parser.parse())
            self.status_message = f"Loaded {len(self.preview_data)} sessions from {file_path.name}"
        except Exception as e:
            self.status_message = f"Error loading file: {e}"
            self.preview_data = None

    def render(self) -> None:
        """Render the screen."""
        with self.terminal.hidden_cursor(), self.terminal.cbreak():
            # Clear screen
            print(self.terminal.clear)
            
            # Header
            print(self.terminal.bold('RunCTL - Data Import'))
            print(f"Current format: {self.format_type} (Press 'f' to change)")
            print(f"Current directory: {self.current_path}")
            print('-' * self.terminal.width)
            
            # File list
            visible_lines = self.terminal.height - 8
            end_idx = min(self.scroll_offset + visible_lines, len(self.file_list))
            for idx in range(self.scroll_offset, end_idx):
                file = self.file_list[idx]
                prefix = '→ ' if idx == self.selected_index else '  '
                if idx == self.selected_index:
                    print(self.terminal.reverse(f"{prefix}{file.name}"))
                else:
                    print(f"{prefix}{file.name}")
            
            # Preview section if data is loaded
            if self.preview_data:
                print('-' * self.terminal.width)
                print(self.terminal.bold('Preview:'))
                for idx, session in enumerate(self.preview_data[:3]):  # Show first 3 sessions
                    metrics = session.metrics
                    print(f"Session {idx + 1}:")
                    print(f"  Time: {metrics.timestamp}")
                    print(f"  Distance: {metrics.distance:.1f}m")
                    print(f"  Duration: {metrics.duration:.1f}s")
                    print(f"  Avg Pace: {metrics.avg_pace:.1f}s/km")
                print("\nPress 'v' for detailed view")
            
            # Footer with status and help
            print(self.terminal.move(self.terminal.height - 2, 0))
            print('-' * self.terminal.width)
            if self.status_message:
                print(self.status_message)
            print("↑/↓: Navigate  ←/→: Change dir  f: Change format  v: View details  q: Quit") 
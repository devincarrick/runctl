"""Data import screen for importing running data from CSV files."""
from pathlib import Path
from typing import List, Optional

from blessed import Terminal
from blessed.keyboard import Keystroke

from ...data.csv_parser import CSVParser
from ...data.models import RunningMetrics
from ..navigation import Screen
from .session_preview import SessionPreviewScreen


class DataImportScreen(Screen):
    """Screen for importing running data from CSV files."""
    
    def __init__(self, term: Terminal) -> None:
        """Initialize the data import screen.
        
        Args:
            term: Terminal instance
        """
        super().__init__(term)
        self.terminal = term  # Store terminal reference for consistency
        self.file_path: Optional[Path] = None
        self.status_message: Optional[str] = None  # Renamed from error_message
        self.preview_data: Optional[List[RunningMetrics]] = None  # Initialize as None
        self.format_type: str = 'standard'
        self.selected_index: int = 0
        self.file_list: List[Path] = []
        self.scroll_offset: int = 0
    
    def render(self) -> None:
        """Render the data import screen."""
        self.terminal.clear()
        
        # Print title
        print(self.terminal.center("Import Running Data"))
        print(self.terminal.center("-" * 20))
        print()
        
        # Show current format
        print(self.terminal.center(f"Format: {self.format_type}"))
        print()
        
        # Print current file path or prompt
        if self.file_path:
            print(self.terminal.center(f"Selected file: {self.file_path}"))
            print()
            print(self.terminal.center("Press Enter to import or select a different file"))
        else:
            print(self.terminal.center("Enter the path to your CSV file:"))
            print(self.terminal.center("(Press q to quit, f to change format)"))
        
        # Print status message if any
        if self.status_message:
            print()
            print(self.terminal.center(self.terminal.red(self.status_message)))
    
    def preview_file(self, file_path: Path) -> None:
        """Preview the selected file.
        
        Args:
            file_path: Path to the file to preview
        """
        try:
            parser = CSVParser(file_path, format_type=self.format_type)
            self.preview_data = list(parser.parse())
            self.status_message = f"Loaded {len(self.preview_data)} sessions"
        except Exception as e:
            self.status_message = str(e)
            self.preview_data = None
    
    def handle_input(self, key: Keystroke) -> Optional[Screen]:
        """Handle user input.
        
        Args:
            key: The pressed key
            
        Returns:
            The next screen to display, or None to stay on current screen
        """
        if key.name == "q":
            return None
        
        if key.name == "f":
            # Cycle through formats
            formats = ['standard', 'raw_workout', 'stryd']
            current_idx = formats.index(self.format_type)
            self.format_type = formats[(current_idx + 1) % len(formats)]
            return self
        
        if key.name == "KEY_ENTER" and self.file_path:
            self.preview_file(self.file_path)
            if self.preview_data:
                preview_screen = SessionPreviewScreen(self.terminal, self.preview_data)
                preview_screen.run()
                return self
            return self
        
        if key.name == "KEY_UP":
            self.selected_index = max(0, self.selected_index - 1)
        elif key.name == "KEY_DOWN":
            self.selected_index = min(len(self.file_list) - 1, self.selected_index + 1)
        elif key.name == "v" and self.preview_data:
            preview_screen = SessionPreviewScreen(self.terminal, self.preview_data)
            preview_screen.run()
            return self
        
        # Handle file path input
        if key.is_sequence:
            if key.name == "KEY_BACKSPACE":
                if self.file_path:
                    self.file_path = Path(str(self.file_path)[:-1])
                    if str(self.file_path) == ".":
                        self.file_path = None
        else:
            if self.file_path:
                self.file_path = Path(str(self.file_path) + key)
            else:
                self.file_path = Path(key)
        
        self.status_message = None
        return self 
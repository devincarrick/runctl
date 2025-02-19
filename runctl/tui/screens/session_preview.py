"""Session preview screen for RunCTL."""
from typing import List, Optional

from blessed import Terminal
from blessed.keyboard import Keystroke

from ...data.models import RunningSession
from ..components.base import Screen


class SessionPreviewScreen(Screen):
    """Screen for detailed session preview."""

    def __init__(self, terminal: Terminal, sessions: List[RunningSession]):
        """Initialize the session preview screen.
        
        Args:
            terminal: Blessed Terminal instance
            sessions: List of running sessions to preview
        """
        super().__init__(terminal)
        self.sessions = sessions
        self.current_session_idx = 0
        self.scroll_offset = 0
        self.export_format: Optional[str] = None
        self.status_message = ''

    @property
    def current_session(self) -> RunningSession:
        """Get the currently selected session."""
        return self.sessions[self.current_session_idx]

    def handle_input(self, key: Keystroke) -> bool:
        """Handle user input.
        
        Args:
            key: The pressed key
            
        Returns:
            bool: True if the screen should continue, False to exit
        """
        if key.name == 'KEY_LEFT':
            # Previous session
            if self.current_session_idx > 0:
                self.current_session_idx -= 1
                self.scroll_offset = 0
        elif key.name == 'KEY_RIGHT':
            # Next session
            if self.current_session_idx < len(self.sessions) - 1:
                self.current_session_idx += 1
                self.scroll_offset = 0
        elif key.name == 'KEY_UP':
            # Scroll up
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif key.name == 'KEY_DOWN':
            # Scroll down (limit will be checked in render)
            self.scroll_offset += 1
        elif key.name == 'e':
            # Toggle export format
            formats = [None, 'csv', 'json', 'gpx']
            current_idx = formats.index(self.export_format)
            self.export_format = formats[(current_idx + 1) % len(formats)]
        elif key.name == 'x' and self.export_format:
            # Export session
            self._export_session()
        elif key.name == 'q':
            return False
        
        return True

    def _export_session(self) -> None:
        """Export the current session in the selected format."""
        try:
            session = self.current_session
            filename = f"session_{session.metrics.timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            if self.export_format == 'csv':
                # TODO: Implement CSV export
                self.status_message = "CSV export not yet implemented"
            elif self.export_format == 'json':
                # TODO: Implement JSON export
                self.status_message = "JSON export not yet implemented"
            elif self.export_format == 'gpx':
                # TODO: Implement GPX export
                self.status_message = "GPX export not yet implemented"
            
        except Exception as e:
            self.status_message = f"Export failed: {e}"

    def _format_pace(self, seconds_per_km: float) -> str:
        """Format pace in min:sec/km.
        
        Args:
            seconds_per_km: Pace in seconds per kilometer
            
        Returns:
            str: Formatted pace string
        """
        minutes = int(seconds_per_km // 60)
        seconds = int(seconds_per_km % 60)
        return f"{minutes}:{seconds:02d}/km"

    def render(self) -> None:
        """Render the screen."""
        with self.terminal.hidden_cursor(), self.terminal.cbreak():
            # Clear screen
            print(self.terminal.clear)
            
            # Header
            session = self.current_session
            metrics = session.metrics
            print(self.terminal.bold(f"Session Details ({self.current_session_idx + 1}/{len(self.sessions)})"))
            print(f"ID: {session.id}")
            print('-' * self.terminal.width)
            
            # Basic metrics
            visible_lines = self.terminal.height - 8
            content_lines = []
            
            # Time and distance
            content_lines.extend([
                f"Date: {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Distance: {metrics.distance/1000:.2f} km",
                f"Duration: {metrics.duration/60:.1f} min",
                f"Avg Pace: {self._format_pace(metrics.avg_pace)}",
                ""
            ])
            
            # Heart rate data if available
            if metrics.avg_heart_rate or metrics.max_heart_rate:
                content_lines.extend([
                    "Heart Rate:",
                    f"  Average: {metrics.avg_heart_rate:.0f} bpm" if metrics.avg_heart_rate else "",
                    f"  Maximum: {metrics.max_heart_rate:.0f} bpm" if metrics.max_heart_rate else "",
                    ""
                ])
            
            # Stryd metrics if available
            if metrics.power is not None:
                content_lines.extend([
                    "Power Metrics:",
                    f"  Power: {metrics.power:.1f} W/kg",
                    f"  Form Power: {metrics.form_power:.1f} W/kg" if metrics.form_power else "",
                    f"  Air Power: {metrics.air_power:.1f} W/kg" if metrics.air_power else "",
                    ""
                ])
            
            # Form metrics if available
            if any([metrics.ground_time, metrics.vertical_oscillation, metrics.cadence]):
                content_lines.extend([
                    "Form Metrics:",
                    f"  Ground Time: {metrics.ground_time:.0f} ms" if metrics.ground_time else "",
                    f"  Vertical Oscillation: {metrics.vertical_oscillation:.1f} cm" if metrics.vertical_oscillation else "",
                    f"  Cadence: {metrics.cadence:.0f} spm" if metrics.cadence else "",
                    ""
                ])
            
            # Environmental data if available
            if metrics.elevation or metrics.temperature:
                content_lines.extend([
                    "Environmental:",
                    f"  Elevation: {metrics.elevation:.1f} m" if metrics.elevation else "",
                    f"  Temperature: {metrics.temperature:.1f}°C" if metrics.temperature else "",
                    f"  Weather: {metrics.weather_condition}" if metrics.weather_condition else "",
                    ""
                ])
            
            # Metadata
            if session.tags or session.equipment or session.notes:
                content_lines.extend([
                    "Metadata:",
                    f"  Tags: {', '.join(session.tags)}" if session.tags else "",
                    f"  Equipment: {session.equipment}" if session.equipment else "",
                    f"  Notes: {session.notes}" if session.notes else "",
                    ""
                ])
            
            # Remove empty lines and handle scrolling
            content_lines = [line for line in content_lines if line]
            max_scroll = max(0, len(content_lines) - visible_lines)
            self.scroll_offset = min(self.scroll_offset, max_scroll)
            
            # Display visible content
            for line in content_lines[self.scroll_offset:self.scroll_offset + visible_lines]:
                print(line)
            
            # Footer
            print(self.terminal.move(self.terminal.height - 3, 0))
            print('-' * self.terminal.width)
            if self.status_message:
                print(self.status_message)
            
            # Help text
            export_status = f" | Export format: {self.export_format or 'none'} (e: change, x: export)" if len(self.sessions) > 1 else ""
            navigation = "←/→: Change session | " if len(self.sessions) > 1 else ""
            print(f"{navigation}↑/↓: Scroll{export_status} | q: Back") 
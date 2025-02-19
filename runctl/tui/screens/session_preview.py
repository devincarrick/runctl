"""Session preview screen for RunCTL."""
from typing import List

from blessed import Terminal
from blessed.keyboard import Keystroke

from ...data.models import RunningSession
from ...data.stats import SessionStats, calculate_stats
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
        self.status_message = ''
        self.show_stats = False
        self._stats: SessionStats = calculate_stats(sessions) if sessions else None

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
        elif key.name == 's':
            # Toggle statistics view
            self.show_stats = not self.show_stats
            self.scroll_offset = 0
        elif key.name == 'q':
            return False
        
        return True

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

    def _format_duration(self, seconds: float) -> str:
        """Format duration in HH:MM:SS.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            str: Formatted duration string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def render(self) -> None:
        """Render the screen."""
        with self.terminal.hidden_cursor(), self.terminal.cbreak():
            # Clear screen
            print(self.terminal.clear)
            
            if self.show_stats and self._stats:
                self._render_stats()
            else:
                self._render_session()
            
            # Footer
            print(self.terminal.move(self.terminal.height - 3, 0))
            print('-' * self.terminal.width)
            if self.status_message:
                print(self.status_message)
            
            # Help text
            navigation = "←/→: Change session | " if len(self.sessions) > 1 else ""
            stats_toggle = "s: Toggle stats | "
            print(f"{navigation}↑/↓: Scroll | {stats_toggle}q: Back")

    def _render_stats(self) -> None:
        """Render statistics view."""
        stats = self._stats
        print(self.terminal.bold("Session Statistics"))
        print('-' * self.terminal.width)
        
        content_lines = []
        
        # Distance and time totals
        content_lines.extend([
            "Totals:",
            f"  Distance: {stats.total_distance/1000:.2f} km",
            f"  Duration: {self._format_duration(stats.total_duration)}",
            f"  Average Pace: {self._format_pace(stats.avg_pace)}",
            ""
        ])
        
        # Pace analysis
        content_lines.extend([
            "Pace Analysis:",
            f"  Fastest: {self._format_pace(stats.fastest_pace)}",
            f"  Slowest: {self._format_pace(stats.slowest_pace)}",
            ""
        ])
        
        # Time of day distribution
        total_runs = stats.morning_runs + stats.afternoon_runs + stats.evening_runs
        if total_runs > 0:
            morning_pct = (stats.morning_runs / total_runs) * 100
            afternoon_pct = (stats.afternoon_runs / total_runs) * 100
            evening_pct = (stats.evening_runs / total_runs) * 100
            
            content_lines.extend([
                "Time of Day:",
                f"  Morning (before 12:00): {stats.morning_runs} runs ({morning_pct:.1f}%)",
                f"  Afternoon (12:00-17:00): {stats.afternoon_runs} runs ({afternoon_pct:.1f}%)",
                f"  Evening (after 17:00): {stats.evening_runs} runs ({evening_pct:.1f}%)",
                ""
            ])
        
        # Display content with scrolling
        visible_lines = self.terminal.height - 8
        max_scroll = max(0, len(content_lines) - visible_lines)
        self.scroll_offset = min(self.scroll_offset, max_scroll)
        
        for line in content_lines[self.scroll_offset:self.scroll_offset + visible_lines]:
            print(line)

    def _render_session(self) -> None:
        """Render individual session view."""
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
            f"Duration: {self._format_duration(metrics.duration)}",
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
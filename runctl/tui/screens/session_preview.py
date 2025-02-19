"""Session preview screen for displaying running session details."""
from typing import List, Optional

from blessed import Terminal
from blessed.keyboard import Keystroke

from ...data.models import RunningMetrics
from ...data.stats import calculate_stats
from ..navigation import Screen


class SessionPreviewScreen(Screen):
    """Screen for previewing running session details."""
    
    def __init__(self, term: Terminal, sessions: List[RunningMetrics]) -> None:
        """Initialize the session preview screen.
        
        Args:
            term: Terminal instance
            sessions: List of running sessions to display
        """
        super().__init__(term)
        self.sessions = sessions
        self.current_session = sessions[0] if sessions else None
        self.scroll_offset = 0
        self.show_stats = False
        self._stats = calculate_stats(sessions) if sessions else None
    
    def render(self) -> None:
        """Render the session preview screen."""
        self.term.clear()
        
        if not self.sessions:
            print(self.term.center("No sessions to display"))
            return
        
        if self.show_stats:
            self._render_stats()
        else:
            self._render_session()
        
        # Print help text at the bottom
        print(self.term.move_xy(0, self.term.height - 2))
        print(self.term.center("q: quit | ←/→: prev/next session | ↑/↓: scroll | s: toggle stats"))
    
    def _render_stats(self) -> None:
        """Render session statistics."""
        if not self._stats:
            return
        
        # Format statistics
        stats_lines = [
            "Session Statistics",
            "-----------------",
            f"Total Distance: {self._stats.total_distance / 1000:.2f} km",
            f"Total Duration: {self._format_duration(self._stats.total_duration)}",
            f"Average Pace: {self._format_pace(self._stats.avg_pace)}",
            "",
            "Pace Analysis",
            "-------------",
            f"Fastest Pace: {self._format_pace(self._stats.fastest_pace)}",
            f"Slowest Pace: {self._format_pace(self._stats.slowest_pace)}",
            "",
            "Time of Day Distribution",
            "----------------------",
            f"Morning Runs: {self._stats.morning_runs}",
            f"Afternoon Runs: {self._stats.afternoon_runs}",
            f"Evening Runs: {self._stats.evening_runs}"
        ]
        
        # Center and print each line
        for i, line in enumerate(stats_lines):
            print(self.term.move_xy(0, i))
            print(self.term.center(line))
    
    def _render_session(self) -> None:
        """Render current session details."""
        if not self.current_session:
            return
        
        # Format session details
        session_lines = self._get_session_lines()
        
        # Apply scroll offset and print visible lines
        visible_height = self.term.height - 2
        visible_lines = session_lines[self.scroll_offset:self.scroll_offset + visible_height]
        for i, line in enumerate(visible_lines):
            print(self.term.move_xy(0, i))
            print(self.term.center(line))
    
    def handle_input(self, keystroke: Keystroke) -> Optional[Screen]:
        """Handle input for the session preview screen."""
        session_lines = self._get_session_lines()
        visible_height = self.term.height - 2
        # Calculate max scroll based on the number of lines that can be hidden
        max_scroll = max(0, len(session_lines) - visible_height)
        print(
            f"Lines: {len(session_lines)}, "
            f"Term height: {self.term.height}, "
            f"Visible height: {visible_height}, "
            f"Max scroll: {max_scroll}, "
            f"Current offset: {self.scroll_offset}"
        )

        # Handle quit first
        if str(keystroke) == "q":
            return None

        # Handle scrolling
        if keystroke.name == "KEY_UP":
            self.scroll_offset = max(0, self.scroll_offset - 1)
            print(f"After KEY_UP: scroll_offset = {self.scroll_offset}")
        elif keystroke.name == "KEY_DOWN":
            if len(session_lines) > visible_height:
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
            print(f"After KEY_DOWN: scroll_offset = {self.scroll_offset}")
        
        # Handle stats toggle
        elif str(keystroke) == "s":
            self.show_stats = not self.show_stats
            self.scroll_offset = 0
        
        # Handle navigation only when not in stats view
        elif not self.show_stats:
            # Handle session navigation
            if keystroke.name == "KEY_LEFT" and self.sessions.index(self.current_session) > 0:
                self.current_session = self.sessions[
                    self.sessions.index(self.current_session) - 1
                ]
                self.scroll_offset = 0
            
            elif (
                keystroke.name == "KEY_RIGHT" and 
                self.sessions.index(self.current_session) < len(self.sessions) - 1
            ):
                self.current_session = self.sessions[
                    self.sessions.index(self.current_session) + 1
                ]
                self.scroll_offset = 0
        
        return self
    
    def _get_session_lines(self) -> List[str]:
        """Get the list of lines for the current session.
        
        Returns:
            List of formatted lines
        """
        if not self.current_session:
            return []
        
        # Base lines that are always present
        lines = [
            f"Session {self.sessions.index(self.current_session) + 1} of {len(self.sessions)}",
            "-" * 40,
            f"Date: {self.current_session.timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"Distance: {self.current_session.distance / 1000:.2f} km",
            f"Duration: {self._format_duration(self.current_session.duration)}",
            f"Average Pace: {self._format_pace(self.current_session.avg_pace)}",
            "",
            "Additional Metrics",
            "------------------"
        ]
        
        # Add optional metrics
        if self.current_session.avg_heart_rate is not None:
            lines.append(
                f"Average Heart Rate: {self.current_session.avg_heart_rate:.0f} bpm"
            )
        
        if self.current_session.max_heart_rate is not None:
            lines.append(
                f"Maximum Heart Rate: {self.current_session.max_heart_rate:.0f} bpm"
            )
        
        if self.current_session.elevation_gain is not None:
            lines.append(
                f"Elevation Gain: {self.current_session.elevation_gain:.0f} m"
            )
        
        if self.current_session.calories is not None:
            lines.append(
                f"Calories: {self.current_session.calories:.0f} kcal"
            )
        
        if self.current_session.cadence is not None:
            lines.append(
                f"Average Cadence: {self.current_session.cadence:.0f} spm"
            )
        
        if self.current_session.temperature is not None:
            lines.append(
                f"Temperature: {self.current_session.temperature:.1f}°C"
            )
        
        # Add padding to ensure scrolling is possible
        current_lines = len(lines)
        # Add enough padding to ensure we can scroll at least one line
        padding_needed = max(0, self.term.height + 1)
        lines.extend([""] * padding_needed)
        
        print(f"Base lines: {current_lines}, Padding: {padding_needed}, Total: {len(lines)}")
        
        return lines
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _format_pace(self, pace: float) -> str:
        """Format pace in seconds per kilometer to MM:SS/km.
        
        Args:
            pace: Pace in seconds per kilometer
            
        Returns:
            Formatted pace string
        """
        minutes = int(pace // 60)
        seconds = int(pace % 60)
        return f"{minutes:02d}:{seconds:02d}/km" 
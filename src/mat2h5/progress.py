"""
Colored progress tracking with red, white, and blue sections.
Visual progress display for batch conversion operations.
"""

import sys
import time
from typing import Optional
from pathlib import Path


# ANSI color codes
RED = '\033[91m'
WHITE = '\033[97m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class ColoredProgress:
    """
    Progress tracker with red (beginning), white (middle), blue (end) sections.
    """
    
    def __init__(self, total: int, width: int = 60):
        """
        Initialize progress tracker.
        
        Args:
            total: Total number of items to process
            width: Width of progress bar in characters
        """
        self.total = total
        self.width = width
        self.current = 0
        self.start_time = time.time()
        self.phase = 'beginning'  # beginning, middle, end
        
    def update(self, n: int = 1, message: str = ""):
        """Update progress by n items"""
        self.current = min(self.current + n, self.total)
        self._update_phase()
        self._display(message)
    
    def _update_phase(self):
        """Update which phase we're in based on progress"""
        progress_pct = self.current / self.total if self.total > 0 else 0
        
        if progress_pct < 0.33:
            self.phase = 'beginning'
        elif progress_pct < 0.67:
            self.phase = 'middle'
        else:
            self.phase = 'end'
    
    def _get_color(self) -> str:
        """Get color code for current phase"""
        if self.phase == 'beginning':
            return RED
        elif self.phase == 'middle':
            return WHITE
        else:
            return BLUE
    
    def _display(self, message: str = ""):
        """Display progress bar"""
        if self.total == 0:
            return
        
        progress_pct = self.current / self.total
        filled = int(self.width * progress_pct)
        empty = self.width - filled
        
        # Calculate section widths (33% each)
        section_width = self.width // 3
        red_end = section_width
        white_end = section_width * 2
        
        # Build progress bar with colors
        # Use ASCII characters for Windows compatibility
        bar_parts = []
        filled_char = '#'  # ASCII instead of '█'
        empty_char = '.'   # ASCII instead of '░'
        
        # Red section (beginning)
        if filled > 0:
            red_filled = min(filled, red_end)
            bar_parts.append(f"{RED}{filled_char * red_filled}{RESET}")
            if filled > red_end:
                # White section (middle)
                white_filled = min(filled - red_end, section_width)
                bar_parts.append(f"{WHITE}{filled_char * white_filled}{RESET}")
                if filled > white_end:
                    # Blue section (end)
                    blue_filled = filled - white_end
                    bar_parts.append(f"{BLUE}{filled_char * blue_filled}{RESET}")
        
        # Empty section
        if empty > 0:
            bar_parts.append(f"{RESET}{empty_char * empty}")
        
        bar = ''.join(bar_parts)
        
        # Calculate ETA
        elapsed = time.time() - self.start_time
        if self.current > 0 and elapsed > 0:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            eta_str = f"ETA: {remaining:.0f}s"
        else:
            eta_str = "ETA: --"
        
        # Status line
        status = f"{self.current}/{self.total} ({progress_pct*100:.1f}%)"
        color = self._get_color()
        
        # Print progress (handle encoding errors on Windows)
        try:
            output = f"\r{color}{BOLD}[{self.phase.upper()}]{RESET} {bar} {status} {eta_str}"
            if message:
                output += f" | {message}"
            sys.stdout.write(output)
            sys.stdout.flush()
        except UnicodeEncodeError:
            # Fallback to ASCII-only output
            output = f"\r[{self.phase.upper()}] {bar} {status} {eta_str}"
            if message:
                output += f" | {message}"
            sys.stdout.write(output)
            sys.stdout.flush()
    
    def finish(self, message: str = "Complete!"):
        """Finish progress display"""
        self.current = self.total
        self.phase = 'end'
        self._display(message)
        sys.stdout.write("\n")
        sys.stdout.flush()
    
    def clear(self):
        """Clear progress line"""
        sys.stdout.write("\r" + " " * (self.width + 50) + "\r")
        sys.stdout.flush()


def print_section_header(section: str, color: str, text: str):
    """Print a colored section header"""
    print(f"\n{color}{BOLD}{'='*70}")
    print(f"{section.upper()}: {text}")
    print(f"{'='*70}{RESET}\n")


def print_red_header(text: str):
    """Print red section header"""
    print_section_header("BEGINNING", RED, text)


def print_white_header(text: str):
    """Print white section header"""
    print_section_header("PROCESSING", WHITE, text)


def print_blue_header(text: str):
    """Print blue section header"""
    print_section_header("FINALIZING", BLUE, text)


#!/usr/bin/env python3
"""
Standalone Stock Plot Demo using Textual + Plotext
Reads stock data from CSV files and displays interactive charts with zoom

Features:
- Interactive stock selection from CSV files
- Dual chart comparison (side-by-side)
- Timeline shifting (spacebar/arrow keys to move day-by-day)
- Zoom in/out with synchronized views
- Defaults to 30-day window for engaging initial view
- Handles different data lengths (auto-syncs to shortest dataset)

Usage: python stock_plot_demo.py

Controls:
- Space/]: Move forward 1 day
- [: Move backward 1 day
- +/-: Zoom out/in
- i/o: Zoom in/out (alternative)
- r: Reset to 30-day view
- b: Back to stock selection
- q: Quit
"""

import plotext as plt
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Header, Footer, Button, Label, OptionList
from textual.widgets.option_list import Option
from textual.screen import Screen
from textual.binding import Binding
from rich.text import Text


# ============================================================================
# STOCK DATA LOADER
# ============================================================================

class StockData:
    """Loads and manages stock data from CSV files"""

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.symbol = csv_path.stem.rsplit('_', 1)[0]  # Extract symbol from filename
        self.period = csv_path.stem.rsplit('_', 1)[1]  # Extract period (30, 365, 2000)
        self.df = pd.read_csv(csv_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df = self.df.sort_values('Date')

    def get_data(self, start_idx: int = 0, end_idx: Optional[int] = None) -> Tuple[List[str], List[float]]:
        """Get dates and close prices within the specified range"""
        if end_idx is None:
            end_idx = len(self.df)

        subset = self.df.iloc[start_idx:end_idx]
        # Use Dolphie's exact date format: "d/m/y H:M:S"
        dates = [d.strftime("%d/%m/%y %H:%M:%S") for d in subset['Date']]
        closes = subset['Close'].tolist()

        return dates, closes

    def __len__(self):
        return len(self.df)


# ============================================================================
# STOCK CHART WIDGET (Following Dolphie Pattern)
# ============================================================================

class StockChart(Static):
    """
    A Textual widget for rendering stock charts using plotext.
    Follows the Dolphie pattern for responsive, thread-safe rendering.
    """

    def __init__(self, stock_data: StockData, color: tuple, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stock_data = stock_data
        self.color = color
        self.marker = "braille"

        # Zoom state
        self.start_idx = 0
        self.end_idx = len(stock_data)

    def on_mount(self) -> None:
        """Render the chart when mounted."""
        self.render_chart()

    def on_show(self) -> None:
        """Render the chart when the widget is shown."""
        self.render_chart()

    def on_resize(self) -> None:
        """Re-render the chart when the widget is resized - CRITICAL!"""
        self.render_chart()

    def zoom_in(self) -> None:
        """Zoom in - show fewer data points"""
        total = self.end_idx - self.start_idx
        if total > 20:  # Minimum zoom
            quarter = total // 4
            self.start_idx += quarter
            self.end_idx -= quarter
            self.render_chart()

    def zoom_out(self) -> None:
        """Zoom out - show more data points"""
        total_available = len(self.stock_data)
        quarter = (self.end_idx - self.start_idx) // 4

        self.start_idx = max(0, self.start_idx - quarter)
        self.end_idx = min(total_available, self.end_idx + quarter)
        self.render_chart()

    def reset_zoom(self) -> None:
        """Reset to show all data"""
        self.start_idx = 0
        self.end_idx = len(self.stock_data)
        self.render_chart()

    def shift_forward(self, days: int = 1) -> bool:
        """
        Shift the time window forward by N days.
        Returns True if shifted, False if at the end.
        """
        total_available = len(self.stock_data)
        window_size = self.end_idx - self.start_idx

        # Check if we can shift forward
        if self.end_idx + days <= total_available:
            self.start_idx += days
            self.end_idx += days
            self.render_chart()
            return True
        elif self.end_idx < total_available:
            # Shift to the very end
            self.end_idx = total_available
            self.start_idx = max(0, self.end_idx - window_size)
            self.render_chart()
            return True
        return False

    def shift_backward(self, days: int = 1) -> bool:
        """
        Shift the time window backward by N days.
        Returns True if shifted, False if at the beginning.
        """
        window_size = self.end_idx - self.start_idx

        # Check if we can shift backward
        if self.start_idx - days >= 0:
            self.start_idx -= days
            self.end_idx -= days
            self.render_chart()
            return True
        elif self.start_idx > 0:
            # Shift to the very beginning
            self.start_idx = 0
            self.end_idx = min(len(self.stock_data), window_size)
            self.render_chart()
            return True
        return False

    def render_chart(self) -> None:
        """
        Renders the stock chart using plotext.
        Thread-safe: snapshots data before plotting.
        Following Dolphie's pattern exactly.
        """
        # Lower minimum size requirements
        if self.size.width < 2 or self.size.height < 2:
            self.update(f"Size: {self.size.width}x{self.size.height}")
            return

        try:
            # CRITICAL: Snapshot data to lists for thread-safety (Dolphie pattern)
            dates, closes = self.stock_data.get_data(self.start_idx, self.end_idx)

            if not dates or not closes:
                self.update("")
                return

            # Setup plot (Dolphie _setup_plot pattern)
            plt.clf()
            plt.date_form("d/m/y H:M:S")  # Dolphie uses this exact format
            plt.canvas_color((10, 14, 27))
            plt.axes_color((10, 14, 27))
            plt.ticks_color((133, 159, 213))
            plt.plotsize(self.size.width, self.size.height)

            # Plot the data
            plt.plot(
                dates,
                closes,
                marker=self.marker,
                label=self.stock_data.symbol,
                color=self.color
            )

            # Calculate stats for title
            min_price = min(closes)
            max_price = max(closes)
            current_price = closes[-1]
            price_change = ((current_price - closes[0]) / closes[0]) * 100

            plt.title(
                f"{self.stock_data.symbol} ({self.stock_data.period}d): ₹{current_price:.2f} "
                f"({price_change:+.2f}%) | Range: ₹{min_price:.2f}-₹{max_price:.2f}"
            )

            # Finalize plot with yticks (Dolphie _finalize_plot pattern)
            max_y_value = max_price
            max_y_ticks = 5
            y_tick_interval = (max_y_value / max_y_ticks) if max_y_ticks > 0 else 0

            if y_tick_interval >= 1:
                y_ticks = [i * y_tick_interval for i in range(int(max_y_ticks) + 1)]
            else:
                y_ticks = [float(i) for i in range(int(max_y_value) + 2)]

            y_labels = [f"₹{val:.0f}" for val in y_ticks]
            plt.yticks(y_ticks, y_labels)

            # Convert to ANSI and update widget - THE MAGIC!
            self.update(Text.from_ansi(plt.build()))

        except (OSError, ValueError, Exception) as e:
            # Handle errors gracefully
            self.update(f"Error: {e}")


# ============================================================================
# STOCK SELECTION SCREEN
# ============================================================================

class StockSelectionScreen(Screen):
    """Screen for selecting stocks to display"""

    CSS = """
    StockSelectionScreen {
        align: center middle;
    }

    #selection_container {
        width: 80;
        height: auto;
        max-height: 40;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #title_label {
        width: 100%;
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    #subtitle_label {
        width: 100%;
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    #stock_list {
        height: 20;
        border: solid $primary;
        margin: 1 0;
    }

    #selection_info {
        width: 100%;
        text-align: center;
        color: $warning;
        margin: 1 0;
    }

    #button_container {
        width: 100%;
        align: center middle;
        height: auto;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, cache_dir: Path):
        super().__init__()
        self.cache_dir = cache_dir
        self.csv_files = sorted(cache_dir.glob("*.csv"))
        self.selected_stocks: List[Path] = []

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Container(id="selection_container"):
            yield Label("📊 Stock Selection", id="title_label")
            yield Label("Select exactly 2 stocks to compare", id="subtitle_label")

            # Create option list with all CSV files
            option_list = OptionList(id="stock_list")
            for csv_file in self.csv_files:
                symbol = csv_file.stem.rsplit('_', 1)[0]
                period = csv_file.stem.rsplit('_', 1)[1]
                option_list.add_option(
                    Option(f"{symbol} ({period} days)", id=str(csv_file))
                )
            yield option_list

            yield Label("Selected: 0/2", id="selection_info")

            with Horizontal(id="button_container"):
                yield Button("Start Charts", id="btn_start", variant="success", disabled=True)
                yield Button("Quit [q]", id="btn_quit", variant="error")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection"""
        csv_path = Path(event.option.id)

        if csv_path in self.selected_stocks:
            # Deselect
            self.selected_stocks.remove(csv_path)
        else:
            # Select (max 2)
            if len(self.selected_stocks) < 2:
                self.selected_stocks.append(csv_path)
            else:
                # Replace oldest selection
                self.selected_stocks.pop(0)
                self.selected_stocks.append(csv_path)

        # Update UI
        self.update_selection_info()

    def update_selection_info(self) -> None:
        """Update the selection info label and button state"""
        info_label = self.query_one("#selection_info", Label)
        start_button = self.query_one("#btn_start", Button)

        count = len(self.selected_stocks)
        info_label.update(f"Selected: {count}/2")

        if count == 2:
            stocks_text = " vs ".join([p.stem.rsplit('_', 1)[0] for p in self.selected_stocks])
            info_label.update(f"Selected: {stocks_text}")
            start_button.disabled = False
        else:
            start_button.disabled = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "btn_start" and len(self.selected_stocks) == 2:
            # Start the chart screen with selected stocks
            self.app.push_screen(ChartScreen(self.selected_stocks))
        elif event.button.id == "btn_quit":
            self.app.exit()


# ============================================================================
# CHART SCREEN
# ============================================================================

class ChartScreen(Screen):
    """Screen for displaying stock charts"""

    CSS = """
    ChartScreen {
        background: $surface;
    }

    #main_container {
        height: 100%;
        width: 100%;
    }

    #charts_container {
        height: 1fr;
        width: 100%;
    }

    .chart_panel {
        height: 100%;
        width: 1fr;
        border: solid $primary;
        margin: 1;
    }

    StockChart {
        height: 100%;
        width: 100%;
    }

    #controls {
        height: 5;
        width: 100%;
        background: $surface-darken-1;
        align: center middle;
    }

    #info {
        height: 3;
        width: 100%;
        background: $surface-darken-2;
        content-align: center middle;
    }

    Button {
        margin: 0 1;
    }

    .info_label {
        color: $accent;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("i", "zoom_in", "Zoom In"),
        Binding("o", "zoom_out", "Zoom Out"),
        Binding("minus", "zoom_in", "Zoom In", show=False),
        Binding("plus", "zoom_out", "Zoom Out", show=False),
        Binding("r", "reset", "Reset"),
        Binding("space", "shift_forward", "Day +1"),
        Binding("left_square_bracket", "shift_backward", "Day -1", show=False),
        Binding("right_square_bracket", "shift_forward", "Day +1", show=False),
        Binding("b", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, stock_paths: List[Path]):
        super().__init__()
        self.stock1 = StockData(stock_paths[0])
        self.stock2 = StockData(stock_paths[1])
        self.chart1: Optional[StockChart] = None
        self.chart2: Optional[StockChart] = None

        # Calculate minimum data length for synchronization
        # EDGE CASE HANDLING: When stocks have different data lengths
        # (e.g., one has 30 days, another has 365 days), we default to
        # showing a window equal to the shortest dataset to keep them synchronized
        self.min_data_length = min(len(self.stock1), len(self.stock2))
        self.max_data_length = max(len(self.stock1), len(self.stock2))

        # Default zoom window: 30 days (or less if data is shorter)
        # This creates an engaging initial view that users can zoom out from
        self.default_window_size = min(30, self.min_data_length)

    def compose(self) -> ComposeResult:
        """Create child widgets for the chart screen."""
        yield Header(show_clock=True)

        with Container(id="main_container"):
            # Info bar
            with Container(id="info"):
                info_text = (
                    f"📈 Stock Charts ({self.stock1.symbol}: {len(self.stock1)}d, "
                    f"{self.stock2.symbol}: {len(self.stock2)}d, default: {self.default_window_size}d) | "
                    f"[Space/]]Day +1 [[]Day -1 [+/-]Zoom [r]Reset [b]Back [q]Quit"
                )
                yield Label(info_text, classes="info_label")

            # Charts side by side
            with Horizontal(id="charts_container"):
                with Container(classes="chart_panel"):
                    self.chart1 = StockChart(
                        self.stock1,
                        color=(68, 180, 255),  # Blue
                        id="chart1"
                    )
                    yield self.chart1

                with Container(classes="chart_panel"):
                    self.chart2 = StockChart(
                        self.stock2,
                        color=(84, 239, 174),  # Green
                        id="chart2"
                    )
                    yield self.chart2

            # Control buttons
            with Horizontal(id="controls"):
                yield Button("← Day", id="btn_shift_back", variant="default")
                yield Button("Day → [Space]", id="btn_shift_forward", variant="default")
                yield Button("Zoom In [i]", id="btn_zoom_in", variant="primary")
                yield Button("Zoom Out [o]", id="btn_zoom_out", variant="success")
                yield Button("Reset [r]", id="btn_reset", variant="warning")
                yield Button("Back [b]", id="btn_back", variant="default")
                yield Button("Quit [q]", id="btn_quit", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize charts with default 30-day window (or less if data is shorter)"""
        if self.chart1 and self.chart2:
            # Set both charts to show the default window (30 days or less)
            # This creates an engaging zoomed-in initial view
            self.chart1.start_idx = 0
            self.chart1.end_idx = min(self.default_window_size, len(self.stock1))
            self.chart2.start_idx = 0
            self.chart2.end_idx = min(self.default_window_size, len(self.stock2))

            # Render both charts
            self.chart1.render_chart()
            self.chart2.render_chart()

            # Notify user about the default view
            if self.default_window_size < self.min_data_length:
                self.notify(
                    f"🔍 Showing {self.default_window_size}d window (use [+] or [o] to zoom out and see more data)",
                    severity="information",
                    timeout=4
                )

            # Also notify if data lengths differ
            if len(self.stock1) != len(self.stock2):
                self.notify(
                    f"📊 {self.stock1.symbol}={len(self.stock1)}d, {self.stock2.symbol}={len(self.stock2)}d",
                    severity="information",
                    timeout=3
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id

        if button_id == "btn_shift_forward":
            self.action_shift_forward()
        elif button_id == "btn_shift_back":
            self.action_shift_backward()
        elif button_id == "btn_zoom_in":
            self.action_zoom_in()
        elif button_id == "btn_zoom_out":
            self.action_zoom_out()
        elif button_id == "btn_reset":
            self.action_reset()
        elif button_id == "btn_back":
            self.action_back()
        elif button_id == "btn_quit":
            self.app.exit()

    def action_zoom_in(self) -> None:
        """Zoom in on both charts"""
        if self.chart1 and self.chart2:
            self.chart1.zoom_in()
            self.chart2.zoom_in()

    def action_zoom_out(self) -> None:
        """Zoom out on both charts"""
        if self.chart1 and self.chart2:
            self.chart1.zoom_out()
            self.chart2.zoom_out()

    def action_reset(self) -> None:
        """Reset zoom on both charts to default 30-day window"""
        if self.chart1 and self.chart2:
            # Reset to default window size (30 days or less)
            self.chart1.start_idx = 0
            self.chart1.end_idx = min(self.default_window_size, len(self.stock1))
            self.chart2.start_idx = 0
            self.chart2.end_idx = min(self.default_window_size, len(self.stock2))

            self.chart1.render_chart()
            self.chart2.render_chart()

            self.notify(f"📍 Reset to {self.default_window_size}d window", severity="information")

    def action_shift_forward(self) -> None:
        """Shift timeline forward by 1 day"""
        if self.chart1 and self.chart2:
            shifted1 = self.chart1.shift_forward(1)
            shifted2 = self.chart2.shift_forward(1)
            if not shifted1 and not shifted2:
                self.notify("📍 Reached end of data", severity="information")

    def action_shift_backward(self) -> None:
        """Shift timeline backward by 1 day"""
        if self.chart1 and self.chart2:
            shifted1 = self.chart1.shift_backward(1)
            shifted2 = self.chart2.shift_backward(1)
            if not shifted1 and not shifted2:
                self.notify("📍 Reached beginning of data", severity="information")

    def action_back(self) -> None:
        """Go back to stock selection"""
        self.app.pop_screen()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class StockPlotApp(App):
    """
    Textual app for displaying dual stock charts with zoom controls.
    """

    def __init__(self):
        super().__init__()

        # Find CSV files
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"

        if not self.cache_dir.exists():
            print(f"Error: Cache directory not found: {self.cache_dir}")
            exit(1)

        csv_files = list(self.cache_dir.glob("*.csv"))
        if len(csv_files) < 2:
            print(f"Error: Need at least 2 CSV files in {self.cache_dir}")
            exit(1)

    def on_mount(self) -> None:
        """Show stock selection screen on startup"""
        self.push_screen(StockSelectionScreen(self.cache_dir))


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = StockPlotApp()
    app.run()

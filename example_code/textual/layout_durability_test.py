#!/usr/bin/env python3
"""
Layout Durability Test
Tests progressively complex layouts to identify breaking points.

This experiment adds UI elements incrementally to understand why
the main Artha TUI layout broke while the simple demo works.

Test Levels:
1. Level 1: Simple dual charts (working baseline)
2. Level 2: Add top metrics bar
3. Level 3: Add ticker bar
4. Level 4: Add side panels (portfolio + watchlist + coach)
5. Level 5: Full Artha layout with all widgets
"""

import plotext as plt
import pandas as pd
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Static, Header, Footer, Button, Label,
    Placeholder, DataTable
)
from textual.binding import Binding
from textual.screen import Screen
from rich.text import Text


# ============================================================================
# STOCK CHART (From working demo - DO NOT MODIFY)
# ============================================================================

class StockData:
    """Loads and manages stock data from CSV files"""

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.symbol = csv_path.stem.rsplit('_', 1)[0]
        self.period = csv_path.stem.rsplit('_', 1)[1]
        self.df = pd.read_csv(csv_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df = self.df.sort_values('Date')

    def get_data(self, start_idx: int = 0, end_idx: Optional[int] = None):
        if end_idx is None:
            end_idx = len(self.df)
        subset = self.df.iloc[start_idx:end_idx]
        dates = [d.strftime("%d/%m/%y %H:%M:%S") for d in subset['Date']]
        closes = subset['Close'].tolist()
        return dates, closes

    def __len__(self):
        return len(self.df)


class StockChart(Static):
    """Working stock chart from demo - WITH ANIMATION SUPPORT"""

    def __init__(self, stock_data: StockData, color: tuple, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stock_data = stock_data
        self.color = color
        self.marker = "braille"
        self.start_idx = 0
        self.end_idx = min(30, len(stock_data))
        self.render_count = 0  # Track render calls for debugging

    def on_mount(self) -> None:
        self.render_chart()

    def on_resize(self) -> None:
        self.render_chart()

    def shift_forward(self, days: int = 1) -> bool:
        """Shift timeline forward (for animation)"""
        total_available = len(self.stock_data)
        window_size = self.end_idx - self.start_idx

        if self.end_idx + days <= total_available:
            self.start_idx += days
            self.end_idx += days
            self.render_chart()
            return True
        elif self.end_idx < total_available:
            self.end_idx = total_available
            self.start_idx = max(0, self.end_idx - window_size)
            self.render_chart()
            return True
        return False

    def shift_backward(self, days: int = 1) -> bool:
        """Shift timeline backward"""
        window_size = self.end_idx - self.start_idx

        if self.start_idx - days >= 0:
            self.start_idx -= days
            self.end_idx -= days
            self.render_chart()
            return True
        elif self.start_idx > 0:
            self.start_idx = 0
            self.end_idx = min(len(self.stock_data), window_size)
            self.render_chart()
            return True
        return False

    def reset(self) -> None:
        """Reset to initial view"""
        self.start_idx = 0
        self.end_idx = min(30, len(self.stock_data))
        self.render_chart()

    def render_chart(self) -> None:
        self.render_count += 1

        if self.size.width < 2 or self.size.height < 2:
            self.update(f"Size: {self.size.width}x{self.size.height}")
            return

        try:
            dates, closes = self.stock_data.get_data(self.start_idx, self.end_idx)
            if not dates or not closes:
                self.update("")
                return

            plt.clf()
            plt.date_form("d/m/y H:M:S")
            plt.canvas_color((10, 14, 27))
            plt.axes_color((10, 14, 27))
            plt.ticks_color((133, 159, 213))
            plt.plotsize(self.size.width, self.size.height)

            plt.plot(dates, closes, marker=self.marker,
                    label=self.stock_data.symbol, color=self.color)

            max_price = max(closes)
            y_ticks = [i * (max_price / 5) for i in range(6)]
            y_labels = [f"₹{val:.0f}" for val in y_ticks]
            plt.yticks(y_ticks, y_labels)

            # Show render count and current date range in title
            plt.title(
                f"{self.stock_data.symbol} ({self.stock_data.period}d) | "
                f"Renders: {self.render_count} | Day {self.start_idx}-{self.end_idx}"
            )
            self.update(Text.from_ansi(plt.build()))

        except Exception as e:
            self.update(f"Error: {e}")


# ============================================================================
# BASE TEST SCREEN WITH ANIMATION
# ============================================================================

class BaseTestScreen(Screen):
    """Base screen with animation capabilities"""

    def __init__(self, stock1: StockData, stock2: StockData, level_name: str):
        super().__init__()
        self.stock1 = stock1
        self.stock2 = stock2
        self.level_name = level_name
        self.chart1: Optional[StockChart] = None
        self.chart2: Optional[StockChart] = None
        self.is_playing = False
        self.animation_speed = 0.5  # seconds between frames
        self.animation_timer = None

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("space", "step_forward", "Step +1"),
        Binding("left_square_bracket", "step_backward", "Step -1"),
        Binding("p", "toggle_play", "Play/Pause"),
        Binding("r", "reset_animation", "Reset"),
        Binding("1", "set_speed_slow", "Slow"),
        Binding("2", "set_speed_medium", "Medium"),
        Binding("3", "set_speed_fast", "Fast"),
    ]

    def on_mount(self) -> None:
        """Start with paused animation"""
        self.update_status()

    def update_status(self) -> None:
        """Update status label with animation info"""
        status_label = self.query_one("#animation_status", Label)
        play_status = "▶ PLAYING" if self.is_playing else "⏸ PAUSED"
        speed_name = {0.5: "SLOW", 0.2: "MEDIUM", 0.05: "FAST"}.get(self.animation_speed, "CUSTOM")

        status = (
            f"{self.level_name} | {play_status} | Speed: {speed_name} ({self.animation_speed}s) | "
            f"[Space]Step [P]Play/Pause [1/2/3]Speed [R]Reset [Esc]Back"
        )
        status_label.update(status)

    def action_step_forward(self) -> None:
        """Manually step forward one day"""
        if self.chart1 and self.chart2:
            self.chart1.shift_forward(1)
            self.chart2.shift_forward(1)

    def action_step_backward(self) -> None:
        """Manually step backward one day"""
        if self.chart1 and self.chart2:
            self.chart1.shift_backward(1)
            self.chart2.shift_backward(1)

    def action_toggle_play(self) -> None:
        """Toggle auto-play animation"""
        self.is_playing = not self.is_playing

        if self.is_playing:
            self.start_animation()
        else:
            self.stop_animation()

        self.update_status()

    def action_reset_animation(self) -> None:
        """Reset animation to beginning"""
        self.stop_animation()
        if self.chart1 and self.chart2:
            self.chart1.reset()
            self.chart2.reset()
        self.update_status()

    def action_set_speed_slow(self) -> None:
        """Set slow speed (0.5s between frames)"""
        self.animation_speed = 0.5
        if self.is_playing:
            self.restart_animation()
        self.update_status()

    def action_set_speed_medium(self) -> None:
        """Set medium speed (0.2s between frames)"""
        self.animation_speed = 0.2
        if self.is_playing:
            self.restart_animation()
        self.update_status()

    def action_set_speed_fast(self) -> None:
        """Set FAST speed (0.05s between frames - STRESS TEST!)"""
        self.animation_speed = 0.05
        if self.is_playing:
            self.restart_animation()
        self.update_status()
        self.notify("⚡ FAST MODE - This will stress test the layout!", severity="warning")

    def start_animation(self) -> None:
        """Start auto-play animation"""
        self.animation_timer = self.set_interval(self.animation_speed, self.animation_tick)

    def stop_animation(self) -> None:
        """Stop auto-play animation"""
        if self.animation_timer:
            self.animation_timer.stop()
            self.animation_timer = None

    def restart_animation(self) -> None:
        """Restart animation with new speed"""
        self.stop_animation()
        self.start_animation()

    def animation_tick(self) -> None:
        """Called on each animation frame"""
        if self.chart1 and self.chart2:
            # Try to advance both charts
            can_advance1 = self.chart1.shift_forward(1)
            can_advance2 = self.chart2.shift_forward(1)

            # If either hit the end, loop back to beginning
            if not can_advance1 or not can_advance2:
                if self.chart1:
                    self.chart1.reset()
                if self.chart2:
                    self.chart2.reset()
                self.notify("🔄 Animation loop reset", severity="information", timeout=2)


# ============================================================================
# TEST LEVEL SCREENS
# ============================================================================

class Level1Screen(BaseTestScreen):
    """Level 1: Simple dual charts (BASELINE - WORKING)"""

    CSS = """
    #animation_status {
        dock: top;
        height: 3;
        background: $boost;
        content-align: center middle;
        text-style: bold;
    }

    #charts_container {
        layout: horizontal;
        height: 100%;
    }

    .chart_panel {
        width: 1fr;
        height: 100%;
        border: solid green;
    }

    StockChart {
        width: 100%;
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id="animation_status")

        with Horizontal(id="charts_container"):
            with Container(classes="chart_panel"):
                self.chart1 = StockChart(self.stock1, color=(68, 180, 255), id="chart1")
                yield self.chart1
            with Container(classes="chart_panel"):
                self.chart2 = StockChart(self.stock2, color=(84, 239, 174), id="chart2")
                yield self.chart2

        yield Footer()


class Level2Screen(BaseTestScreen):
    """Level 2: Add top metrics bar"""

    CSS = """
    #animation_status {
        dock: top;
        height: 3;
        background: $boost;
        content-align: center middle;
        text-style: bold;
    }

    #top_metrics {
        height: 5;
        layout: horizontal;
        background: $boost;
        border: solid $primary;
    }

    .metric_card {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        text-align: center;
        border: solid $accent;
    }

    #charts_container {
        layout: horizontal;
        height: 1fr;
    }

    .chart_panel {
        width: 1fr;
        height: 100%;
        border: solid green;
    }

    StockChart {
        width: 100%;
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id="animation_status")

        # Top metrics bar
        with Horizontal(id="top_metrics"):
            yield Placeholder("Day", classes="metric_card", variant="text")
            yield Placeholder("Cash", classes="metric_card", variant="text")
            yield Placeholder("Portfolio", classes="metric_card", variant="text")
            yield Placeholder("P&L", classes="metric_card", variant="text")

        # Charts
        with Horizontal(id="charts_container"):
            with Container(classes="chart_panel"):
                self.chart1 = StockChart(self.stock1, color=(68, 180, 255), id="chart1")
                yield self.chart1
            with Container(classes="chart_panel"):
                self.chart2 = StockChart(self.stock2, color=(84, 239, 174), id="chart2")
                yield self.chart2

        yield Footer()


class Level3Screen(BaseTestScreen):
    """Level 3: Add ticker bar"""

    CSS = """
    #animation_status {
        dock: top;
        height: 3;
        background: $boost;
        content-align: center middle;
        text-style: bold;
    }

    #top_metrics {
        height: 5;
        layout: horizontal;
        background: $boost;
        border: solid $primary;
    }

    .metric_card {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        text-align: center;
        border: solid $accent;
    }

    #ticker_bar {
        height: 3;
        background: $panel-darken-1;
        border: solid $secondary;
    }

    #charts_container {
        layout: horizontal;
        height: 1fr;
    }

    .chart_panel {
        width: 1fr;
        height: 100%;
        border: solid green;
    }

    StockChart {
        width: 100%;
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id="animation_status")

        # Top metrics
        with Horizontal(id="top_metrics"):
            yield Placeholder("Day", classes="metric_card", variant="text")
            yield Placeholder("Cash", classes="metric_card", variant="text")
            yield Placeholder("Portfolio", classes="metric_card", variant="text")
            yield Placeholder("P&L", classes="metric_card", variant="text")

        # Ticker bar
        yield Placeholder("Live Ticker: RELIANCE: ₹1234 | TCS: ₹2962 | INFY: ₹1436",
                         id="ticker_bar", variant="text")

        # Charts
        with Horizontal(id="charts_container"):
            with Container(classes="chart_panel"):
                self.chart1 = StockChart(self.stock1, color=(68, 180, 255), id="chart1")
                yield self.chart1
            with Container(classes="chart_panel"):
                self.chart2 = StockChart(self.stock2, color=(84, 239, 174), id="chart2")
                yield self.chart2

        yield Footer()


class Level4Screen(BaseTestScreen):
    """Level 4: Add side panels (portfolio, watchlist, coach)"""

    CSS = """
    #animation_status {
        dock: top;
        height: 3;
        background: $boost;
        content-align: center middle;
        text-style: bold;
    }

    #top_metrics {
        height: 5;
        layout: horizontal;
        background: $boost;
        border: solid $primary;
    }

    .metric_card {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        text-align: center;
        border: solid $accent;
    }

    #ticker_bar {
        height: 3;
        background: $panel-darken-1;
        border: solid $secondary;
    }

    #main_content {
        layout: horizontal;
        height: 1fr;
    }

    #left_panel {
        width: 2fr;
        layout: vertical;
        height: 100%;
    }

    #right_panel {
        width: 1fr;
        layout: vertical;
        height: 100%;
    }

    #charts_container {
        layout: horizontal;
        height: 20;
    }

    .chart_panel {
        width: 1fr;
        height: 100%;
        border: solid green;
    }

    StockChart {
        width: 100%;
        height: 100%;
    }

    #portfolio_section {
        height: 1fr;
        border: solid $primary;
    }

    #watchlist_section {
        height: 1fr;
        border: solid $accent;
    }

    #coach_section {
        height: 1fr;
        border: solid $secondary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id="animation_status")

        # Top metrics
        with Horizontal(id="top_metrics"):
            yield Placeholder("Day", classes="metric_card", variant="text")
            yield Placeholder("Cash", classes="metric_card", variant="text")
            yield Placeholder("Portfolio", classes="metric_card", variant="text")
            yield Placeholder("P&L", classes="metric_card", variant="text")

        # Ticker bar
        yield Placeholder("Live Ticker", id="ticker_bar", variant="text")

        # Main content with side panels
        with Horizontal(id="main_content"):
            # Left panel: Charts + Portfolio
            with Vertical(id="left_panel"):
                with Horizontal(id="charts_container"):
                    with Container(classes="chart_panel"):
                        self.chart1 = StockChart(self.stock1, color=(68, 180, 255), id="chart1")
                        yield self.chart1
                    with Container(classes="chart_panel"):
                        self.chart2 = StockChart(self.stock2, color=(84, 239, 174), id="chart2")
                        yield self.chart2

                yield Placeholder("Portfolio Positions", id="portfolio_section", variant="size")

            # Right panel: Watchlist + Coach
            with Vertical(id="right_panel"):
                yield Placeholder("Watchlist", id="watchlist_section", variant="size")
                yield Placeholder("AI Coach Insights", id="coach_section", variant="size")

        yield Footer()


class Level5Screen(BaseTestScreen):
    """Level 5: Full Artha-style layout with DataTable"""

    CSS = """
    #animation_status {
        dock: top;
        height: 3;
        background: $boost;
        content-align: center middle;
        text-style: bold;
    }

    #top_metrics {
        height: 5;
        layout: horizontal;
        background: $boost;
        border: solid $primary;
    }

    .metric_card {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        text-align: center;
        border: solid $accent;
    }

    #ticker_bar {
        height: 3;
        background: $panel-darken-1;
        border: solid $secondary;
    }

    #main_content {
        layout: horizontal;
        height: 1fr;
    }

    #left_panel {
        width: 2fr;
        layout: vertical;
        height: 100%;
    }

    #right_panel {
        width: 1fr;
        layout: vertical;
        height: 100%;
    }

    #charts_container {
        layout: horizontal;
        height: 20;
    }

    .chart_panel {
        width: 1fr;
        height: 100%;
        border: solid green;
    }

    StockChart {
        width: 100%;
        height: 100%;
    }

    #portfolio_section {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #watchlist_section {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }

    #coach_section {
        height: 1fr;
        border: solid $secondary;
        padding: 1;
    }

    DataTable {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id="animation_status")

        # Top metrics
        with Horizontal(id="top_metrics"):
            yield Placeholder("Day: 8", classes="metric_card", variant="text")
            yield Placeholder("Cash: ₹643,241", classes="metric_card", variant="text")
            yield Placeholder("Portfolio: ₹996,306", classes="metric_card", variant="text")
            yield Placeholder("P&L: -1.04%", classes="metric_card", variant="text")

        # Ticker
        yield Placeholder("RELIANCE: ₹1384 -0.57% | TCS: ₹2962 -2.16% | INFY: ₹1436 -0.37%",
                         id="ticker_bar", variant="text")

        # Main content
        with Horizontal(id="main_content"):
            # Left panel
            with Vertical(id="left_panel"):
                # Charts
                with Horizontal(id="charts_container"):
                    with Container(classes="chart_panel"):
                        self.chart1 = StockChart(self.stock1, color=(68, 180, 255), id="chart1")
                        yield self.chart1
                    with Container(classes="chart_panel"):
                        self.chart2 = StockChart(self.stock2, color=(84, 239, 174), id="chart2")
                        yield self.chart2

                # Portfolio table
                with Container(id="portfolio_section"):
                    table = DataTable(id="portfolio_table")
                    table.add_columns("Symbol", "Qty", "Avg Price", "Current", "P&L %")
                    table.add_row("INFY", "80", "₹1,482", "₹1,436", "-0.37%")
                    table.add_row("RELIANCE", "90", "₹1,406", "₹1,384", "-0.57%")
                    table.add_row("TCS", "50", "₹3,025", "₹2,962", "-2.16%")
                    yield table

            # Right panel
            with Vertical(id="right_panel"):
                yield Placeholder("Watchlist:\nRELIANCE ₹1384\nTCS ₹2962\nINFY ₹1436",
                                id="watchlist_section", variant="text")
                yield Placeholder("AI Coach Insights:\nWaiting for trades...",
                                id="coach_section", variant="text")

        yield Footer()


# ============================================================================
# MAIN TEST APP
# ============================================================================

class LayoutTestApp(App):
    """Progressive layout durability test"""

    CSS = """
    Screen {
        background: $surface;
    }

    #menu_container {
        align: center middle;
        width: 80;
        height: auto;
        border: thick $primary;
        padding: 2;
    }

    Button {
        margin: 1;
        width: 100%;
    }

    #level_title {
        dock: top;
        height: 3;
        background: $boost;
        content-align: center middle;
        text-style: bold;
    }
    """

    def __init__(self):
        super().__init__()
        cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"
        self.stock1 = StockData(cache_dir / "TCS_365.csv")
        self.stock2 = StockData(cache_dir / "INFY_365.csv")

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="menu_container"):
            yield Label("Layout Durability Test\nSelect Test Level:", id="menu_title")
            yield Button("Level 1: Dual Charts (Baseline)", id="level1", variant="success")
            yield Button("Level 2: + Top Metrics", id="level2", variant="primary")
            yield Button("Level 3: + Ticker Bar", id="level3", variant="primary")
            yield Button("Level 4: + Side Panels", id="level4", variant="warning")
            yield Button("Level 5: Full Layout (Like Artha)", id="level5", variant="error")
            yield Button("Quit", id="quit", variant="default")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "level1":
            self.push_screen(Level1Screen(self.stock1, self.stock2, "Level 1: Dual Charts"))
        elif button_id == "level2":
            self.push_screen(Level2Screen(self.stock1, self.stock2, "Level 2: + Metrics"))
        elif button_id == "level3":
            self.push_screen(Level3Screen(self.stock1, self.stock2, "Level 3: + Ticker"))
        elif button_id == "level4":
            self.push_screen(Level4Screen(self.stock1, self.stock2, "Level 4: + Panels"))
        elif button_id == "level5":
            self.push_screen(Level5Screen(self.stock1, self.stock2, "Level 5: Full Layout"))
        elif button_id == "quit":
            self.exit()


if __name__ == "__main__":
    app = LayoutTestApp()
    app.run()

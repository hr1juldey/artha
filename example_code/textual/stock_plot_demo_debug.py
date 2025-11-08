#!/usr/bin/env python3
"""
Debug version - minimal stock plot demo
"""

import plotext as plt
import pandas as pd
from pathlib import Path
from typing import List, Tuple

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Static, Header, Footer, Label
from textual.binding import Binding
from rich.text import Text


class DebugChart(Static):
    """Debug version of stock chart"""

    def __init__(self, csv_path: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load data
        self.log_messages = []
        try:
            df = pd.read_csv(csv_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').head(100)  # Use first 100 points

            self.dates = [d.strftime("%d/%m/%Y") for d in df['Date']]
            self.closes = df['Close'].tolist()
            self.symbol = csv_path.stem.rsplit('_', 1)[0]

            self.log(f"Loaded {len(self.dates)} data points")
            self.log(f"Date range: {self.dates[0]} to {self.dates[-1]}")
            self.log(f"Price range: {min(self.closes):.2f} to {max(self.closes):.2f}")
        except Exception as e:
            self.log(f"ERROR loading data: {e}")
            self.dates = []
            self.closes = []
            self.symbol = "ERROR"

    def log(self, msg: str):
        """Log a message"""
        self.log_messages.append(msg)
        print(f"[DebugChart] {msg}")

    def on_mount(self) -> None:
        """When mounted, render"""
        self.log("on_mount called")
        self.render_chart()

    def on_resize(self) -> None:
        """Re-render on resize"""
        self.log(f"on_resize called - size: {self.size.width}x{self.size.height}")
        self.render_chart()

    def render_chart(self) -> None:
        """Render the chart"""
        self.log(f"render_chart called - size: {self.size.width}x{self.size.height}")

        if not self.dates or not self.closes:
            self.log("No data to render")
            self.update("No data available")
            return

        if self.size.width < 10 or self.size.height < 5:
            self.log("Widget too small")
            self.update("Widget too small")
            return

        try:
            self.log("Setting up plotext...")

            # Clear and setup
            plt.clf()
            plt.date_form("d/m/Y")
            plt.plotsize(self.size.width, self.size.height)

            # Colors
            plt.canvas_color((10, 14, 27))
            plt.axes_color((10, 14, 27))
            plt.ticks_color((133, 159, 213))

            self.log(f"Plotting {len(self.dates)} points...")

            # Plot
            plt.plot(
                self.dates,
                self.closes,
                marker="braille",
                label=self.symbol,
                color=(68, 180, 255)
            )

            plt.title(f"{self.symbol} - Debug Chart")

            # Build
            self.log("Building plot...")
            output = plt.build()
            self.log(f"Plot output length: {len(output)}")

            if not output:
                self.log("ERROR: plotext.build() returned empty string!")
                self.update("ERROR: Empty plot output")
                return

            # Convert to Rich Text
            self.log("Converting to Rich Text...")
            rich_text = Text.from_ansi(output)
            self.log(f"Rich text length: {len(rich_text.plain)}")

            # Update widget
            self.log("Updating widget...")
            self.update(rich_text)
            self.log("Update complete!")

        except Exception as e:
            import traceback
            error_msg = f"ERROR in render_chart: {e}\n{traceback.format_exc()}"
            self.log(error_msg)
            self.update(f"Render error: {e}")


class DebugApp(App):
    """Debug app"""

    CSS = """
    #chart_container {
        height: 100%;
        width: 100%;
        border: solid green;
        padding: 1;
    }

    #info {
        height: 5;
        width: 100%;
        background: $surface-darken-2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        yield Label("Debug Chart Test - Check console for logs", id="info")

        cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"
        csv_path = cache_dir / "ICICIBANK_365.csv"

        with Container(id="chart_container"):
            yield DebugChart(csv_path, id="debug_chart")

        yield Footer()


if __name__ == "__main__":
    app = DebugApp()
    app.run()

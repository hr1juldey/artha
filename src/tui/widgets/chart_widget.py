"""Portfolio Chart Widget using plotext for terminal visualization"""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive
import plotext as plt
from src.models import GameState
from typing import List, Dict


class PortfolioChartWidget(Static):
    """Live updating portfolio chart with multiple series and zoom controls"""

    portfolio_history: reactive[List[Dict]] = reactive([])

    def __init__(self, portfolio_history: List[Dict] = None, title: str = "Portfolio", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chart_title = title
        self.portfolio_history = portfolio_history or []
        # Zoom state
        self.start_idx = 0
        self.end_idx = None  # None means show all data

    def watch_portfolio_history(self, new_history: List[Dict]) -> None:
        """React to portfolio history changes"""
        self.refresh_chart()

    def on_mount(self) -> None:
        """Initialize the chart when widget is mounted"""
        self.refresh_chart()

    def on_resize(self) -> None:
        """Handle widget resize events"""
        self.refresh_chart()

    def zoom_in(self) -> bool:
        """Zoom in - show fewer days (more detail)"""
        if not self.portfolio_history:
            return False

        total = len(self.portfolio_history)
        current_window = (self.end_idx if self.end_idx else total) - self.start_idx

        if current_window <= 5:  # Minimum zoom: 5 days
            return False

        # Reduce window by 25%
        quarter = current_window // 4
        self.start_idx += quarter
        if self.end_idx:
            self.end_idx -= quarter
        else:
            self.end_idx = total - quarter

        self.refresh_chart()
        return True

    def zoom_out(self) -> bool:
        """Zoom out - show more days (less detail)"""
        if not self.portfolio_history:
            return False

        total = len(self.portfolio_history)
        current_window = (self.end_idx if self.end_idx else total) - self.start_idx

        # Expand window by 25%
        quarter = max(1, current_window // 4)

        new_start = max(0, self.start_idx - quarter)
        new_end = min(total, (self.end_idx if self.end_idx else total) + quarter)

        # If we've reached full view, set end_idx to None
        if new_start == 0 and new_end == total:
            self.start_idx = 0
            self.end_idx = None
        else:
            self.start_idx = new_start
            self.end_idx = new_end

        self.refresh_chart()
        return True

    def reset_zoom(self) -> None:
        """Reset to show all data"""
        self.start_idx = 0
        self.end_idx = None
        self.refresh_chart()

    def refresh_chart(self) -> None:
        """Render chart with multiple series - Following Dolphie pattern"""
        # Critical: Check size before rendering
        if self.size.width < 2 or self.size.height < 2:
            self.update(f"Size: {self.size.width}x{self.size.height}")
            return

        if not self.portfolio_history:
            self.update("📈 No data yet. Make trades to see your portfolio grow!")
            return

        try:
            # Setup plot (Dolphie _setup_plot pattern)
            plt.clf()  # Clear everything

            # Set canvas colors (Dolphie pattern)
            plt.canvas_color((10, 14, 27))
            plt.axes_color((10, 14, 27))
            plt.ticks_color((133, 159, 213))

            # Set plot size
            plt.plotsize(self.size.width, self.size.height)

            # Apply zoom window
            end_idx = self.end_idx if self.end_idx is not None else len(self.portfolio_history)
            history_window = self.portfolio_history[self.start_idx:end_idx]

            if not history_window:
                self.update("No data in current zoom window")
                return

            # Extract data (snapshot to lists for thread-safety)
            days = [entry['day'] for entry in history_window]
            total_values = [entry['total_value'] for entry in history_window]

            # Add stocks and cash values if available
            if 'positions_value' in history_window[0]:
                positions_values = [entry['positions_value'] for entry in history_window]
                cash_values = [entry['cash'] for entry in history_window]

                # Plot multiple series
                plt.plot(days, total_values, label="Total", color=(84, 239, 174), marker="braille")
                plt.plot(days, positions_values, label="Stocks", color=(68, 180, 255), marker="braille")
                plt.plot(days, cash_values, label="Cash", color=(255, 212, 59), marker="braille")
            else:
                # Fallback to single series
                plt.plot(days, total_values, label="Portfolio", color=(84, 239, 174), marker="braille")

            # Add benchmark (initial capital as horizontal line)
            if self.portfolio_history:
                initial_value = self.portfolio_history[0]['total_value']
                plt.hline(initial_value, color=(200, 200, 200))

            # Finalize plot with title showing zoom info
            zoom_info = f"Days {days[0]}-{days[-1]}" if len(days) < len(self.portfolio_history) else f"Day {days[-1]}"
            plt.title(f"{self.chart_title} - {zoom_info}")
            plt.xlabel("Day")
            plt.ylabel("Value (₹)")

            # CRITICAL: Build and convert to Rich Text (this is what makes it work!)
            from rich.text import Text
            chart_output = plt.build()

            if not chart_output:
                self.update("ERROR: Empty plot output")
                return

            self.update(Text.from_ansi(chart_output))

        except Exception as e:
            # Handle errors gracefully
            self.update(f"Chart Error: {e}")

    def update_portfolio_history(self, portfolio_history: List[Dict]) -> None:
        """Update the widget with new portfolio history"""
        # Create a new list to trigger reactive watcher
        # (Textual reactive only triggers on reference change, not content change)
        self.portfolio_history = list(portfolio_history)
        # Also explicitly refresh to ensure update
        self.refresh_chart()


class StockMiniChart(Static):
    """Mini sparkline chart for individual stocks"""

    def __init__(self, symbol: str, price_history: List[float], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbol = symbol
        self.price_history = price_history

    def on_mount(self) -> None:
        """Initialize the chart when widget is mounted"""
        self.render_mini_chart()

    def on_resize(self) -> None:
        """Handle widget resize events"""
        self.render_mini_chart()

    def render_mini_chart(self) -> None:
        """Render a compact sparkline - Following Dolphie pattern"""
        # Check size
        if self.size.width < 2 or self.size.height < 2:
            self.update(f"{self.symbol}: Size: {self.size.width}x{self.size.height}")
            return

        if len(self.price_history) < 2:
            self.update(f"{self.symbol}: No history")
            return

        try:
            # Setup plot (Dolphie pattern)
            plt.clf()

            # Set canvas colors
            plt.canvas_color((10, 14, 27))
            plt.axes_color((10, 14, 27))
            plt.ticks_color((133, 159, 213))

            # Create mini sparkline
            plt.plotsize(self.size.width, self.size.height)
            days = list(range(len(self.price_history)))

            # Determine color based on price change
            price_change = self.price_history[-1] - self.price_history[0]
            plot_color = (84, 239, 174) if price_change >= 0 else (255, 85, 85)

            plt.plot(days, self.price_history, marker="braille", color=plot_color)

            # No labels for mini chart
            plt.xticks([])
            plt.yticks([])

            # CRITICAL: Build and convert to Rich Text
            from rich.text import Text
            chart_output = plt.build()

            if not chart_output:
                self.update(f"{self.symbol}: Empty")
                return

            # Add symbol and price change
            pct_change = (price_change / self.price_history[0]) * 100 if self.price_history[0] != 0 else 0
            color = "green" if price_change >= 0 else "red"

            output = f"[bold]{self.symbol}[/] [{color}]{pct_change:+.2f}%[/]\n"
            self.update(output + Text.from_ansi(chart_output))

        except Exception as e:
            self.update(f"{self.symbol}: Error: {e}")


class EnhancedPortfolioGrid(Static):
    """Enhanced portfolio display using dataframe-textual principles"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.positions = []
        
    def update_portfolio(self, portfolio) -> None:
        """Update the portfolio grid with new data"""
        # Since we can't directly use dataframe-textual without installing it,
        # we'll create a simple text representation of the portfolio
        if not portfolio.positions:
            self.update("No positions yet. Make your first trade!")
            return
            
        # Create a simple text-based grid representation
        header = f"{'Symbol':<10} {'Qty':<8} {'Avg Price':<12} {'Current':<12} {'P&L':<12} {'XIRR':<10}"
        separator = "-" * len(header)
        
        rows = [header, separator]
        
        for pos in portfolio.positions:
            # Check if position supports XIRR calculation
            if hasattr(pos, 'calculate_xirr'):
                xirr_val = pos.calculate_xirr()
                xirr_str = f"{xirr_val*100:.2f}%"
            else:
                xirr_str = "N/A"
                
            # Calculate P&L (use appropriate method based on position type)
            if hasattr(pos, 'unrealized_pnl'):
                pnl = pos.unrealized_pnl
            else:
                market_value = pos.quantity * pos.current_price
                cost_basis = pos.quantity * pos.avg_buy_price
                pnl = market_value - cost_basis
                
            row = (
                f"{pos.symbol:<10} "
                f"{pos.quantity:<8} "
                f"₹{pos.avg_buy_price:<11,.2f} "
                f"₹{pos.current_price:<11,.2f} "
                f"₹{pnl:<11,.2f} "
                f"{xirr_str:<10}"
            )
            rows.append(row)
            
        result = "\n".join(rows)
        self.update(result)
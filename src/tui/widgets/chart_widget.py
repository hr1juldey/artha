"""Portfolio Chart Widget using plotext for terminal visualization"""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive
import plotext as plt
from src.models import GameState
from typing import List, Dict


class PortfolioChartWidget(Static):
    """Live updating portfolio chart with multiple series"""

    portfolio_history: reactive[List[Dict]] = reactive([])

    def __init__(self, portfolio_history: List[Dict] = None, title: str = "Portfolio", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chart_title = title
        self.portfolio_history = portfolio_history or []

    def watch_portfolio_history(self, new_history: List[Dict]) -> None:
        """React to portfolio history changes"""
        self.refresh_chart()

    def on_mount(self) -> None:
        """Initialize the chart when widget is mounted"""
        self.refresh_chart()

    def on_resize(self) -> None:
        """Handle widget resize events"""
        self.refresh_chart()

    def refresh_chart(self) -> None:
        """Render chart with multiple series"""
        plt.clear_data()
        plt.clear_figure()

        if not self.portfolio_history:
            self.update("📈 No data yet. Make trades to see your portfolio grow!")
            return

        # Get widget size and set plot size accordingly
        # Subtract border/padding (approximately 4 lines for border and labels)
        width = self.size.width - 4
        height = self.size.height - 4

        # Ensure minimum size with more generous constraints
        min_width = 40  # Minimum width for readable charts
        min_height = 10  # Minimum height for readable charts
        
        if width < min_width:
            width = min_width
        if height < min_height:
            height = min_height

        # Also ensure we don't exceed reasonable maximums to prevent distortion
        max_width = 120  # Maximum width to prevent excessive stretching
        max_height = 30  # Maximum height to prevent excessive stretching
        
        if width > max_width:
            width = max_width
        if height > max_height:
            height = max_height

        plt.plotsize(width, height)

        # Extract data
        days = [entry['day'] for entry in self.portfolio_history]
        total_values = [entry['total_value'] for entry in self.portfolio_history]

        # Add stocks and cash values if available
        if 'positions_value' in self.portfolio_history[0]:
            positions_values = [entry['positions_value'] for entry in self.portfolio_history]
            cash_values = [entry['cash'] for entry in self.portfolio_history]

            # Plot multiple series
            plt.plot(days, total_values, label="Total Value", color="green", marker="braille")
            plt.plot(days, positions_values, label="Stocks Value", color="cyan", marker="braille")
            plt.plot(days, cash_values, label="Cash", color="yellow", marker="braille")
        else:
            # Fallback to single series
            plt.plot(days, total_values, label="Portfolio Value", color="green", marker="dot")

        # Add benchmark (initial capital as horizontal line)
        if self.portfolio_history:
            initial_value = self.portfolio_history[0]['total_value']
            plt.hline(initial_value, color="white")

        # Styling
        plt.title(f"{self.chart_title} - Day {days[-1] if days else 0}")
        plt.xlabel("Day")
        plt.ylabel("Value (₹)")
        plt.theme("dark")

        # Build and update
        chart_text = plt.build()
        self.update(chart_text)

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
        """Render a compact sparkline"""
        plt.clear_data()
        plt.clear_figure()

        if len(self.price_history) < 2:
            self.update(f"{self.symbol}: No history")
            return

        # Get widget size and set plot size accordingly
        width = max(self.size.width - 2, 20)
        height = max(self.size.height - 2, 6)

        # Create mini sparkline
        plt.plotsize(width, height)
        days = list(range(len(self.price_history)))
        plt.plot(days, self.price_history, marker="braille", color="green")
        plt.theme("dark")

        # No labels for mini chart
        plt.xticks([])
        plt.yticks([])

        chart_text = plt.build()

        # Add symbol and price change
        price_change = self.price_history[-1] - self.price_history[0]
        pct_change = (price_change / self.price_history[0]) * 100 if self.price_history[0] != 0 else 0
        color = "green" if price_change >= 0 else "red"

        output = f"[bold]{self.symbol}[/] [{color}]{pct_change:+.2f}%[/]\n{chart_text}"
        self.update(output)


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
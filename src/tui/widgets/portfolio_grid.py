"""Portfolio display widget"""
from textual.widgets import DataTable
from src.models import Portfolio

class PortfolioGrid(DataTable):
    """Display portfolio positions in a table"""

    def on_mount(self) -> None:
        """Setup columns"""
        self.add_columns(
            "Symbol",
            "Qty",
            "Avg Price",
            "Current",
            "P&L",
            "% Change"
        )
        self.cursor_type = "row"
        self.zebra_stripes = True

    def update_portfolio(self, portfolio: Portfolio) -> None:
        """Update table with portfolio data"""
        self.clear()

        for position in portfolio.positions:
            pnl_color = "green" if position.unrealized_pnl > 0 else "red"

            self.add_row(
                position.symbol,
                str(position.quantity),
                f"₹{position.avg_buy_price:,.2f}",
                f"₹{position.current_price:,.2f}",
                f"[{pnl_color}]₹{position.unrealized_pnl:,.2f}[/]",
                f"[{pnl_color}]{position.unrealized_pnl_pct:+.2f}%[/]"
            )
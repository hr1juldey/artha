"""Watchlist with mini charts for each stock"""
from textual.widgets import Static
from textual.containers import VerticalScroll
from src.tui.widgets.chart_widget import StockMiniChart


class WatchlistWidget(VerticalScroll):
    """Watchlist with mini charts for each stock"""

    DEFAULT_WATCHLIST = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.watchlist_symbols = self.DEFAULT_WATCHLIST

    def on_mount(self) -> None:
        """Populate watchlist"""
        self.border_title = "📋 Watchlist"
        self.refresh_watchlist()

    def refresh_watchlist(self) -> None:
        """Refresh watchlist with latest data"""
        try:
            self.remove_children()
        except Exception:
            # If there are no children to remove, continue
            pass

        for symbol in self.watchlist_symbols:
            # Get price history from market data (will need to be implemented in the data loader)
            try:
                price_history = self.app.market_data.get_price_history(symbol, days=30)
            except AttributeError:
                # Fallback if market_data not available during init
                price_history = [1000]  # Default static price

            if price_history and len(price_history) > 1:
                # Add mini chart
                mini_chart = StockMiniChart(symbol, price_history)
                self.mount(mini_chart)
            else:
                # Fallback text
                self.mount(Static(f"[yellow]{symbol}: No data[/]"))
"""Enhanced Watchlist with Stock Selection and Price Tracking"""
from textual.app import ComposeResult
from textual.widgets import Static, SelectionList, Label
from textual.widgets.selection_list import Selection
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.binding import Binding
import plotext as plt
from typing import List, Dict, Tuple, Optional
from rich.text import Text


# Unique color palette for different stocks (RGB tuples)
STOCK_COLORS = [
    (68, 180, 255),   # Blue
    (84, 239, 174),   # Green
    (255, 212, 59),   # Yellow
    (255, 121, 198),  # Pink
    (189, 147, 249),  # Purple
    (255, 184, 108),  # Orange
    (139, 233, 253),  # Cyan
    (80, 250, 123),   # Bright Green
    (255, 85, 85),    # Red
    (241, 250, 140),  # Lime
]


class StockPriceChart(Static):
    """
    Chart widget for displaying stock price history with multiple stocks support.
    Follows the Dolphie pattern for responsive, thread-safe rendering.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Map of symbol -> (price_history, color)
        self.stock_data: Dict[str, Tuple[List[float], Tuple[int, int, int]]] = {}
        self.focus_mode = False  # If True, show only the first selected stock
        self.focused_symbol: Optional[str] = None
        self.marker = "braille"

    def set_stock_data(self, stock_data: Dict[str, Tuple[List[float], Tuple[int, int, int]]]):
        """Update stock data and re-render"""
        self.stock_data = stock_data
        self.render_chart()

    def toggle_focus_mode(self, focused_symbol: Optional[str] = None):
        """Toggle between showing all stocks and focusing on one"""
        self.focus_mode = not self.focus_mode
        if self.focus_mode and focused_symbol:
            self.focused_symbol = focused_symbol
        self.render_chart()

    def on_mount(self) -> None:
        """Render the chart when mounted."""
        self.render_chart()

    def on_show(self) -> None:
        """Render the chart when the widget is shown."""
        self.render_chart()

    def on_resize(self) -> None:
        """Re-render the chart when the widget is resized - CRITICAL!"""
        self.render_chart()

    def render_chart(self) -> None:
        """
        Renders stock price charts using plotext.
        Thread-safe: snapshots data before plotting.
        Following Dolphie's pattern exactly.
        """
        # Check minimum size
        if self.size.width < 2 or self.size.height < 2:
            self.update(f"Size: {self.size.width}x{self.size.height}")
            return

        if not self.stock_data:
            self.update("\n\n\n📈 Watchlist is empty\n\n   Press 'w' to add stocks to track\n\n   Then press Space to see prices change over time")
            return

        try:
            # CRITICAL: Snapshot data for thread-safety (Dolphie pattern)
            data_snapshot = dict(self.stock_data)

            # Setup plot (Dolphie _setup_plot pattern)
            plt.clf()
            plt.canvas_color((10, 14, 27))
            plt.axes_color((10, 14, 27))
            plt.ticks_color((133, 159, 213))
            plt.plotsize(self.size.width, self.size.height)

            # Determine which stocks to display
            if self.focus_mode and self.focused_symbol and self.focused_symbol in data_snapshot:
                # Show only focused stock
                stocks_to_plot = {self.focused_symbol: data_snapshot[self.focused_symbol]}
                title_suffix = f"(Focus: {self.focused_symbol})"
            else:
                # Show all stocks
                stocks_to_plot = data_snapshot
                title_suffix = f"({len(stocks_to_plot)} stocks)" if len(stocks_to_plot) > 1 else ""

            # Plot each stock
            for symbol, (price_history, color) in stocks_to_plot.items():
                if not price_history or len(price_history) < 1:
                    continue

                days = list(range(len(price_history)))
                plt.plot(
                    days,
                    price_history,
                    marker=self.marker,
                    label=symbol,
                    color=color
                )

            # Calculate stats for title (from all plotted stocks)
            if stocks_to_plot:
                all_prices = []
                for price_history, _ in stocks_to_plot.values():
                    all_prices.extend(price_history)

                if all_prices:
                    min_price = min(all_prices)
                    max_price = max(all_prices)
                    plt.title(f"Stock Prices {title_suffix} | Range: ₹{min_price:.2f}-₹{max_price:.2f}")
                else:
                    plt.title(f"Stock Prices {title_suffix}")

            plt.xlabel("Days")
            plt.ylabel("Price (₹)")

            # Convert to ANSI and update widget - THE MAGIC!
            chart_output = plt.build()
            if chart_output:
                self.update(Text.from_ansi(chart_output))
            else:
                self.update("No chart data")

        except (OSError, ValueError, Exception) as e:
            # Handle errors gracefully
            self.update(f"Chart Error: {e}")


class EnhancedWatchlistWidget(Vertical):
    """
    Enhanced Watchlist Widget with:
    - Stock selection list (left)
    - Price tracking chart (right)
    - Focus mode toggle ('f' key)
    """

    BINDINGS = [
        Binding("f", "toggle_focus", "Toggle Focus", show=True),
    ]

    # Default available stocks
    DEFAULT_STOCKS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_stocks: List[str] = []
        self.stock_color_map: Dict[str, Tuple[int, int, int]] = {}
        self.next_color_idx = 0
        self.game_state = None  # Will be set by dashboard

    def compose(self) -> ComposeResult:
        """Create watchlist layout: selection list on left, chart on right"""
        yield Label("📋 Watchlist - Select stocks to track", id="watchlist-title")

        with Horizontal(id="watchlist-content"):
            # Left panel: Stock selection
            with Vertical(id="stock-selection-panel"):
                yield Label("Available Stocks:", id="selection-label")

                # Create selection list with all available stocks
                selection_list = SelectionList(id="stock-selector")
                yield selection_list

            # Right panel: Price chart
            yield StockPriceChart(id="watchlist-chart")

    def on_mount(self) -> None:
        """Initialize the watchlist"""
        self.border_title = "📋 Watchlist"
        self.populate_stock_selector()
        # Don't refresh chart - wait for user to select stocks
        # Show empty state message
        chart = self.query_one("#watchlist-chart", StockPriceChart)
        chart.set_stock_data({})

    def populate_stock_selector(self) -> None:
        """Populate the stock selector with available stocks"""
        selector = self.query_one("#stock-selector", SelectionList)

        # Get available stocks from market data if available
        try:
            available_stocks = self.app.market_data.get_default_stocks()
        except (AttributeError, Exception):
            # Fallback to default stocks
            available_stocks = self.DEFAULT_STOCKS

        # Add each stock as a selectable option
        for symbol in available_stocks:
            selector.add_option(Selection(symbol, symbol, False))

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle stock selection changes"""
        selector = self.query_one("#stock-selector", SelectionList)

        # Get currently selected stocks
        self.selected_stocks = list(selector.selected)

        # Assign colors to new stocks
        for symbol in self.selected_stocks:
            if symbol not in self.stock_color_map:
                # Assign next color from palette
                self.stock_color_map[symbol] = STOCK_COLORS[self.next_color_idx % len(STOCK_COLORS)]
                self.next_color_idx += 1

        # Refresh chart with selected stocks
        self.refresh_chart()

    def refresh_chart(self) -> None:
        """Refresh the chart with current selected stocks"""
        chart = self.query_one("#watchlist-chart", StockPriceChart)

        if not self.selected_stocks:
            chart.set_stock_data({})
            return

        # Get price history for each selected stock
        stock_data = {}

        # Get current game day for relative price tracking
        try:
            # Try to get game state from app first (most reliable)
            if hasattr(self.app, 'game_state') and self.app.game_state:
                game_state = self.app.game_state
                current_day = game_state.current_day
                total_days = game_state.total_days
            elif hasattr(self, 'game_state') and self.game_state:
                # Fallback to instance game_state
                current_day = self.game_state.current_day
                total_days = self.game_state.total_days
            else:
                # Last resort - use defaults
                current_day = 1
                total_days = 30
        except (AttributeError, Exception):
            current_day = 1
            total_days = 30

        for symbol in self.selected_stocks:
            try:
                # Build price history from game start (day 1) to current day
                price_history = []

                # Calculate prices for each day from day 1 to current_day
                for day in range(1, current_day + 1):
                    # day_offset: how many days ago from "total_days"
                    # Day 1 of game = total_days ago
                    # Current day of game = (total_days - current_day) ago
                    day_offset = total_days - day
                    try:
                        price = self.app.market_data.get_price_at_day(symbol, day_offset)
                        if price > 0:
                            price_history.append(price)
                    except Exception:
                        # If price fetch fails, use last known price or skip
                        if price_history:
                            price_history.append(price_history[-1])
                        continue

                if price_history and len(price_history) > 0:
                    color = self.stock_color_map.get(symbol, STOCK_COLORS[0])
                    stock_data[symbol] = (price_history, color)
            except (AttributeError, Exception):
                # Skip stocks with no data
                continue

        chart.set_stock_data(stock_data)

    def action_toggle_focus(self) -> None:
        """Toggle focus mode - show one stock vs all stocks"""
        chart = self.query_one("#watchlist-chart", StockPriceChart)

        # Get the first selected stock for focus
        focused_symbol = self.selected_stocks[0] if self.selected_stocks else None

        if not focused_symbol:
            self.app.notify("Select at least one stock to use focus mode", severity="warning")
            return

        chart.toggle_focus_mode(focused_symbol)

        # Notify user
        if chart.focus_mode:
            self.app.notify(f"📍 Focused on {focused_symbol}", severity="information")
        else:
            self.app.notify(f"📊 Showing all {len(self.selected_stocks)} stocks", severity="information")

    def update_prices(self) -> None:
        """Update prices for all selected stocks (called when day advances)"""
        self.refresh_chart()

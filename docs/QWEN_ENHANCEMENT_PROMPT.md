# Artha Trading Simulator - Professional Enhancement Prompt

**Target**: Transform Artha into a professional-grade trading terminal with live plots, realistic market simulation, and polished UX

---

## 🚨 PHASE 1: CRITICAL FIXES (DO THIS FIRST!)

Before any enhancements, you MUST fix these two blocking bugs:

### Bug #1: Trade Modal Escape Key Fix
**File**: `src/tui/screens/trade_modal.py`

**Problem**: Users cannot exit the buy/sell screen because Input/Select widgets capture the Escape key before the modal's BINDINGS action can execute.

**Fix**:
```python
from textual.events import Key

class TradeModal(ModalScreen[dict]):
    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def on_key(self, event: Key) -> None:
        """Handle key presses - ensure escape works even when widgets have focus"""
        if event.key == "escape":
            self.dismiss(None)
            event.prevent_default()
            event.stop()
```

**Test**: Press Escape while on symbol input, quantity input, or action select. Should immediately close modal.

---

### Bug #2: Database Constraint Violation Fix
**File**: `src/database/dao.py` (lines 82-110, `save_positions` function)

**Problem**: UNIQUE constraint violation on (game_id, symbol) because DELETE operations don't flush before INSERT operations.

**Fix**: Use UPDATE/INSERT/DELETE pattern instead of DELETE-all + INSERT-all:
```python
async def save_positions(session: AsyncSession, game_id: int, positions: List) -> None:
    """Save positions using UPDATE/INSERT/DELETE pattern to avoid constraint violations"""
    # Load existing positions into dict
    result = await session.execute(
        select(Position).where(Position.game_id == game_id)
    )
    existing_positions = {pos.symbol: pos for pos in result.scalars().all()}

    # Update or insert each position
    for pos in positions:
        if pos.symbol in existing_positions:
            # UPDATE existing position (no constraint violation)
            db_pos = existing_positions[pos.symbol]
            db_pos.quantity = pos.quantity
            db_pos.avg_buy_price = pos.avg_buy_price
            db_pos.current_price = pos.current_price
            # Mark as processed
            del existing_positions[pos.symbol]
        else:
            # INSERT new position
            db_pos = Position(
                game_id=game_id,
                symbol=pos.symbol,
                quantity=pos.quantity,
                avg_buy_price=pos.avg_buy_price,
                current_price=pos.current_price
            )
            session.add(db_pos)

    # DELETE positions that no longer exist
    for symbol, db_pos in existing_positions.items():
        await session.delete(db_pos)

    await session.commit()
```

**Test**: Buy stock, press spacebar to advance day 5 times. Should work without crashes.

---

## 🎯 PHASE 2: PROFESSIONAL TRADING TERMINAL UI

Transform the UI into a Bloomberg Terminal / Zerodha Kite style interface with:

### Design Reference Sources
Use these as inspiration (search with tavily if needed):
- Bloomberg Terminal layout
- Interactive Brokers TWS
- Zerodha Kite web interface
- TradingView charts
- Dolphie TUI (for Textual patterns) - https://github.com/charles-001/dolphie
- Memray TUI (for layout ideas) - https://github.com/bloomberg/memray

### Main Dashboard Layout (`src/tui/screens/main_screen.py`)

**Current State**: Basic layout with simple portfolio grid
**Target State**: Multi-panel professional trading dashboard

```python
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, TabbedContent, TabPane
from src.tui.widgets.chart_widget import PortfolioChartWidget, StockMiniChart
from src.tui.widgets.live_ticker import LiveTickerWidget
from src.tui.widgets.watchlist import WatchlistWidget
from src.tui.widgets.order_book import OrderBookWidget

class MainScreen(Screen):
    """Professional trading terminal dashboard"""

    BINDINGS = [
        ("t", "trade", "Trade"),
        ("space", "advance_day", "Next Day"),
        ("c", "coach", "AI Coach"),
        ("w", "add_to_watchlist", "Add to Watchlist"),
        ("r", "refresh", "Refresh"),
        ("s", "save", "Save"),
        ("h", "help", "Help"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    #top-bar {
        height: 5;
        background: $primary;
        border: solid green;
    }

    #market-summary {
        height: 3;
        background: $surface;
        color: $text;
    }

    #main-chart {
        height: 20;
        border: round green;
        background: $surface;
    }

    #portfolio-section {
        height: 15;
        border: solid blue;
    }

    #watchlist-section {
        height: 15;
        border: solid yellow;
    }

    #ticker-bar {
        height: 3;
        background: $primary-darken-2;
    }

    .metric-card {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        text-align: center;
    }

    .positive { color: #00ff00; }
    .negative { color: #ff0000; }
    .neutral { color: #ffff00; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # Top bar with key metrics
        with Container(id="top-bar"):
            with Horizontal(id="metrics-row"):
                yield Static(self._format_metric("Day", self.game_state.current_day), classes="metric-card")
                yield Static(self._format_metric("Cash", self.portfolio.cash, prefix="₹"), classes="metric-card positive")
                yield Static(self._format_metric("Portfolio", self.portfolio.total_value, prefix="₹"), classes="metric-card")
                yield Static(self._format_metric("P&L", self.portfolio.total_pnl, prefix="₹", show_sign=True),
                           classes=f"metric-card {self._pnl_class()}")
                yield Static(self._format_metric("P&L %", self._calculate_pnl_pct(), suffix="%", show_sign=True),
                           classes=f"metric-card {self._pnl_class()}")

        # Market summary ticker (scrolling ticker of all positions)
        with Container(id="ticker-bar"):
            yield LiveTickerWidget(self.portfolio.positions, id="live-ticker")

        # Main content area
        with Horizontal(id="main-content"):
            # Left panel: Charts and portfolio
            with Vertical(id="left-panel", classes="panel"):
                # Portfolio value chart with live updates
                with Container(id="main-chart"):
                    yield PortfolioChartWidget(
                        self.game_state.portfolio_history,
                        id="portfolio-chart",
                        title="Portfolio Performance"
                    )

                # Portfolio positions with enhanced grid
                with TabbedContent(id="portfolio-tabs"):
                    with TabPane("Positions", id="positions-tab"):
                        yield DataTable(id="portfolio-grid", zebra_stripes=True, cursor_type="row")
                    with TabPane("History", id="history-tab"):
                        yield DataTable(id="trade-history", zebra_stripes=True)

            # Right panel: Watchlist and market data
            with Vertical(id="right-panel", classes="panel"):
                # Watchlist with mini charts
                with Container(id="watchlist-section"):
                    yield WatchlistWidget(id="watchlist")

                # Order book / Recent trades
                with Container(id="order-book-section"):
                    yield OrderBookWidget(id="order-book")

                # AI Coach insights
                with ScrollableContainer(id="coach-insights-section"):
                    yield Static("💡 AI Coach Insights\n\nWaiting for trades...", id="coach-insights")

        yield Footer()

    def _format_metric(self, label: str, value, prefix="", suffix="", show_sign=False) -> str:
        """Format metric for display"""
        if isinstance(value, float):
            if show_sign:
                sign = "+" if value >= 0 else ""
                return f"{label}\n{sign}{prefix}{value:,.2f}{suffix}"
            return f"{label}\n{prefix}{value:,.2f}{suffix}"
        return f"{label}\n{prefix}{value}{suffix}"

    def _pnl_class(self) -> str:
        """Return CSS class based on P&L"""
        pnl = self.portfolio.total_pnl
        if pnl > 0:
            return "positive"
        elif pnl < 0:
            return "negative"
        return "neutral"

    def _calculate_pnl_pct(self) -> float:
        """Calculate P&L percentage"""
        invested = self.portfolio.invested
        if invested > 0:
            return (self.portfolio.total_pnl / invested) * 100
        return 0.0
```

### Enhanced Portfolio Grid with XIRR Display

**Current**: Simple text grid
**Target**: Professional DataTable with sorting, color coding, and XIRR

```python
def _populate_portfolio_grid(self) -> None:
    """Populate the portfolio DataTable with enhanced display"""
    table = self.query_one("#portfolio-grid", DataTable)
    table.clear(columns=True)

    # Add columns
    table.add_columns(
        "Symbol",
        "Quantity",
        "Avg Price",
        "Current",
        "Mkt Value",
        "P&L ₹",
        "P&L %",
        "XIRR %",
        "Days Held"
    )

    # Sort positions by P&L (descending)
    sorted_positions = sorted(
        self.portfolio.positions,
        key=lambda p: p.unrealized_pnl if hasattr(p, 'unrealized_pnl') else 0,
        reverse=True
    )

    for pos in sorted_positions:
        # Calculate metrics
        pnl = pos.unrealized_pnl if hasattr(pos, 'unrealized_pnl') else 0
        pnl_pct = pos.unrealized_pnl_pct if hasattr(pos, 'unrealized_pnl_pct') else 0
        xirr = pos.calculate_xirr() * 100 if hasattr(pos, 'calculate_xirr') else 0
        days_held = self._calculate_days_held(pos)

        # Color code based on P&L
        pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "white"

        # Add row with rich text formatting
        table.add_row(
            f"[bold cyan]{pos.symbol}[/]",
            f"{pos.quantity}",
            f"₹{pos.avg_buy_price:,.2f}",
            f"₹{pos.current_price:,.2f}",
            f"₹{pos.market_value:,.2f}",
            f"[{pnl_color}]{pnl:+,.2f}[/]",
            f"[{pnl_color}]{pnl_pct:+.2f}%[/]",
            f"[{pnl_color}]{xirr:+.2f}%[/]",
            f"{days_held}d"
        )
```

---

## 📊 PHASE 3: LIVE CHARTS AND VISUALIZATIONS

### Real-Time Portfolio Chart Updates

**Create**: `src/tui/widgets/chart_widget.py` enhancements

```python
import plotext as plt
from textual.widgets import Static
from textual.reactive import reactive
from typing import List, Dict

class PortfolioChartWidget(Static):
    """Live updating portfolio chart with multiple series"""

    portfolio_history: reactive[List[Dict]] = reactive([])

    def __init__(self, portfolio_history: List[Dict] = None, title: str = "Portfolio", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.portfolio_history = portfolio_history or []
        self.chart_title = title

    def watch_portfolio_history(self, new_history: List[Dict]) -> None:
        """React to portfolio history changes"""
        self.refresh_chart()

    def refresh_chart(self) -> None:
        """Render chart with multiple series"""
        plt.clear_data()
        plt.clear_figure()

        if not self.portfolio_history:
            self.update("📈 No data yet. Make trades to see your portfolio grow!")
            return

        # Extract data
        days = [entry['day'] for entry in self.portfolio_history]
        total_values = [entry['total_value'] for entry in self.portfolio_history]
        cash_values = [entry['cash'] for entry in self.portfolio_history]
        positions_values = [entry['positions_value'] for entry in self.portfolio_history]

        # Plot multiple series
        plt.plot(days, total_values, label="Total Value", color="green", marker="braille")
        plt.plot(days, positions_values, label="Stocks Value", color="cyan", marker="braille")
        plt.plot(days, cash_values, label="Cash", color="yellow", marker="braille")

        # Add benchmark (initial capital as horizontal line)
        if self.portfolio_history:
            initial_value = self.portfolio_history[0]['total_value']
            plt.hline(initial_value, color="white", label="Initial Capital")

        # Styling
        plt.title(f"{self.chart_title} - Day {days[-1]}")
        plt.xlabel("Day")
        plt.ylabel("Value (₹)")
        plt.theme("dark")

        # Build and update
        chart_text = plt.build()
        self.update(chart_text)

    def update_data(self, new_history: List[Dict]) -> None:
        """Update chart with new data"""
        self.portfolio_history = new_history


class StockMiniChart(Static):
    """Mini sparkline chart for individual stocks"""

    def __init__(self, symbol: str, price_history: List[float], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbol = symbol
        self.price_history = price_history
        self.render_mini_chart()

    def render_mini_chart(self) -> None:
        """Render a compact sparkline"""
        plt.clear_data()
        plt.clear_figure()

        if len(self.price_history) < 2:
            self.update(f"{self.symbol}: No history")
            return

        # Create mini sparkline
        plt.plotsize(40, 8)  # Small chart
        days = list(range(len(self.price_history)))
        plt.plot(days, self.price_history, marker="braille", color="green")
        plt.theme("dark")

        # No labels for mini chart
        plt.xticks([])
        plt.yticks([])

        chart_text = plt.build()

        # Add symbol and price change
        price_change = self.price_history[-1] - self.price_history[0]
        pct_change = (price_change / self.price_history[0]) * 100
        color = "green" if price_change >= 0 else "red"

        output = f"[bold]{self.symbol}[/] [{color}]{pct_change:+.2f}%[/]\n{chart_text}"
        self.update(output)
```

### Live Ticker Widget (Scrolling Prices)

**Create**: `src/tui/widgets/live_ticker.py`

```python
from textual.widgets import Static
from textual import work
from textual.reactive import reactive
import asyncio

class LiveTickerWidget(Static):
    """Scrolling ticker tape of stock prices"""

    ticker_text: reactive[str] = reactive("Loading...")

    def __init__(self, positions: List, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.positions = positions

    def on_mount(self) -> None:
        """Start ticker animation"""
        self.animate_ticker()

    @work(exclusive=True)
    async def animate_ticker(self) -> None:
        """Animate scrolling ticker"""
        while True:
            ticker_items = []
            for pos in self.positions:
                pnl = pos.unrealized_pnl if hasattr(pos, 'unrealized_pnl') else 0
                pnl_pct = pos.unrealized_pnl_pct if hasattr(pos, 'unrealized_pnl_pct') else 0
                color = "green" if pnl > 0 else "red" if pnl < 0 else "white"

                ticker_items.append(
                    f"[bold cyan]{pos.symbol}[/]: ₹{pos.current_price:.2f} "
                    f"[{color}]{pnl_pct:+.2f}%[/]"
                )

            ticker_text = "   📊   ".join(ticker_items) + "   📊   "
            self.ticker_text = ticker_text

            await asyncio.sleep(2)  # Update every 2 seconds

    def watch_ticker_text(self, new_text: str) -> None:
        """Update display"""
        self.update(new_text)
```

### Watchlist Widget with Mini Charts

**Create**: `src/tui/widgets/watchlist.py`

```python
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
        self.remove_children()

        for symbol in self.watchlist_symbols:
            # Get price history from market data
            price_history = self.app.market_data.get_price_history(symbol, days=30)

            if price_history:
                # Add mini chart
                mini_chart = StockMiniChart(symbol, price_history)
                self.mount(mini_chart)
            else:
                # Fallback text
                self.mount(Static(f"[yellow]{symbol}: No data[/]"))
```

---

## 🎮 PHASE 4: ENHANCED MARKET SIMULATION

### Realistic Market Dynamics

**Enhance**: `src/data/loader.py`

Add realistic market behavior:

```python
class EnhancedMarketDataLoader(MarketDataLoader):
    """Market loader with realistic simulation"""

    def __init__(self):
        super().__init__()
        self.market_sentiment = 0.0  # -1 (bearish) to +1 (bullish)
        self.volatility_regime = "normal"  # low, normal, high
        self.sector_trends = {}  # Track sector momentum

    def simulate_market_day(self, current_day: int) -> Dict[str, float]:
        """Simulate realistic market movements for all stocks"""
        # Update market regime
        self._update_market_regime(current_day)

        # Generate correlated returns for all stocks
        returns = {}
        market_return = self._generate_market_return()

        for symbol in self.tracked_symbols:
            # Stock return = market return + stock-specific noise
            stock_beta = self._get_stock_beta(symbol)
            stock_return = (market_return * stock_beta) + self._generate_stock_noise()
            returns[symbol] = stock_return

        return returns

    def _update_market_regime(self, day: int) -> None:
        """Update market sentiment and volatility"""
        # Market sentiment changes gradually (random walk)
        sentiment_change = random.gauss(0, 0.05)
        self.market_sentiment = max(-1, min(1, self.market_sentiment + sentiment_change))

        # Volatility regime switches (Markov chain)
        if random.random() < 0.05:  # 5% chance of regime switch
            regimes = ["low", "normal", "high"]
            self.volatility_regime = random.choice(regimes)

    def _generate_market_return(self) -> float:
        """Generate market-wide return"""
        # Base volatility by regime
        vol_map = {"low": 0.01, "normal": 0.02, "high": 0.04}
        volatility = vol_map[self.volatility_regime]

        # Return = sentiment drift + random noise
        drift = self.market_sentiment * 0.001  # Small positive drift in bull market
        noise = random.gauss(0, volatility)

        return drift + noise

    def _get_stock_beta(self, symbol: str) -> float:
        """Get stock's beta (market sensitivity)"""
        # Realistic betas for Indian stocks
        beta_map = {
            "RELIANCE": 1.2,    # High beta
            "TCS": 0.8,         # Low beta (defensive)
            "INFY": 0.9,        # Low beta
            "HDFCBANK": 1.0,    # Market beta
            "ICICIBANK": 1.1,   # Slightly higher
        }
        return beta_map.get(symbol, 1.0)  # Default to market beta

    def _generate_stock_noise(self) -> float:
        """Generate stock-specific random noise"""
        return random.gauss(0, 0.015)  # 1.5% stock-specific volatility

    def get_price_history(self, symbol: str, days: int = 30) -> List[float]:
        """Get recent price history for sparkline charts"""
        df = self.get_stock_data(symbol, days=days)
        if df is not None and not df.empty:
            return df['Close'].tail(days).tolist()
        return []
```

### Order Book Simulation (Optional Advanced Feature)

**Create**: `src/tui/widgets/order_book.py`

```python
from textual.widgets import Static, DataTable
from textual.containers import Container

class OrderBookWidget(Container):
    """Simulated order book for educational purposes"""

    def compose(self) -> ComposeResult:
        yield Static("📖 Order Book", id="order-book-title")
        yield DataTable(id="order-book-table", zebra_stripes=True)

    def on_mount(self) -> None:
        """Initialize order book"""
        table = self.query_one("#order-book-table", DataTable)
        table.add_columns("Bid Qty", "Bid Price", "Ask Price", "Ask Qty")
        self.refresh_order_book()

    def refresh_order_book(self, symbol: str = "MARKET") -> None:
        """Show simulated order book for selected symbol"""
        table = self.query_one("#order-book-table", DataTable)
        table.clear()

        # Simulate 5 levels of orders
        current_price = 2500.0  # Get from market data

        for level in range(5):
            bid_price = current_price - (level + 1) * 0.5
            ask_price = current_price + (level + 1) * 0.5
            bid_qty = random.randint(10, 500)
            ask_qty = random.randint(10, 500)

            table.add_row(
                f"{bid_qty}",
                f"[green]₹{bid_price:.2f}[/]",
                f"[red]₹{ask_price:.2f}[/]",
                f"{ask_qty}"
            )
```

---

## 🧪 PHASE 5: TESTING CRITERIA

After each phase, run these tests:

### Test Suite 1: Critical Functionality

```bash
# Test 1: Escape key in trade modal
# 1. Run game: python -m src.main
# 2. Press 't' to open trade modal
# 3. Press Escape (should close immediately)
# 4. Try from different input fields (symbol, quantity, action)
# ✅ PASS: Modal closes without error
# ❌ FAIL: Modal stays open or crashes

# Test 2: Day advancement without crashes
# 1. Start new game with ₹100,000
# 2. Buy RELIANCE 10 shares
# 3. Press spacebar 10 times to advance days
# ✅ PASS: No database errors, prices update
# ❌ FAIL: UNIQUE constraint error

# Test 3: Multiple position updates
# 1. Buy RELIANCE 10 shares (day 1)
# 2. Buy TCS 5 shares (day 2)
# 3. Press spacebar 5 times
# 4. Buy RELIANCE 10 more shares (day 7)
# 5. Press spacebar 5 more times
# ✅ PASS: Both positions show correct quantities
# ❌ FAIL: Positions duplicated or lost
```

### Test Suite 2: UI and Charts

```bash
# Test 4: Portfolio chart displays
# 1. Start game, make 2-3 trades
# 2. Advance 10 days
# 3. Check if chart shows on main screen
# ✅ PASS: Chart visible with line graph
# ❌ FAIL: Chart missing or shows "No data"

# Test 5: Chart updates on day advance
# 1. Note current chart shape
# 2. Press spacebar to advance day
# 3. Chart should extend with new point
# ✅ PASS: Chart updates smoothly
# ❌ FAIL: Chart doesn't update or flickers

# Test 6: Portfolio grid shows XIRR
# 1. Buy stock and hold for 5+ days
# 2. Check portfolio grid has XIRR column
# 3. XIRR should show percentage (e.g., +15.32%)
# ✅ PASS: XIRR column visible with values
# ❌ FAIL: XIRR shows N/A or errors

# Test 7: Live ticker scrolls
# 1. Have 3+ positions
# 2. Watch ticker bar at top
# 3. Should show scrolling prices
# ✅ PASS: Ticker animates smoothly
# ❌ FAIL: Ticker static or garbled
```

### Test Suite 3: Market Simulation

```bash
# Test 8: Prices change realistically
# 1. Track one stock price
# 2. Advance 20 days
# 3. Prices should vary but not jump wildly
# ✅ PASS: Daily changes are ~1-3%
# ❌ FAIL: Prices stuck or change 50%+ per day

# Test 9: Extended gameplay beyond 280 days
# 1. Create test save at day 275
# 2. Advance to day 300
# 3. Advance to day 500
# ✅ PASS: Game continues smoothly
# ❌ FAIL: Game freezes or crashes

# Test 10: Market sentiment affects all stocks
# 1. Advance 50 days
# 2. Most stocks should move in similar direction
# 3. Some correlation expected (not random walk)
# ✅ PASS: Market shows trends
# ❌ FAIL: All stocks move independently
```

### Test Suite 4: Coach and Memory

```bash
# Test 11: Coach remembers trades
# 1. Make 5 trades over 10 days
# 2. Press 'c' for coach
# 3. Coach should reference your trading patterns
# ✅ PASS: Coach mentions "You tend to..."
# ❌ FAIL: Coach gives generic advice

# Test 12: Coach tracks portfolio trends
# 1. Grow portfolio by 20% over 15 days
# 2. Ask coach for insights
# 3. Coach should mention positive trend
# ✅ PASS: Coach acknowledges growth
# ❌ FAIL: Coach doesn't mention performance

# Test 13: Memory persists across saves
# 1. Make trades, advance days
# 2. Save game
# 3. Load game
# 4. Check coach insights
# ✅ PASS: Coach remembers history
# ❌ FAIL: Coach memory reset
```

### Test Suite 5: Edge Cases

```bash
# Test 14: Sell all shares of position
# 1. Buy 10 RELIANCE shares
# 2. Sell all 10 shares
# 3. Position should disappear from grid
# ✅ PASS: Position removed cleanly
# ❌ FAIL: Position shows 0 shares or errors

# Test 15: Insufficient funds
# 1. Have ₹10,000 cash
# 2. Try to buy 100 RELIANCE shares (₹250,000)
# 3. Should show clear error
# ✅ PASS: Error message, trade rejected
# ❌ FAIL: Trade executes or crashes

# Test 16: Empty portfolio display
# 1. Start new game
# 2. Don't make any trades
# 3. Advance a few days
# ✅ PASS: Shows "No positions" message
# ❌ FAIL: Crashes or shows empty table

# Test 17: Large position quantities
# 1. Buy 5000 shares of a stock
# 2. Check formatting in grid
# ✅ PASS: Numbers formatted with commas
# ❌ FAIL: Numbers overflow or garbled

# Test 18: Negative P&L display
# 1. Buy stock
# 2. Wait for price to drop
# 3. Check P&L column is red
# ✅ PASS: Red text with negative sign
# ❌ FAIL: Wrong color or sign
```

---

## 🔍 USING CONTEXT7 AND TAVILY SEARCH MCP

### When to Use Context7

**Use context7 when you need to**:
- Find similar patterns in Textual documentation
- Search for how other TUI apps handle specific features
- Find example code for plotext usage
- Locate best practices for reactive widgets

**Example queries**:
```bash
# Finding Textual patterns
@context7 "How do I create a ModalScreen that properly handles Escape key in Textual 0.50+?"

# Finding chart examples
@context7 "plotext examples for terminal line charts with multiple series"

# Finding reactive widget patterns
@context7 "Textual reactive attributes and watch methods for live updates"

# Finding DataTable patterns
@context7 "Textual DataTable sorting and color coding rows"
```

### When to Use Tavily Search MCP

**Use tavily search when you need to**:
- Research real trading terminal UIs
- Find finance/market simulation best practices
- Look up XIRR calculation methods
- Research market microstructure

**Example queries**:
```bash
# UI research
tavily: "Bloomberg terminal interface layout design"
tavily: "Zerodha Kite trading platform UI components"
tavily: "TradingView chart widget design patterns"

# Market simulation
tavily: "Stock market simulation random walk model"
tavily: "Market microstructure order book simulation"
tavily: "Realistic stock price generation for games"

# Financial calculations
tavily: "XIRR calculation implementation Python"
tavily: "Portfolio return calculation methods"
tavily: "Beta coefficient calculation stocks"

# TUI references
tavily: "Best terminal UI trading applications"
tavily: "ASCII charts for financial data visualization"
```

### Decision Tree: Which Tool to Use?

```
Need to solve a problem?
│
├─ Is it about Textual framework usage?
│  └─ Use context7 with Textual docs
│
├─ Is it about code patterns in Python?
│  └─ Use context7 with GitHub examples
│
├─ Is it about financial domain knowledge?
│  └─ Use tavily search for concepts
│
├─ Is it about UI design inspiration?
│  └─ Use tavily search for screenshots/descriptions
│
└─ Is it about market simulation theory?
   └─ Use tavily search for algorithms
```

### Debugging Workflow

```
1. Hit an error/bug
   ↓
2. Read the error message carefully
   ↓
3. Check if it's a Textual API issue
   → YES: context7 "Textual [error message]"
   → NO: Continue
   ↓
4. Check if it's a domain knowledge gap
   → YES: tavily "[financial concept] explanation"
   → NO: Continue
   ↓
5. Search for similar implementations
   → context7 "[feature] implementation examples"
   ↓
6. Try fix, test, iterate
   ↓
7. If still stuck after 3 attempts:
   → Post detailed question with:
      - What you tried
      - Expected vs actual behavior
      - Relevant code snippets
      - Error messages
```

---

## 📋 IMPLEMENTATION CHECKLIST

Track your progress:

### Phase 1: Critical Fixes
- [ ] Fix escape key in trade_modal.py
- [ ] Fix database constraint in dao.py
- [ ] Test: Modal closes with Escape
- [ ] Test: Day advancement works without crashes
- [ ] Test: Multiple position updates work

### Phase 2: Professional UI
- [ ] Update main_screen.py with new layout
- [ ] Add metric cards in top bar
- [ ] Create live ticker widget
- [ ] Enhance portfolio DataTable with colors
- [ ] Add XIRR column to portfolio grid
- [ ] Test: All widgets render correctly
- [ ] Test: Layout responsive to terminal size

### Phase 3: Live Charts
- [ ] Enhance PortfolioChartWidget with multiple series
- [ ] Create StockMiniChart for watchlist
- [ ] Create LiveTickerWidget with animation
- [ ] Create WatchlistWidget with mini charts
- [ ] Test: Charts update on day advance
- [ ] Test: Charts show accurate data
- [ ] Test: Mini charts render in watchlist

### Phase 4: Market Simulation
- [ ] Add market sentiment to data loader
- [ ] Add volatility regimes
- [ ] Implement stock betas
- [ ] Add correlated returns generation
- [ ] Add price history method for charts
- [ ] Test: Prices change realistically
- [ ] Test: Game works beyond day 280
- [ ] Test: Market shows trending behavior

### Phase 5: Testing
- [ ] Run all 18 test cases
- [ ] Document any failures
- [ ] Fix critical issues first
- [ ] Fix medium priority issues
- [ ] Polish UI issues last

---

## 🎯 SUCCESS METRICS

Consider the enhancement successful when:

1. **Stability**: All 18 tests pass without crashes
2. **Performance**: Game responds within 100ms to all actions
3. **Visuals**: Charts update smoothly, colors appropriate
4. **Realism**: Prices change 1-3% per day on average
5. **UX**: Users can understand the interface without documentation
6. **Memory**: Game runs for 500+ days without memory leaks
7. **Coach**: AI provides personalized insights based on history
8. **Persistence**: All data survives save/load cycles

---

## 🚀 FINAL NOTES

**Remember**:
- Fix critical bugs FIRST before any enhancements
- Test after EACH phase, not at the end
- Use context7 for code patterns
- Use tavily for domain knowledge
- Keep the UI professional and clean
- Make realistic market simulation, not random
- Document any blockers immediately

**Goal**: Transform Artha into a professional trading terminal that teaches investing through realistic simulation and intelligent coaching.

Good luck! 🎮📈

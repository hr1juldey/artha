"""Professional Trading Terminal Dashboard"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable, SelectionList
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from src.models import GameState
from src.tui.widgets.chart_widget import PortfolioChartWidget
from src.tui.widgets.live_ticker import LiveTickerWidget
from src.tui.widgets.enhanced_watchlist import EnhancedWatchlistWidget
from src.tui.screens.trade_modal import TradeModal
from src.engine.trade_executor import TradeExecutor
from src.utils.xirr_calculator import TransactionType
import asyncio


class DashboardScreen(Screen):
    """Professional trading terminal dashboard"""
    
    BINDINGS = [
        ("t", "trade", "Trade"),
        ("space", "advance_day", "Next Day"),
        ("c", "coach", "AI Coach"),
        ("w", "add_stock_to_watchlist", "Add to Watchlist"),
        ("plus", "chart_zoom_in", "Chart Zoom In"),
        ("minus", "chart_zoom_out", "Chart Zoom Out"),
        ("equal", "chart_reset_zoom", "Chart Reset"),
        ("r", "refresh", "Refresh"),
        ("s", "save", "Save"),
        ("h", "help", "Help"),
        ("q", "quit", "Quit"),
    ]

    # CSS styling - Fixed for proper chart rendering
    CSS = """
    #top-bar {
        height: 5;
        background: $boost;
        border: solid $primary;
    }

    #metrics-row {
        layout: horizontal;
        height: 100%;
    }

    #ticker-bar {
        height: 3;
        background: $panel-darken-1;
    }

    #main-content {
        layout: horizontal;
        height: 1fr;
    }

    #left-panel {
        width: 2fr;
        layout: vertical;
        height: 100%;
    }

    #right-panel {
        width: 1fr;
        layout: vertical;
        height: 100%;
    }

    #main-chart {
        height: 1fr;
        border: solid $primary;
        background: $surface;
    }

    #portfolio-title {
        height: auto;
        background: $boost;
        padding: 0 1;
    }

    #portfolio-grid {
        height: 1fr;
        border: solid $primary;
    }

    #watchlist {
        height: 1fr;
        border: solid $accent;
        padding: 0;
    }

    #watchlist-title {
        height: auto;
        background: $boost;
        padding: 0 1;
        text-align: center;
        color: $accent;
    }

    #watchlist-content {
        height: 1fr;
        width: 100%;
    }

    #stock-selection-panel {
        width: 30%;
        height: 100%;
        border-right: solid $primary;
        padding: 1;
    }

    #selection-label {
        height: auto;
        color: $text-muted;
        margin-bottom: 1;
    }

    #stock-selector {
        height: 1fr;
        border: none;
    }

    #watchlist-chart {
        width: 70%;
        height: 100%;
        padding: 1;
    }

    #coach-title {
        height: auto;
        background: $boost;
        padding: 0 1;
    }

    #coach-insights {
        height: 1fr;
        border: solid $secondary;
        padding: 1;
    }

    .metric-card {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        text-align: center;
    }

    .positive { color: $success; }
    .negative { color: $error; }
    .neutral { color: $warning; }
    """

    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self.portfolio = game_state.portfolio

    def compose(self) -> ComposeResult:
        """Create professional trading terminal layout"""
        yield Header(show_clock=True)

        # Top bar with key metrics
        with Horizontal(id="top-bar"):
            yield Static(self._format_metric("Day", self.game_state.current_day), classes="metric-card")
            yield Static(self._format_metric("Cash", self.portfolio.cash, prefix="₹"), classes="metric-card positive")
            yield Static(self._format_metric("Portfolio", self.portfolio.total_value, prefix="₹"), classes="metric-card")
            yield Static(self._format_metric("P&L", self.portfolio.total_pnl, prefix="₹", show_sign=True),
                       classes=f"metric-card {self._pnl_class()}")
            yield Static(self._format_metric("P&L %", self._calculate_pnl_pct(), suffix="%", show_sign=True),
                       classes=f"metric-card {self._pnl_class()}")

        # Market summary ticker (scrolling ticker of all positions)
        yield LiveTickerWidget(self.portfolio.positions, id="ticker-bar")

        # Main content area
        with Horizontal(id="main-content"):
            # Left panel: Charts and portfolio
            with Vertical(id="left-panel"):
                yield PortfolioChartWidget(
                    self.game_state.portfolio_history,
                    id="main-chart",
                    title="Portfolio Performance"
                )
                yield Static("📋 Portfolio Positions", id="portfolio-title")
                yield DataTable(id="portfolio-grid", zebra_stripes=True, cursor_type="row")

            # Right panel: Watchlist and AI Coach
            with Vertical(id="right-panel"):
                yield EnhancedWatchlistWidget(id="watchlist")
                yield Static("💡 AI Coach Insights", id="coach-title")
                with ScrollableContainer(id="coach-insights"):
                    yield Static("Waiting for trades...", id="coach-insights-text")

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

    def on_mount(self) -> None:
        """Initialize screen"""
        # Update portfolio grid with initial data
        self._populate_portfolio_grid()

        # Update chart with initial data
        chart_widget = self.query_one("#main-chart", PortfolioChartWidget)
        if chart_widget:
            chart_widget.update_portfolio_history(self.game_state.portfolio_history)

        # Initialize watchlist with game state reference
        try:
            watchlist_widget = self.query_one("#watchlist", EnhancedWatchlistWidget)
            watchlist_widget.game_state = self.game_state
        except Exception:
            pass

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

        # Check if portfolio positions exist and have the required attributes
        if not hasattr(self.portfolio, 'positions'):
            return

        # Sort positions by P&L (descending)
        try:
            sorted_positions = sorted(
                self.portfolio.positions,
                key=lambda p: p.unrealized_pnl if hasattr(p, 'unrealized_pnl') else 0,
                reverse=True
            )
        except TypeError:
            # Fallback if positions don't have the attribute yet
            sorted_positions = self.portfolio.positions

        # Calculate game's current date for XIRR calculation
        from datetime import timedelta
        game_current_date = self.game_state.created_at.date() + timedelta(days=self.game_state.current_day)

        for pos in sorted_positions:
            # Calculate metrics
            pnl = pos.unrealized_pnl if hasattr(pos, 'unrealized_pnl') else (pos.current_price - pos.avg_buy_price) * pos.quantity if hasattr(pos, 'avg_buy_price') else 0
            pnl_pct = pos.unrealized_pnl_pct if hasattr(pos, 'unrealized_pnl_pct') else 0
            # Pass game's current date for proper XIRR calculation based on simulation time
            xirr = pos.calculate_xirr(game_current_date) * 100 if hasattr(pos, 'calculate_xirr') else 0
            days_held = self._calculate_days_held(pos)

            # Color code based on P&L
            pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "white"

            # Add row with rich text formatting
            table.add_row(
                f"[bold cyan]{pos.symbol}[/]",
                f"{pos.quantity}",
                f"₹{pos.avg_buy_price:,.2f}" if hasattr(pos, 'avg_buy_price') else f"₹{pos.current_price:,.2f}",
                f"₹{pos.current_price:,.2f}",
                f"₹{pos.market_value if hasattr(pos, 'market_value') else pos.quantity * pos.current_price:,.2f}",
                f"[{pnl_color}]{pnl:+,.2f}[/]",
                f"[{pnl_color}]{pnl_pct:+.2f}%[/]",
                f"[{pnl_color}]{xirr:+.2f}%[/]",
                f"{days_held}d"
            )

    def _calculate_days_held(self, position) -> int:
        """Calculate number of days this position has been held"""
        # If position has transaction history, calculate from first transaction
        if hasattr(position, 'transactions') and position.transactions:
            from datetime import timedelta
            game_current_date = self.game_state.created_at.date() + timedelta(days=self.game_state.current_day)
            first_transaction_date = position.transactions[0].date
            days_held = (game_current_date - first_transaction_date).days
            return days_held
        # Fallback: assume held since game start
        return self.game_state.current_day

    def action_quit(self) -> None:
        """Quit application"""
        self.app.exit()
    
    def action_save(self) -> None:
        """Save game"""
        asyncio.create_task(self.app._save_current_game())

    def action_trade(self) -> None:
        """Open trade modal"""
        stocks = self.app.market_data.get_default_stocks()
        cash = self.game_state.portfolio.cash

        def handle_trade(result):
            if result:
                self._execute_trade(result)

        self.app.push_screen(TradeModal(stocks, cash), handle_trade)

    def _execute_trade(self, trade_data: dict) -> None:
        """Execute the trade"""
        symbol = trade_data["symbol"]
        action = trade_data["action"]
        quantity = trade_data["quantity"]

        # Get current price
        price = self.app.market_data.get_current_price(symbol)

        if price <= 0:
            self.app.notify("Could not get price for stock", severity="error")
            return

        # Calculate game's current date for transaction
        from datetime import timedelta
        game_current_date = self.game_state.created_at.date() + timedelta(days=self.game_state.current_day)

        # Execute trade
        if action == "BUY":
            result = TradeExecutor.execute_buy(
                self.game_state.portfolio,
                symbol,
                quantity,
                price,
                game_current_date
            )
        else:
            result = TradeExecutor.execute_sell(
                self.game_state.portfolio,
                symbol,
                quantity,
                price,
                game_current_date
            )

        # Show result
        if result.success:
            self.app.notify(result.message, severity="information")
            self._refresh_display()

            # Record trade in coach memory
            from datetime import datetime
            trade_info = {
                "action": action,
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "portfolio_value": self.game_state.portfolio.total_value,
                "timestamp": datetime.now()
            }
            self.app.coach.add_to_memory("trade", trade_info)

            # Get enhanced AI feedback
            feedback = self.app.coach.get_enhanced_trade_feedback(
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                portfolio_value=self.game_state.portfolio.total_value,
                cash_remaining=self.game_state.portfolio.cash,
                num_positions=len(self.game_state.portfolio.positions)
            )
            self.app.notify(f"Coach: {feedback}", timeout=10)

            # Auto-save after trade
            asyncio.create_task(self.app._save_current_game())
        else:
            self.app.notify(result.message, severity="error")

    def action_advance_day(self) -> None:
        """Advance game by one day with extended support"""
        # Add day limit check to prevent freezing beyond 270-280 days
        if self.game_state.current_day >= 1000:  # Set a hard limit at 1000 days
            self.app.notify("Maximum simulation days reached.", severity="error")
            return
        
        # For soft warnings
        if self.game_state.current_day >= 500:
            self.app.notify("Approaching maximum simulation days. Consider starting a new game.", severity="warning")

        self.game_state.current_day += 1

        # Update prices for all positions
        for position in self.game_state.portfolio.positions:
            # For days beyond the original range, we'll use the market data loader's 
            # extended functionality to simulate prices beyond historical data
            try:
                # Get price from N days ago
                if self.game_state.current_day <= self.game_state.total_days:
                    days_ago = self.game_state.total_days - self.game_state.current_day
                    new_price = self.app.market_data.get_price_at_day(position.symbol, days_ago)
                else:
                    # Beyond original period, use extended simulation
                    new_price = self.app.market_data.get_price_at_day_with_simulation(position.symbol)
                
                if new_price > 0:
                    position.current_price = new_price
            except Exception as e:
                # Fallback to current price if historical lookup fails
                self.app.notify(f"Price update issue for {position.symbol}: {str(e)}", severity="warning")

        # Record portfolio state for coach memory and charting
        self.game_state.record_portfolio_state()
        
        # Add portfolio snapshot to coach memory
        portfolio_snapshot = {
            "day": self.game_state.current_day,
            "total_value": self.game_state.portfolio.total_value,
            "cash": self.game_state.portfolio.cash,
            "positions_value": self.game_state.portfolio.positions_value,
            "pnl": self.game_state.portfolio.total_pnl,
            "num_positions": len(self.game_state.portfolio.positions)
        }
        self.app.coach.add_to_memory("portfolio_snapshot", portfolio_snapshot)

        self._refresh_display()

        # Update watchlist prices (CRITICAL: update game state reference first)
        try:
            watchlist_widget = self.query_one("#watchlist", EnhancedWatchlistWidget)
            watchlist_widget.game_state = self.game_state  # Update reference
            watchlist_widget.update_prices()  # Refresh chart with new day
        except Exception as e:
            # Log error for debugging but don't crash
            import traceback
            traceback.print_exc()

        self.app.notify(f"Advanced to day {self.game_state.current_day}")

        # Auto-save
        asyncio.create_task(self.app._save_current_game())

    def _refresh_display(self) -> None:
        """Refresh all displays with updated values and styling"""
        # CRITICAL: Always use fresh reference from game_state
        portfolio = self.game_state.portfolio

        # Update portfolio grid
        self._populate_portfolio_grid()

        # Update chart
        chart_widget = self.query_one("#main-chart", PortfolioChartWidget)
        if chart_widget:
            chart_widget.update_portfolio_history(self.game_state.portfolio_history)

        # Update ticker with latest positions
        ticker_widget = self.query_one("#ticker-bar", LiveTickerWidget)
        if ticker_widget and hasattr(ticker_widget, 'update_positions'):
            ticker_widget.update_positions(portfolio.positions)

        # Update summary cards individually with fresh values and CSS classes
        top_bar = self.query_one("#top-bar")
        children_list = list(top_bar.children)

        # Calculate fresh values
        current_pnl = portfolio.total_pnl
        current_total_value = portfolio.total_value
        current_cash = portfolio.cash
        current_pnl_pct = (current_pnl / portfolio.invested) * 100 if portfolio.invested > 0 else 0.0
        pnl_class = "positive" if current_pnl > 0 else "negative" if current_pnl < 0 else "neutral"

        for i, child in enumerate(children_list):
            if i == 0:  # Day
                child.update(self._format_metric("Day", self.game_state.current_day))
                child.set_classes("metric-card")
            elif i == 1:  # Cash
                child.update(self._format_metric("Cash", current_cash, prefix="₹"))
                child.set_classes("metric-card positive")
            elif i == 2:  # Total Value
                child.update(self._format_metric("Portfolio", current_total_value, prefix="₹"))
                child.set_classes("metric-card")
            elif i == 3:  # P&L ₹
                child.update(self._format_metric("P&L", current_pnl, prefix="₹", show_sign=True))
                child.set_classes(f"metric-card {pnl_class}")
            elif i == 4:  # P&L %
                child.update(self._format_metric("P&L %", current_pnl_pct, suffix="%", show_sign=True))
                child.set_classes(f"metric-card {pnl_class}")
        
    def action_coach(self) -> None:
        """Get portfolio insights from coach with enhanced trend analysis"""
        portfolio = self.game_state.portfolio
        cash_percentage = (portfolio.cash / portfolio.total_value) * 100 if portfolio.total_value > 0 else 100
        # Calculate total P&L percentage based on invested amount
        total_invested = portfolio.invested
        total_pnl_percentage = (portfolio.total_pnl / total_invested) * 100 if total_invested > 0 else 0

        # Use enhanced portfolio insights
        insights = self.app.coach.get_portfolio_trend_insights()
        
        # If the enhanced insights are not available, fall back to basic analysis
        if not insights or "Not enough data" in insights:
            insights = self.app.coach.get_portfolio_insights(
                num_positions=len(portfolio.positions),
                total_value=portfolio.total_value,
                cash_percentage=cash_percentage,
                total_pnl_percentage=total_pnl_percentage
            )

        # Update coach insights display (NO notification - insights show in the panel only)
        coach_insights_widget = self.query_one("#coach-insights-text", Static)
        if coach_insights_widget:
            coach_insights_widget.update(insights)

    def action_help(self) -> None:
        """Show help screen"""
        from src.tui.screens.help_screen import HelpScreen
        self.app.push_screen(HelpScreen())
        
    def action_refresh(self) -> None:
        """Refresh the display"""
        self._refresh_display()

    def action_chart_zoom_in(self) -> None:
        """Zoom in on portfolio chart (show fewer days, more detail)"""
        chart_widget = self.query_one("#main-chart", PortfolioChartWidget)
        if chart_widget:
            if chart_widget.zoom_in():
                self.app.notify("📊 Chart zoomed in", severity="information", timeout=1)
            else:
                self.app.notify("⚠ Maximum zoom reached (5 days minimum)", severity="warning", timeout=2)

    def action_chart_zoom_out(self) -> None:
        """Zoom out on portfolio chart (show more days, less detail)"""
        chart_widget = self.query_one("#main-chart", PortfolioChartWidget)
        if chart_widget:
            chart_widget.zoom_out()
            self.app.notify("📊 Chart zoomed out", severity="information", timeout=1)

    def action_chart_reset_zoom(self) -> None:
        """Reset chart zoom to show all data"""
        chart_widget = self.query_one("#main-chart", PortfolioChartWidget)
        if chart_widget:
            chart_widget.reset_zoom()
            self.app.notify("📊 Chart zoom reset to full view", severity="information", timeout=1)

    def action_add_stock_to_watchlist(self) -> None:
        """Add a stock to the watchlist - opens stock selector"""
        # Get available stocks
        stocks = self.app.market_data.get_default_stocks()

        # Create a simple prompt to add stock
        from textual.widgets import OptionList
        from textual.widgets.option_list import Option
        from textual.screen import ModalScreen
        from textual.containers import Vertical as VerticalContainer
        from textual.widgets import Label, Button

        class AddStockModal(ModalScreen):
            """Modal for adding stock to watchlist"""

            CSS = """
            AddStockModal {
                align: center middle;
            }

            #add_stock_dialog {
                width: 50;
                height: auto;
                max-height: 30;
                background: $surface;
                border: thick $primary;
                padding: 1 2;
            }

            #stock_option_list {
                height: 15;
                margin: 1 0;
                border: solid $accent;
            }
            """

            def __init__(self, stocks, watchlist_widget):
                super().__init__()
                self.stocks = stocks
                self.watchlist_widget = watchlist_widget

            def compose(self) -> ComposeResult:
                with VerticalContainer(id="add_stock_dialog"):
                    yield Label("Select stock to add to watchlist:", id="modal_title")
                    option_list = OptionList(id="stock_option_list")
                    for stock in self.stocks:
                        option_list.add_option(Option(stock, id=stock))
                    yield option_list
                    yield Label("Press Enter to add, Esc to cancel", id="modal_hint")

            def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
                """Add selected stock to watchlist"""
                stock_symbol = event.option.id

                # Add to watchlist by programmatically selecting it
                try:
                    selector = self.watchlist_widget.query_one("#stock-selector", SelectionList)

                    # Find and toggle the selection
                    for idx, option in enumerate(selector._options):
                        if option.id == stock_symbol:
                            # Check if already selected
                            if stock_symbol not in self.watchlist_widget.selected_stocks:
                                selector.select(idx)
                                self.app.notify(f"✓ Added {stock_symbol} to watchlist", severity="information")
                            else:
                                self.app.notify(f"ℹ {stock_symbol} already in watchlist", severity="warning")
                            break
                except Exception as e:
                    self.app.notify(f"Error adding stock: {e}", severity="error")

                self.dismiss()

            def on_key(self, event) -> None:
                """Handle escape key"""
                if event.key == "escape":
                    self.dismiss()

        # Show the modal
        try:
            watchlist_widget = self.query_one("#watchlist", EnhancedWatchlistWidget)
            self.app.push_screen(AddStockModal(stocks, watchlist_widget))
        except Exception as e:
            self.app.notify(f"Failed to open stock selector: {e}", severity="error")
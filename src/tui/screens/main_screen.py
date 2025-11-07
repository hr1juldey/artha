"""Main game screen"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Vertical
from src.tui.widgets.portfolio_grid import PortfolioGrid
from src.models import GameState
from src.tui.screens.trade_modal import TradeModal
from src.engine.trade_executor import TradeExecutor
from src.utils.xirr_calculator import TransactionType
import asyncio
from datetime import datetime

class MainScreen(Screen):
    """Main game screen with portfolio display"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "menu", "Menu"),
        ("s", "save", "Save"),  # NEW
        ("t", "trade", "Trade"),  # NEW
        ("space", "advance_day", "Next Day"),  # NEW
        ("c", "coach", "Coach"),  # NEW
        ("h", "help", "Help"),  # NEW
    ]

    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()

        with Container():
            # Status bar
            yield Static(
                f"[bold]{self.game_state.player_name}[/bold] | "
                f"Day: {self.game_state.current_day}/{self.game_state.total_days} | "
                f"Cash: ₹{self.game_state.portfolio.cash:,.2f} | "
                f"Total: ₹{self.game_state.portfolio.total_value:,.2f}",
                id="status"
            )

            # Portfolio
            with Vertical():
                yield Static("## Portfolio", classes="section-title")
                yield PortfolioGrid()

        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen"""
        portfolio_grid = self.query_one(PortfolioGrid)
        portfolio_grid.update_portfolio(self.game_state.portfolio)

    def action_quit(self) -> None:
        """Quit application"""
        self.app.exit()

    def action_menu(self) -> None:
        """Return to menu"""
        self.app.pop_screen()
    
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

        # Execute trade
        if action == "BUY":
            result = TradeExecutor.execute_buy(
                self.game_state.portfolio,
                symbol,
                quantity,
                price
            )
        else:
            result = TradeExecutor.execute_sell(
                self.game_state.portfolio,
                symbol,
                quantity,
                price
            )

        # Show result
        if result.success:
            self.app.notify(result.message, severity="information")
            self._refresh_display()

            # Record trade in coach memory
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
        self.app.notify(f"Advanced to day {self.game_state.current_day}")

        # Auto-save
        asyncio.create_task(self.app._save_current_game())

    def _refresh_display(self) -> None:
        """Refresh portfolio display"""
        portfolio_grid = self.query_one(PortfolioGrid)
        portfolio_grid.update_portfolio(self.game_state.portfolio)

        # Update status bar
        status = self.query_one("#status", Static)
        status.update(
            f"[bold]{self.game_state.player_name}[/bold] | "
            f"Day: {self.game_state.current_day}/{self.game_state.total_days} | "
            f"Cash: ₹{self.game_state.portfolio.cash:,.2f} | "
            f"Total: ₹{self.game_state.portfolio.total_value:,.2f}"
        )
        
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

        self.app.notify(f"Coach Insights:\n{insights}", timeout=15)

    def action_help(self) -> None:
        """Show help screen"""
        from src.tui.screens.help_screen import HelpScreen
        self.app.push_screen(HelpScreen())
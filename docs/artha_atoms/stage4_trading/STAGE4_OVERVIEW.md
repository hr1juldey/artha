# Stage 4: Trading Engine

**Duration**: 2 hours (Hours 6-8)
**Status**: Core Game Mechanics
**Depends On**: Stage 3 complete and working

---

## Objective

Implement full trading functionality:
- Buy/Sell order execution
- Trade modal UI
- Portfolio updates
- Day advance mechanic
- Commission/fees calculation

---

## Success Criteria

- [ ] Can open trade modal with 't' key
- [ ] Can buy stocks
- [ ] Can sell stocks from portfolio
- [ ] Portfolio updates immediately
- [ ] Cash balance adjusts correctly
- [ ] Commission calculated and deducted
- [ ] Can advance day with SPACE
- [ ] Prices update on day advance
- [ ] Trade history saved to database

---

## Files to Create

### 1. `src/engine/__init__.py`
```python
"""Game engine package"""
from src.engine.trade_executor import TradeExecutor

__all__ = ["TradeExecutor"]
```

### 2. `src/engine/trade_executor.py`
```python
"""Trade execution logic"""
from dataclasses import dataclass
from enum import Enum
from src.models import Portfolio, Position
from src.config import COMMISSION_RATE

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class TradeResult:
    """Result of trade execution"""
    success: bool
    message: str
    executed_price: float = 0.0
    quantity: int = 0
    total_cost: float = 0.0
    commission: float = 0.0

class TradeExecutor:
    """Executes buy/sell orders"""

    @staticmethod
    def calculate_commission(amount: float) -> float:
        """Calculate commission (0.03% or ₹20 max)"""
        commission = amount * COMMISSION_RATE
        return min(commission, 20.0)

    @staticmethod
    def execute_buy(
        portfolio: Portfolio,
        symbol: str,
        quantity: int,
        price: float
    ) -> TradeResult:
        """Execute buy order"""
        # Calculate costs
        cost = price * quantity
        commission = TradeExecutor.calculate_commission(cost)
        total_cost = cost + commission

        # Check if enough cash
        if portfolio.cash < total_cost:
            return TradeResult(
                success=False,
                message=f"Insufficient funds. Need ₹{total_cost:,.2f}, have ₹{portfolio.cash:,.2f}"
            )

        # Deduct cash
        portfolio.cash -= total_cost

        # Find existing position or create new
        existing_pos = None
        for pos in portfolio.positions:
            if pos.symbol == symbol:
                existing_pos = pos
                break

        if existing_pos:
            # Update average buy price
            total_qty = existing_pos.quantity + quantity
            total_cost_basis = (existing_pos.avg_buy_price * existing_pos.quantity) + cost
            existing_pos.avg_buy_price = total_cost_basis / total_qty
            existing_pos.quantity = total_qty
            existing_pos.current_price = price
        else:
            # Create new position
            new_pos = Position(
                symbol=symbol,
                quantity=quantity,
                avg_buy_price=price,
                current_price=price
            )
            portfolio.positions.append(new_pos)

        return TradeResult(
            success=True,
            message=f"Bought {quantity} shares of {symbol} at ₹{price:,.2f}",
            executed_price=price,
            quantity=quantity,
            total_cost=total_cost,
            commission=commission
        )

    @staticmethod
    def execute_sell(
        portfolio: Portfolio,
        symbol: str,
        quantity: int,
        price: float
    ) -> TradeResult:
        """Execute sell order"""
        # Find position
        position = None
        for pos in portfolio.positions:
            if pos.symbol == symbol:
                position = pos
                break

        if not position:
            return TradeResult(
                success=False,
                message=f"No position in {symbol}"
            )

        if position.quantity < quantity:
            return TradeResult(
                success=False,
                message=f"Insufficient quantity. Have {position.quantity}, trying to sell {quantity}"
            )

        # Calculate proceeds
        proceeds = price * quantity
        commission = TradeExecutor.calculate_commission(proceeds)
        net_proceeds = proceeds - commission

        # Update position
        position.quantity -= quantity
        if position.quantity == 0:
            portfolio.positions.remove(position)
        else:
            position.current_price = price

        # Add cash
        portfolio.cash += net_proceeds

        return TradeResult(
            success=True,
            message=f"Sold {quantity} shares of {symbol} at ₹{price:,.2f}",
            executed_price=price,
            quantity=quantity,
            total_cost=net_proceeds,
            commission=commission
        )
```

### 3. `src/tui/screens/trade_modal.py`
```python
"""Trade modal dialog"""
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Input, Select, Button, Label, Static
from textual.containers import Container, Vertical, Horizontal
from src.engine.trade_executor import OrderSide

class TradeModal(ModalScreen[dict]):
    """Modal for executing trades"""

    def __init__(self, available_stocks: list[str], cash: float):
        super().__init__()
        self.available_stocks = available_stocks
        self.cash = cash

    def compose(self) -> ComposeResult:
        with Container(id="trade-modal"):
            with Vertical():
                yield Static("# Execute Trade", id="modal-title")
                yield Static(f"Available Cash: ₹{self.cash:,.2f}", id="cash-display")

                yield Label("Stock Symbol:")
                yield Select(
                    options=[(s, s) for s in self.available_stocks],
                    id="symbol-select"
                )

                yield Label("Action:")
                yield Select(
                    options=[("Buy", "BUY"), ("Sell", "SELL")],
                    id="action-select"
                )

                yield Label("Quantity:")
                yield Input(
                    placeholder="Enter quantity",
                    type="integer",
                    id="quantity-input"
                )

                yield Static("", id="estimate")

                with Horizontal():
                    yield Button("Execute", variant="success", id="execute-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "execute-btn":
            # Get values
            symbol = self.query_one("#symbol-select", Select).value
            action = self.query_one("#action-select", Select).value
            qty_input = self.query_one("#quantity-input", Input)

            try:
                quantity = int(qty_input.value)
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")

                result = {
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity
                }
                self.dismiss(result)
            except ValueError as e:
                self.query_one("#estimate", Static).update(f"[red]Error: {e}[/]")
        else:
            self.dismiss(None)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update estimate when quantity changes"""
        try:
            quantity = int(event.value)
            estimate = self.query_one("#estimate", Static)
            estimate.update(f"Estimated cost: ~₹{quantity * 2000:,.2f} (example)")
        except:
            pass
```

### 4. UPDATE `src/tui/screens/main_screen.py`
```python
# Add imports
from src.tui.screens.trade_modal import TradeModal
from src.engine.trade_executor import TradeExecutor, OrderSide

# Update BINDINGS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "menu", "Menu"),
        ("s", "save", "Save"),
        ("t", "trade", "Trade"),  # NEW
        ("space", "advance_day", "Next Day"),  # NEW
    ]

# Add these methods
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
        else:  # SELL
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
            # Auto-save after trade
            import asyncio
            asyncio.create_task(self.app._save_current_game())
        else:
            self.app.notify(result.message, severity="error")

    def action_advance_day(self) -> None:
        """Advance game by one day"""
        self.game_state.current_day += 1

        # Update prices for all positions
        for position in self.game_state.portfolio.positions:
            # Get price from N days ago
            days_ago = self.game_state.total_days - self.game_state.current_day
            new_price = self.app.market_data.get_price_at_day(position.symbol, days_ago)
            if new_price > 0:
                position.current_price = new_price

        self._refresh_display()
        self.app.notify(f"Advanced to day {self.game_state.current_day}")

        # Auto-save
        import asyncio
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
```

### 5. UPDATE `src/tui/app.tcss`
```css
/* Add modal styles */
#trade-modal {
    width: 60;
    height: auto;
    border: thick $primary;
    background: $surface;
    padding: 1 2;
}

#modal-title {
    text-align: center;
    text-style: bold;
    color: $accent;
}

#cash-display {
    text-align: center;
    color: $success;
    padding-bottom: 1;
}

Label {
    padding-top: 1;
}

Input, Select {
    margin-bottom: 1;
}

#estimate {
    padding: 1 0;
    text-align: center;
}

Horizontal {
    align: center middle;
    height: auto;
}

Horizontal Button {
    margin: 1;
}
```

---

## Qwen Coder Prompt for Stage 4

```
CONTEXT:
- Stage 3 working with real market data
- Now implementing full trading functionality
- Use TradeExecutor for all buy/sell logic
- Trade modal provides UI for order entry

TASK:
1. Create src/engine/__init__.py
2. Create src/engine/trade_executor.py (TradeExecutor class)
3. Create src/tui/screens/trade_modal.py (TradeModal screen)
4. Update src/tui/screens/main_screen.py (add trade and advance_day actions)
5. Update src/tui/app.tcss (add modal styles)

CRITICAL RULES:
- Validate sufficient funds before buy
- Validate sufficient quantity before sell
- Calculate commission (0.03% or ₹20 max)
- Update portfolio immediately after trade
- Auto-save after each trade
- Update all prices on day advance

VALIDATION:
1. Run: python -m src.main
2. Start/load game
3. Press 't' - trade modal opens
4. Select stock, BUY, quantity 10
5. Click Execute
6. Verify: cash decreased, position added, notification shown
7. Press 't' again, SELL 5 shares
8. Verify: cash increased, quantity reduced
9. Press SPACE - advance day
10. Verify: day counter increments, prices update
11. Verify: game auto-saves after trades

EXPECTED OUTPUT:
- Trade modal works
- Buy/sell execute correctly
- Portfolio updates instantly
- Day advance works
- Prices change on day advance
- Auto-save after operations
```

---

## Validation Checklist

- [ ] Trade modal opens with 't'
- [ ] Can buy stocks
- [ ] Cash decreases correctly
- [ ] Commission calculated
- [ ] Position added/updated
- [ ] Can sell stocks
- [ ] Cash increases on sell
- [ ] Can advance day
- [ ] Prices update on day advance
- [ ] Auto-saves work

---

## Next: Stage 5 adds AI coach

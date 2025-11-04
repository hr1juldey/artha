# Stage 6: Polish & Production Ready

**Duration**: 2 hours (Hours 10-12)
**Status**: Final Polish
**Depends On**: Stage 5 complete and working

---

## Objective

Production-ready game with:
- Comprehensive error handling
- Input validation
- Help system
- Testing
- Performance optimization
- Final bug fixes

---

## Success Criteria

- [ ] All error paths handled
- [ ] Input validation everywhere
- [ ] Help screen works
- [ ] No known bugs
- [ ] Performance acceptable
- [ ] Clean code organization
- [ ] Ready for players

---

## Tasks

### 1. Error Handling

#### UPDATE `src/engine/trade_executor.py`
Add validation:
```python
@staticmethod
def validate_trade_inputs(
    symbol: str,
    quantity: int,
    price: float
) -> tuple[bool, str]:
    """Validate trade inputs"""
    if not symbol or len(symbol) == 0:
        return False, "Symbol cannot be empty"

    if quantity <= 0:
        return False, "Quantity must be positive"

    if quantity > 10000:
        return False, "Quantity too large (max 10,000)"

    if price <= 0:
        return False, "Price must be positive"

    if price > 100000:
        return False, "Price unrealistic (>₹1L)"

    return True, "OK"
```

### 2. Help Screen

#### CREATE `src/tui/screens/help_screen.py`
```python
"""Help screen"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.containers import Container, VerticalScroll

class HelpScreen(Screen):
    """Help and instructions"""

    BINDINGS = [
        ("escape", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            with VerticalScroll():
                yield Static("""
# Artha - Help

## Objective
Learn stock market investing by managing a virtual portfolio over 30 days.

## Controls
- **t**: Open trade dialog (buy/sell stocks)
- **Space**: Advance to next day
- **c**: Get AI coach insights
- **s**: Save game
- **m**: Return to menu
- **q**: Quit
- **h**: Show this help

## How to Play

### Starting Out
1. You start with ₹10,00,000 (10 lakhs)
2. Browse available stocks
3. Execute trades to build portfolio
4. Monitor daily performance

### Trading
1. Press 't' to open trade dialog
2. Select stock, action (buy/sell), and quantity
3. Commission: 0.03% or ₹20 (whichever is less)
4. Trade executes at current market price

### Day Advance
- Press Space to advance one day
- Stock prices update based on historical data
- Your portfolio value changes accordingly

### AI Coach
- Press 'c' for portfolio insights
- Get feedback after each trade
- Learn investing concepts

## Tips
- Diversify across multiple stocks
- Don't invest all cash at once
- Monitor your P&L regularly
- Learn from the AI coach feedback

## Winning
- Beat the market (better than holding cash)
- Finish 30 days with positive returns
- Learn key investing concepts

Press ESC to close help.
                """, id="help-text")

        yield Footer()

    def action_close(self) -> None:
        """Close help screen"""
        self.app.pop_screen()
```

### 3. Input Validation

#### UPDATE `src/tui/screens/trade_modal.py`
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button clicks - ENHANCED"""
    if event.button.id == "execute-btn":
        # Get values
        symbol_select = self.query_one("#symbol-select", Select)
        action_select = self.query_one("#action-select", Select)
        qty_input = self.query_one("#quantity-input", Input)

        if symbol_select.value == Select.BLANK:
            self.query_one("#estimate", Static).update("[red]Please select a stock[/]")
            return

        if action_select.value == Select.BLANK:
            self.query_one("#estimate", Static).update("[red]Please select an action[/]")
            return

        if not qty_input.value or qty_input.value.strip() == "":
            self.query_one("#estimate", Static).update("[red]Please enter quantity[/]")
            return

        try:
            quantity = int(qty_input.value)

            # Validate
            from src.engine.trade_executor import TradeExecutor
            valid, message = TradeExecutor.validate_trade_inputs(
                symbol_select.value, quantity, 100.0  # Price checked later
            )

            if not valid:
                self.query_one("#estimate", Static).update(f"[red]{message}[/]")
                return

            result = {
                "symbol": symbol_select.value,
                "action": action_select.value,
                "quantity": quantity
            }
            self.dismiss(result)

        except ValueError:
            self.query_one("#estimate", Static).update("[red]Invalid quantity[/]")
    else:
        self.dismiss(None)
```

### 4. Performance Monitoring

#### CREATE `src/utils/__init__.py`
```python
"""Utilities package"""
```

#### CREATE `src/utils/performance.py`
```python
"""Performance monitoring"""
import time
from functools import wraps

def time_it(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        if elapsed > 1.0:  # Log slow operations
            print(f"[SLOW] {func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper
```

### 5. Comprehensive Testing

#### CREATE `tests/__init__.py`
```python
"""Test package"""
```

#### CREATE `tests/test_trade_executor.py`
```python
"""Test trade execution"""
import pytest
from src.engine.trade_executor import TradeExecutor
from src.models import Portfolio, Position

def test_buy_success():
    """Test successful buy"""
    portfolio = Portfolio(cash=100000)

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 10, 1000.0
    )

    assert result.success
    assert len(portfolio.positions) == 1
    assert portfolio.positions[0].quantity == 10
    assert portfolio.cash < 100000  # Cash reduced

def test_buy_insufficient_funds():
    """Test buy with insufficient funds"""
    portfolio = Portfolio(cash=100)

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 10, 1000.0
    )

    assert not result.success
    assert "Insufficient funds" in result.message

def test_sell_success():
    """Test successful sell"""
    portfolio = Portfolio(
        cash=50000,
        positions=[Position("TEST", 10, 1000.0, 1100.0)]
    )

    result = TradeExecutor.execute_sell(
        portfolio, "TEST", 5, 1100.0
    )

    assert result.success
    assert portfolio.positions[0].quantity == 5
    assert portfolio.cash > 50000  # Cash increased

def test_sell_insufficient_quantity():
    """Test sell with insufficient quantity"""
    portfolio = Portfolio(
        cash=50000,
        positions=[Position("TEST", 5, 1000.0, 1100.0)]
    )

    result = TradeExecutor.execute_sell(
        portfolio, "TEST", 10, 1100.0
    )

    assert not result.success
    assert "Insufficient quantity" in result.message

def test_commission_calculation():
    """Test commission calculation"""
    # Small trade
    commission = TradeExecutor.calculate_commission(10000)
    assert commission == 3.0  # 0.03% of 10k

    # Large trade
    commission = TradeExecutor.calculate_commission(1000000)
    assert commission == 20.0  # Capped at ₹20
```

### 6. Final Updates

#### UPDATE `src/tui/screens/main_screen.py`
Add help binding:
```python
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "menu", "Menu"),
        ("s", "save", "Save"),
        ("t", "trade", "Trade"),
        ("space", "advance_day", "Next Day"),
        ("c", "coach", "Coach"),
        ("h", "help", "Help"),  # NEW
    ]

    def action_help(self) -> None:
        """Show help screen"""
        from src.tui.screens.help_screen import HelpScreen
        self.app.push_screen(HelpScreen())
```

#### UPDATE `src/tui/app.py`
Add error logging:
```python
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_DIR / "artha.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ArthaApp(App):
    # ... existing code ...

    def on_exception(self, exception: Exception) -> None:
        """Handle exceptions"""
        logger.error(f"Exception: {exception}", exc_info=True)
        self.notify(
            f"An error occurred. Check logs for details.",
            severity="error"
        )
```

### 7. Configuration File

#### CREATE `config.yaml` (in project root)
```yaml
# Artha Configuration

game:
  initial_capital: 1000000
  default_days: 30
  commission_rate: 0.0003

data:
  cache_enabled: true
  cache_duration_hours: 24
  default_stocks:
    - RELIANCE
    - TCS
    - INFY
    - HDFCBANK
    - ICICIBANK

ai:
  enabled: true
  model: "qwen3:8b"
  timeout_seconds: 30
  fallback_on_error: true

display:
  currency_symbol: "₹"
  date_format: "%Y-%m-%d"
  theme: "dark"
```

### 8. README Update

#### UPDATE `README.md`
```markdown
# Artha - Stock Market Learning Simulator

A text-based stock market simulator for learning investing.

## Quick Start

### Prerequisites
- Python 3.12+
- Ollama (optional, for AI coach)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd artha

# Install dependencies
pip install -e .

# Run the game
python -m src.main
```

### Optional: AI Coach

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull qwen3:8b

# Start Ollama
ollama serve
```

## How to Play

1. Start with ₹10,00,000 virtual cash
2. Trade Indian stocks (NSE)
3. Learn from AI coach feedback
4. Complete 30 days with positive returns

## Controls

- `t` - Trade (buy/sell)
- `Space` - Advance day
- `c` - Coach insights
- `s` - Save game
- `h` - Help
- `q` - Quit

## Features

- Real historical stock data (yfinance)
- AI coach powered by DSPy + Ollama
- Portfolio tracking and analysis
- Save/load games
- Educational feedback

## Testing

```bash
pytest tests/
```

## License

MIT
```

---

## Qwen Coder Prompt for Stage 6

```
CONTEXT:
- Stage 5 complete with AI coach
- Final polish for production release
- Add error handling, validation, help, tests

TASK:
1. Update src/engine/trade_executor.py (add validate_trade_inputs)
2. Create src/tui/screens/help_screen.py (comprehensive help)
3. Update src/tui/screens/trade_modal.py (add input validation)
4. Create src/utils/performance.py (performance monitoring)
5. Create tests/test_trade_executor.py (unit tests)
6. Update src/tui/screens/main_screen.py (add help action)
7. Update src/tui/app.py (add error logging)
8. Create config.yaml (configuration file)
9. Update README.md (comprehensive docs)

CRITICAL RULES:
- Validate ALL user inputs
- Handle ALL error cases
- Log errors don't crash
- Help screen accessible with 'h'
- Tests must pass
- README must be clear

VALIDATION:
1. Run: pytest tests/
2. All tests pass
3. Run: python -m src.main
4. Test all error paths:
   - Enter invalid quantity (negative, zero, too large)
   - Try to sell more than owned
   - Try to buy without sufficient cash
5. Press 'h' - help displays
6. All functionality works smoothly
7. No crashes under any normal use
8. Check artha.log has proper logging

EXPECTED OUTPUT:
- All tests pass
- Input validation works
- Help screen comprehensive
- Error handling robust
- Logging functional
- Game stable and polished
```

---

## Final Validation Checklist

### Functionality
- [ ] All stages 1-5 work correctly
- [ ] Help screen displays
- [ ] All controls work
- [ ] Save/load works
- [ ] Trading works
- [ ] AI coach works (or falls back gracefully)

### Error Handling
- [ ] Invalid inputs rejected
- [ ] Helpful error messages
- [ ] No crashes on errors
- [ ] Errors logged properly

### Performance
- [ ] App starts quickly (<5s)
- [ ] Trades execute fast (<1s)
- [ ] Day advance smooth
- [ ] No lag in UI

### User Experience
- [ ] Controls intuitive
- [ ] Feedback clear
- [ ] Help comprehensive
- [ ] Visual layout clean

### Testing
- [ ] Unit tests pass
- [ ] Manual testing complete
- [ ] Edge cases covered
- [ ] No known bugs

---

## Game Complete!

After Stage 6, you have a fully functional, production-ready stock market learning simulator!

**Key Achievements:**
- ✅ Working TUI with multiple screens
- ✅ Database persistence
- ✅ Real market data integration
- ✅ Full trading engine
- ✅ AI coach with DSPy + Ollama
- ✅ Comprehensive error handling
- ✅ Help system
- ✅ Tests
- ✅ Documentation

**Total Time:** 12 hours
**Result:** Playable, stable, educational game

🎉 Congratulations!

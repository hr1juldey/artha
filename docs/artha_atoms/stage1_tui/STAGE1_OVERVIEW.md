# Stage 1: Minimal TUI Prototype

**Duration**: 2 hours (Hours 0-2)
**Status**: Foundation
**Criticality**: HIGHEST - Everything builds on this

---

## Objective

Create a minimal but fully functional Textual TUI application with:

- Basic app structure
- Multiple screens (menu, game)
- Mock data display
- Keyboard navigation
- Clean exit handling

**No database yet** - use in-memory mock data only.

---

## Success Criteria

- [ ] App launches with `python -m src.main`
- [ ] Can navigate between menu and game screens
- [ ] Portfolio displays with mock data (3-5 stocks)
- [ ] Keyboard shortcuts work (q=quit, m=menu, p=portfolio)
- [ ] No crashes or errors
- [ ] Clean terminal on exit

---

## Reference Materials

**Primary Examples**:

1. `example_code/textual/calculator.py` - App structure
2. `example_code/textual/code_browser.py` - Screen navigation
3. `example_code/dspy_toys/dspy_text_RPG_game.py` - Game state management

**Key Patterns to Copy**:

- App class with BINDINGS
- Screen composition
- State management
- Rich formatting for tables

---

## Files to Create

### 1. `src/__init__.py`

```python
"""Artha - Stock Market Learning Simulator"""
__version__ = "0.1.0"
```

### 2. `src/config.py`

```python
"""Configuration settings"""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "artha.db"

# Game settings
INITIAL_CAPITAL = 1_000_000  # ₹10 lakhs
COMMISSION_RATE = 0.0003  # 0.03%

# Display settings
CURRENCY_SYMBOL = "₹"
DATE_FORMAT = "%Y-%m-%d"
```

### 3. `src/models/__init__.py`

```python
"""Data models (Pydantic, not SQLAlchemy yet)"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class Position:
    """Single stock position"""
    symbol: str
    quantity: int
    avg_buy_price: float
    current_price: float

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_buy_price

    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        return (self.unrealized_pnl / self.cost_basis) * 100 if self.cost_basis > 0 else 0.0

@dataclass
class Portfolio:
    """User's portfolio"""
    cash: float
    positions: List[Position] = field(default_factory=list)

    @property
    def positions_value(self) -> float:
        return sum(p.market_value for p in self.positions)

    @property
    def total_value(self) -> float:
        return self.cash + self.positions_value

    @property
    def invested(self) -> float:
        return sum(p.cost_basis for p in self.positions)

    @property
    def total_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self.positions)

@dataclass
class GameState:
    """Current game state"""
    player_name: str
    current_day: int
    total_days: int
    initial_capital: float
    portfolio: Portfolio
    created_at: datetime = field(default_factory=datetime.now)
```

### 4. `src/tui/widgets/portfolio_grid.py`

```python
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
```

### 5. `src/tui/screens/main_screen.py`

```python
"""Main game screen"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Vertical
from src.tui.widgets.portfolio_grid import PortfolioGrid
from src.models import GameState

class MainScreen(Screen):
    """Main game screen with portfolio display"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "menu", "Menu"),
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
```

### 6. `src/tui/screens/menu_screen.py`

```python
"""Menu screen"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Container, Vertical

class MenuScreen(Screen):
    """Main menu screen"""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()

        with Container(id="menu-container"):
            with Vertical(id="menu-options"):
                yield Static("# Artha", id="title")
                yield Static("Stock Market Learning Simulator", id="subtitle")
                yield Button("New Game", id="new-game", variant="success")
                yield Button("Continue", id="continue", disabled=True)
                yield Button("Quit", id="quit-btn", variant="error")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "new-game":
            self.app.push_screen("main")
        elif event.button.id == "quit-btn":
            self.app.exit()

    def action_quit(self) -> None:
        """Quit application"""
        self.app.exit()
```

### 7. `src/tui/app.py`

```python
"""Main Textual application"""
from textual.app import App, ComposeResult
from textual.binding import Binding
from src.tui.screens.menu_screen import MenuScreen
from src.tui.screens.main_screen import MainScreen
from src.models import GameState, Portfolio, Position
from src.config import INITIAL_CAPITAL

class ArthaApp(App):
    """Artha TUI Application"""

    CSS_PATH = "app.tcss"
    TITLE = "Artha - Stock Market Simulator"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.game_state = self._create_mock_game()

    def _create_mock_game(self) -> GameState:
        """Create mock game state with fake data"""
        # Mock portfolio with 3 positions
        positions = [
            Position(
                symbol="RELIANCE",
                quantity=50,
                avg_buy_price=2450.00,
                current_price=2520.00
            ),
            Position(
                symbol="TCS",
                quantity=30,
                avg_buy_price=3200.00,
                current_price=3180.00
            ),
            Position(
                symbol="INFY",
                quantity=100,
                avg_buy_price=1450.00,
                current_price=1520.00
            ),
        ]

        # Calculate remaining cash
        invested = sum(p.cost_basis for p in positions)
        cash = INITIAL_CAPITAL - invested

        portfolio = Portfolio(cash=cash, positions=positions)

        return GameState(
            player_name="Demo Player",
            current_day=5,
            total_days=30,
            initial_capital=INITIAL_CAPITAL,
            portfolio=portfolio
        )

    def on_mount(self) -> None:
        """Initialize app"""
        self.install_screen(MenuScreen(), name="menu")
        self.install_screen(MainScreen(self.game_state), name="main")
        self.push_screen("menu")
```

### 8. `src/tui/app.tcss`

```css
/* Textual CSS for styling */

Screen {
    align: center middle;
}

#menu-container {
    width: 60;
    height: auto;
    border: thick $background 80%;
    background: $surface;
    padding: 2 4;
}

#menu-options {
    width: 100%;
    height: auto;
}

#title {
    text-align: center;
    text-style: bold;
    color: $accent;
}

#subtitle {
    text-align: center;
    color: $text-muted;
    padding-bottom: 2;
}

Button {
    width: 100%;
    margin: 1 0;
}

#status {
    dock: top;
    height: 3;
    content-align: center middle;
    background: $boost;
    border-bottom: solid $primary;
}

.section-title {
    text-style: bold;
    color: $accent;
    padding: 1 0;
}

DataTable {
    height: 1fr;
}
```

### 9. `src/main.py`

```python
"""Entry point for Artha application"""
from src.tui.app import ArthaApp

def main():
    """Run the application"""
    app = ArthaApp()
    app.run()

if __name__ == "__main__":
    main()
```

---

## Qwen Coder Prompt for Stage 1

```bash
CONTEXT:
- You are implementing Stage 1 of the Artha stock market simulator
- This is a Textual TUI application
- Use only in-memory mock data (no database yet)
- Reference: example_code/textual/calculator.py and code_browser.py

TASK:
Create the following files in order:
1. src/__init__.py (package marker)
2. src/config.py (configuration constants)
3. src/models/__init__.py (Pydantic dataclasses: Position, Portfolio, GameState)
4. src/tui/widgets/__init__.py (empty)
5. src/tui/widgets/portfolio_grid.py (DataTable widget)
6. src/tui/screens/__init__.py (empty)
7. src/tui/screens/menu_screen.py (menu with buttons)
8. src/tui/screens/main_screen.py (main game screen)
9. src/tui/__init__.py (empty)
10. src/tui/app.py (main App class with mock data)
11. src/tui/app.tcss (CSS styling)
12. src/main.py (entry point)

SPECIFICATIONS:
- Copy the EXACT code provided in STAGE1_OVERVIEW.md
- Ensure all imports are correct
- Use dataclasses (not SQLAlchemy) for models
- Mock data: 3 stock positions with realistic prices
- Portfolio should show P&L in green (profit) or red (loss)

VALIDATION:
After implementation, test:
1. Run: python -m src.main
2. Verify menu screen appears
3. Click "New Game" button
4. Verify main screen shows with portfolio table
5. Verify 3 stocks are displayed with P&L
6. Press 'm' to return to menu
7. Press 'q' to quit cleanly

EXPECTED OUTPUT:
- Clean launch with no errors
- Menu screen with 3 buttons
- Main screen with status bar and portfolio table
- Colored P&L (green/red)
- Keyboard shortcuts work

ERROR HANDLING:
- If Textual import fails: check pyproject.toml has textual>=6.4.0
- If CSS not loading: ensure app.tcss is in src/tui/ folder
- If widgets not showing: check compose() methods return ComposeResult
```

---

## Validation Checklist

After Qwen Coder completes:

- [ ] All files created in correct locations
- [ ] No syntax errors
- [ ] All imports resolve
- [ ] App launches with `python -m src.main`
- [ ] Menu screen displays
- [ ] Can start new game
- [ ] Portfolio table shows 3 stocks
- [ ] P&L colors work (green/red)
- [ ] Status bar shows correct values
- [ ] Keyboard shortcuts work
- [ ] Can quit cleanly with 'q'
- [ ] No console errors

---

## Common Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'src'"

**Fix**: Run from project root: `cd /path/to/artha && python -m src.main`

### Issue: CSS not loading

**Fix**: Check app.tcss path in ArthaApp.CSS_PATH

### Issue: Widgets not displaying

**Fix**: Ensure all compose() methods use `yield` not `return`

### Issue: Colors not working

**Fix**: Use Rich markup: `[green]text[/]` or `[red]text[/]`

---

## Next Stage Preview

Stage 2 will add:

- SQLAlchemy models
- Database persistence
- Save/Load functionality

But Stage 1 must work perfectly first!

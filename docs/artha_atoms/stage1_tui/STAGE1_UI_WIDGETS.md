# Stage 1: UI Widgets & Components Specification

## **Complete widget selection and layout design for Stage 1 TUI**

---

## Widget Selection from Textual Gallery

### Primary Widgets Used

| Widget | Purpose in Artha | Properties | Import From |
|--------|------------------|------------|-------------|
| **Header** | App title and subtitle | Shows "Artha" + status | `textual.widgets` |
| **Footer** | Key bindings display | Auto-shows BINDINGS | `textual.widgets` |
| **DataTable** | Portfolio grid | Rows, columns, cursors | `textual.widgets` |
| **Button** | Menu actions | Variants: success/error | `textual.widgets` |
| **Static** | Text display | Status bar, titles | `textual.widgets` |
| **Container** | Layout wrapper | Groups widgets | `textual.containers` |
| **Vertical** | Vertical layout | Stack widgets | `textual.containers` |
| **Horizontal** | Horizontal layout | Side-by-side | `textual.containers` |

### Widgets NOT Used (Yet)

Stage 1 keeps it simple. These will be added in later stages:

- **Input** - Stage 4 (trade quantity)
- **Select** - Stage 4 (stock picker)
- **Tabs** - Stage 6 (multiple views)
- **ProgressBar** - Stage 3 (data loading)
- **Markdown** - Stage 6 (help)
- **Tree** - Future (stock categories)

---

## Screen Layouts

### 1. Menu Screen Layout

```bash
┌─────────────────────────────────────────────────────┐
│ Header: Artha - Stock Market Simulator              │
├─────────────────────────────────────────────────────┤
│                                                     │
│                    ┌─────────────┐                  │
│                    │             │                  │
│                    │   # Artha   │  ← Static        │
│                    │             │                  │
│                    │ Stock Market│  ← Static        │
│                    │  Simulator  │                  │
│                    │             │                  │
│                    │ ┌─────────┐ │                  │
│                    │ │New Game │ │  ← Button        │
│                    │ └─────────┘ │                  │
│                    │             │                  │
│                    │ ┌─────────┐ │                  │
│                    │ │Continue │ │  ← Button        │
│                    │ └─────────┘ │  (disabled)      │
│                    │             │                  │
│                    │ ┌─────────┐ │                  │
│                    │ │  Quit   │ │  ← Button        │
│                    │ └─────────┘ │                  │
│                    │             │                  │
│                    └─────────────┘                  │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Footer: [q]uit                                      │
└─────────────────────────────────────────────────────┘

Container hierarchy:
- Screen
  - Header
  - Container (id="menu-container")
    - Vertical (id="menu-options")
      - Static (id="title") "# Artha"
      - Static (id="subtitle") "Stock Market..."
      - Button (id="new-game") variant=success
      - Button (id="continue") disabled=True
      - Button (id="quit-btn") variant=error
  - Footer
```

### 2. Main Game Screen Layout

```bash
┌─────────────────────────────────────────────────────────────┐
│ Header: Artha - Playing                                     │
├─────────────────────────────────────────────────────────────┤
│ Status: Player | Day: 5/30 | Cash: ₹850,000 | Total: ₹1M    │ ← Static
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ## Portfolio                                  ← Static      │
│                                                             │
│ ┌─────────┬─────┬──────────┬──────────┬─────────┬────────┐  │
│ │ Symbol  │ Qty │ Avg Price│ Current  │   P&L   │ Change │  │
│ ├─────────┼─────┼──────────┼──────────┼─────────┼────────┤  │
│ │RELIANCE │  50 │  ₹2,450  │  ₹2,520  │  ₹3,500 │ +2.9%  │  │ ← DataTable
│ │  TCS    │  30 │  ₹3,200  │  ₹3,180  │   -₹600 │ -0.6%  │  │
│ │  INFY   │ 100 │  ₹1,450  │  ₹1,520  │  ₹7,000 │ +4.8%  │  │
│ └─────────┴─────┴──────────┴──────────┴─────────┴────────┘  │
│                                                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Footer: [t]rade [Space]Next Day [m]enu [s]ave [q]uit        │
└─────────────────────────────────────────────────────────────┘

Container hierarchy:
- Screen
  - Header
  - Container
    - Static (id="status") dock=top
    - Vertical
      - Static (classes="section-title") "## Portfolio"
      - PortfolioGrid (custom DataTable)
  - Footer
```

---

## Widget Configurations

### Header Widget

```python
from textual.widgets import Header

# Usage in Screen.compose():
yield Header()

# Properties (auto-managed):
# - Shows app.TITLE
# - Can show subtitle
# - Clock (optional)
```

**Configuration in App:**

```python
class ArthaApp(App):
    TITLE = "Artha - Stock Market Simulator"
    SUB_TITLE = "Learn Investing"  # Optional
```

### Footer Widget

```python
from textual.widgets import Footer

# Usage in Screen.compose():
yield Footer()

# Auto-displays from BINDINGS:
# [q]uit [t]rade [m]enu etc.
```

**Bindings Configuration:**

```python
BINDINGS = [
    ("q", "quit", "Quit"),
    ("t", "trade", "Trade"),
    ("space", "advance_day", "Next Day"),
]
# Format: (key, action, description)
```

### DataTable Widget

```python
from textual.widgets import DataTable

class PortfolioGrid(DataTable):
    def on_mount(self) -> None:
        # Add columns
        self.add_columns(
            "Symbol",      # Column 1
            "Qty",         # Column 2
            "Avg Price",   # Column 3
            "Current",     # Column 4
            "P&L",         # Column 5
            "% Change"     # Column 6
        )

        # Configure appearance
        self.cursor_type = "row"      # Highlight full row
        self.zebra_stripes = True     # Alternating colors
        self.show_cursor = True       # Visible cursor

    def update_portfolio(self, portfolio: Portfolio):
        self.clear()  # Remove old data

        for position in portfolio.positions:
            # Color based on profit/loss
            pnl_color = "green" if position.unrealized_pnl > 0 else "red"

            # Add row with formatted data
            self.add_row(
                position.symbol,                              # Plain text
                str(position.quantity),                       # Plain text
                f"₹{position.avg_buy_price:,.2f}",           # Formatted
                f"₹{position.current_price:,.2f}",           # Formatted
                f"[{pnl_color}]₹{position.unrealized_pnl:,.2f}[/]",  # Colored
                f"[{pnl_color}]{position.unrealized_pnl_pct:+.2f}%[/]"  # Colored
            )
```

**Key DataTable Properties:**

- `cursor_type`: "cell", "row", "column", "none"
- `zebra_stripes`: bool - alternating row colors
- `show_header`: bool - show column headers
- `show_cursor`: bool - highlight selection
- `fixed_rows`: int - freeze top N rows
- `fixed_columns`: int - freeze left N columns

### Button Widget

```python
from textual.widgets import Button

# Basic button
Button("Click me", id="my-button")

# With variant (color scheme)
Button("New Game", id="new-game", variant="success")  # Green
Button("Quit", id="quit-btn", variant="error")        # Red
Button("Continue", id="continue", variant="primary")   # Blue

# Disabled
Button("Continue", id="continue", disabled=True)

# Variants available:
# - default (gray)
# - primary (blue)
# - success (green)
# - warning (yellow)
# - error (red)
```

**Button Events:**

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "new-game":
        # Handle new game
        pass
```

### Static Widget

```python
from textual.widgets import Static

# Simple text
Static("Hello World")

# With ID for updates
Static("Cash: ₹1,000,000", id="status")

# With classes for styling
Static("## Portfolio", classes="section-title")

# With Rich markup
Static("[bold]Player Name[/bold] | [green]₹1,000,000[/green]")

# Update dynamically
status = self.query_one("#status", Static)
status.update(f"New text: {value}")
```

**Rich Markup in Static:**

```python
# Colors
"[red]Error[/]"
"[green]Success[/]"
"[yellow]Warning[/]"
"[blue]Info[/]"

# Styles
"[bold]Bold text[/]"
"[italic]Italic text[/]"
"[underline]Underlined[/]"

# Combined
"[bold green]Success![/]"
"[italic red]Error message[/]"
```

### Container Widgets

```python
from textual.containers import Container, Vertical, Horizontal

# Container - generic wrapper
with Container(id="my-container"):
    yield Widget1()
    yield Widget2()

# Vertical - stack vertically
with Vertical(id="menu-options"):
    yield Button("Option 1")
    yield Button("Option 2")
    yield Button("Option 3")

# Horizontal - side by side
with Horizontal():
    yield Button("Cancel")
    yield Button("OK")
```

**Container CSS Properties:**

- `align`: horizontal vertical - alignment
- `border`: line style for borders
- `padding`: spacing inside
- `margin`: spacing outside
- `width/height`: size constraints

---

## Complete Project Structure

```bash
artha/
├── src/
│   ├── __init__.py                  # Package marker
│   │   └── Contains: __version__ = "0.1.0"
│   │
│   ├── config.py                    # Global configuration
│   │   └── Contains:
│   │       - Path constants (PROJECT_ROOT, DATA_DIR, DB_PATH)
│   │       - Game settings (INITIAL_CAPITAL, COMMISSION_RATE)
│   │       - Display settings (CURRENCY_SYMBOL, DATE_FORMAT)
│   │
│   ├── main.py                      # Entry point
│   │   └── Contains:
│   │       - main() function
│   │       - Instantiates and runs ArthaApp
│   │
│   ├── models/                      # Data models (Pydantic)
│   │   ├── __init__.py
│   │   │   └── Exports: Position, Portfolio, GameState
│   │   │
│   │   └── Contains dataclasses:
│   │       - Position: single stock position
│   │       - Portfolio: collection of positions + cash
│   │       - GameState: complete game state
│   │
│   └── tui/                         # Terminal UI package
│       ├── __init__.py              # Empty
│       │
│       ├── app.py                   # Main Textual application
│       │   └── Contains:
│       │       - ArthaApp(App) class
│       │       - CSS_PATH reference
│       │       - BINDINGS for keyboard
│       │       - _create_mock_game() for demo data
│       │       - Screen installation
│       │
│       ├── app.tcss                 # Textual CSS stylesheet
│       │   └── Contains:
│       │       - Screen styling
│       │       - Container layouts
│       │       - Button styles
│       │       - DataTable appearance
│       │       - Color schemes
│       │
│       ├── screens/                 # Screen definitions
│       │   ├── __init__.py          # Empty
│       │   │
│       │   ├── menu_screen.py       # Main menu
│       │   │   └── Contains:
│       │   │       - MenuScreen(Screen) class
│       │   │       - compose() with buttons
│       │   │       - on_button_pressed() handler
│       │   │       - BINDINGS
│       │   │
│       │   └── main_screen.py       # Game screen
│       │       └── Contains:
│       │           - MainScreen(Screen) class
│       │           - compose() with portfolio
│       │           - on_mount() to load data
│       │           - action_* methods
│       │           - BINDINGS
│       │
│       └── widgets/                 # Custom widgets
│           ├── __init__.py          # Empty
│           │
│           └── portfolio_grid.py    # Portfolio table
│               └── Contains:
│                   - PortfolioGrid(DataTable) class
│                   - on_mount() for column setup
│                   - update_portfolio() method
│
├── data/                            # Runtime data (created at runtime)
│   └── .gitkeep                     # Keep folder in git
│
├── tests/                           # Tests (Stage 6)
│   └── __init__.py
│
├── docs/                            # Documentation
│   └── (existing docs)
│
├── pyproject.toml                   # Dependencies (already exists)
├── README.md                        # Project readme
└── .gitignore                       # Git ignore rules
```

---

## File Dependencies & Import Graph

```bash
main.py
  └─> tui.app.ArthaApp
      ├─> tui.screens.MenuScreen
      │   └─> textual.widgets.{Header, Footer, Button, Static}
      │   └─> textual.containers.{Container, Vertical}
      │
      ├─> tui.screens.MainScreen
      │   ├─> tui.widgets.PortfolioGrid
      │   │   └─> textual.widgets.DataTable
      │   │   └─> models.Portfolio
      │   │
      │   └─> textual.widgets.{Header, Footer, Static}
      │   └─> textual.containers.{Container, Vertical}
      │
      ├─> models.{Position, Portfolio, GameState}
      └─> config (constants)
```

---

## Widget Styling via CSS

### Color Scheme

```css
/* app.tcss - Color Variables */

/* Available color variables in Textual:
   $primary - Primary theme color
   $secondary - Secondary theme color
   $accent - Accent color
   $success - Success/positive (green)
   $warning - Warning (yellow)
   $error - Error/negative (red)
   $surface - Surface background
   $background - Main background
   $boost - Slightly lighter background
   $text - Main text color
   $text-muted - Dimmed text
   $text-disabled - Disabled text
*/
```

### CSS Rules Used

```css
/* Screen-level */
Screen {
    align: center middle;  /* Center content */
}

/* Containers */
#menu-container {
    width: 60;                    /* 60 columns wide */
    height: auto;                 /* Auto height */
    border: thick $background 80%;/* Thick border */
    background: $surface;         /* Surface color */
    padding: 2 4;                 /* Padding: top/bottom left/right */
}

/* Buttons */
Button {
    width: 100%;      /* Full width of container */
    margin: 1 0;      /* Margin: top/bottom left/right */
}

/* Status bar */
#status {
    dock: top;                    /* Dock to top */
    height: 3;                    /* 3 rows tall */
    content-align: center middle; /* Center text */
    background: $boost;           /* Lighter bg */
    border-bottom: solid $primary;/* Bottom border */
}

/* DataTable */
DataTable {
    height: 1fr;      /* Fill remaining space */
}
```

---

## Textual Event System

### Event Types Used in Stage 1

| Event | Trigger | Handler Method |
|-------|---------|----------------|
| `Mount` | Widget added to app | `on_mount()` |
| `Button.Pressed` | Button clicked | `on_button_pressed(event)` |
| `Key` | Keyboard input | Handled by BINDINGS |
| `Resize` | Terminal resized | Auto-handled |

### Event Flow Example

```python
# User presses 'q' key
1. Textual checks BINDINGS
2. Finds: ("q", "quit", "Quit")
3. Calls: action_quit()
4. Method executes: self.app.exit()
5. App shuts down
```

### Button Event Handling

```python
class MenuScreen(Screen):
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when any button is pressed"""
        # event.button is the Button widget
        # event.button.id is the button's ID

        if event.button.id == "new-game":
            # Handle new game
            self.app.push_screen("main")
        elif event.button.id == "continue":
            # Handle continue
            pass
        elif event.button.id == "quit-btn":
            # Handle quit
            self.app.exit()
```

---

## Mock Data Structure

For Stage 1, we use in-memory mock data:

```python
def _create_mock_game(self) -> GameState:
    """Create demonstration game state"""

    # Mock positions (3 stocks)
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

    # Calculate invested amount
    invested = sum(p.cost_basis for p in positions)
    # invested = (50*2450) + (30*3200) + (100*1450)
    # invested = 122,500 + 96,000 + 145,000 = 363,500

    # Remaining cash
    cash = INITIAL_CAPITAL - invested
    # cash = 1,000,000 - 363,500 = 636,500

    # Create portfolio
    portfolio = Portfolio(
        cash=636500,
        positions=positions
    )

    # Portfolio metrics (auto-calculated):
    # positions_value = (50*2520) + (30*3180) + (100*1520)
    #                 = 126,000 + 95,400 + 152,000 = 373,400
    # total_value = 636,500 + 373,400 = 1,009,900
    # total_pnl = 373,400 - 363,500 = 9,900
    # pnl_pct = (9,900 / 363,500) * 100 = 2.72%

    return GameState(
        player_name="Demo Player",
        current_day=5,
        total_days=30,
        initial_capital=1_000_000,
        portfolio=portfolio,
        created_at=datetime.now()
    )
```

---

## Keyboard Bindings

### Global Bindings (App level)

```python
class ArthaApp(App):
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
```

### Menu Screen Bindings

```python
class MenuScreen(Screen):
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def action_quit(self) -> None:
        self.app.exit()
```

### Main Game Screen Bindings

```python
class MainScreen(Screen):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "menu", "Menu"),
        ("s", "save", "Save"),
    ]

    def action_quit(self) -> None:
        self.app.exit()

    def action_menu(self) -> None:
        self.app.pop_screen()  # Go back to menu

    def action_save(self) -> None:
        self.app.notify("Save not implemented yet")
```

---

## Component Interaction Flow

### Menu to Game Transition

```bash
User clicks "New Game" button
  │
  ├─> Button.Pressed event fires
  │
  ├─> on_button_pressed() called
  │
  ├─> Check: event.button.id == "new-game"
  │
  ├─> Execute: self.app.push_screen("main")
  │
  ├─> Textual shows MainScreen
  │
  ├─> MainScreen.on_mount() called
  │
  ├─> Load game_state from app
  │
  ├─> Update PortfolioGrid with data
  │
  └─> Screen rendered
```

### Portfolio Update Flow

```bash
MainScreen.on_mount()
  │
  ├─> query_one(PortfolioGrid)
  │
  ├─> portfolio_grid.update_portfolio(game_state.portfolio)
  │
  ├─> PortfolioGrid.clear() - remove old rows
  │
  ├─> For each position:
  │   ├─> Calculate P&L color (green/red)
  │   ├─> Format values (₹1,234.56)
  │   └─> Add row with add_row()
  │
  └─> DataTable renders automatically
```

---

## Testing Checklist

### Visual Tests (Manual)

- [ ] Menu screen displays correctly
- [ ] Title and subtitle visible
- [ ] All 3 buttons present
- [ ] "New Game" is green
- [ ] "Quit" is red
- [ ] "Continue" is disabled (gray)
- [ ] Clicking "New Game" shows game screen
- [ ] Game screen shows status bar
- [ ] Portfolio table displays
- [ ] 3 stocks visible (RELIANCE, TCS, INFY)
- [ ] Green P&L for RELIANCE (profit)
- [ ] Red P&L for TCS (loss)
- [ ] Green P&L for INFY (profit)
- [ ] Footer shows key bindings
- [ ] 'q' key quits app
- [ ] 'm' key returns to menu

### Functional Tests

- [ ] App launches without errors
- [ ] No import errors
- [ ] No attribute errors
- [ ] Data displays correctly
- [ ] Calculations accurate
- [ ] Navigation works
- [ ] Exit is clean

---

## Common Widget Patterns

### Pattern 1: Dynamic Text Updates

```python
# Get widget reference
status = self.query_one("#status", Static)

# Update its content
status.update(f"New status: {value}")
```

### Pattern 2: Table Row Updates

```python
# Clear existing data
table.clear()

# Add new rows
for item in items:
    table.add_row(col1, col2, col3)
```

### Pattern 3: Button State Changes

```python
# Get button
button = self.query_one("#continue", Button)

# Enable/disable
button.disabled = False
```

### Pattern 4: Screen Navigation

```python
# Push new screen (can go back)
self.app.push_screen("screen_name")

# Pop current screen (go back)
self.app.pop_screen()

# Switch screen (can't go back)
self.app.switch_screen("screen_name")

# Exit app
self.app.exit()
```

---

## Widget Property Reference

### DataTable Quick Reference

```python
# Creation
table = DataTable()

# Setup
table.add_columns("Col1", "Col2", "Col3")
table.cursor_type = "row"
table.zebra_stripes = True

# Data
table.add_row("val1", "val2", "val3")
table.clear()  # Remove all rows

# Styling
# Use Rich markup in values:
table.add_row(
    "Plain",
    "[green]Colored[/]",
    "[bold]Bold[/]"
)
```

### Button Quick Reference

```python
# Variants
Button("Text", variant="default")   # Gray
Button("Text", variant="primary")   # Blue
Button("Text", variant="success")   # Green
Button("Text", variant="warning")   # Yellow
Button("Text", variant="error")     # Red

# States
button.disabled = True
button.disabled = False

# Events
def on_button_pressed(self, event: Button.Pressed):
    if event.button.id == "my-button":
        pass
```

### Static Quick Reference

```python
# Creation
Static("Plain text")
Static("[bold]Rich markup[/]")

# Update
widget.update("New content")

# Styling
Static("Text", classes="my-class")
Static("Text", id="my-id")
```

---

## Next Steps After Stage 1

Once Stage 1 is working, Stage 2 will add:

- **Input** widgets for user data entry
- **Select** widgets for dropdown choices
- **Modal screens** for dialogs
- More complex layouts

But for now, keep it simple with just these widgets:
✅ Header
✅ Footer
✅ DataTable
✅ Button
✅ Static
✅ Container/Vertical/Horizontal

**Total widget types: 7** - Very manageable for Stage 1!

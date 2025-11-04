# ISSUE 1: CORRECT FIX - Escape Key Not Working

## Problem Diagnosis

The escape binding was added but **IT'S NOT WORKING** because:

1. **Input/Select widgets capture Escape first** - When these widgets have focus, they consume the Escape key
2. **Need to use `app.pop_screen` action** - This is the Textual built-in action that works correctly

## The Real Fix

**File:** `src/tui/screens/trade_modal.py`

### Change Line 12 from

```python
BINDINGS = [
    ("escape", "dismiss_modal", "Cancel"),
]
```

### To

```python
BINDINGS = [
    ("escape", "app.pop_screen", "Cancel"),
]
```

### AND DELETE lines 20-22

```python
def action_dismiss_modal(self) -> None:
    """Dismiss modal without executing trade"""
    self.dismiss(None)
```

## Why This Works

- `app.pop_screen` is a **built-in Textual action** that properly dismisses modals
- It has **higher priority** than widget-level key handling
- When used with ModalScreen, it automatically calls `dismiss(None)`
- This is the **standard Textual pattern** for modal dismissal

## Alternative Fix (If above doesn't work)

If `app.pop_screen` still doesn't work because focus is trapped, add this method:

```python
def on_key(self, event: Key) -> None:
    """Handle key presses at modal level"""
    if event.key == "escape":
        self.dismiss(None)
        event.prevent_default()
        event.stop()
```

**Import needed:**

```python
from textual.events import Key
```

## Complete Corrected Code

```python
"""Trade modal dialog"""
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Input, Select, Button, Label, Static
from textual.containers import Container, Vertical, Horizontal
from textual.events import Key  # ADD THIS
from src.engine.trade_executor import OrderSide

class TradeModal(ModalScreen[dict]):
    """Modal for executing trades"""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, available_stocks: list[str], cash: float):
        super().__init__()
        self.available_stocks = available_stocks
        self.cash = cash

    def on_key(self, event: Key) -> None:
        """Handle key presses - ensure escape works even when widgets have focus"""
        if event.key == "escape":
            self.dismiss(None)
            event.prevent_default()
            event.stop()

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
                    symbol_select.value, quantity, 100.0
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
        else:  # Cancel button
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

## Test Steps

1. **Kill the current app** (Ctrl+C if still running)
2. Apply the complete code above
3. Run: `python -m src.main`
4. Start new game
5. Press 't' to open trade modal
6. **Try these escape scenarios:**
   - Press Escape when quantity input has focus
   - Press Escape when select dropdown is open
   - Press Escape when nothing has focus
7. **ALL should close the modal**

## Why the Original Fix Failed

The original fix used a custom action `dismiss_modal` which has **lower priority** than widget key handlers. The `on_key` method intercepts at the **event level** before widgets process it, ensuring Escape always works.

This is a **common Textual pattern** for modals with form inputs.

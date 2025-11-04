"""Trade modal dialog"""
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Input, Select, Button, Label, Static
from textual.containers import Container, Vertical, Horizontal
from textual.events import Key
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
        if event.input.id != "quantity-input":
            return

        try:
            if not event.value or event.value.strip() == "":
                return

            quantity = int(event.value)
            if quantity <= 0:
                return

            estimate = self.query_one("#estimate", Static)
            # Get approximate price (this is just an estimate before actual trade)
            estimate.update(f"Estimated cost: ~₹{quantity * 2000:,.2f} (example)")
        except ValueError:
            # Not a valid integer yet, ignore
            pass
        except Exception as e:
            # Log unexpected errors
            print(f"Error updating estimate: {e}")
"""Help screen"""
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Footer
from textual.containers import Container, VerticalScroll

class HelpScreen(ModalScreen):
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
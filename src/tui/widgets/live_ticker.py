"""Scrolling ticker tape of stock prices"""
from textual.widgets import Static
from textual import work
from textual.reactive import reactive
import asyncio
from typing import List
from src.models import Position


class LiveTickerWidget(Static):
    """Scrolling ticker tape of stock prices"""

    ticker_text: reactive[str] = reactive("Loading...")

    def __init__(self, positions: List[Position], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.positions = positions or []

    def on_mount(self) -> None:
        """Start ticker animation"""
        self.animate_ticker()

    @work(exclusive=True)
    async def animate_ticker(self) -> None:
        """Animate scrolling ticker"""
        while True:
            ticker_items = []
            for pos in self.positions:
                # Calculate P&L values with fallbacks for different position types
                if hasattr(pos, 'unrealized_pnl'):
                    pnl = pos.unrealized_pnl
                else:
                    pnl = (pos.current_price - pos.avg_buy_price) * pos.quantity if hasattr(pos, 'avg_buy_price') else 0
                    
                if hasattr(pos, 'unrealized_pnl_pct'):
                    pnl_pct = pos.unrealized_pnl_pct
                else:
                    cost = pos.avg_buy_price * pos.quantity if hasattr(pos, 'avg_buy_price') else pos.current_price * pos.quantity
                    pnl_pct = (pnl / cost) * 100 if cost > 0 else 0

                color = "green" if pnl >= 0 else "red"

                ticker_items.append(
                    f"[bold cyan]{pos.symbol}[/]: ₹{pos.current_price:.2f} "
                    f"[{color}]{pnl_pct:+.2f}%[/]"
                )

            if ticker_items:
                ticker_text = "   📊   ".join(ticker_items) + "   📊   "
            else:
                ticker_text = "No positions yet. Make your first trade!   📊"

            self.ticker_text = ticker_text

            await asyncio.sleep(2)  # Update every 2 seconds

    def watch_ticker_text(self, new_text: str) -> None:
        """Update display"""
        self.update(new_text)
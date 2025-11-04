"""Stock selector widget"""
from textual.widgets import ListView, ListItem, Label
from textual.containers import Container

class StockSelector(ListView):
    """Widget to select stocks"""

    def __init__(self, stocks: list[str]):
        super().__init__()
        self.stocks = stocks

    def on_mount(self) -> None:
        """Populate list"""
        for stock in self.stocks:
            self.append(ListItem(Label(stock)))
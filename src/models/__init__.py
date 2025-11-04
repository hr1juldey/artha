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
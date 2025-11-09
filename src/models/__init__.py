"""Data models (Pydantic, not SQLAlchemy yet)"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Union
from .transaction_models import EnhancedPosition, PositionTransaction

@dataclass
class Position:
    """Single stock position (legacy model for backward compatibility)"""
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
    positions: List[Union[Position, EnhancedPosition]] = field(default_factory=list)
    realized_pnl: float = 0.0  # Cumulative P&L from closed positions

    @property
    def positions_value(self) -> float:
        return sum(self._get_market_value(p) for p in self.positions)

    @property
    def total_value(self) -> float:
        return self.cash + self.positions_value

    @property
    def invested(self) -> float:
        return sum(self._get_cost_basis(p) for p in self.positions)

    @property
    def total_pnl(self) -> float:
        """Total P&L = Realized (from closed trades) + Unrealized (from open positions)"""
        unrealized = sum(self._get_unrealized_pnl(p) for p in self.positions)
        return self.realized_pnl + unrealized

    def _get_market_value(self, position: Union[Position, EnhancedPosition]) -> float:
        """Get market value of position regardless of type"""
        if hasattr(position, 'market_value'):
            return position.market_value
        else:
            return position.quantity * position.current_price

    def _get_cost_basis(self, position: Union[Position, EnhancedPosition]) -> float:
        """Get cost basis of position regardless of type"""
        if hasattr(position, 'cost_basis'):
            return position.cost_basis
        else:
            return position.quantity * position.avg_buy_price

    def _get_unrealized_pnl(self, position: Union[Position, EnhancedPosition]) -> float:
        """Get unrealized P&L of position regardless of type"""
        if hasattr(position, 'unrealized_pnl'):
            return position.unrealized_pnl
        else:
            market_value = position.quantity * position.current_price
            cost_basis = position.quantity * position.avg_buy_price
            return market_value - cost_basis

@dataclass
class GameState:
    """Current game state"""
    player_name: str
    current_day: int
    total_days: int
    initial_capital: float
    portfolio: Portfolio
    created_at: datetime = field(default_factory=datetime.now)
    portfolio_history: List[dict] = field(default_factory=list)  # Track history for charts and coach memory
    
    def record_portfolio_state(self) -> None:
        """Record current portfolio state for history tracking"""
        state = {
            "day": self.current_day,
            "total_value": self.portfolio.total_value,
            "cash": self.portfolio.cash,
            "positions_value": self.portfolio.positions_value,
            "pnl": self.portfolio.total_pnl
        }
        self.portfolio_history.append(state)
        
        # Keep only recent history to prevent memory bloat (e.g., last 300 days)
        if len(self.portfolio_history) > 300:
            self.portfolio_history = self.portfolio_history[-300:]
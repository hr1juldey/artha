"""Trade execution logic"""
from dataclasses import dataclass
from enum import Enum
from src.models import Portfolio, Position
from src.config import COMMISSION_RATE

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class TradeResult:
    """Result of trade execution"""
    success: bool
    message: str
    executed_price: float = 0.0
    quantity: int = 0
    total_cost: float = 0.0
    commission: float = 0.0

class TradeExecutor:
    """Executes buy/sell orders"""

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

    @staticmethod
    def calculate_commission(amount: float) -> float:
        """Calculate commission (0.03% or ₹20 max)"""
        commission = amount * COMMISSION_RATE
        return min(commission, 20.0)

    @staticmethod
    def execute_buy(
        portfolio: Portfolio,
        symbol: str,
        quantity: int,
        price: float
    ) -> TradeResult:
        """Execute buy order"""
        # Validate inputs first
        valid, message = TradeExecutor.validate_trade_inputs(symbol, quantity, price)
        if not valid:
            return TradeResult(success=False, message=message)

        # Calculate costs
        cost = price * quantity
        commission = TradeExecutor.calculate_commission(cost)
        total_cost = cost + commission

        # Check if enough cash
        if portfolio.cash < total_cost:
            return TradeResult(
                success=False,
                message=f"Insufficient funds. Need ₹{total_cost:,.2f}, have ₹{portfolio.cash:,.2f}"
            )

        # Deduct cash
        portfolio.cash -= total_cost

        # Find existing position or create new
        existing_pos = None
        for pos in portfolio.positions:
            if pos.symbol == symbol:
                existing_pos = pos
                break

        if existing_pos:
            # Update average buy price
            total_qty = existing_pos.quantity + quantity
            total_cost_basis = (existing_pos.avg_buy_price * existing_pos.quantity) + cost
            existing_pos.avg_buy_price = total_cost_basis / total_qty
            existing_pos.quantity = total_qty
            existing_pos.current_price = price
        else:
            # Create new position
            new_pos = Position(
                symbol=symbol,
                quantity=quantity,
                avg_buy_price=price,
                current_price=price
            )
            portfolio.positions.append(new_pos)

        return TradeResult(
            success=True,
            message=f"Bought {quantity} shares of {symbol} at ₹{price:,.2f}",
            executed_price=price,
            quantity=quantity,
            total_cost=total_cost,
            commission=commission
        )

    @staticmethod
    def execute_sell(
        portfolio: Portfolio,
        symbol: str,
        quantity: int,
        price: float
    ) -> TradeResult:
        """Execute sell order"""
        # Validate inputs first
        valid, message = TradeExecutor.validate_trade_inputs(symbol, quantity, price)
        if not valid:
            return TradeResult(success=False, message=message)

        # Find position
        position = None
        for pos in portfolio.positions:
            if pos.symbol == symbol:
                position = pos
                break

        if not position:
            return TradeResult(
                success=False,
                message=f"No position in {symbol}"
            )

        if position.quantity < quantity:
            return TradeResult(
                success=False,
                message=f"Insufficient quantity. Have {position.quantity}, trying to sell {quantity}"
            )

        # Calculate proceeds
        proceeds = price * quantity
        commission = TradeExecutor.calculate_commission(proceeds)
        net_proceeds = proceeds - commission

        # Update position
        position.quantity -= quantity
        if position.quantity == 0:
            portfolio.positions.remove(position)
        else:
            position.current_price = price

        # Add cash
        portfolio.cash += net_proceeds

        return TradeResult(
            success=True,
            message=f"Sold {quantity} shares of {symbol} at ₹{price:,.2f}",
            executed_price=price,
            quantity=quantity,
            total_cost=net_proceeds,
            commission=commission
        )
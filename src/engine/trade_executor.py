"""Trade execution logic"""
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, date
from src.models import Portfolio, Position
from src.config import COMMISSION_RATE
from src.utils.xirr_calculator import TransactionType
from src.models.transaction_models import EnhancedPosition, PositionTransaction

# Reuse TransactionType as OrderSide for compatibility
OrderSide = TransactionType

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
        price: float,
        transaction_date: date = None
    ) -> TradeResult:
        """Execute buy order with transaction tracking"""
        # Validate inputs first
        valid, message = TradeExecutor.validate_trade_inputs(symbol, quantity, price)
        if not valid:
            return TradeResult(success=False, message=message)

        # Use provided transaction date or default to current date
        if transaction_date is None:
            transaction_date = datetime.now().date()

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

        # Find existing position (either legacy Position or EnhancedPosition)
        existing_pos = None
        pos_idx = -1
        for i, pos in enumerate(portfolio.positions):
            if hasattr(pos, 'symbol') and pos.symbol == symbol:
                existing_pos = pos
                pos_idx = i
                break

        # Create transaction record
        transaction = PositionTransaction(
            date=transaction_date,
            quantity=quantity,
            price=price,
            transaction_type=OrderSide.BUY
        )

        if existing_pos:
            # Check if existing position supports transactions
            if hasattr(existing_pos, 'add_transaction'):
                # Add transaction to existing enhanced position
                existing_pos.add_transaction(transaction)
                existing_pos.current_price = price  # Update current price
            else:
                # Handle legacy Position model - convert to EnhancedPosition
                # WARNING: We cannot accurately determine the original purchase date from legacy Position
                # This will result in incorrect XIRR calculations. The proper fix is to store
                # transaction history in the database.
                enhanced_pos = EnhancedPosition(
                    symbol=symbol,
                    current_price=price,
                )

                # Create a transaction representing the existing holdings
                # NOTE: Using current transaction date as fallback since we don't have historical data
                # This is a known limitation of the legacy Position model
                existing_transaction = PositionTransaction(
                    date=transaction_date,  # LIMITATION: Unknown actual purchase date
                    quantity=existing_pos.quantity,
                    price=existing_pos.avg_buy_price,
                    transaction_type=OrderSide.BUY
                )
                enhanced_pos.add_transaction(existing_transaction)

                # Then add the new transaction
                enhanced_pos.add_transaction(transaction)

                # Replace the legacy position with the enhanced one
                portfolio.positions[pos_idx] = enhanced_pos
        else:
            # Create new enhanced position with first transaction
            new_pos = EnhancedPosition(
                symbol=symbol,
                current_price=price,
            )
            new_pos.add_transaction(transaction)
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
        price: float,
        transaction_date: date = None
    ) -> TradeResult:
        """Execute sell order with transaction tracking"""
        # Validate inputs first
        valid, message = TradeExecutor.validate_trade_inputs(symbol, quantity, price)
        if not valid:
            return TradeResult(success=False, message=message)

        # Use provided transaction date or default to current date
        if transaction_date is None:
            transaction_date = datetime.now().date()

        # Find position
        position = None
        pos_idx = -1
        for i, pos in enumerate(portfolio.positions):
            if hasattr(pos, 'symbol') and pos.symbol == symbol:
                position = pos
                pos_idx = i
                break

        if not position:
            return TradeResult(
                success=False,
                message=f"No position in {symbol}"
            )

        # Check quantity based on position type
        if hasattr(position, 'quantity'):
            if hasattr(position, 'add_transaction'):
                # EnhancedPosition - use its quantity property
                available_quantity = position.quantity
            else:
                # Legacy Position model
                available_quantity = position.quantity
        else:
            # Fallback for old position model
            available_quantity = position.quantity if hasattr(position, 'quantity') else 0

        if available_quantity < quantity:
            return TradeResult(
                success=False,
                message=f"Insufficient quantity. Have {available_quantity}, trying to sell {quantity}"
            )

        # Calculate proceeds
        proceeds = price * quantity
        commission = TradeExecutor.calculate_commission(proceeds)
        net_proceeds = proceeds - commission

        # Create transaction record
        transaction = PositionTransaction(
            date=transaction_date,
            quantity=quantity,
            price=price,
            transaction_type=OrderSide.SELL
        )

        if hasattr(position, 'add_transaction'):
            # Add transaction to enhanced position
            position.add_transaction(transaction)
            if position.quantity == 0:
                # Remove position if all shares sold
                portfolio.positions.pop(pos_idx)
            else:
                position.current_price = price
        else:
            # Handle legacy Position model by converting to EnhancedPosition first
            if hasattr(position, 'quantity'):
                # Convert legacy position to enhanced position (if it's not already)
                # WARNING: We cannot accurately determine the original purchase date from legacy Position
                enhanced_pos = EnhancedPosition(
                    symbol=symbol,
                    current_price=price,
                )

                # Create a transaction representing the existing holdings
                # NOTE: Using current transaction date as fallback since we don't have historical data
                existing_transaction = PositionTransaction(
                    date=transaction_date,  # LIMITATION: Unknown actual purchase date
                    quantity=position.quantity,
                    price=position.avg_buy_price,
                    transaction_type=OrderSide.BUY
                )
                enhanced_pos.add_transaction(existing_transaction)

                # Add the sell transaction
                enhanced_pos.add_transaction(transaction)

                # Replace the legacy position with the enhanced one
                portfolio.positions[pos_idx] = enhanced_pos

                # If quantity becomes 0, remove the position
                if enhanced_pos.quantity == 0:
                    portfolio.positions.pop(pos_idx)
            else:
                # Fallback for basic position - use legacy approach
                position.quantity -= quantity
                if position.quantity == 0:
                    portfolio.positions.pop(pos_idx)
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
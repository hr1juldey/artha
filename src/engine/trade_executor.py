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
    realized_pnl: float = 0.0  # Realized P&L (only for sell orders)
    cost_breakdown: dict = None  # Detailed cost breakdown for transparency

    def __post_init__(self):
        """Initialize cost_breakdown as empty dict if None"""
        if self.cost_breakdown is None:
            self.cost_breakdown = {}

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
        """Calculate commission (0.03% or ₹20 max) - LEGACY METHOD"""
        commission = amount * COMMISSION_RATE
        return min(commission, 20.0)

    @staticmethod
    def calculate_all_costs(
        trade_value: float,
        is_buy: bool = True
    ) -> tuple[float, dict]:
        """
        Calculate ALL transaction costs for Indian stock markets

        Returns: (total_cost, cost_breakdown_dict)

        Includes:
        - Brokerage (0.03%)
        - STT (0.1% on sell only)
        - Exchange charges (0.00325%)
        - GST (18% on brokerage + exchange)
        - SEBI fees (₹10 per crore)
        """
        from src.config import (
            BROKERAGE_RATE, STT_RATE_BUY, STT_RATE_SELL,
            EXCHANGE_CHARGES_RATE, GST_RATE, SEBI_FEES_RATE
        )

        # 1. Brokerage
        brokerage = trade_value * BROKERAGE_RATE
        brokerage = min(brokerage, 20.0)  # Cap at ₹20

        # 2. STT (Securities Transaction Tax)
        stt_rate = STT_RATE_BUY if is_buy else STT_RATE_SELL
        stt = trade_value * stt_rate

        # 3. Exchange transaction charges
        exchange_charges = trade_value * EXCHANGE_CHARGES_RATE

        # 4. SEBI fees
        sebi_fees = trade_value * SEBI_FEES_RATE

        # 5. GST (on brokerage + exchange charges)
        taxable_amount = brokerage + exchange_charges
        gst = taxable_amount * GST_RATE

        # Total
        total = brokerage + stt + exchange_charges + sebi_fees + gst

        # Breakdown for transparency
        breakdown = {
            'brokerage': round(brokerage, 2),
            'stt': round(stt, 2),
            'exchange_charges': round(exchange_charges, 2),
            'gst': round(gst, 2),
            'sebi_fees': round(sebi_fees, 2),
            'total': round(total, 2)
        }

        return total, breakdown

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

        # Calculate all costs (brokerage, STT, exchange, GST, SEBI)
        trade_value = price * quantity
        commission, cost_breakdown = TradeExecutor.calculate_all_costs(trade_value, is_buy=True)
        total_cost = trade_value + commission

        # Check if enough cash
        if portfolio.cash < total_cost:
            return TradeResult(
                success=False,
                message=f"Insufficient funds. Need ₹{total_cost:,.2f}, have ₹{portfolio.cash:,.2f}",
                cost_breakdown=cost_breakdown
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
            transaction_type=OrderSide.BUY,
            commission=commission  # Include ALL transaction costs
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
            commission=commission,
            cost_breakdown=cost_breakdown
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

        # Calculate all costs (includes STT on sell which is the biggest cost)
        trade_value = price * quantity
        commission, cost_breakdown = TradeExecutor.calculate_all_costs(trade_value, is_buy=False)
        net_proceeds = trade_value - commission

        # Create transaction record
        transaction = PositionTransaction(
            date=transaction_date,
            quantity=quantity,
            price=price,
            transaction_type=OrderSide.SELL,
            commission=commission  # Include ALL transaction costs
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

        # Calculate realized P&L
        # Cost basis of sold shares = avg_buy_price * quantity
        # (avg_buy_price already includes commission in cost basis calculation)
        if hasattr(position, 'avg_buy_price'):
            cost_basis_sold = position.avg_buy_price * quantity
        else:
            # Fallback for legacy positions (shouldn't happen)
            cost_basis_sold = 0

        realized_pnl = trade_value - commission - cost_basis_sold

        # Update portfolio's cumulative realized P&L
        portfolio.realized_pnl += realized_pnl

        # Add cash
        portfolio.cash += net_proceeds

        return TradeResult(
            success=True,
            message=f"Sold {quantity} shares of {symbol} at ₹{price:,.2f}",
            executed_price=price,
            quantity=quantity,
            total_cost=net_proceeds,
            commission=commission,
            realized_pnl=realized_pnl,
            cost_breakdown=cost_breakdown
        )
"""
Enhanced Position Model with Transaction History and XIRR Calculation

This module implements an improved position model that tracks individual transactions
instead of just averaging buy prices, allowing for proper XIRR calculations.
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Union
from enum import Enum
from src.utils.xirr_calculator import TransactionType, calculate_position_xirr
from src.database.models import Transaction

@dataclass
class PositionTransaction:
    """Represents a buy/sell transaction for position tracking"""
    date: Union[datetime, date]
    quantity: int  # Number of shares
    price: float   # Price per share
    transaction_type: TransactionType
    commission: float = 0.0  # Transaction cost (default 0 for backward compatibility)


@dataclass
class EnhancedPosition:
    """Enhanced position that tracks individual transactions for proper XIRR calculations"""

    symbol: str
    _current_price: float = field(default=0.0, init=False)  # Private field
    transactions: List[PositionTransaction] = field(default_factory=list)

    # Cached values calculated from transactions
    _quantity: int = field(default=0, init=False)
    _avg_buy_price: float = field(default=0.0, init=False)
    _cost_basis: float = field(default=0.0, init=False)

    def __init__(self, symbol: str, current_price: float, transactions: List[PositionTransaction] = None):
        """Initialize position with symbol and current price"""
        self.symbol = symbol
        self._current_price = current_price
        self.transactions = transactions if transactions is not None else []
        self._recalculate_position()

    @property
    def current_price(self) -> float:
        """Get current price"""
        return self._current_price

    @current_price.setter
    def current_price(self, value: float):
        """Set current price and recalculate dependent values"""
        self._current_price = value
        # No need to recalculate quantity/avg_buy_price/cost_basis as they don't depend on current_price

    @property
    def quantity(self) -> int:
        """Get current quantity"""
        return self._quantity

    @property
    def avg_buy_price(self) -> float:
        """Get average buy price"""
        return self._avg_buy_price

    @property
    def cost_basis(self) -> float:
        """Get cost basis"""
        return self._cost_basis

    @property
    def market_value(self) -> float:
        """Calculate market value dynamically based on current price"""
        return abs(self._quantity) * self._current_price

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L dynamically"""
        if self._quantity > 0:
            # Calculate proportional cost basis for remaining shares
            total_bought_quantity = sum(t.quantity for t in self.transactions if t.transaction_type == TransactionType.BUY)
            if total_bought_quantity > 0:
                avg_cost_per_share = self._cost_basis / total_bought_quantity
                remaining_cost_basis = avg_cost_per_share * self._quantity
                return self.market_value - remaining_cost_basis
        return 0.0

    @property
    def unrealized_pnl_pct(self) -> float:
        """Calculate unrealized P&L percentage dynamically"""
        if self._cost_basis > 0:
            return (self.unrealized_pnl / self._cost_basis) * 100
        return 0.0

    def __post_init__(self):
        """This won't be called since we override __init__"""
        pass
    
    def add_transaction(self, transaction: PositionTransaction) -> None:
        """Add a new transaction to the position"""
        self.transactions.append(transaction)
        self._recalculate_position()
    
    def _recalculate_position(self) -> None:
        """Recalculate position metrics based on all transactions"""
        # Calculate quantity by summing all transactions
        total_quantity = 0
        total_cost_basis = 0

        for trans in self.transactions:
            if trans.transaction_type == TransactionType.BUY:
                total_quantity += trans.quantity  # quantity for buys
                # FIX: Include commission in cost basis (with backward compatibility)
                commission = trans.commission if hasattr(trans, 'commission') else 0.0
                total_cost_basis += (trans.quantity * trans.price + commission)
            else:  # SELL
                total_quantity -= trans.quantity  # quantity for sells

        self._quantity = total_quantity
        self._cost_basis = total_cost_basis  # Total cost basis from all BUY transactions

        # Calculate avg buy price based on total bought quantity
        total_bought_quantity = sum(trans.quantity for trans in self.transactions if trans.transaction_type == TransactionType.BUY)
        self._avg_buy_price = self._cost_basis / total_bought_quantity if total_bought_quantity > 0 else 0

        # Note: market_value, unrealized_pnl, and unrealized_pnl_pct are now @property methods
        # that calculate dynamically based on current_price
    
    def calculate_xirr(self, current_date: Union[datetime, date] = None) -> float:
        """Calculate XIRR for this position"""
        if current_date is None:
            current_date = datetime.now().date()
        
        # Convert our transactions to the format expected by the XIRR calculator
        from src.utils.xirr_calculator import Transaction as XirrTransaction
        xirr_transactions = []
        for trans in self.transactions:
            # Convert to the XIRR calculator's Transaction format
            # Amount is: negative for buys (cash outflow), positive for sells (cash inflow)
            trans_amount = trans.quantity * trans.price  # quantity * price = transaction value
            if trans.transaction_type == TransactionType.BUY:
                trans_amount = -abs(trans_amount)  # Negative for buys
            else:  # SELL
                trans_amount = abs(trans_amount)  # Positive for sells
            
            xirr_transactions.append(XirrTransaction(
                date=trans.date,
                amount=trans_amount,
                transaction_type=trans.transaction_type
            ))
        
        current_value = self.quantity * self.current_price
        return calculate_position_xirr(xirr_transactions, current_value, current_date)
    
    def calculate_pnl_for_transaction(self, index: int) -> float:
        """Calculate P&L for a specific buy transaction"""
        if index >= len(self.transactions) or self.transactions[index].transaction_type != TransactionType.BUY:
            return 0.0  # Only calculate for buy transactions
        
        buy_transaction = self.transactions[index]
        buy_price = buy_transaction.price
        buy_quantity = buy_transaction.quantity
        current_value = buy_quantity * self.current_price
        buy_cost = buy_quantity * buy_price
        
        return current_value - buy_cost
    
    def get_fifo_sells(self) -> List[dict]:
        """Return FIFO (First In, First Out) based P&L for all transactions"""
        if not self.transactions:
            return []
        
        # Track which buy transactions are sold against which sell transactions
        buy_queue = []
        results = []
        
        for i, trans in enumerate(self.transactions):
            if trans.transaction_type == TransactionType.BUY:
                # Add buy transaction to queue
                buy_queue.append({
                    'index': i,
                    'quantity': trans.quantity,
                    'price': trans.price,
                    'remaining': trans.quantity
                })
            else:  # SELL
                sell_quantity = trans.quantity
                sell_price = trans.price
                
                # Match against FIFO buy transactions
                while sell_quantity > 0 and buy_queue:
                    buy_trans = buy_queue[0]
                    
                    if buy_trans['remaining'] <= sell_quantity:
                        # Sell all of this buy transaction
                        sold_quantity = buy_trans['remaining']
                        pnl = sold_quantity * (sell_price - buy_trans['price'])
                        results.append({
                            'buy_index': buy_trans['index'],
                            'sell_index': i,
                            'quantity': sold_quantity,
                            'pnl': pnl
                        })
                        
                        sell_quantity -= sold_quantity
                        buy_queue.pop(0)  # Remove this buy from queue
                    else:
                        # Sell only part of this buy transaction
                        sold_quantity = sell_quantity
                        pnl = sold_quantity * (sell_price - buy_trans['price'])
                        results.append({
                            'buy_index': buy_trans['index'],
                            'sell_index': i,
                            'quantity': sold_quantity,
                            'pnl': pnl
                        })
                        
                        buy_trans['remaining'] -= sold_quantity
                        sell_quantity = 0
        
        return results


# Example usage and test function
def demo_enhanced_position():
    """Demonstrate the enhanced position model with XIRR calculation"""
    from datetime import datetime
    
    # Create an enhanced position
    position = EnhancedPosition(
        symbol="RELIANCE",
        current_price=2500.0
    )
    
    # Add some transactions
    # Buy 100 shares at 2000 on day 1
    position.add_transaction(Transaction(
        date=datetime(2023, 1, 1).date(),
        amount=100,  # quantity
        price=2000.0,
        transaction_type=TransactionType.BUY
    ))
    
    # Buy 50 shares at 2200 on day 30
    position.add_transaction(Transaction(
        date=datetime(2023, 1, 31).date(),
        amount=50,  # quantity
        price=2200.0,
        transaction_type=TransactionType.BUY
    ))
    
    # Sell 30 shares at 2400 on day 60
    position.add_transaction(Transaction(
        date=datetime(2023, 3, 1).date(),
        amount=30,  # quantity
        price=2400.0,
        transaction_type=TransactionType.SELL
    ))
    
    print(f"Symbol: {position.symbol}")
    print(f"Quantity: {position.quantity}")
    print(f"Avg Buy Price: {position.avg_buy_price:.2f}")
    print(f"Current Price: {position.current_price}")
    print(f"Market Value: {position.market_value:.2f}")
    print(f"Unrealized P&L: {position.unrealized_pnl:.2f}")
    print(f"Unrealized P&L %: {position.unrealized_pnl_pct:.2f}%")
    
    # Calculate XIRR
    xirr_result = position.calculate_xirr()
    print(f"XIRR: {xirr_result:.4f} ({xirr_result*100:.2f}%)")
    
    # Calculate P&L for each transaction
    pnl1 = position.calculate_pnl_for_transaction(0)  # First buy
    pnl2 = position.calculate_pnl_for_transaction(1)  # Second buy
    print(f"P&L for first buy transaction: {pnl1:.2f}")
    print(f"P&L for second buy transaction: {pnl2:.2f}")
    
    # FIFO P&L calculation
    fifo_results = position.get_fifo_sells()
    print(f"FIFO sell results: {fifo_results}")


if __name__ == "__main__":
    demo_enhanced_position()
# Stage 4: Trading Logic & State Machines

**Supplement to**: STAGE4_OVERVIEW.md
**Purpose**: Detailed trading logic, validation rules, state machines, and edge cases

---

## Trading Engine Architecture

```
┌─────────────────────────────────────────────────────┐
│             Trade Execution Flow                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  User Input (Symbol, Action, Quantity)              │
│            ▼                                         │
│  ┌──────────────────────┐                          │
│  │  Input Validation     │                          │
│  │  - Symbol exists      │                          │
│  │  - Quantity > 0       │                          │
│  │  - Action valid       │                          │
│  └──────────┬───────────┘                          │
│             ▼                                         │
│  ┌──────────────────────┐                          │
│  │  Price Lookup         │                          │
│  │  - Get current price  │                          │
│  │  - Validate price > 0 │                          │
│  └──────────┬───────────┘                          │
│             ▼                                         │
│  ┌──────────────────────┐                          │
│  │  Business Rules       │                          │
│  │  - Check funds (BUY)  │                          │
│  │  - Check holdings(SELL)│                         │
│  │  - Calculate commision│                          │
│  └──────────┬───────────┘                          │
│             ▼                                         │
│  ┌──────────────────────┐                          │
│  │  Execute Trade        │                          │
│  │  - Update cash        │                          │
│  │  - Update positions   │                          │
│  │  - Log transaction    │                          │
│  └──────────┬───────────┘                          │
│             ▼                                         │
│  ┌──────────────────────┐                          │
│  │  Persist State        │                          │
│  │  - Save to database   │                          │
│  │  - Update UI          │                          │
│  └──────────────────────┘                          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Trade Validation Rules

### Input Validation

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    error_message: Optional[str] = None

    @staticmethod
    def success() -> 'ValidationResult':
        return ValidationResult(is_valid=True, error_message=None)

    @staticmethod
    def failure(message: str) -> 'ValidationResult':
        return ValidationResult(is_valid=False, error_message=message)

class TradeValidator:
    """Validates trade inputs"""

    # Business rule constants
    MIN_QUANTITY = 1
    MAX_QUANTITY = 10000
    MIN_PRICE = 0.01
    MAX_PRICE = 100000.0  # ₹1 lakh max per share
    MIN_TRADE_VALUE = 100.0  # ₹100 minimum trade
    MAX_TRADE_VALUE = 10000000.0  # ₹1 crore max trade

    @staticmethod
    def validate_symbol(symbol: str) -> ValidationResult:
        """Validate stock symbol

        Rules:
            - Not empty
            - Length between 1-20 characters
            - Alphanumeric only

        Args:
            symbol: Stock symbol

        Returns:
            ValidationResult
        """
        if not symbol or len(symbol.strip()) == 0:
            return ValidationResult.failure("Symbol cannot be empty")

        symbol = symbol.strip().upper()

        if len(symbol) > 20:
            return ValidationResult.failure("Symbol too long (max 20 characters)")

        if not symbol.replace('.', '').isalnum():
            return ValidationResult.failure("Symbol must be alphanumeric")

        return ValidationResult.success()

    @staticmethod
    def validate_action(action: str) -> ValidationResult:
        """Validate trade action

        Rules:
            - Must be "BUY" or "SELL"

        Args:
            action: Trade action

        Returns:
            ValidationResult
        """
        action = action.strip().upper()

        if action not in ["BUY", "SELL"]:
            return ValidationResult.failure("Action must be BUY or SELL")

        return ValidationResult.success()

    @staticmethod
    def validate_quantity(quantity: int) -> ValidationResult:
        """Validate quantity

        Rules:
            - Must be positive integer
            - Between MIN_QUANTITY and MAX_QUANTITY

        Args:
            quantity: Number of shares

        Returns:
            ValidationResult
        """
        if not isinstance(quantity, int):
            return ValidationResult.failure("Quantity must be an integer")

        if quantity < TradeValidator.MIN_QUANTITY:
            return ValidationResult.failure(
                f"Quantity must be at least {TradeValidator.MIN_QUANTITY}"
            )

        if quantity > TradeValidator.MAX_QUANTITY:
            return ValidationResult.failure(
                f"Quantity cannot exceed {TradeValidator.MAX_QUANTITY}"
            )

        return ValidationResult.success()

    @staticmethod
    def validate_price(price: float) -> ValidationResult:
        """Validate price

        Rules:
            - Must be positive
            - Between MIN_PRICE and MAX_PRICE

        Args:
            price: Price per share

        Returns:
            ValidationResult
        """
        if price < TradeValidator.MIN_PRICE:
            return ValidationResult.failure(
                f"Price must be at least ₹{TradeValidator.MIN_PRICE}"
            )

        if price > TradeValidator.MAX_PRICE:
            return ValidationResult.failure(
                f"Price cannot exceed ₹{TradeValidator.MAX_PRICE:,.0f}"
            )

        return ValidationResult.success()

    @staticmethod
    def validate_trade_value(
        quantity: int,
        price: float
    ) -> ValidationResult:
        """Validate total trade value

        Rules:
            - Total value between MIN_TRADE_VALUE and MAX_TRADE_VALUE

        Args:
            quantity: Number of shares
            price: Price per share

        Returns:
            ValidationResult
        """
        total_value = quantity * price

        if total_value < TradeValidator.MIN_TRADE_VALUE:
            return ValidationResult.failure(
                f"Trade value too small (min ₹{TradeValidator.MIN_TRADE_VALUE:.0f})"
            )

        if total_value > TradeValidator.MAX_TRADE_VALUE:
            return ValidationResult.failure(
                f"Trade value too large (max ₹{TradeValidator.MAX_TRADE_VALUE:,.0f})"
            )

        return ValidationResult.success()

    @classmethod
    def validate_trade_inputs(
        cls,
        symbol: str,
        action: str,
        quantity: int,
        price: float
    ) -> ValidationResult:
        """Validate all trade inputs

        Args:
            symbol: Stock symbol
            action: BUY or SELL
            quantity: Number of shares
            price: Price per share

        Returns:
            ValidationResult with first error found, or success
        """
        # Validate each field
        checks = [
            cls.validate_symbol(symbol),
            cls.validate_action(action),
            cls.validate_quantity(quantity),
            cls.validate_price(price),
            cls.validate_trade_value(quantity, price),
        ]

        # Return first failure
        for result in checks:
            if not result.is_valid:
                return result

        return ValidationResult.success()
```

---

## Business Rules

### Buy Order Rules

```python
class BuyOrderRules:
    """Business rules for buy orders"""

    @staticmethod
    def can_afford(
        cash: float,
        quantity: int,
        price: float,
        commission: float
    ) -> tuple[bool, str]:
        """Check if user can afford purchase

        Args:
            cash: Available cash
            quantity: Shares to buy
            price: Price per share
            commission: Commission amount

        Returns:
            (can_afford, message)
        """
        total_cost = (quantity * price) + commission

        if cash < total_cost:
            shortage = total_cost - cash
            return False, f"Insufficient funds. Need ₹{shortage:,.2f} more"

        return True, "OK"

    @staticmethod
    def check_diversification_warning(
        current_positions: int,
        new_symbol: str,
        existing_symbols: list[str]
    ) -> Optional[str]:
        """Check if user should diversify more

        Args:
            current_positions: Number of current positions
            new_symbol: Symbol being bought
            existing_symbols: Symbols already owned

        Returns:
            Warning message if applicable, None otherwise
        """
        # Check if adding to existing position
        if new_symbol in existing_symbols:
            return None  # Adding to existing is fine

        # Check if too few positions
        if current_positions == 0:
            return "Tip: Consider building a diversified portfolio with 5-7 stocks"

        if current_positions < 3:
            return "Good! Building diversification"

        return None

    @staticmethod
    def check_concentration_risk(
        portfolio_value: float,
        trade_value: float
    ) -> Optional[str]:
        """Check if single trade is too large

        Args:
            portfolio_value: Total portfolio value
            trade_value: Value of this trade

        Returns:
            Warning message if applicable, None otherwise
        """
        if portfolio_value == 0:
            return None  # First trade

        trade_pct = (trade_value / portfolio_value) * 100

        if trade_pct > 50:
            return f"Warning: This trade is {trade_pct:.1f}% of your portfolio"

        if trade_pct > 30:
            return f"Caution: Large position ({trade_pct:.1f}% of portfolio)"

        return None
```

### Sell Order Rules

```python
class SellOrderRules:
    """Business rules for sell orders"""

    @staticmethod
    def can_sell(
        symbol: str,
        quantity: int,
        positions: list
    ) -> tuple[bool, str]:
        """Check if user can sell shares

        Args:
            symbol: Stock symbol
            quantity: Shares to sell
            positions: List of Position objects

        Returns:
            (can_sell, message)
        """
        # Find position
        position = None
        for pos in positions:
            if pos.symbol == symbol:
                position = pos
                break

        if position is None:
            return False, f"You don't own any {symbol} shares"

        if quantity > position.quantity:
            return False, f"You only own {position.quantity} shares (trying to sell {quantity})"

        return True, "OK"

    @staticmethod
    def check_selling_at_loss(
        avg_buy_price: float,
        current_price: float
    ) -> Optional[str]:
        """Check if selling at a loss

        Args:
            avg_buy_price: Average purchase price
            current_price: Current selling price

        Returns:
            Warning message if selling at loss, None otherwise
        """
        if current_price < avg_buy_price:
            loss_pct = ((current_price - avg_buy_price) / avg_buy_price) * 100
            return f"Note: Selling at {loss_pct:.1f}% loss"

        return None

    @staticmethod
    def check_selling_entire_position(
        quantity: int,
        position_quantity: int,
        num_positions: int
    ) -> Optional[str]:
        """Check if selling entire position reduces diversification

        Args:
            quantity: Shares being sold
            position_quantity: Total shares owned
            num_positions: Total number of positions

        Returns:
            Warning message if applicable, None otherwise
        """
        if quantity == position_quantity:  # Selling all
            if num_positions <= 3:
                return "Warning: Selling entire position reduces diversification"

        return None
```

---

## Commission Calculation

```python
class CommissionCalculator:
    """Calculate trading commission"""

    # Commission rules
    COMMISSION_RATE = 0.0003  # 0.03%
    MAX_COMMISSION = 20.0  # ₹20 maximum

    @staticmethod
    def calculate(trade_value: float) -> float:
        """Calculate commission for trade

        Formula:
            commission = min(trade_value * 0.03%, ₹20)

        Args:
            trade_value: Total value of trade (quantity * price)

        Returns:
            Commission amount

        Examples:
            >>> CommissionCalculator.calculate(10000)  # ₹10k trade
            3.0  # 0.03% = ₹3

            >>> CommissionCalculator.calculate(1000000)  # ₹10L trade
            20.0  # Capped at ₹20

            >>> CommissionCalculator.calculate(50000)  # ₹50k trade
            15.0  # 0.03% = ₹15
        """
        commission = trade_value * CommissionCalculator.COMMISSION_RATE
        return min(commission, CommissionCalculator.MAX_COMMISSION)

    @staticmethod
    def calculate_with_breakdown(
        quantity: int,
        price: float
    ) -> dict:
        """Calculate commission with detailed breakdown

        Args:
            quantity: Number of shares
            price: Price per share

        Returns:
            Dict with breakdown:
                - trade_value: Total trade value
                - commission_rate: Rate applied
                - commission_calculated: Before cap
                - commission_final: After cap
                - total_cost: Trade value + commission
        """
        trade_value = quantity * price
        commission_calculated = trade_value * CommissionCalculator.COMMISSION_RATE
        commission_final = min(commission_calculated, CommissionCalculator.MAX_COMMISSION)

        return {
            'trade_value': trade_value,
            'commission_rate': CommissionCalculator.COMMISSION_RATE,
            'commission_calculated': commission_calculated,
            'commission_final': commission_final,
            'total_cost': trade_value + commission_final,
            'capped': commission_calculated > CommissionCalculator.MAX_COMMISSION
        }
```

---

## Trade Execution Engine

```python
from dataclasses import dataclass
from typing import Optional
from src.models import Portfolio, Position

@dataclass
class TradeResult:
    """Result of trade execution"""
    success: bool
    message: str
    commission: float = 0.0
    new_cash: float = 0.0
    new_position_quantity: int = 0
    new_position_avg_price: float = 0.0

class TradeExecutor:
    """Executes trades and updates portfolio"""

    @staticmethod
    def execute_buy(
        portfolio: Portfolio,
        symbol: str,
        quantity: int,
        price: float
    ) -> TradeResult:
        """Execute buy order

        Process:
            1. Validate inputs
            2. Calculate costs
            3. Check funds
            4. Update cash
            5. Update or create position
            6. Return result

        Args:
            portfolio: Portfolio to update
            symbol: Stock symbol
            quantity: Shares to buy
            price: Price per share

        Returns:
            TradeResult
        """
        # Validate inputs
        validation = TradeValidator.validate_trade_inputs(
            symbol, "BUY", quantity, price
        )
        if not validation.is_valid:
            return TradeResult(
                success=False,
                message=validation.error_message
            )

        # Calculate costs
        trade_value = quantity * price
        commission = CommissionCalculator.calculate(trade_value)
        total_cost = trade_value + commission

        # Check funds
        can_afford, message = BuyOrderRules.can_afford(
            portfolio.cash, quantity, price, commission
        )
        if not can_afford:
            return TradeResult(
                success=False,
                message=message
            )

        # Update cash
        portfolio.cash -= total_cost

        # Update or create position
        existing_position = portfolio.get_position(symbol)

        if existing_position:
            # Add to existing position (average down/up)
            total_quantity = existing_position.quantity + quantity
            total_cost_basis = (
                (existing_position.quantity * existing_position.avg_buy_price) +
                (quantity * price)
            )
            new_avg_price = total_cost_basis / total_quantity

            existing_position.quantity = total_quantity
            existing_position.avg_buy_price = new_avg_price

            result_quantity = total_quantity
            result_avg_price = new_avg_price

        else:
            # Create new position
            new_position = Position(
                symbol=symbol,
                quantity=quantity,
                avg_buy_price=price,
                current_price=price
            )
            portfolio.positions.append(new_position)

            result_quantity = quantity
            result_avg_price = price

        return TradeResult(
            success=True,
            message=f"Bought {quantity} shares of {symbol} at ₹{price:,.2f}",
            commission=commission,
            new_cash=portfolio.cash,
            new_position_quantity=result_quantity,
            new_position_avg_price=result_avg_price
        )

    @staticmethod
    def execute_sell(
        portfolio: Portfolio,
        symbol: str,
        quantity: int,
        price: float
    ) -> TradeResult:
        """Execute sell order

        Process:
            1. Validate inputs
            2. Check holdings
            3. Calculate proceeds
            4. Update position
            5. Update cash
            6. Return result

        Args:
            portfolio: Portfolio to update
            symbol: Stock symbol
            quantity: Shares to sell
            price: Price per share

        Returns:
            TradeResult
        """
        # Validate inputs
        validation = TradeValidator.validate_trade_inputs(
            symbol, "SELL", quantity, price
        )
        if not validation.is_valid:
            return TradeResult(
                success=False,
                message=validation.error_message
            )

        # Check holdings
        can_sell, message = SellOrderRules.can_sell(
            symbol, quantity, portfolio.positions
        )
        if not can_sell:
            return TradeResult(
                success=False,
                message=message
            )

        # Calculate proceeds
        trade_value = quantity * price
        commission = CommissionCalculator.calculate(trade_value)
        net_proceeds = trade_value - commission

        # Update position
        position = portfolio.get_position(symbol)

        if position.quantity == quantity:
            # Selling entire position - remove from portfolio
            portfolio.positions.remove(position)
            result_quantity = 0
            result_avg_price = 0.0
        else:
            # Partial sell - reduce quantity
            position.quantity -= quantity
            result_quantity = position.quantity
            result_avg_price = position.avg_buy_price

        # Update cash
        portfolio.cash += net_proceeds

        return TradeResult(
            success=True,
            message=f"Sold {quantity} shares of {symbol} at ₹{price:,.2f}",
            commission=commission,
            new_cash=portfolio.cash,
            new_position_quantity=result_quantity,
            new_position_avg_price=result_avg_price
        )

    @staticmethod
    def estimate_trade(
        action: str,
        quantity: int,
        price: float,
        current_cash: float = 0.0,
        current_holdings: int = 0
    ) -> dict:
        """Estimate trade without executing

        Args:
            action: BUY or SELL
            quantity: Shares to trade
            price: Price per share
            current_cash: Available cash (for BUY check)
            current_holdings: Current shares (for SELL check)

        Returns:
            Dict with estimate details
        """
        trade_value = quantity * price
        commission = CommissionCalculator.calculate(trade_value)

        if action == "BUY":
            total_cost = trade_value + commission
            can_execute = current_cash >= total_cost if current_cash > 0 else True

            return {
                'action': 'BUY',
                'quantity': quantity,
                'price': price,
                'trade_value': trade_value,
                'commission': commission,
                'total_cost': total_cost,
                'can_execute': can_execute,
                'cash_remaining': current_cash - total_cost if can_execute else 0,
            }
        else:  # SELL
            net_proceeds = trade_value - commission
            can_execute = current_holdings >= quantity if current_holdings > 0 else True

            return {
                'action': 'SELL',
                'quantity': quantity,
                'price': price,
                'trade_value': trade_value,
                'commission': commission,
                'net_proceeds': net_proceeds,
                'can_execute': can_execute,
                'cash_after': current_cash + net_proceeds if can_execute else current_cash,
            }
```

---

## State Machine: Portfolio Updates

```
BUY Flow:
┌─────────────┐
│ Initial     │
│ State       │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Validate Inputs  │──► [Invalid] ──► Return Error
└────────┬─────────┘
         │ [Valid]
         ▼
┌──────────────────┐
│ Check Funds      │──► [Insufficient] ──► Return Error
└────────┬─────────┘
         │ [Sufficient]
         ▼
┌──────────────────┐
│ Deduct Cash      │
└────────┬─────────┘
         │
         ▼
    ┌────────────┐
    │ Position   │
    │ Exists?    │
    └─┬────────┬─┘
      │        │
   [Yes]     [No]
      │        │
      ▼        ▼
┌──────────┐ ┌──────────┐
│ Update   │ │ Create   │
│ Existing │ │ New      │
│ Position │ │ Position │
└────┬─────┘ └────┬─────┘
     │            │
     └────┬───────┘
          ▼
    ┌───────────┐
    │ Return    │
    │ Success   │
    └───────────┘

SELL Flow:
┌─────────────┐
│ Initial     │
│ State       │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Validate Inputs  │──► [Invalid] ──► Return Error
└────────┬─────────┘
         │ [Valid]
         ▼
┌──────────────────┐
│ Check Holdings   │──► [Insufficient] ──► Return Error
└────────┬─────────┘
         │ [Sufficient]
         ▼
┌──────────────────┐
│ Calculate        │
│ Proceeds         │
└────────┬─────────┘
         │
         ▼
    ┌────────────┐
    │ Selling    │
    │ All?       │
    └─┬────────┬─┘
      │        │
   [Yes]     [No]
      │        │
      ▼        ▼
┌──────────┐ ┌──────────┐
│ Remove   │ │ Reduce   │
│ Position │ │ Quantity │
└────┬─────┘ └────┬─────┘
     │            │
     └────┬───────┘
          ▼
    ┌───────────┐
    │ Add Cash  │
    └─────┬─────┘
          ▼
    ┌───────────┐
    │ Return    │
    │ Success   │
    └───────────┘
```

---

## Edge Cases and Handling

### Edge Case 1: Zero Price

```python
def handle_zero_price(symbol: str, price: float) -> tuple[bool, str]:
    """Handle case where price lookup returns 0

    This can happen if:
        - Symbol not found
        - Network error
        - Data source issue

    Args:
        symbol: Stock symbol
        price: Price returned

    Returns:
        (should_proceed, message)
    """
    if price <= 0:
        return False, f"Unable to get price for {symbol}. Please try again or check symbol."

    return True, "OK"
```

### Edge Case 2: Exact Cash Match

```python
def handle_exact_cash_match():
    """Handle when trade cost exactly matches available cash

    Example: Cash = ₹10,000, Trade cost = ₹10,000

    Result: Allow trade, cash becomes 0
    """
    # This is handled correctly by >= check in can_afford
    # cash >= total_cost allows exact matches
    pass
```

### Edge Case 3: Fractional Shares

```python
def prevent_fractional_shares(quantity: any) -> tuple[bool, str]:
    """Ensure quantity is integer (no fractional shares)

    Args:
        quantity: Quantity input

    Returns:
        (is_valid, message)
    """
    if not isinstance(quantity, int):
        try:
            quantity = int(quantity)
            return True, f"Rounded to {quantity} shares"
        except:
            return False, "Quantity must be a whole number"

    return True, "OK"
```

### Edge Case 4: Same-Day Buy and Sell

```python
def handle_same_day_round_trip(
    symbol: str,
    action: str,
    trade_history: list
) -> Optional[str]:
    """Detect same-day buy and sell (day trading)

    This is educational - warn about short-term trading

    Args:
        symbol: Stock symbol
        action: Current action
        trade_history: List of trades today

    Returns:
        Warning message if applicable
    """
    from datetime import datetime

    today_trades = [
        t for t in trade_history
        if t.date.date() == datetime.now().date() and t.symbol == symbol
    ]

    if action == "SELL" and any(t.action == "BUY" for t in today_trades):
        return "Note: Day trading detected. Long-term investing usually performs better."

    return None
```

### Edge Case 5: Position Averaging

```python
def explain_position_averaging(
    existing_avg: float,
    existing_qty: int,
    new_price: float,
    new_qty: int
) -> dict:
    """Explain how averaging works

    Args:
        existing_avg: Current average buy price
        existing_qty: Current quantity
        new_price: Price of new purchase
        new_qty: Quantity of new purchase

    Returns:
        Dict with explanation
    """
    total_qty = existing_qty + new_qty
    total_cost = (existing_qty * existing_avg) + (new_qty * new_price)
    new_avg = total_cost / total_qty

    direction = "down" if new_price < existing_avg else "up"

    return {
        'new_avg_price': new_avg,
        'total_quantity': total_qty,
        'direction': direction,
        'explanation': f"Averaging {direction}: {existing_qty}@₹{existing_avg:.2f} + {new_qty}@₹{new_price:.2f} = {total_qty}@₹{new_avg:.2f}"
    }
```

---

## Testing Edge Cases

```python
import pytest
from src.engine.trade_executor import TradeExecutor
from src.models import Portfolio, Position

def test_buy_with_exact_cash():
    """Test buying when cost exactly matches cash"""
    portfolio = Portfolio(cash=10030.0)  # 10000 + 30 commission

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 100, 100.0  # 100 shares @ ₹100
    )

    # Commission is ₹3 (0.03% of 10000)
    # Total cost = 10003
    assert result.success
    assert portfolio.cash < 30  # Should have small amount left


def test_buy_insufficient_funds():
    """Test buying without enough cash"""
    portfolio = Portfolio(cash=5000.0)

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 100, 100.0  # Need ₹10,003
    )

    assert not result.success
    assert "Insufficient funds" in result.message
    assert portfolio.cash == 5000.0  # Unchanged


def test_sell_entire_position():
    """Test selling all shares of a position"""
    portfolio = Portfolio(
        cash=10000.0,
        positions=[Position("TEST", 50, 100.0, 100.0)]
    )

    result = TradeExecutor.execute_sell(
        portfolio, "TEST", 50, 110.0  # Sell all at profit
    )

    assert result.success
    assert len(portfolio.positions) == 0  # Position removed
    assert portfolio.cash > 10000.0  # Cash increased


def test_sell_more_than_owned():
    """Test selling more shares than owned"""
    portfolio = Portfolio(
        cash=10000.0,
        positions=[Position("TEST", 50, 100.0, 100.0)]
    )

    result = TradeExecutor.execute_sell(
        portfolio, "TEST", 100, 110.0  # Try to sell 100, only have 50
    )

    assert not result.success
    assert "only own 50" in result.message.lower()


def test_position_averaging_up():
    """Test averaging up (buying at higher price)"""
    portfolio = Portfolio(
        cash=50000.0,
        positions=[Position("TEST", 100, 100.0, 110.0)]
    )

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 50, 120.0  # Buy 50 more at ₹120
    )

    assert result.success
    position = portfolio.get_position("TEST")
    assert position.quantity == 150

    # Calculate expected average
    expected_avg = ((100 * 100) + (50 * 120)) / 150
    assert abs(position.avg_buy_price - expected_avg) < 0.01


def test_position_averaging_down():
    """Test averaging down (buying at lower price)"""
    portfolio = Portfolio(
        cash=50000.0,
        positions=[Position("TEST", 100, 120.0, 110.0)]
    )

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 100, 100.0  # Buy 100 more at ₹100
    )

    assert result.success
    position = portfolio.get_position("TEST")
    assert position.quantity == 200

    # Average should be lower than original 120
    assert position.avg_buy_price < 120.0
    assert position.avg_buy_price > 100.0
```

---

## Integration with UI

### Trade Modal Data Flow

```python
def handle_trade_modal_result(result: dict, game_state, market_data) -> TradeResult:
    """Process trade from UI modal

    Args:
        result: Dict from TradeModal (symbol, action, quantity)
        game_state: Current game state
        market_data: MarketDataLoader instance

    Returns:
        TradeResult
    """
    # Extract values
    symbol = result['symbol']
    action = result['action']
    quantity = result['quantity']

    # Get current price
    price = market_data.get_current_price(symbol)

    if price <= 0:
        return TradeResult(
            success=False,
            message=f"Could not get price for {symbol}"
        )

    # Execute trade
    portfolio = game_state.portfolio

    if action == "BUY":
        trade_result = TradeExecutor.execute_buy(
            portfolio, symbol, quantity, price
        )
    else:
        trade_result = TradeExecutor.execute_sell(
            portfolio, symbol, quantity, price
        )

    return trade_result
```

---

## Validation Checklist

### Trade Execution
- [ ] Buy order validates funds
- [ ] Sell order validates holdings
- [ ] Commission calculated correctly
- [ ] Cash updated correctly
- [ ] Positions updated correctly
- [ ] Can't sell more than owned
- [ ] Can't buy with insufficient funds

### Position Management
- [ ] New position created correctly
- [ ] Existing position updated (averaging)
- [ ] Position removed when quantity = 0
- [ ] Average price calculated correctly

### Edge Cases
- [ ] Zero price handled
- [ ] Exact cash match works
- [ ] Integer quantity enforced
- [ ] Large trades validated
- [ ] Small trades validated

---

## Quick Reference

### Import Statements

```python
from src.engine.trade_executor import TradeExecutor, TradeResult
from src.models import Portfolio, Position
```

### Common Code Snippets

```python
# Execute buy
result = TradeExecutor.execute_buy(portfolio, "RELIANCE", 10, 2500.0)

# Execute sell
result = TradeExecutor.execute_sell(portfolio, "TCS", 5, 3500.0)

# Estimate trade
estimate = TradeExecutor.estimate_trade("BUY", 10, 2500.0, current_cash=50000)

# Calculate commission
commission = CommissionCalculator.calculate(25000)  # ₹25k trade
```

---

This document provides all trading logic patterns needed for Stage 4 implementation.

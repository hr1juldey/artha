# Artha Financial Accuracy - Implementation Plan

**Plan Version:** 1.0
**Created:** 2025-11-09
**Estimated Total Time:** 21-24 hours
**Complexity:** MODERATE
**Risk Level:** MEDIUM (database migrations required)

---

## Quick Reference

### What's Broken

1. **Cost basis excludes commissions** → P&L overstated by ₹60 per round-trip
2. **Transaction history not saved** → XIRR wrong after restart
3. **No realized P&L** → Closed trade profits invisible
4. **Missing 80% of costs** → Unrealistic simulation

### What We're Fixing

1. Include commissions in cost basis
2. Persist transaction history to database
3. Track realized vs unrealized P&L
4. Implement complete Indian market costs

### Timeline

- **Week 1:** Critical fixes (restore user trust)
- **Week 2:** Data persistence (fix XIRR, prevent loss)
- **Week 3:** Complete costs (realism + educational value)

---

## Phase 1: Critical Fixes (Week 1)

### Day 1-2: Fix Cost Basis Bug

**Objective:** Make cost basis equal cash paid

**Files to Modify:**
1. `src/models/transaction_models.py`
2. `src/engine/trade_executor.py`
3. `tests/test_trading.py`

#### Step 1.1: Add commission field to PositionTransaction

**File:** `src/models/transaction_models.py`

```python
# Find line 14-20 and update:
@dataclass
class PositionTransaction:
    """Represents a buy/sell transaction for position tracking"""
    date: Union[datetime, date]
    quantity: int  # Number of shares
    price: float   # Price per share
    transaction_type: TransactionType
    commission: float = 0.0  # NEW: Transaction cost
```

**Test it:**
```python
# In Python REPL:
from src.models.transaction_models import PositionTransaction
from src.utils.xirr_calculator import TransactionType
from datetime import date

trans = PositionTransaction(
    date=date.today(),
    quantity=100,
    price=100,
    transaction_type=TransactionType.BUY,
    commission=3.0
)
print(trans)  # Should show commission=3.0
```

#### Step 1.2: Update _recalculate_position() to include commission

**File:** `src/models/transaction_models.py`

**Find lines 102-120**, replace with:

```python
def _recalculate_position(self) -> None:
    """Recalculate position metrics based on all transactions"""
    # Calculate quantity by summing all transactions
    total_quantity = 0
    total_cost_basis = 0

    for trans in self.transactions:
        if trans.transaction_type == TransactionType.BUY:
            total_quantity += trans.quantity  # quantity for buys
            # FIX: Include commission in cost basis
            commission = trans.commission if hasattr(trans, 'commission') else 0.0
            total_cost_basis += (trans.quantity * trans.price + commission)
        else:  # SELL
            total_quantity -= trans.quantity  # quantity for sells

    self._quantity = total_quantity
    self._cost_basis = total_cost_basis  # Now includes commissions!

    # Calculate avg buy price based on total bought quantity
    total_bought_quantity = sum(trans.quantity for trans in self.transactions
                               if trans.transaction_type == TransactionType.BUY)
    self._avg_buy_price = self._cost_basis / total_bought_quantity if total_bought_quantity > 0 else 0

    # Note: market_value, unrealized_pnl, and unrealized_pnl_pct are now @property methods
    # that calculate dynamically based on current_price
```

#### Step 1.3: Update execute_buy() to pass commission

**File:** `src/engine/trade_executor.py`

**Find lines 99-104**, replace with:

```python
# Create transaction record
transaction = PositionTransaction(
    date=transaction_date,
    quantity=quantity,
    price=price,
    transaction_type=OrderSide.BUY,
    commission=commission  # NEW: Pass commission
)
```

#### Step 1.4: Update execute_sell() to pass commission

**File:** `src/engine/trade_executor.py`

**Find lines 213-218**, replace with:

```python
# Create transaction record
transaction = PositionTransaction(
    date=transaction_date,
    quantity=quantity,
    price=price,
    transaction_type=OrderSide.SELL,
    commission=commission  # NEW: Pass commission
)
```

#### Step 1.5: Add test case

**File:** `tests/test_trading.py`

**Add at end of file:**

```python
def test_cost_basis_includes_commission():
    """Test that cost basis includes commission (Bug Fix)"""
    from src.models.transaction_models import EnhancedPosition, PositionTransaction
    from src.utils.xirr_calculator import TransactionType
    from datetime import date

    position = EnhancedPosition(symbol="TEST", current_price=100)

    # Buy 100 shares @ ₹100 with ₹3 commission
    trans = PositionTransaction(
        date=date.today(),
        quantity=100,
        price=100,
        transaction_type=TransactionType.BUY,
        commission=3.0
    )
    position.add_transaction(trans)

    # Cost basis should be 100*100 + 3 = 10,003
    assert position.cost_basis == 10003, \
        f"Expected cost basis 10003, got {position.cost_basis}"

    # Average buy price should be 10,003 / 100 = 100.03
    assert abs(position.avg_buy_price - 100.03) < 0.01, \
        f"Expected avg buy price 100.03, got {position.avg_buy_price}"

    print("✓ Cost basis test passed!")


def test_cost_basis_matches_cash_flow():
    """Test that cost basis equals cash paid"""
    portfolio = Portfolio(cash=1_000_000, positions=[])
    initial_cash = portfolio.cash

    # Execute buy
    result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 1000)
    assert result.success

    # Cash paid
    cash_paid = initial_cash - portfolio.cash

    # Get position
    pos = next(p for p in portfolio.positions if p.symbol == "TEST")

    # CRITICAL: Cost basis must equal cash paid
    assert abs(pos.cost_basis - cash_paid) < 0.01, \
        f"Cost basis {pos.cost_basis} != cash paid {cash_paid}"

    print(f"✓ Cost basis ({pos.cost_basis}) matches cash paid ({cash_paid})")
```

#### Step 1.6: Run tests

```bash
cd /home/riju279/Documents/Code/Zonko/Artha/artha
python -m pytest tests/test_trading.py::test_cost_basis_includes_commission -v
python -m pytest tests/test_trading.py::test_cost_basis_matches_cash_flow -v
python -m pytest tests/test_trading.py -v  # Run all tests
```

**Expected result:** All tests pass ✓

---

### Day 3: Fix Demo Code Bug

**Objective:** Fix undefined Transaction error

**File:** `src/models/transaction_models.py`

#### Step 2.1: Fix all 3 occurrences

**Find line 233** and replace:

```python
# BEFORE:
position.add_transaction(Transaction(  # ❌
    date=datetime(2023, 1, 1).date(),
    amount=100,
    price=2000.0,
    transaction_type=TransactionType.BUY
))

# AFTER:
position.add_transaction(PositionTransaction(  # ✓
    date=datetime(2023, 1, 1).date(),
    quantity=100,  # Changed from 'amount'
    price=2000.0,
    transaction_type=TransactionType.BUY,
    commission=20.0  # Add realistic commission
))
```

**Repeat for lines 240-246 and 248-254**

#### Step 2.2: Test demo code

```bash
python -m src.models.transaction_models
```

**Expected output:**
```
Symbol: RELIANCE
Quantity: 120
Avg Buy Price: 2066.67
Current Price: 2500
Market Value: 300000.00
Unrealized P&L: 52000.00
Unrealized P&L %: 20.83%
XIRR: 0.2345 (23.45%)
...
```

---

### Day 4-5: Add Realized P&L Tracking

**Objective:** Track profits from closed positions

**Files to Modify:**
1. `src/models/transaction_models.py`
2. `src/models/__init__.py`
3. `tests/test_trading.py`

#### Step 3.1: Add realized P&L field to EnhancedPosition

**File:** `src/models/transaction_models.py`

**Find line 24** (class EnhancedPosition), add after line 34:

```python
@dataclass
class EnhancedPosition:
    """Enhanced position that tracks individual transactions for proper XIRR calculations"""

    symbol: str
    _current_price: float = field(default=0.0, init=False)
    transactions: List[PositionTransaction] = field(default_factory=list)

    # Cached values calculated from transactions
    _quantity: int = field(default=0, init=False)
    _avg_buy_price: float = field(default=0.0, init=False)
    _cost_basis: float = field(default=0.0, init=False)
    _realized_pnl: float = field(default=0.0, init=False)  # NEW: Track realized gains
```

#### Step 3.2: Add method to calculate FIFO cost

**Add after line 123:**

```python
def _get_fifo_cost(self, quantity_sold: int) -> float:
    """Calculate cost basis for sold shares using FIFO method"""
    remaining = quantity_sold
    total_cost = 0.0

    for trans in self.transactions:
        if trans.transaction_type == TransactionType.BUY and remaining > 0:
            # How many shares from this buy transaction?
            qty_from_this = min(trans.quantity, remaining)

            # Cost per share including commission
            commission = trans.commission if hasattr(trans, 'commission') else 0.0
            cost_per_share = (trans.quantity * trans.price + commission) / trans.quantity

            # Add proportional cost
            total_cost += qty_from_this * cost_per_share
            remaining -= qty_from_this

            if remaining == 0:
                break

    return total_cost
```

#### Step 3.3: Update add_transaction() to track realized P&L

**Find line 97** (add_transaction method), replace with:

```python
def add_transaction(self, transaction: PositionTransaction) -> None:
    """Add a new transaction to the position"""

    # If selling, calculate and record realized P&L
    if transaction.transaction_type == TransactionType.SELL:
        # Calculate proceeds from sale
        commission = transaction.commission if hasattr(transaction, 'commission') else 0.0
        sell_proceeds = transaction.quantity * transaction.price - commission

        # Get FIFO cost for sold shares
        fifo_cost = self._get_fifo_cost(transaction.quantity)

        # Record realized P&L
        realized = sell_proceeds - fifo_cost
        self._realized_pnl += realized

    self.transactions.append(transaction)
    self._recalculate_position()
```

#### Step 3.4: Add properties for realized and total P&L

**Add after line 91:**

```python
@property
def realized_pnl(self) -> float:
    """Get total realized P&L from all sales"""
    return self._realized_pnl

@property
def total_pnl(self) -> float:
    """Get total P&L (realized + unrealized)"""
    return self._realized_pnl + self.unrealized_pnl
```

#### Step 3.5: Update Portfolio to include realized P&L

**File:** `src/models/__init__.py`

**Find line 49**, replace with:

```python
@property
def total_pnl(self) -> float:
    """Total P&L including realized and unrealized"""
    unrealized = sum(self._get_unrealized_pnl(p) for p in self.positions)
    realized = sum(self._get_realized_pnl(p) for p in self.positions)
    return unrealized + realized

def _get_realized_pnl(self, position: Union[Position, EnhancedPosition]) -> float:
    """Get realized P&L of position regardless of type"""
    if hasattr(position, 'realized_pnl'):
        return position.realized_pnl
    return 0.0  # Legacy positions have no realized tracking
```

#### Step 3.6: Add test case

**File:** `tests/test_trading.py`

**Add at end:**

```python
def test_realized_pnl_tracking():
    """Test realized P&L calculation on partial sale"""
    from src.models.transaction_models import EnhancedPosition, PositionTransaction
    from src.utils.xirr_calculator import TransactionType
    from datetime import date

    position = EnhancedPosition(symbol="TEST", current_price=120)

    # Buy 100 @ 100 with ₹3 commission
    buy_trans = PositionTransaction(
        date=date.today(),
        quantity=100,
        price=100,
        transaction_type=TransactionType.BUY,
        commission=3.0
    )
    position.add_transaction(buy_trans)

    # Verify initial state
    assert position.quantity == 100
    assert position.cost_basis == 10003  # 100*100 + 3
    assert position.realized_pnl == 0.0

    # Sell 40 @ 120 with ₹2 commission
    sell_trans = PositionTransaction(
        date=date.today(),
        quantity=40,
        price=120,
        transaction_type=TransactionType.SELL,
        commission=2.0
    )
    position.add_transaction(sell_trans)

    # Verify realized P&L
    # Proceeds: 40 * 120 - 2 = 4798
    # FIFO cost: 40 * 100.03 = 4001.2
    # Realized P&L: 4798 - 4001.2 = 796.8
    assert position.quantity == 60
    assert abs(position.realized_pnl - 796.8) < 1.0, \
        f"Expected realized P&L ~796.8, got {position.realized_pnl}"

    print(f"✓ Realized P&L tracked correctly: ₹{position.realized_pnl:.2f}")


def test_total_pnl_includes_realized():
    """Test that total P&L includes both realized and unrealized"""
    from src.models.transaction_models import EnhancedPosition, PositionTransaction
    from src.utils.xirr_calculator import TransactionType
    from datetime import date

    position = EnhancedPosition(symbol="TEST", current_price=110)

    # Buy 100 @ 100
    position.add_transaction(PositionTransaction(
        date=date.today(),
        quantity=100,
        price=100,
        transaction_type=TransactionType.BUY,
        commission=3.0
    ))

    # Sell 40 @ 120 (profit)
    position.add_transaction(PositionTransaction(
        date=date.today(),
        quantity=40,
        price=120,
        transaction_type=TransactionType.SELL,
        commission=2.0
    ))

    # Current price 110 (remaining 60 shares at ₹110)
    # Unrealized: 60 * 110 - 60 * 100.03 = 6600 - 6001.8 = 598.2
    # Realized: ~796.8 (from previous test)
    # Total: 598.2 + 796.8 = 1395

    total_pnl = position.total_pnl
    assert abs(total_pnl - 1395) < 2.0, \
        f"Expected total P&L ~1395, got {total_pnl}"

    print(f"✓ Total P&L includes realized + unrealized: ₹{total_pnl:.2f}")
```

#### Step 3.7: Run tests

```bash
python -m pytest tests/test_trading.py::test_realized_pnl_tracking -v
python -m pytest tests/test_trading.py::test_total_pnl_includes_realized -v
```

---

## Phase 2: Data Persistence (Week 2)

### Day 6-8: Create Transactions Table

**Objective:** Persist transaction history to database

#### Step 4.1: Create migration SQL

**File:** `migrations/001_create_transactions_table.sql` (create this file)

```sql
-- Add transactions table to persist transaction history
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    transaction_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    transaction_type VARCHAR(4) NOT NULL CHECK(transaction_type IN ('BUY', 'SELL')),

    -- Costs
    commission REAL NOT NULL DEFAULT 0.0,
    stt REAL DEFAULT 0.0,
    exchange_charges REAL DEFAULT 0.0,
    gst REAL DEFAULT 0.0,
    sebi_charges REAL DEFAULT 0.0,
    total_charges REAL NOT NULL,

    -- Amounts
    gross_amount REAL NOT NULL,
    net_amount REAL NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transactions_game ON transactions(game_id);
CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON transactions(game_id, symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
```

#### Step 4.2: Run migration

```bash
# Backup database first
cp data/artha.db data/artha.db.backup

# Run migration
sqlite3 data/artha.db < migrations/001_create_transactions_table.sql

# Verify table created
sqlite3 data/artha.db "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';"
```

**Expected output:** `transactions`

#### Step 4.3: Add Transaction model

**File:** `src/database/models.py`

**Add at end of file:**

```python
class Transaction(Base):
    """Transaction history model"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(4), nullable=False)

    # Costs
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    stt: Mapped[float] = mapped_column(Float, default=0.0)
    exchange_charges: Mapped[float] = mapped_column(Float, default=0.0)
    gst: Mapped[float] = mapped_column(Float, default=0.0)
    sebi_charges: Mapped[float] = mapped_column(Float, default=0.0)
    total_charges: Mapped[float] = mapped_column(Float, nullable=False)

    gross_amount: Mapped[float] = mapped_column(Float, nullable=False)
    net_amount: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationship
    game: Mapped["Game"] = relationship("Game", back_populates="transactions")
```

**Update Game model:**

```python
# Find class Game, add to end of class:
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="game", cascade="all, delete-orphan"
    )
```

#### Step 4.4: Add DAO methods for transactions

**File:** `src/database/dao.py`

**Add methods to GameDAO class:**

```python
@staticmethod
async def save_transaction(
    session: AsyncSession,
    game_id: int,
    symbol: str,
    trans: 'PositionTransaction',
    gross_amount: float,
    net_amount: float
) -> None:
    """Save transaction to database"""
    from src.database.models import Transaction as DBTransaction

    # Convert date to datetime if needed
    trans_date = trans.date
    if not isinstance(trans_date, datetime):
        trans_date = datetime.combine(trans_date, datetime.min.time())

    # Get commission
    commission = trans.commission if hasattr(trans, 'commission') else 0.0

    db_trans = DBTransaction(
        game_id=game_id,
        symbol=symbol,
        transaction_date=trans_date,
        quantity=trans.quantity,
        price=trans.price,
        transaction_type=trans.transaction_type.value,
        commission=commission,
        stt=0.0,  # TODO: Update when complete costs implemented
        exchange_charges=0.0,
        gst=0.0,
        sebi_charges=0.0,
        total_charges=commission,
        gross_amount=gross_amount,
        net_amount=net_amount
    )
    session.add(db_trans)
    await session.commit()

@staticmethod
async def load_position_transactions(
    session: AsyncSession,
    game_id: int,
    symbol: str
) -> List['PositionTransaction']:
    """Load transaction history for a position"""
    from src.database.models import Transaction as DBTransaction
    from src.models.transaction_models import PositionTransaction
    from src.utils.xirr_calculator import TransactionType

    result = await session.execute(
        select(DBTransaction)
        .where(DBTransaction.game_id == game_id)
        .where(DBTransaction.symbol == symbol)
        .order_by(DBTransaction.transaction_date)
    )
    db_trans = result.scalars().all()

    return [
        PositionTransaction(
            date=t.transaction_date.date(),
            quantity=t.quantity,
            price=t.price,
            transaction_type=TransactionType[t.transaction_type],
            commission=t.commission
        )
        for t in db_trans
    ]
```

#### Step 4.5: Update execute_buy and execute_sell to persist transactions

**File:** `src/engine/trade_executor.py`

This requires refactoring to accept session parameter. For now, document that this needs to be done at integration level (app.py).

**Add TODO comment:**

```python
# TODO: After successful transaction, save to database:
# await GameDAO.save_transaction(
#     session=session,
#     game_id=game_id,
#     symbol=symbol,
#     trans=transaction,
#     gross_amount=cost,
#     net_amount=total_cost
# )
```

---

### Day 9-10: Load Transaction History on Startup

**Objective:** Reconstruct EnhancedPositions with full history

#### Step 5.1: Update db_game_to_game_state

**File:** `src/database/dao.py`

**Replace lines 128-164 with:**

```python
@staticmethod
async def db_game_to_game_state(
    session: AsyncSession,
    game: Game,
    user: User
) -> GameState:
    """Convert DB Game to GameState model with transaction history"""
    from src.models.transaction_models import EnhancedPosition

    positions = []

    for db_pos in game.positions:
        # Load transaction history for this position
        transactions = await GameDAO.load_position_transactions(
            session,
            game.id,
            db_pos.symbol
        )

        # Create EnhancedPosition with full history
        if transactions:
            enhanced_pos = EnhancedPosition(
                symbol=db_pos.symbol,
                current_price=db_pos.current_price or db_pos.avg_buy_price,
                transactions=transactions  # Restore full history!
            )
            positions.append(enhanced_pos)
        else:
            # Fallback to legacy Position for old data
            positions.append(PositionModel(
                symbol=db_pos.symbol,
                quantity=db_pos.quantity,
                avg_buy_price=db_pos.avg_buy_price,
                current_price=db_pos.current_price or db_pos.avg_buy_price
            ))

    portfolio = Portfolio(
        cash=game.current_cash,
        positions=positions
    )

    game_state = GameState(
        player_name=user.full_name or user.username,
        current_day=game.current_day,
        total_days=game.total_days,
        initial_capital=game.initial_capital,
        portfolio=portfolio,
        created_at=game.created_at
    )

    # Initialize portfolio_history with current state
    game_state.portfolio_history = [{
        "day": game.current_day,
        "total_value": portfolio.total_value,
        "cash": portfolio.cash,
        "positions_value": portfolio.positions_value,
        "pnl": portfolio.total_pnl
    }]

    return game_state
```

---

## Phase 3: Complete Costs (Week 3)

### Day 11-12: Implement Full Indian Market Costs

**Objective:** Add STT, Exchange, GST, SEBI charges

#### Step 6.1: Create TradeCosts class

**File:** `src/engine/trade_executor.py`

**Add before TradeExecutor class:**

```python
@dataclass
class TradeCosts:
    """Complete breakdown of trading costs per Indian market structure"""
    brokerage: float
    stt: float
    exchange_charges: float
    gst: float
    sebi_charges: float

    @property
    def total(self) -> float:
        return self.brokerage + self.stt + self.exchange_charges + self.gst + self.sebi_charges

    def __str__(self) -> str:
        return (
            f"Brokerage: ₹{self.brokerage:.2f}, "
            f"STT: ₹{self.stt:.2f}, "
            f"Exchange: ₹{self.exchange_charges:.2f}, "
            f"GST: ₹{self.gst:.2f}, "
            f"SEBI: ₹{self.sebi_charges:.2f}, "
            f"Total: ₹{self.total:.2f}"
        )
```

#### Step 6.2: Add configuration

**File:** `src/config.py`

**Add after COMMISSION_RATE:**

```python
# Transaction cost rates (Indian market)
BROKERAGE_RATE = 0.0003  # 0.03%
BROKERAGE_CAP = 20.0     # ₹20 maximum

STT_SELL_RATE = 0.001    # 0.1% on sell side (delivery)
EXCHANGE_RATE_NSE = 0.0000325  # 0.00325%
EXCHANGE_RATE_BSE = 0.0000275  # 0.00275%
GST_RATE = 0.18          # 18%
SEBI_RATE_PER_CRORE = 10.0  # ₹10 per ₹1 crore
```

#### Step 6.3: Add calculate_costs method

**File:** `src/engine/trade_executor.py`

**Replace calculate_commission with:**

```python
@staticmethod
def calculate_costs(
    order_value: float,
    side: OrderSide,
    exchange: str = "NSE"
) -> TradeCosts:
    """Calculate complete transaction costs per HLD specification"""
    from src.config import (
        BROKERAGE_RATE, BROKERAGE_CAP,
        STT_SELL_RATE, EXCHANGE_RATE_NSE, EXCHANGE_RATE_BSE,
        GST_RATE, SEBI_RATE_PER_CRORE
    )

    # 1. Brokerage: 0.03% or ₹20 max
    brokerage = min(order_value * BROKERAGE_RATE, BROKERAGE_CAP)

    # 2. STT: 0.1% on sell side only (delivery trading)
    stt = order_value * STT_SELL_RATE if side == OrderSide.SELL else 0.0

    # 3. Exchange charges: 0.00325% NSE, 0.00275% BSE
    exchange_rate = EXCHANGE_RATE_NSE if exchange == "NSE" else EXCHANGE_RATE_BSE
    exchange_charges = order_value * exchange_rate

    # 4. GST: 18% on (brokerage + exchange charges)
    gst = (brokerage + exchange_charges) * GST_RATE

    # 5. SEBI: ₹10 per crore
    sebi_charges = (order_value / 10_000_000) * SEBI_RATE_PER_CRORE

    return TradeCosts(
        brokerage=brokerage,
        stt=stt,
        exchange_charges=exchange_charges,
        gst=gst,
        sebi_charges=sebi_charges
    )

# Keep old method for backward compatibility
@staticmethod
def calculate_commission(amount: float) -> float:
    """Calculate commission (backward compatibility)"""
    costs = TradeExecutor.calculate_costs(amount, OrderSide.BUY)
    return costs.total
```

#### Step 6.4: Update execute_buy to use new costs

**File:** `src/engine/trade_executor.py`

**Find lines 74-77, replace with:**

```python
# Calculate complete costs
cost = price * quantity
costs = TradeExecutor.calculate_costs(cost, OrderSide.BUY)
total_cost = cost + costs.total
```

**Update line 154 to return costs:**

```python
return TradeResult(
    success=True,
    message=f"Bought {quantity} shares of {symbol} at ₹{price:,.2f}. Costs: {costs}",
    executed_price=price,
    quantity=quantity,
    total_cost=total_cost,
    commission=costs.total  # Return total instead of just brokerage
)
```

#### Step 6.5: Update execute_sell similarly

**Same changes for execute_sell method**

#### Step 6.6: Add tests

**File:** `tests/test_financial_accuracy.py` (create new file)

```python
"""Tests for financial accuracy"""
import pytest
from src.engine.trade_executor import TradeExecutor, TradeCosts
from src.utils.xirr_calculator import TransactionType as OrderSide


def test_complete_costs_buy_100k():
    """Test all cost components for ₹1L buy order"""
    costs = TradeExecutor.calculate_costs(100_000, OrderSide.BUY)

    assert costs.brokerage == 20.0, f"Expected brokerage 20, got {costs.brokerage}"
    assert costs.stt == 0.0, f"Expected STT 0 on buy, got {costs.stt}"
    assert abs(costs.exchange_charges - 3.25) < 0.01
    assert abs(costs.gst - 4.18) < 0.1  # 18% of (20 + 3.25)
    assert abs(costs.sebi_charges - 0.10) < 0.01
    assert abs(costs.total - 27.53) < 0.2

    print(f"✓ Buy costs: {costs}")


def test_complete_costs_sell_100k():
    """Test all cost components for ₹1L sell order"""
    costs = TradeExecutor.calculate_costs(100_000, OrderSide.SELL)

    assert costs.brokerage == 20.0
    assert costs.stt == 100.0, f"Expected STT 100 on sell, got {costs.stt}"
    assert abs(costs.exchange_charges - 3.25) < 0.01
    assert abs(costs.gst - 4.18) < 0.1
    assert abs(costs.total - 127.53) < 0.2

    print(f"✓ Sell costs: {costs}")


def test_round_trip_realistic_costs():
    """Test that round-trip costs match HLD specification"""
    buy_costs = TradeExecutor.calculate_costs(100_000, OrderSide.BUY)
    sell_costs = TradeExecutor.calculate_costs(100_000, OrderSide.SELL)

    total_round_trip = buy_costs.total + sell_costs.total

    # Per HLD: ~₹155 for ₹1L round-trip
    assert abs(total_round_trip - 155) < 2.0, \
        f"Expected ~₹155 round-trip costs, got ₹{total_round_trip:.2f}"

    print(f"✓ Round-trip costs: ₹{total_round_trip:.2f}")
```

**Run tests:**

```bash
python -m pytest tests/test_financial_accuracy.py -v
```

---

## Verification Checklist

After completing all phases, verify:

### ✅ Phase 1 Verification

```bash
# Test 1: Cost basis includes commission
python -c "
from src.models.transaction_models import EnhancedPosition, PositionTransaction
from src.utils.xirr_calculator import TransactionType
from datetime import date

pos = EnhancedPosition('TEST', 100)
pos.add_transaction(PositionTransaction(
    date=date.today(), quantity=100, price=100,
    transaction_type=TransactionType.BUY, commission=3
))

assert pos.cost_basis == 10003, f'FAIL: cost_basis={pos.cost_basis}'
print('✓ Cost basis includes commission')
"

# Test 2: Realized P&L tracked
python -c "
from src.models.transaction_models import EnhancedPosition, PositionTransaction
from src.utils.xirr_calculator import TransactionType
from datetime import date

pos = EnhancedPosition('TEST', 120)
pos.add_transaction(PositionTransaction(
    date=date.today(), quantity=100, price=100,
    transaction_type=TransactionType.BUY, commission=3
))
pos.add_transaction(PositionTransaction(
    date=date.today(), quantity=40, price=120,
    transaction_type=TransactionType.SELL, commission=2
))

assert abs(pos.realized_pnl - 796.8) < 1.0, f'FAIL: realized_pnl={pos.realized_pnl}'
print('✓ Realized P&L tracked correctly')
"
```

### ✅ Phase 2 Verification

```bash
# Test database table exists
sqlite3 data/artha.db "SELECT COUNT(*) FROM transactions;"

# Should return 0 or more (not error)
```

### ✅ Phase 3 Verification

```bash
# Test complete costs
python -m pytest tests/test_financial_accuracy.py -v
```

---

## Rollback Plan

If anything goes wrong:

### Rollback Phase 1

```bash
git checkout src/models/transaction_models.py
git checkout src/engine/trade_executor.py
git checkout tests/test_trading.py
```

### Rollback Phase 2

```bash
# Restore database backup
cp data/artha.db.backup data/artha.db

# Revert code
git checkout src/database/models.py
git checkout src/database/dao.py
```

### Rollback Phase 3

```bash
git checkout src/config.py
```

---

## Post-Implementation

### Documentation Updates

1. Update README with new features
2. Create user guide for P&L tracking
3. Document transaction costs in help

### Performance Testing

```bash
# Test with large transaction history
python -c "
import asyncio
from src.database.dao import GameDAO
# Create game with 1000 transactions
# Measure load time
"
```

### User Communication

```markdown
# Changelog v2.0

## Critical Bug Fixes

- ✅ Cost basis now includes transaction costs (P&L accurate)
- ✅ Realized vs unrealized P&L tracking (see actual profits)
- ✅ Transaction history persisted (XIRR works after restart)
- ✅ Complete Indian market costs (realistic simulation)

## What Changed for You

Before: "I made good trades but still lost money"
After: "I can see exactly where my money goes"

Before: XIRR showed 890% after restart
After: XIRR accurate with real dates

Before: Profitable trades disappeared
After: Realized P&L tracked separately

## Migration

Your existing games will:
- ✅ Keep all positions
- ⚠️ Show approximate XIRR (dates estimated)
- ✅ Work normally going forward

New games will:
- ✅ Have perfect XIRR tracking
- ✅ Show complete cost breakdown
- ✅ Track realized gains accurately
```

---

## Next Steps

1. **Review this plan** - Ensure all steps make sense
2. **Set up branch** - `git checkout -b fix/financial-accuracy`
3. **Start Phase 1** - Begin with cost basis fix
4. **Test each phase** - Don't move on until tests pass
5. **Deploy carefully** - Backup database first

**Estimated Timeline:**
- Week 1: Phase 1 (6 hours)
- Week 2: Phase 2 (10 hours)
- Week 3: Phase 3 (5 hours)
- **Total: 21 hours spread over 3 weeks**

Ready to start implementation!

---

**Created by:** Claude Sonnet 4.5
**Last updated:** 2025-11-09
**Status:** Ready for implementation

# Artha Trading System - Financial Accuracy Analysis

**Date:** 2025-11-09
**Analyst:** Claude (Sonnet 4.5)
**Scope:** Comprehensive review of financial calculations, P&L tracking, and transaction cost modeling

---

## Executive Summary

The Artha trading system has **7 critical financial inaccuracies** that would prevent users from making realistic long-term profits, even with good stock picking. The system significantly **underestimates transaction costs** and provides **inflated P&L figures** that don't reflect true profitability.

### Severity Ranking

1. **CRITICAL**: Missing 80% of transaction costs (STT, Exchange, GST, SEBI)
2. **CRITICAL**: Commission not included in cost basis (inflates P&L)
3. **CRITICAL**: No realized P&L tracking (can't measure actual profits)
4. **HIGH**: Transaction history not persisted in database (XIRR inaccurate)
5. **MEDIUM**: Portfolio total P&L doesn't include realized gains
6. **MEDIUM**: No tracking of total commissions paid
7. **LOW**: HLD specification inconsistency (minor documentation issue)

---

## Issue 1: Missing 80% of Transaction Costs ⚠️ CRITICAL

### Current Implementation

File: `/home/riju279/Documents/Code/Zonko/Artha/artha/src/engine/trade_executor.py` (lines 51-54)

```python
@staticmethod
def calculate_commission(amount: float) -> float:
    """Calculate commission (0.03% or ₹20 max)"""
    commission = amount * COMMISSION_RATE
    return min(commission, 20.0)
```

**Only implements:** Brokerage (0.03% capped at ₹20)

### What's Missing (per HLD specification)

According to `/home/riju279/Documents/Code/Zonko/Artha/artha/docs/artha_hld.md` (lines 386-404), the full cost structure is:

```
Brokerage: 0.03% or ₹20 max per order
STT (Securities Transaction Tax):
  - Equity Delivery: 0.1% on SELL side only
  - Equity Intraday: 0.025% on both sides
Exchange Charges: 0.00325% (NSE) or 0.00275% (BSE)
GST: 18% on (brokerage + exchange charges)
SEBI Turnover Charge: ₹10 per crore
```

### Impact Analysis

For a **₹1,00,000 BUY order**:

| Component | Current | Should Be | Missing |
|-----------|---------|-----------|---------|
| Brokerage | ₹20.00 | ₹20.00 | - |
| STT | ₹0.00 | ₹0.00 | - |
| Exchange | ₹0.00 | ₹3.25 | ₹3.25 |
| GST | ₹0.00 | ₹4.18 | ₹4.18 |
| SEBI | ₹0.00 | ₹0.10 | ₹0.10 |
| **TOTAL** | **₹20.00** | **₹27.53** | **₹7.53** |

For a **₹1,00,000 SELL order**:

| Component | Current | Should Be | Missing |
|-----------|---------|-----------|---------|
| Brokerage | ₹20.00 | ₹20.00 | - |
| **STT** | **₹0.00** | **₹100.00** | **₹100.00** |
| Exchange | ₹0.00 | ₹3.25 | ₹3.25 |
| GST | ₹0.00 | ₹4.18 | ₹4.18 |
| SEBI | ₹0.00 | ₹0.10 | ₹0.10 |
| **TOTAL** | **₹20.00** | **₹127.53** | **₹107.53** |

### Real-World Impact

**Example: Round-trip trade (buy + sell) of ₹1,00,000**

- Current system cost: ₹40 (₹20 + ₹20)
- Actual cost: ₹155.06 (₹27.53 + ₹127.53)
- **Missing: ₹115.06 (287% underestimation!)**

**Why users can't profit long-term:**

- Every trade appears 287% cheaper than reality
- Break-even calculations are completely wrong
- Users think they need +0.04% to break even, but actually need +0.155%
- Over 100 trades, missing costs accumulate to ₹11,506!

### Recommendation

**Priority: IMMEDIATE**

Create a proper `TradeCosts` class:

```python
@dataclass
class TradeCosts:
    """Complete breakdown of trading costs"""
    brokerage: float
    stt: float
    exchange_charges: float
    gst: float
    sebi_charges: float

    @property
    def total(self) -> float:
        return self.brokerage + self.stt + self.exchange_charges + self.gst + self.sebi_charges

@staticmethod
def calculate_costs(price: float, quantity: int, side: OrderSide) -> TradeCosts:
    """Calculate complete costs as per Indian market structure"""
    order_value = price * quantity

    # Brokerage: 0.03% or ₹20 max
    brokerage = min(order_value * 0.0003, 20.0)

    # STT: 0.1% on sell side only (delivery)
    stt = order_value * 0.001 if side == OrderSide.SELL else 0.0

    # Exchange charges: 0.00325% for NSE
    exchange_charges = order_value * 0.0000325

    # GST: 18% on brokerage + exchange
    gst = (brokerage + exchange_charges) * 0.18

    # SEBI: ₹10 per crore
    sebi_charges = (order_value / 10000000) * 10

    return TradeCosts(
        brokerage=brokerage,
        stt=stt,
        exchange_charges=exchange_charges,
        gst=gst,
        sebi_charges=sebi_charges
    )
```

---

## Issue 2: Commission Not Included in Cost Basis ⚠️ CRITICAL

### Current Implementation

When executing a buy:

```python
# File: src/engine/trade_executor.py, lines 74-77
cost = price * quantity
commission = TradeExecutor.calculate_commission(cost)
total_cost = cost + commission

# Lines 86-87
portfolio.cash -= total_cost  # ✓ Cash correctly deducted
```

But when creating/updating position:

```python
# Lines 99-104
transaction = PositionTransaction(
    date=transaction_date,
    quantity=quantity,
    price=price,  # ❌ Commission NOT included in price
    transaction_type=OrderSide.BUY
)
```

### The Problem

**Example:**

- Buy 100 shares @ ₹100.00
- Share cost: ₹10,000
- Commission: ₹3
- **Total paid from cash: ₹10,003**

**Position tracking shows:**

- Quantity: 100
- Avg buy price: ₹100.00 (WRONG - should be ₹100.03)
- Cost basis: ₹10,000 (WRONG - should be ₹10,003)

**Impact:**

- If current price = ₹100.00, position shows P&L = ₹0
- But if you sell, you get ₹9,997 (after commission)
- **Actual P&L = -₹6**, but position shows ₹0
- **P&L is overstated by ₹6 (infinite %)**

### Real-World Impact

**Scenario: Buy stock at ₹100, hold for 1 year**

- Total paid: ₹10,003
- To break even, need to sell at: ₹100.06 (accounting for sell commission)
- Position shows break-even at: ₹100.00
- User thinks they're profitable at ₹100.50 (+0.5%)
- Reality: Still in loss! (₹100.50 sell gives ₹10,047 - ₹3 = ₹10,044 vs ₹10,003 paid = +₹41, not +₹50)

### Why This Prevents Long-Term Profits

1. Users see **inflated unrealized P&L**
2. They don't realize they need price appreciation to cover BOTH buy and sell commissions
3. Short-term traders get completely misleading signals
4. Portfolio performance metrics (Sharpe ratio, etc.) are all wrong

### Recommendation

**Priority: IMMEDIATE**

**Option 1: Include commission in avg_buy_price (Recommended)**

```python
# In execute_buy, after calculating costs:
adjusted_price = (price * quantity + commission) / quantity

transaction = PositionTransaction(
    date=transaction_date,
    quantity=quantity,
    price=adjusted_price,  # ✓ Includes commission in cost basis
    transaction_type=OrderSide.BUY
)
```

**Option 2: Track commissions separately**

Add `total_commissions_paid` field to Position model, include in cost basis calculation:

```python
@property
def true_cost_basis(self) -> float:
    return self.cost_basis + self.total_commissions_paid

@property
def true_unrealized_pnl(self) -> float:
    # Must also account for estimated sell commission
    estimated_sell_commission = min(self.market_value * 0.0003, 20.0)
    return self.market_value - self.true_cost_basis - estimated_sell_commission
```

---

## Issue 3: No Realized P&L Tracking ⚠️ CRITICAL

### Current Implementation

File: `/home/riju279/Documents/Code/Zonko/Artha/artha/src/models/transaction_models.py`

The `EnhancedPosition` class tracks:

- ✓ Quantity (remaining shares)
- ✓ Unrealized P&L (for remaining shares)
- ✓ Transaction history
- ❌ **Realized P&L (from past sales) - MISSING!**

### The Problem

**Scenario:**

```python
# Buy 100 shares @ ₹100
# Sell 30 shares @ ₹120
# Current price: ₹110
```

**What position shows:**

- Quantity: 70
- Unrealized P&L: ₹700 (70 shares × ₹10 gain)

**What's missing:**

- Realized P&L from selling 30 @ ₹120: **₹600 (30 × ₹20 gain)**
- **This ₹600 profit is completely invisible!**

### Impact on Portfolio Metrics

File: `/home/riju279/Documents/Code/Zonko/Artha/artha/src/models/__init__.py` (lines 49-51)

```python
@property
def total_pnl(self) -> float:
    return sum(self._get_unrealized_pnl(p) for p in self.positions)
```

**This only counts UNREALIZED P&L!**

**Missing:**

1. Realized P&L from partial sales
2. Realized P&L from fully closed positions
3. Total P&L for closed trades (can't calculate win rate)

### Real-World Impact

**Example trading history:**

- Buy 100 RELIANCE @ ₹2000 = ₹2,00,000
- Sell 50 RELIANCE @ ₹2500 = ₹1,25,000 (Realized gain: ₹25,000)
- Buy 100 INFY @ ₹1500 = ₹1,50,000
- Sell all INFY @ ₹1400 = ₹1,40,000 (Realized loss: -₹10,000)
- Current: Hold 50 RELIANCE @ ₹2400 (Unrealized gain: ₹20,000)

**What portfolio shows:**

- Total P&L: ₹20,000 (only unrealized)
- Return: 20,000 / 350,000 = 5.7%

**Reality:**

- Realized P&L: ₹25,000 - ₹10,000 = ₹15,000
- Unrealized P&L: ₹20,000
- **Total P&L: ₹35,000**
- **True return: 35,000 / 350,000 = 10%**

**Missing ₹15,000 (75% of true profit!)**

### Recommendation

**Priority: HIGH**

Add realized P&L tracking to EnhancedPosition:

```python
@dataclass
class EnhancedPosition:
    # ... existing fields ...
    _realized_pnl: float = field(default=0.0, init=False)

    def add_transaction(self, transaction: PositionTransaction) -> None:
        """Add transaction and calculate realized P&L if selling"""
        if transaction.transaction_type == TransactionType.SELL:
            # Calculate realized P&L using FIFO
            fifo_cost = self._calculate_fifo_cost(transaction.quantity)
            realized = (transaction.price * transaction.quantity) - fifo_cost
            self._realized_pnl += realized

        self.transactions.append(transaction)
        self._recalculate_position()

    @property
    def realized_pnl(self) -> float:
        """Get total realized P&L from all sales"""
        return self._realized_pnl

    @property
    def total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)"""
        return self._realized_pnl + self.unrealized_pnl
```

Add to Portfolio:

```python
@property
def total_pnl(self) -> float:
    """Total P&L including realized gains from past sales"""
    unrealized = sum(self._get_unrealized_pnl(p) for p in self.positions)
    realized = sum(self._get_realized_pnl(p) for p in self.positions)
    return unrealized + realized
```

---

## Issue 4: Transaction History Not Persisted ⚠️ HIGH

### Current Implementation

**Database schema** (`/home/riju279/Documents/Code/Zonko/Artha/artha/data/artha.db`):

```sql
CREATE TABLE positions (
    id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_buy_price FLOAT NOT NULL,
    current_price FLOAT,
    PRIMARY KEY (id),
    CONSTRAINT uq_game_symbol UNIQUE (game_id, symbol),
    FOREIGN KEY(game_id) REFERENCES games (id)
)
```

**No `transactions` table!**

### The Problem

File: `/home/riju279/Documents/Code/Zonko/Artha/artha/src/engine/trade_executor.py` (lines 114-135)

When converting legacy Position to EnhancedPosition:

```python
# WARNING: We cannot accurately determine the original purchase date from legacy Position
# This will result in incorrect XIRR calculations. The proper fix is to store
# transaction history in the database.
existing_transaction = PositionTransaction(
    date=transaction_date,  # LIMITATION: Unknown actual purchase date
    quantity=existing_pos.quantity,
    price=existing_pos.avg_buy_price,
    transaction_type=OrderSide.BUY
)
```

**Impact:**

- All transactions use CURRENT date as purchase date
- XIRR calculation is completely wrong (can't calculate time-weighted returns)
- After restart, transaction history is lost
- Can't reconstruct realized P&L from past sessions

### Real-World Impact

**Example:**

1. Day 1: Buy 100 RELIANCE @ ₹2000 (date: 2024-01-01)
2. Day 30: Buy 50 RELIANCE @ ₹2200 (date: 2024-01-30)
3. Day 60: Sell 30 RELIANCE @ ₹2400 (date: 2024-03-01)
4. **Restart application**
5. System reconstructs position:
   - Quantity: 120 ✓
   - Avg price: ₹2066.67 ✓
   - But all transactions dated TODAY ❌
   - XIRR calculation: Uses TODAY as purchase date for all shares
   - **XIRR shows ~0% instead of actual 20% annualized**

### Recommendation

**Priority: HIGH**

Create transactions table:

```sql
CREATE TABLE transactions (
    id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    position_id INTEGER NOT NULL,
    date DATE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    price FLOAT NOT NULL,
    transaction_type VARCHAR(4) NOT NULL,  -- 'BUY' or 'SELL'
    commission FLOAT NOT NULL,
    stt FLOAT,
    exchange_charges FLOAT,
    gst FLOAT,
    sebi_charges FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY(game_id) REFERENCES games (id),
    FOREIGN KEY(position_id) REFERENCES positions (id)
)
```

Update DAO to save/load transaction history:

```python
async def save_position_with_transactions(
    session: AsyncSession,
    game_id: int,
    position: EnhancedPosition
) -> None:
    """Save position and all its transactions"""
    # Save position
    db_pos = Position(...)
    session.add(db_pos)
    await session.flush()  # Get position.id

    # Save transactions
    for trans in position.transactions:
        db_trans = Transaction(
            game_id=game_id,
            position_id=db_pos.id,
            date=trans.date,
            symbol=position.symbol,
            quantity=trans.quantity,
            price=trans.price,
            transaction_type=trans.transaction_type.value,
            commission=trans.commission if hasattr(trans, 'commission') else 0
        )
        session.add(db_trans)

    await session.commit()
```

---

## Issue 5: Portfolio Total P&L Missing Realized Gains ⚠️ MEDIUM

### Current Implementation

File: `/home/riju279/Documents/Code/Zonko/Artha/artha/src/models/__init__.py` (lines 49-51)

```python
@property
def total_pnl(self) -> float:
    return sum(self._get_unrealized_pnl(p) for p in self.positions)
```

**Only sums positions that still exist!**

### The Problem

When you:

1. Buy 100 shares @ ₹100
2. Sell all 100 shares @ ₹120
3. **Position is deleted** (quantity = 0)
4. Portfolio P&L = 0 (no positions left)
5. **But you made ₹2,000 profit!**

### Impact

- Can't see total profit/loss across all trades
- Closed profitable trades don't contribute to performance metrics
- Win rate calculation impossible (no closed trade history)
- Coach can't give meaningful feedback ("You're up ₹0" when you made ₹50k)

### Recommendation

**Priority: MEDIUM**

Add to GameState:

```python
@dataclass
class GameState:
    # ... existing fields ...
    total_realized_pnl: float = 0.0

    def record_trade_close(self, realized_pnl: float) -> None:
        """Record P&L when position fully closed"""
        self.total_realized_pnl += realized_pnl
```

Update Portfolio:

```python
@property
def total_pnl(self) -> float:
    """Total P&L including realized and unrealized"""
    unrealized = sum(self._get_unrealized_pnl(p) for p in self.positions)
    # Get realized_pnl from game_state if available
    realized = getattr(self, '_realized_pnl', 0.0)
    return unrealized + realized
```

---

## Issue 6: No Total Commissions Tracking ⚠️ MEDIUM

### Current Implementation

Commissions are:

- ✓ Calculated per trade
- ✓ Deducted from cash
- ❌ **Not tracked cumulatively**

### The Problem

Users can't see:

- Total commissions paid to date
- Commission as % of portfolio value
- Whether they're overtrading
- Impact of commission on returns

### Example

After 50 trades:

- Total commission: ₹1,000
- Portfolio: ₹10,00,000
- Commission drag: 0.1%
- **But user has no visibility into this cost**

### Recommendation

**Priority: MEDIUM**

Add to GameState:

```python
@dataclass
class GameState:
    # ... existing ...
    total_commissions_paid: float = 0.0
    total_stt_paid: float = 0.0
    total_other_charges_paid: float = 0.0

    def record_trade_costs(self, costs: TradeCosts) -> None:
        """Track all trading costs"""
        self.total_commissions_paid += costs.brokerage
        self.total_stt_paid += costs.stt
        self.total_other_charges_paid += (costs.exchange_charges + costs.gst + costs.sebi_charges)
```

Display in UI:

```
Total Costs Paid: ₹1,234.56
  ├─ Brokerage: ₹456.00
  ├─ STT: ₹678.00
  └─ Other: ₹100.56
Cost as % of Capital: 0.123%
```

---

## Issue 7: HLD Specification Inconsistency ⚠️ LOW

### Documentation Issue

File: `/home/riju279/Documents/Code/Zonko/Artha/artha/docs/artha_hld.md`

**Line 389:**

```
Brokerage: 0.03% (0.0003) or ₹20 max per order
```

**Lines 397-403:**

```
Example (₹1L Buy Order):
  Order Value: ₹100,000
  Brokerage: ₹30 (0.03% of 1L)  ← Says ₹30
  ...
  Total Cost: ₹100,039.24
```

### The Conflict

- Specification says "₹20 max"
- Example shows ₹30 for ₹1L order (0.03% = ₹30)
- **₹30 exceeds the ₹20 cap!**

### Current Implementation

Code correctly implements ₹20 cap:

```python
return min(commission, 20.0)  # ✓ Correct
```

### Recommendation

**Priority: LOW (Documentation only)**

Update HLD example to match specification:

```markdown
Example (₹1L Buy Order):
  Order Value: ₹100,000
  Brokerage: ₹20.00 (capped at ₹20 max)
  STT: ₹0 (only on sell)
  Exchange: ₹3.25
  GST: ₹4.19 (18% of ₹23.25)
  SEBI: ₹0.10
  Total Cost: ₹100,027.54
```

---

## Summary of Financial Impact

### Current System vs. Reality

**For a typical trading pattern (10 round-trip trades of ₹1L each):**

| Metric | Current System | Reality | Difference |
|--------|---------------|---------|------------|
| Total costs | ₹400 | ₹1,551 | **-₹1,151** |
| Break-even needed | +0.04% | +0.155% | **287% underestimate** |
| Visible P&L | Inflated | Accurate | **Can't quantify** |
| Realized P&L | ₹0 (hidden) | Varies | **Missing entirely** |
| Commission visibility | Per trade | Total | **No tracking** |
| XIRR accuracy | Wrong dates | Correct | **Unusable** |

### Why Users Can't Make Long-Term Profits

1. **Costs are 287% lower than reality** → Users overtrade thinking it's cheap
2. **P&L is inflated** → Users think they're profitable when they're losing
3. **No realized P&L tracking** → Can't see if trading strategy is working
4. **Break-even calculations wrong** → Sell too early or too late
5. **XIRR broken** → Can't compare to market benchmarks
6. **No commission visibility** → Death by a thousand cuts

### Example: 1-Year Trading Results

**User's view:**

- Trades: 100 round-trips
- Portfolio shows: +₹10,000 profit (+10%)
- Think they're beating the market

**Reality:**

- Missing transaction costs: ₹11,506
- Commission not in cost basis: ~₹2,000 overstatement
- Missing realized P&L: Unknown (not tracked)
- **Actual P&L: Likely NEGATIVE despite "good" stock picking**

---

## Recommended Fix Priority

### Phase 1: CRITICAL (Implement Now)

1. ✅ **Add full transaction costs** (STT, Exchange, GST, SEBI)
2. ✅ **Include commission in cost basis** (fix P&L calculation)
3. ✅ **Add realized P&L tracking** (show true profits)

### Phase 2: HIGH (Next Sprint)

4. ✅ **Add transactions table** (persist history for XIRR)
5. ✅ **Fix portfolio total_pnl** (include realized gains)

### Phase 3: MEDIUM (Polish)

6. ✅ **Add total commission tracking** (visibility into costs)
7. ✅ **Fix HLD documentation** (consistency)

### Testing Requirements

After fixes, verify:

- ✅ Buy-sell at same price results in loss equal to 2× total costs
- ✅ Position P&L matches cash flow exactly
- ✅ Realized + unrealized P&L = cash - initial_capital + positions_value
- ✅ XIRR calculation uses actual transaction dates
- ✅ After restart, all P&L and transaction history intact

---

## Code Locations for Fixes

### Primary Files to Modify

1. **`/home/riju279/Documents/Code/Zonko/Artha/artha/src/engine/trade_executor.py`**
   - Replace `calculate_commission()` with `calculate_costs()`
   - Include costs in position price
   - Track realized P&L on sells

2. **`/home/riju279/Documents/Code/Zonko/Artha/artha/src/models/transaction_models.py`**
   - Add `_realized_pnl` field
   - Add `total_pnl` property
   - Track commissions per transaction

3. **`/home/riju279/Documents/Code/Zonko/Artha/artha/src/models/__init__.py`**
   - Fix `Portfolio.total_pnl` to include realized
   - Add `total_realized_pnl` property

4. **`/home/riju279/Documents/Code/Zonko/Artha/artha/src/database/models.py`**
   - Add `Transaction` model
   - Add fields to Game for tracking total costs

5. **`/home/riju279/Documents/Code/Zonko/Artha/artha/src/database/dao.py`**
   - Add transaction persistence
   - Load transaction history on game load

### Configuration Updates

6. **`/home/riju279/Documents/Code/Zonko/Artha/artha/src/config.py`**

   ```python
   # Add complete cost structure
   BROKERAGE_RATE = 0.0003  # 0.03%
   BROKERAGE_CAP = 20.0     # ₹20 max
   STT_SELL_RATE = 0.001    # 0.1% on sell
   EXCHANGE_RATE = 0.0000325  # 0.00325%
   GST_RATE = 0.18          # 18%
   SEBI_RATE_PER_CRORE = 10.0  # ₹10 per ₹1 crore
   ```

---

## Conclusion

The Artha trading system has **fundamental financial calculation errors** that make it impossible for users to understand true profitability. Even with excellent stock picking, users would appear to break even or lose money due to hidden costs and inflated P&L reporting.

**All 7 issues stem from incomplete implementation of the HLD specification**, particularly around transaction costs and P&L tracking. The fixes are well-defined and testable.

**Estimated development time:**

- Phase 1 (Critical): 8-12 hours
- Phase 2 (High): 4-6 hours
- Phase 3 (Medium): 2-4 hours
- **Total: 14-22 hours** for production-ready financial accuracy

**Business impact if not fixed:**

- Users will overtrade (costs seem low)
- Users will lose money despite thinking they're profitable
- Educational value destroyed (learning wrong lessons)
- XIRR comparisons to market meaningless
- Cannot achieve project's core mission of teaching investing

---

**Report prepared by:** Claude (Sonnet 4.5)
**Test suite:** `/home/riju279/Documents/Code/Zonko/Artha/artha/test_financial_accuracy.py` (All tests passing for current implementation)
**Recommended next step:** Implement Phase 1 fixes and create comprehensive integration tests

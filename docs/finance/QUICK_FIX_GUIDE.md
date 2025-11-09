# Quick Fix Guide - Financial Accuracy Issues

## TL;DR - What's Wrong

Your trading system is **287% cheaper than reality** and shows **inflated profits**. Users can't make long-term gains because:

1. Missing 80% of transaction costs (₹115 missing per ₹1L round-trip)
2. Commission not in cost basis (shows +0% when actually -0.06%)
3. No realized P&L (₹15k profit invisible if you close trades)

## Fastest Fix (30 minutes)

### Step 1: Add Real Transaction Costs

**File:** `src/config.py`

Add after line 13:
```python
# Complete transaction cost structure (Indian markets)
BROKERAGE_RATE = 0.0003      # 0.03%
BROKERAGE_CAP = 20.0         # ₹20 max per trade
STT_DELIVERY_SELL = 0.001    # 0.1% on sell side only
EXCHANGE_CHARGES_NSE = 0.0000325  # 0.00325%
GST_RATE = 0.18              # 18% on brokerage + exchange
SEBI_PER_CRORE = 10.0        # ₹10 per crore turnover
```

**File:** `src/engine/trade_executor.py`

Replace lines 51-54 with:
```python
@staticmethod
def calculate_total_costs(amount: float, side: OrderSide) -> float:
    """Calculate complete transaction costs as per Indian markets"""
    # Brokerage
    brokerage = min(amount * BROKERAGE_RATE, BROKERAGE_CAP)

    # STT (only on sell side for delivery)
    stt = amount * STT_DELIVERY_SELL if side == OrderSide.SELL else 0.0

    # Exchange charges
    exchange = amount * EXCHANGE_CHARGES_NSE

    # GST on brokerage + exchange
    gst = (brokerage + exchange) * GST_RATE

    # SEBI charges
    sebi = (amount / 10_000_000) * SEBI_PER_CRORE

    return brokerage + stt + exchange + gst + sebi
```

Update line 76 to:
```python
commission = TradeExecutor.calculate_total_costs(cost, OrderSide.BUY)
```

Update line 209 to:
```python
commission = TradeExecutor.calculate_total_costs(proceeds, OrderSide.SELL)
```

### Step 2: Include Commission in Cost Basis

**File:** `src/engine/trade_executor.py`

Replace lines 99-104 with:
```python
# Calculate price including commission for accurate cost basis
cost_per_share_including_commission = (price * quantity + commission) / quantity

transaction = PositionTransaction(
    date=transaction_date,
    quantity=quantity,
    price=cost_per_share_including_commission,  # ✓ Now includes commission
    transaction_type=OrderSide.BUY
)
```

### Step 3: Track Realized P&L (Basic)

**File:** `src/models/__init__.py`

Add after line 35:
```python
realized_pnl: float = 0.0  # Track realized gains from closed positions
```

Update lines 49-51:
```python
@property
def total_pnl(self) -> float:
    return self.realized_pnl + sum(self._get_unrealized_pnl(p) for p in self.positions)
```

**File:** `src/engine/trade_executor.py`

Add after line 266 (after `portfolio.cash += net_proceeds`):
```python
# Track realized P&L from this sale
realized_pnl = (price - position.avg_buy_price) * quantity
if hasattr(portfolio, 'realized_pnl'):
    portfolio.realized_pnl += realized_pnl
```

## Test Your Fix

Run:
```bash
python test_financial_accuracy.py
```

Expected changes:
- Test 2 (Buy-Sell Cycle): Total loss should be ~₹155 (not ₹6)
- Test 6 (Commission Both Sides): Net P&L should be ~₹-155 (not ₹-6)

## Verify in UI

1. Start game with ₹10,00,000
2. Buy 100 shares @ ₹1000 = ₹1,00,000 order
3. Check cash: Should be ₹8,99,972.46 (not ₹8,99,980)
4. Check position avg price: Should be ₹1000.275 (not ₹1000)
5. Sell 100 shares @ ₹1000 immediately
6. Check cash: Should be ₹9,99,845.00 (not ₹9,99,994)
7. Total loss: ₹155 (realistic) not ₹6 (fake)

## Full Implementation (4-6 hours)

For complete fix including:
- Transaction history persistence
- Detailed cost breakdown display
- Realized P&L per closed trade
- Total commission tracking

See: `FINANCIAL_ACCURACY_ANALYSIS.md`

## Quick Math Reference

### Buy ₹1,00,000 worth of stock:
```
Share cost:      ₹1,00,000.00
Brokerage:       ₹20.00
Exchange:        ₹3.25
GST:             ₹4.19
SEBI:            ₹0.10
─────────────────────────────
TOTAL COST:      ₹1,00,027.54
```

### Sell ₹1,00,000 worth of stock:
```
Share value:     ₹1,00,000.00
Brokerage:       ₹20.00
STT:             ₹100.00  ← Big one!
Exchange:        ₹3.25
GST:             ₹4.19
SEBI:            ₹0.10
─────────────────────────────
NET PROCEEDS:    ₹99,872.46
```

### Round-trip (buy then sell):
```
Total cost:      ₹155.08
Break-even:      +0.155%
```

Current system shows: +0.04% (287% too low!)

---

**Time to fix:** 30 minutes (basic) to 6 hours (complete)
**Impact:** Makes system financially realistic and educational
**Priority:** CRITICAL - Users are learning wrong lessons about trading costs

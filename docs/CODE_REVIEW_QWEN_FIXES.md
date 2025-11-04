# CRITICAL CODE REVIEW - FIXES REQUIRED

**Date:** November 4, 2025
**Reviewer:** Claude Code
**Implementation By:** Qwen CLI
**Status:** ⚠️ IMPLEMENTATION HAS CRITICAL HOLES

---

## 🚨 CRITICAL ISSUES (Must Fix Immediately)

### ISSUE 1: TradeModal Cannot Be Exited with Escape Key ⚠️ **CRITICAL**

**File:** `src/tui/screens/trade_modal.py`

**Problem:** User reported they cannot exit the Buy/Sell screen. The modal is missing the escape key binding.

**Current Code (Lines 8-10):**

```python
class TradeModal(ModalScreen[dict]):
    """Modal for executing trades"""
```

**Missing:** No BINDINGS attribute

**Reference:** Textual documentation requires modals to have escape binding:
<https://textual.textualize.io/guide/screens/#modal-screens>

**FIX REQUIRED:**

```python
class TradeModal(ModalScreen[dict]):
    """Modal for executing trades"""

    BINDINGS = [
        ("escape", "dismiss_modal", "Cancel"),
    ]

    def action_dismiss_modal(self) -> None:
        """Dismiss modal without executing trade"""
        self.dismiss(None)
```

**Test After Fix:**

1. Run app: `python -m src.main`
2. Start new game
3. Press 't' to open trade modal
4. Press Escape
5. Verify modal closes without executing trade

---

### ISSUE 2: DSPy Signatures Missing Critical Context Fields ⚠️ **CRITICAL**

**File:** `src/coach/signatures.py`

**Problem:** TradeFeedbackSignature is missing fields that provide essential context for AI to give good feedback.

**Current Code (Lines 4-14):**

```python
class TradeFeedbackSignature(dspy.Signature):
    """Generate educational feedback for a trade."""
    action: str = dspy.InputField(desc="BUY or SELL")
    symbol: str = dspy.InputField(desc="Stock symbol")
    quantity: int = dspy.InputField(desc="Number of shares")
    price: float = dspy.InputField(desc="Execution price")
    portfolio_value: float = dspy.InputField(desc="Total portfolio value")

    feedback: str = dspy.OutputField(
        desc="2-3 concise educational bullets about this trade (max 60 chars each)"
    )
```

**Missing Fields:**

- `cash_remaining` - How much cash left after trade
- `num_positions` - Number of different stocks owned

**Reference:** See `docs/artha_atoms/stage5_coach/STAGE5_DSPY_PATTERNS.md` lines 72-92

**FIX REQUIRED:**

```python
class TradeFeedbackSignature(dspy.Signature):
    """Generate educational feedback for a trade.

    Focus on:
    - Whether the trade aligns with diversification principles
    - Risk management considerations
    - Learning opportunity from this specific trade

    Keep feedback to 2-3 bullets, max 60 characters each.
    Use simple language suitable for beginners.
    """

    # Trade details (inputs)
    action: str = dspy.InputField(
        desc="Trade action: BUY or SELL"
    )

    symbol: str = dspy.InputField(
        desc="Stock symbol (e.g., RELIANCE, TCS)"
    )

    quantity: int = dspy.InputField(
        desc="Number of shares traded"
    )

    price: float = dspy.InputField(
        desc="Execution price per share in rupees"
    )

    # Portfolio context (inputs) - THESE ARE MISSING!
    portfolio_value: float = dspy.InputField(
        desc="Total portfolio value in rupees"
    )

    cash_remaining: float = dspy.InputField(
        desc="Cash remaining after trade in rupees"
    )

    num_positions: int = dspy.InputField(
        desc="Total number of different stocks owned"
    )

    # Output
    feedback: str = dspy.OutputField(
        desc="2-3 concise educational bullet points, each max 60 chars. Focus on portfolio implications, risk, and learning."
    )
```

**ALSO UPDATE:** `src/coach/manager.py` line 25-32

**Current:**

```python
def get_trade_feedback(
    self,
    action: str,
    symbol: str,
    quantity: int,
    price: float,
    portfolio_value: float
) -> str:
```

**Change To:**

```python
def get_trade_feedback(
    self,
    action: str,
    symbol: str,
    quantity: int,
    price: float,
    portfolio_value: float,
    cash_remaining: float,
    num_positions: int
) -> str:
```

**ALSO UPDATE:** Call site in `src/tui/screens/main_screen.py` line 113-119

**Current:**

```python
feedback = self.app.coach.get_trade_feedback(
    action=action,
    symbol=symbol,
    quantity=quantity,
    price=price,
    portfolio_value=self.game_state.portfolio.total_value
)
```

**Change To:**

```python
feedback = self.app.coach.get_trade_feedback(
    action=action,
    symbol=symbol,
    quantity=quantity,
    price=price,
    portfolio_value=self.game_state.portfolio.total_value,
    cash_remaining=self.game_state.portfolio.cash,
    num_positions=len(self.game_state.portfolio.positions)
)
```

**ALSO UPDATE:** DSPy module call in `src/coach/manager.py` line 38-44

**Current:**

```python
result = self.trade_feedback(
    action=action,
    symbol=symbol,
    quantity=quantity,
    price=price,
    portfolio_value=portfolio_value
)
```

**Change To:**

```python
result = self.trade_feedback(
    action=action,
    symbol=symbol,
    quantity=quantity,
    price=price,
    portfolio_value=portfolio_value,
    cash_remaining=cash_remaining,
    num_positions=num_positions
)
```

**Test After Fix:**

1. Start Ollama: `ollama serve`
2. Pull model: `ollama pull qwen3:8b`
3. Run app and execute trade
4. Verify feedback includes context about diversification and position count

---

## 🟡 HIGH PRIORITY ISSUES (Should Fix)

### ISSUE 3: Market Data Loader Missing Fallback Mock Data

**File:** `src/data/loader.py`

**Problem:** When network fails or yfinance has issues, the function returns None. The spec requires fallback to mock data.

**Current Code (Lines 58-63):**

```python
if not df.empty:
    # Save to cache
    df.to_csv(cache_file)
    self._cache[symbol_with_suffix] = df
    return df
else:
    return None  # ❌ WRONG - Should return mock data
```

**Reference:** `docs/artha_atoms/stage3_data/STAGE3_DATA_PATTERNS.md` lines 138-186

**FIX REQUIRED:**

Add this method to MarketDataLoader class:

```python
def _generate_mock_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
    """Generate fallback mock data when download fails

    Args:
        symbol: Stock symbol
        days: Number of days of data

    Returns:
        Mock DataFrame with realistic price movements
    """
    import numpy as np

    print(f"⚠️  Using mock data for {symbol} (download failed)")

    # Base prices for common stocks
    base_prices = {
        "RELIANCE": 2500.0,
        "TCS": 3500.0,
        "INFY": 1500.0,
        "HDFCBANK": 1600.0,
        "ICICIBANK": 950.0,
        "HINDUNILVR": 2400.0,
        "ITC": 450.0,
        "SBIN": 600.0,
        "BHARTIARTL": 900.0,
        "BAJFINANCE": 7000.0,
    }

    base_price = base_prices.get(symbol, 1000.0)

    # Generate dates
    dates = pd.date_range(
        end=datetime.now(),
        periods=days,
        freq='D'
    )

    # Random walk with slight upward bias
    np.random.seed(hash(symbol) % (2**32))  # Consistent for same symbol
    returns = np.random.normal(0.001, 0.02, days)  # 0.1% daily return, 2% volatility
    prices = base_price * (1 + returns).cumprod()

    # Create DataFrame
    df = pd.DataFrame({
        'Open': prices * 0.995,
        'High': prices * 1.01,
        'Low': prices * 0.99,
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, days)
    }, index=dates)

    return df
```

**Update get_stock_data method (Lines 45-63):**

```python
# Download from yfinance
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    ticker = yf.Ticker(symbol_with_suffix)
    df = ticker.history(start=start_date, end=end_date)

    if not df.empty:
        # Save to cache
        df.to_csv(cache_file)
        self._cache[symbol_with_suffix] = df
        return df
    else:
        # ✅ FIX: Return mock data instead of None
        return self._generate_mock_data(symbol, days)

except Exception as e:
    print(f"Error downloading {symbol}: {e}")
    # ✅ FIX: Return mock data instead of None
    return self._generate_mock_data(symbol, days)
```

**Test After Fix:**

1. Disconnect internet
2. Run app
3. Try to trade
4. Verify mock prices are used and app doesn't crash

---

### ISSUE 4: PortfolioReviewSignature Missing Field Names

**File:** `src/coach/signatures.py`

**Problem:** The signature field names don't match the spec. This causes inconsistency.

**Current Code (Lines 16-25):**

```python
class PortfolioReviewSignature(dspy.Signature):
    """Analyze portfolio and provide insights."""
    num_positions: int = dspy.InputField(desc="Number of positions")
    total_value: float = dspy.InputField(desc="Total portfolio value")
    cash_pct: float = dspy.InputField(desc="Percentage in cash")
    total_pnl_pct: float = dspy.InputField(desc="Total P&L percentage")

    insights: str = dspy.OutputField(
        desc="2-3 brief insights about portfolio diversification and risk"
    )
```

**Reference:** `docs/artha_atoms/stage5_coach/STAGE5_DSPY_PATTERNS.md` lines 104-128

**FIX REQUIRED:**

```python
class PortfolioReviewSignature(dspy.Signature):
    """Analyze an investment portfolio and provide strategic insights.

    Evaluate:
    - Diversification level (number of positions)
    - Cash allocation (% in cash vs invested)
    - Overall performance (P&L percentage)
    - Risk profile

    Provide 2-3 actionable insights for improvement.
    Use beginner-friendly language.
    """

    # Portfolio metrics (inputs)
    num_positions: int = dspy.InputField(
        desc="Number of different stocks currently owned"
    )

    total_value: float = dspy.InputField(
        desc="Total portfolio value in rupees (cash + holdings)"
    )

    cash_percentage: float = dspy.InputField(
        desc="Percentage of portfolio in cash (0-100)"
    )

    total_pnl_percentage: float = dspy.InputField(
        desc="Total profit/loss percentage since start"
    )

    # Output
    insights: str = dspy.OutputField(
        desc="2-3 strategic insights about portfolio health, diversification, and next steps. Each insight should be actionable and educational."
    )
```

**ALSO UPDATE:** Manager call in `src/coach/manager.py` line 62-66

**Current:**

```python
result = self.portfolio_review(
    num_positions=num_positions,
    total_value=total_value,
    cash_pct=cash_pct,
    total_pnl_pct=total_pnl_pct
)
```

**Change To:**

```python
result = self.portfolio_review(
    num_positions=num_positions,
    total_value=total_value,
    cash_percentage=cash_pct,
    total_pnl_percentage=total_pnl_pct
)
```

---

### ISSUE 5: QuestionAnswerSignature Missing Context Field

**File:** `src/coach/signatures.py`

**Problem:** The Q&A signature is missing the user_portfolio_size field which provides important context.

**Current Code (Lines 27-33):**

```python
class QuestionAnswerSignature(dspy.Signature):
    """Answer investing questions."""
    question: str = dspy.InputField(desc="Student's question about investing")

    answer: str = dspy.OutputField(
        desc="Clear, educational answer suitable for teenagers"
    )
```

**Reference:** `docs/artha_atoms/stage5_coach/STAGE5_DSPY_PATTERNS.md` lines 130-159

**FIX REQUIRED:**

```python
class InvestingQuestionSignature(dspy.Signature):
    """Answer investment-related questions for teenage beginners.

    Provide:
    - Clear, simple explanations
    - Real-world examples
    - Practical takeaways

    Avoid jargon. If technical terms are necessary, explain them.
    Keep answer to 3-4 sentences maximum.
    """

    # Input
    question: str = dspy.InputField(
        desc="Student's question about investing, stocks, or portfolio management"
    )

    # Context (optional but helpful)
    user_portfolio_size: int = dspy.InputField(
        desc="Number of stocks user currently owns (for context)"
    )

    # Output
    answer: str = dspy.OutputField(
        desc="Clear, educational answer suitable for teenagers. 3-4 sentences max. Include practical example if helpful."
    )
```

**ALSO UPDATE:** Manager method signature (line 73)

**Current:**

```python
def answer_question(self, question: str) -> str:
```

**Change To:**

```python
def answer_question(self, question: str, user_portfolio_size: int = 0) -> str:
```

**ALSO UPDATE:** Call inside method (line 79)

**Current:**

```python
result = self.qa_module(question=question)
```

**Change To:**

```python
result = self.qa_module(
    question=question,
    user_portfolio_size=user_portfolio_size
)
```

---

## 🟢 MEDIUM PRIORITY ISSUES (Good to Fix)

### ISSUE 6: Help Screen Should Use ModalScreen

**File:** `src/tui/screens/help_screen.py`

**Problem:** Help screen uses regular Screen instead of ModalScreen. Modal is better for overlays.

**Current Code (Line 7):**

```python
class HelpScreen(Screen):
```

**FIX REQUIRED:**

```python
class HelpScreen(ModalScreen):
```

**Import Update (Line 3):**

```python
from textual.screen import ModalScreen
```

**Test After Fix:**

1. Press 'h' for help
2. Verify background is dimmed (modal effect)
3. Press Escape to close
4. Verify you're back at game screen

---

### ISSUE 7: Trade Executor Missing Edge Case - Exact Cash Match

**File:** `src/engine/trade_executor.py`

**Problem:** The current implementation handles this correctly with `<` but doesn't have explicit test for exact match edge case.

**Current Code (Line 73):**

```python
if portfolio.cash < total_cost:
```

**This is CORRECT** (< allows exact match), but add comment for clarity:

```python
# Check if enough cash (allows exact match where cash == total_cost)
if portfolio.cash < total_cost:
```

**ADD TEST:** in `tests/test_trade_executor.py`

```python
def test_buy_exact_cash_match():
    """Test buying when cost exactly matches available cash"""
    # Cost = 10 shares * 1000 = 10,000
    # Commission = 10,000 * 0.0003 = 3
    # Total = 10,003
    portfolio = Portfolio(cash=10003.0)

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 10, 1000.0
    )

    assert result.success
    assert abs(portfolio.cash) < 0.01  # Should be approximately 0
```

---

### ISSUE 8: Missing Input Validation in Trade Modal

**File:** `src/tui/screens/trade_modal.py`

**Problem:** The on_input_changed handler (line 92-99) catches all exceptions with bare `except:`. Should be specific.

**Current Code:**

```python
def on_input_changed(self, event: Input.Changed) -> None:
    """Update estimate when quantity changes"""
    try:
        quantity = int(event.value)
        estimate = self.query_one("#estimate", Static)
        estimate.update(f"Estimated cost: ~₹{quantity * 2000:,.2f} (example)")
    except:  # ❌ Too broad
        pass
```

**FIX REQUIRED:**

```python
def on_input_changed(self, event: Input.Changed) -> None:
    """Update estimate when quantity changes"""
    if event.input.id != "quantity-input":
        return

    try:
        if not event.value or event.value.strip() == "":
            return

        quantity = int(event.value)
        if quantity <= 0:
            return

        estimate = self.query_one("#estimate", Static)
        # Get approximate price (this is just an estimate before actual trade)
        estimate.update(f"Estimated cost: ~₹{quantity * 2000:,.2f} (example)")
    except ValueError:
        # Not a valid integer yet, ignore
        pass
    except Exception as e:
        # Log unexpected errors
        print(f"Error updating estimate: {e}")
```

---

### ISSUE 9: Position Averaging Logic Needs Test

**File:** `src/engine/trade_executor.py`

**Problem:** The averaging logic (lines 90-94) is correct but needs test coverage.

**Current Code:**

```python
if existing_pos:
    # Update average buy price
    total_qty = existing_pos.quantity + quantity
    total_cost_basis = (existing_pos.avg_buy_price * existing_pos.quantity) + cost
    existing_pos.avg_buy_price = total_cost_basis / total_qty
```

**ADD TESTS:** in `tests/test_trade_executor.py`

```python
def test_position_averaging_up():
    """Test averaging up (buying at higher price)"""
    portfolio = Portfolio(
        cash=50000.0,
        positions=[Position("TEST", 100, 100.0, 110.0)]
    )

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 50, 120.0
    )

    assert result.success
    position = portfolio.positions[0]
    assert position.quantity == 150

    # Expected average: (100*100 + 50*120) / 150 = 106.67
    expected_avg = (100 * 100 + 50 * 120) / 150
    assert abs(position.avg_buy_price - expected_avg) < 0.01


def test_position_averaging_down():
    """Test averaging down (buying at lower price)"""
    portfolio = Portfolio(
        cash=50000.0,
        positions=[Position("TEST", 100, 120.0, 110.0)]
    )

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 100, 100.0
    )

    assert result.success
    position = portfolio.positions[0]
    assert position.quantity == 200

    # Expected average: (100*120 + 100*100) / 200 = 110
    expected_avg = (100 * 120 + 100 * 100) / 200
    assert abs(position.avg_buy_price - expected_avg) < 0.01
```

---

## 📋 VERIFICATION CHECKLIST

After making all fixes, verify:

### Critical Fixes

- [ ] Can exit trade modal with Escape key
- [ ] Trade feedback includes cash_remaining and num_positions
- [ ] Market data falls back to mock when download fails
- [ ] All DSPy signatures have complete field sets

### High Priority Fixes

- [ ] Portfolio review uses correct field names (cash_percentage not cash_pct)
- [ ] Q&A signature includes user_portfolio_size
- [ ] Help screen is ModalScreen with dimmed background

### Medium Priority Fixes

- [ ] Trade executor has edge case tests
- [ ] Input validation is specific, not bare except
- [ ] Position averaging has test coverage

### Regression Testing

- [ ] All existing tests still pass: `pytest tests/ -v`
- [ ] App launches without errors: `python -m src.main`
- [ ] Can complete full game flow:
  - Start new game
  - Execute buy trade
  - Execute sell trade
  - Advance day
  - Get coach insights
  - Save game
  - Quit and restart
  - Continue game
  - Press 'h' for help
  - All features work

---

## 🔧 FIX IMPLEMENTATION ORDER

1. **FIRST:** Fix TradeModal escape binding (CRITICAL - user can't exit!)
2. **SECOND:** Fix DSPy signatures (CRITICAL - coach not working properly)
3. **THIRD:** Fix market data fallback (HIGH - app crashes without network)
4. **FOURTH:** Fix field naming consistency (HIGH - causes confusion)
5. **FIFTH:** Add remaining tests and polish (MEDIUM - quality improvements)

---

## 📝 TESTING PROTOCOL

After each fix:

```bash
# Run specific test file if applicable
pytest tests/test_trade_executor.py -v

# Run all tests
pytest tests/ -v

# Manual test the fix
python -m src.main
# Test the specific functionality you fixed
```

After ALL fixes:

```bash
# Full test suite
pytest tests/ -v

# Full manual validation
python -m src.main
# Go through complete game flow
# Test all edge cases mentioned above
```

---

## 🎯 EXPECTED OUTCOME

After all fixes:

- ✅ User can exit all modals with Escape
- ✅ AI coach provides context-aware feedback
- ✅ App works offline with mock data
- ✅ All DSPy signatures are complete and consistent
- ✅ All tests pass
- ✅ No crashes in normal usage
- ✅ Code matches specifications exactly

---

**QWEN: Start with ISSUE 1 (TradeModal escape) and work through each issue in order. Test after EACH fix. Report completion of each issue before moving to the next.**

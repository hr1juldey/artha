# Stage 6: Test Cases & Quality Assurance

**Supplement to**: STAGE6_OVERVIEW.md
**Purpose**: Comprehensive test cases, validation scenarios, and quality checklists

---

## Testing Strategy

```
┌────────────────────────────────────────────────────┐
│              Testing Pyramid                        │
├────────────────────────────────────────────────────┤
│                                                     │
│                    ▲                               │
│                   ╱ ╲                              │
│                  ╱   ╲    Manual Testing          │
│                 ╱     ╲   (User scenarios)        │
│                ╱───────╲                          │
│               ╱         ╲                         │
│              ╱           ╲  Integration Tests     │
│             ╱             ╲ (Component interaction)│
│            ╱───────────────╲                      │
│           ╱                 ╲                     │
│          ╱                   ╲  Unit Tests        │
│         ╱                     ╲ (Individual funcs) │
│        ╱───────────────────────╲                  │
│                                                     │
└────────────────────────────────────────────────────┘
```

---

## Unit Tests

### Test: Trade Executor

#### File: `tests/test_trade_executor.py`

```python
"""Unit tests for trade execution engine"""
import pytest
from src.engine.trade_executor import TradeExecutor, TradeResult
from src.models import Portfolio, Position

class TestBuyOrders:
    """Test buy order execution"""

    def test_buy_success_new_position(self):
        """Test successful buy creating new position"""
        portfolio = Portfolio(cash=100000.0)

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", 10, 1000.0
        )

        assert result.success
        assert len(portfolio.positions) == 1
        assert portfolio.positions[0].symbol == "TEST"
        assert portfolio.positions[0].quantity == 10
        assert portfolio.positions[0].avg_buy_price == 1000.0
        # Cash should be reduced by cost + commission
        # Cost = 10 * 1000 = 10,000
        # Commission = 10,000 * 0.0003 = 3
        # Total = 10,003
        assert abs(portfolio.cash - 89997.0) < 0.01

    def test_buy_success_add_to_existing(self):
        """Test successful buy adding to existing position"""
        portfolio = Portfolio(
            cash=100000.0,
            positions=[Position("TEST", 10, 1000.0, 1000.0)]
        )

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", 5, 1200.0
        )

        assert result.success
        assert len(portfolio.positions) == 1
        assert portfolio.positions[0].quantity == 15

        # New average: (10*1000 + 5*1200) / 15 = 16000/15 = 1066.67
        expected_avg = (10 * 1000.0 + 5 * 1200.0) / 15
        assert abs(portfolio.positions[0].avg_buy_price - expected_avg) < 0.01

    def test_buy_insufficient_funds(self):
        """Test buy fails with insufficient funds"""
        portfolio = Portfolio(cash=5000.0)

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", 100, 1000.0  # Need 100,000 + commission
        )

        assert not result.success
        assert "Insufficient funds" in result.message
        assert len(portfolio.positions) == 0
        assert portfolio.cash == 5000.0  # Unchanged

    def test_buy_exact_cash_match(self):
        """Test buy when cost exactly matches cash"""
        # Setup: cash = cost + commission
        # Cost = 10 * 1000 = 10,000
        # Commission = 3
        portfolio = Portfolio(cash=10003.0)

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", 10, 1000.0
        )

        assert result.success
        assert abs(portfolio.cash) < 0.01  # Should be ~0

    def test_buy_invalid_quantity_zero(self):
        """Test buy fails with zero quantity"""
        portfolio = Portfolio(cash=100000.0)

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", 0, 1000.0
        )

        assert not result.success
        assert "at least 1" in result.message.lower()

    def test_buy_invalid_quantity_negative(self):
        """Test buy fails with negative quantity"""
        portfolio = Portfolio(cash=100000.0)

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", -10, 1000.0
        )

        assert not result.success

    def test_buy_invalid_price_zero(self):
        """Test buy fails with zero price"""
        portfolio = Portfolio(cash=100000.0)

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", 10, 0.0
        )

        assert not result.success

    def test_buy_large_quantity(self):
        """Test buy with large quantity"""
        portfolio = Portfolio(cash=100000000.0)  # 10 crore

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", 9999, 1000.0
        )

        assert result.success
        assert portfolio.positions[0].quantity == 9999

    def test_buy_exceeds_max_quantity(self):
        """Test buy fails exceeding max quantity"""
        portfolio = Portfolio(cash=100000000.0)

        result = TradeExecutor.execute_buy(
            portfolio, "TEST", 10001, 1000.0  # Max is 10,000
        )

        assert not result.success


class TestSellOrders:
    """Test sell order execution"""

    def test_sell_success_partial(self):
        """Test successful partial sell"""
        portfolio = Portfolio(
            cash=50000.0,
            positions=[Position("TEST", 100, 1000.0, 1100.0)]
        )

        result = TradeExecutor.execute_sell(
            portfolio, "TEST", 50, 1100.0
        )

        assert result.success
        assert len(portfolio.positions) == 1
        assert portfolio.positions[0].quantity == 50
        assert portfolio.positions[0].avg_buy_price == 1000.0  # Unchanged

        # Cash increase: 50 * 1100 - commission
        # Revenue = 55,000
        # Commission = 55,000 * 0.0003 = 16.5
        # Net = 54,983.5
        expected_cash = 50000.0 + 55000.0 - 16.5
        assert abs(portfolio.cash - expected_cash) < 0.01

    def test_sell_success_entire_position(self):
        """Test successful sell of entire position"""
        portfolio = Portfolio(
            cash=50000.0,
            positions=[Position("TEST", 100, 1000.0, 1100.0)]
        )

        result = TradeExecutor.execute_sell(
            portfolio, "TEST", 100, 1100.0
        )

        assert result.success
        assert len(portfolio.positions) == 0  # Position removed

    def test_sell_insufficient_quantity(self):
        """Test sell fails with insufficient quantity"""
        portfolio = Portfolio(
            cash=50000.0,
            positions=[Position("TEST", 50, 1000.0, 1100.0)]
        )

        result = TradeExecutor.execute_sell(
            portfolio, "TEST", 100, 1100.0
        )

        assert not result.success
        assert "only own 50" in result.message.lower()
        assert portfolio.positions[0].quantity == 50  # Unchanged

    def test_sell_position_not_owned(self):
        """Test sell fails for unowned stock"""
        portfolio = Portfolio(
            cash=50000.0,
            positions=[Position("OTHER", 100, 1000.0, 1100.0)]
        )

        result = TradeExecutor.execute_sell(
            portfolio, "TEST", 10, 1100.0
        )

        assert not result.success
        assert "don't own" in result.message.lower()

    def test_sell_at_profit(self):
        """Test sell at profit (price > avg_buy_price)"""
        portfolio = Portfolio(
            cash=50000.0,
            positions=[Position("TEST", 100, 1000.0, 1200.0)]
        )

        initial_cash = portfolio.cash

        result = TradeExecutor.execute_sell(
            portfolio, "TEST", 100, 1200.0
        )

        assert result.success
        # Profit = (1200 - 1000) * 100 = 20,000
        # But check actual cash increase
        cash_increase = portfolio.cash - initial_cash
        assert cash_increase > 100000  # Selling 100 shares


    def test_sell_at_loss(self):
        """Test sell at loss (price < avg_buy_price)"""
        portfolio = Portfolio(
            cash=50000.0,
            positions=[Position("TEST", 100, 1000.0, 800.0)]
        )

        result = TradeExecutor.execute_sell(
            portfolio, "TEST", 100, 800.0
        )

        assert result.success
        # Loss scenario but sell still executes


class TestCommissionCalculation:
    """Test commission calculation"""

    def test_commission_small_trade(self):
        """Test commission on small trade (percentage applies)"""
        from src.engine.trade_executor import CommissionCalculator

        # 10,000 trade
        commission = CommissionCalculator.calculate(10000.0)
        expected = 10000.0 * 0.0003  # 3.0
        assert abs(commission - expected) < 0.01

    def test_commission_large_trade(self):
        """Test commission capped at ₹20"""
        from src.engine.trade_executor import CommissionCalculator

        # 1,000,000 trade
        commission = CommissionCalculator.calculate(1000000.0)
        assert commission == 20.0  # Capped

    def test_commission_medium_trade(self):
        """Test commission on medium trade"""
        from src.engine.trade_executor import CommissionCalculator

        # 50,000 trade
        commission = CommissionCalculator.calculate(50000.0)
        expected = 50000.0 * 0.0003  # 15.0
        assert abs(commission - expected) < 0.01

    def test_commission_exactly_at_cap(self):
        """Test trade size that exactly hits cap"""
        from src.engine.trade_executor import CommissionCalculator

        # 20 / 0.0003 = 66,666.67
        # Any trade >= this should be capped at 20
        commission = CommissionCalculator.calculate(66667.0)
        assert commission == 20.0


class TestTradeValidation:
    """Test trade input validation"""

    def test_validate_symbol_valid(self):
        """Test valid symbol passes"""
        from src.engine.trade_executor import TradeValidator

        result = TradeValidator.validate_symbol("RELIANCE")
        assert result.is_valid

    def test_validate_symbol_empty(self):
        """Test empty symbol fails"""
        from src.engine.trade_executor import TradeValidator

        result = TradeValidator.validate_symbol("")
        assert not result.is_valid

    def test_validate_action_valid(self):
        """Test valid actions pass"""
        from src.engine.trade_executor import TradeValidator

        assert TradeValidator.validate_action("BUY").is_valid
        assert TradeValidator.validate_action("SELL").is_valid

    def test_validate_action_invalid(self):
        """Test invalid action fails"""
        from src.engine.trade_executor import TradeValidator

        result = TradeValidator.validate_action("HOLD")
        assert not result.is_valid


class TestTradeEstimation:
    """Test trade estimation"""

    def test_estimate_buy(self):
        """Test buy estimation"""
        estimate = TradeExecutor.estimate_trade(
            "BUY", 10, 1000.0, current_cash=50000.0
        )

        assert estimate['action'] == 'BUY'
        assert estimate['trade_value'] == 10000.0
        assert estimate['commission'] > 0
        assert estimate['total_cost'] > 10000.0
        assert estimate['can_execute'] == True

    def test_estimate_sell(self):
        """Test sell estimation"""
        estimate = TradeExecutor.estimate_trade(
            "SELL", 10, 1000.0, current_cash=50000.0, current_holdings=20
        )

        assert estimate['action'] == 'SELL'
        assert estimate['trade_value'] == 10000.0
        assert estimate['commission'] > 0
        assert estimate['net_proceeds'] < 10000.0
        assert estimate['can_execute'] == True
```

---

## Integration Tests

### Test: Trading Flow with Database

#### File: `tests/test_trading_integration.py`

```python
"""Integration tests for trading with database"""
import pytest
import asyncio
from pathlib import Path
from datetime import datetime

from src.database.connection import DatabaseConnection
from src.database.dao import GameDAO
from src.engine.trade_executor import TradeExecutor
from src.models import Portfolio, Position

@pytest.fixture
async def test_db():
    """Create test database"""
    db_path = Path("test_artha_integration.db")
    db = DatabaseConnection(db_path)
    await db.create_tables()

    yield db

    await db.close()
    db_path.unlink(missing_ok=True)

@pytest.mark.asyncio
async def test_complete_trading_flow(test_db):
    """Test complete flow: create game, trade, save, load"""

    async with test_db.get_session() as session:
        dao = GameDAO(session)

        # Create user and game
        user = await dao.create_user("testuser")
        game = await dao.create_game(
            user_id=user.id,
            initial_capital=1000000.0,
            start_date=datetime.now()
        )
        await session.commit()

        # Create portfolio
        portfolio = Portfolio(cash=game.current_cash)

        # Execute buy trade
        buy_result = TradeExecutor.execute_buy(
            portfolio, "RELIANCE", 10, 2500.0
        )

        assert buy_result.success

        # Save position to database
        position = portfolio.get_position("RELIANCE")
        await dao.create_position(
            game_id=game.id,
            symbol="RELIANCE",
            quantity=position.quantity,
            avg_buy_price=position.avg_buy_price
        )

        # Update game cash
        await dao.update_game_state(game.id, current_cash=portfolio.cash)
        await session.commit()

        # Load game back
        loaded_game = await dao.get_game_by_id(game.id)

        assert loaded_game is not None
        assert len(loaded_game.positions) == 1
        assert loaded_game.positions[0].symbol == "RELIANCE"
        assert loaded_game.positions[0].quantity == 10

        # Execute sell trade
        sell_result = TradeExecutor.execute_sell(
            portfolio, "RELIANCE", 5, 2600.0
        )

        assert sell_result.success

        # Update database
        db_pos = loaded_game.positions[0]
        await dao.update_position(
            position_id=db_pos.id,
            quantity=portfolio.get_position("RELIANCE").quantity,
            avg_buy_price=portfolio.get_position("RELIANCE").avg_buy_price
        )
        await dao.update_game_state(game.id, current_cash=portfolio.cash)
        await session.commit()

        # Verify final state
        final_game = await dao.get_game_by_id(game.id)
        assert final_game.positions[0].quantity == 5


@pytest.mark.asyncio
async def test_multiple_positions(test_db):
    """Test managing multiple positions"""

    async with test_db.get_session() as session:
        dao = GameDAO(session)

        # Setup
        user = await dao.create_user("trader")
        game = await dao.create_game(user.id, 1000000.0, datetime.now())
        await session.commit()

        portfolio = Portfolio(cash=game.current_cash)

        # Buy multiple stocks
        symbols = ["RELIANCE", "TCS", "INFY"]
        for symbol in symbols:
            result = TradeExecutor.execute_buy(
                portfolio, symbol, 10, 2000.0
            )
            assert result.success

            # Save to database
            pos = portfolio.get_position(symbol)
            await dao.create_position(
                game.id, symbol, pos.quantity, pos.avg_buy_price
            )

        await dao.update_game_state(game.id, current_cash=portfolio.cash)
        await session.commit()

        # Load and verify
        loaded_game = await dao.get_game_by_id(game.id)
        assert len(loaded_game.positions) == 3
```

---

## Manual Test Scenarios

### Scenario 1: New Game Flow

**Objective**: Verify user can start and play a new game

**Steps**:
1. Launch app: `python -m src.main`
2. Click "New Game" button
3. Verify main screen appears
4. Verify portfolio shows empty or starting positions
5. Verify cash shows ₹10,00,000
6. Verify day shows "Day 1"
7. Verify status bar is visible

**Expected Results**:
- [ ] App launches without errors
- [ ] New game starts successfully
- [ ] UI renders correctly
- [ ] All data displays properly

---

### Scenario 2: Execute Buy Trade

**Objective**: Verify user can buy stocks

**Steps**:
1. Start game
2. Press 't' to open trade modal
3. Select "RELIANCE" from dropdown
4. Select "BUY" action
5. Enter quantity: 10
6. Click "Execute"
7. Verify trade executes
8. Check portfolio grid shows new position
9. Check cash decreased
10. Check AI coach feedback appears

**Expected Results**:
- [ ] Trade modal opens
- [ ] All controls work
- [ ] Trade executes successfully
- [ ] Portfolio updates
- [ ] Cash decreases by correct amount
- [ ] Feedback is helpful

**Test Cases**:
- Buy with sufficient funds ✓
- Buy with insufficient funds (should fail)
- Buy with invalid quantity (should reject)
- Buy same stock twice (should average)

---

### Scenario 3: Execute Sell Trade

**Objective**: Verify user can sell stocks

**Prerequisite**: Own some shares

**Steps**:
1. Ensure portfolio has RELIANCE position (buy if needed)
2. Press 't' to open trade modal
3. Select "RELIANCE"
4. Select "SELL"
5. Enter quantity: 5
6. Click "Execute"
7. Verify sell executes
8. Check portfolio quantity decreased
9. Check cash increased

**Expected Results**:
- [ ] Can sell owned shares
- [ ] Portfolio quantity updates
- [ ] Cash increases correctly
- [ ] Position removed if selling all

**Test Cases**:
- Sell partial position ✓
- Sell entire position ✓
- Try to sell more than owned (should fail)
- Try to sell unowned stock (should fail)

---

### Scenario 4: Day Advance

**Objective**: Verify day advance updates prices

**Steps**:
1. Start game with some positions
2. Note current prices
3. Press Space to advance day
4. Verify day number incremented
5. Verify prices changed
6. Verify P&L updated

**Expected Results**:
- [ ] Day increments
- [ ] Prices update
- [ ] P&L recalculated
- [ ] No errors

---

### Scenario 5: Save and Load Game

**Objective**: Verify game persistence

**Steps**:
1. Start new game
2. Execute some trades
3. Press 's' to save
4. Note current state (day, cash, positions)
5. Press 'q' to quit
6. Restart app
7. Click "Continue Game"
8. Verify state matches

**Expected Results**:
- [ ] Save succeeds
- [ ] Can restart app
- [ ] Continue button enabled
- [ ] All state restored correctly

---

### Scenario 6: AI Coach Feedback

**Objective**: Verify AI coach works

**Prerequisite**: Ollama running with qwen3:8b

**Steps**:
1. Start game
2. Execute trade
3. Observe feedback notification
4. Press 'c' for portfolio insights
5. Verify feedback is relevant

**Expected Results**:
- [ ] Feedback appears after trade
- [ ] Feedback is educational
- [ ] Feedback is concise
- [ ] No crashes if Ollama offline

**Test Cases**:
- With Ollama online (get AI feedback)
- With Ollama offline (get fallback messages)

---

### Scenario 7: Error Handling

**Objective**: Verify app handles errors gracefully

**Test Cases**:

#### 7a: Invalid Trade Inputs
- Enter negative quantity → Rejected with message
- Enter zero quantity → Rejected
- Enter very large quantity (>10,000) → Rejected
- Leave quantity empty → Validation error

#### 7b: Network Issues
- Stop internet connection
- Try to download stock data
- Should fall back to cached or mock data
- No crash

#### 7c: Database Issues
- Delete database file while running
- Try to save game
- Should show error message
- App remains stable

---

## Performance Tests

### Test: App Startup Time

**Objective**: App starts in reasonable time

**Method**:
```bash
time python -m src.main
```

**Expected**: < 5 seconds

---

### Test: Trade Execution Speed

**Objective**: Trades execute quickly

**Method**: Execute trade, measure time to update

**Expected**: < 1 second

---

### Test: Day Advance Speed

**Objective**: Day advance doesn't lag

**Method**: Advance multiple days, measure per-day time

**Expected**: < 2 seconds per day

---

## Accessibility Tests

### Test: Keyboard Navigation

**Objective**: All functions accessible via keyboard

**Test**:
- [ ] 't' opens trade modal
- [ ] Space advances day
- [ ] 'c' shows coach insights
- [ ] 's' saves game
- [ ] 'm' returns to menu
- [ ] 'h' shows help
- [ ] 'q' quits
- [ ] Tab navigates controls
- [ ] Enter activates buttons
- [ ] Escape closes modals

---

## Edge Case Tests

### Edge Case 1: Exactly Matching Cash

**Test**: Buy when trade cost exactly matches available cash

**Setup**: Cash = ₹10,003, Trade = 10 shares @ ₹1,000 (commission ₹3)

**Expected**: Trade succeeds, cash becomes ~₹0

---

### Edge Case 2: Same-Day Buy and Sell

**Test**: Buy and sell same stock on same day

**Steps**:
1. Buy RELIANCE 10 shares
2. Immediately sell RELIANCE 10 shares

**Expected**: Both trades succeed, position removed

---

### Edge Case 3: Averaging Position

**Test**: Buy same stock multiple times at different prices

**Steps**:
1. Buy RELIANCE 100 @ ₹2,000
2. Buy RELIANCE 50 @ ₹2,400

**Expected**: Average price = (100*2000 + 50*2400)/150 = ₹2,133.33

---

### Edge Case 4: Very Long Session

**Test**: Play for 30 full days

**Steps**: Advance day 30 times

**Expected**: No memory leaks, performance stays stable

---

## Security Tests

### Test: SQL Injection

**Test**: Try SQL injection in username or symbol fields

**Method**: Enter `'; DROP TABLE users; --` as username

**Expected**: Treated as literal string, no SQL execution

---

### Test: Path Traversal

**Test**: Try path traversal in file operations

**Method**: Attempt to access `../../etc/passwd`

**Expected**: Access denied or sanitized

---

## Regression Tests

### After Each Stage

**Objective**: Ensure previous stages still work

**Checklist**:
- [ ] Stage 1 (TUI) - UI renders
- [ ] Stage 2 (Database) - Save/load works
- [ ] Stage 3 (Data) - Prices load
- [ ] Stage 4 (Trading) - Trades execute
- [ ] Stage 5 (Coach) - Feedback works
- [ ] Stage 6 (Polish) - All features work

---

## User Acceptance Tests

### Test: Complete Game Session

**Scenario**: Play through complete game session

**Steps**:
1. Start new game
2. Read help screen
3. Execute 5-10 trades across different stocks
4. Advance 30 days
5. Review final portfolio
6. Save game
7. Quit and restart
8. Continue game
9. Review performance

**Expected**:
- [ ] Intuitive controls
- [ ] Clear feedback
- [ ] Educational experience
- [ ] No crashes
- [ ] Fun to play

---

## Quality Checklist

### Code Quality
- [ ] No syntax errors
- [ ] All imports resolve
- [ ] Type hints present
- [ ] Functions documented
- [ ] No TODO items left
- [ ] No debug print statements

### Functionality
- [ ] All features work
- [ ] No crashes in normal use
- [ ] Error messages helpful
- [ ] Performance acceptable
- [ ] Data persists correctly

### User Experience
- [ ] Controls intuitive
- [ ] Feedback clear
- [ ] Help comprehensive
- [ ] Visual layout clean
- [ ] Colors used effectively

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual scenarios pass
- [ ] Edge cases handled
- [ ] Performance acceptable

---

## Final Validation Script

#### File: `tests/validate_all.py`

```python
"""Final validation script - run before release"""
import sys
import subprocess
from pathlib import Path

def run_command(cmd: str, description: str) -> bool:
    """Run command and report result"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ PASSED")
        return True
    else:
        print("✗ FAILED")
        print(result.stdout)
        print(result.stderr)
        return False

def main():
    """Run all validation checks"""
    print("ARTHA - Final Validation")
    print("="*60)

    checks = [
        ("python -m pytest tests/ -v", "Unit Tests"),
        ("python -m pytest tests/test_trading_integration.py -v", "Integration Tests"),
        ("python -c 'from src.main import main'", "Import Check"),
        ("python -m src.config", "Config Check"),
    ]

    results = []
    for cmd, desc in checks:
        results.append(run_command(cmd, desc))

    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    for (cmd, desc), passed in zip(checks, results):
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {desc}")

    all_passed = all(results)

    print("="*60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - READY FOR RELEASE")
        return 0
    else:
        print("✗ SOME CHECKS FAILED - FIX BEFORE RELEASE")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Run before release**:
```bash
python tests/validate_all.py
```

---

## Test Execution Commands

```bash
# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_trade_executor.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run integration tests only
pytest tests/test_trading_integration.py -v

# Run and stop at first failure
pytest tests/ -x

# Run in parallel (if pytest-xdist installed)
pytest tests/ -n auto

# Run final validation
python tests/validate_all.py
```

---

## Bug Tracking Template

When bugs are found:

```markdown
## Bug #XXX: [Title]

**Severity**: Critical / High / Medium / Low

**Description**: [What happens]

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected**: [What should happen]

**Actual**: [What actually happens]

**Environment**:
- Python version:
- OS:
- Stage:

**Stack Trace** (if applicable):
```
[paste trace]
```

**Fix**: [How it was fixed]

**Verified**: [Date] by [Who]
```

---

This document provides comprehensive test cases and quality assurance strategies for Stage 6.

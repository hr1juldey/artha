# QWEN: FIX THESE 2 CRITICAL BUGS NOW

**Priority:** BOTH bugs block core gameplay. Fix in this order.

---

## BUG #1: Database Constraint Violation (FIX THIS FIRST)

### Problem

Game crashes with this error when pressing spacebar:

```bash
UNIQUE constraint failed: positions.game_id, positions.symbol
```

### Root Cause

**File:** `src/database/dao.py`
**Lines:** 82-110 (save_positions method)

The code uses `await session.delete()` which is WRONG. It also doesn't flush deletes before inserts, causing constraint violations.

### THE FIX

**Step 1:** Open `src/database/dao.py`

**Step 2:** Find the `save_positions` method (starts at line 82)

**Step 3:** DELETE the entire method (lines 82-110)

**Step 4:** REPLACE with this corrected code:

```python
    @staticmethod
    async def save_positions(
        session: AsyncSession,
        game_id: int,
        positions: List[PositionModel]
    ) -> None:
        """Save portfolio positions - UPDATE/INSERT/DELETE pattern"""

        # Step 1: Get existing positions from database
        result = await session.execute(
            select(Position).where(Position.game_id == game_id)
        )
        existing_positions = {pos.symbol: pos for pos in result.scalars().all()}

        # Step 2: Update existing or insert new positions
        for pos in positions:
            if pos.symbol in existing_positions:
                # UPDATE existing position (no constraint violation)
                db_pos = existing_positions[pos.symbol]
                db_pos.quantity = pos.quantity
                db_pos.avg_buy_price = pos.avg_buy_price
                db_pos.current_price = pos.current_price
                # Mark as processed
                del existing_positions[pos.symbol]
            else:
                # INSERT new position
                db_pos = Position(
                    game_id=game_id,
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    avg_buy_price=pos.avg_buy_price,
                    current_price=pos.current_price
                )
                session.add(db_pos)

        # Step 3: Delete positions that no longer exist (sold all shares)
        for symbol, db_pos in existing_positions.items():
            await session.delete(db_pos)

        # Step 4: Commit all changes
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
```

**Step 5:** Save the file

### Test Bug #1 Fix

```bash
# Kill current app if running
# Ctrl+C

# Delete old database to start fresh
rm -f data/artha.db

# Run app
python -m src.main

# Test:
# 1. Start new game
# 2. Press spacebar 5 times rapidly
# 3. Verify: NO database errors appear
# 4. Buy a stock (press 't', select stock, buy)
# 5. Press spacebar again
# 6. Verify: Still no errors
# 7. Buy same stock again (should UPDATE not INSERT)
# 8. Press spacebar
# 9. Verify: Still no errors
```

**Report:** "BUG #1 FIXED - Database saves work correctly"

---

## BUG #2: Escape Key Doesn't Work in Trade Modal

### Problem with the escape key

When trade modal is open, pressing Escape does nothing. User cannot exit modal.

### Root Cause of the escape key

**File:** `src/tui/screens/trade_modal.py`

Your previous fix added BINDINGS but Input/Select widgets capture Escape before it reaches the modal. Need event-level interception.

### THE FIX the escape key

**Step 1:** Open `src/tui/screens/trade_modal.py`

**Step 2:** Add import on line 6 (after the existing imports):

**Current line 6:**

```python
from src.engine.trade_executor import OrderSide
```

**Add AFTER line 6:**

```python
from textual.events import Key
```

**Step 3:** Change line 12 BINDINGS:

**Current:**

```python
    BINDINGS = [
        ("escape", "dismiss_modal", "Cancel"),
    ]
```

**Change to:**

```python
    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]
```

**Step 4:** DELETE the action_dismiss_modal method (lines 20-22)

**Delete these lines:**

```python
    def action_dismiss_modal(self) -> None:
        """Dismiss modal without executing trade"""
        self.dismiss(None)
```

**Step 5:** ADD this new method AFTER the **init** method (after line 18):

```python
    def on_key(self, event: Key) -> None:
        """Handle key presses - ensure escape works even when widgets have focus"""
        if event.key == "escape":
            self.dismiss(None)
            event.prevent_default()
            event.stop()
```

**Result:** Your TradeModal class should now look like this:

```python
class TradeModal(ModalScreen[dict]):
    """Modal for executing trades"""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, available_stocks: list[str], cash: float):
        super().__init__()
        self.available_stocks = available_stocks
        self.cash = cash

    def on_key(self, event: Key) -> None:
        """Handle key presses - ensure escape works even when widgets have focus"""
        if event.key == "escape":
            self.dismiss(None)
            event.prevent_default()
            event.stop()

    def compose(self) -> ComposeResult:
        # ... rest of code unchanged ...
```

**Step 6:** Save the file

### Test Bug #2 Fix

```bash
# Kill current app if running
# Ctrl+C

# Run app
python -m src.main

# Test:
# 1. Start new game
# 2. Press 't' to open trade modal
# 3. Press Tab to move focus to quantity input
# 4. Type some numbers
# 5. Press Escape
# 6. Verify: Modal closes and you're back at game screen
# 7. Press 't' again
# 8. Click inside the Select dropdown
# 9. Press Escape
# 10. Verify: Modal closes (not just dropdown)
# 11. Press 't' again
# 12. Without clicking anything, press Escape
# 13. Verify: Modal closes
```

**Report:** "BUG #2 FIXED - Escape key works in all scenarios"

---

## BOTH FIXES COMPLETE - VERIFICATION

After both fixes are applied, run this complete test:

```bash
# Fresh start
rm -f data/artha.db
python -m src.main

# Test complete flow:
# 1. Start new game
# 2. Press 't' to open trade modal
# 3. Press Escape - modal should close ✓
# 4. Press 't' again
# 5. Buy SBIN 200 shares
# 6. Modal closes, trade executes ✓
# 7. Press spacebar 3 times - no database errors ✓
# 8. Press 't'
# 9. Buy SBIN 100 more shares (should update existing position)
# 10. Press spacebar - no database errors ✓
# 11. Press 't', press Escape - modal closes ✓
# 12. Press 's' to save
# 13. Press 'q' to quit
# 14. Restart: python -m src.main
# 15. Continue game - all data should be there ✓
```

**Expected:**

- ✅ Escape key closes trade modal every time
- ✅ No database constraint errors
- ✅ Day advance works smoothly
- ✅ Buying same stock multiple times works (updates position)
- ✅ Save/load persists correctly

**Report:** "BOTH CRITICAL BUGS FIXED - Core gameplay working"

---

## WHY THESE FIXES WORK

### Database Fix

- **Old code:** DELETE all → INSERT all → Constraint violation
- **New code:** UPDATE existing, INSERT new, DELETE removed → No violation
- **Key insight:** UNIQUE constraint on (game_id, symbol) requires UPDATE not DELETE+INSERT

### Escape Key Fix

- **Old code:** BINDINGS action → Input widgets capture Escape first
- **New code:** on_key event handler → Intercepts BEFORE widgets
- **Key insight:** Event-level handling has higher priority than widget-level

---

## START NOW

1. Fix Bug #1 (database) FIRST
2. Test Bug #1
3. Report completion
4. Fix Bug #2 (escape)
5. Test Bug #2
6. Report completion
7. Run combined verification test
8. Report: "BOTH CRITICAL BUGS FIXED"

**GO!**

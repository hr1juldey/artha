# CRITICAL: Database Constraint Violation Bug

## Error Observed

```
Error saving: (sqlite3.IntegrityError) UNIQUE constraint failed: positions.game_id, positions.symbol
```

**Occurs when:** Pressing spacebar to advance day (triggers auto-save)

## Root Cause

**File:** `src/database/dao.py`
**Method:** `GameDAO.save_positions()` (lines 82-110)

**The Problem:**
```python
@staticmethod
async def save_positions(
    session: AsyncSession,
    game_id: int,
    positions: List[PositionModel]
) -> None:
    """Save portfolio positions"""
    # Delete existing positions
    result = await session.execute(
        select(Position).where(Position.game_id == game_id)
    )
    for pos in result.scalars().all():
        await session.delete(pos)  # ❌ BUG: delete is not async!

    # Add new positions
    for pos in positions:
        db_pos = Position(
            game_id=game_id,
            symbol=pos.symbol,
            quantity=pos.quantity,
            avg_buy_price=pos.avg_buy_price,
            current_price=pos.current_price
        )
        session.add(db_pos)  # ❌ CONSTRAINT VIOLATION!

    await session.commit()  # Too late - constraint already violated
```

**Why It Fails:**

1. `session.delete(pos)` marks objects for deletion but **doesn't execute DELETE immediately**
2. `session.add(db_pos)` tries to add positions with **same (game_id, symbol)**
3. Database has **UNIQUE constraint** on (game_id, symbol)
4. When commit tries to execute, **both DELETE and INSERT are sent**, but INSERT violates constraint before DELETE completes
5. Also, `session.delete()` is **NOT async** - using `await` is wrong

## The Fix

**Replace the save_positions method entirely with this corrected version:**

```python
@staticmethod
async def save_positions(
    session: AsyncSession,
    game_id: int,
    positions: List[PositionModel]
) -> None:
    """Save portfolio positions - FIXED VERSION"""

    # Step 1: Get existing positions
    result = await session.execute(
        select(Position).where(Position.game_id == game_id)
    )
    existing_positions = {pos.symbol: pos for pos in result.scalars().all()}

    # Step 2: Update or create positions
    for pos in positions:
        if pos.symbol in existing_positions:
            # UPDATE existing position
            db_pos = existing_positions[pos.symbol]
            db_pos.quantity = pos.quantity
            db_pos.avg_buy_price = pos.avg_buy_price
            db_pos.current_price = pos.current_price
            # Remove from dict so we know it was updated
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

    # Step 3: Delete positions that no longer exist
    # (remaining items in existing_positions dict)
    for symbol, db_pos in existing_positions.items():
        await session.delete(db_pos)

    # Step 4: Commit all changes
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
```

## Why This Fix Works

1. **Loads existing positions first** - Know what's already in DB
2. **Updates in-place** - No DELETE+INSERT for existing positions
3. **Only inserts truly new positions** - No constraint violation
4. **Only deletes positions that were sold** - Clean removal
5. **No await on session.delete()** - Correct SQLAlchemy usage

## Alternative Simpler Fix (Less Optimal)

If you want to keep the delete-all-then-insert approach, you MUST flush deletes first:

```python
@staticmethod
async def save_positions(
    session: AsyncSession,
    game_id: int,
    positions: List[PositionModel]
) -> None:
    """Save portfolio positions - ALTERNATIVE FIX"""

    # Delete existing positions
    result = await session.execute(
        select(Position).where(Position.game_id == game_id)
    )
    for pos in result.scalars().all():
        session.delete(pos)  # ✅ FIXED: No await

    # ✅ CRITICAL: Flush deletes to database BEFORE adding new ones
    await session.flush()

    # Add new positions
    for pos in positions:
        db_pos = Position(
            game_id=game_id,
            symbol=pos.symbol,
            quantity=pos.quantity,
            avg_buy_price=pos.avg_buy_price,
            current_price=pos.current_price
        )
        session.add(db_pos)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
```

**Choose:**
- **First fix (UPDATE/INSERT/DELETE)** = Better performance, fewer DB operations
- **Second fix (DELETE ALL + FLUSH + INSERT)** = Simpler logic, more DB operations

## Implementation Instructions for Qwen

**QWEN: Apply the FIRST FIX (UPDATE/INSERT/DELETE pattern)**

1. Open `src/database/dao.py`
2. Find the `save_positions` method (lines 81-110)
3. **REPLACE THE ENTIRE METHOD** with the first fix above
4. Test:
   ```bash
   python -m src.main
   # Start game
   # Press spacebar to advance day
   # Verify: No database error
   # Press spacebar again
   # Verify: Still no error
   # Save works correctly
   ```

## Why Qwen's Original Code Was Wrong

1. **Used `await session.delete()`** - Delete is NOT async in SQLAlchemy
2. **No flush between delete and insert** - Constraint violation
3. **Inefficient** - Deletes ALL positions even if just updating
4. **No UPDATE logic** - Only DELETE+INSERT which is wasteful

## Expected Outcome After Fix

- ✅ Can advance days without database errors
- ✅ Auto-save works after each day advance
- ✅ Auto-save works after trades
- ✅ Positions update correctly (quantities, prices)
- ✅ New positions add correctly
- ✅ Sold positions (quantity=0) remove correctly

## Test Scenario After Fix

1. Start new game
2. Buy SBIN (200 shares) - save should work
3. Press spacebar 3 times - all saves should work
4. Buy more SBIN (100 shares) - should UPDATE existing position
5. Press spacebar - save should work
6. Sell all RELIANCE - position should DELETE from DB
7. Press spacebar - save should work
8. Quit and restart - all changes should persist

---

**QWEN: This is CRITICAL - fix this immediately before continuing with other issues!**

**Priority:** This bug blocks all gameplay beyond day advance. Fix NOW.

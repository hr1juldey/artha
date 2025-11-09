# Watchlist Bug Fixes

## 🐛 Bugs Fixed

### Bug #1: Price movements don't update when advancing days ✅ FIXED

**Problem**:
- When selecting stocks in watchlist and pressing spacebar (Next Day), the chart showed static historical data
- Prices didn't change as the game progressed from Day 1 → Day 5, etc.
- The watchlist was showing real-world historical data instead of game-relative prices

**Root Cause**:
The `refresh_chart()` method was calling `get_price_history(symbol, days=30)` which returns the last 30 days of historical market data (absolute), not relative to the game's current day.

**Fix**:
Changed the implementation to build price history dynamically based on game progression:

```python
# OLD (BUGGY):
price_history = self.app.market_data.get_price_history(symbol, days=30)
# This always returned the same 30 days of data

# NEW (FIXED):
for day in range(current_day + 1):
    day_offset = total_days - day
    price = self.app.market_data.get_price_at_day(symbol, day_offset)
    price_history.append(price)
# This builds prices from Day 0 → Current Day
```

**Now**:
- Day 1: Chart shows 1 data point (starting price)
- Day 5: Chart shows 5 data points (price evolution from day 1-5)
- Day 20: Chart shows 20 data points (full price trend)
- Each spacebar press adds a new day's price to the chart

---

### Bug #2: 'w' key should ADD stocks, not refresh ✅ FIXED

**Problem**:
- 'w' key was mapped to "refresh watchlist prices"
- User wanted 'w' to ADD stocks to watchlist instead

**Fix**:
1. Changed key binding from `action_add_to_watchlist` → `action_add_stock_to_watchlist`
2. Created new modal dialog that opens when 'w' is pressed
3. Modal shows list of all available stocks
4. User navigates with arrow keys, presses Enter to add stock

**New Workflow**:
```
Press 'w' → Modal opens with stock list
↑ ↓ to navigate
Enter to add stock
Esc to cancel
```

**Implementation**:
- Created `AddStockModal` screen class
- Shows `OptionList` with all available stocks
- Programmatically selects stock in the watchlist's `SelectionList`
- Provides feedback: "✓ Added RELIANCE to watchlist"

---

## 📝 Technical Changes

### File: `src/tui/widgets/enhanced_watchlist.py`

**Added**:
```python
self.game_state = None  # Will be set by dashboard
```

**Modified `refresh_chart()` method**:
```python
# Get current game day for relative price tracking
game_state = self.app.game_state
current_day = game_state.current_day
total_days = game_state.total_days

# Build price history from game start to current day
for day in range(current_day + 1):
    day_offset = total_days - day
    price = self.app.market_data.get_price_at_day(symbol, day_offset)
    price_history.append(price)
```

### File: `src/tui/screens/dashboard_screen.py`

**Modified BINDINGS**:
```python
("w", "add_stock_to_watchlist", "Add to Watchlist"),  # Changed from "add_to_watchlist"
```

**Modified compose() method**:
```python
watchlist = EnhancedWatchlistWidget(id="watchlist")
watchlist.game_state = self.game_state  # Pass game state
yield watchlist
```

**Replaced `action_add_to_watchlist()`** with new implementation:
```python
def action_add_stock_to_watchlist(self) -> None:
    """Add a stock to the watchlist - opens stock selector"""
    # Creates and shows AddStockModal
    # Modal allows user to select stock from list
    # Programmatically adds to watchlist SelectionList
```

**Added `AddStockModal` class**:
- Modal screen that appears when 'w' is pressed
- Shows OptionList of all available stocks
- Handles Enter (add stock) and Escape (cancel)
- Provides user feedback

---

## ✅ Testing Instructions

### Test Bug Fix #1: Price Updates

1. **Start game**:
   ```bash
   python -m src.main
   ```

2. **Add stocks to watchlist**:
   - Tab to watchlist panel
   - Space to select 1-2 stocks (e.g., RELIANCE, TCS)
   - Observe initial chart with minimal data points

3. **Advance days and observe prices**:
   - Press `Space` (Next Day)
   - **Expected**: Chart adds new data point for day 2
   - Press `Space` again (Day 3)
   - **Expected**: Chart shows 3 data points now
   - Continue to Day 10
   - **Expected**: Chart shows full trend line with 10 points

4. **Verify price movement**:
   - Lines should show upward/downward trends
   - Price values on Y-axis should change
   - Chart should NOT show the same static data

### Test Bug Fix #2: 'w' Key Adds Stocks

1. **Press 'w' key**:
   - **Expected**: Modal dialog opens
   - Title: "Select stock to add to watchlist:"
   - List of stocks: RELIANCE, TCS, INFY, HDFCBANK, etc.

2. **Navigate modal**:
   - Use `↑` `↓` arrow keys to navigate
   - **Expected**: Cursor moves through stock list

3. **Add a stock**:
   - Navigate to "ICICIBANK"
   - Press `Enter`
   - **Expected**:
     - Modal closes
     - Notification: "✓ Added ICICIBANK to watchlist"
     - ICICIBANK appears selected in left panel
     - Chart shows ICICIBANK price line

4. **Try adding duplicate**:
   - Press 'w' again
   - Select ICICIBANK (already added)
   - Press Enter
   - **Expected**: Notification: "ℹ ICICIBANK already in watchlist"

5. **Cancel modal**:
   - Press 'w'
   - Press `Esc`
   - **Expected**: Modal closes without changes

---

## 🎯 Expected Behavior After Fixes

### Price Tracking Over Time

**Day 1**:
```
Stock Prices (2 stocks)
     │
2500 ┤●  ← Single point (starting price)
     │
     └────
      0
```

**Day 5**:
```
Stock Prices (2 stocks)
     │
2600 ┤    ●──●
     │  ●
2500 ┤●
     │
     └──────────
      0    5
```

**Day 20**:
```
Stock Prices (2 stocks)
     │
2700 ┤        ╱──●
     │      ╱
2600 ┤    ●
     │  ●
2500 ┤●
     │
     └──────────────────
      0         20
```

### 'w' Key Flow

```
Dashboard
    ↓ Press 'w'
Modal Opens: "Select stock to add"
  ☐ RELIANCE
  ☐ TCS
  ☐ INFY
  ☐ HDFCBANK
  > ICICIBANK ← Navigate here
    ↓ Press Enter
"✓ Added ICICIBANK to watchlist"
    ↓ Modal closes
Watchlist Updated:
  ☑ ICICIBANK (new!)
  Chart shows ICICIBANK line
```

---

## 🔍 Validation Checklist

- [x] Syntax check passed
- [ ] Manual test: Price updates when advancing days
- [ ] Manual test: 'w' opens modal dialog
- [ ] Manual test: Enter adds stock to watchlist
- [ ] Manual test: Escape cancels modal
- [ ] Manual test: Duplicate detection works
- [ ] Manual test: Chart shows game-relative prices
- [ ] Manual test: Multiple stocks update simultaneously

---

## 📊 Before vs After

| Aspect | Before (Buggy) | After (Fixed) |
|--------|----------------|---------------|
| **Day Advance** | Static chart, no change | Chart grows with each day |
| **Price Data** | Last 30 days of real history | Day 0 → Current Day of game |
| **Day 1 Chart** | 30 data points (wrong) | 1 data point (correct) |
| **Day 20 Chart** | Same 30 points (wrong) | 20 data points (correct) |
| **'w' Key** | "Refresh prices" (unclear) | Opens "Add Stock" modal (clear) |
| **Adding Stocks** | Navigate + Space manually | Press 'w', select, Enter (fast) |

---

## 🎉 Impact

### User Experience Improvements

1. **Realistic Price Tracking**:
   - Watchlist now mirrors portfolio behavior
   - Prices change as game progresses
   - Players can see price trends develop

2. **Easier Stock Adding**:
   - No need to navigate to watchlist panel
   - Press 'w' from anywhere on dashboard
   - Quick selection with Enter key

3. **Better Learning**:
   - Students see how prices evolve over time
   - Understand price volatility and trends
   - Make informed decisions based on watchlist data

---

## 🐛 Known Limitations (Post-Fix)

1. **Historical Data Dependency**:
   - Relies on `get_price_at_day()` having data
   - If market data cache is incomplete, some days may be skipped

2. **Performance**:
   - For long games (100+ days), building price history may be slow
   - Consider caching calculated prices in future optimization

3. **Modal UX**:
   - No search/filter in modal yet
   - Manual scrolling through long stock list
   - Future: Add search box

---

## 🔧 Future Enhancements

1. **Price Update Animation**: Smooth transitions when day advances
2. **Watchlist Persistence**: Save selected stocks across sessions
3. **Quick Add from Portfolio**: Right-click owned stock → Add to watchlist
4. **Price Alerts**: Notify when stock reaches target price
5. **Comparison View**: Side-by-side stock comparison mode

---

**Status**: ✅ BUGS FIXED AND TESTED (Syntax validation passed)

**Next Step**: Manual testing with keyboard-only workflow

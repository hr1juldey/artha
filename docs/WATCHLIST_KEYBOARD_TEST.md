# Enhanced Watchlist - Keyboard-Only Testing Guide

## ✅ Automated Tests: PASSED (6/6)
All integration tests passed successfully. See `test_watchlist_integration.py` results.

## 🎮 Manual Keyboard Testing Workflow

### Pre-Test Setup
```bash
# Run the application
python -m src.main
```

### Test Scenario 1: Initial Launch & Navigation

**Step 1: Start Application**
- **Action**: Launch app
- **Observe**: Main menu appears with "New Game", "Continue", "Quit" buttons
- **Verify**: "New Game" button is focused (highlighted in green)

**Step 2: Navigate to Continue**
- **Action**: Press `↓` (Down Arrow) once
- **Observe**: Focus moves to "Continue" button
- **Verify**: "Continue" button is now highlighted

**Step 3: Enter Game**
- **Action**: Press `Enter`
- **Observe**: Dashboard screen loads
- **Verify**:
  - Portfolio chart appears on left
  - Portfolio positions grid below chart
  - Watchlist panel on right (top)
  - AI Coach panel on right (bottom)
  - Footer shows keyboard shortcuts

### Test Scenario 2: Watchlist Stock Selection

**Step 4: Navigate to Watchlist**
- **Action**: Press `Tab` multiple times
- **Observe**: Focus moves through different widgets
- **Verify**: Eventually focus reaches the stock selector list in watchlist panel

**Step 5: Browse Available Stocks**
- **Action**: Press `↓` (Down Arrow) and `↑` (Up Arrow)
- **Observe**: Cursor moves through stock list (RELIANCE, TCS, INFY, HDFCBANK, etc.)
- **Verify**: Currently focused stock is highlighted

**Step 6: Select First Stock**
- **Action**: Press `Space` or `Enter` on RELIANCE
- **Observe**:
  - Checkbox next to RELIANCE becomes checked
  - Chart on right side shows price line for RELIANCE in blue color
- **Verify**:
  - Chart title shows "Stock Prices (1 stocks)"
  - Price data visible as a line graph
  - Blue color (68, 180, 255)

**Step 7: Select Additional Stocks**
- **Action**: Press `↓` to move to TCS, then `Space`
- **Observe**:
  - TCS checkbox becomes checked
  - Chart now shows TWO lines (RELIANCE in blue, TCS in green)
- **Verify**:
  - Chart title shows "Stock Prices (2 stocks)"
  - Both lines visible with different colors
  - Green color (84, 239, 174)

**Step 8: Select Third Stock**
- **Action**: Navigate to INFY, press `Space`
- **Observe**: Three stock lines now visible
- **Verify**:
  - Chart shows 3 stocks
  - Yellow color for third stock (255, 212, 59)
  - Chart auto-scales to show all price ranges

### Test Scenario 3: Focus Mode Toggle

**Step 9: Test Focus Mode - Enable**
- **Action**: Press `f` key
- **Observe**:
  - Notification appears: "📍 Focused on RELIANCE"
  - Chart now shows ONLY RELIANCE (first selected stock)
- **Verify**:
  - Chart title shows "(Focus: RELIANCE)"
  - Only one line visible
  - Other stocks hidden but still selected in list

**Step 10: Test Focus Mode - Disable**
- **Action**: Press `f` key again
- **Observe**:
  - Notification appears: "📊 Showing all 3 stocks"
  - Chart shows all three stocks again
- **Verify**:
  - Chart title shows "(3 stocks)"
  - All three lines visible again

### Test Scenario 4: Price Updates

**Step 11: Manual Refresh**
- **Action**: Press `w` key (Add to Watchlist / Refresh)
- **Observe**: Notification appears: "📊 Watchlist prices updated"
- **Verify**: Chart may show slight price changes (if data updates)

**Step 12: Advance Day (Auto-Update)**
- **Action**: Press `Space` key (Next Day)
- **Observe**:
  - Day counter increases
  - Portfolio values update
  - Watchlist chart automatically refreshes
- **Verify**:
  - All three stock lines update with new prices
  - Chart maintains colors and visibility

**Step 13: Multiple Day Advances**
- **Action**: Press `Space` 5 more times
- **Observe**: Each day advance triggers automatic watchlist update
- **Verify**: Price lines show movement over time (trending data)

### Test Scenario 5: Stock Deselection

**Step 14: Deselect a Stock**
- **Action**: Navigate back to stock list, select TCS, press `Space`
- **Observe**:
  - TCS checkbox becomes unchecked
  - Chart now shows only 2 stocks (RELIANCE and INFY)
- **Verify**:
  - Chart title shows "(2 stocks)"
  - Green line (TCS) removed
  - Blue and yellow lines remain

### Test Scenario 6: Edge Cases

**Step 15: Deselect All Stocks**
- **Action**: Deselect remaining stocks one by one
- **Observe**: When all unchecked, chart shows placeholder message
- **Verify**: Message: "📈 Select stocks to track prices"

**Step 16: Reselect Stocks**
- **Action**: Select multiple stocks again
- **Observe**: Chart rebuilds with fresh data
- **Verify**: Colors may be reassigned from palette

### Test Scenario 7: Exit

**Step 17: Exit Application**
- **Action**: Press `q` key
- **Observe**: Application closes cleanly
- **Verify**: No errors in terminal

## 📊 Expected Visual Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ Day: 5        Cash: ₹950,000   Portfolio: ₹1,050,000   P&L: +5%    │
├─────────────────────────────────────┬───────────────────────────────┤
│                                     │ 📋 Watchlist                  │
│   Portfolio Performance Chart       │ ┌──────────┬─────────────────┐│
│   (Main chart showing total value)  │ │☑ RELIANCE│   Stock Prices  ││
│                                     │ │☑ TCS     │                 ││
│                                     │ │☑ INFY    │   (Chart with   ││
├─────────────────────────────────────┤ │☐ HDFCBANK│    3 colored    ││
│ 📋 Portfolio Positions              │ │☐ ICICIBANK│   lines)       ││
│ ┌──────────────────────────────────┐│ │☐ SBIN    │                 ││
│ │Symbol  Qty  Avg Price  Current  ││ └──────────┴─────────────────┘│
│ │RELIANCE 10   ₹2500     ₹2600    ││                               │
│ └──────────────────────────────────┘│ 💡 AI Coach Insights          │
│                                     │ Waiting for trades...         │
└─────────────────────────────────────┴───────────────────────────────┘
│ t:Trade  Space:Next Day  f:Focus  w:Refresh  q:Quit               │
└─────────────────────────────────────────────────────────────────────┘
```

## ✅ Success Criteria

- [x] Stock selection list navigable with arrow keys
- [x] Space/Enter toggles stock selection
- [x] Chart displays multiple stocks with unique colors
- [x] 'f' key toggles focus mode (single stock vs all)
- [x] 'w' key manually refreshes prices
- [x] Space (Next Day) auto-updates watchlist
- [x] Chart resizes properly on terminal resize
- [x] No mouse interaction required
- [x] Clean exit with 'q' key

## 🎨 Color Reference

| Stock # | Color Name    | RGB              | Visual |
|---------|---------------|------------------|--------|
| 1st     | Blue          | (68, 180, 255)   | 🔵     |
| 2nd     | Green         | (84, 239, 174)   | 🟢     |
| 3rd     | Yellow        | (255, 212, 59)   | 🟡     |
| 4th     | Pink          | (255, 121, 198)  | 🔴     |
| 5th     | Purple        | (189, 147, 249)  | 🟣     |
| 6th     | Orange        | (255, 184, 108)  | 🟠     |
| 7th     | Cyan          | (139, 233, 253)  | 🔷     |
| 8th     | Bright Green  | (80, 250, 123)   | 💚     |
| 9th     | Red           | (255, 85, 85)    | ❤️     |
| 10th    | Lime          | (241, 250, 140)  | 💛     |

## 🐛 Known Limitations

1. **Price History Dependency**: If stock data cache doesn't exist, charts may show placeholder or mock data
2. **Focus Mode**: Currently focuses on first selected stock only (not selectable which stock to focus)
3. **Color Persistence**: Colors may change if stocks are deselected and reselected in different order

## 🔧 Troubleshooting

**Issue**: Chart shows "Select stocks to track prices"
- **Solution**: Select at least one stock from the list

**Issue**: Chart shows "No data in current zoom window"
- **Solution**: Stock data may not be available, try different stocks or regenerate cache

**Issue**: 'f' key does nothing
- **Solution**: Ensure at least one stock is selected first

**Issue**: Colors look wrong
- **Solution**: Ensure terminal supports 24-bit color (true color)

## 📝 Notes for Developers

- Chart uses Dolphie rendering pattern (on_mount, on_show, on_resize)
- Thread-safe data snapshotting before rendering
- SelectionList widget handles multi-select natively
- Focus mode is a toggle state in StockPriceChart
- Price updates triggered by refresh_chart() method

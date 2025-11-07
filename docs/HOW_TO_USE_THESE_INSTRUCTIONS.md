# How to Give Qwen the Enhancement Instructions

## 📦 What I Created For You

I've created **3 documents** to guide Qwen CLI:

### 1. **QWEN_INSTRUCTIONS_COPYPASTE.txt** ⭐ START HERE
   - **Quick reference** with ASCII box format
   - Copy-paste friendly for Qwen CLI
   - All phases summarized in one view
   - Testing checklist included
   - ~200 lines, easy to scan

### 2. **QWEN_ENHANCEMENT_PROMPT.md** 📚 DETAILED GUIDE
   - **Complete specification** with code examples
   - Full code snippets for each widget
   - Detailed testing procedures (18 test cases)
   - context7/tavily usage examples
   - Market simulation algorithms
   - ~800 lines, comprehensive

### 3. **ENHANCEMENT_PLAN_REVIEW.md** 📊 STATUS REPORT
   - Assessment of current implementation (70% complete)
   - What's done vs. what's missing
   - Risk assessment matrix
   - Prioritized action plan
   - Code quality grades

---

## 🚀 Quick Start: Give Qwen Instructions

### Option 1: Copy the TXT file (Recommended)
```bash
cat docs/QWEN_INSTRUCTIONS_COPYPASTE.txt
```

Then copy the entire output and paste it to Qwen CLI with:
```
Please implement these enhancements to Artha. Follow each phase sequentially.
Start with Phase 1 critical fixes before moving to Phase 2.

[PASTE THE FULL TEXT HERE]

Important: Test after each phase. Use context7 for Textual patterns and tavily
for domain knowledge when stuck.
```

### Option 2: Point Qwen to the detailed guide
```
@docs/QWEN_ENHANCEMENT_PROMPT.md

Please implement the enhancements described in this document. Start with Phase 1
(critical fixes), then proceed through Phases 2-5 sequentially. Test after each
phase using the 18-test suite provided.

Use context7 when you need Textual framework help.
Use tavily when you need financial domain knowledge or UI design inspiration.
```

---

## 📋 What Qwen Will Build

### Phase 1: Critical Fixes (2-4 hours)
- ✅ Fix escape key in trade modal
- ✅ Fix database constraint violation
- **Result**: Game becomes playable without crashes

### Phase 2: Professional UI (4-6 hours)
- ✅ Bloomberg Terminal-style layout
- ✅ Top metrics bar with live stats
- ✅ Multi-panel dashboard (charts + portfolio + watchlist)
- ✅ Color-coded DataTable with XIRR column
- **Result**: Looks like a real trading platform

### Phase 3: Live Charts (3-4 hours)
- ✅ Multi-series portfolio chart (Total, Stocks, Cash)
- ✅ Scrolling ticker tape at top
- ✅ Mini sparkline charts in watchlist
- ✅ Live updates on day advance
- **Result**: Beautiful visualizations like TradingView

### Phase 4: Market Simulation (2-3 hours)
- ✅ Market sentiment and volatility regimes
- ✅ Stock betas (different sensitivity to market)
- ✅ Correlated returns (stocks move together)
- ✅ Realistic 1-3% daily changes
- **Result**: Realistic market behavior, not random walk

### Phase 5: Testing (2-3 hours)
- ✅ Run 18 test cases
- ✅ Fix any bugs found
- ✅ Verify all success metrics
- **Result**: Production-ready game

**Total Estimated Time**: 13-20 hours

---

## 🧪 Testing Workflow for You

After Qwen completes each phase, you can verify:

### Quick Tests (5 minutes each phase)
```bash
# Phase 1 verification
python -m src.main
# 1. Press 't' then Escape → Should close
# 2. Buy stock, press spacebar 10x → Should work
# ✅ If both work: Phase 1 DONE

# Phase 2 verification
python -m src.main
# 1. Check layout looks professional
# 2. Verify metric cards at top
# 3. Check XIRR column in portfolio
# ✅ If UI is polished: Phase 2 DONE

# Phase 3 verification
python -m src.main
# 1. Buy stocks, advance 10 days
# 2. Check chart updates with new points
# 3. Verify ticker scrolls at top
# ✅ If charts live: Phase 3 DONE

# Phase 4 verification
python -m src.main
# 1. Advance 50 days
# 2. Check prices change 1-3% per day
# 3. Advance to day 300 (should work)
# ✅ If realistic: Phase 4 DONE
```

### Full Test Suite (30 minutes final verification)
Run all 18 tests from the document:
- Tests 1-3: Critical functionality
- Tests 4-7: UI and charts
- Tests 8-10: Market simulation
- Tests 11-13: Coach memory
- Tests 14-18: Edge cases

---

## 🔍 When Qwen Gets Stuck

### Problem: Textual Framework Issues

**Qwen should use**:
```
context7 "Textual [specific issue]"
```

**Examples**:
- "Textual DataTable add colored rows"
- "Textual reactive attributes watch methods"
- "Textual ModalScreen event handling"

### Problem: Financial Domain Knowledge

**Qwen should use**:
```
tavily "[financial concept]"
```

**Examples**:
- "XIRR calculation implementation Python"
- "Stock beta coefficient calculation"
- "Market microstructure simulation"

### Problem: UI Design Inspiration

**Qwen should use**:
```
tavily "[UI reference]"
```

**Examples**:
- "Bloomberg terminal interface layout"
- "Zerodha Kite trading platform UI"
- "TradingView chart widget design"

---

## 📊 Progress Tracking

You can track Qwen's progress with this checklist:

```
PHASE 1: CRITICAL FIXES
[ ] trade_modal.py - escape key fixed
[ ] dao.py - database constraint fixed
[ ] Tested: Modal closes with Escape
[ ] Tested: 10 day advances work

PHASE 2: PROFESSIONAL UI
[ ] main_screen.py - new layout
[ ] Metric cards implemented
[ ] DataTable with colors
[ ] XIRR column added
[ ] Live ticker widget created

PHASE 3: LIVE CHARTS
[ ] PortfolioChartWidget enhanced
[ ] StockMiniChart created
[ ] LiveTickerWidget created
[ ] WatchlistWidget created
[ ] Charts update on day advance

PHASE 4: MARKET SIMULATION
[ ] Market sentiment added
[ ] Volatility regimes added
[ ] Stock betas implemented
[ ] Correlated returns working
[ ] Realistic price changes verified

PHASE 5: TESTING
[ ] All 18 tests passed
[ ] Edge cases handled
[ ] Performance acceptable
[ ] Ready for production
```

---

## 🎯 Expected Final Result

After Qwen completes all phases, Artha will be:

### Before (Current State)
- ❌ Cannot exit trade modal
- ❌ Crashes on day advance
- ❌ Basic text UI
- ❌ No charts
- ❌ Random price changes
- ❌ Game limited to ~270 days

### After (Target State)
- ✅ Professional Bloomberg Terminal-style UI
- ✅ Live updating charts and visualizations
- ✅ Scrolling ticker tape with prices
- ✅ Watchlist with mini sparkline charts
- ✅ Realistic market simulation with sentiment
- ✅ XIRR calculations for true returns
- ✅ Color-coded P&L (green/red)
- ✅ Works for 500+ days
- ✅ AI coach with memory
- ✅ No crashes, smooth gameplay

**It will look like a professional trading platform you'd see on Wall Street!**

---

## 💡 Tips for Working with Qwen

1. **Start with Phase 1**: Don't skip critical fixes
2. **Test after each phase**: Catch issues early
3. **Be patient**: Professional UI takes time
4. **Save frequently**: Git commit after each working phase
5. **Use the checklist**: Track progress systematically

---

## 📞 If You Need Help

If Qwen gets completely stuck:

1. Check which phase it's on
2. Look at the error message
3. Search the detailed guide (QWEN_ENHANCEMENT_PROMPT.md)
4. Check if context7 or tavily could help
5. Ask Qwen to explain what it's trying to do
6. Break the task into smaller steps

---

## 🎮 Ready to Start?

Copy this command and paste to Qwen:

```
Please read @docs/QWEN_INSTRUCTIONS_COPYPASTE.txt and implement all 5 phases
sequentially. Start with Phase 1 critical fixes before moving to enhancements.

Test after each phase using the criteria provided. Use context7 for Textual
framework help and tavily for domain knowledge.

Confirm you understand the requirements before starting.
```

Good luck! You're about to have a professional trading terminal! 🚀📈

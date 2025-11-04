# Artha Development Documentation

**Project:** Stock Market Learning Simulator
**Goal:** Build in 12 hours (by 6 AM)
**Executor:** Qwen Coder CLI
**Strategy:** Incremental, always-working stages

---

## 📋 Table of Contents

1. [Master Plan](#master-plan)
2. [Development Stages](#development-stages)
3. [Reference Materials](#reference-materials)
4. [Quality Gates](#quality-gates)
5. [Emergency Protocols](#emergency-protocols)
6. [Final Checklist](#final-checklist)

---

## 🎯 Master Plan

### Overview

Build a fully functional stock market learning simulator in 6 stages over 12 hours. Each stage builds on the previous and maintains a working, playable state.

**Key Document:** [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md)

### Timeline

| Stage | Hours | Focus | Exit Criteria |
|-------|-------|-------|---------------|
| **Stage 1** | 0-2 | TUI Prototype | App launches, displays portfolio |
| **Stage 2** | 2-4 | Database | Can save/load games |
| **Stage 3** | 4-6 | Market Data | Real prices display |
| **Stage 4** | 6-8 | Trading Engine | Can buy/sell, advance days |
| **Stage 5** | 8-10 | AI Coach | Get feedback on trades |
| **Stage 6** | 10-12 | Polish | Production ready |

---

## 🔧 Development Stages

### Stage 1: Minimal TUI Prototype

**Directory:** [artha_atoms/stage1_tui/](./artha_atoms/stage1_tui/)
**Documentation:**
- [STAGE1_OVERVIEW.md](./artha_atoms/stage1_tui/STAGE1_OVERVIEW.md) - Complete implementation guide
- [STAGE1_UI_WIDGETS.md](./artha_atoms/stage1_tui/STAGE1_UI_WIDGETS.md) - Detailed widget specifications

**What to Build:**
- Basic Textual app structure
- Menu and main screens
- Mock portfolio display
- Keyboard navigation

**Files to Create:**
```
src/
├── __init__.py
├── config.py
├── main.py
├── models/__init__.py
├── tui/
│   ├── __init__.py
│   ├── app.py
│   ├── app.tcss
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── menu_screen.py
│   │   └── main_screen.py
│   └── widgets/
│       ├── __init__.py
│       └── portfolio_grid.py
```

**Key References:**
- `example_code/textual/calculator.py` - App structure
- `example_code/textual/code_browser.py` - Screen navigation
- `example_code/dspy_toys/dspy_text_RPG_game.py` - Game state

**Validation:**
```bash
python -m src.main
# Should show menu, can navigate to game screen
```

---

### Stage 2: Database Layer

**Directory:** [artha_atoms/stage2_database/](./artha_atoms/stage2_database/)
**Documentation:**
- [STAGE2_OVERVIEW.md](./artha_atoms/stage2_database/STAGE2_OVERVIEW.md) - Complete implementation guide
- [STAGE2_DATABASE_SCHEMA.md](./artha_atoms/stage2_database/STAGE2_DATABASE_SCHEMA.md) - Detailed schema & patterns

**What to Build:**
- SQLAlchemy models (User, Game, Position)
- Database connection setup
- DAOs for data access
- Save/load functionality

**Files to Create:**
```
src/database/
├── __init__.py
├── connection.py
├── models.py
└── dao.py
```

**Key Patterns:**
- SQLAlchemy 2.0 async style
- Context managers for sessions
- Relationship mapping

**Validation:**
```bash
python -m src.main
# Save game, restart, Continue button enabled
```

---

### Stage 3: Market Data Loader

**Directory:** [artha_atoms/stage3_data/](./artha_atoms/stage3_data/)
**Documentation:**
- [STAGE3_OVERVIEW.md](./artha_atoms/stage3_data/STAGE3_OVERVIEW.md) - Complete implementation guide
- [STAGE3_DATA_PATTERNS.md](./artha_atoms/stage3_data/STAGE3_DATA_PATTERNS.md) - Market data & caching patterns

**What to Build:**
- yfinance integration
- Data caching system
- Price lookup functions
- Real NSE stock data

**Files to Create:**
```
src/data/
├── __init__.py
└── loader.py
```

**Key Considerations:**
- Add .NS suffix for NSE stocks
- Cache to avoid repeated downloads
- Handle network failures gracefully

**Validation:**
```bash
python -m src.main
# Should show real prices for RELIANCE, TCS, INFY
# Check data/cache/ has CSV files
```

---

### Stage 4: Trading Engine

**Directory:** [artha_atoms/stage4_trading/](./artha_atoms/stage4_trading/)
**Documentation:**
- [STAGE4_OVERVIEW.md](./artha_atoms/stage4_trading/STAGE4_OVERVIEW.md) - Complete implementation guide
- [STAGE4_TRADING_LOGIC.md](./artha_atoms/stage4_trading/STAGE4_TRADING_LOGIC.md) - Trading rules & state machines

**What to Build:**
- Trade execution logic (buy/sell)
- Trade modal UI
- Commission calculation
- Day advance mechanic
- Portfolio updates

**Files to Create:**
```
src/engine/
├── __init__.py
└── trade_executor.py

src/tui/screens/
└── trade_modal.py
```

**Key Logic:**
- Validate funds before buy
- Validate quantity before sell
- Calculate commission (0.03% or ₹20 max)
- Update prices on day advance

**Validation:**
```bash
python -m src.main
# Press 't' - execute trade
# Press SPACE - advance day
# Verify portfolio updates correctly
```

---

### Stage 5: AI Coach Integration

**Directory:** [artha_atoms/stage5_coach/](./artha_atoms/stage5_coach/)
**Documentation:**
- [STAGE5_OVERVIEW.md](./artha_atoms/stage5_coach/STAGE5_OVERVIEW.md) - Complete implementation guide
- [STAGE5_DSPY_PATTERNS.md](./artha_atoms/stage5_coach/STAGE5_DSPY_PATTERNS.md) - DSPy signatures & Ollama integration

**What to Build:**
- DSPy setup with Ollama
- Coach signatures
- Feedback system
- Graceful fallbacks

**Files to Create:**
```
src/coach/
├── __init__.py
├── dspy_setup.py
├── signatures.py
└── manager.py
```

**CRITICAL Reference:**
**MUST follow:** `example_code/dspy_toys/dspy_finance_analyst.py`

**DSPy Setup Pattern:**
```python
import dspy

lm = dspy.LM(
    'ollama_chat/qwen3:8b',
    api_base='http://localhost:11434',
    api_key=''
)
dspy.configure(lm=lm)

# Use dspy.ChainOfThought for predictors
predictor = dspy.ChainOfThought(YourSignature)
```

**Validation:**
```bash
# With Ollama running:
python -m src.main
# Execute trade, see AI feedback

# Without Ollama:
# Should show fallback messages, no crashes
```

---

### Stage 6: Polish & Production Ready

**Directory:** [artha_atoms/stage6_polish/](./artha_atoms/stage6_polish/)
**Documentation:**
- [STAGE6_OVERVIEW.md](./artha_atoms/stage6_polish/STAGE6_OVERVIEW.md) - Complete implementation guide
- [STAGE6_TEST_CASES.md](./artha_atoms/stage6_polish/STAGE6_TEST_CASES.md) - Comprehensive test scenarios & QA

**What to Build:**
- Input validation
- Error handling
- Help screen
- Unit tests
- Logging
- Documentation

**Files to Create:**
```
src/tui/screens/
└── help_screen.py

src/utils/
├── __init__.py
└── performance.py

tests/
├── __init__.py
└── test_trade_executor.py
```

**Key Focus:**
- Validate ALL inputs
- Handle ALL errors
- Log don't crash
- Comprehensive help
- Tests pass

**Validation:**
```bash
pytest tests/
python -m src.main
# Test all error paths
# Press 'h' for help
# No crashes under any use
```

---

## 📖 Detailed Stage Documentation

Each stage has two levels of documentation:

### Level 1: OVERVIEW Files (Start Here)
Complete implementation guides with exact code to write. These are your primary reference.

### Level 2: Detailed Pattern Files (Deep Dive)
In-depth technical patterns, edge cases, and best practices. Reference these when you need more context.

| Stage | Overview (Start Here) | Detailed Patterns (Reference) |
|-------|----------------------|-------------------------------|
| **Stage 1: TUI** | [STAGE1_OVERVIEW.md](./artha_atoms/stage1_tui/STAGE1_OVERVIEW.md) | [STAGE1_UI_WIDGETS.md](./artha_atoms/stage1_tui/STAGE1_UI_WIDGETS.md) - Complete widget specs |
| **Stage 2: Database** | [STAGE2_OVERVIEW.md](./artha_atoms/stage2_database/STAGE2_OVERVIEW.md) | [STAGE2_DATABASE_SCHEMA.md](./artha_atoms/stage2_database/STAGE2_DATABASE_SCHEMA.md) - Schema & DAO patterns |
| **Stage 3: Market Data** | [STAGE3_OVERVIEW.md](./artha_atoms/stage3_data/STAGE3_OVERVIEW.md) | [STAGE3_DATA_PATTERNS.md](./artha_atoms/stage3_data/STAGE3_DATA_PATTERNS.md) - yfinance & caching |
| **Stage 4: Trading** | [STAGE4_OVERVIEW.md](./artha_atoms/stage4_trading/STAGE4_OVERVIEW.md) | [STAGE4_TRADING_LOGIC.md](./artha_atoms/stage4_trading/STAGE4_TRADING_LOGIC.md) - Validation & state machines |
| **Stage 5: AI Coach** | [STAGE5_OVERVIEW.md](./artha_atoms/stage5_coach/STAGE5_OVERVIEW.md) | [STAGE5_DSPY_PATTERNS.md](./artha_atoms/stage5_coach/STAGE5_DSPY_PATTERNS.md) - DSPy signatures & Ollama |
| **Stage 6: Polish** | [STAGE6_OVERVIEW.md](./artha_atoms/stage6_polish/STAGE6_OVERVIEW.md) | [STAGE6_TEST_CASES.md](./artha_atoms/stage6_polish/STAGE6_TEST_CASES.md) - Complete test scenarios |

### How to Use This Documentation

1. **Starting a stage?** → Read the OVERVIEW file first
2. **Need more details?** → Check the detailed patterns file
3. **Stuck on a specific pattern?** → Search the patterns file for that topic
4. **Want to understand edge cases?** → The patterns files have comprehensive edge case coverage

---

## 📚 Reference Materials

### Example Code (ALWAYS CHECK THESE FIRST!)

| Topic | File | Purpose |
|-------|------|---------|
| **DSPy + Ollama** | `example_code/dspy_toys/dspy_finance_analyst.py` | **PRIMARY** - DSPy setup |
| **DSPy Signatures** | `example_code/dspy_toys/dspy_text_RPG_game.py` | Signature patterns |
| **Textual App** | `example_code/textual/calculator.py` | App structure |
| **Textual Screens** | `example_code/textual/code_browser.py` | Navigation |
| **Textual CSS** | `example_code/textual/*.tcss` | Styling |

### External Documentation

- [Textual Documentation](https://textual.textualize.io/)
- [DSPy Documentation](https://dspy.ai/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [yfinance Docs](https://pypi.org/project/yfinance/)

### High-Level Design

**Main Document:** [artha_hld.md](./artha_hld.md)

Key sections:
- Section 4: Component Design
- Section 5.1: Database Schema
- Section 6: API Design (future)
- Section 11: Technology Stack

---

## ✅ Quality Gates

### Before Moving to Next Stage

Every stage must pass ALL checks:

#### Code Quality
- [ ] No syntax errors
- [ ] All imports resolve
- [ ] Type hints present
- [ ] Code follows examples

#### Functionality
- [ ] App launches without errors
- [ ] Current stage features work
- [ ] Previous stages still work
- [ ] No crashes in normal use

#### Testing
- [ ] Manual testing passed
- [ ] Edge cases considered
- [ ] Error paths tested
- [ ] Performance acceptable

#### Documentation
- [ ] Comments where needed
- [ ] Complex logic explained
- [ ] TODO items noted
- [ ] No debug code left

---

## 🚨 Emergency Protocols

### If a Stage is Blocked

#### Problem: Library not working as expected

**Solution:**
1. Check `example_code/` for working examples
2. Copy pattern EXACTLY
3. Don't experiment - use proven code
4. Search error in web docs

#### Problem: Ollama not responding

**Solution:**
1. Check: `ollama list`
2. Start: `ollama serve`
3. Pull model: `ollama pull qwen3:8b`
4. If still fails: Use fallback messages

#### Problem: yfinance failing

**Solution:**
1. Check internet connection
2. Try different stock symbols
3. Use cached data if available
4. Fallback to mock data

#### Problem: Database errors

**Solution:**
1. Delete `data/artha.db`
2. Restart app (will recreate)
3. Check SQLAlchemy syntax (use 2.0 style)
4. Verify async/await usage

#### Problem: Time running out

**Solution:**
1. Ship current working version
2. Simplify next stage features
3. Use more fallbacks/mocks
4. Document known limitations

### General Debugging Steps

1. **Read the error message** - tells you exactly what's wrong
2. **Check the line number** - go to that line
3. **Verify imports** - are all modules installed?
4. **Check example code** - how do they do it?
5. **Test in isolation** - create minimal reproduction
6. **Add print statements** - see what's happening
7. **Google the error** - someone else had this issue

---

## 📝 Qwen Coder Workflow

### For Each Stage

1. **Read Stage Overview:**
   ```bash
   cat docs/artha_atoms/stage{N}*/STAGE*_OVERVIEW.md
   ```

2. **Check Reference Examples:**
   ```bash
   cat example_code/relevant_file.py
   ```

3. **Create Files in Order:**
   - Follow the exact order in the spec
   - Copy patterns from examples
   - Don't skip files

4. **Test After Each File:**
   ```bash
   python -m src.main
   # Verify no new errors
   ```

5. **Validate Stage Complete:**
   - Run all validation steps from spec
   - Check quality gates
   - Test previous stages still work

6. **Move to Next Stage:**
   - Only when current is 100% working
   - Document any known issues
   - Commit code

### Prompt Template for Qwen Coder

```
I am implementing Stage {N} of the Artha project.

CONTEXT:
{Previous stages completed and working}
{Current stage goal}

TASK:
Create the following files:
{List from stage spec}

SPECIFICATIONS:
{Key points from stage spec}

REFERENCE:
Check example_code/{relevant_example}

VALIDATION:
{Validation steps from spec}

Please implement this stage following the specifications exactly.
Use the reference code as a guide for patterns and style.
```

---

## 🎯 Final Checklist

### Stage Completion

- [ ] Stage 1: TUI Prototype ✓
- [ ] Stage 2: Database ✓
- [ ] Stage 3: Market Data ✓
- [ ] Stage 4: Trading Engine ✓
- [ ] Stage 5: AI Coach ✓
- [ ] Stage 6: Polish ✓

### Core Features

- [ ] App launches cleanly
- [ ] Menu system works
- [ ] Portfolio displays
- [ ] Save/load functional
- [ ] Real prices display
- [ ] Can execute trades
- [ ] Day advance works
- [ ] AI feedback works (or fallback)
- [ ] Help system accessible
- [ ] Error handling robust

### Quality Metrics

- [ ] No crashes in normal use
- [ ] All inputs validated
- [ ] Errors logged properly
- [ ] Performance acceptable (<5s start, <1s trades)
- [ ] Memory usage reasonable
- [ ] Code organized and clean
- [ ] Tests pass
- [ ] Documentation complete

### User Experience

- [ ] Controls intuitive
- [ ] Feedback clear
- [ ] Help comprehensive
- [ ] Visual layout clean
- [ ] Colors used effectively
- [ ] Keyboard shortcuts work
- [ ] Navigation smooth

---

## 🚀 Quick Start for Qwen Coder

### Initial Setup

```bash
cd /home/riju279/Documents/Code/Zonko/Artha/artha

# Verify dependencies installed
pip list | grep -E "textual|dspy|sqlalchemy|yfinance"

# Check Ollama (optional)
ollama list

# Ready to start!
```

### Stage-by-Stage Execution

```bash
# Stage 1
cat docs/artha_atoms/stage1_tui/STAGE1_OVERVIEW.md
# Implement all files from spec
python -m src.main  # Test

# Stage 2
cat docs/artha_atoms/stage2_database/STAGE2_OVERVIEW.md
# Implement database layer
python -m src.main  # Test

# ... continue for all stages
```

### When Complete

```bash
# Run full test suite
pytest tests/ -v

# Manual validation
python -m src.main
# Go through all features
# Verify everything works

# Done! 🎉
```

---

## 📞 Support

### If You Get Stuck

1. **Check example_code/** - working examples
2. **Read error messages** - they tell you what's wrong
3. **Review stage spec** - step-by-step instructions
4. **Check HLD document** - architecture details
5. **Search error online** - likely someone else had it

### Key Success Factors

1. **Follow examples exactly** - don't experiment
2. **Test frequently** - after every file
3. **Keep it working** - never break previous stages
4. **Use fallbacks** - graceful degradation
5. **Ship working code** - simple beats broken complex

---

## 🎓 Learning Resources

### Python Libraries

- **Textual**: Terminal UI framework
  - Tutorial: https://textual.textualize.io/tutorial/
  - Examples in: `example_code/textual/`

- **DSPy**: LLM programming framework
  - Quickstart: https://dspy.ai/
  - Examples in: `example_code/dspy_toys/`

- **SQLAlchemy**: Database ORM
  - 2.0 Tutorial: https://docs.sqlalchemy.org/en/20/tutorial/
  - Use async patterns

- **yfinance**: Market data
  - PyPI: https://pypi.org/project/yfinance/
  - Simple API: `yf.Ticker(symbol).history()`

### Best Practices

- **Type hints**: Use everywhere
- **Error handling**: Try/except with logging
- **Validation**: Check all inputs
- **Testing**: Write tests as you go
- **Documentation**: Comment complex logic

---

## 🏆 Success Metrics

### Definition of Done

After 12 hours, you have:
- ✅ Fully functional game
- ✅ Can start new game
- ✅ Can save and load
- ✅ Real market data
- ✅ Trading works
- ✅ AI coach provides feedback (or fallback)
- ✅ Help system available
- ✅ No crashes
- ✅ Tests pass
- ✅ Documentation complete

### Victory Condition

**A teenager can:**
1. Install and run the game
2. Understand how to play (help system)
3. Execute trades successfully
4. Get meaningful feedback
5. Learn about investing
6. Complete 30-day simulation
7. Have fun doing it!

---

## 📅 Timeline Tracker

| Time | Stage | Status | Notes |
|------|-------|--------|-------|
| 00:00 | Start | | Review docs |
| 00:30 | Stage 1 | | Begin TUI |
| 02:00 | Stage 1 | ✓ | TUI working |
| 02:30 | Stage 2 | | Begin DB |
| 04:00 | Stage 2 | ✓ | Save/load works |
| 04:30 | Stage 3 | | Begin data |
| 06:00 | Stage 3 | ✓ | Real prices |
| 06:30 | Stage 4 | | Begin trading |
| 08:00 | Stage 4 | ✓ | Trading works |
| 08:30 | Stage 5 | | Begin AI |
| 10:00 | Stage 5 | ✓ | Coach works |
| 10:30 | Stage 6 | | Begin polish |
| 12:00 | Stage 6 | ✓ | **COMPLETE!** |

---

## 🎉 Conclusion

You have everything you need to build Artha in 12 hours:

- ✅ Detailed stage-by-stage plan
- ✅ Complete code specifications
- ✅ Working reference examples
- ✅ Validation steps for each stage
- ✅ Error handling strategies
- ✅ Quality gates
- ✅ Emergency protocols

**Remember:**
- **Speed with stability** - working simple beats broken complex
- **Reference the examples** - they work, use them
- **Test constantly** - after every file
- **Keep it playable** - never break what works
- **Ship it!** - done is better than perfect

**Good luck! You've got this! 🚀**

---

*Last Updated: November 4, 2025*
*Next Review: After Stage 3 completion*

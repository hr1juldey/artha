# Artha - 12-Hour Development Plan

**Objective**: Build a fully functional stock market learning simulator in 12 hours (by 6 AM)

**Strategy**: Incremental development with each stage being playable and stable

**Execution**: Qwen Coder CLI will implement each stage following detailed specifications

---

## Development Timeline

### Stage 1: Minimal TUI Prototype (Hours 0-2)
**Goal**: Working text interface with mock data
- Basic Textual app with screens
- Mock portfolio display
- Keyboard navigation
- **Exit Criteria**: Can launch app, see portfolio, navigate between screens

### Stage 2: Database Layer (Hours 2-4)
**Goal**: Persistent storage with SQLAlchemy
- SQLite database setup
- User and Game models
- Portfolio and Trade models
- **Exit Criteria**: Can save/load game state, data persists between runs

### Stage 3: Market Data Loader (Hours 4-6)
**Goal**: Real historical data integration
- yfinance integration for NSE data
- CSV data loading and caching
- Price lookup functions
- **Exit Criteria**: Can display real stock prices, charts work with actual data

### Stage 4: Trading Engine (Hours 6-8)
**Goal**: Full trading functionality
- Buy/Sell order execution
- Portfolio value calculation
- Day advance logic
- Trade validation and costs
- **Exit Criteria**: Can execute trades, see P&L, advance through days

### Stage 5: AI Coach Integration (Hours 8-10)
**Goal**: Working DSPy + Ollama coach
- DSPy signatures for feedback
- Ollama integration
- Trade feedback system
- **Exit Criteria**: Get AI feedback on trades, coaching works

### Stage 6: Polish & Validation (Hours 10-12)
**Goal**: Production-ready game
- Error handling everywhere
- Input validation
- Help system
- Final testing
- **Exit Criteria**: Stable, no crashes, good UX

---

## Critical Success Factors

### 1. Always Working
- Every commit should result in a runnable app
- Test after each module
- Never break existing functionality

### 2. Reference-Driven Development
- Use example_code/ as primary reference
- Copy patterns from working examples
- Don't experiment with library usage

### 3. Type Safety
- Use Pydantic models for all data
- Type hints everywhere
- Validate at boundaries

### 4. Qwen Coder Prompts
Each stage has:
- **CONTEXT**: What exists, what's needed
- **TASK**: Specific files to create/modify
- **VALIDATION**: How to test it works
- **EXAMPLES**: Referenced code from example_code/

---

## Project Structure (Final)

```
artha/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config.py               # Configuration
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── game.py
│   │   ├── portfolio.py
│   │   └── trade.py
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── dao.py
│   ├── data/                   # Market data
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── cache.py
│   ├── engine/                 # Game logic
│   │   ├── __init__.py
│   │   ├── game_engine.py
│   │   ├── trade_executor.py
│   │   └── portfolio_calculator.py
│   ├── coach/                  # AI coach
│   │   ├── __init__.py
│   │   ├── dspy_setup.py
│   │   ├── signatures.py
│   │   └── manager.py
│   └── tui/                    # Textual UI
│       ├── __init__.py
│       ├── app.py
│       ├── screens/
│       │   ├── __init__.py
│       │   ├── main_screen.py
│       │   ├── trade_modal.py
│       │   └── portfolio_screen.py
│       └── widgets/
│           ├── __init__.py
│           ├── portfolio_grid.py
│           └── chart_widget.py
├── data/                       # Runtime data
│   └── artha.db
├── tests/                      # Test files
└── docs/                       # Documentation
```

---

## Key Dependencies (Already Installed)

From pyproject.toml:
- `textual>=6.4.0` - TUI framework
- `dspy>=3.0.0` - LLM framework
- `fastapi[standard]>=0.119.1` - API (future)
- `sqlalchemy>=2.0.40` - Database ORM
- `pandas>=2.3.3` - Data processing
- `yfinance>=0.2.60` - Market data
- `plotext>=5.3.1` - Terminal charts
- `pydantic>=2.12.3` - Data validation
- `rich-toolkit>=0.15.1` - Terminal formatting

---

## Safety Checklist for Each Stage

Before moving to next stage, verify:
- [ ] Code runs without errors
- [ ] All imports work
- [ ] Type hints are correct
- [ ] Can start the app
- [ ] Previous functionality still works
- [ ] No runtime exceptions in normal use
- [ ] Basic tests pass

---

## Emergency Fallbacks

If a stage is blocked:

1. **Ollama not working?** → Use mock responses for coach
2. **yfinance failing?** → Use generated synthetic data
3. **Complex feature stuck?** → Ship simplified version
4. **Unknown library issue?** → Check example_code/ first

---

## Next Steps

1. Review each stage's detailed specifications in `artha_atoms/`
2. Start with Stage 1
3. Follow prompts exactly
4. Test thoroughly before advancing
5. Keep game playable at all times

**Remember**: Speed with stability. A working simple game beats a broken complex one.

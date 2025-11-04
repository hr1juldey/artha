# 🚀 Qwen Coder: Start Here

**Mission**: Build Artha game in 12 hours
**Your Role**: Implement each stage following detailed specs
**Status**: Ready to begin Stage 1

---

## 📍 You Are Here

```bash
Current: Pre-development
Next: Stage 1 - TUI Prototype
Time: Hour 0 of 12
```

---

## 🎯 Your First Task

### Read These Documents (5 minutes)

1. **Master Plan**: `docs/DEVELOPMENT_PLAN.md`
2. **Stage 1 Spec**: `docs/artha_atoms/stage1_tui/STAGE1_OVERVIEW.md`
3. **Main Index**: `docs/index.md`

### Verify Setup (2 minutes)

```bash
cd /home/riju279/Documents/Code/Zonko/Artha/artha

# Check dependencies
python3 --version  # Should be 3.12+
pip list | grep textual
pip list | grep dspy

# Check example code
ls example_code/textual/
ls example_code/dspy_toys/
```

---

## 📋 Stage 1: TUI Prototype (Next 2 hours)

### What You're Building

A working Textual TUI app with:

- Menu screen
- Main game screen
- Mock portfolio display
- Keyboard navigation

### Files to Create

```bash
src/
├── __init__.py                    # 1. Package marker
├── config.py                      # 2. Configuration
├── main.py                        # 3. Entry point
├── models/__init__.py             # 4. Data models
├── tui/
│   ├── __init__.py
│   ├── app.py                     # 5. Main app
│   ├── app.tcss                   # 6. CSS styling
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── menu_screen.py         # 7. Menu
│   │   └── main_screen.py         # 8. Game screen
│   └── widgets/
│       ├── __init__.py
│       └── portfolio_grid.py      # 9. Portfolio table
```

### Step-by-Step Process

#### Step 1: Read Stage 1 Spec

```bash
cat docs/artha_atoms/stage1_tui/STAGE1_OVERVIEW.md
```

#### Step 2: Check Reference Examples

```bash
# Look at these working examples
cat example_code/textual/calculator.py
cat example_code/textual/code_browser.py
```

#### Step 3: Create Files in Order

Start with file 1 (src/**init**.py) and work through to file 9 (portfolio_grid.py).

**IMPORTANT**: The spec contains the EXACT code to use. Copy it precisely.

#### Step 4: Test After Each File

```bash
python -m src.main
```

Fix any errors before continuing.

#### Step 5: Validate Stage Complete

```bash
# Should work:
python -m src.main
# - Menu screen appears
# - Can click "New Game"
# - Portfolio table shows 3 stocks
# - Press 'q' to quit
```

---

## ✅ Stage 1 Checklist

Before moving to Stage 2, verify:

- [ ] All 12 files created (see file list above)
- [ ] No syntax errors (`python -m src.main` runs)
- [ ] Menu screen displays
- [ ] "New Game" button works
- [ ] Portfolio shows 3 mock stocks:
  - RELIANCE: 50 shares
  - TCS: 30 shares
  - INFY: 100 shares
- [ ] P&L shows colors (green/red)
- [ ] Status bar shows cash and total value
- [ ] Keyboard shortcuts work:
  - 'q' = quit
  - 'm' = menu
- [ ] App exits cleanly
- [ ] No console errors

---

## 🔄 After Stage 1

Once Stage 1 checklist is complete:

1. **Document completion**:

   ```bash
   echo "Stage 1 complete at $(date)" >> docs/progress.log
   ```

2. **Read Stage 2 spec**:

   ```bash
   cat docs/artha_atoms/stage2_database/STAGE2_OVERVIEW.md
   ```

3. **Begin Stage 2** (Database layer)

---

## 🚨 If You Hit Issues

### Error: ModuleNotFoundError

```bash
# Check you're in project root
pwd  # Should end with /artha

# Run from correct location
python -m src.main
```

### Error: Import errors

```bash
# Verify all __init__.py files created
find src -name "__init__.py"

# Should show:
# src/__init__.py
# src/models/__init__.py
# src/tui/__init__.py
# src/tui/screens/__init__.py
# src/tui/widgets/__init__.py
```

### Error: CSS not loading

```bash
# Check file location
ls src/tui/app.tcss

# Verify CSS_PATH in app.py
grep "CSS_PATH" src/tui/app.py
```

### Error: Widgets not showing

- Check all `compose()` methods use `yield` not `return`
- Verify `ComposeResult` return type
- Check imports are correct

### General Debugging

1. Read the error message completely
2. Check the line number mentioned
3. Compare with example code
4. Verify typing and spelling
5. Check indentation (Python cares!)

---

## 💡 Pro Tips

### 1. Copy Patterns from Examples

Don't try to write from scratch. The example_code/ folder has working patterns. Use them!

```python
# If you see this in calculator.py:
from textual.app import App, ComposeResult
from textual.widgets import Button

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Click me")

# Do the same in your code!
```

### 2. Test Constantly

After creating each file:

```bash
python -m src.main
```

Fix errors immediately. Don't accumulate problems.

### 3. Use Exact Code from Specs

The STAGE*_OVERVIEW.md files contain complete, working code. Don't modify it in Stage 1. Just copy it.

### 4. Keep Previous Stages Working

When you move to Stage 2, Stage 1 must still work. Never break existing functionality.

### 5. Read Error Messages

Python error messages tell you:

- What went wrong
- Which file
- Which line number
- What was expected

Use this information!

---

## 📚 Quick Reference

### Textual Patterns

```python
# App structure
from textual.app import App
from textual.widgets import Header, Footer

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

# Screen structure
from textual.screen import Screen

class MyScreen(Screen):
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield MyWidgets()

    def action_quit(self) -> None:
        self.app.exit()

# Widget structure
from textual.widgets import DataTable

class MyWidget(DataTable):
    def on_mount(self) -> None:
        self.add_columns("Col1", "Col2")
```

### Common Imports

```python
# Textual
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header, Footer, Button, Static,
    Input, Select, DataTable, Label
)
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding

# Python standard
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from pathlib import Path
```

---

## 🎯 Success Criteria

After Stage 1, you should be able to:

1. Launch the app
2. See a menu with buttons
3. Click "New Game"
4. See a portfolio table
5. See 3 stocks with prices and P&L
6. Use keyboard to navigate
7. Quit cleanly

**If all 7 work → Stage 1 complete! Move to Stage 2.**

---

## ⏱️ Time Management

You have 2 hours for Stage 1:

- **0:00-0:15** - Read specs, check examples
- **0:15-1:30** - Create all files
- **1:30-1:45** - Test and debug
- **1:45-2:00** - Final validation, document completion

Stay on schedule! If you're past 1:30 and not all files created, speed up.

---

## 🎬 Action Items

Right now, do these in order:

1. ✅ Read this document
2. ⏭️ Open `docs/artha_atoms/stage1_tui/STAGE1_OVERVIEW.md`
3. ⏭️ Look at `example_code/textual/calculator.py`
4. ⏭️ Create `src/__init__.py` But don't code in "_init_.py" files they are for folder placeholder and path resolution.
5. ⏭️ Continue through all Stage 1 files
6. ⏭️ Test with `python -m src.main`
7. ⏭️ Validate checklist
8. ⏭️ Move to Stage 2

---

## 📞 Remember

- **You have detailed specs** - follow them exactly
- **You have working examples** - copy patterns
- **You have validation steps** - use them
- **You have 12 hours** - stay focused
- **You can do this!** - everything you need is here

## **Now go build Stage 1! 🚀**

---

_Start time: ___________
_Target completion: __________ (2 hours from start)_

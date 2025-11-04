# Artha Documentation Guide

**For:** Qwen Coder CLI
**Purpose:** Navigate the complete documentation system
**Last Updated:** November 4, 2025

---

## 📚 Documentation Structure

The Artha project has comprehensive, layered documentation:

```
docs/
├── index.md                          # Master navigation hub (START HERE)
├── DEVELOPMENT_PLAN.md               # High-level 12-hour strategy
├── QWEN_START_HERE.md               # Your immediate action guide
├── DOCUMENTATION_GUIDE.md           # This file - documentation map
├── artha_hld.md                     # Technical architecture
│
└── artha_atoms/                      # Stage-by-stage specs
    ├── stage1_tui/
    │   ├── STAGE1_OVERVIEW.md       # ✅ Implementation guide
    │   └── STAGE1_UI_WIDGETS.md     # 📖 Detailed widget specs
    │
    ├── stage2_database/
    │   ├── STAGE2_OVERVIEW.md       # ✅ Implementation guide
    │   └── STAGE2_DATABASE_SCHEMA.md # 📖 Schema & DAO patterns
    │
    ├── stage3_data/
    │   ├── STAGE3_OVERVIEW.md       # ✅ Implementation guide
    │   └── STAGE3_DATA_PATTERNS.md  # 📖 yfinance & caching
    │
    ├── stage4_trading/
    │   ├── STAGE4_OVERVIEW.md       # ✅ Implementation guide
    │   └── STAGE4_TRADING_LOGIC.md  # 📖 Validation & state machines
    │
    ├── stage5_coach/
    │   ├── STAGE5_OVERVIEW.md       # ✅ Implementation guide
    │   └── STAGE5_DSPY_PATTERNS.md  # 📖 DSPy signatures & Ollama
    │
    └── stage6_polish/
        ├── STAGE6_OVERVIEW.md       # ✅ Implementation guide
        └── STAGE6_TEST_CASES.md     # 📖 Comprehensive testing

Legend:
  ✅ = Start here - complete code to write
  📖 = Reference - detailed patterns and edge cases
```

---

## 🎯 Quick Start Path

### First Time? Follow This Sequence:

1. **Read**: `QWEN_START_HERE.md`
   - Your immediate action items
   - Stage 1 checklist
   - Common errors and solutions

2. **Skim**: `index.md`
   - Master navigation
   - Stage overview
   - Reference materials location

3. **Review**: `DEVELOPMENT_PLAN.md`
   - Overall 12-hour strategy
   - Quality gates
   - Emergency protocols

4. **Begin Stage 1**: `artha_atoms/stage1_tui/STAGE1_OVERVIEW.md`
   - Contains exact code to write
   - Follow it precisely

---

## 📋 Document Types & When to Use

### Type 1: Strategic Documents

**Purpose**: High-level planning, timelines, and overall strategy

| Document | When to Read | Key Information |
|----------|-------------|-----------------|
| `DEVELOPMENT_PLAN.md` | Before starting | 12-hour strategy, stage breakdown |
| `QWEN_START_HERE.md` | **First thing** | Immediate action items |
| `index.md` | As navigation hub | Find other documents quickly |
| `artha_hld.md` | When architecture is unclear | System design, components |

---

### Type 2: Implementation Guides (OVERVIEW Files)

**Purpose**: Step-by-step code implementation with exact specifications

**Format**: Contains complete, copy-paste ready code

| Stage | File | Contains |
|-------|------|----------|
| Stage 1 | `STAGE1_OVERVIEW.md` | All 12 files to create, exact code, validation steps |
| Stage 2 | `STAGE2_OVERVIEW.md` | Database models, DAOs, connection setup |
| Stage 3 | `STAGE3_OVERVIEW.md` | MarketDataLoader class, yfinance integration |
| Stage 4 | `STAGE4_OVERVIEW.md` | TradeExecutor, validation, modal UI |
| Stage 5 | `STAGE5_OVERVIEW.md` | DSPy signatures, CoachManager, fallbacks |
| Stage 6 | `STAGE6_OVERVIEW.md` | Error handling, help screen, tests, polish |

**How to use**:
1. Read the OVERVIEW file for your current stage
2. Copy code exactly as shown
3. Test after creating each file
4. Move to next file when tests pass

---

### Type 3: Pattern Reference Documents

**Purpose**: Deep technical details, edge cases, best practices

**Format**: Comprehensive reference material

| Stage | File | When to Reference |
|-------|------|-------------------|
| Stage 1 | `STAGE1_UI_WIDGETS.md` | Need widget property details, layout clarification |
| Stage 2 | `STAGE2_DATABASE_SCHEMA.md` | Complex query patterns, relationship details |
| Stage 3 | `STAGE3_DATA_PATTERNS.md` | Cache behavior, error handling, NSE symbols |
| Stage 4 | `STAGE4_TRADING_LOGIC.md` | Validation rules, edge cases, commission logic |
| Stage 5 | `STAGE5_DSPY_PATTERNS.md` | Signature design, prompting strategies, fallbacks |
| Stage 6 | `STAGE6_TEST_CASES.md` | Test scenarios, QA checklists, validation scripts |

**How to use**:
1. Start with OVERVIEW file
2. If you encounter an issue or need more detail, check the pattern file
3. Search for specific topics (e.g., "commission", "validation", "caching")
4. Implement patterns from examples shown

---

## 🔍 Finding Information Fast

### Scenario-Based Navigation

#### "I'm starting Stage N"
1. Read: `artha_atoms/stageN_*/STAGEN_OVERVIEW.md`
2. Keep open: Pattern reference file for that stage
3. Reference: `example_code/` folder for library patterns

#### "I hit an error with [library]"
1. Check: Pattern reference file for that stage
2. Look at: `example_code/` working examples
3. Review: Emergency Protocols in `index.md`

#### "I need to understand [specific topic]"
| Topic | Document(s) to Check |
|-------|---------------------|
| Textual widgets | `STAGE1_UI_WIDGETS.md` |
| Database queries | `STAGE2_DATABASE_SCHEMA.md` |
| yfinance API | `STAGE3_DATA_PATTERNS.md` |
| Trade validation | `STAGE4_TRADING_LOGIC.md` |
| DSPy signatures | `STAGE5_DSPY_PATTERNS.md` |
| Testing strategy | `STAGE6_TEST_CASES.md` |
| Overall architecture | `artha_hld.md` |

#### "I'm stuck and don't know what to do"
1. Read: Emergency Protocols section in `index.md`
2. Check: Common errors section in `QWEN_START_HERE.md`
3. Review: Debugging steps in pattern file for current stage

---

## 📖 Reading Order by Stage

### Stage 1 (Hours 0-2)
```
1. QWEN_START_HERE.md (sections relevant to Stage 1)
2. STAGE1_OVERVIEW.md (complete read)
3. STAGE1_UI_WIDGETS.md (reference as needed)
4. example_code/textual/calculator.py (for patterns)
```

### Stage 2 (Hours 2-4)
```
1. STAGE2_OVERVIEW.md (complete read)
2. STAGE2_DATABASE_SCHEMA.md (reference for patterns)
3. Focus on: DAO patterns, async session management
```

### Stage 3 (Hours 4-6)
```
1. STAGE3_OVERVIEW.md (complete read)
2. STAGE3_DATA_PATTERNS.md (reference for edge cases)
3. Focus on: NSE symbol format, caching strategy
```

### Stage 4 (Hours 6-8)
```
1. STAGE4_OVERVIEW.md (complete read)
2. STAGE4_TRADING_LOGIC.md (reference for validation)
3. Focus on: Input validation, commission calculation
```

### Stage 5 (Hours 8-10)
```
1. STAGE5_OVERVIEW.md (complete read)
2. STAGE5_DSPY_PATTERNS.md (reference for signatures)
3. example_code/dspy_toys/dspy_finance_analyst.py (CRITICAL)
4. Focus on: DSPy setup, fallback patterns
```

### Stage 6 (Hours 10-12)
```
1. STAGE6_OVERVIEW.md (complete read)
2. STAGE6_TEST_CASES.md (reference for test scenarios)
3. Focus on: Error handling, validation, testing
```

---

## 🎓 Documentation Best Practices

### For Qwen Coder CLI:

#### DO:
✅ Read OVERVIEW files completely before starting a stage
✅ Copy code exactly as shown in OVERVIEW files
✅ Test after each file creation
✅ Reference pattern files when you need more detail
✅ Check example_code/ for working library patterns
✅ Follow validation steps precisely

#### DON'T:
❌ Skip reading OVERVIEW files
❌ Modify code without understanding it
❌ Continue if tests fail - fix immediately
❌ Ignore error messages
❌ Break previous stage functionality
❌ Leave TODO items or debug code

---

## 🚨 Emergency Documentation

### When Things Go Wrong

#### Error: "I don't understand the architecture"
**Read**: `artha_hld.md` sections 4 and 11

#### Error: "Library not working as expected"
**Check**:
1. `example_code/` for that library
2. Pattern file for current stage
3. Emergency Protocols in `index.md`

#### Error: "Tests failing"
**Reference**:
1. Validation section in OVERVIEW file
2. Test cases in `STAGE6_TEST_CASES.md`
3. Debugging steps in pattern file

#### Error: "Time running out"
**Read**: Emergency Protocols → "Time running out" in `index.md`

---

## 📊 Documentation Completeness

### Coverage by Stage

| Stage | OVERVIEW | Patterns | Examples | Tests | Status |
|-------|----------|----------|----------|-------|--------|
| Stage 1 | ✓ Complete | ✓ Complete | ✓ Textual | ✓ Manual | 100% |
| Stage 2 | ✓ Complete | ✓ Complete | ✓ SQLAlchemy | ✓ Integration | 100% |
| Stage 3 | ✓ Complete | ✓ Complete | ✓ yfinance | ✓ Unit | 100% |
| Stage 4 | ✓ Complete | ✓ Complete | ✓ Trading | ✓ Unit+Integration | 100% |
| Stage 5 | ✓ Complete | ✓ Complete | ✓ DSPy | ✓ Integration | 100% |
| Stage 6 | ✓ Complete | ✓ Complete | ✓ Testing | ✓ Full Suite | 100% |

---

## 🔗 Cross-References

### Documents That Reference Each Other

```
QWEN_START_HERE.md
    ├─→ STAGE1_OVERVIEW.md
    ├─→ index.md
    └─→ DEVELOPMENT_PLAN.md

index.md (Central Hub)
    ├─→ All OVERVIEW files
    ├─→ All Pattern files
    ├─→ DEVELOPMENT_PLAN.md
    └─→ artha_hld.md

Each OVERVIEW file
    ├─→ Corresponding Pattern file
    ├─→ example_code/ files
    └─→ Next stage OVERVIEW

Each Pattern file
    ├─→ Corresponding OVERVIEW file
    └─→ example_code/ files
```

---

## 💡 Tips for Effective Documentation Use

### 1. Two-Monitor Setup (Recommended)
- **Monitor 1**: Code editor
- **Monitor 2**: Documentation (OVERVIEW file open)

### 2. One-Monitor Workflow
- Use split screen
- Keep OVERVIEW file open while coding
- Quick Alt+Tab to reference patterns

### 3. Documentation Reading Strategy
- **First pass**: Skim entire OVERVIEW to understand scope
- **Second pass**: Read code blocks carefully
- **While coding**: Keep document open, copy code exactly

### 4. When to Dig Deeper
Read pattern files when:
- Error occurs that's not explained in OVERVIEW
- Need to understand edge cases
- Want to validate approach
- Troubleshooting failing tests

### 5. Example Code Usage
- **Don't**: Copy example code directly into project
- **Do**: Study patterns and adapt to specifications
- **Remember**: OVERVIEW files have exact code to use

---

## 📝 Documentation Maintenance

### For Human Reviewers

This documentation is designed to be:
- **Complete**: Every aspect of implementation is covered
- **Precise**: Exact code and specifications provided
- **Layered**: Quick-start (OVERVIEW) + Deep-dive (Patterns)
- **Referenced**: Cross-linked for easy navigation

### Document Update Protocol

If code changes, update in this order:
1. OVERVIEW file (primary source of truth)
2. Pattern file (if edge cases or patterns change)
3. index.md (if structure changes)
4. artha_hld.md (if architecture changes)

---

## 🎯 Success Metrics

### You're using documentation correctly if:
- [ ] You read OVERVIEW before writing code
- [ ] You copy code exactly from OVERVIEW
- [ ] You test after each file
- [ ] You reference patterns when stuck
- [ ] Previous stages keep working
- [ ] You complete stages on schedule

### You need to adjust if:
- [ ] Writing code before reading OVERVIEW
- [ ] Skipping validation steps
- [ ] Tests failing and continuing anyway
- [ ] Not referencing example code
- [ ] Breaking previous functionality
- [ ] Falling behind schedule

---

## 🚀 Quick Reference Card

### Core Documents (Bookmark These)

| Purpose | Document | Shortcut |
|---------|----------|----------|
| **Start here** | QWEN_START_HERE.md | `docs/QWEN_START_HERE.md` |
| **Navigation** | index.md | `docs/index.md` |
| **Current stage** | STAGE{N}_OVERVIEW.md | `docs/artha_atoms/stage{N}_*/` |
| **Deep dive** | Stage pattern file | Same folder as OVERVIEW |
| **Examples** | example_code/ | `example_code/` |
| **Architecture** | artha_hld.md | `docs/artha_hld.md` |

### Essential Commands

```bash
# View documentation
cat docs/QWEN_START_HERE.md
cat docs/artha_atoms/stage1_tui/STAGE1_OVERVIEW.md

# Test after changes
python -m src.main

# Run tests
pytest tests/

# Check dependencies
pip list | grep -E "textual|dspy|sqlalchemy|yfinance"
```

---

## 📞 Getting Help

### Problem-Solving Path

```
Encounter Issue
     ↓
Check OVERVIEW file
     ↓
     ├─ Found solution → Continue
     └─ Not found → Check Pattern file
           ↓
           ├─ Found solution → Continue
           └─ Not found → Check example_code/
                 ↓
                 ├─ Found solution → Continue
                 └─ Not found → Check Emergency Protocols (index.md)
```

---

## 🎉 Conclusion

You now have:
- **Complete specifications** for all 6 stages
- **Detailed patterns** for complex topics
- **Working examples** to reference
- **Clear navigation** to find information fast

**Remember**:
- Start with OVERVIEW files
- Reference pattern files when needed
- Copy code exactly
- Test constantly
- Keep previous stages working

**You have everything you need to succeed! 🚀**

---

*This is a living document. As you progress, refer back to this guide to stay oriented.*

*Good luck with the implementation!*

# Stage 5: AI Coach Integration

**Duration**: 2 hours (Hours 8-10)
**Status**: AI Features
**Depends On**: Stage 4 complete and working

---

## Objective

Integrate DSPy + Ollama for AI coaching:
- Trade feedback system
- Portfolio analysis
- Question answering
- Graceful fallbacks

---

## Success Criteria

- [ ] DSPy configured with Ollama
- [ ] Trade feedback after each trade
- [ ] Can ask coach questions with 'c' key
- [ ] Feedback displays in UI
- [ ] Works offline with fallback messages
- [ ] No crashes if Ollama unavailable

---

## Reference Materials

**CRITICAL**: Use example_code/dspy_toys/dspy_finance_analyst.py as primary reference
**Also see**: example_code/dspy_toys/dspy_text_RPG_game.py for DSPy Signatures

---

## Files to Create

### 1. `src/coach/__init__.py`
```python
"""AI Coach package"""
from src.coach.manager import CoachManager

__all__ = ["CoachManager"]
```

### 2. `src/coach/dspy_setup.py`
```python
"""DSPy configuration for Ollama"""
import dspy

def setup_dspy(model: str = "qwen3:8b"):
    """Configure DSPy with Ollama"""
    try:
        lm = dspy.LM(
            f'ollama_chat/{model}',
            api_base='http://localhost:11434',
            api_key=''
        )
        dspy.configure(lm=lm)
        return True
    except Exception as e:
        print(f"Failed to setup DSPy: {e}")
        return False
```

### 3. `src/coach/signatures.py`
```python
"""DSPy signatures for coaching"""
import dspy

class TradeFeedbackSignature(dspy.Signature):
    """Generate educational feedback for a trade."""
    action: str = dspy.InputField(desc="BUY or SELL")
    symbol: str = dspy.InputField(desc="Stock symbol")
    quantity: int = dspy.InputField(desc="Number of shares")
    price: float = dspy.InputField(desc="Execution price")
    portfolio_value: float = dspy.InputField(desc="Total portfolio value")

    feedback: str = dspy.OutputField(
        desc="2-3 concise educational bullets about this trade (max 60 chars each)"
    )

class PortfolioReviewSignature(dspy.Signature):
    """Analyze portfolio and provide insights."""
    num_positions: int = dspy.InputField(desc="Number of positions")
    total_value: float = dspy.InputField(desc="Total portfolio value")
    cash_pct: float = dspy.InputField(desc="Percentage in cash")
    total_pnl_pct: float = dspy.InputField(desc="Total P&L percentage")

    insights: str = dspy.OutputField(
        desc="2-3 brief insights about portfolio diversification and risk"
    )

class QuestionAnswerSignature(dspy.Signature):
    """Answer investing questions."""
    question: str = dspy.InputField(desc="Student's question about investing")

    answer: str = dspy.OutputField(
        desc="Clear, educational answer suitable for teenagers"
    )
```

### 4. `src/coach/manager.py`
```python
"""Coach manager with DSPy"""
import dspy
from src.coach.signatures import (
    TradeFeedbackSignature,
    PortfolioReviewSignature,
    QuestionAnswerSignature
)
from src.coach.dspy_setup import setup_dspy

class CoachManager:
    """Manages AI coaching interactions"""

    def __init__(self):
        self.enabled = setup_dspy()

        if self.enabled:
            try:
                self.trade_feedback = dspy.ChainOfThought(TradeFeedbackSignature)
                self.portfolio_review = dspy.ChainOfThought(PortfolioReviewSignature)
                self.qa_module = dspy.ChainOfThought(QuestionAnswerSignature)
            except Exception as e:
                print(f"Error initializing DSPy modules: {e}")
                self.enabled = False

    def get_trade_feedback(
        self,
        action: str,
        symbol: str,
        quantity: int,
        price: float,
        portfolio_value: float
    ) -> str:
        """Get feedback on a trade"""
        if not self.enabled:
            return self._fallback_trade_feedback(action, symbol, quantity)

        try:
            result = self.trade_feedback(
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                portfolio_value=portfolio_value
            )
            return result.feedback
        except Exception as e:
            print(f"Coach error: {e}")
            return self._fallback_trade_feedback(action, symbol, quantity)

    def get_portfolio_insights(
        self,
        num_positions: int,
        total_value: float,
        cash_pct: float,
        total_pnl_pct: float
    ) -> str:
        """Get portfolio analysis"""
        if not self.enabled:
            return self._fallback_portfolio_insights(num_positions)

        try:
            result = self.portfolio_review(
                num_positions=num_positions,
                total_value=total_value,
                cash_pct=cash_pct,
                total_pnl_pct=total_pnl_pct
            )
            return result.insights
        except Exception as e:
            print(f"Coach error: {e}")
            return self._fallback_portfolio_insights(num_positions)

    def answer_question(self, question: str) -> str:
        """Answer a question"""
        if not self.enabled:
            return "AI coach is offline. Try checking your Ollama setup!"

        try:
            result = self.qa_module(question=question)
            return result.answer
        except Exception as e:
            print(f"Coach error: {e}")
            return "Sorry, I couldn't process that question right now."

    def _fallback_trade_feedback(
        self, action: str, symbol: str, quantity: int
    ) -> str:
        """Fallback when AI unavailable"""
        if action == "BUY":
            return f"• Bought {quantity} shares of {symbol}\n• Monitor performance daily\n• Consider diversification"
        else:
            return f"• Sold {quantity} shares of {symbol}\n• Profit-taking is wise\n• Reinvest or hold cash"

    def _fallback_portfolio_insights(self, num_positions: int) -> str:
        """Fallback portfolio insights"""
        if num_positions == 0:
            return "• Portfolio empty - time to invest!\n• Start with 3-5 different stocks\n• Diversify across sectors"
        elif num_positions < 3:
            return "• Good start! Consider adding more stocks\n• Diversification reduces risk\n• Aim for 5-7 positions"
        else:
            return f"• {num_positions} positions - good diversification\n• Monitor each stock regularly\n• Rebalance if needed"
```

### 5. UPDATE `src/tui/app.py`
```python
# Add import
from src.coach import CoachManager

# In __init__:
    def __init__(self):
        super().__init__()
        self.market_data = MarketDataLoader()
        self.coach = CoachManager()  # NEW
        self.game_state = self._create_mock_game()
```

### 6. UPDATE `src/tui/screens/main_screen.py`
```python
# Update BINDINGS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "menu", "Menu"),
        ("s", "save", "Save"),
        ("t", "trade", "Trade"),
        ("space", "advance_day", "Next Day"),
        ("c", "coach", "Coach"),  # NEW
    ]

# Update _execute_trade to get feedback:
    def _execute_trade(self, trade_data: dict) -> None:
        """Execute the trade"""
        symbol = trade_data["symbol"]
        action = trade_data["action"]
        quantity = trade_data["quantity"]

        # Get current price
        price = self.app.market_data.get_current_price(symbol)

        if price <= 0:
            self.app.notify("Could not get price for stock", severity="error")
            return

        # Execute trade
        if action == "BUY":
            result = TradeExecutor.execute_buy(
                self.game_state.portfolio,
                symbol,
                quantity,
                price
            )
        else:
            result = TradeExecutor.execute_sell(
                self.game_state.portfolio,
                symbol,
                quantity,
                price
            )

        # Show result
        if result.success:
            self.app.notify(result.message, severity="information")
            self._refresh_display()

            # Get AI feedback
            feedback = self.app.coach.get_trade_feedback(
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                portfolio_value=self.game_state.portfolio.total_value
            )
            self.app.notify(f"Coach: {feedback}", timeout=10)

            # Auto-save after trade
            import asyncio
            asyncio.create_task(self.app._save_current_game())
        else:
            self.app.notify(result.message, severity="error")

# Add coach action:
    def action_coach(self) -> None:
        """Get portfolio insights from coach"""
        portfolio = self.game_state.portfolio
        cash_pct = (portfolio.cash / portfolio.total_value) * 100 if portfolio.total_value > 0 else 100
        total_pnl_pct = (portfolio.total_pnl / portfolio.invested) * 100 if portfolio.invested > 0 else 0

        insights = self.app.coach.get_portfolio_insights(
            num_positions=len(portfolio.positions),
            total_value=portfolio.total_value,
            cash_pct=cash_pct,
            total_pnl_pct=total_pnl_pct
        )

        self.app.notify(f"Coach Insights:\n{insights}", timeout=15)
```

---

## Qwen Coder Prompt for Stage 5

```
CONTEXT:
- Stage 4 working with full trading
- Now integrating DSPy + Ollama for AI coaching
- MUST follow example_code/dspy_toys/dspy_finance_analyst.py pattern
- Use graceful fallbacks if Ollama unavailable

TASK:
1. Create src/coach/__init__.py
2. Create src/coach/dspy_setup.py (DSPy configuration)
3. Create src/coach/signatures.py (DSPy Signatures - copy pattern from examples!)
4. Create src/coach/manager.py (CoachManager with fallbacks)
5. Update src/tui/app.py (initialize CoachManager)
6. Update src/tui/screens/main_screen.py (add coach binding, get feedback after trades)

CRITICAL RULES:
- Copy DSPy setup from example_code/dspy_toys/dspy_finance_analyst.py EXACTLY
- Use format: dspy.LM('ollama_chat/qwen3:8b', api_base='http://localhost:11434', api_key='')
- Always have fallback messages if DSPy fails
- Don't crash if Ollama not running
- Keep feedback concise (2-3 bullets, 60 chars max each)
- Use dspy.ChainOfThought for predictors

VALIDATION:
1. Ensure Ollama is running: ollama list
2. Run: python -m src.main
3. Start game, execute trade
4. Verify feedback appears after trade
5. Press 'c' for coach insights
6. Verify insights display
7. Stop Ollama: sudo systemctl stop ollama
8. Execute another trade
9. Verify fallback feedback still works
10. No crashes even with Ollama offline

EXPECTED OUTPUT:
- AI feedback after each trade
- Coach insights on demand
- Fallback messages work offline
- No crashes or hangs
- Feedback is educational and concise
```

---

## Validation Checklist

- [ ] Ollama check on startup
- [ ] Trade feedback appears
- [ ] Coach insights work ('c' key)
- [ ] Fallback messages if Ollama offline
- [ ] No crashes without Ollama
- [ ] Feedback is concise and helpful
- [ ] DSPy configured correctly

---

## Next: Stage 6 final polish

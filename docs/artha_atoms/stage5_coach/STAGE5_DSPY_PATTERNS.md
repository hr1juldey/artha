# Stage 5: DSPy Patterns & AI Coach

**Supplement to**: STAGE5_OVERVIEW.md
**Purpose**: Detailed DSPy signature design, prompting strategies, and Ollama integration patterns

---

## DSPy Architecture

```
┌──────────────────────────────────────────────────────┐
│           DSPy + Ollama Architecture                  │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────┐                                │
│  │  Application    │                                │
│  │  (Artha TUI)    │                                │
│  └────────┬────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────┐                                │
│  │  CoachManager   │                                │
│  │  - High-level   │                                │
│  │    interface    │                                │
│  └────────┬────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────┐                                │
│  │  DSPy Modules   │                                │
│  │  - ChainOfThought│                               │
│  │  - Predictors    │                               │
│  └────────┬────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────┐                                │
│  │  DSPy           │                                │
│  │  Signatures     │                                │
│  │  - Input fields │                                │
│  │  - Output fields│                                │
│  └────────┬────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────┐                                │
│  │  DSPy.LM        │                                │
│  │  (ollama_chat)  │                                │
│  └────────┬────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────┐                                │
│  │  Ollama API     │                                │
│  │  (localhost:    │                                │
│  │   11434)        │                                │
│  └────────┬────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────┐                                │
│  │  qwen3:8b       │                                │
│  │  (LLM Model)    │                                │
│  └─────────────────┘                                │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## DSPy Setup Patterns

### Standard Ollama Configuration

```python
"""DSPy configuration for Ollama"""
import dspy
from typing import Optional

def setup_dspy_ollama(
    model: str = "qwen3:8b",
    api_base: str = "http://localhost:11434",
    timeout: int = 30
) -> tuple[bool, Optional[str]]:
    """Configure DSPy with Ollama

    Args:
        model: Ollama model name (e.g., "qwen3:8b", "llama2", "mistral")
        api_base: Ollama API endpoint
        timeout: Request timeout in seconds

    Returns:
        (success, error_message)

    Example:
        >>> success, error = setup_dspy_ollama()
        >>> if success:
        ...     # DSPy is configured
        ...     pass
    """
    try:
        # Create LM instance
        lm = dspy.LM(
            f'ollama_chat/{model}',
            api_base=api_base,
            api_key='',  # Ollama doesn't require API key
            timeout=timeout
        )

        # Configure DSPy globally
        dspy.configure(lm=lm)

        # Test connection with simple prompt
        test_signature = dspy.Signature("question -> answer")
        test_module = dspy.ChainOfThought(test_signature)

        try:
            result = test_module(question="What is 2+2?")
            if result.answer:
                return True, None
        except Exception as e:
            return False, f"Connection test failed: {e}"

        return True, None

    except Exception as e:
        return False, f"Setup failed: {e}"
```

### Health Check Pattern

```python
def check_ollama_availability(
    api_base: str = "http://localhost:11434"
) -> tuple[bool, list[str]]:
    """Check if Ollama is running and get available models

    Args:
        api_base: Ollama API endpoint

    Returns:
        (is_available, list_of_models)

    Example:
        >>> available, models = check_ollama_availability()
        >>> if available:
        ...     print(f"Available models: {models}")
    """
    import requests

    try:
        # Try to get model list
        response = requests.get(
            f"{api_base}/api/tags",
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            return True, models

        return False, []

    except requests.exceptions.ConnectionError:
        return False, []
    except Exception as e:
        print(f"Health check error: {e}")
        return False, []
```

---

## DSPy Signature Design

### Signature Anatomy

```python
import dspy

class ExampleSignature(dspy.Signature):
    """Signature docstring: Describes the task for the LLM

    This docstring is CRITICAL - it tells the LLM what to do.
    Be clear, concise, and specific.
    """

    # Input fields: What the LLM receives
    input_field: str = dspy.InputField(
        desc="Description of this input (helps LLM understand context)"
    )

    # Output fields: What the LLM should produce
    output_field: str = dspy.OutputField(
        desc="Description of expected output format and constraints"
    )
```

### Investment Coach Signatures

#### 1. Trade Feedback Signature

```python
import dspy

class TradeFeedbackSignature(dspy.Signature):
    """Provide concise educational feedback on a stock trade for a teenage investor.

    Focus on:
    - Whether the trade aligns with diversification principles
    - Risk management considerations
    - Learning opportunity from this specific trade

    Keep feedback to 2-3 bullets, max 60 characters each.
    Use simple language suitable for beginners.
    """

    # Trade details (inputs)
    action: str = dspy.InputField(
        desc="Trade action: BUY or SELL"
    )

    symbol: str = dspy.InputField(
        desc="Stock symbol (e.g., RELIANCE, TCS)"
    )

    quantity: int = dspy.InputField(
        desc="Number of shares traded"
    )

    price: float = dspy.InputField(
        desc="Execution price per share in rupees"
    )

    # Portfolio context (inputs)
    portfolio_value: float = dspy.InputField(
        desc="Total portfolio value in rupees"
    )

    cash_remaining: float = dspy.InputField(
        desc="Cash remaining after trade in rupees"
    )

    num_positions: int = dspy.InputField(
        desc="Total number of different stocks owned"
    )

    # Output
    feedback: str = dspy.OutputField(
        desc="2-3 concise educational bullet points, each max 60 chars. Focus on portfolio implications, risk, and learning."
    )

# Usage pattern
def get_trade_feedback_example():
    """Example of using TradeFeedbackSignature"""

    # Create predictor
    feedback_module = dspy.ChainOfThought(TradeFeedbackSignature)

    # Execute
    result = feedback_module(
        action="BUY",
        symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        portfolio_value=1000000.0,
        cash_remaining=975000.0,
        num_positions=1
    )

    print(result.feedback)
    # Output example:
    # • Good first position! Aim for 5-7 stocks for diversification
    # • This is 2.5% of portfolio - reasonable position sizing
    # • Consider adding stocks from different sectors
```

#### 2. Portfolio Review Signature

```python
class PortfolioReviewSignature(dspy.Signature):
    """Analyze an investment portfolio and provide strategic insights.

    Evaluate:
    - Diversification level (number of positions)
    - Cash allocation (% in cash vs invested)
    - Overall performance (P&L percentage)
    - Risk profile

    Provide 2-3 actionable insights for improvement.
    Use beginner-friendly language.
    """

    # Portfolio metrics (inputs)
    num_positions: int = dspy.InputField(
        desc="Number of different stocks currently owned"
    )

    total_value: float = dspy.InputField(
        desc="Total portfolio value in rupees (cash + holdings)"
    )

    cash_percentage: float = dspy.InputField(
        desc="Percentage of portfolio in cash (0-100)"
    )

    total_pnl_percentage: float = dspy.InputField(
        desc="Total profit/loss percentage since start"
    )

    # Output
    insights: str = dspy.OutputField(
        desc="2-3 strategic insights about portfolio health, diversification, and next steps. Each insight should be actionable and educational."
    )

# Usage pattern
def get_portfolio_review_example():
    """Example of using PortfolioReviewSignature"""

    review_module = dspy.ChainOfThought(PortfolioReviewSignature)

    result = review_module(
        num_positions=3,
        total_value=1050000.0,
        cash_percentage=15.0,
        total_pnl_percentage=5.0
    )

    print(result.insights)
    # Output example:
    # • Good diversification with 3 stocks! Consider adding 2-3 more
    # • 15% cash allocation is healthy - keeps options open
    # • 5% return is solid! Monitor each position's performance
```

#### 3. Question-Answer Signature

```python
class InvestingQuestionSignature(dspy.Signature):
    """Answer investment-related questions for teenage beginners.

    Provide:
    - Clear, simple explanations
    - Real-world examples
    - Practical takeaways

    Avoid jargon. If technical terms are necessary, explain them.
    Keep answer to 3-4 sentences maximum.
    """

    # Input
    question: str = dspy.InputField(
        desc="Student's question about investing, stocks, or portfolio management"
    )

    # Context (optional but helpful)
    user_portfolio_size: int = dspy.InputField(
        desc="Number of stocks user currently owns (for context)"
    )

    # Output
    answer: str = dspy.OutputField(
        desc="Clear, educational answer suitable for teenagers. 3-4 sentences max. Include practical example if helpful."
    )

# Usage pattern
def answer_investing_question_example():
    """Example of using InvestingQuestionSignature"""

    qa_module = dspy.ChainOfThought(InvestingQuestionSignature)

    result = qa_module(
        question="What is diversification?",
        user_portfolio_size=2
    )

    print(result.answer)
    # Output example:
    # Diversification means spreading your money across different stocks
    # instead of putting everything in one place. Think of it like not
    # carrying all your eggs in one basket - if one drops, you don't lose
    # everything. You currently have 2 stocks, which is a start. Aim for
    # 5-7 different stocks across various sectors for good diversification.
```

#### 4. Trade Strategy Signature

```python
class TradeStrategySignature(dspy.Signature):
    """Suggest whether to buy, sell, or hold based on portfolio analysis.

    Consider:
    - Current portfolio composition
    - Cash availability
    - Diversification needs
    - Risk management

    Provide specific, actionable recommendation with reasoning.
    Educational tone for beginners.
    """

    # Portfolio state (inputs)
    current_positions: str = dspy.InputField(
        desc="List of current stocks with quantities (e.g., 'RELIANCE:10, TCS:5')"
    )

    cash_available: float = dspy.InputField(
        desc="Available cash in rupees"
    )

    days_remaining: int = dspy.InputField(
        desc="Days remaining in simulation"
    )

    # Output
    recommendation: str = dspy.OutputField(
        desc="Specific recommendation: what to BUY/SELL/HOLD and why. Include reasoning for educational value."
    )

# Usage pattern
def get_strategy_recommendation_example():
    """Example of using TradeStrategySignature"""

    strategy_module = dspy.ChainOfThought(TradeStrategySignature)

    result = strategy_module(
        current_positions="RELIANCE:10, TCS:5",
        cash_available=500000.0,
        days_remaining=20
    )

    print(result.recommendation)
    # Output example:
    # Consider BUYING a banking stock like HDFCBANK to diversify sectors.
    # You currently have energy (RELIANCE) and IT (TCS), but no financial
    # sector exposure. With ₹5L cash and 20 days left, you have time to
    # build a more balanced portfolio. Aim for 5-7 positions total.
```

---

## Predictor Patterns

### ChainOfThought vs Predict

```python
import dspy

# ChainOfThought: Better for complex reasoning
# Generates intermediate reasoning steps
cot_module = dspy.ChainOfThought(TradeFeedbackSignature)

# Predict: Faster, direct answer
# Good for simple classifications
predict_module = dspy.Predict(TradeFeedbackSignature)

# Recommendation: Use ChainOfThought for Artha
# It produces better quality, more thoughtful responses
```

### Error Handling Patterns

```python
def safe_dspy_call(
    module: dspy.Module,
    fallback_message: str,
    **kwargs
) -> str:
    """Safely call DSPy module with fallback

    Args:
        module: DSPy module to call
        fallback_message: Message to return if call fails
        **kwargs: Arguments to pass to module

    Returns:
        Module output or fallback message
    """
    try:
        result = module(**kwargs)

        # Check if result has expected attribute
        if hasattr(result, 'feedback'):
            return result.feedback
        elif hasattr(result, 'insights'):
            return result.insights
        elif hasattr(result, 'answer'):
            return result.answer
        else:
            # Generic attribute access
            for attr in dir(result):
                if not attr.startswith('_'):
                    return getattr(result, attr)

        return fallback_message

    except Exception as e:
        print(f"DSPy call failed: {e}")
        return fallback_message
```

---

## Coach Manager Implementation

### Complete CoachManager with Best Practices

```python
"""AI Coach Manager with DSPy"""
import dspy
from typing import Optional
from src.coach.signatures import (
    TradeFeedbackSignature,
    PortfolioReviewSignature,
    InvestingQuestionSignature,
    TradeStrategySignature
)
from src.coach.dspy_setup import setup_dspy_ollama, check_ollama_availability

class CoachManager:
    """Manages AI coaching interactions with graceful fallbacks"""

    def __init__(self, model: str = "qwen3:8b"):
        """Initialize coach manager

        Args:
            model: Ollama model name
        """
        self.model = model
        self.enabled = False
        self.modules = {}

        # Check Ollama availability first
        available, models = check_ollama_availability()

        if not available:
            print("⚠️  Ollama not running - using fallback messages")
            return

        if model not in models:
            print(f"⚠️  Model {model} not found. Available: {models}")
            print("    Using fallback messages")
            return

        # Setup DSPy
        success, error = setup_dspy_ollama(model)

        if not success:
            print(f"⚠️  DSPy setup failed: {error}")
            print("    Using fallback messages")
            return

        # Initialize modules
        try:
            self.modules = {
                'trade_feedback': dspy.ChainOfThought(TradeFeedbackSignature),
                'portfolio_review': dspy.ChainOfThought(PortfolioReviewSignature),
                'qa': dspy.ChainOfThought(InvestingQuestionSignature),
                'strategy': dspy.ChainOfThought(TradeStrategySignature),
            }

            self.enabled = True
            print(f"✓ AI Coach initialized with {model}")

        except Exception as e:
            print(f"⚠️  Module initialization failed: {e}")
            print("    Using fallback messages")

    def get_trade_feedback(
        self,
        action: str,
        symbol: str,
        quantity: int,
        price: float,
        portfolio_value: float,
        cash_remaining: float,
        num_positions: int
    ) -> str:
        """Get feedback on a trade

        Args:
            action: BUY or SELL
            symbol: Stock symbol
            quantity: Shares traded
            price: Price per share
            portfolio_value: Total portfolio value
            cash_remaining: Cash after trade
            num_positions: Number of different stocks owned

        Returns:
            Feedback message (AI or fallback)
        """
        if not self.enabled:
            return self._fallback_trade_feedback(action, symbol, quantity)

        try:
            result = self.modules['trade_feedback'](
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                portfolio_value=portfolio_value,
                cash_remaining=cash_remaining,
                num_positions=num_positions
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
        """Get portfolio analysis insights

        Args:
            num_positions: Number of positions
            total_value: Total portfolio value
            cash_pct: Cash percentage
            total_pnl_pct: Total P&L percentage

        Returns:
            Insights message (AI or fallback)
        """
        if not self.enabled:
            return self._fallback_portfolio_insights(num_positions)

        try:
            result = self.modules['portfolio_review'](
                num_positions=num_positions,
                total_value=total_value,
                cash_percentage=cash_pct,
                total_pnl_percentage=total_pnl_pct
            )

            return result.insights

        except Exception as e:
            print(f"Coach error: {e}")
            return self._fallback_portfolio_insights(num_positions)

    def answer_question(
        self,
        question: str,
        user_portfolio_size: int = 0
    ) -> str:
        """Answer investing question

        Args:
            question: User's question
            user_portfolio_size: Number of stocks owned (for context)

        Returns:
            Answer (AI or fallback)
        """
        if not self.enabled:
            return "AI coach is offline. Start Ollama to get answers!"

        try:
            result = self.modules['qa'](
                question=question,
                user_portfolio_size=user_portfolio_size
            )

            return result.answer

        except Exception as e:
            print(f"Coach error: {e}")
            return "Sorry, I couldn't process that question. Try rephrasing?"

    def get_strategy_recommendation(
        self,
        current_positions: str,
        cash_available: float,
        days_remaining: int
    ) -> str:
        """Get strategic recommendation

        Args:
            current_positions: String of positions (e.g., "RELIANCE:10, TCS:5")
            cash_available: Available cash
            days_remaining: Days left in simulation

        Returns:
            Recommendation (AI or fallback)
        """
        if not self.enabled:
            return "Build a diversified portfolio with 5-7 different stocks."

        try:
            result = self.modules['strategy'](
                current_positions=current_positions,
                cash_available=cash_available,
                days_remaining=days_remaining
            )

            return result.recommendation

        except Exception as e:
            print(f"Coach error: {e}")
            return "Focus on diversification across different sectors."

    # ============ FALLBACK MESSAGES ============

    def _fallback_trade_feedback(
        self,
        action: str,
        symbol: str,
        quantity: int
    ) -> str:
        """Fallback feedback when AI unavailable"""
        if action == "BUY":
            return f"• Bought {quantity} shares of {symbol}\n• Monitor daily performance\n• Consider diversification"
        else:
            return f"• Sold {quantity} shares of {symbol}\n• Profit-taking is wise\n• Reinvest or hold cash"

    def _fallback_portfolio_insights(self, num_positions: int) -> str:
        """Fallback insights when AI unavailable"""
        if num_positions == 0:
            return "• Portfolio empty - time to invest!\n• Start with 3-5 different stocks\n• Diversify across sectors"
        elif num_positions < 3:
            return "• Good start! Add more stocks\n• Diversification reduces risk\n• Aim for 5-7 positions"
        elif num_positions < 7:
            return f"• {num_positions} positions - good!\n• Monitor each stock\n• Rebalance if needed"
        else:
            return f"• {num_positions} positions - well diversified!\n• Don't over-diversify\n• Quality over quantity"
```

---

## Prompting Best Practices

### 1. Be Specific in Descriptions

```python
# Bad - vague description
feedback: str = dspy.OutputField(desc="Give feedback")

# Good - specific expectations
feedback: str = dspy.OutputField(
    desc="2-3 concise educational bullet points, each max 60 chars. Focus on portfolio implications, risk, and learning."
)
```

### 2. Provide Context

```python
# Bad - minimal context
class BadSignature(dspy.Signature):
    """Answer question"""
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()

# Good - rich context
class GoodSignature(dspy.Signature):
    """Answer investment question for teenage beginner.
    Use simple language, avoid jargon, include examples."""

    question: str = dspy.InputField(desc="Student's investment question")
    portfolio_size: int = dspy.InputField(desc="Number of stocks owned")
    answer: str = dspy.OutputField(desc="Clear 3-4 sentence answer with example")
```

### 3. Constrain Output Format

```python
# Helps ensure consistent output
feedback: str = dspy.OutputField(
    desc="Format: bullet points with • character, max 60 chars each, 2-3 bullets total"
)
```

### 4. Use Examples in Docstring

```python
class ExampleRichSignature(dspy.Signature):
    """Provide trade feedback.

    Example good feedback:
    • Good diversification - you now own 3 different stocks
    • Position size is 2.5% of portfolio - reasonable
    • Consider adding a banking stock next

    Focus on educational value for beginners.
    """
    # ... fields ...
```

---

## Testing Strategies

### Unit Tests for Coach

```python
import pytest
from src.coach.manager import CoachManager

def test_coach_initialization():
    """Test coach initializes"""
    coach = CoachManager()
    # Should not crash even if Ollama offline
    assert coach is not None

def test_trade_feedback_fallback():
    """Test fallback works when Ollama offline"""
    coach = CoachManager()
    coach.enabled = False  # Force fallback

    feedback = coach.get_trade_feedback(
        action="BUY",
        symbol="TEST",
        quantity=10,
        price=100.0,
        portfolio_value=100000.0,
        cash_remaining=99000.0,
        num_positions=1
    )

    assert feedback is not None
    assert len(feedback) > 0
    assert "TEST" in feedback or "Bought" in feedback

@pytest.mark.skipif(
    not check_ollama_availability()[0],
    reason="Ollama not available"
)
def test_trade_feedback_with_ollama():
    """Test real AI feedback (only runs if Ollama available)"""
    coach = CoachManager()

    if not coach.enabled:
        pytest.skip("Ollama not configured")

    feedback = coach.get_trade_feedback(
        action="BUY",
        symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        portfolio_value=1000000.0,
        cash_remaining=975000.0,
        num_positions=1
    )

    assert feedback is not None
    assert len(feedback) > 20  # Should be substantial
```

### Integration Test Pattern

```python
def test_coach_in_trading_flow():
    """Test coach integrated with trading"""
    from src.engine.trade_executor import TradeExecutor
    from src.models import Portfolio
    from src.coach.manager import CoachManager

    # Setup
    portfolio = Portfolio(cash=1000000.0)
    coach = CoachManager()

    # Execute trade
    result = TradeExecutor.execute_buy(
        portfolio, "RELIANCE", 10, 2500.0
    )

    assert result.success

    # Get feedback
    feedback = coach.get_trade_feedback(
        action="BUY",
        symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        portfolio_value=portfolio.total_value,
        cash_remaining=portfolio.cash,
        num_positions=len(portfolio.positions)
    )

    assert feedback is not None
    print(f"Coach feedback: {feedback}")
```

---

## Performance Optimization

### Caching Responses

```python
from functools import lru_cache

class CachedCoachManager(CoachManager):
    """Coach with response caching for repeated queries"""

    @lru_cache(maxsize=100)
    def _cached_qa(self, question: str, portfolio_size: int) -> str:
        """Cached Q&A for common questions"""
        return super().answer_question(question, portfolio_size)

    def answer_question(self, question: str, user_portfolio_size: int = 0) -> str:
        """Answer with caching"""
        return self._cached_qa(question, user_portfolio_size)
```

### Async Pattern (Optional)

```python
import asyncio

async def async_coach_feedback(coach, **kwargs):
    """Get feedback asynchronously (doesn't block UI)"""

    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    feedback = await loop.run_in_executor(
        None,
        lambda: coach.get_trade_feedback(**kwargs)
    )

    return feedback

# Usage in TUI
async def handle_trade_with_async_feedback():
    feedback = await async_coach_feedback(
        coach,
        action="BUY",
        symbol="RELIANCE",
        # ... other args ...
    )

    app.notify(feedback)
```

---

## Common Issues and Solutions

### Issue 1: Ollama Not Running

**Symptom**: Coach always uses fallback messages

**Solution**:
```bash
# Check if Ollama running
curl http://localhost:11434/api/tags

# If not running
ollama serve

# If model not pulled
ollama pull qwen3:8b
```

### Issue 2: Slow Responses

**Symptom**: UI freezes during coach calls

**Solution**: Use timeouts and async patterns
```python
# Add timeout to setup
setup_dspy_ollama(model="qwen3:8b", timeout=10)

# Or use async pattern shown above
```

### Issue 3: Poor Quality Responses

**Symptom**: Generic or unhelpful feedback

**Solution**: Improve signature descriptions
```python
# Add more specific constraints
feedback: str = dspy.OutputField(
    desc="""Provide exactly 2-3 bullet points.
    Each bullet must:
    - Start with • character
    - Be max 60 characters
    - Focus on one specific insight
    - Be actionable and educational

    Good example:
    • Good diversification - 3 stocks in different sectors
    • Position size is 2.5% - reasonable and safe
    • Consider adding a financial sector stock next"""
)
```

### Issue 4: Unexpected Output Format

**Symptom**: Output doesn't match expected format

**Solution**: Add format validation
```python
def validate_and_fix_feedback(feedback: str) -> str:
    """Ensure feedback is properly formatted"""
    lines = feedback.split('\n')

    # Ensure bullet points
    formatted = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('•'):
            line = f"• {line}"
        if line:
            formatted.append(line)

    # Limit to 3 bullets
    return '\n'.join(formatted[:3])
```

---

## Validation Checklist

### DSPy Setup
- [ ] Ollama installed and running
- [ ] qwen3:8b model pulled
- [ ] DSPy configured correctly
- [ ] Connection test passes
- [ ] Fallback works when Ollama offline

### Signatures
- [ ] Clear docstrings
- [ ] Specific field descriptions
- [ ] Appropriate input context
- [ ] Output format constraints

### Coach Manager
- [ ] Initializes without errors
- [ ] Handles Ollama offline gracefully
- [ ] Returns helpful fallback messages
- [ ] AI feedback is educational
- [ ] Responses are concise

### Integration
- [ ] Works with trading engine
- [ ] Feedback appears after trades
- [ ] Portfolio insights available
- [ ] Q&A system functional
- [ ] No UI blocking

---

## Quick Reference

### Import Statements

```python
import dspy
from src.coach.manager import CoachManager
from src.coach.signatures import TradeFeedbackSignature
```

### Common Code Snippets

```python
# Initialize coach
coach = CoachManager()

# Get trade feedback
feedback = coach.get_trade_feedback(
    action="BUY",
    symbol="RELIANCE",
    quantity=10,
    price=2500.0,
    portfolio_value=1000000.0,
    cash_remaining=975000.0,
    num_positions=1
)

# Get portfolio insights
insights = coach.get_portfolio_insights(
    num_positions=3,
    total_value=1050000.0,
    cash_pct=15.0,
    total_pnl_pct=5.0
)

# Answer question
answer = coach.answer_question(
    question="What is diversification?",
    user_portfolio_size=2
)
```

---

This document provides all DSPy patterns needed for Stage 5 implementation.

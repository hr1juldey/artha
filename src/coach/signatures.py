"""DSPy signatures for coaching"""
import dspy

class TradeFeedbackSignature(dspy.Signature):
    """Generate educational feedback for a trade.

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

    # Portfolio context (inputs) - THESE ARE MISSING!
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
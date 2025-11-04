"""Coach manager with DSPy"""
import dspy
from src.coach.signatures import (
    TradeFeedbackSignature,
    PortfolioReviewSignature,
    InvestingQuestionSignature
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
                self.qa_module = dspy.ChainOfThought(InvestingQuestionSignature)
            except Exception as e:
                print(f"Error initializing DSPy modules: {e}")
                self.enabled = False

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
        """Get feedback on a trade"""
        if not self.enabled:
            return self._fallback_trade_feedback(action, symbol, quantity)

        try:
            result = self.trade_feedback(
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
        cash_percentage: float,
        total_pnl_percentage: float
    ) -> str:
        """Get portfolio analysis"""
        if not self.enabled:
            return self._fallback_portfolio_insights(num_positions)

        try:
            result = self.portfolio_review(
                num_positions=num_positions,
                total_value=total_value,
                cash_percentage=cash_percentage,
                total_pnl_percentage=total_pnl_percentage
            )
            return result.insights
        except Exception as e:
            print(f"Coach error: {e}")
            return self._fallback_portfolio_insights(num_positions)

    def answer_question(self, question: str, user_portfolio_size: int = 0) -> str:
        """Answer a question"""
        if not self.enabled:
            return "AI coach is offline. Try checking your Ollama setup!"

        try:
            result = self.qa_module(
                question=question,
                user_portfolio_size=user_portfolio_size
            )
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
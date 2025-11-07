"""Enhanced Coach Manager with Memory and Context"""
import dspy
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import numpy as np
from src.coach.signatures import (
    TradeFeedbackSignature,
    PortfolioReviewSignature,
    InvestingQuestionSignature
)
from src.coach.dspy_setup import setup_dspy

@dataclass
class CoachMemory:
    """Memory structure for the AI coach"""
    trade_history: List[Dict] = field(default_factory=list)
    portfolio_history: List[Dict] = field(default_factory=list)
    user_behavior_patterns: Dict = field(default_factory=dict)
    learning_progress: Dict = field(default_factory=dict)
    feedback_history: List[Dict] = field(default_factory=list)


class EnhancedCoachManager:
    """Enhanced AI coach with memory and contextual intelligence"""

    def __init__(self):
        self.enabled = setup_dspy()
        self.memory = CoachMemory()

        if self.enabled:
            try:
                self.trade_feedback = dspy.ChainOfThought(TradeFeedbackSignature)
                self.portfolio_review = dspy.ChainOfThought(PortfolioReviewSignature)
                self.qa_module = dspy.ChainOfThought(InvestingQuestionSignature)
                
                # Additional enhanced modules
                from src.coach.signatures import EnhancedTradeFeedbackSignature, TrendAnalysisSignature
                self.enhanced_trade_feedback = dspy.ChainOfThought(EnhancedTradeFeedbackSignature)
                self.trend_analysis = dspy.ChainOfThought(TrendAnalysisSignature)
            except Exception as e:
                print(f"Error initializing DSPy modules: {e}")
                self.enabled = False

    def add_to_memory(self, event_type: str, data: Dict) -> None:
        """Add event to coach memory"""
        timestamp = datetime.now()
        
        if event_type == "trade":
            self.memory.trade_history.append({
                "timestamp": timestamp,
                "data": data
            })
        elif event_type == "portfolio_snapshot":
            self.memory.portfolio_history.append({
                "timestamp": timestamp,
                "day": data["day"],
                "total_value": data["total_value"],
                "cash": data["cash"],
                "positions_value": data["positions_value"],
                "pnl": data["pnl"]
            })
        
        # Keep only recent history to avoid memory bloat
        if len(self.memory.trade_history) > 100:
            self.memory.trade_history = self.memory.trade_history[-100:]
        if len(self.memory.portfolio_history) > 300:  # 300 days of history
            self.memory.portfolio_history = self.memory.portfolio_history[-300:]
        
        # Update user behavior patterns based on new data
        self._update_behavior_patterns()

    def _update_behavior_patterns(self) -> None:
        """Update user behavior patterns based on stored history"""
        if not self.memory.trade_history:
            return

        # Analyze risk patterns
        recent_trades = self.memory.trade_history[-20:]  # Last 20 trades
        aggressive_trades = 0
        total_trades = len(recent_trades)
        
        for trade in recent_trades:
            trade_data = trade["data"]
            trade_value = trade_data["quantity"] * trade_data["price"]
            portfolio_value = trade_data.get("portfolio_value", 1000000)
            if portfolio_value > 0 and (trade_value / portfolio_value) > 0.1:  # More than 10% of portfolio
                aggressive_trades += 1
        
        risk_level = "high" if aggressive_trades/total_trades > 0.5 else "moderate" if aggressive_trades/total_trades > 0.2 else "low"
        
        self.memory.user_behavior_patterns["risk_level"] = risk_level
        self.memory.user_behavior_patterns["aggressive_trade_percentage"] = aggressive_trades/total_trades if total_trades > 0 else 0

    def _analyze_diversification_trends(self) -> Dict:
        """Analyze diversification patterns"""
        if not self.memory.portfolio_history:
            return {"diversification_score": 5}  # Default score out of 10
        
        # Get the latest position count from portfolio history
        latest_snapshot = self.memory.portfolio_history[-1]
        num_positions = latest_snapshot.get("num_positions", 1)
        diversification_score = min(10, max(1, num_positions * 2))  # Scale: 2 points per position, max 10
        
        return {"diversification_score": diversification_score}

    def _analyze_timing_patterns(self) -> Dict:
        """Analyze user's timing patterns"""
        if len(self.memory.portfolio_history) < 3:
            return {"pattern": "insufficient_data"}
        
        # Calculate returns and volatility
        values = [entry["total_value"] for entry in self.memory.portfolio_history]
        
        if len(values) < 2:
            return {"pattern": "insufficient_data"}
        
        # Calculate daily returns
        daily_returns = np.diff(values) / values[:-1]
        avg_return = np.mean(daily_returns)
        volatility = np.std(daily_returns)
        
        # Determine if user tends to buy high or sell low
        # This is a simplified analysis based on correlation between purchases and subsequent returns
        buy_high_count = 0
        sell_low_count = 0
        
        for i in range(1, len(self.memory.portfolio_history)):
            prev_value = self.memory.portfolio_history[i-1]["total_value"]
            curr_value = self.memory.portfolio_history[i]["total_value"]
            
            # Check if there was significant trading activity in this period
            # (This would require checking against trade history to be more accurate)
        
        return {
            "avg_daily_return": avg_return,
            "volatility": volatility,
            "buy_high_count": buy_high_count,
            "sell_low_count": sell_low_count
        }

    def get_enhanced_trade_feedback(
        self,
        action: str,
        symbol: str,
        quantity: int,
        price: float,
        portfolio_value: float,
        cash_remaining: float,
        num_positions: int
    ) -> str:
        """Get feedback considering historical patterns and context"""
        if not self.enabled:
            return self._fallback_trade_feedback(action, symbol, quantity)

        # Get historical context
        risk_patterns = self.memory.user_behavior_patterns.get("risk_level", "moderate")
        diversification_trends = self._analyze_diversification_trends()
        timing_patterns = self._analyze_timing_patterns()
        
        # Calculate portfolio trend
        portfolio_trend = 0.0
        if len(self.memory.portfolio_history) >= 2:
            first_value = self.memory.portfolio_history[0]["total_value"]
            last_value = self.memory.portfolio_history[-1]["total_value"]
            portfolio_trend = (last_value - first_value) / first_value * 100

        try:
            result = self.enhanced_trade_feedback(
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                portfolio_value=portfolio_value,
                cash_remaining=cash_remaining,
                num_positions=num_positions,
                risk_patterns=risk_patterns,
                diversification_trends=diversification_trends,
                timing_patterns=timing_patterns,
                portfolio_trend=portfolio_trend
            )
            return result.feedback
        except Exception as e:
            print(f"Enhanced coach error: {e}")
            return self._fallback_trade_feedback(action, symbol, quantity)

    def get_portfolio_trend_insights(self) -> str:
        """Get insights based on portfolio value trends over time"""
        if not self.enabled or len(self.memory.portfolio_history) < 2:
            return "Not enough data to analyze trends."

        try:
            # Calculate performance metrics
            first_value = self.memory.portfolio_history[0]["total_value"]
            last_value = self.memory.portfolio_history[-1]["total_value"]
            total_return = (last_value - first_value) / first_value * 100
            
            # Calculate volatility (annualized)
            values = [entry["total_value"] for entry in self.memory.portfolio_history]
            daily_returns = np.diff(values) / values[:-1]
            volatility = np.std(daily_returns) * 100 * np.sqrt(252)  # Annualized volatility
            
            # Determine trend direction
            if total_return > 10:
                trend = "strongly positive"
            elif total_return > 0:
                trend = "positive"
            elif total_return > -10:
                trend = "negative"
            else:
                trend = "strongly negative"
            
            # Get user risk level from patterns
            user_risk_level = self.memory.user_behavior_patterns.get("risk_level", "moderate")
            
            result = self.trend_analysis(
                total_return=total_return,
                volatility=volatility,
                trend=trend,
                portfolio_size=len(self.memory.portfolio_history),
                user_risk_level=user_risk_level
            )
            
            return result.insights
        except Exception as e:
            print(f"Trend analysis error: {e}")
            return "Could not analyze portfolio trends."

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
        """Get feedback on a trade - backward compatibility"""
        return self.get_enhanced_trade_feedback(
            action, symbol, quantity, price, 
            portfolio_value, cash_remaining, num_positions
        )

    def get_portfolio_insights(
        self,
        num_positions: int,
        total_value: float,
        cash_percentage: float,
        total_pnl_percentage: float
    ) -> str:
        """Get portfolio analysis - now with trend insights"""
        if not self.enabled:
            return self._fallback_portfolio_insights(num_positions)

        try:
            # Try to get trend insights if we have enough data
            trend_insights = self.get_portfolio_trend_insights()
            if trend_insights and "Not enough data" not in trend_insights:
                return trend_insights
            else:
                # Fall back to basic analysis if not enough data for trend analysis
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
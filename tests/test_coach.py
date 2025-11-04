"""Tests for the coach functionality"""
import pytest
from src.coach.manager import CoachManager


def test_coach_manager_initialization():
    """Test that coach manager initializes."""
    coach = CoachManager()
    # The coach might be enabled or disabled depending on Ollama availability
    assert coach is not None
    assert hasattr(coach, 'enabled')


def test_fallback_trade_feedback():
    """Test fallback trade feedback functionality."""
    coach = CoachManager()
    
    # Test BUY feedback
    feedback = coach._fallback_trade_feedback("BUY", "RELIANCE", 10)
    assert "Bought 10 shares of RELIANCE" in feedback
    
    # Test SELL feedback
    feedback = coach._fallback_trade_feedback("SELL", "TCS", 5)
    assert "Sold 5 shares of TCS" in feedback


def test_fallback_portfolio_insights():
    """Test fallback portfolio insights functionality."""
    coach = CoachManager()
    
    # Test with 0 positions
    insights = coach._fallback_portfolio_insights(0)
    assert "Portfolio empty" in insights
    
    # Test with 1 position
    insights = coach._fallback_portfolio_insights(1)
    assert "Good start" in insights
    
    # Test with 5 positions
    insights = coach._fallback_portfolio_insights(5)
    assert "5 positions - good diversification" in insights
"""Tests for the trading functionality"""
import pytest
from src.engine.trade_executor import TradeExecutor
from src.models import Portfolio, Position


def test_trade_calculate_commission():
    """Test commission calculation"""
    # Test small transaction (should be percentage-based)
    commission = TradeExecutor.calculate_commission(10000)
    expected = min(10000 * 0.0003, 20.0)  # 0.03% of 10k = 3, but max is 20
    assert commission == expected
    assert abs(commission - 3.0) < 0.01  # 0.03% of 10000 (accounting for floating point precision)

    # Test large transaction (should hit max commission)
    commission = TradeExecutor.calculate_commission(200000)
    expected = min(200000 * 0.0003, 20.0)  # 0.03% of 200k = 60, but max is 20
    assert commission == expected
    assert commission == 20.0  # Should be capped at 20


def test_trade_buy_success():
    """Test successful buy order execution"""
    portfolio = Portfolio(cash=100000, positions=[])
    
    result = TradeExecutor.execute_buy(portfolio, "RELIANCE", 10, 2500.0)
    
    assert result.success is True
    assert result.message.startswith("Bought 10 shares of RELIANCE")
    assert result.executed_price == 2500.0
    assert result.quantity == 10
    assert len(portfolio.positions) == 1
    assert portfolio.positions[0].symbol == "RELIANCE"
    assert portfolio.positions[0].quantity == 10
    assert portfolio.cash == 100000 - (2500 * 10) - result.commission  # 100000 - 25000 - com


def test_trade_buy_insufficient_funds():
    """Test buy order with insufficient funds"""
    portfolio = Portfolio(cash=10000, positions=[])
    
    # Try to buy 10 shares at ₹2500 each (would cost ₹25000 + commission)
    result = TradeExecutor.execute_buy(portfolio, "RELIANCE", 10, 2500.0)
    
    assert result.success is False
    assert "Insufficient funds" in result.message


def test_trade_buy_existing_position():
    """Test buying more of an existing position"""
    # Start with existing position
    existing_pos = Position(symbol="RELIANCE", quantity=5, avg_buy_price=2400.0, current_price=2400.0)
    portfolio = Portfolio(cash=100000, positions=[existing_pos])
    
    # Buy 10 more shares at different price
    result = TradeExecutor.execute_buy(portfolio, "RELIANCE", 10, 2500.0)
    
    assert result.success is True
    assert len(portfolio.positions) == 1  # Still only one position
    assert portfolio.positions[0].quantity == 15  # 5 + 10
    # Check that average buy price is correct: (5*2400 + 10*2500) / 15
    expected_avg = (5 * 2400 + 10 * 2500) / 15
    assert portfolio.positions[0].avg_buy_price == expected_avg


def test_trade_sell_success():
    """Test successful sell order execution"""
    position = Position(symbol="RELIANCE", quantity=20, avg_buy_price=2400.0, current_price=2500.0)
    portfolio = Portfolio(cash=50000, positions=[position])
    
    result = TradeExecutor.execute_sell(portfolio, "RELIANCE", 5, 2500.0)
    
    assert result.success is True
    assert result.message.startswith("Sold 5 shares of RELIANCE")
    assert result.executed_price == 2500.0
    assert result.quantity == 5
    assert portfolio.positions[0].quantity == 15  # 20 - 5
    assert portfolio.cash == 50000 + (2500 * 5) - result.commission  # 50000 + 12500 - com


def test_trade_sell_insufficient_quantity():
    """Test sell order with insufficient quantity"""
    position = Position(symbol="RELIANCE", quantity=10, avg_buy_price=2400.0, current_price=2500.0)
    portfolio = Portfolio(cash=50000, positions=[position])
    
    # Try to sell 15 shares when only have 10
    result = TradeExecutor.execute_sell(portfolio, "RELIANCE", 15, 2500.0)
    
    assert result.success is False
    assert "Insufficient quantity" in result.message


def test_trade_sell_no_position():
    """Test sell order with no existing position"""
    portfolio = Portfolio(cash=50000, positions=[])
    
    result = TradeExecutor.execute_sell(portfolio, "RELIANCE", 5, 2500.0)
    
    assert result.success is False
    assert "No position in RELIANCE" in result.message


def test_trade_sell_full_position():
    """Test selling entire position (should remove position)"""
    position = Position(symbol="RELIANCE", quantity=10, avg_buy_price=2400.0, current_price=2500.0)
    portfolio = Portfolio(cash=50000, positions=[position])
    
    result = TradeExecutor.execute_sell(portfolio, "RELIANCE", 10, 2500.0)
    
    assert result.success is True
    assert len(portfolio.positions) == 0  # Position removed completely
    assert portfolio.cash > 50000  # Cash increased
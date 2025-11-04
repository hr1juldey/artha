"""Test trade execution"""
import pytest
from src.engine.trade_executor import TradeExecutor
from src.models import Portfolio, Position

def test_buy_success():
    """Test successful buy"""
    portfolio = Portfolio(cash=100000)

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 10, 1000.0
    )

    assert result.success
    assert len(portfolio.positions) == 1
    assert portfolio.positions[0].quantity == 10
    assert portfolio.cash < 100000  # Cash reduced

def test_buy_insufficient_funds():
    """Test buy with insufficient funds"""
    portfolio = Portfolio(cash=100)

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 10, 1000.0
    )

    assert not result.success
    assert "Insufficient funds" in result.message

def test_sell_success():
    """Test successful sell"""
    portfolio = Portfolio(
        cash=50000,
        positions=[Position("TEST", 10, 1000.0, 1100.0)]
    )

    result = TradeExecutor.execute_sell(
        portfolio, "TEST", 5, 1100.0
    )

    assert result.success
    assert portfolio.positions[0].quantity == 5
    assert portfolio.cash > 50000  # Cash increased

def test_sell_insufficient_quantity():
    """Test sell with insufficient quantity"""
    portfolio = Portfolio(
        cash=50000,
        positions=[Position("TEST", 5, 1000.0, 1100.0)]
    )

    result = TradeExecutor.execute_sell(
        portfolio, "TEST", 10, 1100.0
    )

    assert not result.success
    assert "Insufficient quantity" in result.message

def test_commission_calculation():
    """Test commission calculation"""
    # Small trade
    commission = TradeExecutor.calculate_commission(10000)
    assert abs(commission - 3.0) < 0.01  # 0.03% of 10k (accounting for floating point precision)

    # Large trade
    commission = TradeExecutor.calculate_commission(1000000)
    assert commission == 20.0  # Capped at ₹20

def test_validate_trade_inputs():
    """Test input validation"""
    # Valid inputs
    valid, msg = TradeExecutor.validate_trade_inputs("RELIANCE", 10, 2000.0)
    assert valid
    assert msg == "OK"

    # Empty symbol
    valid, msg = TradeExecutor.validate_trade_inputs("", 10, 2000.0)
    assert not valid
    assert "Symbol cannot be empty" in msg

    # Negative quantity
    valid, msg = TradeExecutor.validate_trade_inputs("RELIANCE", -5, 2000.0)
    assert not valid
    assert "Quantity must be positive" in msg

    # Zero quantity
    valid, msg = TradeExecutor.validate_trade_inputs("RELIANCE", 0, 2000.0)
    assert not valid
    assert "Quantity must be positive" in msg

    # Large quantity
    valid, msg = TradeExecutor.validate_trade_inputs("RELIANCE", 20000, 2000.0)
    assert not valid
    assert "Quantity too large" in msg

    # Negative price
    valid, msg = TradeExecutor.validate_trade_inputs("RELIANCE", 10, -500.0)
    assert not valid
    assert "Price must be positive" in msg

    # Very high price
    valid, msg = TradeExecutor.validate_trade_inputs("RELIANCE", 10, 200000.0)
    assert not valid
    assert "Price unrealistic" in msg

def test_buy_exact_cash_match():
    """Test buying when cost exactly matches available cash"""
    # Cost = 10 shares * 1000 = 10,000
    # Commission = 10,000 * 0.0003 = 3
    # Total = 10,003
    portfolio = Portfolio(cash=10003.0)

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 10, 1000.0
    )

    assert result.success
    assert abs(portfolio.cash) < 0.01  # Should be approximately 0


def test_position_averaging_up():
    """Test averaging up (buying at higher price)"""
    portfolio = Portfolio(
        cash=50000.0,
        positions=[Position("TEST", 100, 100.0, 110.0)]
    )

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 50, 120.0
    )

    assert result.success
    position = portfolio.positions[0]
    assert position.quantity == 150

    # Expected average: (100*100 + 50*120) / 150 = 106.67
    expected_avg = (100 * 100 + 50 * 120) / 150
    assert abs(position.avg_buy_price - expected_avg) < 0.01


def test_position_averaging_down():
    """Test averaging down (buying at lower price)"""
    portfolio = Portfolio(
        cash=50000.0,
        positions=[Position("TEST", 100, 120.0, 110.0)]
    )

    result = TradeExecutor.execute_buy(
        portfolio, "TEST", 100, 100.0
    )

    assert result.success
    position = portfolio.positions[0]
    assert position.quantity == 200

    # Expected average: (100*120 + 100*100) / 200 = 110
    expected_avg = (100 * 120 + 100 * 100) / 200
    assert abs(position.avg_buy_price - expected_avg) < 0.01
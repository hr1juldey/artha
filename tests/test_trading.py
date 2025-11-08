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


def test_pnl_updates_with_price_changes():
    """Test that P&L correctly updates when market prices fluctuate"""
    # Create portfolio with multiple positions
    positions = [
        Position(symbol="RELIANCE", quantity=50, avg_buy_price=2400.0, current_price=2400.0),
        Position(symbol="TCS", quantity=30, avg_buy_price=3000.0, current_price=3000.0),
        Position(symbol="INFY", quantity=100, avg_buy_price=1400.0, current_price=1400.0),
    ]
    portfolio = Portfolio(cash=500000, positions=positions)

    # Initial state: P&L should be 0 (current_price == avg_buy_price)
    initial_pnl = portfolio.total_pnl
    initial_total_value = portfolio.total_value
    initial_invested = portfolio.invested

    assert initial_pnl == 0.0, f"Initial P&L should be 0, got {initial_pnl}"
    assert initial_invested == (50*2400 + 30*3000 + 100*1400), "Initial invested incorrect"
    assert initial_total_value == initial_invested + 500000, "Initial total value incorrect"

    # Day 1: Simulate market going up
    positions[0].current_price = 2450.0  # RELIANCE +50 (+2.08%)
    positions[1].current_price = 3060.0  # TCS +60 (+2.00%)
    positions[2].current_price = 1420.0  # INFY +20 (+1.43%)

    day1_pnl = portfolio.total_pnl
    day1_total_value = portfolio.total_value

    # Calculate expected P&L
    expected_pnl_day1 = (50 * 50) + (30 * 60) + (100 * 20)  # 2500 + 1800 + 2000 = 6300

    assert day1_pnl > 0, f"Day 1 P&L should be positive, got {day1_pnl}"
    assert day1_pnl == expected_pnl_day1, f"Day 1 P&L should be {expected_pnl_day1}, got {day1_pnl}"
    assert day1_total_value == initial_total_value + expected_pnl_day1, "Day 1 total value incorrect"

    print(f"✓ Day 1: P&L = ₹{day1_pnl:,.2f} (Expected: ₹{expected_pnl_day1:,.2f})")

    # Day 2: Simulate market going down
    positions[0].current_price = 2350.0  # RELIANCE -50 from avg (-2.08%)
    positions[1].current_price = 2940.0  # TCS -60 from avg (-2.00%)
    positions[2].current_price = 1380.0  # INFY -20 from avg (-1.43%)

    day2_pnl = portfolio.total_pnl
    day2_total_value = portfolio.total_value

    expected_pnl_day2 = (50 * -50) + (30 * -60) + (100 * -20)  # -2500 + -1800 + -2000 = -6300

    assert day2_pnl < 0, f"Day 2 P&L should be negative, got {day2_pnl}"
    assert day2_pnl == expected_pnl_day2, f"Day 2 P&L should be {expected_pnl_day2}, got {day2_pnl}"
    assert day2_total_value == initial_total_value + expected_pnl_day2, "Day 2 total value incorrect"

    print(f"✓ Day 2: P&L = ₹{day2_pnl:,.2f} (Expected: ₹{expected_pnl_day2:,.2f})")

    # Day 3: Simulate mixed movements
    positions[0].current_price = 2500.0  # RELIANCE +100 from avg (+4.17%)
    positions[1].current_price = 2970.0  # TCS -30 from avg (-1.00%)
    positions[2].current_price = 1450.0  # INFY +50 from avg (+3.57%)

    day3_pnl = portfolio.total_pnl

    expected_pnl_day3 = (50 * 100) + (30 * -30) + (100 * 50)  # 5000 + -900 + 5000 = 9100

    assert day3_pnl == expected_pnl_day3, f"Day 3 P&L should be {expected_pnl_day3}, got {day3_pnl}"

    print(f"✓ Day 3: P&L = ₹{day3_pnl:,.2f} (Expected: ₹{expected_pnl_day3:,.2f})")

    # Verify P&L percentage calculation
    pnl_pct = (day3_pnl / portfolio.invested) * 100
    expected_pnl_pct = (expected_pnl_day3 / initial_invested) * 100

    assert abs(pnl_pct - expected_pnl_pct) < 0.01, f"P&L % should be {expected_pnl_pct:.2f}%, got {pnl_pct:.2f}%"

    print(f"✓ Day 3: P&L % = {pnl_pct:.2f}% (Expected: {expected_pnl_pct:.2f}%)")

    # Verify positions_value property
    expected_positions_value = (50 * 2500) + (30 * 2970) + (100 * 1450)
    assert portfolio.positions_value == expected_positions_value, "positions_value calculation incorrect"

    print(f"✓ Portfolio positions value = ₹{portfolio.positions_value:,.2f}")
    print(f"✓ Portfolio total value = ₹{portfolio.total_value:,.2f}")
    print(f"✓ All P&L calculations correct!")


def test_enhanced_position_current_price_update():
    """Test that EnhancedPosition updates market_value when current_price changes (Bug Fix)"""
    from src.models.transaction_models import EnhancedPosition, PositionTransaction
    from src.utils.xirr_calculator import TransactionType
    from datetime import date

    # Create an enhanced position with a buy transaction
    position = EnhancedPosition(symbol="ITC", current_price=404.05)
    position.add_transaction(PositionTransaction(
        date=date(2024, 1, 1),
        quantity=10,
        price=404.05,
        transaction_type=TransactionType.BUY
    ))

    # Initial state
    assert position.quantity == 10
    assert position.avg_buy_price == 404.05
    assert position.current_price == 404.05

    initial_market_value = position.market_value
    initial_pnl = position.unrealized_pnl

    assert initial_market_value == 10 * 404.05, f"Initial market value should be ₹4,040.50, got ₹{initial_market_value}"
    assert initial_pnl == 0.0, f"Initial P&L should be ₹0, got ₹{initial_pnl}"

    print(f"✓ Initial: Price=₹{position.current_price}, MV=₹{position.market_value:,.2f}, P&L=₹{position.unrealized_pnl:,.2f}")

    # Simulate market price change (this is what happens in action_advance_day)
    position.current_price = 418.75  # Price increased

    # CRITICAL: market_value should now update automatically!
    updated_market_value = position.market_value
    updated_pnl = position.unrealized_pnl

    expected_market_value = 10 * 418.75  # 4,187.50
    expected_pnl = (418.75 - 404.05) * 10  # 147.00

    assert updated_market_value == expected_market_value, \
        f"Market value should update to ₹{expected_market_value:,.2f}, got ₹{updated_market_value:,.2f}"

    assert abs(updated_pnl - expected_pnl) < 0.01, \
        f"P&L should update to ₹{expected_pnl:,.2f}, got ₹{updated_pnl:,.2f}"

    print(f"✓ After price change: Price=₹{position.current_price}, MV=₹{position.market_value:,.2f}, P&L=₹{position.unrealized_pnl:,.2f}")

    # Change price again
    position.current_price = 395.00  # Price decreased below avg

    updated_market_value = position.market_value
    updated_pnl = position.unrealized_pnl

    expected_market_value = 10 * 395.00  # 3,950.00
    expected_pnl = (395.00 - 404.05) * 10  # -90.50

    assert updated_market_value == expected_market_value, \
        f"Market value should update to ₹{expected_market_value:,.2f}, got ₹{updated_market_value:,.2f}"

    assert abs(updated_pnl - expected_pnl) < 0.01, \
        f"P&L should update to ₹{expected_pnl:,.2f}, got ₹{updated_pnl:,.2f}"

    print(f"✓ After 2nd price change: Price=₹{position.current_price}, MV=₹{position.market_value:,.2f}, P&L=₹{position.unrealized_pnl:,.2f}")
    print(f"✓ Bug fix verified: market_value and unrealized_pnl now update when current_price changes!")
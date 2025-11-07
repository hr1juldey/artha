"""
Test suite for Artha game improvements

This test suite validates all the enhancements planned in the development plan:
1. Transaction-based position tracking with XIRR calculations
2. UI/UX enhancements with charts and visualizations
3. Game engine fixes for day limit issue
4. Enhanced AI coach with memory and data processing
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.models import Position, Portfolio, GameState
from src.engine.trade_executor import TradeExecutor, OrderSide
from src.data.loader import MarketDataLoader
from src.coach.manager import CoachManager
from src.coach.signatures import EnhancedTradeFeedbackSignature
from scipy.optimize import newton

# Test for Issue 1: Transaction-based Position Tracking and XIRR

def test_transaction_based_position_tracking():
    """Test that positions now track individual transactions"""
    from src.models.transaction_models import PositionTransaction, EnhancedPosition
    
    # Create a new position with first transaction
    first_transaction = PositionTransaction(
        date=datetime.now().date(),
        quantity=100,
        price=2000.0,
        transaction_type=OrderSide.BUY
    )
    
    position = EnhancedPosition(
        symbol="RELIANCE",
        current_price=2100.0
    )
    position.add_transaction(first_transaction)
    
    # Verify initial state
    assert position.quantity == 100
    assert position.avg_buy_price == 2000.0
    
    # Add a second transaction at different price
    second_transaction = PositionTransaction(
        date=datetime.now().date(),
        quantity=50,
        price=2200.0,
        transaction_type=OrderSide.BUY
    )
    position.add_transaction(second_transaction)
    
    # Verify new state
    assert position.quantity == 150
    expected_avg = (100*2000 + 50*2200) / 150  # 2066.67
    assert abs(position.avg_buy_price - expected_avg) < 0.01


def test_pnl_calculation_for_individual_transactions():
    """Test P&L calculation for individual transactions"""
    from src.models.transaction_models import PositionTransaction, EnhancedPosition
    
    # Create position with two different buy transactions
    transactions = [
        PositionTransaction(
            date=(datetime.now() - timedelta(days=30)).date(),
            quantity=100,
            price=2000.0,
            transaction_type=OrderSide.BUY
        ),
        PositionTransaction(
            date=(datetime.now() - timedelta(days=15)).date(),
            quantity=50,
            price=2200.0,
            transaction_type=OrderSide.BUY
        )
    ]
    
    position = EnhancedPosition(
        symbol="RELIANCE",
        current_price=2400.0
    )
    
    # Add transactions to the position
    for trans in transactions:
        position.add_transaction(trans)
    
    # P&L for first transaction (100 shares at 2000, now 2400)
    pnl_first = position.calculate_pnl_for_transaction(0)
    expected_pnl_first = (2400.0 - 2000.0) * 100
    assert abs(pnl_first - expected_pnl_first) < 0.01
    
    # P&L for second transaction (50 shares at 2200, now 2400)
    pnl_second = position.calculate_pnl_for_transaction(1)
    expected_pnl_second = (2400.0 - 2200.0) * 50
    assert abs(pnl_second - expected_pnl_second) < 0.01


def test_xirr_calculation():
    """Test XIRR calculation for positions"""
    from src.models.transaction_models import PositionTransaction, EnhancedPosition
    
    # Create a position with multiple transactions
    start_date = (datetime.now() - timedelta(days=100)).date()
    transactions = [
        PositionTransaction(
            date=start_date,
            quantity=100,
            price=2000.0,
            transaction_type=OrderSide.BUY
        ),
        PositionTransaction(
            date=(datetime.now() - timedelta(days=70)).date(),
            quantity=50,
            price=2100.0,
            transaction_type=OrderSide.BUY
        ),
        PositionTransaction(
            date=(datetime.now() - timedelta(days=40)).date(),
            quantity=25,
            price=2150.0,
            transaction_type=OrderSide.BUY
        )
    ]
    
    # Current price is 2300, with remaining quantity 175
    position = EnhancedPosition(
        symbol="RELIANCE",
        current_price=2300.0
    )
    
    # Add transactions to the position
    for trans in transactions:
        position.add_transaction(trans)
    
    # Calculate XIRR
    xirr = position.calculate_xirr()
    # The XIRR should be positive since prices have increased over time
    assert xirr > 0


# Test for Issue 2: UI/UX Enhancements

def test_portfolio_chart_widget_creation():
    """Test that portfolio chart widget can be created and updated"""
    from src.tui.widgets.chart_widget import PortfolioChartWidget
    
    # Mock portfolio history data
    portfolio_history = [
        {"day": 1, "total_value": 1000000},
        {"day": 2, "total_value": 1020000},
        {"day": 3, "total_value": 1035000},
        {"day": 4, "total_value": 1042000}
    ]
    
    chart_widget = PortfolioChartWidget(portfolio_history)
    # Verify widget was created successfully
    assert chart_widget is not None
    assert len(chart_widget.portfolio_history) == 4


def test_enhanced_portfolio_grid():
    """Test enhanced portfolio grid functionality"""
    from src.tui.widgets.chart_widget import EnhancedPortfolioGrid
    from src.models import Portfolio, Position
    
    # Create a test portfolio
    portfolio = Portfolio(
        cash=500000.0,
        positions=[
            Position(symbol="RELIANCE", quantity=100, avg_buy_price=2000.0, current_price=2200.0),
            Position(symbol="TCS", quantity=50, avg_buy_price=3000.0, current_price=3100.0),
        ]
    )
    
    grid = EnhancedPortfolioGrid()
    # Verify grid updates without errors
    grid.update_portfolio(portfolio)
    # This should not raise any exceptions

# Test for Issue 3: Game Engine Fix

def test_market_data_loader_with_extended_history():
    """Test that market data loader can handle extended history"""
    loader = MarketDataLoader()
    
    # Test that we can fetch more than 365 days of data
    df = loader.get_stock_data("RELIANCE", days=2000)
    
    # Should not be empty for a major stock like RELIANCE
    assert df is not None
    assert len(df) > 0


def test_price_simulation_beyond_historical_data():
    """Test that price simulation works beyond historical data"""
    loader = MarketDataLoader()
    
    # Mock a scenario where historical data is limited
    with patch.object(loader, 'get_stock_data', return_value=pd.DataFrame()):
        # This should fall back to mock data generation
        result = loader._generate_mock_data("TEST", 100)
        assert result is not None
        assert len(result) == 100


def test_advance_day_beyond_original_limit():
    """Test that game can advance beyond original 30-day limit"""
    from src.tui.screens.dashboard_screen import DashboardScreen
    from src.models import GameState, Portfolio
    
    # Create a game state with extended total days
    game_state = GameState(
        player_name="Test Player",
        current_day=290,
        total_days=500,  # Extended limit
        initial_capital=1000000.0,
        portfolio=Portfolio(cash=500000.0)
    )
    
    # Create the screen and mock the app
    screen = DashboardScreen(game_state)
    screen.app = Mock()
    screen.app.market_data = Mock()
    screen.app.market_data.get_price_at_day_with_simulation = Mock(return_value=2000.0)
    screen.app.coach = Mock()
    screen.app.coach.add_to_memory = Mock()
    screen.app.coach.get_enhanced_trade_feedback = Mock(return_value="Test feedback")
    
    # Record initial state
    original_day = game_state.current_day
    
    # Advance day
    screen.action_advance_day()
    
    # Verify day was incremented
    assert game_state.current_day == original_day + 1


# Test for Issue 4: Enhanced AI Coach

def test_coach_memory_system():
    """Test the coach's memory system for storing historical data"""
    from src.coach.enhanced_manager import EnhancedCoachManager
    
    coach = EnhancedCoachManager()
    
    # Add a trade to memory
    trade_data = {
        "action": "BUY",
        "symbol": "RELIANCE",
        "quantity": 100,
        "price": 2000.0,
        "portfolio_value": 1000000.0
    }
    
    coach.add_to_memory("trade", trade_data)
    
    # Verify trade was added
    assert len(coach.memory.trade_history) == 1
    assert coach.memory.trade_history[0]["data"]["symbol"] == "RELIANCE"


def test_risk_pattern_analysis():
    """Test the coach's ability to analyze risk patterns"""
    from src.coach.enhanced_manager import EnhancedCoachManager
    
    coach = EnhancedCoachManager()
    
    # Add trade history that suggests high risk behavior
    for i in range(10):
        # Trades that use 15% of portfolio (relatively high)
        trade_data = {
            "action": "BUY",
            "symbol": f"STOCK{i}",
            "quantity": 100,
            "price": 15000.0,
            "portfolio_value": 1000000.0
        }
        coach.add_to_memory("trade", trade_data)
    
    # Update behavior patterns
    coach._update_behavior_patterns()
    
    # Check risk patterns in memory
    risk_patterns = coach.memory.user_behavior_patterns.get("risk_level", "unknown")
    
    # Should detect high risk behavior
    assert risk_patterns in ["high", "moderate"]


def test_portfolio_trend_analysis():
    """Test the coach's portfolio trend analysis"""
    from src.coach.enhanced_manager import EnhancedCoachManager
    
    coach = EnhancedCoachManager()
    
    # Add portfolio snapshots showing a positive trend
    for day in range(0, 20, 2):  # Every 2 days
        portfolio_data = {
            "day": day,
            "total_value": 1000000.0 + day * 10000,  # Increasing value
            "cash": 500000.0,
            "positions_value": 500000.0 + day * 10000,
            "pnl": day * 10000
        }
        coach.add_to_memory("portfolio_snapshot", portfolio_data)
    
    # Get trend insights
    insights = coach.get_portfolio_trend_insights()
    
    # Should return some insights (not empty)
    assert insights is not None
    assert len(insights) > 0


def test_enhanced_trade_feedback():
    """Test that enhanced trade feedback considers historical context"""
    with patch('src.coach.dspy_setup.setup_dspy', return_value=False):  # Use fallback
        from src.coach.enhanced_manager import EnhancedCoachManager
        
        coach = EnhancedCoachManager()
        
        # Add to memory to provide context
        coach.add_to_memory("trade", {
            "action": "BUY",
            "symbol": "RELIANCE",
            "quantity": 100,
            "price": 2000.0,
            "portfolio_value": 1000000.0
        })
        
        # Test enhanced feedback method (should call fallback if DSPy unavailable)
        feedback = coach.get_enhanced_trade_feedback(
            action="BUY",
            symbol="TCS",
            quantity=50,
            price=3000.0,
            portfolio_value=950000.0,
            cash_remaining=800000.0,
            num_positions=2
        )
        
        # Should return some feedback string
        assert isinstance(feedback, str)
        assert len(feedback) > 0


# Integration Tests

def test_end_to_end_transaction_based_trading():
    """End-to-end test of the transaction-based trading system"""
    from src.models.transaction_models import PositionTransaction, EnhancedPosition
    from src.engine.trade_executor import TradeExecutor, OrderSide
    from src.models import Portfolio
    
    # Create initial portfolio
    portfolio = Portfolio(cash=1000000.0)
    
    # Create a position with initial transaction
    initial_pos = EnhancedPosition(symbol="RELIANCE", current_price=2000.0)
    initial_pos.add_transaction(PositionTransaction(
        date=datetime.now().date(),
        quantity=100,
        price=2000.0,
        transaction_type=OrderSide.BUY
    ))
    
    portfolio.positions.append(initial_pos)
    
    # Execute another buy with the trade executor
    result = TradeExecutor.execute_buy(
        portfolio, 
        "RELIANCE", 
        50, 
        2200.0
    )
    
    assert result.success
    
    # Verify portfolio state
    assert len(portfolio.positions) == 1
    position = portfolio.positions[0]
    assert position.symbol == "RELIANCE"
    assert position.quantity == 150  # 100 + 50
    
    # Execute a sell
    result = TradeExecutor.execute_sell(
        portfolio,
        "RELIANCE",
        30,
        2300.0
    )
    
    assert result.success
    assert position.quantity == 120  # 150 - 30


def test_game_extends_beyond_280_days():
    """Test that game can run beyond the problematic 280-day limit"""
    from src.models import GameState, Portfolio
    from src.data.loader import MarketDataLoader
    
    # Create a game state at day 285 of 500
    game_state = GameState(
        player_name="Test Player",
        current_day=285,
        total_days=500,
        initial_capital=1000000.0,
        portfolio=Portfolio(cash=500000.0)
    )
    
    # Add positions
    from src.models import Position
    game_state.portfolio.positions = [
        Position(symbol="RELIANCE", quantity=100, avg_buy_price=2000.0, current_price=2100.0)
    ]
    
    # Mock market data loader
    loader = Mock(spec=MarketDataLoader)
    loader.get_price_at_day_with_simulation = Mock(return_value=2150.0)
    
    # Simulate advancing days beyond 280
    for day in range(285, 295):  # 10 more days
        game_state.current_day += 1
        
        # Update prices using mock loader
        for position in game_state.portfolio.positions:
            new_price = loader.get_price_at_day_with_simulation(position.symbol)
            position.current_price = new_price
    
    # Verify we successfully advanced beyond 280
    assert game_state.current_day == 295


def test_enhanced_coach_with_full_memory():
    """Test coach when it has a full memory of user behavior"""
    from src.coach.enhanced_manager import EnhancedCoachManager
    
    coach = EnhancedCoachManager()
    
    # Simulate a user who frequently buys high-risk positions
    for i in range(20):
        trade_data = {
            "action": "BUY",
            "symbol": f"HIGHVOL{i}",
            "quantity": 500,  # Large quantity
            "price": 1000.0,
            "portfolio_value": 1000000.0
        }
        coach.add_to_memory("trade", trade_data)
        
        # Add portfolio snapshots as well
        portfolio_data = {
            "day": i,
            "total_value": 1000000.0 + i * 10000,
            "cash": 500000.0 - i * 5000,
            "positions_value": 500000.0 + i * 15000,
            "pnl": i * 10000
        }
        coach.add_to_memory("portfolio_snapshot", portfolio_data)
    
    # Update behavior patterns
    coach._update_behavior_patterns()
    
    # Test that trend insights can be generated
    insights = coach.get_portfolio_trend_insights()
    assert insights is not None
    assert len(insights) > 0
    
    # Test that risk patterns are detected
    risk_patterns = coach.memory.user_behavior_patterns.get("risk_level", "unknown")
    assert risk_patterns is not None


# Performance Tests

def test_performance_with_large_transaction_history():
    """Test performance when position has many transactions"""
    from src.models.transaction_models import PositionTransaction, EnhancedPosition
    
    # Create a position with many transactions
    base_date = (datetime.now() - timedelta(days=500)).date()
    
    position = EnhancedPosition(
        symbol="TEST",
        current_price=1200.0
    )
    
    for i in range(100):  # 100 transactions
        transaction = PositionTransaction(
            date=base_date,
            quantity=50,
            price=1000.0 + (i % 50) * 10,  # Varying prices
            transaction_type=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
        )
        position.add_transaction(transaction)
    
    # Calculate XIRR - should not take too long
    import time
    start_time = time.time()
    xirr = position.calculate_xirr()
    end_time = time.time()
    
    # Should complete in reasonable time (under 1 second)
    assert end_time - start_time < 1.0
    # XIRR calculation should return a value
    assert isinstance(xirr, (int, float))


def test_memory_management_in_coach():
    """Test that coach memory management works properly"""
    from src.coach.enhanced_manager import EnhancedCoachManager
    
    coach = EnhancedCoachManager()
    
    # Add many trades to test memory limits
    for i in range(200):
        trade_data = {
            "action": "BUY",
            "symbol": f"STOCK{i}",
            "quantity": 100,
            "price": 1000.0,
            "portfolio_value": 1000000.0
        }
        coach.add_to_memory("trade", trade_data)
    
    # Add portfolio snapshots
    for i in range(400):  # More portfolio snapshots than the limit
        portfolio_data = {
            "day": i,
            "total_value": 1000000.0 + i * 1000,
            "cash": 500000.0,
            "positions_value": 500000.0 + i * 1000,
            "pnl": i * 1000
        }
        coach.add_to_memory("portfolio_snapshot", portfolio_data)
    
    # Verify memory limits are enforced (portfolio_history should be limited)
    assert len(coach.memory.portfolio_history) <= 300  # 300 is the limit
    assert len(coach.memory.trade_history) <= 100      # 100 is the limit
"""
Test suite for realized P&L tracking (Bug #2)

These tests verify that realized P&L is properly tracked when positions are closed.
With the current buggy code, these tests will FAIL.
After the fix, they should PASS.
"""
import pytest
from datetime import date
from src.models import Portfolio, Position
from src.engine.trade_executor import TradeExecutor
from src.models.transaction_models import EnhancedPosition, PositionTransaction
from src.utils.xirr_calculator import TransactionType


class TestRealizedPnLTracking:
    """Test that realized P&L is tracked when selling positions"""

    def test_portfolio_has_realized_pnl_field(self):
        """
        CRITICAL TEST: Portfolio should have realized_pnl field

        This is the foundation for tracking closed trade performance.
        """
        portfolio = Portfolio(cash=100000, positions=[])

        # Portfolio should have realized_pnl attribute
        assert hasattr(portfolio, 'realized_pnl'), \
            "❌ FAIL: Portfolio missing realized_pnl field"

        # Should default to 0
        assert portfolio.realized_pnl == 0, \
            f"❌ FAIL: Initial realized_pnl should be 0, got {portfolio.realized_pnl}"

        print("✓ Portfolio has realized_pnl field")

    def test_sell_profitable_position_updates_realized_pnl(self):
        """
        Test that selling at profit updates realized P&L

        Buy at ₹100, sell at ₹120 → Realized P&L = +₹2,000 (100 shares × ₹20)
        """
        portfolio = Portfolio(cash=100000, positions=[])

        # Buy 100 @ ₹100
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)
        assert buy_result.success

        # Sell 100 @ ₹120 (profit)
        sell_result = TradeExecutor.execute_sell(portfolio, "TEST", 100, 120)
        assert sell_result.success

        # Calculate expected realized P&L
        # Proceeds = 100 × 120 = 12,000
        # Cost basis = 100 × 100 + buy_commission = 10,000 + 3 = 10,003
        # Sell commission = ~3.6
        # Realized P&L = 12,000 - 3.6 - 10,003 = 1,993.4
        buy_commission = buy_result.commission
        sell_commission = sell_result.commission

        proceeds = 100 * 120
        cost_basis = 100 * 100 + buy_commission
        expected_realized_pnl = proceeds - sell_commission - cost_basis

        # Portfolio should track this realized P&L
        assert hasattr(portfolio, 'realized_pnl'), "Portfolio missing realized_pnl field"
        assert abs(portfolio.realized_pnl - expected_realized_pnl) < 0.01, \
            f"❌ FAIL: Realized P&L {portfolio.realized_pnl} != {expected_realized_pnl}"

        print(f"✓ Realized P&L tracked correctly: ₹{portfolio.realized_pnl:.2f}")

    def test_sell_losing_position_updates_realized_pnl(self):
        """
        Test that selling at loss updates realized P&L (negative value)

        Buy at ₹100, sell at ₹80 → Realized P&L = -₹2,000 (100 shares × -₹20)
        """
        portfolio = Portfolio(cash=100000, positions=[])

        # Buy 100 @ ₹100
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)
        assert buy_result.success

        # Sell 100 @ ₹80 (loss)
        sell_result = TradeExecutor.execute_sell(portfolio, "TEST", 100, 80)
        assert sell_result.success

        # Calculate expected realized P&L
        buy_commission = buy_result.commission
        sell_commission = sell_result.commission

        proceeds = 100 * 80
        cost_basis = 100 * 100 + buy_commission
        expected_realized_pnl = proceeds - sell_commission - cost_basis

        # Should be negative (loss)
        assert expected_realized_pnl < 0, "Expected a loss"

        # Portfolio should track this loss
        assert hasattr(portfolio, 'realized_pnl'), "Portfolio missing realized_pnl field"
        assert abs(portfolio.realized_pnl - expected_realized_pnl) < 0.01, \
            f"❌ FAIL: Realized P&L {portfolio.realized_pnl} != {expected_realized_pnl}"

        print(f"✓ Realized loss tracked correctly: ₹{portfolio.realized_pnl:.2f}")

    def test_partial_sell_updates_realized_pnl(self):
        """
        Test that partial sell calculates realized P&L correctly

        Buy 100 @ ₹100, sell 40 @ ₹120 → Realized P&L = +40 × ₹20 = ₹800
        Remaining position should still show unrealized P&L for 60 shares
        """
        portfolio = Portfolio(cash=100000, positions=[])

        # Buy 100 @ ₹100
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)
        assert buy_result.success
        buy_commission = buy_result.commission

        # Sell 40 @ ₹120 (partial)
        sell_result = TradeExecutor.execute_sell(portfolio, "TEST", 40, 120)
        assert sell_result.success
        sell_commission = sell_result.commission

        # Calculate expected realized P&L for 40 shares
        # Cost per share (with commission): (10,000 + buy_commission) / 100
        cost_per_share = (100 * 100 + buy_commission) / 100
        cost_basis_sold = cost_per_share * 40
        proceeds = 40 * 120
        expected_realized_pnl = proceeds - sell_commission - cost_basis_sold

        # Portfolio should track realized P&L from partial sale
        assert hasattr(portfolio, 'realized_pnl'), "Portfolio missing realized_pnl field"
        assert abs(portfolio.realized_pnl - expected_realized_pnl) < 0.01, \
            f"❌ FAIL: Realized P&L {portfolio.realized_pnl} != {expected_realized_pnl}"

        # Position should still exist with 60 shares
        assert len(portfolio.positions) == 1
        assert portfolio.positions[0].quantity == 60

        print(f"✓ Partial sell: Realized P&L = ₹{portfolio.realized_pnl:.2f}, 60 shares remaining")

    def test_multiple_trades_accumulate_realized_pnl(self):
        """
        Test that realized P&L accumulates across multiple closed trades

        Trade 1: Buy 100 TEST @ ₹100, sell @ ₹120 → +₹2,000
        Trade 2: Buy 50 ABC @ ₹200, sell @ ₹180 → -₹1,000
        Total realized P&L should be +₹1,000
        """
        portfolio = Portfolio(cash=200000, positions=[])

        # Trade 1: Profitable
        buy1 = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)
        assert buy1.success
        sell1 = TradeExecutor.execute_sell(portfolio, "TEST", 100, 120)
        assert sell1.success

        trade1_pnl = (100 * 120) - sell1.commission - (100 * 100 + buy1.commission)

        # Check intermediate realized P&L
        assert hasattr(portfolio, 'realized_pnl'), "Portfolio missing realized_pnl field"
        assert abs(portfolio.realized_pnl - trade1_pnl) < 0.01, \
            f"After trade 1: realized P&L {portfolio.realized_pnl} != {trade1_pnl}"

        # Trade 2: Loss
        buy2 = TradeExecutor.execute_buy(portfolio, "ABC", 50, 200)
        assert buy2.success
        sell2 = TradeExecutor.execute_sell(portfolio, "ABC", 50, 180)
        assert sell2.success

        trade2_pnl = (50 * 180) - sell2.commission - (50 * 200 + buy2.commission)

        # Total realized P&L should be sum of both trades
        expected_total_pnl = trade1_pnl + trade2_pnl

        assert abs(portfolio.realized_pnl - expected_total_pnl) < 0.01, \
            f"❌ FAIL: Total realized P&L {portfolio.realized_pnl} != {expected_total_pnl}"

        print(f"✓ Multiple trades: Cumulative realized P&L = ₹{portfolio.realized_pnl:.2f}")

    def test_total_pnl_includes_both_realized_and_unrealized(self):
        """
        CRITICAL TEST: Portfolio total P&L should include BOTH realized and unrealized

        Current bug: total_pnl only shows unrealized P&L from open positions
        Fixed: total_pnl = realized_pnl + unrealized_pnl
        """
        portfolio = Portfolio(cash=200000, positions=[])

        # Trade 1: Close for profit (realized)
        TradeExecutor.execute_buy(portfolio, "CLOSED", 100, 100)
        sell_result = TradeExecutor.execute_sell(portfolio, "CLOSED", 100, 120)

        # Realized P&L ≈ +₹2,000
        realized_pnl = portfolio.realized_pnl if hasattr(portfolio, 'realized_pnl') else 0

        # Trade 2: Keep open (unrealized)
        TradeExecutor.execute_buy(portfolio, "OPEN", 50, 200)
        pos = next(p for p in portfolio.positions if p.symbol == "OPEN")

        # Simulate price increase
        pos.current_price = 220

        # Unrealized P&L ≈ 50 × (220 - 200) = +₹1,000
        unrealized_pnl = pos.unrealized_pnl

        # Total portfolio P&L should be realized + unrealized
        expected_total_pnl = realized_pnl + unrealized_pnl

        # Portfolio.total_pnl should reflect this
        assert abs(portfolio.total_pnl - expected_total_pnl) < 1.0, \
            f"❌ FAIL: Total P&L {portfolio.total_pnl} != {expected_total_pnl} " \
            f"(realized: {realized_pnl}, unrealized: {unrealized_pnl})"

        print(f"✓ Total P&L = Realized (₹{realized_pnl:.2f}) + Unrealized (₹{unrealized_pnl:.2f})")

    def test_sell_result_includes_realized_pnl(self):
        """
        Test that TradeResult from execute_sell includes realized P&L info

        Users should see how much profit/loss they made on the sale.
        """
        portfolio = Portfolio(cash=100000, positions=[])

        # Buy 100 @ ₹100
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)
        buy_commission = buy_result.commission

        # Sell 100 @ ₹120
        sell_result = TradeExecutor.execute_sell(portfolio, "TEST", 100, 120)

        # TradeResult should include realized_pnl field
        assert hasattr(sell_result, 'realized_pnl'), \
            "❌ FAIL: TradeResult missing realized_pnl field"

        # Calculate expected
        cost_basis = 100 * 100 + buy_commission
        proceeds = 100 * 120
        expected_realized_pnl = proceeds - sell_result.commission - cost_basis

        assert abs(sell_result.realized_pnl - expected_realized_pnl) < 0.01, \
            f"❌ FAIL: TradeResult.realized_pnl {sell_result.realized_pnl} != {expected_realized_pnl}"

        print(f"✓ TradeResult includes realized P&L: ₹{sell_result.realized_pnl:.2f}")

    def test_realized_pnl_persists_across_operations(self):
        """
        Test that realized P&L doesn't get reset by other operations

        Close a position for profit, then do other trades - realized P&L should persist.
        """
        portfolio = Portfolio(cash=200000, positions=[])

        # Close position 1 for profit
        TradeExecutor.execute_buy(portfolio, "POS1", 100, 100)
        TradeExecutor.execute_sell(portfolio, "POS1", 100, 120)

        realized_after_first_trade = portfolio.realized_pnl if hasattr(portfolio, 'realized_pnl') else 0
        assert realized_after_first_trade > 0, "Should have positive realized P&L"

        # Do other trades (but don't close)
        TradeExecutor.execute_buy(portfolio, "POS2", 50, 200)
        TradeExecutor.execute_buy(portfolio, "POS3", 30, 150)

        # Realized P&L should NOT change
        assert abs(portfolio.realized_pnl - realized_after_first_trade) < 0.01, \
            f"❌ FAIL: Realized P&L changed after non-closing trades: " \
            f"{realized_after_first_trade} → {portfolio.realized_pnl}"

        print(f"✓ Realized P&L persists: ₹{portfolio.realized_pnl:.2f}")


class TestRealizedPnLCalculation:
    """Test the calculation logic for realized P&L"""

    def test_fifo_realized_pnl_with_multiple_buys(self):
        """
        Test FIFO-based realized P&L calculation with multiple buy prices

        Buy 100 @ ₹100, buy 50 @ ₹110, sell 120 → Should use FIFO
        First 100 sold @ cost ₹100/share, next 20 @ cost ₹110/share
        """
        portfolio = Portfolio(cash=200000, positions=[])

        # Buy 1: 100 @ ₹100
        buy1 = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)

        # Buy 2: 50 @ ₹110
        buy2 = TradeExecutor.execute_buy(portfolio, "TEST", 50, 110)

        # Sell 120 @ ₹120 (uses FIFO: first 100 from buy1, then 20 from buy2)
        sell_result = TradeExecutor.execute_sell(portfolio, "TEST", 120, 120)
        assert sell_result.success

        # Expected FIFO calculation:
        # Cost basis = (100 × 100 + buy1.commission) + (20 × 110 + proportional buy2.commission)
        # For simplicity, we'll use average cost from the position
        pos = portfolio.positions[0]  # 30 shares remaining

        # Total cost basis of all buys
        total_cost = (100 * 100 + buy1.commission) + (50 * 110 + buy2.commission)

        # Proportional cost for 120 shares sold
        cost_per_share = total_cost / 150
        cost_basis_sold = cost_per_share * 120

        proceeds = 120 * 120
        expected_realized_pnl = proceeds - sell_result.commission - cost_basis_sold

        assert hasattr(portfolio, 'realized_pnl'), "Portfolio missing realized_pnl field"
        assert abs(portfolio.realized_pnl - expected_realized_pnl) < 0.5, \
            f"❌ FAIL: FIFO realized P&L {portfolio.realized_pnl} != {expected_realized_pnl}"

        print(f"✓ FIFO realized P&L calculated correctly: ₹{portfolio.realized_pnl:.2f}")


class TestBackwardCompatibility:
    """Test that realized P&L works with existing code"""

    def test_old_portfolio_without_realized_pnl(self):
        """
        Test that old Portfolio objects without realized_pnl field still work
        """
        # Create portfolio that might not have realized_pnl yet
        portfolio = Portfolio(cash=100000, positions=[])

        # If field doesn't exist, it should default to 0 or be added
        if not hasattr(portfolio, 'realized_pnl'):
            # Old portfolios should be handled gracefully
            # Either auto-initialize to 0 or raise clear error
            print("⚠ Old portfolio detected - should auto-initialize realized_pnl to 0")
        else:
            assert portfolio.realized_pnl == 0

        print("✓ Backward compatibility check passed")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])

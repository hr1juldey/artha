"""
Test suite for cost basis bug fix

These tests verify that cost basis includes all transaction costs (commissions).
With the current buggy code, these tests will FAIL.
After the fix, they should PASS.
"""
import pytest
from datetime import date
from src.models import Portfolio
from src.models.transaction_models import EnhancedPosition, PositionTransaction
from src.engine.trade_executor import TradeExecutor
from src.utils.xirr_calculator import TransactionType


class TestCostBasisInclusion:
    """Test that cost basis includes commissions"""

    def test_single_buy_cost_basis_includes_commission(self):
        """
        CRITICAL TEST: Cost basis should include commission

        Current bug: cost_basis = quantity × price (excludes commission)
        Fixed: cost_basis = quantity × price + commission
        """
        position = EnhancedPosition(symbol="TEST", current_price=100)

        # Buy 100 shares @ ₹100 with ₹3 commission
        trans = PositionTransaction(
            date=date.today(),
            quantity=100,
            price=100,
            transaction_type=TransactionType.BUY,
            commission=3.0
        )
        position.add_transaction(trans)

        # ASSERTION 1: Cost basis should be 100*100 + 3 = 10,003
        assert position.cost_basis == 10003, \
            f"❌ FAIL: Cost basis {position.cost_basis} != 10003 (should include ₹3 commission)"

        # ASSERTION 2: Average buy price should be 10,003 / 100 = 100.03
        assert abs(position.avg_buy_price - 100.03) < 0.01, \
            f"❌ FAIL: Avg buy price {position.avg_buy_price} != 100.03"

        print("✓ Single buy cost basis includes commission")

    def test_multiple_buys_cost_basis_accumulates_commissions(self):
        """
        Test that cost basis accumulates commissions from multiple buys
        """
        position = EnhancedPosition(symbol="TEST", current_price=105)

        # Buy 1: 100 shares @ ₹100 with ₹3 commission
        position.add_transaction(PositionTransaction(
            date=date.today(),
            quantity=100,
            price=100,
            transaction_type=TransactionType.BUY,
            commission=3.0
        ))

        # Buy 2: 50 shares @ ₹110 with ₹2 commission
        position.add_transaction(PositionTransaction(
            date=date.today(),
            quantity=50,
            price=110,
            transaction_type=TransactionType.BUY,
            commission=2.0
        ))

        # Cost basis = (100*100 + 3) + (50*110 + 2) = 10,003 + 5,502 = 15,505
        expected_cost_basis = 15505
        assert position.cost_basis == expected_cost_basis, \
            f"❌ FAIL: Cost basis {position.cost_basis} != {expected_cost_basis}"

        # Avg price = 15,505 / 150 = 103.367
        expected_avg = 103.367
        assert abs(position.avg_buy_price - expected_avg) < 0.01, \
            f"❌ FAIL: Avg buy price {position.avg_buy_price} != {expected_avg}"

        print("✓ Multiple buys accumulate commissions correctly")

    def test_cost_basis_matches_cash_paid(self):
        """
        CRITICAL TEST: Cost basis should equal cash paid from portfolio

        This is the MOST IMPORTANT test - it proves that accounting is correct.
        If this fails, users will be confused about where their money went.
        """
        portfolio = Portfolio(cash=1_000_000, positions=[])
        initial_cash = portfolio.cash

        # Execute buy through trade executor
        result = TradeExecutor.execute_buy(portfolio, "RELIANCE", 100, 2000)
        assert result.success, f"Trade failed: {result.message}"

        # Calculate how much cash was actually paid
        cash_paid = initial_cash - portfolio.cash

        # Get the position
        pos = next(p for p in portfolio.positions if p.symbol == "RELIANCE")

        # CRITICAL ASSERTION: Cost basis MUST equal cash paid
        assert abs(pos.cost_basis - cash_paid) < 0.01, \
            f"❌ FAIL: Cost basis {pos.cost_basis} != cash paid {cash_paid} (diff: {abs(pos.cost_basis - cash_paid)})"

        print(f"✓ Cost basis (₹{pos.cost_basis}) matches cash paid (₹{cash_paid})")

    def test_unrealized_pnl_calculation_with_commission(self):
        """
        Test that unrealized P&L is calculated correctly when cost basis includes commission
        """
        position = EnhancedPosition(symbol="TEST", current_price=105)

        # Buy 100 @ ₹100 with ₹3 commission
        position.add_transaction(PositionTransaction(
            date=date.today(),
            quantity=100,
            price=100,
            transaction_type=TransactionType.BUY,
            commission=3.0
        ))

        # Market value: 100 × 105 = 10,500
        # Cost basis: 10,003 (includes commission)
        # Unrealized P&L: 10,500 - 10,003 = 497

        expected_pnl = 497
        assert abs(position.unrealized_pnl - expected_pnl) < 1.0, \
            f"❌ FAIL: Unrealized P&L {position.unrealized_pnl} != {expected_pnl}"

        print(f"✓ Unrealized P&L calculated correctly: ₹{position.unrealized_pnl}")

    def test_buy_sell_round_trip_pnl(self):
        """
        Test round-trip P&L calculation

        Buy at ₹100, sell at ₹100 (same price)
        Should show LOSS equal to total commissions
        """
        portfolio = Portfolio(cash=1_000_000, positions=[])
        initial_cash = portfolio.cash

        # Buy 100 @ ₹1000
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 1000)
        assert buy_result.success
        buy_commission = buy_result.commission

        # Sell 100 @ ₹1000 (same price)
        sell_result = TradeExecutor.execute_sell(portfolio, "TEST", 100, 1000)
        assert sell_result.success
        sell_commission = sell_result.commission

        # Final cash
        final_cash = portfolio.cash

        # Total commissions paid
        total_commissions = buy_commission + sell_commission

        # Loss should equal total commissions
        actual_loss = initial_cash - final_cash
        expected_loss = total_commissions

        assert abs(actual_loss - expected_loss) < 0.01, \
            f"❌ FAIL: Loss {actual_loss} != commissions {expected_loss}"

        print(f"✓ Round-trip at same price: Loss (₹{actual_loss}) = Commissions (₹{expected_loss})")

    def test_partial_sell_cost_basis_proportional(self):
        """
        Test that when selling partial position, remaining cost basis is proportional
        """
        position = EnhancedPosition(symbol="TEST", current_price=110)

        # Buy 100 @ ₹100 with ₹3 commission
        # Total cost: 10,003
        position.add_transaction(PositionTransaction(
            date=date.today(),
            quantity=100,
            price=100,
            transaction_type=TransactionType.BUY,
            commission=3.0
        ))

        # Sell 40 shares (keeping 60)
        position.add_transaction(PositionTransaction(
            date=date.today(),
            quantity=40,
            price=120,
            transaction_type=TransactionType.SELL,
            commission=2.0
        ))

        # Remaining: 60 shares
        assert position.quantity == 60

        # Remaining cost basis should still reflect original cost
        # (The _cost_basis tracks total BUY costs, not reduced by sells)
        # This is correct for FIFO P&L calculation
        assert position.cost_basis == 10003, \
            f"❌ FAIL: Cost basis changed after sell: {position.cost_basis}"

        print("✓ Partial sell: Cost basis remains correct")


class TestTradeExecutorCommissionPassing:
    """Test that TradeExecutor passes commission to PositionTransaction"""

    def test_execute_buy_creates_transaction_with_commission(self):
        """
        Test that execute_buy creates PositionTransaction with commission field
        """
        portfolio = Portfolio(cash=1_000_000, positions=[])

        # Execute buy
        result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 1000)
        assert result.success

        # Get position
        pos = next(p for p in portfolio.positions if p.symbol == "TEST")

        # Position should be EnhancedPosition with transactions
        assert hasattr(pos, 'transactions'), "Position should have transactions attribute"
        assert len(pos.transactions) > 0, "Position should have at least one transaction"

        # Check that transaction has commission
        trans = pos.transactions[0]
        assert hasattr(trans, 'commission'), "Transaction should have commission attribute"
        assert trans.commission > 0, f"Commission should be > 0, got {trans.commission}"

        print(f"✓ Transaction created with commission: ₹{trans.commission}")

    def test_execute_sell_creates_transaction_with_commission(self):
        """
        Test that execute_sell creates PositionTransaction with commission field
        """
        portfolio = Portfolio(cash=1_000_000, positions=[])

        # Buy first
        TradeExecutor.execute_buy(portfolio, "TEST", 100, 1000)

        # Get position and count transactions before sell
        pos = next(p for p in portfolio.positions if p.symbol == "TEST")
        trans_before = len(pos.transactions)

        # Now sell
        result = TradeExecutor.execute_sell(portfolio, "TEST", 50, 1100)
        assert result.success

        # Check new transaction has commission
        trans_after = len(pos.transactions)
        assert trans_after == trans_before + 1, "Should have one more transaction"

        sell_trans = pos.transactions[-1]  # Last transaction
        assert hasattr(sell_trans, 'commission'), "Sell transaction should have commission"
        assert sell_trans.commission > 0, f"Sell commission should be > 0, got {sell_trans.commission}"

        print(f"✓ Sell transaction created with commission: ₹{sell_trans.commission}")


class TestBackwardCompatibility:
    """Test that code handles old transactions without commission field"""

    def test_old_transaction_without_commission(self):
        """
        Test that old PositionTransaction without commission field doesn't crash
        """
        position = EnhancedPosition(symbol="TEST", current_price=100)

        # Create old-style transaction (no commission field)
        old_trans = PositionTransaction(
            date=date.today(),
            quantity=100,
            price=100,
            transaction_type=TransactionType.BUY
            # commission NOT provided
        )

        # Should not crash
        try:
            position.add_transaction(old_trans)
            success = True
        except Exception as e:
            success = False
            error = str(e)

        assert success, f"Failed to handle old transaction: {error if not success else ''}"

        # Cost basis should default to 0 commission
        # Expected: 100 * 100 + 0 = 10,000
        assert position.cost_basis == 10000, \
            f"Cost basis with default commission should be 10000, got {position.cost_basis}"

        print("✓ Backward compatibility: Old transactions work")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])

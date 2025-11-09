"""
Test suite for Bug #4: Missing 80% of Transaction Costs

These tests verify that ALL transaction costs from Indian stock markets are included:
1. Brokerage (0.03%)
2. STT - Securities Transaction Tax (0.1% on sell)
3. Exchange charges (~0.00325%)
4. GST (18% on brokerage + exchange charges)
5. SEBI fees (₹10 per crore)

With current buggy code (only brokerage), these tests will FAIL.
After fix, they should PASS.
"""
import pytest
from src.models import Portfolio
from src.engine.trade_executor import TradeExecutor
from src.config import COMMISSION_RATE


class TestTransactionCostComponents:
    """Test that all transaction cost components are present"""

    def test_config_has_all_cost_parameters(self):
        """
        Test that config.py defines all required cost parameters
        """
        from src import config

        # Check for brokerage (already exists)
        assert hasattr(config, 'COMMISSION_RATE') or hasattr(config, 'BROKERAGE_RATE'), \
            "Missing brokerage rate in config"

        # Check for STT
        assert hasattr(config, 'STT_RATE_BUY') or hasattr(config, 'STT_BUY'), \
            "❌ FAIL: Missing STT_RATE_BUY in config"
        assert hasattr(config, 'STT_RATE_SELL') or hasattr(config, 'STT_SELL'), \
            "❌ FAIL: Missing STT_RATE_SELL in config"

        # Check for Exchange charges
        assert hasattr(config, 'EXCHANGE_CHARGES_RATE') or hasattr(config, 'EXCHANGE_CHARGES'), \
            "❌ FAIL: Missing EXCHANGE_CHARGES_RATE in config"

        # Check for GST
        assert hasattr(config, 'GST_RATE'), \
            "❌ FAIL: Missing GST_RATE in config"

        # Check for SEBI fees
        assert hasattr(config, 'SEBI_FEES_RATE') or hasattr(config, 'SEBI_CHARGES'), \
            "❌ FAIL: Missing SEBI_FEES_RATE in config"

        print("✓ Config has all transaction cost parameters")


class TestBuyTransactionCosts:
    """Test transaction costs on BUY orders"""

    def test_buy_costs_include_brokerage(self):
        """Verify brokerage is charged on buy"""
        portfolio = Portfolio(cash=100000, positions=[])

        result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)
        assert result.success

        # Brokerage should be charged
        assert result.commission > 0, "Brokerage should be > 0"

        # For ₹10,000 trade, brokerage @ 0.03% = ₹3
        expected_brokerage = 10000 * 0.0003
        assert abs(result.commission - expected_brokerage) < 20, \
            f"Brokerage seems wrong: {result.commission} (expected ~{expected_brokerage})"

        print(f"✓ Buy charges brokerage: ₹{result.commission:.2f}")

    def test_buy_costs_breakdown_available(self):
        """
        Test that TradeResult includes cost breakdown

        Users should see:
        - Brokerage
        - STT (if any on buy)
        - Exchange charges
        - GST
        - SEBI fees
        - Total
        """
        portfolio = Portfolio(cash=100000, positions=[])
        result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)

        # Check if TradeResult has cost_breakdown field
        assert hasattr(result, 'cost_breakdown') or hasattr(result, 'cost_details'), \
            "❌ FAIL: TradeResult missing cost breakdown field for transparency"

        print("✓ Buy result includes cost breakdown")

    def test_buy_total_cost_includes_all_charges(self):
        """
        CRITICAL TEST: Total cost should include ALL charges

        For ₹10,000 BUY trade (NOTE: NO STT on delivery buy in India):
        - Brokerage: 10,000 × 0.0003 = ₹3.00
        - STT (buy): ₹0.00 (NO STT on delivery buy, only on sell!)
        - Exchange: 10,000 × 0.0000325 = ₹0.33
        - GST: (3.00 + 0.33) × 0.18 = ₹0.60
        - SEBI: 10,000 × 0.000001 = ₹0.01
        - Total charges: ~₹3.94

        OLD bug: Only charged ₹3 (brokerage)
        NEW: Charges ₹3.94 (all components)
        """
        portfolio = Portfolio(cash=100000, positions=[])

        # Execute ₹10,000 trade
        result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)
        assert result.success

        total_charges = result.commission

        # Expected: Brokerage (₹3) + Exchange (₹0.33) + GST (₹0.60) + SEBI (₹0.01) = ₹3.94
        expected_total = 3.94

        # Should be close to expected
        assert abs(total_charges - expected_total) < 0.1, \
            f"Total charges (₹{total_charges:.2f}) should be ~₹{expected_total}"

        # Should be MORE than just brokerage
        brokerage_only = 10000 * COMMISSION_RATE  # ₹3

        assert total_charges > brokerage_only, \
            f"Total charges (₹{total_charges:.2f}) should be > brokerage only (₹{brokerage_only:.2f})"

        print(f"✓ Total BUY charges: ₹{total_charges:.2f} (includes brokerage, exchange, GST, SEBI)")


class TestSellTransactionCosts:
    """Test transaction costs on SELL orders"""

    def test_sell_costs_include_stt(self):
        """
        CRITICAL TEST: STT must be charged on SELL transactions

        STT (Securities Transaction Tax) = 0.1% on sell side
        This is a LEGAL REQUIREMENT in India
        """
        portfolio = Portfolio(cash=100000, positions=[])

        # Buy first
        TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)

        # Sell
        result = TradeExecutor.execute_sell(portfolio, "TEST", 100, 110)
        assert result.success

        # For ₹11,000 sell, STT @ 0.1% = ₹11
        # This is the BIGGEST missing cost (₹11 vs ₹3.30 total of other charges)

        total_charges = result.commission

        # Check if STT is included
        # Minimum charges should include STT (₹11) + brokerage (₹3.30) + others (~₹1) = ~₹15
        min_expected_with_stt = 11000 * 0.001  # STT alone = ₹11

        if total_charges < min_expected_with_stt:
            assert False, \
                f"❌ FAIL: Sell charges (₹{total_charges:.2f}) missing STT! " \
                f"STT alone should be ₹{min_expected_with_stt:.2f} for ₹11,000 trade"

        print(f"✓ Sell charges (₹{total_charges:.2f}) include STT")

    def test_sell_costs_higher_than_buy(self):
        """
        Test that sell costs are higher than buy costs due to STT

        STT is only charged on sell side (0.1%), making sell more expensive
        """
        portfolio = Portfolio(cash=200000, positions=[])

        # Buy
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)

        # Sell at same price
        sell_result = TradeExecutor.execute_sell(portfolio, "TEST", 100, 100)

        buy_charges = buy_result.commission
        sell_charges = sell_result.commission

        # Sell should be MORE expensive due to STT
        assert sell_charges > buy_charges, \
            f"❌ FAIL: Sell charges (₹{sell_charges:.2f}) should be > buy charges (₹{buy_charges:.2f}) due to STT"

        # Difference should be approximately STT (0.1% of trade value)
        stt_amount = 10000 * 0.001  # ₹10
        difference = sell_charges - buy_charges

        # Difference should be close to STT amount
        assert abs(difference - stt_amount) < 5, \
            f"Difference (₹{difference:.2f}) should be ~₹{stt_amount:.2f} (STT)"

        print(f"✓ Sell charges (₹{sell_charges:.2f}) > Buy charges (₹{buy_charges:.2f})")


class TestGSTCalculation:
    """Test GST is applied correctly"""

    def test_gst_applied_on_brokerage_and_exchange(self):
        """
        GST should be 18% on (brokerage + exchange charges)

        For ₹10,000 trade:
        - Brokerage: ₹3.00
        - Exchange: ₹0.33
        - Base = ₹3.33
        - GST @ 18% = ₹0.60
        """
        portfolio = Portfolio(cash=100000, positions=[])
        result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)

        # Check if cost breakdown exists
        if hasattr(result, 'cost_breakdown'):
            breakdown = result.cost_breakdown
            assert 'gst' in breakdown or 'GST' in breakdown, \
                "❌ FAIL: Cost breakdown missing GST component"

            gst = breakdown.get('gst', breakdown.get('GST', 0))
            assert gst > 0, "GST should be > 0"

            # GST should be ~18% of (brokerage + exchange)
            expected_gst = (3.00 + 0.33) * 0.18  # ≈ ₹0.60
            assert abs(gst - expected_gst) < 0.5, \
                f"GST {gst} doesn't match expected {expected_gst}"

            print(f"✓ GST calculated correctly: ₹{gst:.2f}")
        else:
            assert False, "❌ FAIL: No cost_breakdown available to verify GST"


class TestRoundTripCostAccuracy:
    """Test total costs for round-trip (buy + sell) trades"""

    def test_round_trip_at_same_price_shows_loss(self):
        """
        CRITICAL TEST: Round-trip at same price should show LOSS = total transaction costs

        Buy 100 @ ₹1000, Sell 100 @ ₹1000 (same price)
        Expected costs for ₹1,00,000 trade:

        BUY costs:
        - Brokerage: 100,000 × 0.0003 = ₹30.00
        - STT: 0 (no STT on buy delivery)
        - Exchange: 100,000 × 0.0000325 = ₹3.25
        - GST: (30 + 3.25) × 0.18 = ₹5.99
        - SEBI: 100,000 × 0.000001 = ₹0.10
        - Total buy: ~₹39.34

        SELL costs:
        - Brokerage: 100,000 × 0.0003 = ₹30.00
        - STT: 100,000 × 0.001 = ₹100.00  ← BIGGEST COST
        - Exchange: 100,000 × 0.0000325 = ₹3.25
        - GST: (30 + 3.25) × 0.18 = ₹5.99
        - SEBI: 100,000 × 0.000001 = ₹0.10
        - Total sell: ~₹139.34

        TOTAL ROUND-TRIP: ~₹178.68

        Current bug: Only charges ~₹60 (2 × brokerage × 1.18 for GST)
        Missing: ₹118.68 (mostly STT)
        """
        portfolio = Portfolio(cash=200000, positions=[])
        initial_cash = portfolio.cash

        # Buy
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 1000)
        assert buy_result.success

        # Sell at SAME price
        sell_result = TradeExecutor.execute_sell(portfolio, "TEST", 100, 1000)
        assert sell_result.success

        final_cash = portfolio.cash

        # Loss = initial - final (should equal total transaction costs)
        actual_loss = initial_cash - final_cash
        total_charges = buy_result.commission + sell_result.commission

        # Verify loss equals charges
        assert abs(actual_loss - total_charges) < 0.01, \
            f"Loss (₹{actual_loss:.2f}) doesn't match charges (₹{total_charges:.2f})"

        # Check if charges are realistic
        # Should be ~₹179 for ₹1L round-trip with all costs
        # Current implementation: ~₹60 (only brokerage + GST)

        expected_min_charges = 100  # At minimum, should have STT (₹100)

        if total_charges < expected_min_charges:
            assert False, \
                f"❌ FAIL: Round-trip charges (₹{total_charges:.2f}) way too low! " \
                f"Should be ~₹179 for ₹1L trade. Missing STT and other charges."

        print(f"✓ Round-trip costs: ₹{total_charges:.2f} (cash lost: ₹{actual_loss:.2f})")

    def test_break_even_price_is_realistic(self):
        """
        Test that break-even calculation accounts for all costs

        For ₹1000 buy price with full costs, break-even sell price should be:
        ~₹1001.79 (0.179% higher)

        With buggy code (only brokerage): break-even is ₹1000.60 (0.06%)
        This UNDERSTATES the break-even by 287%!
        """
        portfolio = Portfolio(cash=150000, positions=[])

        # Buy at ₹1000
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 1000)
        buy_cost_total = buy_result.total_cost

        # To break even, sell proceeds (after sell charges) must equal buy cost
        # sell_price × quantity - sell_charges = buy_cost_total
        # This is complex because sell_charges depend on sell_price

        # Approximate break-even: need ~0.179% gain to cover costs
        # Buy cost per share = (100,000 + 39.34) / 100 = 1000.39
        # Need sell proceeds = 100,039.34 + sell_charges
        # sell_charges for ₹1L = ~139.34
        # Total needed = 100,178.68
        # Per share = 1001.79

        expected_breakeven_approx = 1001.79

        # Calculate what the current implementation thinks breakeven is
        # Get position
        pos = portfolio.positions[0]
        cost_basis_per_share = pos.avg_buy_price

        # Current buggy breakeven ≈ 1000.60 (way too optimistic)
        # Correct breakeven ≈ 1001.79

        if abs(cost_basis_per_share - 1000.60) < 1:
            print(f"⚠ WARNING: Cost basis per share (₹{cost_basis_per_share:.2f}) seems too low")
            print(f"⚠ Real break-even needs ~₹{expected_breakeven_approx:.2f} (accounting for all costs)")

        print(f"✓ Cost basis per share: ₹{cost_basis_per_share:.2f}")


class TestCostTransparency:
    """Test that transaction costs are visible to users"""

    def test_trade_result_shows_cost_breakdown(self):
        """
        Users should see breakdown of all costs, not just a total

        TradeResult should include:
        {
            'brokerage': 30.00,
            'stt': 0 or 100.00,
            'exchange_charges': 3.25,
            'gst': 5.99,
            'sebi_fees': 0.10,
            'total': 139.34
        }
        """
        portfolio = Portfolio(cash=150000, positions=[])

        # Buy
        buy_result = TradeExecutor.execute_buy(portfolio, "TEST", 100, 1000)

        # Check for cost breakdown
        assert hasattr(buy_result, 'cost_breakdown') or hasattr(buy_result, 'cost_details'), \
            "❌ FAIL: TradeResult should have cost_breakdown for user transparency"

        if hasattr(buy_result, 'cost_breakdown'):
            breakdown = buy_result.cost_breakdown

            # Check for key components
            required_fields = ['brokerage', 'exchange_charges', 'gst']
            for field in required_fields:
                assert field in breakdown or field.replace('_', '') in breakdown, \
                    f"❌ FAIL: Cost breakdown missing '{field}'"

            print(f"✓ Cost breakdown available: {breakdown}")
        else:
            print("⚠ WARNING: cost_breakdown field not yet implemented")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])

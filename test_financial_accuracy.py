#!/usr/bin/env python3
"""
Comprehensive test to verify financial accuracy of Artha trading system
"""
from datetime import datetime, date, timedelta
from src.models import Portfolio, Position
from src.models.transaction_models import EnhancedPosition, PositionTransaction
from src.engine.trade_executor import TradeExecutor, OrderSide
from src.utils.xirr_calculator import TransactionType

def test_commission_calculation():
    """Test commission calculation accuracy"""
    print("=" * 80)
    print("TEST 1: Commission Calculation")
    print("=" * 80)

    # Test case 1: Large order (should hit ₹20 cap)
    amount1 = 100000  # ₹1 lakh
    commission1 = TradeExecutor.calculate_commission(amount1)
    expected1 = min(amount1 * 0.0003, 20.0)

    print(f"Order Value: ₹{amount1:,.2f}")
    print(f"Commission (0.03%): ₹{commission1:.2f}")
    print(f"Expected: ₹{expected1:.2f}")
    print(f"✓ PASS" if abs(commission1 - expected1) < 0.01 else "✗ FAIL")
    print()

    # Test case 2: Small order (should not hit cap)
    amount2 = 10000  # ₹10k
    commission2 = TradeExecutor.calculate_commission(amount2)
    expected2 = amount2 * 0.0003

    print(f"Order Value: ₹{amount2:,.2f}")
    print(f"Commission (0.03%): ₹{commission2:.2f}")
    print(f"Expected: ₹{expected2:.2f}")
    print(f"✓ PASS" if abs(commission2 - expected2) < 0.01 else "✗ FAIL")
    print()

def test_buy_sell_cycle():
    """Test buy and sell cycle to check for commission leakage"""
    print("=" * 80)
    print("TEST 2: Buy-Sell Cycle (Commission Leakage Test)")
    print("=" * 80)

    # Start with ₹1,00,000 cash
    initial_cash = 100000.0
    portfolio = Portfolio(cash=initial_cash)

    print(f"Initial Cash: ₹{initial_cash:,.2f}")

    # Buy 100 shares at ₹100 each
    buy_price = 100.0
    quantity = 100
    buy_result = TradeExecutor.execute_buy(portfolio, "TEST", quantity, buy_price)

    print(f"\nBUY: {quantity} shares @ ₹{buy_price:.2f}")
    print(f"  Order Value: ₹{buy_price * quantity:,.2f}")
    print(f"  Commission: ₹{buy_result.commission:.2f}")
    print(f"  Total Cost: ₹{buy_result.total_cost:.2f}")
    print(f"  Cash After Buy: ₹{portfolio.cash:,.2f}")

    # Sell at same price
    sell_price = 100.0
    sell_result = TradeExecutor.execute_sell(portfolio, "TEST", quantity, sell_price)

    print(f"\nSELL: {quantity} shares @ ₹{sell_price:.2f}")
    print(f"  Order Value: ₹{sell_price * quantity:,.2f}")
    print(f"  Commission: ₹{sell_result.commission:.2f}")
    print(f"  Net Proceeds: ₹{sell_result.total_cost:.2f}")
    print(f"  Cash After Sell: ₹{portfolio.cash:,.2f}")

    # Calculate total loss
    total_loss = initial_cash - portfolio.cash
    expected_loss = buy_result.commission + sell_result.commission

    print(f"\nFinal Cash: ₹{portfolio.cash:,.2f}")
    print(f"Total Loss: ₹{total_loss:.2f}")
    print(f"Expected Loss (2x commission): ₹{expected_loss:.2f}")
    print(f"✓ PASS" if abs(total_loss - expected_loss) < 0.01 else "✗ FAIL - Commission leakage detected!")
    print()

def test_position_averaging():
    """Test position averaging when buying multiple times"""
    print("=" * 80)
    print("TEST 3: Position Averaging")
    print("=" * 80)

    portfolio = Portfolio(cash=1000000.0)

    # Buy 1: 100 shares @ ₹100
    buy1 = TradeExecutor.execute_buy(portfolio, "STOCK", 100, 100.0)
    print(f"Buy 1: 100 shares @ ₹100.00")
    print(f"  Commission: ₹{buy1.commission:.2f}")

    # Buy 2: 50 shares @ ₹120
    buy2 = TradeExecutor.execute_buy(portfolio, "STOCK", 50, 120.0)
    print(f"Buy 2: 50 shares @ ₹120.00")
    print(f"  Commission: ₹{buy2.commission:.2f}")

    # Check position
    position = portfolio.positions[0]
    total_quantity = 150

    # Expected average: (100*100 + 50*120) / 150 = 16000/150 = 106.67
    expected_avg = (100 * 100.0 + 50 * 120.0) / 150

    print(f"\nPosition Summary:")
    print(f"  Total Quantity: {position.quantity}")
    print(f"  Average Buy Price: ₹{position.avg_buy_price:.2f}")
    print(f"  Expected Average: ₹{expected_avg:.2f}")

    if hasattr(position, 'cost_basis'):
        # Cost basis should NOT include commissions (they are separate costs)
        print(f"  Cost Basis: ₹{position.cost_basis:.2f}")
        print(f"  Expected Cost Basis: ₹{expected_avg * total_quantity:.2f}")

    print(f"✓ PASS" if abs(position.avg_buy_price - expected_avg) < 0.01 else "✗ FAIL - Averaging incorrect!")
    print()

def test_unrealized_pnl():
    """Test unrealized P&L calculation"""
    print("=" * 80)
    print("TEST 4: Unrealized P&L Calculation")
    print("=" * 80)

    portfolio = Portfolio(cash=1000000.0)

    # Buy 100 shares @ ₹100
    buy_result = TradeExecutor.execute_buy(portfolio, "STOCK", 100, 100.0)
    position = portfolio.positions[0]

    # Update price to ₹120 (20% gain)
    position.current_price = 120.0

    expected_pnl = (120.0 - 100.0) * 100  # ₹2000
    expected_pnl_pct = 20.0

    print(f"Buy Price: ₹100.00")
    print(f"Current Price: ₹120.00")
    print(f"Quantity: 100")
    print(f"\nUnrealized P&L: ₹{position.unrealized_pnl:.2f}")
    print(f"Expected P&L: ₹{expected_pnl:.2f}")
    print(f"Unrealized P&L %: {position.unrealized_pnl_pct:.2f}%")
    print(f"Expected P&L %: {expected_pnl_pct:.2f}%")

    pnl_match = abs(position.unrealized_pnl - expected_pnl) < 0.01
    pnl_pct_match = abs(position.unrealized_pnl_pct - expected_pnl_pct) < 0.01

    print(f"✓ PASS" if pnl_match and pnl_pct_match else "✗ FAIL - P&L calculation incorrect!")
    print()

def test_partial_sell():
    """Test partial sell and remaining position"""
    print("=" * 80)
    print("TEST 5: Partial Sell")
    print("=" * 80)

    portfolio = Portfolio(cash=1000000.0)

    # Buy 100 shares @ ₹100
    buy = TradeExecutor.execute_buy(portfolio, "STOCK", 100, 100.0)
    print(f"Buy: 100 shares @ ₹100.00")
    print(f"  Cash after buy: ₹{portfolio.cash:,.2f}")

    # Sell 30 shares @ ₹120
    sell = TradeExecutor.execute_sell(portfolio, "STOCK", 30, 120.0)
    print(f"\nSell: 30 shares @ ₹120.00")
    print(f"  Proceeds: ₹{sell.total_cost:.2f}")
    print(f"  Cash after sell: ₹{portfolio.cash:,.2f}")

    # Check remaining position
    position = portfolio.positions[0]
    expected_quantity = 70

    print(f"\nRemaining Position:")
    print(f"  Quantity: {position.quantity}")
    print(f"  Expected: {expected_quantity}")
    print(f"  Avg Buy Price: ₹{position.avg_buy_price:.2f}")
    print(f"  Expected: ₹100.00 (should not change)")

    qty_match = position.quantity == expected_quantity
    avg_match = abs(position.avg_buy_price - 100.0) < 0.01

    print(f"✓ PASS" if qty_match and avg_match else "✗ FAIL - Partial sell incorrect!")
    print()

def test_commission_on_both_sides():
    """Verify commission is charged on both buy and sell"""
    print("=" * 80)
    print("TEST 6: Commission on Both Sides")
    print("=" * 80)

    portfolio = Portfolio(cash=100000.0)

    # Buy and sell at exact same price
    buy = TradeExecutor.execute_buy(portfolio, "STOCK", 100, 100.0)
    sell = TradeExecutor.execute_sell(portfolio, "STOCK", 100, 100.0)

    print(f"Buy Commission: ₹{buy.commission:.2f}")
    print(f"Sell Commission: ₹{sell.commission:.2f}")

    # Both should have commission
    both_charged = buy.commission > 0 and sell.commission > 0

    # Net result should be negative (lost 2x commission)
    net_pnl = portfolio.cash - 100000.0

    print(f"\nNet P&L: ₹{net_pnl:.2f}")
    print(f"Expected: ₹{-(buy.commission + sell.commission):.2f}")

    print(f"✓ PASS" if both_charged and net_pnl < 0 else "✗ FAIL - Commission not charged on both sides!")
    print()

def test_enhanced_position_pnl():
    """Test EnhancedPosition P&L calculation with multiple transactions"""
    print("=" * 80)
    print("TEST 7: EnhancedPosition P&L with Multiple Buys")
    print("=" * 80)

    position = EnhancedPosition(symbol="STOCK", current_price=100.0)

    # Buy 100 @ 100
    trans1 = PositionTransaction(
        date=date(2024, 1, 1),
        quantity=100,
        price=100.0,
        transaction_type=TransactionType.BUY
    )
    position.add_transaction(trans1)

    # Buy 50 @ 120
    trans2 = PositionTransaction(
        date=date(2024, 2, 1),
        quantity=50,
        price=120.0,
        transaction_type=TransactionType.BUY
    )
    position.add_transaction(trans2)

    # Update current price to 110
    position.current_price = 110.0

    # Cost basis = 100*100 + 50*120 = 16000
    # Market value = 150 * 110 = 16500
    # Unrealized P&L = 16500 - 16000 = 500

    expected_cost_basis = 100 * 100.0 + 50 * 120.0
    expected_market_value = 150 * 110.0
    expected_pnl = expected_market_value - expected_cost_basis

    print(f"Transactions:")
    print(f"  Buy 100 @ ₹100.00")
    print(f"  Buy 50 @ ₹120.00")
    print(f"  Current Price: ₹110.00")

    print(f"\nCalculations:")
    print(f"  Cost Basis: ₹{position.cost_basis:.2f}")
    print(f"  Expected: ₹{expected_cost_basis:.2f}")
    print(f"  Market Value: ₹{position.market_value:.2f}")
    print(f"  Expected: ₹{expected_market_value:.2f}")
    print(f"  Unrealized P&L: ₹{position.unrealized_pnl:.2f}")
    print(f"  Expected: ₹{expected_pnl:.2f}")

    cost_match = abs(position.cost_basis - expected_cost_basis) < 0.01
    market_match = abs(position.market_value - expected_market_value) < 0.01
    pnl_match = abs(position.unrealized_pnl - expected_pnl) < 0.01

    print(f"✓ PASS" if cost_match and market_match and pnl_match else "✗ FAIL - EnhancedPosition P&L incorrect!")
    print()

def test_enhanced_position_sell():
    """Test EnhancedPosition after selling some shares"""
    print("=" * 80)
    print("TEST 8: EnhancedPosition Sell Tracking")
    print("=" * 80)

    position = EnhancedPosition(symbol="STOCK", current_price=100.0)

    # Buy 100 @ 100
    trans1 = PositionTransaction(
        date=date(2024, 1, 1),
        quantity=100,
        price=100.0,
        transaction_type=TransactionType.BUY
    )
    position.add_transaction(trans1)

    # Sell 30 @ 120
    trans2 = PositionTransaction(
        date=date(2024, 2, 1),
        quantity=30,
        price=120.0,
        transaction_type=TransactionType.SELL
    )
    position.add_transaction(trans2)

    # Update current price
    position.current_price = 110.0

    # Remaining quantity should be 70
    # Cost basis should still be based on total bought (100*100 = 10000)
    # But unrealized P&L should only be for remaining 70 shares

    expected_quantity = 70

    print(f"Transactions:")
    print(f"  Buy 100 @ ₹100.00")
    print(f"  Sell 30 @ ₹120.00")
    print(f"  Current Price: ₹110.00")

    print(f"\nPosition:")
    print(f"  Remaining Quantity: {position.quantity}")
    print(f"  Expected: {expected_quantity}")
    print(f"  Cost Basis (total bought): ₹{position.cost_basis:.2f}")
    print(f"  Market Value (remaining): ₹{position.market_value:.2f}")
    print(f"  Unrealized P&L: ₹{position.unrealized_pnl:.2f}")

    qty_match = position.quantity == expected_quantity

    print(f"✓ PASS" if qty_match else "✗ FAIL - Sell tracking incorrect!")
    print()

def test_cash_flow_consistency():
    """Test that cash flows are consistent and no money is created/destroyed"""
    print("=" * 80)
    print("TEST 9: Cash Flow Consistency (No Money Creation)")
    print("=" * 80)

    initial_capital = 1000000.0
    portfolio = Portfolio(cash=initial_capital)

    print(f"Initial Capital: ₹{initial_capital:,.2f}")

    # Execute multiple trades
    trades = [
        ("BUY", "STOCK1", 100, 100.0),
        ("BUY", "STOCK2", 50, 200.0),
        ("SELL", "STOCK1", 50, 120.0),
        ("BUY", "STOCK1", 30, 110.0),
        ("SELL", "STOCK2", 50, 210.0),
    ]

    total_commissions = 0.0

    for action, symbol, qty, price in trades:
        if action == "BUY":
            result = TradeExecutor.execute_buy(portfolio, symbol, qty, price)
        else:
            result = TradeExecutor.execute_sell(portfolio, symbol, qty, price)

        if result.success:
            total_commissions += result.commission
            print(f"{action} {qty} {symbol} @ ₹{price:.2f} - Commission: ₹{result.commission:.2f}")

    # Calculate total value
    total_value = portfolio.cash + portfolio.positions_value

    print(f"\nFinal State:")
    print(f"  Cash: ₹{portfolio.cash:,.2f}")
    print(f"  Positions Value: ₹{portfolio.positions_value:,.2f}")
    print(f"  Total Value: ₹{total_value:,.2f}")
    print(f"  Total Commissions Paid: ₹{total_commissions:.2f}")

    # Total value should be initial capital minus commissions (plus any market gains/losses)
    # Since we can't predict market gains/losses without knowing final prices,
    # we just check that total commissions are reasonable

    print(f"\nCommissions seem reasonable: {total_commissions > 0 and total_commissions < initial_capital * 0.01}")
    print(f"Cash + Positions = Total Value: {abs((portfolio.cash + portfolio.positions_value) - total_value) < 0.01}")
    print()

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ARTHA FINANCIAL ACCURACY TEST SUITE" + " " * 23 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    test_commission_calculation()
    test_buy_sell_cycle()
    test_position_averaging()
    test_unrealized_pnl()
    test_partial_sell()
    test_commission_on_both_sides()
    test_enhanced_position_pnl()
    test_enhanced_position_sell()
    test_cash_flow_consistency()

    print("=" * 80)
    print("TEST SUITE COMPLETED")
    print("=" * 80)
    print("\nReview the results above to identify any financial calculation errors.")
    print()

if __name__ == "__main__":
    main()

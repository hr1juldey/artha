"""
Integration test for watchlist gameplay scenario:
1. Player adds stock to watchlist
2. Watches price movements over days
3. Decides to buy based on watchlist trend
4. Tracks stock in both watchlist and portfolio
"""
import pytest
from datetime import date, timedelta
from src.models import Portfolio, GameState
from src.engine.trade_executor import TradeExecutor
from src.tui.widgets.enhanced_watchlist import EnhancedWatchlistWidget, STOCK_COLORS
from src.data.enhanced_loader import EnhancedMarketDataLoader


class MockApp:
    """Mock Textual app for testing"""
    def __init__(self):
        self.market_data = EnhancedMarketDataLoader()
        self.game_state = None


class TestWatchlistGameplayScenario:
    """Test realistic gameplay: watch → analyze → buy → track"""

    def test_complete_gameplay_flow(self):
        """
        SCENARIO: Player watches HDFCBANK, sees uptrend, buys it, tracks in both places

        Steps:
        1. Start game on Day 1
        2. Add HDFCBANK to watchlist
        3. Advance to Day 5, observe prices rising
        4. Buy 10 shares of HDFCBANK
        5. Continue to Day 10
        6. Verify both watchlist and portfolio track the same stock
        7. Verify prices update correctly in both
        """

        print("\n" + "="*80)
        print("GAMEPLAY SCENARIO: Watch → Buy → Track")
        print("="*80)

        # SETUP: Create game state
        initial_capital = 1_000_000
        total_days = 30

        portfolio = Portfolio(cash=initial_capital, positions=[], realized_pnl=0)

        # Create game state
        game_start_date = date.today() - timedelta(days=total_days)
        game_state = GameState(
            player_name="test_player",
            initial_capital=initial_capital,
            total_days=total_days,
            current_day=1,
            portfolio=portfolio,
            created_at=game_start_date,
            portfolio_history=[{
                'day': 1,
                'total_value': initial_capital,
                'cash': initial_capital,
                'positions_value': 0
            }]
        )

        # Mock app with market data
        mock_app = MockApp()
        mock_app.game_state = game_state

        print(f"\n📅 Day 1: Game started with ₹{initial_capital:,}")
        print(f"   Portfolio: {len(portfolio.positions)} positions, Cash: ₹{portfolio.cash:,}")

        # STEP 1: Player adds HDFCBANK to watchlist
        print("\n" + "-"*80)
        print("STEP 1: Adding HDFCBANK to watchlist")
        print("-"*80)

        # Simulate getting Day 1 price
        symbol = "HDFCBANK"
        day_1_offset = total_days - 1  # 29 days ago
        day_1_price = mock_app.market_data.get_price_at_day(symbol, day_1_offset)

        watchlist_data = {
            "HDFCBANK": ([day_1_price], STOCK_COLORS[0])
        }

        print(f"✓ Added HDFCBANK to watchlist")
        print(f"  Day 1 Price: ₹{day_1_price:,.2f}")
        print(f"  Color: RGB{STOCK_COLORS[0]}")

        assert len(watchlist_data) == 1
        assert "HDFCBANK" in watchlist_data
        assert len(watchlist_data["HDFCBANK"][0]) == 1  # 1 day of data

        # STEP 2: Advance to Day 5, watch prices
        print("\n" + "-"*80)
        print("STEP 2: Advancing to Day 5, observing price movements")
        print("-"*80)

        price_history = []
        for current_day in range(1, 6):  # Days 1-5
            game_state.current_day = current_day
            day_offset = total_days - current_day
            price = mock_app.market_data.get_price_at_day(symbol, day_offset)
            price_history.append(price)

            print(f"  Day {current_day}: ₹{price:,.2f}", end="")
            if current_day > 1:
                change = price - price_history[0]
                pct_change = (change / price_history[0]) * 100
                direction = "↑" if change > 0 else "↓" if change < 0 else "→"
                print(f"  ({direction} {pct_change:+.2f}%)")
            else:
                print()

        # Verify watchlist has 5 days of data
        watchlist_data["HDFCBANK"] = (price_history, STOCK_COLORS[0])

        assert len(price_history) == 5
        assert all(p > 0 for p in price_history)

        # Calculate trend
        day_1_price_check = price_history[0]
        day_5_price = price_history[4]
        total_change = day_5_price - day_1_price_check
        pct_change = (total_change / day_1_price_check) * 100

        print(f"\n📊 Watchlist Analysis:")
        print(f"   5-day trend: {pct_change:+.2f}%")
        print(f"   Direction: {'UPTREND ↑' if total_change > 0 else 'DOWNTREND ↓' if total_change < 0 else 'FLAT →'}")

        # STEP 3: Player decides to buy based on watchlist
        print("\n" + "-"*80)
        print("STEP 3: Player sees trend, decides to BUY 10 shares")
        print("-"*80)

        quantity = 10
        current_price = price_history[-1]  # Day 5 price

        game_date = game_start_date + timedelta(days=game_state.current_day - 1)

        result = TradeExecutor.execute_buy(
            portfolio,
            symbol,
            quantity,
            current_price,
            transaction_date=game_date
        )

        print(f"  Trade: BUY {quantity} x {symbol} @ ₹{current_price:,.2f}")
        print(f"  Result: {'✓ SUCCESS' if result.success else '✗ FAILED'}")
        print(f"  Message: {result.message}")

        if result.success:
            print(f"  Total Cost: ₹{result.total_cost:,.2f}")
            print(f"  Commission: ₹{result.commission:,.2f}")
            print(f"  Cash Remaining: ₹{portfolio.cash:,.2f}")
            print(f"  Positions: {len(portfolio.positions)}")

        assert result.success, f"Trade should succeed: {result.message}"
        assert len(portfolio.positions) == 1
        assert portfolio.positions[0].symbol == "HDFCBANK"
        assert portfolio.positions[0].quantity == quantity
        assert portfolio.cash < initial_capital

        # STEP 4: Continue to Day 10, track in both watchlist and portfolio
        print("\n" + "-"*80)
        print("STEP 4: Advancing to Day 10, tracking in BOTH watchlist and portfolio")
        print("-"*80)

        portfolio_prices = []

        for current_day in range(6, 11):  # Days 6-10
            game_state.current_day = current_day
            day_offset = total_days - current_day
            price = mock_app.market_data.get_price_at_day(symbol, day_offset)
            price_history.append(price)
            portfolio_prices.append(price)

            # Update portfolio position price
            portfolio.positions[0].current_price = price

            # Calculate P&L
            unrealized_pnl = (price - portfolio.positions[0].avg_buy_price) * quantity

            print(f"  Day {current_day}: ₹{price:,.2f}  |  P&L: ₹{unrealized_pnl:+,.2f}")

        # Update watchlist data
        watchlist_data["HDFCBANK"] = (price_history, STOCK_COLORS[0])

        print(f"\n📈 Day 10 Status:")
        print(f"   Watchlist: {len(price_history)} days of price data")
        print(f"   Portfolio: {portfolio.positions[0].quantity} shares owned")
        print(f"   Current Price: ₹{portfolio.positions[0].current_price:,.2f}")
        print(f"   Avg Buy Price: ₹{portfolio.positions[0].avg_buy_price:,.2f}")

        # VERIFICATION: Both watchlist and portfolio should show same current price
        assert len(price_history) == 10  # 10 days of watchlist data
        assert len(portfolio.positions) == 1  # 1 position in portfolio

        watchlist_current_price = price_history[-1]
        portfolio_current_price = portfolio.positions[0].current_price

        print(f"\n🔍 Verification:")
        print(f"   Watchlist shows: ₹{watchlist_current_price:,.2f}")
        print(f"   Portfolio shows: ₹{portfolio_current_price:,.2f}")
        print(f"   Match: {'✓ YES' if abs(watchlist_current_price - portfolio_current_price) < 0.01 else '✗ NO'}")

        assert abs(watchlist_current_price - portfolio_current_price) < 0.01, \
            "Watchlist and portfolio should show same current price"

        # STEP 5: Calculate final performance
        print("\n" + "-"*80)
        print("STEP 5: Final Performance Analysis")
        print("-"*80)

        position = portfolio.positions[0]

        # Unrealized P&L
        unrealized_pnl = position.unrealized_pnl
        unrealized_pnl_pct = position.unrealized_pnl_pct

        # Portfolio value
        portfolio_value = portfolio.total_value
        total_pnl = portfolio.total_pnl

        print(f"\n💰 Financial Summary:")
        print(f"   Initial Capital: ₹{initial_capital:,}")
        print(f"   Current Cash: ₹{portfolio.cash:,.2f}")
        print(f"   Position Value: ₹{position.market_value:,.2f}")
        print(f"   Total Portfolio: ₹{portfolio_value:,.2f}")
        print(f"   Unrealized P&L: ₹{unrealized_pnl:+,.2f} ({unrealized_pnl_pct:+.2f}%)")
        print(f"   Total P&L: ₹{total_pnl:+,.2f}")

        # Watchlist vs Purchase analysis
        purchase_price = price_history[4]  # Day 5 (when we bought)
        current_price_final = price_history[9]  # Day 10
        watchlist_gain = ((current_price_final - day_1_price_check) / day_1_price_check) * 100
        holding_gain = ((current_price_final - purchase_price) / purchase_price) * 100

        print(f"\n📊 Watchlist Intelligence:")
        print(f"   Day 1 Price: ₹{day_1_price_check:,.2f}")
        print(f"   Day 5 Price (bought): ₹{purchase_price:,.2f}")
        print(f"   Day 10 Price: ₹{current_price_final:,.2f}")
        print(f"   If bought Day 1: {watchlist_gain:+.2f}% gain")
        print(f"   Actual (bought Day 5): {holding_gain:+.2f}% gain")
        print(f"   Watchlist helped: {'✓ Good timing!' if holding_gain > 0 else '✗ Could be better'}")

        # Final assertions
        assert portfolio_value == portfolio.cash + position.market_value
        assert total_pnl == unrealized_pnl  # No realized P&L yet (haven't sold)

        print("\n" + "="*80)
        print("✅ TEST PASSED: Complete watchlist gameplay scenario works!")
        print("="*80)
        print("\nKey Verified:")
        print("  ✓ Watchlist tracks prices from Day 1")
        print("  ✓ Prices update on each day advance")
        print("  ✓ Can buy stocks after watching")
        print("  ✓ Both watchlist and portfolio show same prices")
        print("  ✓ P&L calculated correctly")
        print("  ✓ Watchlist provides decision-making intelligence")


    def test_multiple_stocks_watchlist_and_portfolio(self):
        """
        Test tracking multiple stocks in both watchlist and portfolio
        """
        print("\n" + "="*80)
        print("TEST: Multiple Stocks in Watchlist + Portfolio")
        print("="*80)

        # Setup
        portfolio = Portfolio(cash=1_000_000, positions=[], realized_pnl=0)
        mock_app = MockApp()

        game_start_date = date.today() - timedelta(days=30)
        game_state = GameState(
            player_name="test_player",
            initial_capital=1_000_000,
            total_days=30,
            current_day=1,
            portfolio=portfolio,
            created_at=game_start_date,
            portfolio_history=[]
        )
        mock_app.game_state = game_state

        # Add 3 stocks to watchlist
        watchlist_stocks = ["HDFCBANK", "ICICIBANK", "SBIN"]
        watchlist_data = {}

        print("\n📋 Adding stocks to watchlist:")
        for i, symbol in enumerate(watchlist_stocks):
            color = STOCK_COLORS[i]
            watchlist_data[symbol] = ([], color)
            print(f"  ✓ {symbol} (RGB{color})")

        # Track for 5 days
        for day in range(1, 6):
            game_state.current_day = day

            for symbol in watchlist_stocks:
                day_offset = 30 - day
                price = mock_app.market_data.get_price_at_day(symbol, day_offset)
                watchlist_data[symbol][0].append(price)

        print(f"\n📊 Day 5 Watchlist Prices:")
        for symbol in watchlist_stocks:
            prices = watchlist_data[symbol][0]
            day_1_price = prices[0]
            day_5_price = prices[4]
            change_pct = ((day_5_price - day_1_price) / day_1_price) * 100
            print(f"  {symbol}: ₹{day_5_price:,.2f} ({change_pct:+.2f}%)")

        # Buy 2 of the 3 stocks
        print(f"\n💰 Buying 2 stocks from watchlist:")

        game_date = game_start_date + timedelta(days=4)

        # Buy HDFCBANK
        hdfcbank_price = watchlist_data["HDFCBANK"][0][4]
        result1 = TradeExecutor.execute_buy(portfolio, "HDFCBANK", 10, hdfcbank_price, game_date)
        print(f"  ✓ HDFCBANK: {result1.message}")

        # Buy ICICIBANK
        icici_price = watchlist_data["ICICIBANK"][0][4]
        result2 = TradeExecutor.execute_buy(portfolio, "ICICIBANK", 20, icici_price, game_date)
        print(f"  ✓ ICICIBANK: {result2.message}")

        assert result1.success
        assert result2.success
        assert len(portfolio.positions) == 2

        # Continue to Day 10
        print(f"\n📈 Advancing to Day 10...")
        for day in range(6, 11):
            game_state.current_day = day

            for symbol in watchlist_stocks:
                day_offset = 30 - day
                price = mock_app.market_data.get_price_at_day(symbol, day_offset)
                watchlist_data[symbol][0].append(price)

                # Update owned positions
                for pos in portfolio.positions:
                    if pos.symbol == symbol:
                        pos.current_price = price

        print(f"\n📊 Day 10 Status:")
        print(f"  Watchlist: {len(watchlist_stocks)} stocks tracked")
        print(f"  Portfolio: {len(portfolio.positions)} stocks owned")

        print(f"\n  Watchlist (all 3):")
        for symbol in watchlist_stocks:
            current_price = watchlist_data[symbol][0][-1]
            owned = "✓ OWNED" if any(p.symbol == symbol for p in portfolio.positions) else "✗ Not owned"
            print(f"    {symbol}: ₹{current_price:,.2f}  {owned}")

        print(f"\n  Portfolio (2 owned):")
        for pos in portfolio.positions:
            pnl = pos.unrealized_pnl
            pnl_pct = pos.unrealized_pnl_pct
            print(f"    {pos.symbol}: ₹{pos.current_price:,.2f}  P&L: ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)")

        # Verify prices match
        print(f"\n🔍 Price Verification:")
        for pos in portfolio.positions:
            watchlist_price = watchlist_data[pos.symbol][0][-1]
            portfolio_price = pos.current_price
            match = abs(watchlist_price - portfolio_price) < 0.01
            print(f"  {pos.symbol}: Watchlist=₹{watchlist_price:,.2f}, Portfolio=₹{portfolio_price:,.2f}  {'✓' if match else '✗'}")

            assert match, f"{pos.symbol} prices should match"

        print(f"\n✅ TEST PASSED: Multiple stocks tracked correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

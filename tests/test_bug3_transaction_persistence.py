"""
Simple tests for Bug #3: Transaction Persistence

Tests that transactions are saved and loaded correctly using the async DAO pattern.
"""
import pytest
from datetime import date
from src.database import init_db, get_session
from src.database.dao import GameDAO, UserDAO
from src.database.models import Transaction
from src.models import Portfolio
from src.engine.trade_executor import TradeExecutor
from src.config import DEFAULT_USERNAME


@pytest.mark.asyncio
async def test_transaction_model_exists():
    """Test that Transaction model exists and can be imported"""
    # If we got here, import succeeded
    assert Transaction is not None
    print("✓ Transaction model exists")


@pytest.mark.asyncio
async def test_game_has_realized_pnl_field():
    """Test that Game model has realized_pnl field"""
    from src.database.models import Game
    assert hasattr(Game, 'realized_pnl'), "Game missing realized_pnl field"
    print("✓ Game has realized_pnl field")


@pytest.mark.asyncio
async def test_save_and_load_transactions():
    """
    CRITICAL TEST: Save transactions to database and reload them

    This tests the complete cycle:
    1. Create trades (which create transactions)
    2. Save to database using save_full_game_state
    3. Load from database
    4. Verify transactions are restored
    """
    await init_db()

    async for session in get_session():
        # Create test user and game
        user = await UserDAO.get_or_create_user(
            session,
            username="test_trans_user",
            full_name="Transaction Test User"
        )

        game = await GameDAO.create_game(
            session,
            user_id=user.id,
            name="Transaction Test",
            initial_capital=100000,
            total_days=30
        )

        # Create portfolio with transactions
        portfolio = Portfolio(cash=100000, positions=[], realized_pnl=0)

        # Execute multiple trades to create transaction history (use realistic prices)
        result1 = TradeExecutor.execute_buy(portfolio, "RELIANCE", 100, 500,
                                            transaction_date=date(2024, 1, 1))
        assert result1.success, f"Buy 1 failed: {result1.message}"

        result2 = TradeExecutor.execute_buy(portfolio, "RELIANCE", 50, 550,
                                            transaction_date=date(2024, 1, 15))
        assert result2.success, f"Buy 2 failed: {result2.message}"

        result3 = TradeExecutor.execute_sell(portfolio, "RELIANCE", 30, 600,
                                             transaction_date=date(2024, 1, 30))
        assert result3.success, f"Sell failed: {result3.message}"

        # Portfolio should have 1 position with 3 transactions
        assert len(portfolio.positions) == 1, f"Should have 1 position, got {len(portfolio.positions)}"
        pos = portfolio.positions[0]
        assert hasattr(pos, 'transactions'), "Position should have transactions"
        assert len(pos.transactions) == 3, f"Should have 3 transactions, got {len(pos.transactions)}"

        # Save using the comprehensive method
        await GameDAO.save_full_game_state(
            session,
            game.id,
            portfolio,
            current_day=30
        )

        print(f"✓ Saved game with {len(pos.transactions)} transactions")

        # Load game back
        loaded_game = await GameDAO.get_game(session, game.id)
        assert loaded_game is not None, "Game should load"

        # Convert to GameState
        game_state = GameDAO.db_game_to_game_state(loaded_game, user)
        loaded_portfolio = game_state.portfolio

        # Verify portfolio has the position
        assert len(loaded_portfolio.positions) == 1, "Loaded portfolio should have 1 position"

        # Verify the position has transactions
        loaded_pos = loaded_portfolio.positions[0]
        assert hasattr(loaded_pos, 'transactions'), "Loaded position missing transactions"
        assert len(loaded_pos.transactions) == 3, \
            f"Should have loaded 3 transactions, got {len(loaded_pos.transactions)}"

        # Verify transaction details are correct
        trans = sorted(loaded_pos.transactions, key=lambda t: t.date)
        assert trans[0].quantity == 100, f"First transaction quantity wrong: {trans[0].quantity}"
        assert trans[0].price == 500, f"First transaction price wrong: {trans[0].price}"
        assert trans[1].quantity == 50, "Second transaction quantity wrong"
        assert trans[1].price == 550, "Second transaction price wrong"
        assert trans[2].quantity == 30, "Third transaction quantity wrong"
        assert trans[2].price == 600, "Third transaction price wrong"

        print("✓ All 3 transactions loaded correctly with correct details")


@pytest.mark.asyncio
async def test_realized_pnl_persists():
    """Test that realized P&L is saved and loaded"""
    await init_db()

    async for session in get_session():
        # Create user and game
        user = await UserDAO.get_or_create_user(
            session,
            username="test_pnl_user",
            full_name="PNL Test User"
        )

        game = await GameDAO.create_game(
            session,
            user_id=user.id,
            name="PNL Test",
            initial_capital=100000,
            total_days=30
        )

        # Create portfolio and execute profitable trade
        portfolio = Portfolio(cash=100000, positions=[], realized_pnl=0)

        TradeExecutor.execute_buy(portfolio, "TEST", 100, 100)
        TradeExecutor.execute_sell(portfolio, "TEST", 100, 120)

        # Portfolio should have realized P&L
        assert portfolio.realized_pnl > 0, f"Should have positive P&L, got {portfolio.realized_pnl}"
        original_pnl = portfolio.realized_pnl

        # Save
        await GameDAO.save_full_game_state(session, game.id, portfolio, current_day=10)

        print(f"✓ Saved realized P&L: ₹{original_pnl:.2f}")

        # Load
        loaded_game = await GameDAO.get_game(session, game.id)
        game_state = GameDAO.db_game_to_game_state(loaded_game, user)

        # Verify realized P&L persisted
        loaded_pnl = game_state.portfolio.realized_pnl
        assert abs(loaded_pnl - original_pnl) < 0.01, \
            f"Realized P&L not preserved: {original_pnl} → {loaded_pnl}"

        print(f"✓ Realized P&L persisted correctly: ₹{loaded_pnl:.2f}")


@pytest.mark.asyncio
async def test_xirr_works_after_reload():
    """
    CRITICAL TEST: XIRR calculation should work after loading from database

    This was a major bug - XIRR used wrong dates after reload
    """
    await init_db()

    async for session in get_session():
        # Create user and game
        user = await UserDAO.get_or_create_user(
            session,
            username="test_xirr_user",
            full_name="XIRR Test User"
        )

        game = await GameDAO.create_game(
            session,
            user_id=user.id,
            name="XIRR Test",
            initial_capital=100000,
            total_days=180
        )

        # Create position with known dates
        portfolio = Portfolio(cash=100000, positions=[])
        buy_date = date(2024, 1, 1)
        current_date = date(2024, 7, 1)  # 6 months later

        TradeExecutor.execute_buy(portfolio, "RELIANCE", 100, 500,
                                  transaction_date=buy_date)

        # Update current price
        pos = portfolio.positions[0]
        pos.current_price = 600  # 20% gain (500 * 1.20)

        # Calculate XIRR before save
        xirr_before = pos.calculate_xirr(current_date)
        assert xirr_before > 0, "XIRR should be positive"

        print(f"✓ XIRR before save: {xirr_before:.4f}")

        # Save
        await GameDAO.save_full_game_state(session, game.id, portfolio, current_day=180)

        # Load
        loaded_game = await GameDAO.get_game(session, game.id)
        game_state = GameDAO.db_game_to_game_state(loaded_game, user)
        loaded_pos = game_state.portfolio.positions[0]

        # Set current price (would be set by market data in real app)
        loaded_pos.current_price = 600

        # Calculate XIRR after load
        xirr_after = loaded_pos.calculate_xirr(current_date)

        # XIRRs should be very close
        assert abs(xirr_before - xirr_after) < 0.01, \
            f"XIRR changed after reload: {xirr_before:.4f} → {xirr_after:.4f}"

        print(f"✓ XIRR after load: {xirr_after:.4f} (preserved!)")


@pytest.mark.asyncio
async def test_multiple_positions_transactions():
    """Test that multiple positions each keep their own transactions"""
    await init_db()

    async for session in get_session():
        user = await UserDAO.get_or_create_user(session, username="test_multi", full_name="Multi Test")
        game = await GameDAO.create_game(session, user_id=user.id, name="Multi Test", initial_capital=200000, total_days=30)

        portfolio = Portfolio(cash=200000, positions=[])

        # Create multiple positions with different transaction counts
        TradeExecutor.execute_buy(portfolio, "RELIANCE", 100, 400)
        TradeExecutor.execute_buy(portfolio, "RELIANCE", 50, 420)  # RELIANCE has 2 buys

        TradeExecutor.execute_buy(portfolio, "SBIN", 200, 300)
        TradeExecutor.execute_sell(portfolio, "SBIN", 50, 320)  # SBIN has 1 buy + 1 sell

        # Save
        await GameDAO.save_full_game_state(session, game.id, portfolio, current_day=30)

        # Load
        loaded_game = await GameDAO.get_game(session, game.id)
        game_state = GameDAO.db_game_to_game_state(loaded_game, user)

        # Verify both positions exist
        assert len(game_state.portfolio.positions) == 2, "Should have 2 positions"

        # Find positions
        rel_pos = next(p for p in game_state.portfolio.positions if p.symbol == "RELIANCE")
        sbin_pos = next(p for p in game_state.portfolio.positions if p.symbol == "SBIN")

        # Verify transaction counts
        assert len(rel_pos.transactions) == 2, \
            f"RELIANCE should have 2 transactions, got {len(rel_pos.transactions)}"
        assert len(sbin_pos.transactions) == 2, \
            f"SBIN should have 2 transactions, got {len(sbin_pos.transactions)}"

        print("✓ Multiple positions with separate transaction histories preserved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

"""Tests for the database functionality"""
import pytest
import asyncio
from src.database import init_db, get_session
from src.database.dao import UserDAO, GameDAO
from src.models import Position as PositionModel
from src.config import DEFAULT_USERNAME


@pytest.mark.asyncio
async def test_database_operations():
    """Test basic database operations."""
    # Initialize database
    await init_db()
    
    async for session in get_session():
        # Test user creation/get
        user = await UserDAO.get_or_create_user(
            session, 
            username=DEFAULT_USERNAME,
            full_name="Test User"
        )
        assert user.username == DEFAULT_USERNAME
        
        # Test game creation
        game = await GameDAO.create_game(
            session,
            user_id=user.id,
            name="Test Game",
            initial_capital=1000000.0,
            total_days=30
        )
        assert game.name == "Test Game"
        assert game.current_cash == 1000000.0
        
        # Test position saving
        positions = [
            PositionModel(
                symbol="RELIANCE",
                quantity=50,
                avg_buy_price=2450.00,
                current_price=2520.00
            )
        ]
        await GameDAO.save_positions(session, game.id, positions)
        
        # Test game loading with positions
        loaded_game = await GameDAO.get_game(session, game.id)
        assert len(loaded_game.positions) == 1
        assert loaded_game.positions[0].symbol == "RELIANCE"
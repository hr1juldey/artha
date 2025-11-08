"""Data Access Objects for database operations"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from src.database.models import User, Game, Position
from src.models import GameState, Portfolio, Position as PositionModel

class GameDAO:
    """Data Access Object for Game operations"""

    @staticmethod
    async def create_game(
        session: AsyncSession,
        user_id: int,
        name: str,
        initial_capital: float,
        total_days: int
    ) -> Game:
        """Create a new game"""
        game = Game(
            user_id=user_id,
            name=name,
            initial_capital=initial_capital,
            current_cash=initial_capital,
            total_days=total_days
        )
        session.add(game)
        await session.commit()
        await session.refresh(game)
        return game

    @staticmethod
    async def get_game(session: AsyncSession, game_id: int) -> Optional[Game]:
        """Get game by ID with positions loaded"""
        result = await session.execute(
            select(Game)
            .options(selectinload(Game.positions))
            .where(Game.id == game_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_games(session: AsyncSession, user_id: int) -> List[Game]:
        """Get all games for a user"""
        result = await session.execute(
            select(Game)
            .where(Game.user_id == user_id)
            .order_by(Game.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_game(session: AsyncSession, user_id: int) -> Optional[Game]:
        """Get user's most recent game"""
        result = await session.execute(
            select(Game)
            .options(selectinload(Game.positions))
            .where(Game.user_id == user_id)
            .order_by(Game.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def save_game_state(
        session: AsyncSession,
        game_id: int,
        cash: float,
        current_day: int
    ) -> None:
        """Update game state"""
        result = await session.execute(
            select(Game).where(Game.id == game_id)
        )
        game = result.scalar_one()
        game.current_cash = cash
        game.current_day = current_day
        await session.commit()

    @staticmethod
    async def save_positions(
        session: AsyncSession,
        game_id: int,
        positions: List[PositionModel]
    ) -> None:
        """Save portfolio positions - UPDATE/INSERT/DELETE pattern"""

        # Step 1: Get existing positions from database
        result = await session.execute(
            select(Position).where(Position.game_id == game_id)
        )
        existing_positions = {pos.symbol: pos for pos in result.scalars().all()}

        # Step 2: Update existing or insert new positions
        for pos in positions:
            if pos.symbol in existing_positions:
                # UPDATE existing position (no constraint violation)
                db_pos = existing_positions[pos.symbol]
                db_pos.quantity = pos.quantity
                db_pos.avg_buy_price = pos.avg_buy_price
                db_pos.current_price = pos.current_price
                # Mark as processed
                del existing_positions[pos.symbol]
            else:
                # INSERT new position
                db_pos = Position(
                    game_id=game_id,
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    avg_buy_price=pos.avg_buy_price,
                    current_price=pos.current_price
                )
                session.add(db_pos)

        # Step 3: Delete positions that no longer exist (sold all shares)
        for symbol, db_pos in existing_positions.items():
            await session.delete(db_pos)

        # Step 4: Commit all changes
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    @staticmethod
    def db_game_to_game_state(game: Game, user: User) -> GameState:
        """Convert DB Game to GameState model"""
        positions = [
            PositionModel(
                symbol=pos.symbol,
                quantity=pos.quantity,
                avg_buy_price=pos.avg_buy_price,
                current_price=pos.current_price or pos.avg_buy_price
            )
            for pos in game.positions
        ]

        portfolio = Portfolio(
            cash=game.current_cash,
            positions=positions
        )

        game_state = GameState(
            player_name=user.full_name or user.username,
            current_day=game.current_day,
            total_days=game.total_days,
            initial_capital=game.initial_capital,
            portfolio=portfolio,
            created_at=game.created_at
        )

        # Initialize portfolio_history with current state
        # (Full history is not persisted, so we start with current snapshot)
        game_state.portfolio_history = [{
            "day": game.current_day,
            "total_value": portfolio.total_value,
            "cash": portfolio.cash,
            "positions_value": portfolio.positions_value,
            "pnl": portfolio.total_pnl
        }]

        return game_state

class UserDAO:
    """Data Access Object for User operations"""

    @staticmethod
    async def create_user(
        session: AsyncSession,
        username: str,
        full_name: str = None,
        email: str = None
    ) -> User:
        """Create a new user"""
        user = User(
            username=username,
            full_name=full_name,
            email=email
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_user_by_username(
        session: AsyncSession,
        username: str
    ) -> Optional[User]:
        """Get user by username"""
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        username: str,
        full_name: str = None
    ) -> User:
        """Get existing user or create new one"""
        user = await UserDAO.get_user_by_username(session, username)
        if not user:
            user = await UserDAO.create_user(session, username, full_name)
        return user
"""Data Access Objects for database operations"""
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional, Union
from datetime import datetime
from src.database.models import User, Game, Position, Transaction
from src.models import GameState, Portfolio, Position as PositionModel
from src.models.transaction_models import EnhancedPosition, PositionTransaction
from src.utils.xirr_calculator import TransactionType

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
        """Get game by ID with positions and transactions loaded"""
        result = await session.execute(
            select(Game)
            .options(selectinload(Game.positions))
            .options(selectinload(Game.transactions))
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
            .options(selectinload(Game.transactions))
            .where(Game.user_id == user_id)
            .order_by(Game.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def save_full_game_state(
        session: AsyncSession,
        game_id: int,
        portfolio: Portfolio,
        current_day: int
    ) -> None:
        """Save complete game state: cash, realized_pnl, positions, and transactions"""
        # Update game state
        result = await session.execute(
            select(Game).where(Game.id == game_id)
        )
        game = result.scalar_one()
        game.current_cash = portfolio.cash
        game.current_day = current_day
        game.realized_pnl = portfolio.realized_pnl
        await session.commit()

        # Save positions
        await GameDAO.save_positions(session, game_id, portfolio.positions)

        # Save transactions
        await GameDAO.save_transactions(session, game_id, portfolio.positions)

    @staticmethod
    async def save_game_state(
        session: AsyncSession,
        game_id: int,
        cash: float,
        current_day: int,
        realized_pnl: float = 0.0
    ) -> None:
        """Update game state including realized P&L (legacy method - prefer save_full_game_state)"""
        result = await session.execute(
            select(Game).where(Game.id == game_id)
        )
        game = result.scalar_one()
        game.current_cash = cash
        game.current_day = current_day
        game.realized_pnl = realized_pnl
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
    async def save_transactions(
        session: AsyncSession,
        game_id: int,
        positions: List[Union[PositionModel, EnhancedPosition]]
    ) -> None:
        """Save transaction history for all positions"""

        # Step 1: Delete existing transactions for this game
        await session.execute(
            delete(Transaction).where(Transaction.game_id == game_id)
        )

        # Step 2: Insert all transactions from EnhancedPosition objects
        for pos in positions:
            # Only EnhancedPosition has transactions
            if hasattr(pos, 'transactions') and hasattr(pos, 'symbol'):
                for trans in pos.transactions:
                    # Convert transaction_type enum to string
                    trans_type = trans.transaction_type.value if hasattr(trans.transaction_type, 'value') else str(trans.transaction_type)

                    # Convert date to datetime if needed
                    if hasattr(trans.date, 'date'):
                        # It's already a datetime
                        trans_date = trans.date
                    else:
                        # It's a date, convert to datetime
                        trans_date = datetime.combine(trans.date, datetime.min.time())

                    db_trans = Transaction(
                        game_id=game_id,
                        symbol=pos.symbol,
                        quantity=trans.quantity,
                        price=trans.price,
                        transaction_type=trans_type,
                        transaction_date=trans_date,
                        commission=trans.commission if hasattr(trans, 'commission') else 0.0
                    )
                    session.add(db_trans)

        # Step 3: Commit all transactions
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    @staticmethod
    def db_game_to_game_state(game: Game, user: User) -> GameState:
        """Convert DB Game to GameState model with transaction history"""

        # Group transactions by symbol
        transactions_by_symbol = {}
        for db_trans in game.transactions:
            if db_trans.symbol not in transactions_by_symbol:
                transactions_by_symbol[db_trans.symbol] = []

            # Convert DB transaction to PositionTransaction
            trans_type = TransactionType.BUY if db_trans.transaction_type == "BUY" else TransactionType.SELL
            trans_date = db_trans.transaction_date.date() if hasattr(db_trans.transaction_date, 'date') else db_trans.transaction_date

            pos_trans = PositionTransaction(
                date=trans_date,
                quantity=db_trans.quantity,
                price=db_trans.price,
                transaction_type=trans_type,
                commission=db_trans.commission
            )
            transactions_by_symbol[db_trans.symbol].append(pos_trans)

        # Build positions with transaction history
        positions = []
        for pos in game.positions:
            # Get current price from DB position or use avg_buy_price as fallback
            current_price = pos.current_price or pos.avg_buy_price

            # If we have transaction history for this symbol, create EnhancedPosition
            if pos.symbol in transactions_by_symbol:
                enhanced_pos = EnhancedPosition(
                    symbol=pos.symbol,
                    current_price=current_price,
                    transactions=transactions_by_symbol[pos.symbol]
                )
                positions.append(enhanced_pos)
            else:
                # Fallback to legacy Position if no transaction history
                legacy_pos = PositionModel(
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    avg_buy_price=pos.avg_buy_price,
                    current_price=current_price
                )
                positions.append(legacy_pos)

        portfolio = Portfolio(
            cash=game.current_cash,
            positions=positions,
            realized_pnl=game.realized_pnl if hasattr(game, 'realized_pnl') else 0.0
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
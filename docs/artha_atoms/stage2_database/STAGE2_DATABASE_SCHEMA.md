# Stage 2: Database Schema & Patterns

**Supplement to**: STAGE2_OVERVIEW.md
**Purpose**: Detailed database schema, relationships, and SQLAlchemy patterns

---

## Database Technology

- **ORM**: SQLAlchemy 2.0+ (async style)
- **Database**: SQLite (local file: `data/artha.db`)
- **Driver**: aiosqlite (async SQLite driver)

---

## Complete Database Schema

### Entity-Relationship Diagram

```
┌─────────────────┐
│      User       │
│─────────────────│
│ id (PK)         │
│ username        │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│      Game       │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │
│ start_date      │
│ current_day     │
│ initial_capital │
│ current_cash    │
│ is_active       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│    Position     │
│─────────────────│
│ id (PK)         │
│ game_id (FK)    │
│ symbol          │
│ quantity        │
│ avg_buy_price   │
│ created_at      │
│ updated_at      │
└─────────────────┘
```

---

## SQLAlchemy Model Definitions

### Complete Models with Type Hints

```python
"""Database models using SQLAlchemy 2.0"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

class User(Base):
    """User account"""
    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Fields
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    games: Mapped[List["Game"]] = relationship(
        "Game",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"

class Game(Base):
    """Game session"""
    __tablename__ = "games"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Game State Fields
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, nullable=False)
    current_cash: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="games", lazy="selectin")
    positions: Mapped[List["Position"]] = relationship(
        "Position",
        back_populates="game",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Game(id={self.id}, user_id={self.user_id}, day={self.current_day}, active={self.is_active})>"

class Position(Base):
    """Stock position in a game"""
    __tablename__ = "positions"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), nullable=False, index=True)

    # Position Fields
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_buy_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="positions", lazy="selectin")

    # Composite Index for fast lookups
    __table_args__ = (
        # Unique constraint: one position per symbol per game
        # Actually, we want to allow multiple positions, so no unique constraint
    )

    def __repr__(self) -> str:
        return f"<Position(id={self.id}, game_id={self.game_id}, symbol='{self.symbol}', qty={self.quantity})>"
```

---

## Database Connection Patterns

### Connection Manager

```python
"""Database connection management"""
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from src.database.models import Base

class DatabaseConnection:
    """Manages database connection and sessions"""

    def __init__(self, db_path: Path):
        """Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create async engine with SQLite
        # Note: sqlite+aiosqlite:/// for async SQLite
        self.engine: AsyncEngine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,  # Set to True for SQL debugging
            future=True,
            pool_pre_ping=True,  # Verify connections before using
        )

        # Create session factory
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Manual control over flushing
            autocommit=False,  # Explicit commits
        )

    async def create_tables(self) -> None:
        """Create all tables if they don't exist"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables (for testing)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session (async context manager)

        Usage:
            async with db.get_session() as session:
                # Use session here
                await session.commit()
        """
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database connection"""
        await self.engine.dispose()
```

---

## Data Access Object (DAO) Patterns

### Complete GameDAO Implementation

```python
"""Data Access Object for Game operations"""
from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from src.database.models import User, Game, Position

class GameDAO:
    """Data access for game operations"""

    def __init__(self, session: AsyncSession):
        """Initialize DAO with session

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    # ==================== USER OPERATIONS ====================

    async def create_user(self, username: str) -> User:
        """Create new user

        Args:
            username: Unique username

        Returns:
            Created User object

        Raises:
            IntegrityError: If username already exists
        """
        user = User(username=username)
        self.session.add(user)
        await self.session.flush()  # Get ID without committing
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username

        Args:
            username: Username to search

        Returns:
            User if found, None otherwise
        """
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_user(self, username: str) -> User:
        """Get existing user or create new one

        Args:
            username: Username

        Returns:
            User object (existing or new)
        """
        user = await self.get_user_by_username(username)
        if user is None:
            user = await self.create_user(username)
            await self.session.commit()
        return user

    # ==================== GAME OPERATIONS ====================

    async def create_game(
        self,
        user_id: int,
        initial_capital: float,
        start_date: datetime
    ) -> Game:
        """Create new game

        Args:
            user_id: User ID
            initial_capital: Starting cash
            start_date: Game start date

        Returns:
            Created Game object
        """
        game = Game(
            user_id=user_id,
            initial_capital=initial_capital,
            current_cash=initial_capital,
            start_date=start_date,
            current_day=1,
            is_active=True
        )
        self.session.add(game)
        await self.session.flush()
        return game

    async def get_game_by_id(self, game_id: int) -> Optional[Game]:
        """Get game by ID with all relationships loaded

        Args:
            game_id: Game ID

        Returns:
            Game with positions and user loaded, or None
        """
        stmt = (
            select(Game)
            .where(Game.id == game_id)
            .options(
                selectinload(Game.positions),
                selectinload(Game.user)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_game_for_user(self, user_id: int) -> Optional[Game]:
        """Get active game for user

        Args:
            user_id: User ID

        Returns:
            Active Game if exists, None otherwise
        """
        stmt = (
            select(Game)
            .where(Game.user_id == user_id, Game.is_active == True)
            .options(selectinload(Game.positions))
            .order_by(Game.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_game_state(
        self,
        game_id: int,
        current_day: Optional[int] = None,
        current_cash: Optional[float] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update game state fields

        Args:
            game_id: Game ID
            current_day: New day number (if updating)
            current_cash: New cash amount (if updating)
            is_active: New active status (if updating)

        Returns:
            True if updated, False if game not found
        """
        update_values = {"updated_at": datetime.utcnow()}

        if current_day is not None:
            update_values["current_day"] = current_day
        if current_cash is not None:
            update_values["current_cash"] = current_cash
        if is_active is not None:
            update_values["is_active"] = is_active

        stmt = (
            update(Game)
            .where(Game.id == game_id)
            .values(**update_values)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_games_for_user(
        self,
        user_id: int,
        active_only: bool = False
    ) -> List[Game]:
        """List all games for user

        Args:
            user_id: User ID
            active_only: Only return active games

        Returns:
            List of Game objects
        """
        stmt = select(Game).where(Game.user_id == user_id)

        if active_only:
            stmt = stmt.where(Game.is_active == True)

        stmt = stmt.order_by(Game.updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ==================== POSITION OPERATIONS ====================

    async def create_position(
        self,
        game_id: int,
        symbol: str,
        quantity: int,
        avg_buy_price: float
    ) -> Position:
        """Create new position

        Args:
            game_id: Game ID
            symbol: Stock symbol
            quantity: Number of shares
            avg_buy_price: Average buy price

        Returns:
            Created Position object
        """
        position = Position(
            game_id=game_id,
            symbol=symbol,
            quantity=quantity,
            avg_buy_price=avg_buy_price
        )
        self.session.add(position)
        await self.session.flush()
        return position

    async def get_position(
        self,
        game_id: int,
        symbol: str
    ) -> Optional[Position]:
        """Get position for game and symbol

        Args:
            game_id: Game ID
            symbol: Stock symbol

        Returns:
            Position if found, None otherwise
        """
        stmt = (
            select(Position)
            .where(Position.game_id == game_id, Position.symbol == symbol)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_position(
        self,
        position_id: int,
        quantity: int,
        avg_buy_price: float
    ) -> bool:
        """Update position

        Args:
            position_id: Position ID
            quantity: New quantity
            avg_buy_price: New average buy price

        Returns:
            True if updated, False if not found
        """
        stmt = (
            update(Position)
            .where(Position.id == position_id)
            .values(
                quantity=quantity,
                avg_buy_price=avg_buy_price,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def delete_position(self, position_id: int) -> bool:
        """Delete position (when quantity reaches 0)

        Args:
            position_id: Position ID

        Returns:
            True if deleted, False if not found
        """
        stmt = delete(Position).where(Position.id == position_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_positions_for_game(self, game_id: int) -> List[Position]:
        """Get all positions for a game

        Args:
            game_id: Game ID

        Returns:
            List of Position objects
        """
        stmt = (
            select(Position)
            .where(Position.game_id == game_id)
            .order_by(Position.symbol)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

---

## Usage Patterns

### Pattern 1: Creating New Game

```python
async def create_new_game_flow():
    """Complete flow for creating new game"""
    from src.config import DATA_DIR
    from src.database.connection import DatabaseConnection
    from src.database.dao import GameDAO
    from datetime import datetime

    # Initialize database
    db_path = DATA_DIR / "artha.db"
    db = DatabaseConnection(db_path)
    await db.create_tables()

    # Get session
    async with db.get_session() as session:
        dao = GameDAO(session)

        # Get or create user
        user = await dao.get_or_create_user("player1")

        # Create game
        game = await dao.create_game(
            user_id=user.id,
            initial_capital=1000000.0,
            start_date=datetime.now()
        )

        # Commit transaction
        await session.commit()

        print(f"Created game {game.id} for user {user.username}")
        return game.id
```

### Pattern 2: Loading Existing Game

```python
async def load_game_flow(game_id: int):
    """Load existing game with all data"""
    from src.config import DATA_DIR
    from src.database.connection import DatabaseConnection
    from src.database.dao import GameDAO

    db_path = DATA_DIR / "artha.db"
    db = DatabaseConnection(db_path)

    async with db.get_session() as session:
        dao = GameDAO(session)

        # Load game with positions
        game = await dao.get_game_by_id(game_id)

        if game is None:
            print(f"Game {game_id} not found")
            return None

        print(f"Loaded game {game.id}")
        print(f"  Day: {game.current_day}")
        print(f"  Cash: ₹{game.current_cash:,.2f}")
        print(f"  Positions: {len(game.positions)}")

        for position in game.positions:
            print(f"    {position.symbol}: {position.quantity} @ ₹{position.avg_buy_price:.2f}")

        return game
```

### Pattern 3: Updating Position After Trade

```python
async def update_position_after_buy(game_id: int, symbol: str, quantity: int, price: float):
    """Update or create position after buy trade"""
    from src.config import DATA_DIR
    from src.database.connection import DatabaseConnection
    from src.database.dao import GameDAO

    db_path = DATA_DIR / "artha.db"
    db = DatabaseConnection(db_path)

    async with db.get_session() as session:
        dao = GameDAO(session)

        # Check if position exists
        position = await dao.get_position(game_id, symbol)

        if position is None:
            # Create new position
            position = await dao.create_position(
                game_id=game_id,
                symbol=symbol,
                quantity=quantity,
                avg_buy_price=price
            )
            print(f"Created new position: {symbol}")
        else:
            # Update existing position (average down/up)
            total_quantity = position.quantity + quantity
            total_cost = (position.quantity * position.avg_buy_price) + (quantity * price)
            new_avg_price = total_cost / total_quantity

            await dao.update_position(
                position_id=position.id,
                quantity=total_quantity,
                avg_buy_price=new_avg_price
            )
            print(f"Updated position: {symbol} (new avg: ₹{new_avg_price:.2f})")

        await session.commit()
```

### Pattern 4: Transaction Management

```python
async def safe_trade_execution():
    """Demonstrate transaction rollback on error"""
    from src.config import DATA_DIR
    from src.database.connection import DatabaseConnection
    from src.database.dao import GameDAO

    db_path = DATA_DIR / "artha.db"
    db = DatabaseConnection(db_path)

    try:
        async with db.get_session() as session:
            dao = GameDAO(session)

            # Multiple operations in one transaction
            game = await dao.get_game_by_id(1)

            # Update cash
            new_cash = game.current_cash - 10000
            if new_cash < 0:
                raise ValueError("Insufficient funds")

            await dao.update_game_state(game.id, current_cash=new_cash)

            # Create position
            await dao.create_position(
                game_id=game.id,
                symbol="RELIANCE",
                quantity=10,
                avg_buy_price=2500.0
            )

            # Commit all or nothing
            await session.commit()
            print("Trade executed successfully")

    except ValueError as e:
        # Transaction automatically rolled back
        print(f"Trade failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

---

## Migration Strategy

### Initial Migration (Stage 2)

```python
async def initialize_database():
    """Initialize database on first run"""
    from pathlib import Path
    from src.config import DATA_DIR
    from src.database.connection import DatabaseConnection

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    db_path = DATA_DIR / "artha.db"
    db = DatabaseConnection(db_path)

    # Create all tables
    await db.create_tables()

    print(f"Database initialized at {db_path}")

    await db.close()
```

### Future Migrations (if schema changes)

For future schema changes, use Alembic:

```bash
# Initialize Alembic (do once)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head
```

But for this 12-hour project, just drop and recreate for testing:

```python
async def reset_database_for_testing():
    """Reset database (DESTRUCTIVE - for testing only)"""
    from src.config import DATA_DIR
    from src.database.connection import DatabaseConnection

    db_path = DATA_DIR / "artha.db"
    db = DatabaseConnection(db_path)

    await db.drop_tables()
    await db.create_tables()

    print("Database reset complete")
    await db.close()
```

---

## Testing Patterns

### Test Database Setup

```python
import pytest
from pathlib import Path
from src.database.connection import DatabaseConnection
from src.database.dao import GameDAO

@pytest.fixture
async def test_db():
    """Create test database"""
    db_path = Path("test_artha.db")
    db = DatabaseConnection(db_path)
    await db.create_tables()

    yield db

    # Cleanup
    await db.close()
    db_path.unlink(missing_ok=True)

@pytest.fixture
async def test_dao(test_db):
    """Create DAO for testing"""
    async with test_db.get_session() as session:
        yield GameDAO(session)

@pytest.mark.asyncio
async def test_create_user(test_dao):
    """Test user creation"""
    user = await test_dao.create_user("testuser")
    assert user.id is not None
    assert user.username == "testuser"

@pytest.mark.asyncio
async def test_create_and_load_game(test_dao):
    """Test game creation and loading"""
    from datetime import datetime

    # Create user
    user = await test_dao.create_user("player1")

    # Create game
    game = await test_dao.create_game(
        user_id=user.id,
        initial_capital=1000000.0,
        start_date=datetime.now()
    )

    await test_dao.session.commit()

    # Load game
    loaded = await test_dao.get_game_by_id(game.id)
    assert loaded is not None
    assert loaded.current_cash == 1000000.0
```

---

## Performance Considerations

### Indexes

Already defined in models:
- `User.username` - unique index (for login lookups)
- `Game.user_id` - index (for user's games)
- `Game.is_active` - index (for active game queries)
- `Position.game_id` - index (for position lookups)
- `Position.symbol` - index (for symbol searches)

### Query Optimization

1. **Use selectinload for relationships**: Already configured in models with `lazy="selectin"`
2. **Batch operations**: When updating multiple positions, do in single transaction
3. **Avoid N+1 queries**: Load all positions with game in single query

### Connection Pooling

SQLite doesn't need complex pooling, but configuration is ready for PostgreSQL migration if needed.

---

## Common Patterns Summary

| Operation | Method | Transaction Required |
|-----------|--------|---------------------|
| Create user | `dao.create_user()` | Yes (commit) |
| Get user | `dao.get_user_by_username()` | No (read-only) |
| Create game | `dao.create_game()` | Yes (commit) |
| Load game | `dao.get_game_by_id()` | No (read-only) |
| Update game | `dao.update_game_state()` | Yes (commit) |
| Add position | `dao.create_position()` | Yes (commit) |
| Update position | `dao.update_position()` | Yes (commit) |
| Delete position | `dao.delete_position()` | Yes (commit) |

---

## Integration with Stage 1 Models

### Converting Between Database and Domain Models

```python
from src.models import Portfolio, Position as DomainPosition
from src.database.models import Game, Position as DBPosition

def game_to_portfolio(game: Game, current_prices: dict[str, float]) -> Portfolio:
    """Convert database Game to domain Portfolio

    Args:
        game: Database Game object with positions loaded
        current_prices: Dict of symbol -> current price

    Returns:
        Portfolio domain object
    """
    positions = []

    for db_pos in game.positions:
        current_price = current_prices.get(db_pos.symbol, 0.0)

        domain_pos = DomainPosition(
            symbol=db_pos.symbol,
            quantity=db_pos.quantity,
            avg_buy_price=db_pos.avg_buy_price,
            current_price=current_price
        )
        positions.append(domain_pos)

    return Portfolio(
        cash=game.current_cash,
        positions=positions
    )

def portfolio_to_game_update(
    game_id: int,
    portfolio: Portfolio,
    dao: GameDAO
) -> None:
    """Save portfolio changes to database

    Args:
        game_id: Game ID to update
        portfolio: Domain Portfolio object
        dao: GameDAO instance
    """
    # Update game cash
    await dao.update_game_state(game_id, current_cash=portfolio.cash)

    # Update each position
    for domain_pos in portfolio.positions:
        db_pos = await dao.get_position(game_id, domain_pos.symbol)

        if db_pos is None:
            # Create new
            await dao.create_position(
                game_id=game_id,
                symbol=domain_pos.symbol,
                quantity=domain_pos.quantity,
                avg_buy_price=domain_pos.avg_buy_price
            )
        else:
            # Update existing
            if domain_pos.quantity == 0:
                await dao.delete_position(db_pos.id)
            else:
                await dao.update_position(
                    position_id=db_pos.id,
                    quantity=domain_pos.quantity,
                    avg_buy_price=domain_pos.avg_buy_price
                )
```

---

## Validation Checklist

### Database Setup
- [ ] SQLite file created in `data/artha.db`
- [ ] All tables created (users, games, positions)
- [ ] Relationships work correctly
- [ ] Indexes created

### CRUD Operations
- [ ] Can create user
- [ ] Can create game
- [ ] Can create position
- [ ] Can load game with positions
- [ ] Can update game state
- [ ] Can update position
- [ ] Can delete position

### Transaction Management
- [ ] Commits save changes
- [ ] Rollbacks undo changes
- [ ] Errors don't corrupt database
- [ ] Concurrent access safe (SQLite handles)

### Integration
- [ ] Can save Stage 1 Portfolio to database
- [ ] Can load from database to Portfolio
- [ ] Save/Continue game flow works
- [ ] Multiple games per user works

---

## Quick Reference

### Import Statements

```python
# Models
from src.database.models import Base, User, Game, Position

# Connection
from src.database.connection import DatabaseConnection

# DAO
from src.database.dao import GameDAO

# SQLAlchemy
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
```

### Common Code Snippets

```python
# Initialize database
db = DatabaseConnection(DATA_DIR / "artha.db")
await db.create_tables()

# Get session
async with db.get_session() as session:
    dao = GameDAO(session)
    # ... operations ...
    await session.commit()

# Create game
user = await dao.get_or_create_user("player1")
game = await dao.create_game(user.id, 1000000.0, datetime.now())
await session.commit()

# Load game
game = await dao.get_game_by_id(game_id)

# Update position
position = await dao.get_position(game_id, "RELIANCE")
if position:
    await dao.update_position(position.id, new_qty, new_price)
    await session.commit()
```

---

This document provides all database patterns needed for Stage 2 implementation.

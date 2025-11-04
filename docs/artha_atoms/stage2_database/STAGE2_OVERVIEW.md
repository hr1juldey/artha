# Stage 2: Database Layer

**Duration**: 2 hours (Hours 2-4)
**Status**: Persistence
**Depends On**: Stage 1 complete and working

---

## Objective

Add SQLAlchemy database persistence to enable:
- Save game state
- Load saved games
- Multiple user support
- Trade history tracking

**Keep Stage 1 working** - only add, never break existing functionality.

---

## Success Criteria

- [ ] SQLite database created at `data/artha.db`
- [ ] Can save game state
- [ ] Can load saved game
- [ ] "Continue" button now works in menu
- [ ] Multiple games can be saved
- [ ] All Stage 1 functionality still works
- [ ] Database schema matches HLD

---

## Reference Materials

**Primary Examples**:
1. Check pyproject.toml - sqlalchemy>=2.0.40 is installed
2. SQLAlchemy 2.0 async patterns
3. HLD document - Section 5.1 (Database Schema)

**Key Patterns**:
- Declarative Base
- AsyncSession
- Relationship mapping
- Context managers for sessions

---

## Database Schema

From HLD, we need these tables:

### Users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Games
```sql
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT DEFAULT 'Simulation',
    initial_capital REAL DEFAULT 1000000.0,
    current_cash REAL NOT NULL,
    current_day INTEGER DEFAULT 0,
    total_days INTEGER DEFAULT 30,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Positions
```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    avg_buy_price REAL NOT NULL,
    current_price REAL,
    FOREIGN KEY (game_id) REFERENCES games(id),
    UNIQUE(game_id, symbol)
);
```

---

## Files to Create/Modify

### 1. `src/database/__init__.py`
```python
"""Database package"""
from src.database.connection import init_db, get_session
from src.database.models import User, Game, Position

__all__ = ["init_db", "get_session", "User", "Game", "Position"]
```

### 2. `src/database/connection.py`
```python
"""Database connection management"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import DB_PATH

# Create base for models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH}",
    echo=False,  # Set True for debugging
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    """Initialize database and create tables"""
    from src.database.models import User, Game, Position  # Import here to avoid circular imports

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session
```

### 3. `src/database/models.py`
```python
"""SQLAlchemy database models"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from src.database.connection import Base

class User(Base):
    """User model"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    games: Mapped[List["Game"]] = relationship("Game", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Game(Base):
    """Game model"""
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="Simulation")
    initial_capital: Mapped[float] = mapped_column(Float, default=1_000_000.0)
    current_cash: Mapped[float] = mapped_column(Float, nullable=False)
    current_day: Mapped[int] = mapped_column(Integer, default=0)
    total_days: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="games")
    positions: Mapped[List["Position"]] = relationship("Position", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id={self.id}, name='{self.name}', day={self.current_day})>"

class Position(Base):
    """Position model"""
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint('game_id', 'symbol', name='uq_game_symbol'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_buy_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="positions")

    def __repr__(self):
        return f"<Position(symbol='{self.symbol}', qty={self.quantity})>"
```

### 4. `src/database/dao.py`
```python
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
        """Save portfolio positions"""
        # Delete existing positions
        result = await session.execute(
            select(Position).where(Position.game_id == game_id)
        )
        for pos in result.scalars().all():
            await session.delete(pos)

        # Add new positions
        for pos in positions:
            db_pos = Position(
                game_id=game_id,
                symbol=pos.symbol,
                quantity=pos.quantity,
                avg_buy_price=pos.avg_buy_price,
                current_price=pos.current_price
            )
            session.add(db_pos)

        await session.commit()

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

        return GameState(
            player_name=user.full_name or user.username,
            current_day=game.current_day,
            total_days=game.total_days,
            initial_capital=game.initial_capital,
            portfolio=portfolio,
            created_at=game.created_at
        )

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
```

### 5. UPDATE `src/config.py`
```python
"""Configuration settings"""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)  # Create data dir if it doesn't exist
DB_PATH = DATA_DIR / "artha.db"

# Game settings
INITIAL_CAPITAL = 1_000_000  # ₹10 lakhs
COMMISSION_RATE = 0.0003  # 0.03%
DEFAULT_TOTAL_DAYS = 30

# Display settings
CURRENCY_SYMBOL = "₹"
DATE_FORMAT = "%Y-%m-%d"

# User settings
DEFAULT_USERNAME = "player1"
```

### 6. UPDATE `src/tui/app.py`
Add these imports at top:
```python
from src.database import init_db, get_session, User, Game
from src.database.dao import GameDAO, UserDAO
import asyncio
```

Add these methods to ArthaApp class:
```python
    async def _init_database(self):
        """Initialize database"""
        await init_db()

    async def _load_or_create_game(self) -> GameState:
        """Load latest game or create mock"""
        try:
            async for session in get_session():
                # Get or create default user
                user = await UserDAO.get_or_create_user(
                    session,
                    username=DEFAULT_USERNAME,
                    full_name="Demo Player"
                )

                # Try to load latest game
                game = await GameDAO.get_latest_game(session, user.id)

                if game:
                    # Convert DB game to GameState
                    return GameDAO.db_game_to_game_state(game, user)
                else:
                    # No saved game, return None
                    return None
        except Exception as e:
            self.log(f"Error loading game: {e}")
            return None

    async def _save_current_game(self):
        """Save current game state"""
        try:
            async for session in get_session():
                # Get user
                user = await UserDAO.get_by_username(session, DEFAULT_USERNAME)

                # Check if we have a game_id stored
                if not hasattr(self, 'current_game_id'):
                    # Create new game
                    game = await GameDAO.create_game(
                        session,
                        user_id=user.id,
                        name=f"Game {self.game_state.current_day}",
                        initial_capital=self.game_state.initial_capital,
                        total_days=self.game_state.total_days
                    )
                    self.current_game_id = game.id

                # Save game state
                await GameDAO.save_game_state(
                    session,
                    self.current_game_id,
                    self.game_state.portfolio.cash,
                    self.game_state.current_day
                )

                # Save positions
                await GameDAO.save_positions(
                    session,
                    self.current_game_id,
                    self.game_state.portfolio.positions
                )

                self.notify("Game saved!")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")

    def on_mount(self) -> None:
        """Initialize app - UPDATED"""
        # Initialize database
        asyncio.create_task(self._init_database())

        # Install screens
        self.install_screen(MenuScreen(), name="menu")
        self.install_screen(MainScreen(self.game_state), name="main")
        self.push_screen("menu")
```

### 7. UPDATE `src/tui/screens/menu_screen.py`
Update button handler to check for saved games:
```python
    async def on_mount(self) -> None:
        """Check for saved games"""
        # Check if there's a saved game
        from src.database.dao import UserDAO, GameDAO
        from src.database import get_session
        from src.config import DEFAULT_USERNAME

        try:
            async for session in get_session():
                user = await UserDAO.get_user_by_username(session, DEFAULT_USERNAME)
                if user:
                    game = await GameDAO.get_latest_game(session, user.id)
                    if game:
                        # Enable continue button
                        continue_btn = self.query_one("#continue", Button)
                        continue_btn.disabled = False
        except:
            pass  # Ignore errors, just keep button disabled

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks - UPDATED"""
        if event.button.id == "new-game":
            self.app.game_state = self.app._create_mock_game()
            self.app.push_screen("main")
        elif event.button.id == "continue":
            # Load saved game
            async def load_game():
                loaded_state = await self.app._load_or_create_game()
                if loaded_state:
                    self.app.game_state = loaded_state
                    self.app.push_screen("main")

            asyncio.create_task(load_game())
        elif event.button.id == "quit-btn":
            self.app.exit()
```

### 8. UPDATE `src/tui/screens/main_screen.py`
Add save binding:
```python
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "menu", "Menu"),
        ("s", "save", "Save"),  # NEW
    ]

    def action_save(self) -> None:
        """Save game"""
        asyncio.create_task(self.app._save_current_game())
```

---

## Qwen Coder Prompt for Stage 2

```
CONTEXT:
- Stage 1 is complete and working
- Now adding SQLAlchemy database persistence
- Using SQLite with async support (aiosqlite)
- Must maintain backward compatibility - Stage 1 should still work

TASK:
1. Create src/database/__init__.py
2. Create src/database/connection.py (async engine, Base, init_db)
3. Create src/database/models.py (User, Game, Position SQLAlchemy models)
4. Create src/database/dao.py (GameDAO, UserDAO with async methods)
5. Update src/config.py (add database paths, DEFAULT_USERNAME)
6. Update src/tui/app.py (add database init, load/save methods)
7. Update src/tui/screens/menu_screen.py (enable Continue button if saved game exists)
8. Update src/tui/screens/main_screen.py (add save binding)

CRITICAL RULES:
- Use SQLAlchemy 2.0 style (Mapped, mapped_column)
- All database ops are async (use await)
- Use async context managers: async for session in get_session()
- Create data/ directory if it doesn't exist
- Initialize database on app startup
- Don't break Stage 1 functionality

VALIDATION:
After implementation, test:
1. Run: python -m src.main
2. Start new game
3. Press 's' to save
4. Verify "Game saved!" notification
5. Quit with 'q'
6. Restart: python -m src.main
7. Verify "Continue" button is now enabled
8. Click "Continue"
9. Verify game loads with same state
10. Check data/artha.db file exists

EXPECTED OUTPUT:
- Database file created
- Can save and load games
- Continue button works
- All Stage 1 features still work
- No crashes

ERROR HANDLING:
- If aiosqlite not installed: pip install aiosqlite
- If async errors: check all DB calls use await
- If relationship errors: check back_populates matches
- If save fails: add try/except blocks and log errors
```

---

## Validation Checklist

- [ ] data/artha.db file created
- [ ] Can start new game (Stage 1 still works)
- [ ] Can press 's' to save
- [ ] Save notification appears
- [ ] After restart, Continue button enabled
- [ ] Can load saved game
- [ ] Loaded game has correct data
- [ ] Multiple saves work
- [ ] No async errors in console

---

## Next Stage Preview

Stage 3 will add:
- Real market data from yfinance
- Historical price loading
- Chart display

But Stage 2 must save/load perfectly first!

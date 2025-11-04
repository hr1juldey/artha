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
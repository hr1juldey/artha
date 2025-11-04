"""Configuration settings"""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)  # Create data dir if it doesn't exist
DB_PATH = DATA_DIR / "artha.db"
CACHE_DIR = DATA_DIR / "cache"

# Game settings
INITIAL_CAPITAL = 1_000_000  # ₹10 lakhs
COMMISSION_RATE = 0.0003  # 0.03%
DEFAULT_TOTAL_DAYS = 30

# Display settings
CURRENCY_SYMBOL = "₹"
DATE_FORMAT = "%Y-%m-%d"

# User settings
DEFAULT_USERNAME = "player1"

# Default stocks for new games
DEFAULT_STOCKS = ["RELIANCE", "TCS", "INFY"]
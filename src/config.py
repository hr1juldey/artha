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
DEFAULT_TOTAL_DAYS = 30

# Transaction costs (based on Indian stock market regulations)
# Reference: NSE, BSE, SEBI guidelines

# Brokerage
BROKERAGE_RATE = 0.0003  # 0.03% (discount broker rate)
COMMISSION_RATE = BROKERAGE_RATE  # Alias for backward compatibility

# STT (Securities Transaction Tax) - Government mandated
STT_RATE_BUY = 0.0  # No STT on delivery buy (only on intraday)
STT_RATE_SELL = 0.001  # 0.1% on delivery sell
STT_BUY = STT_RATE_BUY  # Alias
STT_SELL = STT_RATE_SELL  # Alias

# Exchange transaction charges (NSE/BSE)
EXCHANGE_CHARGES_RATE = 0.0000325  # 0.00325% (approximate NSE rate)
EXCHANGE_CHARGES = EXCHANGE_CHARGES_RATE  # Alias

# GST (Goods and Services Tax) - Applied on brokerage + exchange charges
GST_RATE = 0.18  # 18%

# SEBI charges (Securities and Exchange Board of India)
SEBI_FEES_RATE = 0.000001  # ₹10 per crore (0.0001%)
SEBI_CHARGES = SEBI_FEES_RATE  # Alias

# Display settings
CURRENCY_SYMBOL = "₹"
DATE_FORMAT = "%Y-%m-%d"

# User settings
DEFAULT_USERNAME = "player1"

# Default stocks for new games
DEFAULT_STOCKS = ["RELIANCE", "TCS", "INFY"]
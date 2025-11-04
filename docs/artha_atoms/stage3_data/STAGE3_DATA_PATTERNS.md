# Stage 3: Market Data Patterns

**Supplement to**: STAGE3_OVERVIEW.md
**Purpose**: Detailed yfinance usage, caching strategies, and error handling patterns

---

## Market Data Technology

- **Library**: yfinance 0.2.28+
- **Data Source**: Yahoo Finance (NSE/BSE stocks)
- **Cache Strategy**: CSV files in `data/cache/`
- **Fallback**: Mock data if download fails

---

## NSE Stock Symbol Format

### Yahoo Finance NSE Format

NSE (National Stock Exchange) stocks need `.NS` suffix:

```python
# Correct formats
"RELIANCE.NS"   # Reliance Industries
"TCS.NS"        # Tata Consultancy Services
"INFY.NS"       # Infosys
"HDFCBANK.NS"   # HDFC Bank
"ICICIBANK.NS"  # ICICI Bank

# User enters (without suffix)
"RELIANCE"  →  Convert to "RELIANCE.NS"
"TCS"       →  Convert to "TCS.NS"
```

### Symbol Normalization

```python
def normalize_symbol(symbol: str) -> str:
    """Normalize symbol to Yahoo Finance format

    Args:
        symbol: User-entered symbol (e.g., "RELIANCE" or "RELIANCE.NS")

    Returns:
        Yahoo Finance formatted symbol (e.g., "RELIANCE.NS")

    Examples:
        >>> normalize_symbol("RELIANCE")
        'RELIANCE.NS'
        >>> normalize_symbol("RELIANCE.NS")
        'RELIANCE.NS'
        >>> normalize_symbol("reliance")
        'RELIANCE.NS'
    """
    # Convert to uppercase
    symbol = symbol.upper().strip()

    # Add .NS if not present
    if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
        symbol = f"{symbol}.NS"

    return symbol
```

---

## yfinance API Patterns

### Basic Stock Data Download

```python
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Download historical data
def download_stock_data(symbol: str, days: int = 365) -> pd.DataFrame:
    """Download historical stock data

    Args:
        symbol: Stock symbol (with .NS suffix)
        days: Number of days of history

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume

    Raises:
        Exception: If download fails
    """
    ticker = yf.Ticker(symbol)

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Download data
    df = ticker.history(
        start=start_date,
        end=end_date,
        interval='1d'  # Daily data
    )

    return df
```

### Ticker Object Properties

```python
import yfinance as yf

ticker = yf.Ticker("RELIANCE.NS")

# Historical data
history_df = ticker.history(period="1mo")  # 1 month
# period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

# Stock info (metadata)
info = ticker.info
# Keys: longName, sector, industry, marketCap, currency, etc.

# Specific fields
company_name = info.get('longName', 'Unknown')
sector = info.get('sector', 'Unknown')
market_cap = info.get('marketCap', 0)

# Current price (from most recent close)
current_price = history_df['Close'].iloc[-1]
```

### Data Quality Checks

```python
def validate_stock_data(df: pd.DataFrame, symbol: str) -> tuple[bool, str]:
    """Validate downloaded stock data

    Args:
        df: Downloaded DataFrame
        symbol: Stock symbol (for error messages)

    Returns:
        (is_valid, error_message)
    """
    # Check if empty
    if df is None or df.empty:
        return False, f"No data returned for {symbol}"

    # Check minimum rows (need at least 30 days)
    if len(df) < 30:
        return False, f"Insufficient data for {symbol} (only {len(df)} rows)"

    # Check for required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns: {missing_cols}"

    # Check for all-zero prices (data quality issue)
    if (df['Close'] == 0).all():
        return False, f"All prices are zero for {symbol}"

    # Check for too many NaN values
    nan_pct = df['Close'].isna().sum() / len(df) * 100
    if nan_pct > 20:
        return False, f"Too many missing values ({nan_pct:.1f}%) for {symbol}"

    return True, "OK"
```

---

## Caching Strategy

### Cache Directory Structure

```
data/cache/
├── RELIANCE.NS.csv
├── TCS.NS.csv
├── INFY.NS.csv
├── metadata.json         # Cache metadata
└── .cache_info           # Last update timestamps
```

### Cache Metadata Format

```python
# metadata.json structure
{
    "RELIANCE.NS": {
        "last_updated": "2025-11-04T10:30:00",
        "days_cached": 365,
        "rows": 252,
        "date_range": ["2024-11-04", "2025-11-04"]
    },
    "TCS.NS": {
        "last_updated": "2025-11-04T10:31:00",
        "days_cached": 365,
        "rows": 252,
        "date_range": ["2024-11-04", "2025-11-04"]
    }
}
```

### Cache Implementation

```python
from pathlib import Path
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional

class CacheManager:
    """Manages data caching"""

    def __init__(self, cache_dir: Path):
        """Initialize cache manager

        Args:
            cache_dir: Path to cache directory
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = cache_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load cache metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def _save_metadata(self) -> None:
        """Save cache metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def get_cache_path(self, symbol: str) -> Path:
        """Get cache file path for symbol

        Args:
            symbol: Stock symbol (with .NS suffix)

        Returns:
            Path to cache CSV file
        """
        return self.cache_dir / f"{symbol}.csv"

    def is_cache_valid(
        self,
        symbol: str,
        max_age_hours: int = 24
    ) -> bool:
        """Check if cache is valid

        Args:
            symbol: Stock symbol
            max_age_hours: Maximum cache age in hours

        Returns:
            True if cache exists and is fresh
        """
        if symbol not in self.metadata:
            return False

        # Check file exists
        cache_path = self.get_cache_path(symbol)
        if not cache_path.exists():
            return False

        # Check age
        last_updated_str = self.metadata[symbol]['last_updated']
        last_updated = datetime.fromisoformat(last_updated_str)
        age = datetime.now() - last_updated

        return age < timedelta(hours=max_age_hours)

    def read_cache(self, symbol: str) -> Optional[pd.DataFrame]:
        """Read data from cache

        Args:
            symbol: Stock symbol

        Returns:
            DataFrame if cache exists and valid, None otherwise
        """
        if not self.is_cache_valid(symbol):
            return None

        cache_path = self.get_cache_path(symbol)

        try:
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            return df
        except Exception as e:
            print(f"Error reading cache for {symbol}: {e}")
            return None

    def write_cache(
        self,
        symbol: str,
        df: pd.DataFrame,
        days_cached: int
    ) -> None:
        """Write data to cache

        Args:
            symbol: Stock symbol
            df: DataFrame to cache
            days_cached: Number of days requested
        """
        cache_path = self.get_cache_path(symbol)

        # Save CSV
        df.to_csv(cache_path)

        # Update metadata
        self.metadata[symbol] = {
            'last_updated': datetime.now().isoformat(),
            'days_cached': days_cached,
            'rows': len(df),
            'date_range': [
                df.index.min().strftime('%Y-%m-%d'),
                df.index.max().strftime('%Y-%m-%d')
            ]
        }

        self._save_metadata()

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """Clear cache

        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        if symbol:
            # Clear specific symbol
            cache_path = self.get_cache_path(symbol)
            cache_path.unlink(missing_ok=True)

            if symbol in self.metadata:
                del self.metadata[symbol]
                self._save_metadata()
        else:
            # Clear all cache
            for cache_file in self.cache_dir.glob("*.csv"):
                cache_file.unlink()

            self.metadata = {}
            self._save_metadata()
```

---

## Complete MarketDataLoader Implementation

```python
"""Market data loader with caching and error handling"""
from pathlib import Path
from typing import Optional, Dict
import pandas as pd
import yfinance as yf
from datetime import datetime

from src.config import DATA_DIR

class MarketDataLoader:
    """Loads and caches market data"""

    # Default stock list (NSE)
    DEFAULT_STOCKS = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
        "HINDUNILVR", "BHARTIARTL", "SBIN", "BAJFINANCE", "ITC"
    ]

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize market data loader

        Args:
            cache_dir: Cache directory (defaults to DATA_DIR/cache)
        """
        self.cache_dir = cache_dir or (DATA_DIR / "cache")
        self.cache_manager = CacheManager(self.cache_dir)

        # In-memory cache (for current session)
        self._memory_cache: Dict[str, pd.DataFrame] = {}
        self._current_prices: Dict[str, float] = {}

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Yahoo Finance format

        Args:
            symbol: User-entered symbol

        Returns:
            Normalized symbol with .NS suffix
        """
        symbol = symbol.upper().strip()

        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            symbol = f"{symbol}.NS"

        return symbol

    def get_stock_data(
        self,
        symbol: str,
        days: int = 365,
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """Get stock data with caching

        Args:
            symbol: Stock symbol (with or without .NS)
            days: Number of days of history
            force_refresh: Force download even if cached

        Returns:
            DataFrame with OHLCV data, or None if failed

        Process:
            1. Check memory cache (current session)
            2. Check disk cache (if not force_refresh)
            3. Download from yfinance
            4. Validate data
            5. Cache results
        """
        # Normalize symbol
        symbol = self.normalize_symbol(symbol)

        # Check memory cache
        if not force_refresh and symbol in self._memory_cache:
            return self._memory_cache[symbol]

        # Check disk cache
        if not force_refresh:
            cached_df = self.cache_manager.read_cache(symbol)
            if cached_df is not None:
                self._memory_cache[symbol] = cached_df
                self._update_current_price(symbol, cached_df)
                return cached_df

        # Download from yfinance
        try:
            print(f"Downloading {symbol} data...")
            df = self._download_data(symbol, days)

            if df is None or df.empty:
                print(f"No data returned for {symbol}")
                return self._get_fallback_data(symbol, days)

            # Validate
            is_valid, message = self._validate_data(df, symbol)
            if not is_valid:
                print(f"Data validation failed: {message}")
                return self._get_fallback_data(symbol, days)

            # Cache results
            self.cache_manager.write_cache(symbol, df, days)
            self._memory_cache[symbol] = df
            self._update_current_price(symbol, df)

            print(f"Successfully loaded {len(df)} days of data for {symbol}")
            return df

        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
            return self._get_fallback_data(symbol, days)

    def _download_data(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """Download data from yfinance

        Args:
            symbol: Stock symbol with suffix
            days: Number of days

        Returns:
            DataFrame or None
        """
        from datetime import timedelta

        ticker = yf.Ticker(symbol)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = ticker.history(
            start=start_date,
            end=end_date,
            interval='1d'
        )

        return df

    def _validate_data(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> tuple[bool, str]:
        """Validate downloaded data

        Args:
            df: DataFrame to validate
            symbol: Symbol (for error messages)

        Returns:
            (is_valid, message)
        """
        if df is None or df.empty:
            return False, "Empty data"

        if len(df) < 30:
            return False, f"Too few rows: {len(df)}"

        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return False, f"Missing columns: {missing}"

        if (df['Close'] == 0).all():
            return False, "All prices are zero"

        nan_pct = df['Close'].isna().sum() / len(df) * 100
        if nan_pct > 20:
            return False, f"Too many NaNs: {nan_pct:.1f}%"

        return True, "OK"

    def _get_fallback_data(
        self,
        symbol: str,
        days: int
    ) -> pd.DataFrame:
        """Generate fallback mock data

        Args:
            symbol: Stock symbol
            days: Number of days

        Returns:
            Mock DataFrame
        """
        import numpy as np
        from datetime import timedelta

        print(f"Using fallback data for {symbol}")

        # Base prices for common stocks
        base_prices = {
            "RELIANCE.NS": 2500.0,
            "TCS.NS": 3500.0,
            "INFY.NS": 1500.0,
            "HDFCBANK.NS": 1600.0,
            "ICICIBANK.NS": 950.0,
        }

        base_price = base_prices.get(symbol, 1000.0)

        # Generate random walk
        dates = pd.date_range(
            end=datetime.now(),
            periods=days,
            freq='D'
        )

        # Random walk with slight upward bias
        np.random.seed(hash(symbol) % 2**32)  # Consistent for same symbol
        returns = np.random.normal(0.001, 0.02, days)  # 0.1% daily return, 2% volatility
        prices = base_price * (1 + returns).cumprod()

        df = pd.DataFrame({
            'Open': prices * 0.995,
            'High': prices * 1.01,
            'Low': prices * 0.99,
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, days)
        }, index=dates)

        return df

    def _update_current_price(self, symbol: str, df: pd.DataFrame) -> None:
        """Update current price cache

        Args:
            symbol: Stock symbol
            df: DataFrame with price data
        """
        if not df.empty:
            self._current_prices[symbol] = df['Close'].iloc[-1]

    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol

        Args:
            symbol: Stock symbol (with or without .NS)

        Returns:
            Current price (most recent close), or 0 if unavailable
        """
        symbol = self.normalize_symbol(symbol)

        # Check cache first
        if symbol in self._current_prices:
            return self._current_prices[symbol]

        # Load data to populate cache
        df = self.get_stock_data(symbol)

        if df is not None and not df.empty:
            return df['Close'].iloc[-1]

        return 0.0

    def get_price_at_date(
        self,
        symbol: str,
        date: datetime
    ) -> float:
        """Get historical price at specific date

        Args:
            symbol: Stock symbol
            date: Date to get price for

        Returns:
            Close price on that date, or 0 if unavailable
        """
        df = self.get_stock_data(symbol)

        if df is None or df.empty:
            return 0.0

        # Find closest date (in case exact date doesn't exist)
        date_str = date.strftime('%Y-%m-%d')

        try:
            # Try exact match
            if date_str in df.index:
                return df.loc[date_str, 'Close']

            # Find nearest date
            idx = df.index.get_indexer([date], method='nearest')[0]
            return df['Close'].iloc[idx]

        except Exception:
            return 0.0

    def preload_stocks(self, symbols: Optional[list[str]] = None) -> None:
        """Preload data for multiple stocks

        Args:
            symbols: List of symbols to preload (defaults to DEFAULT_STOCKS)
        """
        symbols = symbols or self.DEFAULT_STOCKS

        print(f"Preloading {len(symbols)} stocks...")

        for symbol in symbols:
            self.get_stock_data(symbol)

    def get_available_stocks(self) -> list[str]:
        """Get list of stocks with cached data

        Returns:
            List of stock symbols (without .NS suffix)
        """
        # Return DEFAULT_STOCKS for now
        # In production, could scan cache directory
        return self.DEFAULT_STOCKS.copy()

    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache_manager.clear_cache()
        self._memory_cache.clear()
        self._current_prices.clear()
        print("Cache cleared")
```

---

## Error Handling Patterns

### Network Errors

```python
def safe_download_with_retry(symbol: str, retries: int = 3) -> Optional[pd.DataFrame]:
    """Download with retries on network errors

    Args:
        symbol: Stock symbol
        retries: Number of retry attempts

    Returns:
        DataFrame or None
    """
    import time

    for attempt in range(retries):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y")

            if not df.empty:
                return df

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")

            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

    return None
```

### Invalid Symbols

```python
def validate_symbol_exists(symbol: str) -> tuple[bool, str]:
    """Check if symbol exists on Yahoo Finance

    Args:
        symbol: Stock symbol with .NS suffix

    Returns:
        (exists, message)
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Check if data is available
        if 'regularMarketPrice' in info or 'currentPrice' in info:
            return True, "Symbol exists"

        # Try downloading 5 days
        df = ticker.history(period="5d")
        if not df.empty:
            return True, "Symbol exists"

        return False, "No data available for symbol"

    except Exception as e:
        return False, f"Symbol lookup failed: {e}"
```

### Data Quality Issues

```python
def clean_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess stock data

    Args:
        df: Raw DataFrame from yfinance

    Returns:
        Cleaned DataFrame

    Cleaning steps:
        1. Remove NaN rows
        2. Forward fill remaining NaNs
        3. Remove duplicates
        4. Sort by date
        5. Remove outliers (>50% single-day moves)
    """
    # Remove rows with all NaN
    df = df.dropna(how='all')

    # Forward fill missing values
    df = df.fillna(method='ffill')

    # Remove duplicates
    df = df[~df.index.duplicated(keep='last')]

    # Sort by date
    df = df.sort_index()

    # Remove extreme outliers
    df['pct_change'] = df['Close'].pct_change()
    df = df[abs(df['pct_change']) < 0.5]  # Remove >50% moves
    df = df.drop(columns=['pct_change'])

    return df
```

---

## Integration with Trading Engine

### Price Lookup for Trades

```python
def execute_trade_with_price_lookup(
    loader: MarketDataLoader,
    symbol: str,
    action: str,
    quantity: int
) -> tuple[bool, float, str]:
    """Execute trade with real-time price lookup

    Args:
        loader: MarketDataLoader instance
        symbol: Stock symbol (without .NS)
        action: "BUY" or "SELL"
        quantity: Number of shares

    Returns:
        (success, price, message)
    """
    # Get current price
    price = loader.get_current_price(symbol)

    if price <= 0:
        return False, 0.0, f"Could not get price for {symbol}"

    # Price is valid
    total_value = price * quantity
    return True, price, f"{action} {quantity} shares at ₹{price:.2f} (Total: ₹{total_value:,.2f})"
```

### Day Advance with Historical Prices

```python
def advance_day_with_price_update(
    loader: MarketDataLoader,
    game_state: GameState,
    new_date: datetime
) -> None:
    """Advance game day and update all prices

    Args:
        loader: MarketDataLoader instance
        game_state: Current game state
        new_date: New game date

    Updates all position prices to historical price on new_date
    """
    for position in game_state.portfolio.positions:
        # Get historical price
        new_price = loader.get_price_at_date(position.symbol, new_date)

        if new_price > 0:
            position.current_price = new_price
        else:
            print(f"Warning: Could not get price for {position.symbol} on {new_date}")
            # Keep previous price

    # Update game day
    game_state.current_day += 1
```

---

## Testing Patterns

### Mock Data Loader for Testing

```python
class MockMarketDataLoader:
    """Mock loader for testing"""

    def __init__(self):
        self.prices = {
            "RELIANCE": 2500.0,
            "TCS": 3500.0,
            "INFY": 1500.0,
        }

    def get_current_price(self, symbol: str) -> float:
        return self.prices.get(symbol, 1000.0)

    def get_price_at_date(self, symbol: str, date: datetime) -> float:
        # Return slightly different price for each day
        base = self.prices.get(symbol, 1000.0)
        return base * (1 + (date.day % 30) * 0.01)  # ±30% variation

# Use in tests
def test_trading_with_mock_prices():
    loader = MockMarketDataLoader()
    price = loader.get_current_price("RELIANCE")
    assert price == 2500.0
```

### Testing Cache Behavior

```python
import pytest
from pathlib import Path

def test_cache_read_write(tmp_path):
    """Test cache read/write"""
    cache_manager = CacheManager(tmp_path)

    # Create test data
    df = pd.DataFrame({
        'Close': [100, 101, 102],
        'Volume': [1000, 1100, 1200]
    }, index=pd.date_range('2025-01-01', periods=3))

    # Write cache
    cache_manager.write_cache("TEST.NS", df, 365)

    # Read cache
    cached_df = cache_manager.read_cache("TEST.NS")

    assert cached_df is not None
    assert len(cached_df) == 3
    assert cached_df['Close'].iloc[0] == 100
```

---

## Performance Optimization

### Parallel Downloads

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def preload_stocks_parallel(loader: MarketDataLoader, symbols: list[str]) -> None:
    """Preload multiple stocks in parallel

    Args:
        loader: MarketDataLoader instance
        symbols: List of symbols to load
    """
    def load_one(symbol: str):
        return loader.get_stock_data(symbol)

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(load_one, symbols))

    success_count = sum(1 for r in results if r is not None)
    print(f"Preloaded {success_count}/{len(symbols)} stocks")
```

### Memory-Efficient Streaming

```python
def get_price_series_generator(
    loader: MarketDataLoader,
    symbol: str
) -> Generator[tuple[datetime, float], None, None]:
    """Generator for price series (memory efficient)

    Args:
        loader: MarketDataLoader instance
        symbol: Stock symbol

    Yields:
        (date, price) tuples
    """
    df = loader.get_stock_data(symbol)

    if df is not None:
        for date, row in df.iterrows():
            yield date, row['Close']
```

---

## Common Patterns Summary

| Operation | Method | Caching | Fallback |
|-----------|--------|---------|----------|
| Get latest price | `get_current_price()` | Yes (memory + disk) | 0.0 |
| Get historical data | `get_stock_data()` | Yes (disk) | Mock data |
| Price at specific date | `get_price_at_date()` | Uses cached data | 0.0 |
| Preload stocks | `preload_stocks()` | Writes to disk | Mock data |
| Clear cache | `clear_cache()` | Deletes all | N/A |

---

## Validation Checklist

### Data Download
- [ ] Can download NSE stocks with .NS suffix
- [ ] Handles network errors gracefully
- [ ] Falls back to mock data if download fails
- [ ] Validates data quality before using

### Caching
- [ ] Creates cache directory automatically
- [ ] Writes CSV files correctly
- [ ] Reads from cache if fresh (<24h)
- [ ] Metadata tracks cache status
- [ ] Can clear cache manually

### Price Lookup
- [ ] Current price returns valid float
- [ ] Historical price lookup works
- [ ] Returns 0.0 for invalid symbols
- [ ] Memory cache speeds up repeated lookups

### Integration
- [ ] Works with trading engine
- [ ] Updates prices on day advance
- [ ] Portfolio values calculate correctly
- [ ] No crashes on network issues

---

## Quick Reference

### Import Statements

```python
from src.data.loader import MarketDataLoader
from src.config import DATA_DIR
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
```

### Common Code Snippets

```python
# Initialize loader
loader = MarketDataLoader()

# Get current price
price = loader.get_current_price("RELIANCE")

# Get historical data
df = loader.get_stock_data("TCS", days=365)

# Preload common stocks
loader.preload_stocks()

# Get price on specific date
price_on_date = loader.get_price_at_date("INFY", datetime(2025, 1, 1))

# Clear cache
loader.clear_cache()
```

---

This document provides all market data patterns needed for Stage 3 implementation.

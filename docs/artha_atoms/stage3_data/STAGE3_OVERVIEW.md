# Stage 3: Market Data Loader

**Duration**: 2 hours (Hours 4-6)
**Status**: Real Data Integration
**Depends On**: Stage 2 complete and working

---

## Objective

Replace mock stock prices with real historical data from yfinance:
- Download NSE stock data
- Cache data locally
- Display real prices in portfolio
- Add price history lookup

---

## Success Criteria

- [ ] Can download real stock data
- [ ] Prices update from historical data
- [ ] Data cached for offline use
- [ ] Portfolio shows real Indian stock prices
- [ ] Handles missing data gracefully
- [ ] All previous functionality works

---

## Files to Create

### 1. `src/data/__init__.py`
```python
"""Market data package"""
from src.data.loader import MarketDataLoader

__all__ = ["MarketDataLoader"]
```

### 2. `src/data/loader.py`
```python
"""Market data loading from yfinance"""
import yfinance as yf
import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta
from src.config import DATA_DIR

class MarketDataLoader:
    """Loads and caches market data"""

    def __init__(self):
        self.cache_dir = DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, pd.DataFrame] = {}

    def get_stock_data(
        self,
        symbol: str,
        days: int = 365
    ) -> Optional[pd.DataFrame]:
        """Get stock data for symbol"""
        # Add .NS suffix for NSE stocks if not present
        if not symbol.endswith('.NS'):
            symbol_with_suffix = f"{symbol}.NS"
        else:
            symbol_with_suffix = symbol

        # Check memory cache
        if symbol_with_suffix in self._cache:
            return self._cache[symbol_with_suffix]

        # Check file cache
        cache_file = self.cache_dir / f"{symbol}.csv"
        if cache_file.exists():
            # Check if cache is recent (< 1 day old)
            cache_age = datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )
            if cache_age < timedelta(days=1):
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                self._cache[symbol_with_suffix] = df
                return df

        # Download from yfinance
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            ticker = yf.Ticker(symbol_with_suffix)
            df = ticker.history(start=start_date, end=end_date)

            if not df.empty:
                # Save to cache
                df.to_csv(cache_file)
                self._cache[symbol_with_suffix] = df
                return df
            else:
                return None

        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
            return None

    def get_current_price(self, symbol: str) -> float:
        """Get latest price for symbol"""
        df = self.get_stock_data(symbol)
        if df is not None and not df.empty:
            return float(df['Close'].iloc[-1])
        return 0.0

    def get_price_at_day(self, symbol: str, day_offset: int) -> float:
        """Get price at specific day offset from today"""
        df = self.get_stock_data(symbol)
        if df is not None and not df.empty:
            try:
                idx = -(day_offset + 1)  # Negative index from end
                if abs(idx) <= len(df):
                    return float(df['Close'].iloc[idx])
            except:
                pass
        return 0.0

    def get_default_stocks(self) -> list[str]:
        """Get list of popular Indian stocks"""
        return [
            "RELIANCE",
            "TCS",
            "INFY",
            "HDFCBANK",
            "ICICIBANK",
            "HINDUNILVR",
            "ITC",
            "SBIN",
            "BHARTIARTL",
            "BAJFINANCE"
        ]

    def preload_stocks(self, symbols: list[str]) -> None:
        """Preload data for multiple stocks"""
        for symbol in symbols:
            self.get_stock_data(symbol)
```

### 3. UPDATE `src/config.py`
```python
# Add after other settings
CACHE_DIR = DATA_DIR / "cache"

# Default stocks for new games
DEFAULT_STOCKS = ["RELIANCE", "TCS", "INFY"]
```

### 4. UPDATE `src/tui/app.py`
```python
from src.data import MarketDataLoader

class ArthaApp(App):
    def __init__(self):
        super().__init__()
        self.market_data = MarketDataLoader()
        self.game_state = self._create_mock_game()

    def _create_mock_game(self) -> GameState:
        """Create mock game with REAL prices"""
        from src.config import DEFAULT_STOCKS

        # Preload stock data
        self.market_data.preload_stocks(DEFAULT_STOCKS)

        # Create positions with real prices
        positions = []
        for symbol in DEFAULT_STOCKS[:3]:  # Use first 3
            current_price = self.market_data.get_current_price(symbol)
            # Simulate buying 5 days ago
            buy_price = self.market_data.get_price_at_day(symbol, 5)

            if current_price > 0 and buy_price > 0:
                # Calculate quantity to invest ~₹1.2L per stock
                quantity = int(120000 / buy_price)

                positions.append(Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_buy_price=buy_price,
                    current_price=current_price
                ))

        # Calculate remaining cash
        invested = sum(p.cost_basis for p in positions)
        cash = INITIAL_CAPITAL - invested

        portfolio = Portfolio(cash=cash, positions=positions)

        return GameState(
            player_name="Demo Player",
            current_day=5,
            total_days=30,
            initial_capital=INITIAL_CAPITAL,
            portfolio=portfolio
        )
```

### 5. NEW: `src/tui/widgets/stock_selector.py`
```python
"""Stock selector widget"""
from textual.widgets import ListView, ListItem, Label
from textual.containers import Container

class StockSelector(ListView):
    """Widget to select stocks"""

    def __init__(self, stocks: list[str]):
        super().__init__()
        self.stocks = stocks

    def on_mount(self) -> None:
        """Populate list"""
        for stock in self.stocks:
            self.append(ListItem(Label(stock)))
```

---

## Qwen Coder Prompt for Stage 3

```
CONTEXT:
- Stage 2 is working with database persistence
- Now integrating real market data using yfinance
- Use caching to avoid repeated downloads
- Must handle network failures gracefully

TASK:
1. Create src/data/__init__.py
2. Create src/data/loader.py (MarketDataLoader class)
3. Update src/config.py (add CACHE_DIR, DEFAULT_STOCKS)
4. Update src/tui/app.py (_create_mock_game to use real prices)
5. Create src/tui/widgets/stock_selector.py (for future use)

CRITICAL RULES:
- Add .NS suffix for NSE stocks
- Cache downloaded data to CSV files
- Handle yfinance errors gracefully (return 0.0 or None)
- Preload data at startup to avoid delays
- Use realistic quantities based on price

VALIDATION:
After implementation:
1. Delete data/cache/ folder if exists
2. Run: python -m src.main
3. Start new game
4. Verify portfolio shows real prices (RELIANCE, TCS, INFY)
5. Check data/cache/ folder has CSV files
6. Verify prices are reasonable (₹1000-4000 range)
7. Restart app - should load from cache (faster)
8. Verify P&L calculations work with real prices

EXPECTED OUTPUT:
- Real stock prices display
- Data cached locally
- Fast subsequent loads
- Graceful handling if yfinance fails
- Reasonable position quantities

ERROR HANDLING:
- If yfinance fails: return mock price or 0.0, don't crash
- If no internet: use cached data
- If cache corrupted: re-download
- Log all errors but continue running
```

---

## Validation Checklist

- [ ] Real prices load from yfinance
- [ ] Cache folder created
- [ ] CSV files in cache
- [ ] Prices reasonable for Indian stocks
- [ ] P&L calculations correct
- [ ] Second run uses cache (faster)
- [ ] App works offline if cache exists
- [ ] No crashes on network errors

---

## Next: Stage 4 adds trading engine

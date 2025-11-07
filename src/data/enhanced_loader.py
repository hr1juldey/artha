"""Enhanced Market Data Loader with realistic simulation"""
import yfinance as yf
import pandas as pd
import numpy as np
import random
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from src.config import DATA_DIR


class EnhancedMarketDataLoader:
    """Market loader with realistic simulation"""

    def __init__(self):
        self.cache_dir = DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, pd.DataFrame] = {}
        self._extended_cache: Dict[str, pd.DataFrame] = {}
        
        # Market simulation parameters
        self.market_sentiment = 0.0  # -1 (bearish) to +1 (bullish)
        self.volatility_regime = "normal"  # low, normal, high
        self.sector_trends = {}  # Track sector momentum
        self.tracked_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
        
        # Stock betas (market sensitivity)
        self.stock_betas = {
            "RELIANCE": 1.2,    # High beta
            "TCS": 0.8,         # Low beta (defensive)
            "INFY": 0.9,        # Low beta
            "HDFCBANK": 1.0,    # Market beta
            "ICICIBANK": 1.1,   # Slightly higher
        }

    def simulate_market_day(self, current_day: int) -> Dict[str, float]:
        """Simulate realistic market movements for all stocks"""
        # Update market regime
        self._update_market_regime(current_day)

        # Generate correlated returns for all stocks
        returns = {}
        market_return = self._generate_market_return()

        for symbol in self.tracked_symbols:
            # Stock return = market return + stock-specific noise
            stock_beta = self._get_stock_beta(symbol)
            stock_return = (market_return * stock_beta) + self._generate_stock_noise()
            returns[symbol] = stock_return

        return returns

    def _update_market_regime(self, day: int) -> None:
        """Update market sentiment and volatility"""
        # Market sentiment changes gradually (random walk)
        sentiment_change = random.gauss(0, 0.05)
        self.market_sentiment = max(-1, min(1, self.market_sentiment + sentiment_change))

        # Volatility regime switches (Markov chain)
        if random.random() < 0.05:  # 5% chance of regime switch
            regimes = ["low", "normal", "high"]
            self.volatility_regime = random.choice(regimes)

    def _generate_market_return(self) -> float:
        """Generate market-wide return"""
        # Base volatility by regime
        vol_map = {"low": 0.01, "normal": 0.02, "high": 0.04}
        volatility = vol_map[self.volatility_regime]

        # Return = sentiment drift + random noise
        drift = self.market_sentiment * 0.001  # Small positive drift in bull market
        noise = random.gauss(0, volatility)

        return drift + noise

    def _get_stock_beta(self, symbol: str) -> float:
        """Get stock's beta (market sensitivity)"""
        return self.stock_betas.get(symbol, 1.0)  # Default to market beta

    def _generate_stock_noise(self) -> float:
        """Generate stock-specific random noise"""
        return random.gauss(0, 0.015)  # 1.5% stock-specific volatility

    def get_stock_data(
        self,
        symbol: str,
        days: int = 365
    ) -> Optional[pd.DataFrame]:
        """Get stock data for symbol with extended historical support"""
        # Add .NS suffix for NSE stocks if not present
        if not symbol.endswith('.NS'):
            symbol_with_suffix = f"{symbol}.NS"
        else:
            symbol_with_suffix = symbol

        # Check memory cache for the requested days
        cache_key = f"{symbol_with_suffix}_{days}"
        if cache_key in self._extended_cache:
            return self._extended_cache[cache_key]

        # Check file cache
        cache_file = self.cache_dir / f"{symbol}_{days}.csv"
        if cache_file.exists():
            # Check if cache is recent (< 1 day old)
            cache_age = datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )
            if cache_age < timedelta(days=1):
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                self._extended_cache[cache_key] = df
                return df

        # Download from yfinance with extended period if needed
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            ticker = yf.Ticker(symbol_with_suffix)
            df = ticker.history(start=start_date, end=end_date)

            if not df.empty:
                # Save to cache
                df.to_csv(cache_file)
                self._extended_cache[cache_key] = df
                return df
            else:
                # Return mock data
                return self._generate_mock_data(symbol, days)

        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
            # Return mock data
            return self._generate_mock_data(symbol, days)

    def get_current_price(self, symbol: str) -> float:
        """Get latest price for symbol"""
        df = self.get_stock_data(symbol, days=365)  # Standard period
        if df is not None and not df.empty:
            return float(df['Close'].iloc[-1])
        return 0.0

    def get_price_at_day(self, symbol: str, day_offset: int, max_days: int = 2000) -> float:
        """Get price at specific day offset from today with extended support"""
        # Try to get extended historical data first
        df = self.get_stock_data(symbol, days=max_days)
        if df is not None and not df.empty:
            try:
                idx = -(day_offset + 1)  # Negative index from end
                if abs(idx) <= len(df):
                    return float(df['Close'].iloc[idx])
            except IndexError:
                pass
        
        # If historical data unavailable, calculate using last known price
        df_standard = self.get_stock_data(symbol, days=365)
        if df_standard is not None and not df_standard.empty:
            last_price = float(df_standard['Close'].iloc[-1])
            
            # Apply random walk simulation to continue beyond historical data
            # Use market volatility characteristics for realistic simulation
            volatility_factor = 0.02  # 2% daily volatility
            adjustment = random.uniform(-volatility_factor, volatility_factor)
            return max(1.0, last_price * (1 + adjustment))  # Ensure price doesn't go below ₹1
        
        # Fallback to mock data generation
        return self._generate_fallback_price(symbol)

    def get_price_at_day_with_simulation(self, symbol: str) -> float:
        """Get price using simulation beyond historical data"""
        df = self.get_stock_data(symbol, days=365)
        if df is not None and not df.empty:
            last_price = float(df['Close'].iloc[-1])
            
            # Apply random walk simulation
            volatility_factor = 0.02  # 2% daily volatility
            adjustment = random.uniform(-volatility_factor, volatility_factor)
            return max(1.0, last_price * (1 + adjustment))
        
        return self._generate_fallback_price(symbol)

    def get_price_history(self, symbol: str, days: int = 30) -> List[float]:
        """Get recent price history for sparkline charts"""
        df = self.get_stock_data(symbol, days=days)
        if df is not None and not df.empty:
            return df['Close'].tail(days).tolist()
        return []

    def _generate_fallback_price(self, symbol: str) -> float:
        """Generate fallback price when no data is available"""
        # Base prices for common stocks
        base_prices = {
            "RELIANCE": 2500.0,
            "TCS": 3500.0,
            "INFY": 1500.0,
            "HDFCBANK": 1600.0,
            "ICICIBANK": 950.0,
            "HINDUNILVR": 2400.0,
            "ITC": 450.0,
            "SBIN": 600.0,
            "BHARTIARTL": 900.0,
            "BAJFINANCE": 7000.0,
        }

        return base_prices.get(symbol, 1000.0)

    def _generate_mock_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """Generate fallback mock data with realistic market dynamics"""
        print(f"⚠️  Using mock data for {symbol} (download failed)")

        # Base prices for common stocks
        base_prices = {
            "RELIANCE": 2500.0,
            "TCS": 3500.0,
            "INFY": 1500.0,
            "HDFCBANK": 1600.0,
            "ICICIBANK": 950.0,
            "HINDUNILVR": 2400.0,
            "ITC": 450.0,
            "SBIN": 600.0,
            "BHARTIARTL": 900.0,
            "BAJFINANCE": 7000.0,
        }

        base_price = base_prices.get(symbol, 1000.0)

        # Generate dates
        dates = pd.date_range(
            end=datetime.now(),
            periods=days,
            freq='D'
        )

        # Simulate realistic market behavior based on market regime
        np.random.seed(hash(symbol) % (2**32))  # Consistent for same symbol
        
        # Adjust volatility based on market sentiment and regime
        vol_map = {"low": 0.01, "normal": 0.02, "high": 0.04}
        volatility = vol_map[self.volatility_regime]
        
        # Add drift based on sentiment
        drift = self.market_sentiment * 0.0005  # Small drift based on sentiment
        
        # Generate returns with drift
        returns = np.random.normal(drift, volatility, days)
        prices = base_price * (1 + returns).cumprod()

        # Create DataFrame
        df = pd.DataFrame({
            'Open': prices * 0.995,
            'High': prices * 1.01,
            'Low': prices * 0.99,
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, days)
        }, index=dates)

        return df

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
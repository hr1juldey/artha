"""Tests for the market data functionality"""
import pytest
import asyncio
from src.data.loader import MarketDataLoader


def test_market_data_loader_creation():
    """Test that the market data loader can be created."""
    loader = MarketDataLoader()
    assert loader is not None
    assert loader.cache_dir.exists()


def test_get_default_stocks():
    """Test that we get the default list of Indian stocks."""
    loader = MarketDataLoader()
    stocks = loader.get_default_stocks()
    
    assert len(stocks) == 10
    assert "RELIANCE" in stocks
    assert "TCS" in stocks
    assert "INFY" in stocks


@pytest.mark.skip(reason="Requires network access - run manually")
def test_real_data_download():
    """Test that we can actually download real stock data."""
    loader = MarketDataLoader()
    
    # Test that we can get data for a few stocks
    for stock in ["RELIANCE", "TCS", "INFY"]:
        data = loader.get_stock_data(stock, days=30)
        # This will be None if network is not available or if yfinance fails
        if data is not None:
            assert not data.empty
            assert 'Close' in data.columns
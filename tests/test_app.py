"""Tests for the Artha application"""
import pytest
import asyncio
from src.tui.app import ArthaApp


def test_app_creation():
    """Test that the app can be instantiated without errors."""
    app = ArthaApp()
    assert app is not None
    
    # Verify that the CSS path is set correctly
    assert app.CSS_PATH == "app.tcss"
    
    # Verify the title is set correctly
    assert app.TITLE == "Artha - Stock Market Simulator"


@pytest.mark.asyncio
async def test_database_initialization():
    """Test that the database initializes properly."""
    app = ArthaApp()
    # Initialize the database
    await app._init_database()
    # Verify database file exists
    import os
    from src.config import DB_PATH
    assert os.path.exists(DB_PATH)
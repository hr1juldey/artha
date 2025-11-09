#!/usr/bin/env python3
"""
Test script to verify Enhanced Watchlist integration
This validates the watchlist implementation without running the full TUI
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required imports work"""
    print("✓ Testing imports...")

    try:
        from src.tui.widgets.enhanced_watchlist import (
            EnhancedWatchlistWidget,
            StockPriceChart,
            STOCK_COLORS
        )
        print("  ✓ EnhancedWatchlistWidget imported")
        print("  ✓ StockPriceChart imported")
        print(f"  ✓ STOCK_COLORS palette has {len(STOCK_COLORS)} colors")

        from src.data.enhanced_loader import EnhancedMarketDataLoader
        print("  ✓ EnhancedMarketDataLoader imported")

        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def test_market_data_methods():
    """Test that market data loader has required methods"""
    print("\n✓ Testing MarketDataLoader methods...")

    from src.data.enhanced_loader import EnhancedMarketDataLoader

    loader = EnhancedMarketDataLoader()

    # Check for required methods
    required_methods = [
        'get_default_stocks',
        'get_price_history',
        'get_current_price',
        'get_stock_data'
    ]

    for method in required_methods:
        if hasattr(loader, method):
            print(f"  ✓ {method}() exists")
        else:
            print(f"  ✗ {method}() missing")
            return False

    # Test get_default_stocks
    stocks = loader.get_default_stocks()
    print(f"  ✓ get_default_stocks() returns {len(stocks)} stocks: {stocks[:3]}...")

    # Test get_price_history
    try:
        price_history = loader.get_price_history("RELIANCE", days=30)
        if price_history:
            print(f"  ✓ get_price_history() returns {len(price_history)} data points")
        else:
            print("  ✓ get_price_history() returns empty list (no cache)")
    except Exception as e:
        print(f"  ⚠ get_price_history() error (expected if no data): {e}")

    return True


def test_watchlist_widget_structure():
    """Test watchlist widget structure"""
    print("\n✓ Testing EnhancedWatchlistWidget structure...")

    from src.tui.widgets.enhanced_watchlist import EnhancedWatchlistWidget

    # Check class attributes
    if hasattr(EnhancedWatchlistWidget, 'BINDINGS'):
        bindings = EnhancedWatchlistWidget.BINDINGS
        print(f"  ✓ Widget has {len(bindings)} key binding(s)")
        for binding in bindings:
            print(f"    - {binding.key}: {binding.action}")

    if hasattr(EnhancedWatchlistWidget, 'DEFAULT_STOCKS'):
        print(f"  ✓ DEFAULT_STOCKS defined: {EnhancedWatchlistWidget.DEFAULT_STOCKS[:3]}...")

    # Check required methods
    required_methods = [
        'compose',
        'on_mount',
        'populate_stock_selector',
        'refresh_chart',
        'action_toggle_focus',
        'update_prices'
    ]

    for method in required_methods:
        if hasattr(EnhancedWatchlistWidget, method):
            print(f"  ✓ {method}() exists")
        else:
            print(f"  ✗ {method}() missing")
            return False

    return True


def test_chart_widget_structure():
    """Test chart widget structure"""
    print("\n✓ Testing StockPriceChart structure...")

    from src.tui.widgets.enhanced_watchlist import StockPriceChart

    # Check required methods (Dolphie pattern)
    required_methods = [
        'on_mount',
        'on_show',
        'on_resize',
        'render_chart',
        'set_stock_data',
        'toggle_focus_mode'
    ]

    for method in required_methods:
        if hasattr(StockPriceChart, method):
            print(f"  ✓ {method}() exists (Dolphie pattern)")
        else:
            print(f"  ✗ {method}() missing")
            return False

    return True


def test_color_palette():
    """Test color palette"""
    print("\n✓ Testing stock color palette...")

    from src.tui.widgets.enhanced_watchlist import STOCK_COLORS

    print(f"  ✓ Palette has {len(STOCK_COLORS)} unique colors")

    # Verify all colors are RGB tuples
    for i, color in enumerate(STOCK_COLORS):
        if isinstance(color, tuple) and len(color) == 3:
            r, g, b = color
            if all(0 <= c <= 255 for c in [r, g, b]):
                continue
            else:
                print(f"  ✗ Color {i} has invalid RGB values: {color}")
                return False
        else:
            print(f"  ✗ Color {i} is not an RGB tuple: {color}")
            return False

    print(f"  ✓ All colors are valid RGB tuples")
    print(f"  ✓ Sample colors:")
    for i, color in enumerate(STOCK_COLORS[:3]):
        print(f"    - Color {i}: RGB{color}")

    return True


def test_dashboard_integration():
    """Test dashboard integration"""
    print("\n✓ Testing dashboard integration...")

    try:
        from src.tui.screens.dashboard_screen import DashboardScreen
        print("  ✓ DashboardScreen imported")

        # Check if it imports EnhancedWatchlistWidget
        import inspect
        source = inspect.getsource(DashboardScreen)

        if 'EnhancedWatchlistWidget' in source:
            print("  ✓ DashboardScreen uses EnhancedWatchlistWidget")
        else:
            print("  ✗ DashboardScreen doesn't use EnhancedWatchlistWidget")
            return False

        if 'action_add_to_watchlist' in source:
            print("  ✓ action_add_to_watchlist() defined")

        return True
    except Exception as e:
        print(f"  ✗ Dashboard integration error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Enhanced Watchlist Integration Test")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Market Data Methods", test_market_data_methods),
        ("Watchlist Widget Structure", test_watchlist_widget_structure),
        ("Chart Widget Structure", test_chart_widget_structure),
        ("Color Palette", test_color_palette),
        ("Dashboard Integration", test_dashboard_integration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Watchlist implementation is ready.")
        print("\nManual Testing Instructions:")
        print("1. Run: python -m src.main")
        print("2. Create or continue a game")
        print("3. In the dashboard, look at the right panel (Watchlist)")
        print("4. Use Tab/Arrow keys to navigate to the stock selector")
        print("5. Press Space/Enter to select stocks")
        print("6. Press 'f' to toggle focus mode")
        print("7. Press 'w' to refresh prices")
        print("8. Press Space to advance day and see prices update")
        return 0
    else:
        print("\n⚠ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

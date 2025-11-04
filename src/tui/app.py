"""Main Textual application"""
from textual.app import App, ComposeResult
from textual.binding import Binding
import logging
from src.tui.screens.menu_screen import MenuScreen
from src.tui.screens.main_screen import MainScreen
from src.models import GameState, Portfolio, Position
from src.config import INITIAL_CAPITAL, DEFAULT_USERNAME, DEFAULT_STOCKS, DATA_DIR
from src.database import init_db, get_session, User, Game
from src.database.dao import GameDAO, UserDAO
from src.data import MarketDataLoader
from src.coach import CoachManager
import asyncio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_DIR / "artha.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ArthaApp(App):
    """Artha TUI Application"""

    CSS_PATH = "app.tcss"
    TITLE = "Artha - Stock Market Simulator"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.market_data = MarketDataLoader()
        self.coach = CoachManager()  # NEW
        self.game_state = self._create_mock_game()

    def on_exception(self, exception: Exception) -> None:
        """Handle exceptions"""
        logger.error(f"Exception: {exception}", exc_info=True)
        self.notify(
            f"An error occurred. Check logs for details.",
            severity="error"
        )

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
                user = await UserDAO.get_or_create_user(session, DEFAULT_USERNAME, full_name="Demo Player")

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
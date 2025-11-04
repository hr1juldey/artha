"""Menu screen"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Container, Vertical
from src.database.dao import UserDAO, GameDAO
from src.database import get_session
from src.config import DEFAULT_USERNAME
import asyncio

class MenuScreen(Screen):
    """Main menu screen"""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()

        with Container(id="menu-container"):
            with Vertical(id="menu-options"):
                yield Static("# Artha", id="title")
                yield Static("Stock Market Learning Simulator", id="subtitle")
                yield Button("New Game", id="new-game", variant="success")
                yield Button("Continue", id="continue", disabled=True)
                yield Button("Quit", id="quit-btn", variant="error")

        yield Footer()

    async def on_mount(self) -> None:
        """Check for saved games"""
        # Check if there's a saved game
        try:
            async for session in get_session():
                user = await UserDAO.get_user_by_username(session, DEFAULT_USERNAME)
                if user:
                    game = await GameDAO.get_latest_game(session, user.id)
                    if game:
                        # Enable continue button
                        continue_btn = self.query_one("#continue", Button)
                        continue_btn.disabled = False
        except:
            pass  # Ignore errors, just keep button disabled

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks - UPDATED"""
        if event.button.id == "new-game":
            self.app.game_state = self.app._create_mock_game()
            self.app.push_screen("main")
        elif event.button.id == "continue":
            # Load saved game
            async def load_game():
                loaded_state = await self.app._load_or_create_game()
                if loaded_state:
                    self.app.game_state = loaded_state
                    self.app.push_screen("main")

            asyncio.create_task(load_game())
        elif event.button.id == "quit-btn":
            self.app.exit()

    def action_quit(self) -> None:
        """Quit application"""
        self.app.exit()
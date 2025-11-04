"""Entry point for Artha application"""
from src.tui.app import ArthaApp

def main():
    """Run the application"""
    app = ArthaApp()
    app.run()

if __name__ == "__main__":
    main()
# Artha - Stock Market Learning Simulator

A text-based stock market simulator for learning investing.

## Quick Start

### Prerequisites
- Python 3.12+
- Ollama (optional, for AI coach)

### One-Click Installation

#### Linux/macOS
```bash
# Clone repository
git clone <repo-url>
cd artha

# Run the installer
./install.sh
```

#### Windows
```bash
# Clone repository
git clone <repo-url>
cd artha

# Run the installer
install.bat
```

The installer will automatically:
- Create a virtual environment (if not present)
- Ensure pip is available
- Install UV package manager for faster dependency installation
- Install all required dependencies from requirements.txt
- Set up data directories
- Verify the installation

### Manual Installation

If you prefer to install manually:

```bash
# Clone repository
git clone <repo-url>
cd artha

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate.bat  # Windows

# Install UV (optional, for faster installation)
pip install uv

# Install dependencies
uv pip install -r requirements.txt
# or
pip install -r requirements.txt

# Run the game
python -m src.main
```

### Optional: AI Coach Setup

For AI-powered trading insights:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh  # Linux/macOS
# or download from https://ollama.ai/download  # Windows

# Pull the model
ollama pull qwen3:8b

# Start Ollama service
ollama serve
```

The game will work without Ollama, but will use fallback educational messages instead of AI-generated insights.

## How to Play

1. Start with ₹10,00,000 virtual cash
2. Trade Indian stocks (NSE)
3. Learn from AI coach feedback
4. Complete 30 days with positive returns

## Controls

- `t` - Trade (buy/sell)
- `Space` - Advance day
- `c` - Coach insights
- `s` - Save game
- `h` - Help
- `q` - Quit

## Features

- Real historical stock data (yfinance)
- AI coach powered by DSPy + Ollama
- Portfolio tracking and analysis
- Save/load games
- Educational feedback

## Testing

```bash
pytest tests/
```

## License

MIT
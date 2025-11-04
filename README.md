# Artha - Stock Market Learning Simulator

A text-based stock market simulator for learning investing.

## Quick Start

### Prerequisites
- Python 3.12+
- Ollama (optional, for AI coach)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd artha

# Install dependencies
pip install -e .

# Run the game
python -m src.main
```

### Optional: AI Coach

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull qwen3:8b

# Start Ollama
ollama serve
```

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
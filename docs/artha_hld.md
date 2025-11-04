# Artha – High-Level Design (HLD)

## Stock Market Learning Simulator - Technical Architecture

**Document Version:** 1.0  
**Date:** 2025-11-04  
**Author:** Technical Architecture Team  
**Status:** Design Review

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [System Architecture](#3-system-architecture)
4. [Component Design](#4-component-design)
5. [Data Architecture](#5-data-architecture)
6. [API Design](#6-api-design)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [Security Architecture](#8-security-architecture)
9. [Performance & Scalability](#9-performance--scalability)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Technology Stack](#11-technology-stack)
12. [Integration Points](#12-integration-points)

---

## 1. System Overview

### 1.1 Purpose

Artha is a local-first educational stock market simulator designed to teach Indian teenagers (ages 13-17) about investing using scrambled historical NSE/BSE data. The system operates entirely offline with no external dependencies except initial data download.

### 1.2 Scope

**In-Scope:**

- FastAPI backend for game logic and data serving
- Textual TUI client for user interaction
- SQLite database for persistent state
- Local Ollama LLM for AI coaching
- Data scrambling pipeline for privacy
- Historical data integration via yfinance
- Multi-user support with role-based access

**Out-of-Scope:**

- Real-time market data streaming
- Cloud synchronization
- Mobile applications (Phase 2)
- Live trading integration
- Payment gateway integration (MVP)

### 1.3 Constraints

**Technical:**

- Must run on commodity laptops (4GB RAM minimum)
- No internet required after setup
- Single-server architecture (no distributed systems)
- Python-only technology stack
- Maximum 500 concurrent users per instance

**Business:**

- Zero cost for data acquisition
- No third-party API dependencies (runtime)
- SEBI/NSE compliance for educational use
- Open-source libraries only (MIT/Apache 2.0)

### 1.4 Assumptions

- Users have Python 3.12+ installed
- Ollama runs successfully on user's machine
- yfinance API remains free and accessible
- SQLite sufficient for 10,000 users per instance
- Local storage available: 5GB for data + 2GB for models

---

## 2. Architecture Principles

### 2.1 Design Philosophy

1. **Local-First Architecture**
   - All processing happens on user's machine
   - No cloud dependencies after initial setup
   - Data sovereignty and privacy by design

2. **Separation of Concerns**
   - Backend (FastAPI): Business logic, data access
   - Frontend (Textual): Presentation and user interaction
   - AI (Ollama): Natural language processing
   - Data Layer (SQLite + CSV): Persistence

3. **Stateless API Design**
   - Each API request is self-contained
   - Session management via JWT tokens
   - Idempotent operations where possible

4. **Fail-Safe Defaults**
   - Graceful degradation if Ollama unavailable
   - Offline mode when yfinance unreachable
   - Auto-save every 30 seconds

5. **Educational Focus**
   - Preserve statistical realism over complexity
   - Clear feedback loops for learning
   - Prevent real-money confusion

### 2.2 Quality Attributes

| Attribute | Target | Measurement |
|-----------|--------|-------------|
| **Performance** | API latency <200ms (p95) | Prometheus metrics |
| **Reliability** | 99.5% uptime (local) | Error logs |
| **Scalability** | 500 users/instance | Load testing |
| **Security** | No data leakage | Penetration testing |
| **Usability** | <5 min onboarding | User studies |
| **Maintainability** | Code coverage >80% | pytest + coverage |

---

## 3. System Architecture

### 3.1 Logical Architecture (Layers)

```bash
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          Textual TUI Application (Client)                │   │
│  │  - Keyboard-driven interface                             │   │
│  │  - Real-time chart rendering (Plotext)                   │   │
│  │  - Form handling (trade entry, search)                   │   │
│  │  - State synchronization with backend                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST (localhost:8000)
┌───────────────────────────▼─────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             FastAPI Backend (Server)                     │   │
│  │  ┌────────────────┐  ┌─────────────────┐                 │   │
│  │  │ Game Engine    │  │ Trade Executor  │                 │   │
│  │  │ - State mgmt   │  │ - Order matching│                 │   │
│  │  │ - Day advance  │  │ - Commission    │                 │   │
│  │  └────────────────┘  └─────────────────┘                 │   │
│  │  ┌────────────────┐  ┌─────────────────┐                 │   │
│  │  │ Analytics      │  │ AI Coach Proxy  │                 │   │
│  │  │ - Metrics calc │  │ - Prompt eng.   │                 │   │
│  │  │ - Risk scoring │  │ - Response cache│                 │   │
│  │  └────────────────┘  └─────────────────┘                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ ORM (SQLAlchemy)
┌───────────────────────────▼─────────────────────────────────────┐
│                      DATA ACCESS LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          Data Access Objects (DAOs)                      │   │
│  │  - UserDAO, GameDAO, TradeDAO, AssetDAO                  │   │
│  │  - Query builders with indexing                          │   │
│  │  - Transaction management                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ SQL / File I/O
┌───────────────────────────▼─────────────────────────────────────┐
│                      PERSISTENCE LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   SQLite DB  │  │  CSV Files   │  │  Ollama (External)   │   │
│  │   (Game      │  │  (Scrambled  │  │  - Llama 3.2 3B      │   │
│  │    State)    │  │   OHLCV)     │  │  - HTTP API          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Physical Architecture (Deployment View)

```bash
┌─────────────────────────────────────────────────────────────────┐
│                     User's Local Machine                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Process 1: FastAPI Server (uvicorn)                    │    │
│  │  Port: 8000                                             │    │
│  │  Working Dir: ~/.Artha/                         │    │
│  │  Config: config.yaml                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐    │
│  │  Process 2: Textual TUI Client                          │    │
│  │  Connects to: http://localhost:8000                     │    │
│  │  Terminal: xterm-256color                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐    │
│  │  Process 3: Ollama Service (optional)                   │    │
│  │  Port: 11434                                            │    │
│  │  Model: qwen3:8b                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  File System:                                                   │
│  ~/.Artha/                                              │
│    ├── data/                                                    │
│    │   ├── raw/           # Original downloads (gitignored)     │
│    │   ├── scrambled/     # Transformed CSVs                    │
│    │   └── universe.json  # Asset metadata                      │
│    ├── db/                                                      │
│    │   └── Artha.db  # SQLite database                  │
│    ├── logs/                                                    │
│    │   ├── api.log                                              │
│    │   └── errors.log                                           │
│    └── config.yaml         # User preferences                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Process View (Runtime)

```bash
Startup Sequence:
─────────────────

1. User runs: python -m Artha serve
   ├─> FastAPI app initializes
   ├─> Database connection pool created
   ├─> CSV loaders initialized (lazy loading)
   └─> Server listens on localhost:8000

2. User runs: python -m Artha play
   ├─> Textual app initializes
   ├─> Health check to API (retry 3x)
   ├─> Load user session (if exists)
   └─> Render login screen

3. User logs in
   ├─> POST /api/auth/login
   ├─> JWT token issued (expires 7 days)
   ├─> Load user's active games
   └─> Display game selection screen

4. User selects/creates game
   ├─> GET /api/games/{id} (every 5s polling)
   ├─> Load portfolio data
   ├─> Fetch current prices
   └─> Render main UI

5. User places trade
   ├─> POST /api/trades/execute
   ├─> Validate order (funds, quantity)
   ├─> Execute at simulated price
   ├─> Update database (atomic transaction)
   ├─> Trigger Ollama feedback (async)
   └─> Return updated portfolio

6. User advances day
   ├─> POST /api/games/{id}/advance
   ├─> Update all positions (market-to-market)
   ├─> Check for corporate actions
   ├─> Generate daily summary
   └─> Stream results to client

7. User exits
   ├─> Auto-save current state
   ├─> Close DB connections
   └─> Cleanup temp files
```

---

## 4. Component Design

### 4.1 Backend Components (FastAPI)

#### 4.1.1 Game Engine

**Responsibilities:**

- Manage game lifecycle (create, load, save, delete)
- Advance simulation time (day/week/month)
- Maintain game state consistency
- Handle corporate actions (splits, dividends)

**Interfaces:**

```python
class GameEngine:
    def create_game(self, user_id: int, config: GameConfig) -> Game
    def load_game(self, game_id: int) -> Game
    def advance_day(self, game_id: int, days: int = 1) -> GameState
    def get_state(self, game_id: int) -> GameState
    def apply_corporate_action(self, game_id: int, action: CorporateAction)
    def calculate_metrics(self, game_id: int) -> PerformanceMetrics
```

**Key Algorithms:**

```bash
Day Advance Algorithm:
1. Fetch current day index from game record
2. Load all positions for game
3. For each position:
   a. Read next day's closing price from CSV
   b. Update position.current_price
   c. Calculate unrealized P&L
4. Check for corporate actions (date match)
5. Update game.current_day += 1
6. Commit transaction atomically
7. Return updated state
```

#### 4.1.2 Trade Executor

**Responsibilities:**

- Validate trade requests (funds, limits)
- Execute orders at simulated prices
- Calculate costs (brokerage, STT, GST)
- Update positions and cash balance
- Generate trade confirmations

**Interfaces:**

```python
class TradeExecutor:
    def execute_market_order(
        self, 
        game_id: int, 
        symbol: str, 
        side: OrderSide, 
        quantity: int
    ) -> TradeResult
    
    def execute_limit_order(
        self,
        game_id: int,
        symbol: str,
        side: OrderSide,
        quantity: int,
        limit_price: float
    ) -> TradeResult
    
    def calculate_costs(
        self,
        price: float,
        quantity: int,
        side: OrderSide
    ) -> TradeCosts
    
    def validate_order(
        self,
        game: Game,
        order: OrderRequest
    ) -> ValidationResult
```

**Execution Logic:**

```bash
Market Order Execution:
1. Validate: game.status == 'active'
2. Fetch current price for symbol at game.current_day
3. If BUY:
   a. Required cash = price × qty × (1 + commission_rate)
   b. Check: game.cash >= required_cash
   c. Create position or update avg_buy_price
   d. Deduct cash
4. If SELL:
   a. Check: position.quantity >= qty
   b. Calculate realized P&L
   c. Credit cash = price × qty × (1 - commission_rate)
   d. Reduce position
5. Record trade in trades table
6. Return TradeResult with execution details

Limit Order Execution:
1. Store limit order in pending_orders table
2. On each day advance:
   a. Check if day's high >= limit_price (BUY)
   b. Or day's low <= limit_price (SELL)
   c. If triggered, execute at limit_price
   d. Mark order as filled
3. Return partial fills if volume insufficient
```

**Cost Calculation (Indian Market):**

```bash
Brokerage: 0.03% (0.0003) or ₹20 max per order
STT (Securities Transaction Tax):
  - Equity Delivery: 0.1% on sell side
  - Equity Intraday: 0.025% on both sides
GST: 18% on (brokerage + exchange charges)
Exchange Charges: 0.00325% NSE, 0.00275% BSE
SEBI Turnover Charge: ₹10 per crore

Example (₹1L Buy Order):
  Order Value: ₹100,000
  Brokerage: ₹30 (0.03% of 1L)
  STT: ₹0 (only on sell)
  Exchange: ₹3.25
  GST: ₹5.99 (18% of ₹33.25)
  Total Cost: ₹100,039.24
```

#### 4.1.3 Analytics Engine

**Responsibilities:**

- Calculate portfolio metrics (returns, Sharpe, drawdown)
- Risk attribution (sector, stock concentration)
- Trade analysis (win rate, avg gain/loss)
- Benchmark comparison (Nifty 50)

**Interfaces:**

```python
class AnalyticsEngine:
    def calculate_returns(
        self, 
        game_id: int
    ) -> ReturnsMetrics
    
    def calculate_risk(
        self,
        game_id: int
    ) -> RiskMetrics
    
    def sector_attribution(
        self,
        game_id: int
    ) -> SectorBreakdown
    
    def compare_benchmark(
        self,
        game_id: int,
        benchmark: str = "NIFTY50"
    ) -> BenchmarkComparison
```

**Metrics Formulas:**

```python
# Total Return
total_return = ((current_value - initial_capital) / initial_capital) * 100

# Sharpe Ratio (simplified, annualized)
daily_returns = [r1, r2, ..., rn]
mean_return = sum(daily_returns) / len(daily_returns)
std_dev = sqrt(sum((r - mean_return)^2) / len(daily_returns))
sharpe = (mean_return / std_dev) * sqrt(252)  # 252 trading days

# Max Drawdown
equity_curve = [value on day 1, day 2, ..., day n]
running_max = []
for value in equity_curve:
    running_max.append(max(running_max[-1] if running_max else 0, value))
drawdowns = [(max_val - val) / max_val for val, max_val in zip(equity_curve, running_max)]
max_drawdown = max(drawdowns) * 100

# Win Rate
winning_trades = count(trade.pnl > 0)
total_trades = count(trades)
win_rate = (winning_trades / total_trades) * 100

# Concentration (Herfindahl Index)
concentrations = [(position_value / total_value)^2 for position in positions]
herfindahl = sum(concentrations)  # Range: 0 (diversified) to 1 (concentrated)
```

#### 4.1.4 Data Loader

**Responsibilities:**

- Lazy-load CSV files on demand
- Cache frequently accessed data in memory
- Handle missing data (holidays, gaps)
- Provide fast lookups (symbol → OHLCV)

**Interfaces:**

```python
class DataLoader:
    def load_asset(self, symbol: str) -> pd.DataFrame
    def get_price_at_day(
        self, 
        symbol: str, 
        day_index: int
    ) -> PricePoint
    def get_ohlcv_range(
        self,
        symbol: str,
        start_day: int,
        end_day: int
    ) -> List[PricePoint]
    def preload_universe(self, symbols: List[str])
    def clear_cache(self)
```

**Caching Strategy:**

```bash
In-Memory Cache (LRU):
- Max size: 100 assets × 5 years = ~100MB RAM
- Eviction: Least Recently Used
- Warmup: Preload Nifty 50 on startup

Access Pattern:
1. Check cache for symbol
2. If miss:
   a. Read CSV from disk (pandas.read_csv)
   b. Store in cache with timestamp
   c. Set TTL = 1 hour (for dev, infinite for prod)
3. Return requested rows

Holiday Handling:
- Forward-fill prices (use previous day's close)
- Mark days with volume=0 as non-trading
```

#### 4.1.5 AI Coach Manager

**Responsibilities:**

- Interface with Ollama HTTP API
- Manage prompt templates
- Cache responses to avoid redundancy
- Fallback when Ollama unavailable

**Interfaces:**

```python
class CoachManager:
    def get_trade_feedback(
        self,
        game_id: int,
        trade: Trade,
        portfolio: Portfolio
    ) -> CoachResponse
    
    def get_portfolio_advice(
        self,
        game_id: int
    ) -> CoachResponse
    
    def answer_question(
        self,
        user_id: int,
        question: str
    ) -> CoachResponse
    
    def generate_quiz(
        self,
        topic: str,
        difficulty: int
    ) -> Quiz
```

**Prompt Engineering:**

```python
TRADE_FEEDBACK_TEMPLATE = """
You are a gentle investing coach for Indian teenagers.

Context:
- Student just executed: {side} {quantity} shares of {symbol} at ₹{price}
- Current portfolio value: ₹{portfolio_value}
- Cash remaining: ₹{cash}
- Total positions: {position_count}

Task:
Provide 3 concise bullets (max 80 chars each):
1. What this trade does to their risk/return profile
2. One practical tip for future trades
3. Encouragement + next learning step

Format:
• [Bullet 1]
• [Bullet 2]
• [Bullet 3]

Keep it friendly, educational, and emoji-free.
"""

PORTFOLIO_REVIEW_TEMPLATE = """
You are analyzing a student's portfolio for learning purposes.

Portfolio Snapshot:
{portfolio_json}

Risk Metrics:
- Sector Concentration: {herfindahl}
- Largest Position: {max_position}%
- Total Positions: {count}

Provide 4-5 insights:
1. Overall risk assessment (0-10 scale)
2. Diversification feedback
3. Sector imbalance warnings
4. 2-3 specific actionable improvements

Keep language simple for 15-year-olds.
"""
```

**Ollama Integration:**

```python
import httpx

class OllamaClient:
    BASE_URL = "http://localhost:11434"
    
    async def generate(
        self,
        prompt: str,
        model: str = "qwen3:8b",
        temperature: float = 0.7,
        max_tokens: int = 300
    ) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=30.0
            )
            result = response.json()
            return result['response']
```

### 4.2 Frontend Components (Textual TUI)

#### 4.2.1 Main Application

```python
from textual.app import App
from textual.binding import Binding

class ArthaApp(App):
    CSS_PATH = "styles.css"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("t", "trade", "Trade"),
        Binding("space", "advance_day", "Next Day"),
        Binding("c", "coach", "Coach"),
        Binding("/", "search", "Search"),
    ]
    
    SCREENS = {
        "login": LoginScreen,
        "dashboard": DashboardScreen,
        "game": GameScreen,
        "trade": TradeModal,
        "settings": SettingsScreen,
    }
    
    def on_mount(self):
        self.push_screen("login")
```

#### 4.2.2 Layout Structure

```bash
┌────────────────────────────────────────────────────────────────┐
│ Header: [Username] | Cash: ₹8.5L | Day: 45/365 | NW: ₹11.2L    │
├──────────────────────────┬─────────────────────────────────────┤
│                          │  Portfolio Summary                  │
│   Chart Pane (60%)       │  ┌──────┬────────┬────────┬──────┐  │
│                          │  │Symbol│Qty│Price│P&L %  │      │  │
│   [Candlestick/Line]     │  ├──────┼────────┼────────┼──────┤  │
│                          │  │ZYTEX │ 100│ 345│+12.3% │      │  │
│   Controls:              │  │NEXUS │ 200│ 678│ -5.2% │      │  │
│   ◄ ► Zoom: + -          │  └──────┴────────┴────────┴──────┘  │
│   Pan: ← →               │                                     │
│                          │  Allocation:                        │
│   [Volume bars]          │  IT:     ████████░░ 40%             │
│                          │  Finance:██████░░░░ 30%             │
│                          │  Pharma: ███░░░░░░░ 15%             │
├──────────────────────────┼─────────────────────────────────────┤
│  Watchlist (20%)         │  Notifications/Coach (40%)          │
│  □ STELLAR  ₹456 ↑2.1%   │  🎓  Good trade! You diversified    │
│  □ QUANTUM  ₹234 ↓1.3%   │     into pharma sector.             │
│  □ MORPHO   ₹789 ↑0.8%   │                                     │
│                          │  ⚠️   High concentration in IT      │
│  [Add to Watchlist]      │     (40%). Consider rebalancing.    │
└──────────────────────────┴─────────────────────────────────────┘
│ Footer: [T]rade [C]oach [Space]Next Day [S]ave [Q]uit          │
└────────────────────────────────────────────────────────────────┘
```

#### 4.2.3 Key Widgets

**ChartWidget (Custom Widget):**

```python
from textual.widgets import Static
import plotext as plt

class ChartWidget(Static):
    def __init__(self, symbol: str):
        super().__init__()
        self.symbol = symbol
        self.data: pd.DataFrame = None
        self.chart_type = "candlestick"  # or "line"
        self.zoom_level = 90  # days to display
        
    async def load_data(self):
        response = await api_client.get(
            f"/api/assets/{self.symbol}/chart",
            params={"days": self.zoom_level}
        )
        self.data = pd.DataFrame(response.json())
        self.refresh_chart()
    
    def refresh_chart(self):
        plt.clf()
        plt.date_form('Y-m-d')
        plt.theme('dark')
        
        if self.chart_type == "candlestick":
            plt.candlestick(
                self.data['date'],
                [self.data['open'], 
                 self.data['high'],
                 self.data['low'],
                 self.data['close']]
            )
        else:
            plt.plot(
                self.data['date'],
                self.data['close'],
                label="Close"
            )
        
        plt.title(f"{self.symbol} - {self.chart_type.title()}")
        plt.xlabel("Date")
        plt.ylabel("Price (₹)")
        chart_str = plt.build()
        self.update(chart_str)
```

**PortfolioGrid (DataTable):**

```python
from textual.widgets import DataTable

class PortfolioGrid(DataTable):
    def on_mount(self):
        self.add_columns(
            "Symbol", "Qty", "Avg Price", 
            "Current", "P&L", "% Change"
        )
        self.cursor_type = "row"
        self.zebra_stripes = True
        
    async def refresh_data(self, game_id: int):
        portfolio = await api_client.get(
            f"/api/portfolio/{game_id}"
        )
        self.clear()
        for position in portfolio['positions']:
            pnl_color = "green" if position['pnl'] > 0 else "red"
            self.add_row(
                position['symbol'],
                str(position['quantity']),
                f"₹{position['avg_price']:.2f}",
                f"₹{position['current_price']:.2f}",
                f"[{pnl_color}]₹{position['pnl']:.2f}[/]",
                f"[{pnl_color}]{position['pnl_pct']:+.2f}%[/]"
            )
```

**TradeModal (Modal Screen):**

```python
from textual.screen import ModalScreen
from textual.widgets import Input, Select, Button

class TradeModal(ModalScreen):
    def __init__(self, symbol: str, current_price: float):
        super().__init__()
        self.symbol = symbol
        self.current_price = current_price
    
    def compose(self):
        yield Container(
            Static(f"Trade {self.symbol}"),
            Static(f"Current Price: ₹{self.current_price:.2f}"),
            Select(
                options=[
                    ("Buy", "BUY"),
                    ("Sell", "SELL")
                ],
                id="side"
            ),
            Input(
                placeholder="Quantity",
                type="integer",
                id="quantity"
            ),
            Select(
                options=[
                    ("Market", "MARKET"),
                    ("Limit", "LIMIT")
                ],
                id="order_type"
            ),
            Input(
                placeholder="Limit Price (if applicable)",
                type="number",
                id="limit_price"
            ),
            Static(id="cost_estimate"),
            Button("Execute", variant="success", id="execute"),
            Button("Cancel", variant="error", id="cancel"),
            id="trade_dialog"
        )
    
    def on_input_changed(self, event):
        # Update cost estimate dynamically
        quantity = self.query_one("#quantity").value
        if quantity:
            cost = self.current_price * int(quantity) * 1.0003
            self.query_one("#cost_estimate").update(
                f"Est. Cost: ₹{cost:.2f}"
            )
    
    async def on_button_pressed(self, event):
        if event.button.id == "execute":
            await self.execute_trade()
        else:
            self.dismiss()
    
    async def execute_trade(self):
        data = {
            "game_id": self.app.current_game_id,
            "symbol": self.symbol,
            "side": self.query_one("#side").value,
            "quantity": int(self.query_one("#quantity").value),
            "order_type": self.query_one("#order_type").value,
        }
        
        if data['order_type'] == 'LIMIT':
            data['limit_price'] = float(
                self.query_one("#limit_price").value
            )
        
        result = await api_client.post(
            "/api/trades/execute",
            json=data
        )
        
        if result['status'] == 'success':
            self.app.notify("✓ Trade executed successfully!")
            self.dismiss(result)
        else:
            self.app.notify(
                f"✗ Error: {result['message']}",
                severity="error"
            )
```

---

## 5. Data Architecture

### 5.1 Database Schema (SQLite)

**Schema Design Rationale:**

- Single database file for portability
- Denormalization for read performance (portfolio values cached)
- Indexes on foreign keys and frequently queried columns
- JSON columns for flexible metadata

**Detailed Schema:**

```sql
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT,  -- bcrypt hash for local auth
    role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'parent', 'admin')),
    full_name TEXT,
    date_of_birth DATE,
    language_pref TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

-- Games table
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT DEFAULT 'Simulation',
    difficulty TEXT CHECK(difficulty IN ('easy', 'medium', 'hard')),
    initial_capital REAL DEFAULT 1000000.0,
    current_cash REAL NOT NULL,
    current_value REAL,  -- denormalized: cash + positions value
    current_day INTEGER DEFAULT 0,
    total_days INTEGER DEFAULT 365,
    universe_seed INTEGER NOT NULL,  -- random seed for data scrambling
    start_date TEXT,  -- ISO date string
    status TEXT CHECK(status IN ('active', 'paused', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_games_user ON games(user_id);
CREATE INDEX idx_games_status ON games(status);

-- Positions table
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    avg_buy_price REAL NOT NULL,
    current_price REAL,  -- updated on day advance
    market_value REAL,   -- quantity × current_price
    cost_basis REAL,     -- quantity × avg_buy_price
    unrealized_pnl REAL, -- market_value - cost_basis
    unrealized_pnl_pct REAL,
    sector TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    UNIQUE(game_id, symbol)
);
CREATE INDEX idx_positions_game ON positions(game_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- Trades table
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK(side IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    order_type TEXT CHECK(order_type IN ('MARKET', 'LIMIT', 'STOP_LOSS')),
    limit_price REAL,  -- for limit orders
    brokerage REAL DEFAULT 0.0,
    stt REAL DEFAULT 0.0,
    exchange_charges REAL DEFAULT 0.0,
    gst REAL DEFAULT 0.0,
    total_charges REAL,  -- sum of all charges
    net_amount REAL,     -- price × quantity ± charges
    executed_day INTEGER NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);
CREATE INDEX idx_trades_game ON trades(game_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_day ON trades(executed_day);

-- Assets master (scrambled universe)
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,  -- fictional ticker
    display_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    industry TEXT,
    market_cap_category TEXT,  -- large/mid/small
    original_ticker_hash TEXT,  -- SHA256 of real NSE ticker
    csv_filename TEXT NOT NULL,
    first_day_index INTEGER,
    last_day_index INTEGER,
    avg_daily_volume REAL,
    min_price REAL,
    max_price REAL,
    metadata_json TEXT  -- additional flexible fields
);
CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_assets_sector ON assets(sector);

-- Performance snapshots (daily)
CREATE TABLE portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    day_index INTEGER NOT NULL,
    total_value REAL NOT NULL,
    cash REAL NOT NULL,
    positions_value REAL,
    daily_return REAL,  -- % change from previous day
    cumulative_return REAL,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    UNIQUE(game_id, day_index)
);
CREATE INDEX idx_snapshots_game_day ON portfolio_snapshots(game_id, day_index);

-- Achievements
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,  -- e.g., 'DIVERSIFIER'
    name TEXT NOT NULL,
    description TEXT,
    icon_emoji TEXT,
    criteria_json TEXT NOT NULL,  -- JSON with unlock conditions
    points INTEGER DEFAULT 100,
    rarity TEXT CHECK(rarity IN ('common', 'rare', 'epic', 'legendary'))
);

CREATE TABLE user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    game_id INTEGER,  -- nullable: some achievements are global
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievements(id),
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL,
    UNIQUE(user_id, achievement_id)
);
CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);

-- Tournaments
CREATE TABLE tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    creator_id INTEGER NOT NULL,  -- teacher
    difficulty TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT CHECK(status IN ('draft', 'active', 'completed')),
    max_participants INTEGER DEFAULT 50,
    rules_json TEXT,  -- custom rules
    prize_json TEXT,   -- prize structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id)
);
CREATE INDEX idx_tournaments_status ON tournaments(status);

CREATE TABLE tournament_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,  -- linked game for this tournament
    rank INTEGER,
    final_return REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    total_trades INTEGER,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (game_id) REFERENCES games(id),
    UNIQUE(tournament_id, user_id)
);
CREATE INDEX idx_tournament_participants ON tournament_participants(tournament_id, rank);

-- Coach feedback history
CREATE TABLE coach_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_id INTEGER,
    interaction_type TEXT CHECK(
        interaction_type IN ('trade_feedback', 'portfolio_review', 'question', 'quiz')
    ),
    prompt TEXT,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL
);
CREATE INDEX idx_coach_interactions_user ON coach_interactions(user_id);

-- Limit orders (pending)
CREATE TABLE pending_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    order_type TEXT NOT NULL,
    limit_price REAL,
    stop_price REAL,
    status TEXT DEFAULT 'pending' CHECK(
        status IN ('pending', 'filled', 'cancelled', 'expired')
    ),
    placed_day INTEGER NOT NULL,
    expires_day INTEGER,
    filled_day INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);
CREATE INDEX idx_pending_orders_game ON pending_orders(game_id, status);

-- Audit log (optional, for debugging)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    details TEXT,  -- JSON
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
```

### 5.2 CSV Data Structure (Scrambled OHLCV)

**File Naming Convention:**

```bash
data/scrambled/{SYMBOL}.csv

Example:
data/scrambled/ZYTEX.csv
data/scrambled/NEXWAVE.csv
data/scrambled/MORPHO.csv
```

**CSV Format:**

```csv
day_index,date,open,high,low,close,volume
0,2015-01-01,245.30,248.75,243.10,246.90,1234567
1,2015-01-02,247.00,250.60,246.20,249.85,1456789
2,2015-01-05,250.00,252.30,248.50,251.70,1345678
...
2519,2024-12-31,789.50,795.20,785.30,792.40,2345678
```

**Column Definitions:**

- `day_index`: Integer, 0-indexed, contiguous (skip weekends/holidays)
- `date`: ISO date string (YYYY-MM-DD), fictional dates
- `open`: Opening price (₹)
- `high`: Intraday high (₹)
- `low`: Intraday low (₹)
- `close`: Closing price (₹)
- `volume`: Number of shares traded

**Data Validation Rules:**

```python
# Invariants
assert high >= open >= low
assert high >= close >= low
assert volume >= 0
assert day_index[i+1] == day_index[i] + 1  # contiguous

# Sanity checks
max_daily_move = 0.20  # 20% circuit limit
assert abs(close[i] - close[i-1]) / close[i-1] <= max_daily_move

# Volume check
assert volume > 0 or is_holiday(date)
```

### 5.3 Universe Metadata (JSON)

**File:** `data/universe.json`

```json
{
  "version": "1.0.0",
  "generated_at": "2025-11-04T00:00:00Z",
  "scramble_seed": 42,
  "universe_size": 500,
  "date_range": {
    "start": "2015-01-01",
    "end": "2025-11-04",
    "trading_days": 2520
  },
  "assets": [
    {
      "symbol": "ZYTEX",
      "display_name": "Zytex Pharmaceuticals Ltd.",
      "sector": "Healthcare",
      "industry": "Pharmaceuticals",
      "market_cap_category": "large",
      "original_ticker_hash": "a3f5b2c1...",
      "csv_filename": "ZYTEX.csv",
      "statistics": {
        "avg_price": 345.67,
        "avg_daily_volume": 1234567,
        "volatility": 0.023,
        "beta": 1.05
      }
    },
    {
      "symbol": "NEXWAVE",
      "display_name": "Nexwave Technologies Inc.",
      "sector": "Information Technology",
      "industry": "Software Services",
      "market_cap_category": "mid",
      "original_ticker_hash": "b7e9d3f2...",
      "csv_filename": "NEXWAVE.csv",
      "statistics": {
        "avg_price": 678.90,
        "avg_daily_volume": 987654,
        "volatility": 0.031,
        "beta": 1.23
      }
    }
  ],
  "sectors": {
    "Information Technology": 95,
    "Financial Services": 87,
    "Consumer Goods": 62,
    "Healthcare": 48,
    "Energy": 39,
    "Automobiles": 31,
    "Telecom": 24,
    "Metals": 22,
    "Realty": 18,
    "Others": 74
  },
  "indices": {
    "SHADOW_NIFTY50": {
      "constituents": ["ZYTEX", "NEXWAVE", "MORPHO", ...],
      "csv_filename": "SHADOW_NIFTY50.csv"
    }
  }
}
```

---

## 6. API Design

### 6.1 RESTful API Specification

**Base URL:** `http://localhost:8000/api/v1`

**Authentication:**

- Method: JWT Bearer tokens
- Header: `Authorization: Bearer <token>`
- Token expiry: 7 days (configurable)

**Standard Response Format:**

```json
{
  "status": "success" | "error",
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2025-11-04T10:30:00Z"
}
```

**Error Response:**

```json
{
  "status": "error",
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "You don't have enough cash for this trade.",
    "details": {
      "required": 50000,
      "available": 30000
    }
  },
  "timestamp": "2025-11-04T10:30:00Z"
}
```

### 6.2 Endpoint Catalog

**Authentication Endpoints:**

```bash
POST /api/auth/register
Body: {
  "username": "priya_sharma",
  "password": "SecurePass123!",
  "email": "priya@example.com",
  "role": "student",
  "full_name": "Priya Sharma",
  "date_of_birth": "2010-05-15"
}
Response: {
  "status": "success",
  "data": {
    "user_id": 42,
    "token": "eyJ..."
  }
}

POST /api/auth/login
Body: {
  "username": "priya_sharma",
  "password": "SecurePass123!"
}
Response: {
  "status": "success",
  "data": {
    "user": {...},
    "token": "eyJ..."
  }
}

GET /api/auth/me
Headers: Authorization: Bearer <token>
Response: {
  "status": "success",
  "data": {
    "id": 42,
    "username": "priya_sharma",
    "role": "student",
    ...
  }
}
```

**Game Management:**

```bash
POST /api/games
Body: {
  "name": "My First Simulation",
  "difficulty": "easy",
  "initial_capital": 1000000
}
Response: {
  "status": "success",
  "data": {
    "game_id": 123,
    "created_at": "2025-11-04T10:00:00Z"
  }
}

GET /api/games/{game_id}
Response: {
  "status": "success",
  "data": {
    "id": 123,
    "name": "My First Simulation",
    "current_cash": 985000,
    "current_value": 1045000,
    "current_day": 45,
    "total_days": 365,
    "status": "active",
    "portfolio": {
      "positions": [...],
      "metrics": {...}
    }
  }
}

POST /api/games/{game_id}/advance
Body: {
  "days": 1  # or 7 for week, 30 for month
}
Response: {
  "status": "success",
  "data": {
    "current_day": 46,
    "portfolio_value": 1046500,
    "daily_return": 0.14,
    "events": [
      {
        "type": "price_update",
        "symbol": "ZYTEX",
        "old_price": 345.60,
        "new_price": 348.90
      }
    ]
  }
}

DELETE /api/games/{game_id}
Response: {
  "status": "success",
  "message": "Game deleted successfully"
}
```

**Trading Endpoints:**

```bash
POST /api/trades/execute
Body: {
  "game_id": 123,
  "symbol": "ZYTEX",
  "side": "BUY",
  "quantity": 100,
  "order_type": "MARKET"
}
Response: {
  "status": "success",
  "data": {
    "trade_id": 456,
    "executed_price": 345.70,
    "quantity": 100,
    "total_cost": 34604.10,
    "charges": {
      "brokerage": 10.37,
      "stt": 0.00,
      "exchange": 1.12,
      "gst": 2.07
    },
    "new_cash_balance": 950395.90
  }
}

GET /api/trades/{game_id}?page=1&limit=50
Response: {
  "status": "success",
  "data": {
    "trades": [...],
    "total": 23,
    "page": 1,
    "pages": 1
  }
}

GET /api/portfolio/{game_id}
Response: {
  "status": "success",
  "data": {
    "cash": 950395.90,
    "positions_value": 94604.10,
    "total_value": 1045000.00,
    "positions": [
      {
        "symbol": "ZYTEX",
        "quantity": 100,
        "avg_buy_price": 345.70,
        "current_price": 348.90,
        "market_value": 34890.00,
        "unrealized_pnl": 320.00,
        "unrealized_pnl_pct": 0.93,
        "sector": "Healthcare"
      }
    ],
    "sector_allocation": {
      "Healthcare": 36.8,
      "IT": 32.5,
      "Finance": 30.7
    }
  }
}
```

**Market Data Endpoints:**

```bash
GET /api/assets?sector=IT&limit=50
Response: {
  "status": "success",
  "data": {
    "assets": [
      {
        "symbol": "NEXWAVE",
        "display_name": "Nexwave Technologies Inc.",
        "sector": "Information Technology",
        "current_price": 678.90,
        "day_change": 2.35,
        "day_change_pct": 0.35
      }
    ],
    "total": 95
  }
}

GET /api/assets/{symbol}
Response: {
  "status": "success",
  "data": {
    "symbol": "ZYTEX",
    "display_name": "Zytex Pharmaceuticals Ltd.",
    "sector": "Healthcare",
    "industry": "Pharmaceuticals",
    "current_price": 348.90,
    "statistics": {
      "avg_volume": 1234567,
      "52w_high": 389.50,
      "52w_low": 289.30,
      "volatility": 0.023,
      "beta": 1.05
    }
  }
}

GET /api/assets/{symbol}/chart?start_day=0&end_day=90
Response: {
  "status": "success",
  "data": {
    "symbol": "ZYTEX",
    "ohlcv": [
      {
        "day_index": 0,
        "date": "2015-01-01",
        "open": 245.30,
        "high": 248.75,
        "low": 243.10,
        "close": 246.90,
        "volume": 1234567
      },
      ...
    ],
    "indicators": {
      "sma_20": [247.50, 248.30, ...],
      "sma_50": [245.80, 246.20, ...]
    }
  }
}

GET /api/assets/search?q=pharma
Response: {
  "status": "success",
  "data": {
    "results": [
      {
        "symbol": "ZYTEX",
        "display_name": "Zytex Pharmaceuticals Ltd.",
        "sector": "Healthcare",
        "match_score": 0.95
      }
    ]
  }
}
```

**Analytics Endpoints:**

```bash
GET /api/metrics/{game_id}/performance
Response: {
  "status": "success",
  "data": {
    "total_return": 4.5,
    "total_return_pct": 4.5,
    "annualized_return": 36.8,
    "daily_returns": {
      "mean": 0.12,
      "std": 1.23,
      "min": -5.67,
      "max": 8.90
    },
    "sharpe_ratio": 1.47,
    "sortino_ratio": 2.13,
    "calmar_ratio": 1.89
  }
}

GET /api/metrics/{game_id}/risk
Response: {
  "status": "success",
  "data": {
    "max_drawdown": 12.34,
    "current_drawdown": 2.45,
    "volatility": 15.67,
    "var_95": 23456.78,
    "beta": 1.15,
    "concentration": {
      "herfindahl_index": 0.23,
      "top_3_allocation": 67.8,
      "max_position_pct": 36.8
    }
  }
}

GET /api/metrics/{game_id}/attribution
Response: {
  "status": "success",
  "data": {
    "sector_returns": {
      "Healthcare": 6.7,
      "IT": 3.2,
      "Finance": 1.9
    },
    "top_performers": [
      {"symbol": "ZYTEX", "return_pct": 8.9},
      {"symbol": "NEXWAVE", "return_pct": 5.4}
    ],
    "bottom_performers": [
      {"symbol": "MORPHO", "return_pct": -3.2}
    ]
  }
}

GET /api/metrics/{game_id}/trades-analysis
Response: {
  "status": "success",
  "data": {
    "total_trades": 23,
    "winning_trades": 15,
    "losing_trades": 8,
    "win_rate": 65.22,
    "avg_gain": 1234.56,
    "avg_loss": -678.90,
    "profit_factor": 2.73,
    "avg_holding_days": 12.5
  }
}
```

**AI Coach Endpoints:**

```bash
POST /api/coach/feedback
Body: {
  "game_id": 123,
  "context": "trade",  # or "portfolio", "general"
  "last_trade_id": 456
}
Response: {
  "status": "success",
  "data": {
    "feedback": [
      "You've increased your pharma sector exposure to 37%. This adds concentration risk.",
      "Consider taking partial profits on ZYTEX (+8.9%) to lock in gains.",
      "Next: Learn about sector rotation strategies in the Lessons tab."
    ],
    "sentiment": "cautious",
    "risk_score": 6.2
  }
}

POST /api/coach/ask
Body: {
  "game_id": 123,
  "question": "Should I sell ZYTEX now?"
}
Response: {
  "status": "success",
  "data": {
    "answer": "As an educational coach, I can't give specific buy/sell advice. However, consider these factors: 1) Your gain of 8.9% meets many investors' profit targets, 2) Taking partial profits reduces risk, 3) Review your original investment thesis - has anything changed?",
    "related_lessons": ["profit-taking", "position-sizing"]
  }
}

GET /api/coach/lessons?category=risk_management
Response: {
  "status": "success",
  "data": {
    "lessons": [
      {
        "id": "lesson_001",
        "title": "Understanding Diversification",
        "duration_mins": 5,
        "difficulty": "beginner",
        "content_url": "/lessons/diversification.md"
      }
    ]
  }
}

POST /api/coach/quiz
Body: {
  "topic": "risk_management",
  "difficulty": "medium"
}
Response: {
  "status": "success",
  "data": {
    "quiz_id": 789,
    "questions": [
      {
        "id": 1,
        "text": "What is diversification?",
        "type": "multiple_choice",
        "options": [
          "Buying many stocks from the same sector",
          "Spreading investments across different assets",
          "Only investing in large-cap stocks",
          "Keeping all money in cash"
        ],
        "correct_answer": 1
      }
    ]
  }
}
```

**Tournament Endpoints:**

```bash
POST /api/tournaments (teacher only)
Body: {
  "name": "Class 10-B Winter Tournament",
  "description": "6-week simulation",
  "difficulty": "medium",
  "start_date": "2025-11-10",
  "end_date": "2025-12-22",
  "max_participants": 40
}
Response: {
  "status": "success",
  "data": {
    "tournament_id": 789
  }
}

POST /api/tournaments/{id}/join
Body: {
  "game_id": 123
}
Response: {
  "status": "success",
  "message": "Successfully joined tournament"
}

GET /api/tournaments/{id}/leaderboard
Response: {
  "status": "success",
  "data": {
    "tournament": {...},
    "leaderboard": [
      {
        "rank": 1,
        "username": "priya_sharma",
        "return_pct": 12.34,
        "sharpe_ratio": 1.89,
        "max_drawdown": 8.90
      },
      ...
    ]
  }
}
```

**Admin/Teacher Endpoints:**

```bash
GET /api/admin/students (teacher only)
Response: {
  "status": "success",
  "data": {
    "students": [
      {
        "id": 42,
        "username": "priya_sharma",
        "games_played": 3,
        "avg_return": 6.7,
        "last_active": "2025-11-03"
      }
    ]
  }
}

GET /api/admin/export/{game_id}?format=csv
Response: CSV file download
Headers: Content-Disposition: attachment; filename="game_123_report.csv"
```

### 6.3 WebSocket API (Future Enhancement)

**For real-time updates:**

```bash
WS /ws/game/{game_id}

Client -> Server:
{
  "type": "subscribe",
  "channels": ["portfolio", "prices", "notifications"]
}

Server -> Client:
{
  "type": "price_update",
  "data": {
    "symbol": "ZYTEX",
    "price": 349.20,
    "change": 0.09
  }
}

{
  "type": "notification",
  "data": {
    "message": "Your limit order for NEXWAVE was filled!",
    "severity": "success"
  }
}
```

---

## 7. Data Flow Diagrams

### 7.1 Trade Execution Flow

```bash
┌──────────┐                                                 ┌──────────┐
│  Client  │                                                 │  Server  │
│   (TUI)  │                                                 │ (FastAPI)│
└────┬─────┘                                                 └────┬─────┘
     │                                                            │
     │ 1. User presses 'T' key                                    │
     │                                                            │
     ├──> 2. Open TradeModal(symbol, current_price)               │
     │                                                            │
     │ 3. User enters: BUY 100 ZYTEX @ MARKET                     │
     │                                                            │
     ├──────── POST /api/trades/execute ──────────────────────>   │
     │         {game_id, symbol, side, qty, type}                 │
     │                                                            │
     │                                        4. Validate order   │
     │                                           ├─> Check cash   │
     │                                           ├─> Check limits │
     │                                           └─> Get price    │
     │                                                            │
     │                                        5. Execute trade    │
     │                                           ├─> Deduct cash  │
     │                                           ├─> Create/Update│
     │                                           │   position     │
     │                                           └─> Record trade │
     │                                                            │
     │                                        6. Calculate metrics│
     │                                                            │
     │                                        7. Trigger Ollama   │
     │                                           (async)          │
     │                                                            │
     │  <──────── Response: {trade_id, execution_details}  ───────┤
     │                                                            │
     │ 8. Display confirmation notification                       │
     │                                                            │
     │ 9. Refresh portfolio grid                                  │
     │                                                            │
     ├──────── GET /api/portfolio/{game_id} ──────────────────>   │
     │                                                            │
     │  <──────── Response: {updated portfolio}  ─────────────────┤
     │                                                            │
     │ 10. Update UI with new values                              │
     │                                                            │
     │ 11. Poll coach feedback (after 2s delay)                   │
     │                                                            │
     ├──────── GET /api/coach/feedback ────────────────────────>  │
     │                                                            │
     │                                        12. Ollama responds │
     │                                                            │
     │  <──────── Response: {feedback bullets}  ──────────────────┤
     │                                                            │
     │ 13. Display coach feedback in notification area            │
     │                                                            │
     └────────────────────────────────────────────────────────────┘
```

### 7.2 Day Advance Flow

```bash
┌──────────┐                                                 ┌──────────┐
│  Client  │                                                 │  Server  │
└────┬─────┘                                                 └────┬─────┘
     │                                                            │
     │ 1. User presses SPACE bar                                  │
     │                                                            │
     ├──────── POST /api/games/{id}/advance ──────────────────>   │
     │         {days: 1}                                          │
     │                                                            │
     │                                        2. Load game state  │
     │                                                            │
     │                                        3. For each position│
     │                                           ├─> day_idx++    │
     │                                           ├─> Read CSV     │
     │                                           ├─> Update price │
     │                                           └─> Calc P&L     │
     │                                                            │
     │                                        4. Check pending    │
     │                                           limit orders     │
     │                                           ├─> If triggered │
     │                                           └─> Execute      │
     │                                                            │
     │                                        5. Check corporate  │
     │                                           actions (splits, │
     │                                           dividends)       │
     │                                                            │
     │                                        6. Create snapshot  │
     │                                           in portfolio_    │
     │                                           snapshots table  │
     │                                                            │
     │                                        7. Calculate daily  │
     │                                           metrics          │
     │                                                            │
     │  <──────── Response: {new_state, events}  ─────────────────┤
     │                                                            │
     │ 8. Animate price changes in UI                             │
     │                                                            │
     │ 9. Update header (day counter, net worth)                  │
     │                                                            │
     │ 10. Show event notifications if any                        │
     │     (e.g., "ZYTEX announced 1:2 split")                    │
     │                                                            │
     └────────────────────────────────────────────────────────────┘
```

### 7.3 Data Scrambling Pipeline

```bash
┌────────────────┐       ┌──────────────┐        ┌─────────────────┐
│   yfinance     │       │  Scrambler   │        │  Output CSVs    │
│  (NSE Data)    │       │   Pipeline   │        │  (Anonymized)   │
└───────┬────────┘       └──────┬───────┘        └────────┬────────┘
        │                       │                         │
        │ 1. Download           │                         │
        │    TCS.NS             │                         │
        │    INFY.NS            │                         │
        │    RELIANCE.NS        │                         │
        │    (500 tickers)      │                         │
        │                       │                         │
        ├──────────────────────>│ 2. For each ticker:     │
        │                       │    ├─> Generate random  │
        │                       │    │   seed             │
        │                       │    ├─> Circular shift   │
        │                       │    │   returns (k days) │
        │                       │    ├─> Scale volatility │
        │                       │    │   (0.85-1.25×)     │
        │                       │    ├─> Graft segments   │
        │                       │    │   from other stocks│
        │                       │    ├─> Add Gaussian     │
        │                       │    │   noise (σ=0.003)  │
        │                       │    └─> Rebase prices    │
        │                       │        (₹50-₹2000)      │
        │                       │                         │
        │                       │ 3. Assign fictional     │
        │                       │    ticker (ZYTEX, etc.) │
        │                       │                         │
        │                       ├────────────────────────>│ 4. Write CSV
        │                       │                         │    ZYTEX.csv
        │                       │                         │
        │                       │ 5. Generate universe.json│
        │                       │    with metadata        │
        │                       │                         │
        │                       ├────────────────────────>│ universe.json
        │                       │                         │
        │                       │ 6. Validation:          │
        │                       │    ├─> Statistical tests│
        │                       │    │   (KS test, etc.)  │
        │                       │    ├─> Correlation check│
        │                       │    └─> No exact matches │
        │                       │        to originals     │
        │                       │                         │
        └───────────────────────┴─────────────────────────┴─────────┘
```

### 7.4 Ollama Coach Integration

```bash
┌──────────┐         ┌──────────┐         ┌──────────┐
│  FastAPI │         │  Ollama  │         │  Model   │
│  Server  │         │  HTTP    │         │ (Llama)  │
└────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                     │
     │ 1. User makes trade│                     │
     │                    │                     │
     │ 2. Build prompt    │                     │
     │    with context    │                     │
     │                    │                     │
     ├──── POST /api/generate ───────────────>  │
     │    {model: qwen3:8b,                     │
     │     prompt: "...",                       │
     │     temperature: 0.7}                    │
     │                    │                     │
     │                    ├──────────────────>  │ 3. Generate
     │                    │                     │    response
     │                    │                     │    (5-10s)
     │                    │                     │
     │                    │  <────────────────  │ 4. Return text
     │                    │                     │
     │  <─── Response: {response: "..."}  ──────┤
     │                    │                     │
     │ 5. Post-process:   │                     │
     │    ├─> Remove      │                     │
     │    │   specific    │                     │
     │    │   ticker refs │                     │
     │    ├─> Format as   │                     │
     │    │   bullets     │                     │
     │    └─> Cache       │                     │
     │        (30 mins)   │                     │
     │                    │                     │
     │ 6. Store in DB     │                     │
     │    (coach_         │                     │
     │    interactions)   │                     │
     │                    │                     │
     │ 7. Return to       │                     │
     │    client          │                     │
     │                    │                     │
     └────────────────────┴─────────────────────┴─────────┘
```

---

## 8. Security Architecture

### 8.1 Threat Model

**Assets to Protect:**

1. User credentials (passwords)
2. Game state data (portfolio, trades)
3. Coach interaction history
4. Original ticker mappings (scrambling seeds)

**Threat Actors:**

1. Curious students trying to reverse-engineer data
2. Malicious users attempting SQL injection
3. Unauthorized access to other users' data
4. Local system compromise

**Attack Vectors:**

1. API endpoint exploitation
2. SQL injection via input fields
3. JWT token theft/replay
4. File system access to raw data
5. Command injection via Ollama calls

### 8.2 Security Controls

#### 8.2.1 Authentication & Authorization

```python
# JWT Token Structure
{
  "sub": "user_id_42",
  "username": "priya_sharma",
  "role": "student",
  "exp": 1730998800,  # 7 days from issue
  "iat": 1730394000
}

# Password Hashing
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Role-Based Access Control (RBAC)
from functools import wraps

def require_role(allowed_roles: List[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if user.role not in allowed_roles:
                raise HTTPException(403, "Forbidden")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.post("/api/tournaments")
@require_role(["teacher", "admin"])
async def create_tournament(...):
    ...
```

#### 8.2.2 Input Validation

```python
from pydantic import BaseModel, validator, conint, confloat

class TradeRequest(BaseModel):
    game_id: int
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: conint(gt=0, le=1000000)  # max 1M shares
    order_type: Literal["MARKET", "LIMIT"]
    limit_price: Optional[confloat(gt=0)] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{3,10}, v):
            raise ValueError('Invalid symbol format')
        return v
    
    @validator('limit_price', always=True)
    def validate_limit_price(cls, v, values):
        if values.get('order_type') == 'LIMIT' and v is None:
            raise ValueError('Limit price required for LIMIT orders')
        return v

# SQL Injection Prevention (using SQLAlchemy ORM)
from sqlalchemy import select

async def get_user_games(user_id: int):
    # Safe: parameterized query
    stmt = select(Game).where(Game.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Command Injection Prevention (Ollama calls)
import subprocess

def call_ollama_safe(prompt: str):
    # Use list args, never shell=True
    proc = subprocess.run(
        ['ollama', 'run', 'qwen3:8b', prompt],
        capture_output=True,
        text=True,
        timeout=30,
        shell=False  # Critical!
    )
    return proc.stdout
```

#### 8.2.3 Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/coach/ask")
@limiter.limit("10/minute")  # 10 requests per minute
async def ask_coach(request: Request, ...):
    ...

@app.post("/api/trades/execute")
@limiter.limit("60/minute")  # 60 trades per minute
async def execute_trade(...):
    ...
```

#### 8.2.4 Data Encryption

```python
# Database Encryption (optional, for sensitive deployments)
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()

# Usage in models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email_encrypted = Column(String)  # Encrypted at rest
    
    @property
    def email(self):
        return cipher.decrypt(self.email_encrypted)
    
    @email.setter
    def email(self, value):
        self.email_encrypted = cipher.encrypt(value)
```

#### 8.2.5 Logging & Audit Trail

```python
import logging
from pythonjsonlogger import jsonlogger

# Structured logging
logger = logging.getLogger("Artha")
logHandler = logging.FileHandler("logs/audit.log")
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Audit logging decorator
def audit_log(action: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            logger.info(
                "audit_event",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "action": action,
                    "timestamp": datetime.utcnow().isoformat(),
                    "ip_address": request.client.host
                }
            )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.post("/api/trades/execute")
@audit_log("TRADE_EXECUTE")
async def execute_trade(...):
    ...
```

### 8.3 Privacy Protection

**Data Minimization:**

- No PII required except username and optional email
- Date of birth for age verification only (not stored if not needed)
- No IP logging in production (only in dev)

**Data Anonymization:**

- Original ticker mappings never exposed via API
- Seeds for scrambling stored in encrypted config
- Hash original tickers using SHA-256 + salt

**User Rights:**

- Data export: GET /api/users/me/export → ZIP with all user data
- Data deletion: DELETE /api/users/me → GDPR-compliant cascading delete
- Consent management: Explicit checkbox for data processing

---

## 9. Performance & Scalability

### 9.1 Performance Requirements

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| API Response Time (p95) | <200ms | Prometheus histogram |
| API Response Time (p99) | <500ms | Prometheus histogram |
| Database Query Time | <50ms | SQLAlchemy logging |
| CSV Load Time (single asset) | <100ms | timeit |
| Day Advance (full portfolio) | <1s | End-to-end timer |
| Ollama Coach Response | <10s | External call timer |
| UI Frame Rate | >30 FPS | Textual profiler |
| Memory Usage | <500MB | psutil |

### 9.2 Optimization Strategies

#### 9.2.1 Database Optimization

```sql
-- Indexes (already in schema, repeated for emphasis)
CREATE INDEX idx_games_user_status ON games(user_id, status);
CREATE INDEX idx_positions_game_symbol ON positions(game_id, symbol);
CREATE INDEX idx_trades_game_day ON trades(game_id, executed_day);
CREATE INDEX idx_snapshots_game_day ON portfolio_snapshots(game_id, day_index);

-- Denormalization for read performance
ALTER TABLE positions ADD COLUMN market_value REAL;  -- Cached calculation
ALTER TABLE games ADD COLUMN current_value REAL;     -- Cached total value

-- Query optimization example
-- Bad: N+1 query problem
SELECT * FROM positions WHERE game_id = 123;
-- Then for each position:
SELECT current_price FROM assets WHERE symbol = position.symbol;

-- Good: Single query with JOIN
SELECT p.*, a.csv_filename 
FROM positions p
JOIN assets a ON p.symbol = a.symbol
WHERE p.game_id = 123;
```

#### 9.2.2 Caching Strategy

```python
from functools import lru_cache
import redis

# In-memory cache for asset data
@lru_cache(maxsize=100)
def load_asset_csv(symbol: str) -> pd.DataFrame:
    return pd.read_csv(f"data/scrambled/{symbol}.csv")

# Redis cache for API responses (optional, overkill for MVP)
import redis.asyncio as aioredis

redis_client = aioredis.from_url("redis://localhost")

async def get_portfolio_cached(game_id: int):
    cache_key = f"portfolio:{game_id}"
    cached = await redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    portfolio = await get_portfolio_from_db(game_id)
    await redis_client.setex(
        cache_key,
        30,  # TTL: 30 seconds
        json.dumps(portfolio, default=str)
    )
    return portfolio
```

#### 9.2.3 Async I/O

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import asyncio
import httpx

# Async database operations
engine = create_async_engine("sqlite+aiosqlite:///Artha.db")

async def execute_trade_async(trade_request: TradeRequest):
    async with AsyncSession(engine) as session:
        # All DB operations are non-blocking
        game = await session.get(Game, trade_request.game_id)
        position = await session.execute(
            select(Position).where(
                Position.game_id == trade_request.game_id,
                Position.symbol == trade_request.symbol
            )
        )
        # ... trade logic
        await session.commit()

# Async external calls (Ollama)
async def get_coach_feedback_async(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen3:8b", "prompt": prompt},
            timeout=30.0
        )
        return response.json()

# Parallel operations
async def advance_day_with_feedback(game_id: int):
    # Execute day advance and get coach feedback in parallel
    day_result, coach_result = await asyncio.gather(
        advance_day_logic(game_id),
        get_coach_feedback_async(build_prompt(game_id)),
        return_exceptions=True  # Don't fail if Ollama is down
    )
    return day_result, coach_result
```

#### 9.2.4 Data Loading Optimization

```python
# Lazy loading with chunking
class ChunkedDataLoader:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.csv_path = f"data/scrambled/{symbol}.csv"
        self.chunk_size = 1000  # Load 1000 rows at a time
    
    def get_range(self, start_day: int, end_day: int) -> pd.DataFrame:
        # Only read relevant rows, not entire file
        return pd.read_csv(
            self.csv_path,
            skiprows=range(1, start_day + 1),  # Skip header + rows before start
            nrows=end_day - start_day + 1
        )

# Preload hot data on startup
async def warmup_cache():
    # Load Nifty 50 constituents into memory
    nifty50_symbols = load_nifty50_list()
    await asyncio.gather(*[
        asyncio.to_thread(load_asset_csv, symbol)
        for symbol in nifty50_symbols
    ])
```

### 9.3 Scalability Considerations

**Vertical Scaling (Single Machine):**

- Target: 500 concurrent users on 8GB RAM, 4-core CPU
- SQLite can handle 10,000 users with proper indexing
- Each user's data: ~10KB per game session
- Total storage: 10KB × 10,000 = 100MB (manageable)

**Horizontal Scaling (Future):**

- Phase 2: Move to PostgreSQL for multi-server deployments
- Read replicas for analytics queries
- Session affinity for WebSocket connections
- Shared Redis cache across instances

**Database Sharding (Not MVP):**

```python
# Future: Shard by user_id
def get_shard_id(user_id: int) -> int:
    return user_id % NUM_SHARDS

def get_db_connection(user_id: int):
    shard = get_shard_id(user_id)
    return db_connections[shard]
```

---

## 10. Deployment Architecture

### 10.1 Local Development Setup

```bash
# Directory structure
Artha/
├── server/
│   ├── main.py              # FastAPI app
│   ├── models.py            # SQLAlchemy models
│   ├── services/
│   │   ├── game_engine.py
│   │   ├── trade_executor.py
│   │   ├── analytics.py
│   │   └── coach.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── games.py
│   │   ├── trades.py
│   │   └── coach.py
│   └── utils/
│       ├── security.py
│       └── logging.py
├── client/
│   ├── app.py               # Textual app
│   ├── screens/
│   │   ├── login.py
│   │   ├── dashboard.py
│   │   └── game.py
│   ├── widgets/
│   │   ├── chart.py
│   │   ├── portfolio_grid.py
│   │   └── trade_modal.py
│   └── styles.css           # Textual CSS
├── data/
│   ├── raw/                 # gitignored
│   ├── scrambled/           # version controlled
│   └── universe.json
├── scripts/
│   ├── download_data.py     # yfinance downloader
│   ├── scramble_data.py     # Data transformation
│   └── setup_db.py          # Database initialization
├── tests/
│   ├── test_api.py
│   ├── test_game_engine.py
│   └── test_scrambling.py
├── requirements.txt
├── pyproject.toml
├── README.md
└── .env                     # Environment variables
```

### 10.2 Installation Script

```bash
#!/bin/bash
# install.sh - One-command setup

echo "🎮 Installing Artha..."

# Check Python version
if ! python3 --version | grep -q "3.1[0-9]"; then
    echo "❌ Python 3.10+ required"
    exit 1
fi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Install from https://ollama.ai"
    echo "   Run: curl -fsSL https://ollama.com/install.sh | sh"
else
    echo "✓ Ollama found"
    ollama pull qwen3:8b
fi

# Setup directories
mkdir -p ~/.Artha/{data,db,logs}
mkdir -p data/{raw,scrambled}

# Download sample data (optional)
read -p "Download sample NSE data? (10GB, 30 mins) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python scripts/download_data.py --tickers-file config/nifty500.txt
    python scripts/scramble_data.py
fi

# Initialize database
python scripts/setup_db.py

echo "✅ Installation complete!"
echo "   Start server: python -m Artha serve"
echo "   Start client: python -m Artha play"
```

### 10.3 Configuration Management

```yaml
# config.yaml
app:
  name: Artha
  version: 1.0.0
  debug: false

server:
  host: localhost
  port: 8000
  reload: false
  workers: 1

database:
  url: sqlite+aiosqlite:///~/.Artha/db/Artha.db
  echo: false
  pool_size: 10

data:
  universe_file: data/universe.json
  scrambled_dir: data/scrambled/
  cache_size: 100  # assets

ollama:
  base_url: http://localhost:11434
  model: qwen3:8b
  temperature: 0.7
  timeout: 30

security:
  secret_key: ${SECRET_KEY}  # From environment
  jwt_expiry_days: 7
  bcrypt_rounds: 12

features:
  coach_enabled: true
  tournaments_enabled: true
  achievements_enabled: true

limits:
  max_positions: 50
  max_trades_per_day: 100
  coach_requests_per_hour: 20

logging:
  level: INFO
  format: json
  file: ~/.Artha/logs/app.log
  rotation: 10MB
```

### 10.4 Process Management

```python
# Artha/__main__.py
import click
import uvicorn
from client.app import ArthaApp

@click.group()
def cli():
    """Artha CLI"""
    pass

@cli.command()
@click.option('--port', default=8000, help='Server port')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(port, reload):
    """Start FastAPI server"""
    uvicorn.run(
        "server.main:app",
        host="localhost",
        port=port,
        reload=reload,
        log_level="info"
    )

@cli.command()
def play():
    """Start TUI client"""
    app = ArthaApp()
    app.run()

@cli.command()
def setup():
    """Initialize database and download data"""
    from scripts.setup_db import init_db
    from scripts.download_data import download_nifty500
    
    click.echo("Setting up database...")
    init_db()
    
    if click.confirm("Download NSE data?"):
        download_nifty500()
    
    click.echo("Setup complete!")

if __name__ == "__main__":
    cli()
```

**Usage:**

```bash
# Development
python -m Artha serve --reload
python -m Artha play

# Production
python -m Artha serve --port 8000
```

---

## 11. Technology Stack

### 11.1 Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | FastAPI | 0.104+ | REST API server |
| **ASGI Server** | Uvicorn | 0.24+ | Production server |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Database** | SQLite | 3.40+ | Persistent storage |
| **Data Processing** | pandas | 2.1+ | CSV handling, time series |
| **Numerical** | numpy | 1.24+ | Mathematical operations |
| **Statistics** | scipy | 1.11+ | Statistical functions |
| **ML (optional)** | scikit-learn | 1.3+ | Clustering, PCA |
| **Validation** | Pydantic | 2.4+ | Data validation |
| **Auth** | python-jose | 3.3+ | JWT tokens |
| **Password** | bcrypt | 4.0+ | Password hashing |
| **HTTP Client** | httpx | 0.25+ | Async HTTP (Ollama) |
| **Task Queue** | asyncio | stdlib | Async operations |

### 11.2 Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **TUI Framework** | Textual | 0.41+ | Terminal UI |
| **Charts** | plotext | 5.2+ | ASCII/Unicode charts |
| **HTTP Client** | httpx | 0.25+ | API calls |
| **Config** | PyYAML | 6.0+ | Configuration |

### 11.3 Data & AI Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Market Data** | yfinance | 0.2.32+ | NSE/BSE historical data |
| **LLM Runtime** | Ollama | 0.1.16+ | Local AI inference |
| **LLM Model** | Llama 3.2 | 3B | AI coach |
| **Alt. Model** | Mistral | 7B | Alternative coach |

### 11.4 Development Tools

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Testing** | pytest | 7.4+ | Unit/integration tests |
| **Mocking** | pytest-mock | 3.12+ | Test mocks |
| **Coverage** | pytest-cov | 4.1+ | Code coverage |
| **Linting** | ruff | 0.1+ | Fast linter |
| **Formatting** | black | 23.10+ | Code formatting |
| **Type Checking** | mypy | 1.6+ | Static type checking |
| **Documentation** | mkdocs | 1.5+ | Documentation site |

### 11.5 Dependency Management

```toml
# pyproject.toml
[project]
name = "Artha"
version = "1.0.0"
description = "Stock market learning simulator for Indian teenagers"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.19.0",
    "pandas>=2.1.0",
    "numpy>=1.24.0",
    "scipy>=1.11.0",
    "textual>=0.41.0",
    "plotext>=5.2.0",
    "yfinance>=0.2.32",
    "pydantic>=2.4.0",
    "python-jose[cryptography]>=3.3.0",
    "bcrypt>=4.0.0",
    "httpx>=0.25.0",
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "black>=23.10.0",
    "mypy>=1.6.0",
]

[project.scripts]
Artha = "Artha.__main__:cli"

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## 12. Integration Points

### 12.1 External Systems

#### **yfinance → Artha**

```python
# One-time data download (offline after this)
import yfinance as yf

def download_nse_universe(tickers: List[str]):
    for ticker in tickers:
        try:
            df = yf.download(
                ticker + ".NS",
                start="2015-01-01",
                end="2025-11-04",
                progress=False,
                auto_adjust=True  # Adjust for splits/dividends
            )
            df.to_csv(f"data/raw/{ticker}.csv")
        except Exception as e:
            logger.error(f"Failed to download {ticker}: {e}")
```

#### **Ollama ← Artha**

```python
# Runtime integration (local HTTP)
import httpx

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate(self, prompt: str, model="qwen3:8b"):
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json()["response"]
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
```

### 12.2 Future Integrations (Post-MVP)

**DIKSHA/CBSE Integration:**

- Export learning progress in CBSE digital format
- OAuth integration with DIKSHA platform
- Curriculum mapping API

**School LMS Integration:**

- Google Classroom roster import
- Microsoft Teams assignment sync
- Moodle grade export

**WhatsApp Bot (via Twilio):**

- Daily portfolio summaries
- Achievement notifications
- Tournament updates

---

## 13. Appendices

### 13.1 Glossary

- **OHLCV**: Open, High, Low, Close, Volume (stock price data)
- **NSE**: National Stock Exchange of India
- **BSE**: Bombay Stock Exchange
- **STT**: Securities Transaction Tax
- **TUI**: Text User Interface
- **Scrambling**: Data anonymization technique
- **Sharpe Ratio**: Risk-adjusted return metric
- **Drawdown**: Peak-to-trough decline
- **Herfindahl Index**: Concentration measure (0-1)
- **VaR**: Value at Risk (risk metric)

### 13.2 References

- NSE India: <https://www.nseindia.com>
- yfinance Documentation: <https://pypi.org/project/yfinance/>
- Textual Framework: <https://textual.textualize.io/>
- Ollama: <https://ollama.ai/>
- SEBI Guidelines: <https://www.sebi.gov.in/>

### 13.3 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-04 | Tech Team | Initial HLD creation |

---

**Document Status:** ✅ Ready for Review  
**Next Steps:**

1. Architecture review meeting
2. Security audit
3. Prototype development kickoff

**Approval Required From:**

- [ ] Technical Lead
- [ ] Product Manager
- [ ] Security Officer
- [ ] Legal/Compliance

---

-- *End of High-Level Design Document* --

# Artha Game Enhancement Plan

## Overview

This document outlines the comprehensive plan to enhance the Artha stock market simulator by addressing four key issues:

1. **Improved Position Tracking**: Implement XIRR concepts and proper transaction history
2. **UI/UX Improvements**: Add charts, graphs, and enhanced visualizations
3. **Game Engine Fix**: Resolve the day limit issue beyond 270-280 days
4. **Enhanced AI Coach**: Implement better memory and data processing for the DSPy-based coach

## Issue 1: Trading Logic Enhancement with XIRR Concepts

### Current Problem

- The current implementation averages buy prices, losing individual transaction details
- Cannot track P&L for each individual purchase separately
- No support for advanced investment calculations like XIRR

### Solution Plan

#### 1. New Transaction-Based Position Model

```python
@dataclass
class Transaction:
    """Individual buy/sell transaction"""
    date: datetime
    symbol: str
    quantity: int
    price: float
    action: OrderSide  # BUY or SELL
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Position:
    """Enhanced position tracking individual transactions"""
    symbol: str
    transactions: List[Transaction] = field(default_factory=list)
    quantity: int = field(init=False)  # Calculated from transactions
    avg_buy_price: float = field(init=False)  # Calculated from buy transactions
    current_price: float
    
    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)
        self._recalculate_position()
    
    def calculate_pnl_for_transaction(self, trans_idx: int) -> float:
        """Calculate P&L for a specific buy transaction if sold"""
        trans = self.transactions[trans_idx]
        if trans.action == OrderSide.BUY and trans_idx < len(self.transactions):
            # Calculate P&L based on current price for this specific purchase
            current_quantity = self._get_quantity_from_transaction(trans_idx)
            return (self.current_price - trans.price) * current_quantity
        return 0.0
    
    def calculate_xirr(self) -> float:
        """Calculate XIRR for this position based on all transactions"""
        # Implementation using scipy.optimize to find the rate that makes NPV = 0
        # Cash flows: negative for buys, positive for sells
        cash_flows = []
        dates = []
        
        for trans in self.transactions:
            cash_flow = -trans.price * trans.quantity if trans.action == OrderSide.BUY else trans.price * trans.quantity
            cash_flows.append(cash_flow)
            dates.append(trans.date)
        
        # Add current market value as positive cash flow
        current_value = self.quantity * self.current_price
        cash_flows.append(current_value)
        dates.append(datetime.now())
        
        # Calculate XIRR using scipy.optimize
        # (Implementation details would follow financial mathematics)
        return self._compute_xirr(cash_flows, dates)
```

#### 2. Enhanced Trade Executor

```python
class EnhancedTradeExecutor:
    """Updated trade executor with transaction-level tracking"""
    
    @staticmethod
    def execute_buy_with_transaction(
        portfolio: Portfolio,
        symbol: str,
        quantity: int,
        price: float
    ) -> TradeResult:
        """Execute buy creating new transaction"""
        # Validate inputs
        valid, message = TradeExecutor.validate_trade_inputs(symbol, quantity, price)
        if not valid:
            return TradeResult(success=False, message=message)

        # Calculate costs
        cost = price * quantity
        commission = TradeExecutor.calculate_commission(cost)
        total_cost = cost + commission

        # Check if enough cash
        if portfolio.cash < total_cost:
            return TradeResult(
                success=False,
                message=f"Insufficient funds. Need ₹{total_cost:,.2f}, have ₹{portfolio.cash:,.2f}"
            )

        # Deduct cash
        portfolio.cash -= total_cost

        # Find existing position or create new
        existing_pos = None
        for pos in portfolio.positions:
            if pos.symbol == symbol:
                existing_pos = pos
                break

        if existing_pos:
            # Add new transaction to existing position
            new_transaction = Transaction(
                date=datetime.now(),
                symbol=symbol,
                quantity=quantity,
                price=price,
                action=OrderSide.BUY
            )
            existing_pos.add_transaction(new_transaction)
        else:
            # Create new position with first transaction
            new_transaction = Transaction(
                date=datetime.now(),
                symbol=symbol,
                quantity=quantity,
                price=price,
                action=OrderSide.BUY
            )
            new_pos = Position(
                symbol=symbol,
                transactions=[new_transaction],
                current_price=price
            )
            portfolio.positions.append(new_pos)

        return TradeResult(
            success=True,
            message=f"Bought {quantity} shares of {symbol} at ₹{price:,.2f}",
            executed_price=price,
            quantity=quantity,
            total_cost=total_cost,
            commission=commission
        )
```

#### 3. Database Schema Updates

- Modify Position table to support transaction history
- Create Transaction table to store individual trade records
- Maintain backward compatibility with existing data

## Issue 2: UI/UX Improvements with Charts and Data Visualizations

### Current Problem

- Basic UI with no visualizations
- No charts to see stock trends or portfolio performance
- Poor user experience compared to modern financial tools

### Solution Plan

#### 1. Create Custom Chart Widget with plotext

```python
class PortfolioChartWidget(Static):
    """Widget to display portfolio value chart"""
    
    def __init__(self, portfolio_history: List[Dict]):
        super().__init__()
        self.portfolio_history = portfolio_history
    
    def on_mount(self) -> None:
        self.refresh_chart()

    def refresh_chart(self) -> None:
        """Update chart with latest data"""
        import plotext as plt
        
        # Clear any existing plot
        plt.clear_data()
        
        # Add portfolio data
        days = [entry['day'] for entry in self.portfolio_history]
        values = [entry['total_value'] for entry in self.portfolio_history]
        
        plt.plot(days, values, label="Portfolio Value", color="green")
        plt.title("Portfolio Value Over Time")
        plt.xlabel("Day")
        plt.ylabel("Value (₹)")
        
        # Render to text and update widget
        chart_text = plt.build()
        self.update(chart_text)
```

#### 2. Enhanced Dashboard Layout

```python
class DashboardScreen(Screen):
    """Enhanced dashboard with charts and data"""
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("m", "menu", "Menu"),
        ("s", "save", "Save"),
        ("t", "trade", "Trade"),
        ("space", "advance_day", "Next Day"),
        ("c", "coach", "Coach"),
        ("h", "help", "Help"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state

    def compose(self) -> ComposeResult:
        """Create enhanced dashboard layout"""
        yield Header()

        with Container(id="dashboard"):
            # Top summary row
            with Horizontal(id="summary-row"):
                yield Static("Cash: ₹1,00,000", classes="summary-card")
                yield Static("Total Value: ₹1,50,000", classes="summary-card")
                yield Static("P&L: ₹50,000 (33.33%)", classes="summary-card")
            
            # Chart row
            with Horizontal(id="chart-row"):
                yield PortfolioChartWidget(self.game_state.portfolio_history, id="portfolio-chart")
                
            # Portfolio grid and watchlist
            with Horizontal(id="data-row"):
                with Vertical(id="portfolio-col"):
                    yield Static("## Portfolio", classes="section-title")
                    yield PortfolioGrid(id="portfolio-grid")
                with Vertical(id="watchlist-col"):
                    yield Static("## Watchlist", classes="section-title")
                    yield Static(id="watchlist")
        
        yield Footer()
```

#### 3. Data Visualization Widgets

- Portfolio value trend chart
- Individual stock performance charts
- Allocation pie charts
- P&L breakdown by stock
- Enhanced portfolio grid using dataframe-textual

## Issue 3: Game Engine Fix for Day Limit Issue

### Current Problem

- Game freezes beyond 270-280 days
- Likely caused by data loader limitations
- Historical data not sufficient for extended gameplay

### Solution Plan

#### 1. Enhanced Data Loader

```python
def get_price_at_day(self, symbol: str, day_offset: int, max_days: int = 2000) -> float:
    """Get price at specific day offset with extended historical data and simulation"""
    # Try to get extended historical data
    df = self.get_stock_data(symbol, days=max_days)
    if df is not None and not df.empty:
        try:
            idx = -(day_offset + 1)  # Negative index from end
            if abs(idx) <= len(df):
                return float(df['Close'].iloc[idx])
        except IndexError:
            pass
    
    # If historical data unavailable, simulate using last known price
    if df is not None and not df.empty:
        last_price = float(df['Close'].iloc[-1])
        
        # Apply random walk simulation to continue beyond historical data
        # Use market volatility characteristics for realistic simulation
        import random
        # Adjust price by small amount based on market volatility
        volatility_factor = 0.02  # 2% daily volatility
        adjustment = random.uniform(-volatility_factor, volatility_factor)
        return max(1.0, last_price * (1 + adjustment))  # Ensure price doesn't go below ₹1
    
    # Fallback to mock data generation
    return self._generate_fallback_price(symbol)
```

#### 2. Updated Day Advancement Logic

```python
def action_advance_day(self) -> None:
    """Advance game by one day with proper limit handling"""
    # Implement soft limit with warning
    if self.game_state.current_day >= 500:  # Extended from 30 to 500 days
        self.app.notify("Approaching maximum simulation days. Consider starting a new game.", severity="warning")
    elif self.game_state.current_day >= 1000:  # Hard limit
        self.app.notify("Maximum simulation days reached.", severity="error")
        return
    
    # Increment day
    self.game_state.current_day += 1

    # Update prices for all positions
    for position in self.game_state.portfolio.positions:
        new_price = self.app.market_data.get_price_at_day_with_simulation(position.symbol, self.game_state.current_day)
        if new_price > 0:
            position.current_price = new_price

    # Record portfolio state for charting
    self._record_portfolio_state()

    self._refresh_display()
    self.app.notify(f"Advanced to day {self.game_state.current_day}")

    # Auto-save
    asyncio.create_task(self.app._save_current_game())
```

## Issue 4: Enhanced AI Coach with Better Memory and Data Processing

### Current Problem

- Coach only sees current portfolio
- No memory of wealth trends
- Generic responses with no personalized learning
- Limited data for educational feedback

### Solution Plan

#### 1. Coach Memory System

```python
@dataclass
class CoachMemory:
    """Memory structure for the AI coach"""
    trade_history: List[Dict] = field(default_factory=list)
    portfolio_history: List[Dict] = field(default_factory=list)
    user_behavior_patterns: Dict = field(default_factory=dict)
    learning_progress: Dict = field(default_factory=dict)
    feedback_history: List[Dict] = field(default_factory=list)
```

#### 2. Enhanced DSPy Signatures

```python
class EnhancedTradeFeedbackSignature(dspy.Signature):
    """Generate educational feedback with historical context"""
    action: str = dspy.InputField(desc="BUY or SELL")
    symbol: str = dspy.InputField(desc="Stock symbol")
    quantity: int = dspy.InputField(desc="Number of shares")
    price: float = dspy.InputField(desc="Execution price")
    portfolio_value: float = dspy.InputField(desc="Total portfolio value")
    cash_remaining: float = dspy.InputField(desc="Cash remaining after trade")
    num_positions: int = dspy.InputField(desc="Number of positions")
    
    # Historical context
    risk_patterns: dict = dspy.InputField(desc="User's risk-taking patterns")
    diversification_trends: dict = dspy.InputField(desc="Diversification trends") 
    timing_patterns: dict = dspy.InputField(desc="Timing patterns")
    portfolio_trend: float = dspy.InputField(desc="Current portfolio trend percentage")

    feedback: str = dspy.OutputField(
        desc="2-3 personalized educational bullets about this trade based on user's historical patterns"
    )

class PortfolioTrendAnalysisSignature(dspy.Signature):
    """Analyze portfolio trends and user performance"""
    total_return: float = dspy.InputField(desc="Total portfolio return percentage")
    volatility: float = dspy.InputField(desc="Portfolio volatility percentage")
    trend: str = dspy.InputField(desc="General trend (positive/negative/stable)")
    portfolio_size: int = dspy.InputField(desc="Number of portfolio history records")
    user_risk_level: str = dspy.InputField(desc="User's risk level (low/medium/high)")

    insights: str = dspy.OutputField(
        desc="2-3 personalized insights about user's investment behavior based on trend analysis"
    )
```

#### 3. Enhanced Coach Manager

```python
class EnhancedCoachManager:
    """Enhanced AI coach with memory and context"""
    
    def __init__(self):
        self.enabled = setup_dspy()
        self.memory = CoachMemory()
        
        if self.enabled:
            # Initialize enhanced DSPy modules with memory context
            self.trade_feedback_with_context = dspy.ChainOfThought(EnhancedTradeFeedbackSignature)
            self.trend_analysis = dspy.ChainOfThought(PortfolioTrendAnalysisSignature)

    def add_to_memory(self, event_type: str, data: Dict) -> None:
        """Add event to coach memory"""
        timestamp = datetime.now()
        
        if event_type == "trade":
            self.memory.trade_history.append({
                "timestamp": timestamp,
                "data": data
            })
        elif event_type == "portfolio_snapshot":
            self.memory.portfolio_history.append({
                "timestamp": timestamp,
                "day": data["day"],
                "total_value": data["total_value"],
                "cash": data["cash"],
                "positions_value": data["positions_value"],
                "pnl": data["pnl"]
            })
        
        # Clean up old records to prevent memory bloat
        self._clean_memory()

    def get_personalized_insights(self) -> str:
        """Get insights based on historical patterns and trends"""
        if not self.memory.portfolio_history:
            return "Start playing to get personalized insights!"
        
        # Analyze trends and generate personalized feedback
        first_value = self.memory.portfolio_history[0]["total_value"]
        last_value = self.memory.portfolio_history[-1]["total_value"]
        total_return = (last_value - first_value) / first_value * 100
        
        # Calculate other metrics
        values = [entry["total_value"] for entry in self.memory.portfolio_history]
        volatility = self._calculate_volatility(values)
        trend_direction = "positive" if total_return > 0 else "negative"
        
        try:
            result = self.trend_analysis(
                total_return=total_return,
                volatility=volatility,
                trend=trend_direction,
                portfolio_size=len(self.memory.portfolio_history),
                user_risk_level=self._analyze_risk_level()
            )
            
            return result.insights
        except Exception as e:
            return f"Could not generate insights: {str(e)}"
```

## Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)

1. Implement new transaction-based position model
2. Update trade executor with transaction tracking
3. Modify database schema to support transaction history
4. Basic XIRR calculation functionality

### Phase 2: UI/UX Enhancements (Days 3-4)

1. Create chart widgets using plotext
2. Implement enhanced dashboard layout
3. Add data visualization features
4. Update portfolio grid with dataframe-textual

### Phase 3: Game Engine Fixes (Days 5-6)

1. Extend data loader with simulation capabilities
2. Fix day advancement logic
3. Implement portfolio history tracking for charts
4. Add proper limits and warnings

### Phase 4: Enhanced AI Coach (Days 7-8)

1. Implement memory system for coach
2. Create enhanced DSPy signatures
3. Update coach with historical analysis capabilities
4. Add personalized feedback features

### Phase 5: Integration and Testing (Days 9-10)

1. Integrate all components
2. Write comprehensive test suite
3. Fix any integration issues
4. Performance optimization

### Phase 6: Polish and Documentation (Days 11-12)

1. User experience refinements
2. Error handling improvements
3. Documentation updates
4. Final testing and deployment

## Success Criteria

### Issue 1 (Position Tracking)

- ✅ Individual transactions tracked instead of just averaging
- ✅ XIRR calculations available for positions
- ✅ P&L tracked for each individual buy transaction
- ✅ Backward compatibility maintained

### Issue 2 (UI Enhancement)

- ✅ Portfolio value charts displayed
- ✅ Individual stock performance visualization
- ✅ Enhanced portfolio grid with better formatting
- ✅ Modern, intuitive dashboard layout

### Issue 3 (Day Limit)

- ✅ Game runs beyond 270-280 days without freezing
- ✅ Extended simulation period (up to 1000 days)
- ✅ Proper price simulation beyond historical data
- ✅ Performance remains stable at high day counts

### Issue 4 (AI Coach)

- ✅ Coach remembers wealth trends over time
- ✅ Personalized feedback based on user patterns
- ✅ Trend analysis based on historical portfolio data
- ✅ Educational content tailored to user's learning needs

## Risk Mitigation

### Technical Risks

- **Database Migration**: Plan for safe migration from current schema
- **Performance**: Monitor load times with extended historical data
- **Memory Usage**: Implement proper memory management for coach

### Testing Strategy

- Unit tests for each new component
- Integration tests for end-to-end functionality
- Performance tests for large number of days
- User acceptance testing with actual gameplay

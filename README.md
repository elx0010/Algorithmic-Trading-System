# Algorithmic Trading System

Python-based algorithmic trading system for markets with MACD-base strategy execution, MySQL data persistence, comprehensive error handling, and leveraged position management.

## 📊 System Architecture

The bot operates in a continuous loop executing the following workflow:
1. **Data Collection** - Fetches real-time candlestick data from Coinbase API
2. **Technical Analysis** - Calculates MACD, EMA, and signal line indicators using Pandas
3. **Signal Detection** - Evaluates entry/exit conditions based on momentum and crossovers
4. **Order Execution** - Submits market orders via authenticated API requests
5. **Database Logging** - Persists all market data, trades, and account states
6. **Status Reporting** - Outputs real-time position and performance metrics

### Robust Error Handling
- **Fault-Tolerant API Integration** - Try/except blocks for all network requests
- **Timeout Management** - 10-second timeouts prevent hanging connections
- **Automatic Retry Logic** - Continues operation on failed requests with 10-second backoff
- **Status Code Validation** - Verifies successful API responses before execution
- **Failed Order Logging** - Tracks both successful and failed trades for debugging

### Database Architecture
- **MySQL Data Persistence** - Comprehensive logging across multiple tables
- **Market Data Tracking** - MACD values, signal trends, price movements, timestamps
- **Trade History** - Full audit trail with order IDs, prices, quantities, success/failure status
- **Position Management** - Entry/exit tracking with profit/loss calculations (USD & percentage)
- **Account Balance Monitoring** - Real-time ETH and USD balance snapshots

### Security & Best Practices
- **Environment Variables** - Credentials stored securely in `.env` file
- **JWT Authentication** - Secure API access with dynamic token generation
- **API Key Rotation Support** - Easy credential updates via environment config
- **No Hardcoded Secrets** - Production-ready security implementation

## Tech Stack

- **Language**: Python 3.x
- **Exchange API**: Coinbase Advanced Trade API
- **Database**: MySQL 8.x
- **Libraries**:
  - `mysql-connector-python` - Database operations
  - `pandas` - Data analysis and manipulation
  - `numpy` - Numerical computations
  - `requests` - HTTP API calls
  - `python-dotenv` - Environment management
  - `coinbase` - JWT token generation

## Monitoring

The bot prints real-time status including:
- Current ETH price
- Fast/Slow EMA values
- MACD and Signal line values
- Trend directions
- Account balances (USD & ETH)
- Potential profit/loss on open positions


## Future Enhancements

- [ ] Multi-timeframe analysis
- [ ] Additional technical indicators (RSI, Bollinger Bands)
- [ ] Portfolio diversification (multiple cryptocurrencies)
- [ ] Backtesting framework
- [ ] Web dashboard for monitoring
- [ ] SMS/Email alerts for trades
- [ ] Machine learning integration

## Author

Built as a portfolio project demonstrating expertise in:
- Algorithmic trading strategy development
- RESTful API integration
- Database design and management
- Error handling and fault tolerance
- Financial technology (FinTech) applications

---


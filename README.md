# Automated Crypto Trading Bot

Python-based algorithmic trading system for cryptocurrency markets with MACD-based strategy execution, MySQL data persistence, comprehensive error handling, and leveraged position management.

## 🚀 Features

### Trading Strategy
- **MACD Technical Indicator** - Uses 12/26/9 MACD configuration on 4-hour candles
- **Multiple Exit Strategies**
  - Take Profit: 3% gain target
  - Momentum Loss Detection: Sells when MACD decreases by 2.5+ units
  - Bearish Crossover: Automatic exit on MACD/Signal line cross
- **Leveraged Trading** - 3x leverage for amplified returns
- **Smart Entry Logic** - Buys when MACD increases by 10+ units with upward momentum

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

## 🛠️ Tech Stack

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

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL Server 8.0+
- Coinbase Advanced Trade account with API credentials
- Active internet connection for real-time trading

## ⚙️ Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Trading
```

2. **Install dependencies**
```bash
pip install mysql-connector-python pandas numpy requests python-dotenv coinbase
```

3. **Set up MySQL database**
```sql
CREATE DATABASE trader;

USE trader;

CREATE TABLE market_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    MACD_Value FLOAT,
    Signal_Value FLOAT,
    ETH_Price FLOAT,
    MACD_Trend VARCHAR(10),
    Signal_Trend VARCHAR(10),
    Position VARCHAR(50),
    Time DATETIME
);

CREATE TABLE trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Trade_Type VARCHAR(10),
    Time DATETIME,
    Price FLOAT,
    ETH_Quantity FLOAT,
    MACD_Value FLOAT,
    Signal_Value FLOAT,
    Reason VARCHAR(50),
    Order_ID VARCHAR(100),
    Order_Status VARCHAR(20)
);

CREATE TABLE account_balance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ETH_Balance FLOAT,
    USD_Balance FLOAT,
    Time DATETIME
);

CREATE TABLE positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Entry_Time DATETIME,
    Entry_Price FLOAT,
    Exit_Time DATETIME,
    Exit_Price FLOAT,
    Take_Profit FLOAT,
    ETH_Quantity FLOAT,
    Profit_Loss_USD FLOAT,
    Profit_Loss_Percent FLOAT
);
```

4. **Configure environment variables**

Create a `.env` file in the project directory:
```env
DB_Password=your_mysql_password
host=localhost
API_KEY=your_coinbase_api_key
API_SECRET=your_coinbase_api_secret
```

## 🚀 Usage

**Start the trading bot:**
```bash
python "Trader 3.0.py"
```

The bot will:
1. Connect to Coinbase API and MySQL database
2. Fetch 4-hour ETH-USD candlestick data
3. Calculate MACD indicators in real-time
4. Execute trades based on strategy signals
5. Log all activity to the database
6. Print status updates every 15 seconds

## 📊 Trading Logic

### Buy Conditions
- MACD increases by **≥10 units** between candles
- MACD has upward momentum
- No existing ETH position

### Sell Conditions
1. **Take Profit**: Price reaches 3% above buy price
2. **Momentum Loss**: MACD decreases by ≤2.5 units while above signal
3. **Bearish Crossover**: MACD crosses below signal line with downward momentum

## 📈 Monitoring

The bot prints real-time status including:
- Current ETH price
- Fast/Slow EMA values
- MACD and Signal line values
- Trend directions
- Account balances (USD & ETH)
- Potential profit/loss on open positions

## ⚠️ Risk Disclaimer

**This bot trades with real money using 3x leverage.**

- Cryptocurrency trading involves substantial risk of loss
- Past performance does not guarantee future results
- Only trade with capital you can afford to lose
- The author is not responsible for any financial losses
- Test thoroughly in sandbox environment before live trading

## 🔒 Security Notes

- Never commit `.env` file to version control
- Rotate API keys regularly
- Use API keys with trading permissions only (not withdrawal)
- Monitor database access and secure with strong passwords
- Consider implementing 2FA on exchange account

## 📝 Database Queries

**View recent trades:**
```sql
SELECT * FROM trades ORDER BY Time DESC LIMIT 10;
```

**Calculate total profit/loss:**
```sql
SELECT SUM(Profit_Loss_USD) as Total_PnL FROM positions;
```

**Check win rate:**
```sql
SELECT 
    COUNT(CASE WHEN Profit_Loss_USD > 0 THEN 1 END) * 100.0 / COUNT(*) as Win_Rate_Percent
FROM positions 
WHERE Profit_Loss_USD IS NOT NULL;
```

## 🛣️ Future Enhancements

- [ ] Multi-timeframe analysis
- [ ] Additional technical indicators (RSI, Bollinger Bands)
- [ ] Portfolio diversification (multiple cryptocurrencies)
- [ ] Backtesting framework
- [ ] Web dashboard for monitoring
- [ ] SMS/Email alerts for trades
- [ ] Machine learning integration

## 📄 License

This project is provided as-is for educational purposes.

## 👤 Author

Built as a portfolio project demonstrating expertise in:
- Algorithmic trading strategy development
- RESTful API integration
- Database design and management
- Error handling and fault tolerance
- Financial technology (FinTech) applications

---

**⚡ Live Trading Status**: This bot executes real trades with actual capital. Use responsibly.

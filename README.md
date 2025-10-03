# Binance Quantitative Trading Bot (Flask)

A Flask-based backend service for Binance trading, designed for 24/7 cloud deployment (Render, Railway, etc). Uses Binance Testnet for safe development and includes a sample SMA crossover trading strategy.

## Features
- REST API endpoints for health, trading control, and status
- Loads Binance API credentials from `.env` (never hard-coded)
- Uses official `python-binance` library
- Testnet/mainnet switch via `.env` (`BINANCE_MODE`)
- Sample trading strategy (SMA crossover)
- Background trading loop (threaded)
- Logs to console and `logs/trading.log`
- Error handling for API/network issues
- All API responses in JSON

## Setup

1. **Clone the repo**
2. **Create a `.env` file** (see `.env.example`):
   ```
   BINANCE_API_KEY=your_api_key
   BINANCE_SECRET_KEY=your_secret_key
   BINANCE_MODE=test
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run locally**:
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:5000`.

## API Endpoints
- `GET /health` — returns `{ "status": "OK" }`
- `POST /trade/start` — starts the trading loop
- `GET /trade/status` — shows current trading status and PnL

## Deployment (Render Example)
1. Push your code to a GitHub repo
2. Create a new Web Service on [Render](https://render.com/)
3. Set the build and start commands:
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `python app.py`
4. Add your environment variables in the Render dashboard
5. Deploy!

## Notes
- Uses Binance Testnet by default. Switch to mainnet by setting `BINANCE_MODE=live` in `.env`.
- All logs are saved to `logs/trading.log`.
- For production, use a WSGI server (e.g., Gunicorn) and secure your API endpoints.

---

**This project is for educational/demo purposes. Use at your own risk.**

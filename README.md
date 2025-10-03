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
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **API Key Encryption Setup** (using `secure_config.py`):
   ```bash
   python secure_config.py --setup
   ```
   - Enter your Binance API Key and Secret Key when prompted
   - Choose mode: `test` (for testnet) or `live` (for mainnet)
4. **Verify your configuration**:
   ```bash
   python secure_config.py --verify
   ```
5. **Run locally**:
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:5000`.

### MUST READ SecureConfig Notes

- `.encryption_key` and `.env.encrypted` are generated automatically
- Testnet API Key: apply at https://testnet.binance.vision/
- Mainnet API Key: apply at https://www.binance.com/
- **Backup `.encryption_key` to a secure location**
- Do NOT commit your API keys or `.encryption_key` to version control

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

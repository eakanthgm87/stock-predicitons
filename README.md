# StockProj Grow (Django) - Minimal Functional Prototype

Features:
- User authentication (signup/login/logout)
- Custom watchlist per user
- Fetch historical prices (yfinance) via management command
- Simple AI model (RandomForest) for short-term predictions
- Interactive Plotly charts showing actual vs predicted
- Growth index predictor and profit/loss dashboard
- Grow-themed UI (green gradients)

Quick setup (local):
1. Create virtualenv: python -m venv venv && source venv/bin/activate
2. Install: pip install -r requirements.txt
3. Run migrations: python manage.py migrate
4. Create superuser (optional): python manage.py createsuperuser
5. Fetch sample data (example): python manage.py fetch_prices RELIANCE.NS --start 2018-01-01
6. Run server: python manage.py runserver
7. Open http://127.0.0.1:8000/

Notes:
- Ticker suffixes for NSE use `.NS` (yfinance).
- Models are simple and intended as a starting point. Replace AI model with LSTM/Transformer as needed.

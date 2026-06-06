# 📈 Groww-Style Indian Stock Market Web Application

## Overview

A full-stack stock market web application inspired by Groww. This platform allows users to search Indian stocks, view real-time stock information, analyze stock performance using charts, and monitor market trends.

The application uses a Flask backend, JavaScript frontend, and Yahoo Finance (yfinance) as the data source.

---

## Features

### Market Dashboard
- View popular Indian stocks
- Live stock prices
- Daily gain/loss tracking
- Percentage change indicators

### Stock Search
- Search stocks using ticker symbols
- Search companies by name
- Quick access to stock information

### Interactive Charts
- Historical stock price visualization
- Multiple time ranges
- Dynamic chart updates

### Stock Details
- Current Price
- Previous Close
- Day High
- Day Low
- Market Capitalization
- Daily Change Percentage

### Responsive Design
- Desktop Friendly
- Tablet Friendly
- Mobile Friendly

---

## Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Chart.js

### Backend
- Python
- Flask
- Flask-CORS

### Data Source
- Yahoo Finance (yfinance)

---

## Project Structure

```text
groww-style-stock-app/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── assets/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│
└── README.md
```

---

## API Endpoints

### Get Stock Quote

```http
GET /api/quote?ticker=RELIANCE.NS
```

### Example Response

```json
{
  "symbol": "RELIANCE.NS",
  "lastPrice": 2800.50,
  "change": 25.30,
  "changePercent": 0.91
}
```

---

### Get Historical Data

```http
GET /api/history?ticker=RELIANCE.NS
```

Returns historical stock data used for chart visualization.

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/groww-style-stock-app.git
cd groww-style-stock-app
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Backend

Navigate to backend folder:

```bash
cd backend
python app.py
```

Backend Server:

```text
http://127.0.0.1:5000
```

---

## Run Frontend

Navigate to frontend folder:

```bash
cd frontend
python -m http.server 8000
```

Frontend URL:

```text
http://127.0.0.1:8000
```

---

## Application Workflow

1. User searches for a stock.
2. Frontend sends request to Flask API.
3. Backend fetches stock data using Yahoo Finance.
4. API returns JSON response.
5. Frontend displays stock information and charts.
6. User can analyze stock performance.

---

## Future Enhancements

- User Authentication
- Portfolio Tracking
- Watchlist Management
- AI-Based Stock Prediction
- Technical Indicators
- Candlestick Charts
- Real-Time Stock Updates
- News Sentiment Analysis
- NSE/BSE Top Gainers & Losers
- Portfolio Profit/Loss Tracking

---

## Advantages

- Free stock data source
- Easy to deploy
- Responsive design
- Beginner-friendly code
- Groww-inspired UI
- Lightweight architecture

---

## Limitations

- Depends on Yahoo Finance availability
- Data may be delayed
- Not suitable for live trading
- No broker integration

---

## Disclaimer

This project is intended for educational and learning purposes only. The stock market information displayed should not be considered financial advice. Always perform your own research before making investment decisions.

---

## Author

**Kumar Swamy B G**

Groww-Style Indian Stock Market Web Application

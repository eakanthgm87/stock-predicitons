from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Stock, HistoricalPrice, Watchlist, Prediction, PortfolioHolding, Transaction
from .ai_model import train_model_for_stock, predict_next_n, predicted_cagr
import pandas as pd
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
import yfinance as yf
import json

def index(request):
    return render(request, 'stocks/index.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'stocks/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid credentials')
    return render(request, 'stocks/login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    # ensure user has a watchlist
    watchlist, _ = Watchlist.objects.get_or_create(user=request.user, name='Default')
    stocks = watchlist.stocks.all()
    return render(request, 'stocks/dashboard.html', {'watchlist': watchlist, 'stocks': stocks})

@login_required
def add_ticker(request):
    if request.method == 'POST':
        ticker = request.POST.get('ticker').strip().upper()
        stock, _ = Stock.objects.get_or_create(ticker=ticker)
        watchlist, _ = Watchlist.objects.get_or_create(user=request.user, name='Default')
        watchlist.stocks.add(stock)
        return redirect('dashboard')
    return redirect('dashboard')

@login_required
def remove_ticker(request, pk):
    watchlist = get_object_or_404(Watchlist, user=request.user, name='Default')
    stock = get_object_or_404(Stock, pk=pk)
    watchlist.stocks.remove(stock)
    return redirect('dashboard')

@login_required
def ticker_detail(request, ticker):
    stock = get_object_or_404(Stock, ticker=ticker)

    # Fetch historical prices
    prices_qs = HistoricalPrice.objects.filter(stock=stock).order_by('date')

    # Convert queryset → JSON-safe list
    prices = [
        {
            "date": p.date.strftime("%Y-%m-%d"),   # convert datetime → string
            "close": float(p.close)                # convert Decimal → float
        }
        for p in prices_qs
    ]

    df = pd.DataFrame(prices)

    preds = {}
    rec = 'MODEL_NOT_TRAINED'
    expected_return = 0.0
    cagr = 0.0

    if not df.empty:
        try:
            raw_preds = predict_next_n(ticker, df[['date', 'close']], n_days=7)

            # Convert predictions → JSON-safe dict
            preds = {
                str(k): float(v)
                for k, v in raw_preds.items()
            }

            current_price = df['close'].iloc[-1]
            cagr = predicted_cagr(raw_preds, current_price, days=7)
            expected_return = (list(raw_preds.values())[-1] / current_price) - 1

            if expected_return > 0.03:
                rec = 'BUY'
            elif expected_return < -0.03:
                rec = 'SELL'
            else:
                rec = 'HOLD'

        except FileNotFoundError:
            preds = {}

    # SEND JSON TO TEMPLATE SAFELY
    return render(
        request,
        'stocks/ticker_detail.html',
        {
            'stock': stock,
            'prices': json.dumps(prices),   # JSON → safe for JS
            'preds': json.dumps(preds),     # JSON → safe for JS
            'rec': rec,
            'expected_return': expected_return,
            'cagr': cagr
        }
    )

@csrf_exempt
def api_train(request, ticker):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    stock = get_object_or_404(Stock, ticker=ticker)
    prices_qs = HistoricalPrice.objects.filter(stock=stock).order_by('date')
    prices = list(prices_qs.values('date','close'))
    import pandas as pd
    df = pd.DataFrame(prices)
    if df.empty:
        return JsonResponse({'error': 'no data'}, status=400)
    metrics = train_model_for_stock(ticker, df, nlags=5)
    return JsonResponse({'metrics': metrics})

@csrf_exempt
@csrf_exempt
def api_import(request, ticker):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)

    stock = get_object_or_404(Stock, ticker=ticker)

    import yfinance as yf
    yahoo_ticker = ticker  # default

    # -------------------------------
    # 1. Try original ticker first
    # -------------------------------
    try:
        info = yf.Ticker(ticker).info
        valid_original = ("regularMarketPrice" in info and info["regularMarketPrice"] is not None)
    except Exception:
        valid_original = False

    # -------------------------------
    # 2. If original does NOT exist -> try NSE version
    # -------------------------------
    if not valid_original:
        yahoo_ticker = ticker + ".NS"

    # -------------------------------
    # 3. Download historical data
    # -------------------------------
    try:
        hist = yf.download(yahoo_ticker, period="1y", auto_adjust=False)
    except Exception as e:
        return JsonResponse({'error': f'Error fetching data: {str(e)}'}, status=400)

    if hist.empty:
        return JsonResponse({'error': f'No price data found for {yahoo_ticker}'}, status=400)

    imported = 0

    # -------------------------------
    # 4. Save data to database
    # -------------------------------
    for date, row in hist.iterrows():
        close_price = float(row.get("Close", 0))
        if close_price <= 0:
            continue

        HistoricalPrice.objects.update_or_create(
            stock=stock,
            date=date.date(),
            defaults={
                'open': float(row.get("Open", 0)),
                'high': float(row.get("High", 0)),
                'low': float(row.get("Low", 0)),
                'close': close_price,
                'volume': float(row.get("Volume", 0)),
            }
        )
        imported += 1

    # -------------------------------
    # 5. Reload saved data
    # -------------------------------
    prices_qs = HistoricalPrice.objects.filter(stock=stock).order_by('date')
    df = pd.DataFrame(list(prices_qs.values('date', 'close')))

    if df.empty:
        return JsonResponse({'error': 'Data import failed — no rows saved'}, status=500)

    # -------------------------------
    # 6. Train model
    # -------------------------------
    metrics = train_model_for_stock(ticker, df, nlags=5)

    return JsonResponse({
        "message": f"Imported & trained successfully for {yahoo_ticker}",
        "imported_rows": imported,
        "metrics": metrics
    })


@csrf_exempt
def api_predict(request, ticker):
    if request.method != 'GET':
        return JsonResponse({'error': 'GET only'}, status=400)

    stock = get_object_or_404(Stock, ticker=ticker)
    prices_qs = HistoricalPrice.objects.filter(stock=stock).order_by('date')

    if not prices_qs.exists():
        return JsonResponse({'error': 'No price data available'}, status=400)

    df = pd.DataFrame(list(prices_qs.values('date', 'close')))
    preds = predict_next_n(ticker, df, n_days=7)

    current_price = df['close'].iloc[-1]
    cagr = predicted_cagr(preds, current_price, days=7)
    expected_return = (list(preds.values())[-1] / current_price) - 1

    if expected_return > 0.03:
        recommendation = "BUY"
    elif expected_return < -0.03:
        recommendation = "SELL"
    else:
        recommendation = "HOLD"

    return JsonResponse({
        "predictions": preds,
        "current_price": float(current_price),
        "expected_return": expected_return,
        "cagr": cagr,
        "recommendation": recommendation
    })
from django.http import JsonResponse
import yfinance as yf

def api_quote(request, ticker):
    try:
        # Append .NS for Indian tickers
        if "." not in ticker and ticker.isalpha() and len(ticker) <= 5:
            yf_ticker = ticker + ".NS"
        else:
            yf_ticker = ticker

        data = yf.Ticker(yf_ticker).history(period="5d")

        if data.empty:
            return JsonResponse({"error": "No data"}, status=400)

        last = data.iloc[-1]
        prev = data.iloc[-2]

        return JsonResponse({
            "ticker": ticker,
            "price": float(last["Close"]),
            "prevClose": float(prev["Close"]),
            "change": float(last["Close"] - prev["Close"]),
            "pct": float((last["Close"] - prev["Close"]) / prev["Close"] * 100),
            "closes": [float(x) for x in data["Close"].tail(10).tolist()]
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
import requests
from django.http import JsonResponse

def live_price(request, ticker):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        q = data["quoteResponse"]["result"][0]

        return JsonResponse({
            "ticker": ticker,
            "price": q.get("regularMarketPrice"),
            "prevClose": q.get("regularMarketPreviousClose"),
            "change": q.get("regularMarketChange"),
            "pct": q.get("regularMarketChangePercent"),
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_price(request, ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=10d&interval=1d"

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        result = data["chart"]["result"][0]
        meta = result["meta"]
        closes = result["indicators"]["quote"][0]["close"]

        return JsonResponse({
            "ticker": ticker,
            "price": meta.get("regularMarketPrice"),
            "prevClose": meta.get("previousClose"),
            "closes": closes[-10:],
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
# views.py
import os
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

# TTL for cache (seconds)
CACHE_TTL = 10

# Read key from settings or environment
TWELVEDATA_KEY = getattr(settings, "TWELVEDATA_API_KEY", os.environ.get("TWELVEDATA_API_KEY"))

@require_GET
@csrf_exempt
def td_price(request, ticker):
    """
    Returns JSON:
    {
      "ticker": "TCS.NS",
      "price": 1234.56,
      "prevClose": 1222.11,
      "closes": [ ... ],
    }
    """
    if not TWELVEDATA_KEY:
        return JsonResponse({"error": "TwelveData API key not configured"}, status=500)

    # Normalize ticker (if no exchange given assume NSE)
    symbol = ticker
    if "." not in symbol:
        symbol = f"{symbol}.NS"

    cache_key = f"td:{symbol}"
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse(cached)

    try:
        # Quote (current price + previous close)
        q_url = "https://api.twelvedata.com/quote"
        q_params = {"symbol": symbol, "apikey": TWELVEDATA_KEY}
        q_r = requests.get(q_url, params=q_params, timeout=6)
        q_r.raise_for_status()
        qj = q_r.json()
        if qj.get("status") == "error":
            return JsonResponse({"error": qj.get("message", "quote error")}, status=400)

        # Time series for sparkline (10 values)
        ts_url = "https://api.twelvedata.com/time_series"
        ts_params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": 10,
            "format": "JSON",
            "apikey": TWELVEDATA_KEY
        }
        ts_r = requests.get(ts_url, params=ts_params, timeout=6)
        ts_r.raise_for_status()
        tsj = ts_r.json()
        if tsj.get("status") == "error":
            # still allow quote; just set closes empty
            closes = []
        else:
            values = tsj.get("values") or []
            # API returns newest first; reverse to oldest -> newest
            closes = [float(v["close"]) for v in reversed(values)] if values else []

        price = None
        prev = None
        # TwelveData quote uses 'close' and 'previous_close'
        if "close" in qj:
            try:
                price = float(qj.get("close"))
            except Exception:
                price = None
        if "previous_close" in qj:
            try:
                prev = float(qj.get("previous_close"))
            except Exception:
                prev = None

        resp = {
            "ticker": ticker,
            "symbol": symbol,
            "price": price,
            "prevClose": prev,
            "closes": closes,
        }

        # cache result for small TTL
        cache.set(cache_key, resp, CACHE_TTL)
        return JsonResponse(resp)

    except requests.RequestException as e:
        return JsonResponse({"error": f"request failed: {str(e)}"}, status=502)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def trade_stock(request, ticker):
    """Trade screen: stores buy/sell, updates holdings, and shows a confirmation.
    Uses latest HistoricalPrice as the current price (does NOT call a live API).
    """
    stock = get_object_or_404(Stock, ticker=ticker)
    prices_qs = HistoricalPrice.objects.filter(stock=stock).order_by('-date')
    current_price = prices_qs[0].close if prices_qs.exists() else None

    context = {
        "stock": stock,
        "current_price": current_price,
        "action": None,
        "quantity": None,
        "total_value": None,
        "error": None,
    }

    if request.method == "POST":
        action = request.POST.get("action")  # 'buy' or 'sell'
        qty_raw = request.POST.get("quantity") or "0"

        try:
            qty = int(qty_raw)
        except ValueError:
            context["error"] = "Please enter a valid whole number quantity."
            return render(request, "stocks/trade_stock.html", context)

        if qty <= 0:
            context["error"] = "Quantity must be greater than 0."
            return render(request, "stocks/trade_stock.html", context)

        if current_price is None:
            context["error"] = "No price data available for this stock yet."
            return render(request, "stocks/trade_stock.html", context)

        # Get or create holding for this user & stock
        holding, _ = PortfolioHolding.objects.get_or_create(user=request.user, stock=stock)

        if action == "sell" and holding.quantity < qty:
            context["error"] = "You cannot sell more than you hold."
            return render(request, "stocks/trade_stock.html", context)

        # Save transaction
        Transaction.objects.create(
            user=request.user,
            stock=stock,
            action=action.upper(),
            quantity=qty,
            price=current_price,
        )

        # Update holding
        if action == "buy":
            holding.quantity += qty
        else:  # sell
            holding.quantity -= qty
        holding.save()

        total_value = float(current_price) * qty

        context.update({
            "action": action,
            "quantity": qty,
            "total_value": total_value,
        })

    return render(request, "stocks/trade_stock.html", context)


@login_required

def portfolio_view(request):
    """Show current holdings with live prices, P&L, equity curve and allocation breakdown."""
    holdings = (
        PortfolioHolding.objects
        .filter(user=request.user, quantity__gt=0)
        .select_related("stock")
    )

    portfolio_rows = []
    total_value = 0.0
    total_pnl = 0.0

    # helper: live price from Yahoo Finance
    def fetch_live_price(symbol):
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            result = data.get("quoteResponse", {}).get("result", [])
            if not result:
                return None
            q = result[0]
            return q.get("regularMarketPrice")
        except Exception:
            return None

    # build rows + maintain mapping for later charts
    for h in holdings:
        # all transactions for this stock/user
        tx_qs = Transaction.objects.filter(user=request.user, stock=h.stock).order_by("timestamp")

        # average buy price from BUYs only
        buy_tx = [t for t in tx_qs if t.action == "BUY"]
        total_buy_qty = sum(t.quantity for t in buy_tx)
        if total_buy_qty > 0:
            total_buy_cost = sum(t.quantity * t.price for t in buy_tx)
            avg_buy_price = total_buy_cost / total_buy_qty
        else:
            avg_buy_price = None

        # live price first, fallback to last stored close
        live_price = fetch_live_price(h.stock.ticker)
        if live_price is not None:
            current_price = live_price
        else:
            prices_qs = HistoricalPrice.objects.filter(stock=h.stock).order_by("-date")
            current_price = prices_qs[0].close if prices_qs.exists() else None

        if current_price is not None and avg_buy_price is not None:
            value = current_price * h.quantity
            pnl = (current_price - avg_buy_price) * h.quantity
        else:
            value = None
            pnl = None

        if value is not None:
            total_value += value
        if pnl is not None:
            total_pnl += pnl

        portfolio_rows.append({
            "holding": h,
            "avg_buy_price": avg_buy_price,
            "current_price": current_price,
            "value": value,
            "pnl": pnl,
        })

    # ---- build equity curve (approximate, using current quantities * past closes) ----
    from collections import defaultdict

    equity_by_date = defaultdict(float)
    if holdings:
        holding_qty = {h.stock.id: h.quantity for h in holdings}
        price_qs = HistoricalPrice.objects.filter(stock__in=[h.stock for h in holdings]).order_by("date")
        for p in price_qs:
            qty = holding_qty.get(p.stock_id, 0)
            if qty:
                equity_by_date[p.date] += qty * p.close

    # sort and trim to last 90 points
    sorted_equity = sorted(equity_by_date.items(), key=lambda kv: kv[0])
    if len(sorted_equity) > 90:
        sorted_equity = sorted_equity[-90:]

    equity_labels = [d.strftime("%Y-%m-%d") for d, _ in sorted_equity]
    equity_values = [float(v) for _, v in sorted_equity]

    # ---- allocation breakdown (by stock) ----
    alloc_labels = []
    alloc_values = []
    for row in portfolio_rows:
        if row["value"] is not None and row["value"] > 0:
            alloc_labels.append(row["holding"].stock.ticker)
            alloc_values.append(float(row["value"]))

    # ---- portfolio-level AI suggestion using expected return ----
    portfolio_expected_return = None
    weighted_sum = 0.0
    weight_total = 0.0

    for row in portfolio_rows:
        h = row["holding"]
        # need historical prices for predictions
        prices_qs = HistoricalPrice.objects.filter(stock=h.stock).order_by("date")
        if prices_qs.count() < 10:
            continue
        df = pd.DataFrame(list(prices_qs.values("date", "close")))
        try:
            preds = predict_next_n(h.stock.ticker, df, n_days=7)
        except Exception:
            continue
        if not preds:
            continue
        last_pred = list(preds.values())[-1]
        current_price = row["current_price"] or df["close"].iloc[-1]
        if current_price:
            expected_return = (last_pred / current_price) - 1.0
            value = row["value"] or 0.0
            if value > 0:
                weighted_sum += expected_return * value
                weight_total += value

    if weight_total > 0:
        portfolio_expected_return = weighted_sum / weight_total

    if portfolio_expected_return is None:
        portfolio_suggestion = "HOLD"
    elif portfolio_expected_return > 0.03:
        portfolio_suggestion = "BUY"
    elif portfolio_expected_return < -0.03:
        portfolio_suggestion = "SELL"
    else:
        portfolio_suggestion = "HOLD"

    context = {
        "rows": portfolio_rows,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "equity_labels": json.dumps(equity_labels),
        "equity_values": json.dumps(equity_values),
        "alloc_labels": json.dumps(alloc_labels),
        "alloc_values": json.dumps(alloc_values),
        "portfolio_suggestion": portfolio_suggestion,
    }
    return render(request, "stocks/portfolio.html", context)


@login_required
def history_view(request):
    """Show chronological list of all trades for this user."""
    tx = (
        Transaction.objects
        .filter(user=request.user)
        .select_related("stock")
        .order_by("-timestamp")
    )
    return render(request, "stocks/history.html", {"tx": tx})



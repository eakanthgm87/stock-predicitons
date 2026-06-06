import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
from pathlib import Path
from datetime import timedelta

MODEL_DIR = Path(__file__).resolve().parent / 'models'
MODEL_DIR.mkdir(exist_ok=True)

def _make_features(df, nlags=5):
    data = df.copy()
    for lag in range(1, nlags+1):
        data[f'lag_{lag}'] = data['close'].shift(lag)
    data['return_1d'] = data['close'].pct_change()
    data = data.dropna()
    return data

def train_model_for_stock(ticker, price_df, nlags=5):
    df = price_df[['date','close']].copy()
    df.index = pd.to_datetime(df['date'])
    df = df.sort_index()
    feat = _make_features(df, nlags=nlags)
    X = feat[[f'lag_{i}' for i in range(1, nlags+1)] + ['return_1d']]
    y = feat['close']
    # simple split
    split = int(len(X)*0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test) if len(X_test)>0 else 0.0
    joblib.dump({'model': model, 'nlags': nlags}, MODEL_DIR / f"{ticker}_rf.joblib")
    return {'r2_test': float(score)}

def predict_next_n(ticker, recent_df, n_days=7):
    model_path = MODEL_DIR / f"{ticker}_rf.joblib"
    if not model_path.exists():
        raise FileNotFoundError('model not trained')
    saved = joblib.load(model_path)
    model = saved['model']
    nlags = saved['nlags']
    df = recent_df.copy()
    df.index = pd.to_datetime(df['date'])
    df = df.sort_index()
    last_window = df['close'].tolist()[-nlags:]
    preds = {}
    cur_date = df.index[-1]
    for i in range(1, n_days+1):
        features = {}
        for lag in range(1, nlags+1):
            features[f'lag_{lag}'] = last_window[-lag]
        features['return_1d'] = (last_window[-1]/last_window[-2]) - 1 if len(last_window)>=2 else 0.0
        X = pd.DataFrame([features])
        next_price = model.predict(X)[0]
        cur_date = cur_date + pd.Timedelta(days=1)
        preds[cur_date.strftime('%Y-%m-%d')] = float(next_price)
        last_window.append(next_price)
        last_window.pop(0)
    return preds

def predicted_cagr(preds, current_price, days):
    if not preds:
        return 0.0
    last_price = list(preds.values())[-1]
    years = days/365.0
    if current_price<=0 or years==0:
        return 0.0
    return (last_price/current_price)**(1/years)-1

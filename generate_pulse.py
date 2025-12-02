# generate_pulse.py — Fixed warnings, real climbing curve, Oct 11 start, with caching, removed allocations
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)  # Suppress urllib3 SSL warning

import pandas as pd
from pybit.unified_trading import HTTP
from datetime import datetime, timedelta
import pytz
import time
import os
from joblib import Memory  # For caching

API_KEY = os.environ.get("BYBIT_API_KEY", "bajnYUqpQTd9S4vtrx")
API_SECRET = os.environ.get("BYBIT_API_SECRET", "5v9JzWRd9ZvZVgUnMU48m9ixr9pC6kicgRET")

memory = Memory(location='cache_dir', verbose=0)  # Cache folder for faster loads

@memory.cache(ignore=['session'])  # Cache this function's results
def fetch_transactions(session, start_date, end_date):
    all_transactions = []
    current_start = start_date
    while current_start < end_date:
        chunk_end = min(current_start + timedelta(days=7), end_date)
        chunk_start_ms = int(current_start.timestamp() * 1000)
        chunk_end_ms = int(chunk_end.timestamp() * 1000)

        cursor = None
        while True:
            params = {
                'accountType': 'UNIFIED',
                'category': 'linear',
                'currency': 'USDT',
                'startTime': chunk_start_ms,
                'endTime': chunk_end_ms,
                'limit': 50
            }
            if cursor:
                params['cursor'] = cursor

            try:
                response = session.get_transaction_log(**params)
            except Exception as e:
                time.sleep(5)
                continue

            if response['retCode'] != 0 or not response['result']['list']:
                break

            all_transactions.extend(response['result']['list'])
            cursor = response['result'].get('nextPageCursor')
            if not cursor:
                break
            time.sleep(0.2)  # Reduced sleep for faster fetch, still safe

        current_start = chunk_end

    return all_transactions

def generate_pulse_data():
    session = HTTP(demo=True, api_key=API_KEY, api_secret=API_SECRET, timeout=30)  # Added timeout=30 seconds per call

    # Real total equity from API
    balance_response = session.get_wallet_balance(accountType='UNIFIED')
    if balance_response['retCode'] != 0:
        raise ValueError(f"API failed: {balance_response['retMsg']}")
    current_balance = float(balance_response['result']['list'][0]['totalEquity'])

    # UPNL
    total_unrealized = 0.0
    positions_response = session.get_positions(category='linear', settleCoin='USDT')
    if positions_response['retCode'] == 0:
        positions = positions_response['result']['list']
        total_unrealized = sum(float(p['unrealisedPnl']) for p in positions if p['unrealisedPnl'])

    # October 11 start
    start_date = datetime(2025, 10, 11, tzinfo=pytz.UTC)
    end_date = datetime.now(pytz.UTC)

    # Pull transaction log with caching
    all_transactions = fetch_transactions(session, start_date, end_date)

    df_filtered = pd.DataFrame(all_transactions)
    # Fixed to_datetime: cast to int and use 's' unit
    df_filtered['execTime'] = pd.to_datetime(df_filtered['transactionTime'].astype(int) / 1000, unit='s', utc=True)
    df_filtered['change'] = pd.to_numeric(df_filtered['change'], errors='coerce')
    df_filtered = df_filtered.dropna(subset=['change'])
    df_filtered = df_filtered.sort_values('execTime').reset_index(drop=True)

    # Flat line from Oct 11 (fixed 'h' freq)
    fill_end = df_filtered['execTime'].iloc[0]
    fill_times = pd.date_range(start_date, fill_end, freq='h', inclusive='left')
    fill_df = pd.DataFrame({'execTime': fill_times, 'change': 0.0})
    df_filtered = pd.concat([fill_df, df_filtered], ignore_index=True)
    df_filtered = df_filtered.sort_values('execTime').reset_index(drop=True)

    df_filtered['equity'] = 100000.0 + df_filtered['change'].cumsum()

    total_equity = df_filtered['equity'].iloc[-1] + total_unrealized

    # Stats
    peak = df_filtered['equity'].cummax()
    dd = (df_filtered['equity'] - peak) / peak
    max_dd = round(dd.min() * 100, 1)
    days_live = (end_date - start_date).days

    stats = {
        "return_pct": round(((total_equity / 100000) - 1) * 100, 2),
        "days_live": days_live,
        "max_dd": max_dd
    }

    return df_filtered[['execTime', 'equity']], float(total_equity), stats, float(total_unrealized)
# generate_pulse.py
# ← Paste your entire bybit_tracker_pulse.py code here, BUT replace the plt.show() part with this return:

from datetime import datetime
import pytz

def generate_pulse_data():
    # === PASTE YOUR ENTIRE bybit_tracker_pulse.py CODE HERE ===
    # (from imports all the way to where you have df_filtered and total_equity)
    
    # At the very end, instead of plt.show(), put this:
    stats = {
        "return_pct": ((total_equity / 100000) - 1) * 100,
        "days_live": (datetime.now(pytz.UTC) - datetime(2025, 10, 10, tzinfo=pytz.UTC)).days + 1,
        "max_dd": ((df_filtered['equity'].cummax() - df_filtered['equity']) / df_filtered['equity'].cummax()).min() * 100
    }
    
    return df_filtered.copy(), total_equity, stats
import os
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime
from time import time
from io import StringIO


def fetch_data(coin):
    filename = f"Binance_{coin}USDT_2023_minute.csv"

    if not os.path.isfile(filename):
        print(f"Historical data for {coin} not found. Fetching...")
        url = f"https://www.cryptodatadownload.com/cdd/Binance_{quote(coin)}USDT_2023_minute.csv"
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Fetched data for {coin}")
            # Remove first line
            lines = response.text.split("\n")[1:]
            with open(filename, "w") as f:
                f.write("\n".join(lines))
        else:
            print(f"Failed to fetch data for {coin}. Skipping this signal.")
            return None

    return pd.read_csv(filename, header=None)


def process_signal(signal, historical_data):
    print(f'Simulating Signal ID #{signal[0]} ({signal[3]})')

    trade = {}
    is_open = False
    is_close = False
    open_time = 0
    max_drawdown = 0

    # Filter the data to only include entries after the signal
    relevant_data = historical_data[historical_data.iloc[:,0].astype(float)/1000 > signal['Unix Timestamp']]
    
    for _, row in relevant_data.iterrows():
        if not is_open:
            if signal['Direction'] == 'Long':
                if signal['Entry Min'] <= row.iloc[3:7].astype(float).min() <= signal['Entry Max']:
                    is_open = True
                    trade['Open Price'] = row.iloc[3:7].astype(float).min()
                    trade['Open Time'] = row.iloc[1]
                    open_time = row.iloc[0]/1000
                    print(f'Trade opened at price: {trade["Open Price"]} at time: {trade["Open Time"]}.')
            elif signal['Direction'] == 'Short':
                if signal['Entry Max'] >= row.iloc[3:7].astype(float).max() >= signal['Entry Min']:
                    is_open = True
                    trade['Open Price'] = row.iloc[3:7].astype(float).max()
                    trade['Open Time'] = row.iloc[1]
                    open_time = row.iloc[0]/1000
                    print(f'Trade opened at price: {trade["Open Price"]} at time: {trade["Open Time"]}.')
        else:
            if signal['Direction'] == 'Long':
                if row.iloc[3:7].astype(float).max() >= signal['Short Term Target']:
                    is_close = True
                    trade['Close Price'] = row.iloc[3:7].astype(float).max()
                    trade['Close Time'] = row.iloc[1]
                    print(f'Trade closed at price: {trade["Close Price"]} at time: {trade["Close Time"]}.')
                    break
                elif row.iloc[3:7].astype(float).min() < signal['Stop Loss']:
                    is_close = True
                    trade['Close Price'] = row.iloc[3:7].astype(float).min()
                    trade['Close Time'] = row.iloc[1]
                    print(f'Trade closed due to stop loss at price: {trade["Close Price"]} at time: {trade["Close Time"]}.')
                    break
            elif signal['Direction'] == 'Short':
                if row.iloc[3:7].astype(float).min() <= signal['Short Term Target']:
                    is_close = True
                    trade['Close Price'] = row.iloc[3:7].astype(float).min()
                    trade['Close Time'] = row.iloc[1]
                    print(f'Trade closed at price: {trade["Close Price"]} at time: {trade["Close Time"]}.')
                    break
                elif row.iloc[3:7].astype(float).max() > signal['Stop Loss']:
                    is_close = True
                    trade['Close Price'] = row.iloc[3:7].astype(float).max()
                    trade['Close Time'] = row.iloc[1]
                    print(f'Trade closed due to stop loss at price: {trade["Close Price"]} at time: {trade["Close Time"]}.')
                    break
        if is_open and not is_close:
            max_drawdown = min(max_drawdown, row.iloc[3:7].astype(float).min() - trade['Open Price'])
    
    if not is_open:
        print('Trade did not open.')
    elif not is_close:
        print('Trade did not close.')
    trade['Duration'] = trade['Close Time'] - trade['Open Time'] if 'Close Time' in trade and 'Open Time' in trade else "N/A"
    trade['Max Drawdown'] = max_drawdown

    return trade


def simulate_trades(signals_filename):
    signals = pd.read_csv(signals_filename)
    trades_data = []

    for _, row in signals.iterrows():
        coin = row['Coin']
        historical_data = fetch_data(coin)
        if historical_data is not None:
            trades_data.append(process_signal(row, historical_data))

    df = pd.DataFrame(trades_data)
    df.to_html('simulation_result.html')
    print("Simulation completed. Result has been saved as 'simulation_result.html'.")


# Run the simulation
simulate_trades('signals.csv')

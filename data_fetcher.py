#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import requests
import time
import io


key_path = '/Users/yochainusan/PycharmProjects/backtest_multi/config/alpha_vantage/key.txt'
telegram_key_path = '/Users/yochainusan/PycharmProjects/order_notifier/config/telegram/key.txt'


def retry_get_request(url):
    retries = 1
    success = False
    while not success and retries <= 10:
        try:
            response = requests.get(url)
            success = True
            return response
        except Exception as e:
            wait = retries * 10
            print(f'Error Get Requesting {url}: {e}')
            print('Error! Waiting %s secs and re-trying...' % wait)
            time.sleep(wait)
            retries += 1
    return None


def get_sp500_list():
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    df = table[0]
    df.to_csv('S&P500-Info.csv')
    df.to_csv("S&P500-Symbols.csv", columns=['Symbol'])
    return df['Symbol']


def get_stock_earnings_data(ticker, start_time, time):
    print('--- getting earnings data ---')
    print(ticker)
    api_key = open(key_path,'r').read()
    r = requests.get(f'https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={api_key}')
    json_result = r.json()
    time.sleep(0.4 - ((time.time() - start_time) % 0.4))
    return json_result


def convert_columns_to_adjusted(stock_df):
    df = stock_df.copy()
    adjustment_ratio = df['Adjusted_Close'] / df['Close']
    df['Open'] = (adjustment_ratio * df['Open']).round(2)
    df['High'] = (adjustment_ratio * df['High']).round(2)
    df['Low'] = (adjustment_ratio * df['Low']).round(2)
    df['Close'] = (df['Adjusted_Close']).round(2)
    df = df.drop(['Adjusted_Close'], axis=1)
    return df


def get_stock_data_trade_daily_alpha_vantage(ticker, start_time, time):
    print(ticker)
    api_key = open(key_path, 'r').read()
    data = retry_get_request(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&apikey={api_key}&outputsize=full&datatype=csv').content
    if data is None:
        return None
    data = pd.read_csv(io.StringIO(data.decode('utf-8')))
    if 'close' not in data:
        return None
    data = pd.read_csv(io.StringIO(data.decode('utf-8')))
    data = data[['timestamp', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']]
    data.columns = ["Date", "Open","High","Low","Close","Adjusted_Close","Volume"]
    data = data.iloc[::-1].reset_index(drop=True)
    data = data.iloc[-(252*10):].reset_index(drop=True)
    df = convert_columns_to_adjusted(data)
    time.sleep(0.4 - ((time.time() - start_time) % 0.4))
    return df


def get_data_for_stock(ticker, interval, start_time, time_module):
    # switch call between daily adjusted, TODO: intraday_extended! and weekly adjusted
    if interval == 'D':
        stock_data = get_stock_data_trade_daily_alpha_vantage(ticker, start_time, time_module)
        if stock_data is None:
            return None
        return stock_data


def add_earnings_dates_to_stock(stock_df, earnings_json):
    df = stock_df.copy()
    df['is_earning_days'] = ''
    for quarterly_report in earnings_json['quarterlyEarnings']:
        report_date_string = quarterly_report['reportedDate']
        df['is_earning_days'][df['Date'] == report_date_string] = True
    return df['is_earning_days']


def get_data_dict_for_multiple_stocks(tickers, interval, time_module):
    ohlc_intraday = {} # dictionary with ohlc value for each stock
    start_time = time.time()
    for ticker in tickers:
        stock_data = get_data_for_stock(ticker, interval, start_time, time_module)
        if stock_data is None:
            continue
        # earnings = get_stock_earnings_data(ticker, start_time, time_module)
        # stock_data['is_earning_days'] = add_earnings_dates_to_stock(stock_data, earnings)
        stock_data['is_earning_days'] = ''  # TODO: once I get how to catch and retry, add the earnings back!
        ohlc_intraday[ticker] = stock_data
    return ohlc_intraday


def get_data_dict_for_all_stocks_in_directory(directory_str):
    directory = os.fsencode(directory_str)
    ohlc_intraday = {}
    tickers = []
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".csv") and filename[0].isupper():
            ticker = filename.split('_')[0]
            print(f'pulling ticker csv {ticker}')
            stock_df = pd.read_csv(directory_str + '/' + filename)
            ohlc_intraday[ticker] = stock_df[['Date','Open','High','Low','Close','Volume','is_earning_days']]
            tickers.append(ticker)
    return ohlc_intraday, tickers

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import datetime as dt
import requests
import copy
from alpha_vantage.timeseries import TimeSeries
import time


key_path = '/Users/yochainusan/programs/algo_course/config/alpha_vantage/key.txt'

def get_sp500_list():
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    df = table[0]
    df.to_csv('S&P500-Info.csv')
    df.to_csv("S&P500-Symbols.csv", columns=['Symbol'])
    return df['Symbol']

def get_stock_data_trade_hours_alpha_vantage(ticker, interval, start_time, time):
    ts = TimeSeries(open(key_path,'r').read(), output_format='pandas')
    data = ts.get_intraday(symbol=ticker, interval=interval, outputsize='full')[0]
    data.columns = ["Open","High","Low","Close","Volume"]
    data = data.iloc[::-1]
    data = data.between_time('09:35', '16:00') #remove data outside regular trading hours
    time.sleep(0.4 - ((time.time() - start_time) % 0.4))
    return data


def get_stock_earnings_data(ticker, start_time, time):
    print('--- getting earnings data ---')
    print(ticker)
    api_key = open(key_path,'r').read()
    r = requests.get(f'https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={api_key}')
    json_result = r.json()
    time.sleep(0.4 - ((time.time() - start_time) % 0.4))
    return json_result



def get_stock_data_trade_daily_alpha_vantage(ticker, start_time, time):
    print(ticker)
    ts = TimeSeries(open(key_path,'r').read(), output_format='pandas')
    # data = ts.get_daily_adjusted(symbol=ticker, outputsize='full')[0]
    data = ts.get_daily(symbol=ticker, outputsize='full')[0] # NOT ADJUSTED!!!! the dumbfucks adjusted only the close column
    data = data[['1. open', '2. high', '3. low', '4. close', '5. volume']]
    data.columns = ["Open","High","Low","Close","Volume"]
    data = data.iloc[::-1]
    data = data.iloc[-(365*7):]
    time.sleep(0.4 - ((time.time() - start_time) % 0.4))
    return data

def get_data_for_stock(ticker, interval, start_time, time_module):
    # switch call between daily adjusted, TODO: intraday_extended! and weekly adjusted
    if interval == 'D':
        return get_stock_data_trade_daily_alpha_vantage(ticker, start_time, time_module)

    return get_stock_data_trade_hours_alpha_vantage(ticker, interval, start_time, time_module)


def add_earnings_dates_to_stock(stock_df, earnings_json):
    df = stock_df.copy()
    df['is_earning_days'] = ''
    for quarterly_report in earnings_json['quarterlyEarnings']:
        report_date_string = quarterly_report['reportedDate']
        idx = np.searchsorted(df.index, report_date_string)
        idx_prev = df.index[max(0, idx-1)]
        df['is_earning_days'][idx] = True
        df['is_earning_days'][idx_prev] = True
    return df['is_earning_days']


def get_data_dict_for_multiple_stocks(tickers, interval, time_module):
    ohlc_intraday = {} # dictionary with ohlc value for each stock
    start_time = time.time()
    for ticker in tickers:
        stock_data = get_data_for_stock(ticker, interval, start_time, time_module)
        earnings = get_stock_earnings_data(ticker, start_time, time_module)
        stock_data['is_earning_days'] = add_earnings_dates_to_stock(stock_data, earnings)
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
            stock_df = pd.read_csv(directory_str + '/' + filename)
            ohlc_intraday[ticker] = stock_df[['date', 'Open','High','Low','Close','Volume', 'is_earning_days']]
            tickers.append(ticker)
    return ohlc_intraday, tickers

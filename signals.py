#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def parabolic_trending_n_periods(stock_df, n):
    # assuming parabolic trend (consistent divergence of price from 10 day moving average) will reverse
    # TODO: should be generic for n
    df = stock_df.copy()
    df['parabolic_trend'] = ""
    for i in range(len(df)):
        if i < n + 1:
            continue
        if df["distance_from_10_ma"][i-3] >= 0 and df["distance_from_10_ma"][i] >= df["distance_from_10_ma"][i-1] \
                and df["distance_from_10_ma"][i-1] >= df["distance_from_10_ma"][i-2] \
                and df["distance_from_10_ma"][i-2] >= df["distance_from_10_ma"][i-3]:
            df['parabolic_trend'][i] = "Bearish"
        elif df["distance_from_10_ma"][i-3] <= 0 and df["distance_from_10_ma"][i] <= df["distance_from_10_ma"][i-1] \
                and df["distance_from_10_ma"][i-1] <= df["distance_from_10_ma"][i-2] \
                and df["distance_from_10_ma"][i-2] <= df["distance_from_10_ma"][i-3]:
            df['parabolic_trend'][i] = "Bullish"
    return df['parabolic_trend']

def check_non_adx_indicators_before_n_periods(df, i, num_periods, check_term):
    # check_term could be 'ABOVE' or 'BELOW'
    if i < num_periods:
        return True
    if check_term == 'ABOVE':
        if df['distance_from_10_ma'][i - num_periods] > 0 and df['rsi'][i - num_periods] > 50 and df['+di'][i - num_periods] > 25 and df['-di'][i - num_periods] < 25 and df['stochastic_k'][i - num_periods] > 50 and df['stochastic_d'][i - num_periods] > 50:
            return False
    elif check_term == 'BELOW':
        if df['distance_from_10_ma'][i - num_periods] < 0 and df['rsi'][i - num_periods] < 50 and df['+di'][i - num_periods] < 25 and df['-di'][i - num_periods] > 25 and df['stochastic_k'][i - num_periods] < 50 and df['stochastic_d'][i - num_periods]< 50:
            return False
    return True


def check_more_bull_signals(df, i):
    count = 0
    if df['rsi'][i] >= 90:
        count += 1
    if df['stochastic_k'][i] < 60:
        count += 1
    if df['stochastic_d'][i] < 60:
        count += 1
    return count == 0


def check_more_bear_signals(df, i):
    count = 0
    if df['-di'][i] > 40:
        count += 1
    if df['stochastic_k'][i] < 15:
        count += 1
    if df['stochastic_d'][i] < 15:
        count += 1
    if df['atr_volatility'][i] > 0.075 and df['atr_volatility_ma'][i] > 0.075:
        count += 1
    return count == 0


def check_column_trend(df, column_name, i, diff=0):
    if i > 2:
        if df[column_name][i] + diff < df[column_name][i - 1] + diff < df[column_name][i - 2] + diff:
            return 'DOWN'
        if df[column_name][i] - diff > df[column_name][i - 1] - diff > df[column_name][i - 2] - diff:
            return 'UP'
    return 'NO_TREND'


def indicators_mid_levels_signal(stock_df):
    df = stock_df.copy()
    df['indicators_mid_levels'] = ''
    df['indicators_mid_levels_zone'] = ''
    for i in range(len(df)):
        if i > 1:
            if df['adx'][i] > 25 and df['rsi'][i] > 50 and df['+di'][i] > 25 and df['-di'][i] < 25 and df['stochastic_k'][i] > 50 and df['stochastic_d'][i] > 50:
                df['indicators_mid_levels_zone'][i] = 'positive'
            elif df['adx'][i] > 25 and df['rsi'][i] < 50 and df['+di'][i] < 25 and df['-di'][i] > 25 and df['stochastic_k'][i] < 50 and df['stochastic_d'][i] < 50:
                df['indicators_mid_levels_zone'][i] = 'negative'
    return df['indicators_mid_levels'], df['indicators_mid_levels_zone']


def check_volume_high_enough(df, i):
    return df['ma_volume'][i] != '' and df['Volume'][i] > df['ma_volume'][i]


def check_not_earnings_days(df, i):
    return df['is_earning_days'][i] != True


def check_trend_not_down(df, i):
    return check_column_trend(df, 'stochastic_k', i) != 'DOWN'


def check_trend_not_up(df, i):
    return check_column_trend(df, 'stochastic_k', i) != 'UP'

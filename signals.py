#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


def cross_20_ma(stock_df, signal_direction_column, signal_type_column):
    df = stock_df.copy()
    for i in range(len(df)):
        if i > 1:
            if df['Close'][i] > df['20_ma'][i] and df['Close'][i-1] <= df['20_ma'][i-1]:
                df[signal_direction_column][i] = 'positive'
                df[signal_type_column][i] = 'cross_20'
            elif (df['20_ma'][i] - df['Close'][i]) / df['20_ma'][i] > 0.01 and (df['20_ma'][i-1] - df['Close'][i-1]) / df['20_ma'][i-1] <= 0.01:
                df[signal_direction_column][i] = 'negative'
                df[signal_type_column][i] = 'cross_20'
    return df


def cross_50_ma(stock_df, signal_direction_column, signal_type_column):
    df = stock_df.copy()
    for i in range(len(df)):
        if i > 1:
            if df['Close'][i] > df['50_ma'][i] and df['Close'][i-1] <= df['50_ma'][i-1]:
                df[signal_direction_column][i] = 'positive'
                df[signal_type_column][i] = 'cross_50'
            elif (df['50_ma'][i] - df['Close'][i]) / df['50_ma'][i] > 0.01 and (df['50_ma'][i-1] - df['Close'][i-1]) / df['50_ma'][i-1] <= 0.01:
                df[signal_direction_column][i] = 'negative'
                df[signal_type_column][i] = 'cross_50'
    return df


def indicators_mid_levels_signal(stock_df, signal_direction_column, signal_type_column):
    df = stock_df.copy()
    for i in range(len(df)):
        if i > 1:
            if df['rsi'][i] > 50 and df['+di'][i] > 25 and df['-di'][i] < 25 and df['stochastic_k'][i] > 50:
                df[signal_direction_column][i] = 'positive'
                df[signal_type_column][i] = 'indicators_mid_levels_zone'
            elif df['rsi'][i] < 50 and df['+di'][i] < 25 and df['-di'][i] > 25 and df['stochastic_k'][i] < 50:
                df[signal_direction_column][i] = 'negative'
                df[signal_type_column][i] = 'indicators_mid_levels_zone'
    return df


def joint_signal(stock_df, signal_direction_column, signal_type_column):
    df = stock_df.copy()
    for i in range(len(df)):
        if i > 1:
            if df['indicators_mid_level_direction'][i] == 'positive' and df['cross_50_direction'][i] == 'positive':
                df[signal_direction_column][i] = 'positive'
                df[signal_type_column][i] = 'joint_50'
            elif df['indicators_mid_level_direction'][i] == 'negative' and df['cross_50_direction'][i] == 'negative':
                df[signal_direction_column][i] = 'negative'
                df[signal_type_column][i] = 'joint_50'
            elif df['indicators_mid_level_direction'][i] == 'positive' and df['cross_20_direction'][i] == 'positive':
                df[signal_direction_column][i] = 'positive'
                df[signal_type_column][i] = 'joint_20'
            elif df['indicators_mid_level_direction'][i] == 'negative' and df['cross_20_direction'][i] == 'negative':
                df[signal_direction_column][i] = 'negative'
                df[signal_type_column][i] = 'joint_20'
    return df


def parabolic_trending_n_periods(stock_df, n, signal_direction_column, signal_type_column):
    # assuming parabolic trend (consistent divergence of price from 10 day moving average) will reverse
    # TODO: should be generic for n
    df = stock_df.copy()
    for i in range(len(df)):
        if i < n + 1:
            continue
        if df["distance_from_10_ma"][i-3] >= 0 and df["distance_from_10_ma"][i] <= 0.03 \
                and df["distance_from_10_ma"][i] >= df["distance_from_10_ma"][i-1] \
                and df["distance_from_10_ma"][i-1] >= df["distance_from_10_ma"][i-2] \
                and df["distance_from_10_ma"][i-2] >= df["distance_from_10_ma"][i-3]:
            df[signal_direction_column][i] = "negative"
            df[signal_type_column][i] = "parabolic_trend"
        elif df["distance_from_10_ma"][i-3] <= 0 and df["distance_from_10_ma"][i] >= -0.03 \
                and df["distance_from_10_ma"][i] <= df["distance_from_10_ma"][i-1] \
                and df["distance_from_10_ma"][i-1] <= df["distance_from_10_ma"][i-2] \
                and df["distance_from_10_ma"][i-2] <= df["distance_from_10_ma"][i-3]:
            df[signal_direction_column][i] = "positive"
            df[signal_type_column][i] = "parabolic_trend"
    return df


def check_volume_high_enough(df, i):
    return df['ma_volume'][i] != '' and df['Volume'][i] > df['ma_volume'][i] and df['Volume'][i] >= 1000000


def check_additional_positive_indicators(df, i):
    return df['atr_volatility_ma'][i] < 0.04 and df['distance_from_10_ma'][i] > 0.04


def check_atr_volatility_low_enough(df, i):
    return df['atr_volatility_ma'][i] != '' and df['atr_volatility_ma'][i] < 0.05


def check_not_earnings_days(df, i):
    return df['is_earning_days'][i] != True


def check_trend_not_down(df, i):
    return check_column_trend(df, 'stochastic_k', i) != 'DOWN'


def check_trend_not_up(df, i):
    return check_column_trend(df, 'stochastic_k', i) != 'UP'

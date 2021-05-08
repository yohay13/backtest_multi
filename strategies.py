#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from signals import check_volume_high_enough, check_not_earnings_days


def get_position_type_and_index(df, i, signal_column_name, in_position_column):
    for j in range(i, 0, -1):
        if df[in_position_column][j] != True:
            return df[signal_column_name][j + 1], j + 1
    return 'ERR', -1


def exit_bullish(stock_df, current_index, signal_index, trigger_column):
    df = stock_df.copy()
    df['exits'][current_index] = 'Exit Buy'
    df['action_return'][current_index] = (df[trigger_column][current_index] - df['Close'][signal_index]) / df['Close'][
        signal_index]
    df['action_return_on_signal_index'][signal_index] = df['action_return'][current_index]
    df['in_position'][current_index] = False
    return df


def exit_bearish(stock_df, current_index, signal_index, trigger_column):
    df = stock_df.copy()
    df['exits'][current_index] = 'Exit Sell'
    df['action_return'][current_index] = -(df[trigger_column][current_index] - df['Close'][signal_index]) / df['Close'][
        signal_index]
    df['action_return_on_signal_index'][signal_index] = df['action_return'][current_index]
    df['in_position'][current_index] = False
    return df


def check_early_in_trend(df, signal_column_name, i, signal_value, period_check):
    if i < period_check:
        return False
    for j in range(i, i - period_check, -1):
        if df[signal_column_name][j] != signal_value:
            return True
    return False


def calculate_exits_column_by_atr_and_prev_max_min(stock_df, signal_column_name, signal_type_column_name, prev_max_min_periods):
    df = stock_df.copy()
    df['exits'] = ''
    df['action_return'] = ''
    df['action_return_on_signal_index'] = ''
    df['current_stop_loss'] = ''
    df['current_profit_taker'] = ''
    df['entry_price'] = ''
    df['in_position'] = ''
    df['signal'] = ''
    for i in range(len(df)):
        if i > 1:
            # check in position
            if df['in_position'][i - 1]:
                df['current_stop_loss'][i] = df['current_stop_loss'][i - 1]
                df['current_profit_taker'][i] = df['current_profit_taker'][i - 1]
                df['entry_price'][i] = df['entry_price'][i - 1]
                df['in_position'][i] = df['in_position'][i - 1]
                # check for exit
                signal_type, signal_index = get_position_type_and_index(df, i, signal_column_name, 'in_position')
                if signal_type == 'positive' and df['current_profit_taker'][i] <= df['Open'][i]:
                    df = exit_bullish(df, i, signal_index, 'Open')  # exit open
                    continue
                if signal_type == 'positive' and df['current_profit_taker'][i] <= df['High'][i]:
                    df = exit_bullish(df, i, signal_index, 'current_profit_taker')  # exit pt
                    continue
                if signal_type == 'positive' and df['current_stop_loss'][i] >= df['Open'][i]:
                    df = exit_bullish(df, i, signal_index, 'Open')  # exit open
                    continue
                if signal_type == 'positive' and df['current_stop_loss'][i] >= df['Low'][i]:
                    df = exit_bullish(df, i, signal_index, 'current_stop_loss')  # exit sl
                    continue
                if signal_type == 'negative' and df['current_stop_loss'][i] <= df['Open'][i]:
                    df = exit_bearish(df, i, signal_index, 'Open')  # exit open
                    continue
                if signal_type == 'negative' and df['current_stop_loss'][i] <= df['High'][i]:
                    df = exit_bearish(df, i, signal_index, 'current_stop_loss')  # exit sl
                    continue
                if signal_type == 'negative' and df['current_profit_taker'][i] >= df['Open'][i]:
                    df = exit_bearish(df, i, signal_index, 'Open')  # exit open
                    continue
                if signal_type == 'negative' and df['current_profit_taker'][i] >= df['Low'][i]:
                    df = exit_bearish(df, i, signal_index, 'current_profit_taker')  # exit pt
                    continue
                # check for moving stop loss
                if signal_type == 'positive':
                    if (df['current_profit_taker'][i] - df['entry_price'][i]) * 0.75 <= df['Close'][i] - \
                            df['entry_price'][i]:
                        # new stop_loss is max between close-0.5atr and close+reward/2
                        df['current_stop_loss'][i] = max(df['Close'][i] - 0.5 * df['atr'][i],
                                                         (df['current_profit_taker'][i] + df['entry_price'][i]) / 2)
                        df['current_profit_taker'][i] = df['current_profit_taker'][i] + df['atr'][i]
                elif signal_type == 'negative':
                    if (df['current_profit_taker'][i] - df['entry_price'][i]) * 0.75 >= df['Close'][i] - \
                            df['entry_price'][i]:
                        # new stop_loss is min between close+0.5atr and close+reward/2
                        df['current_stop_loss'][i] = min(df['Close'][i] + 0.5 * df['atr'][i],
                                                         (df['current_profit_taker'][i] + df['entry_price'][i]) / 2)
                        df['current_profit_taker'][i] = df['current_profit_taker'][i] - df['atr'][i]
            # if not in position
            elif not df['in_position'][i - 1]:
                # check if i should enter a bullish position
                if df[signal_column_name][i] == 'positive' and check_volume_high_enough(df,
                                                                                        i) and check_not_earnings_days(
                        df, i) and check_early_in_trend(df, signal_column_name, i, 'positive', 5):
                    df['entry_price'][i] = df['Close'][i]
                    if df[signal_type_column_name][i] == 'parabolic_trend':
                        df['current_profit_taker'][i] = df['entry_price'][i] + ((df['10_ma'][i] - df['entry_price'][i]) / 2)
                        df['current_stop_loss'][i] = df['entry_price'][i] - df['atr'][i] * 0.5
                    else:
                        df['current_profit_taker'][i] = min(df['High'].rolling(prev_max_min_periods).max()[i],
                                                            df['entry_price'][i] + 2 * df['atr'][i])
                        df['current_stop_loss'][i] = max(df['Low'].rolling(prev_max_min_periods).min()[i],
                                                         df['entry_price'][i] - df['atr'][i])
                    if df['current_profit_taker'][i] - df['entry_price'][i] >= 2 * (
                            df['entry_price'][i] - df['current_stop_loss'][i]):
                        # enter position
                        df['in_position'][i] = True
                        df['signal'][i] = 'Bullish'
                    else:
                        df['in_position'][i] = False
                    continue
                # check if i should enter a bearish position
                if df[signal_column_name][i] == 'negative' and check_volume_high_enough(df,
                                                                                        i) and check_not_earnings_days(
                        df, i) and check_early_in_trend(df, signal_column_name, i, 'negative', 5):
                    df['entry_price'][i] = df['Close'][i]
                    if df[signal_type_column_name][i] == 'parabolic_trend':
                        df['current_profit_taker'][i] = df['entry_price'][i] - (abs(df['10_ma'][i] - df['entry_price'][i]) / 2)
                        df['current_stop_loss'][i] = df['entry_price'][i] + df['atr'][i] * 0.5
                    else:
                        df['current_profit_taker'][i] = max(df['Low'].rolling(prev_max_min_periods).min()[i],
                                                            df['entry_price'][i] - 2 * df['atr'][i])
                        df['current_stop_loss'][i] = min(df['High'].rolling(prev_max_min_periods).max()[i],
                                                         df['entry_price'][i] + df['atr'][i])

                    if abs(df['current_profit_taker'][i] - df['entry_price'][i]) >= 2 * abs(
                            df['entry_price'][i] - df['current_stop_loss'][i]):
                        # enter position
                        df['in_position'][i] = True
                        df['signal'][i] = 'Bearish'
                    else:
                        df['in_position'][i] = False
                    continue
    return df

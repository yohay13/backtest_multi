
import pandas as pd
import numpy as np
from data_fetcher import get_sp500_list, get_data_dict_for_all_stocks_in_directory, get_data_dict_for_multiple_stocks
from strategies import calculate_exits_column_by_atr_and_prev_max_min
from indicators import get_ma_column_for_stock, get_distance_between_columns_for_stock, \
    get_adx_column_for_stock, rsi, stochastic, get_ATR_column_for_stock, get_volatility_from_atr
from signals import indicators_mid_levels_signal, parabolic_trending_n_periods, cross_20_ma, cross_50_ma, joint_signal
import time
import matplotlib.pyplot as plt



# See PyCharm help at https://www.jetbrains.com/help/pycharm/

tickers = get_sp500_list()

adjusted_tickers = [elem for elem in tickers if elem != 'GOOG' and elem != 'DUK' and elem != 'HLT' and elem != 'DD' and elem != 'CMCSA' and elem != 'COG' and elem != 'WBA' and elem != 'KMX' and elem != 'ADP' and elem != 'STZ' and elem != 'IQV'] # there were stock splits
adjusted_tickers = [elem for elem in adjusted_tickers if '.' not in elem]
# yahoo finance screener - mega caps only, tech, energey and finance
# adjusted_tickers = ['FB', 'AAPL', 'NFLX', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'BAC', 'C', 'TWTR', 'MA', 'TSM', 'V', 'JPM', 'NVDA', 'XOM', 'CVX']
# adjusted_tickers = ['AAPL', 'FB', 'BKR']
# adjusted_tickers = adjusted_tickers[378:500] # in the middle - missing
# adjusted_tickers = adjusted_tickers[:250] # from beginning

stocks_dict = get_data_dict_for_multiple_stocks(adjusted_tickers, 'D', time) # interval should be: D, W, 30min, 5min etc.

# stocks_dict, adjusted_tickers = get_data_dict_for_all_stocks_in_directory('stocks_csvs_new')
# adjusted_tickers = ['AAPL']
all_stocks_data_df = pd.DataFrame()
all_stocks_data_df['ticker'] = adjusted_tickers

for ticker in adjusted_tickers:
    stocks_dict[ticker]['10_ma'] = get_ma_column_for_stock(stocks_dict[ticker], 'Close', 10)
    stocks_dict[ticker]['20_ma'] = get_ma_column_for_stock(stocks_dict[ticker], 'Close', 20)
    stocks_dict[ticker]['50_ma'] = get_ma_column_for_stock(stocks_dict[ticker], 'Close', 50)
    stocks_dict[ticker]['ma_volume'] = get_ma_column_for_stock(stocks_dict[ticker], 'Volume', 20)
    stocks_dict[ticker]['atr'] = get_ATR_column_for_stock(stocks_dict[ticker], 14)
    stocks_dict[ticker]['distance_from_10_ma'] = get_distance_between_columns_for_stock(stocks_dict[ticker], 'Close', '10_ma')
    stocks_dict[ticker]['adx'], stocks_dict[ticker]['+di'], stocks_dict[ticker]['-di'] = get_adx_column_for_stock(stocks_dict[ticker], 14)
    stocks_dict[ticker]['rsi'] = rsi(stocks_dict[ticker], 14)
    stocks_dict[ticker]['stochastic_k'], stocks_dict[ticker]['stochastic_d'] = stochastic(stocks_dict[ticker], 14, 3)
    stocks_dict[ticker]['atr_volatility'], stocks_dict[ticker]['atr_volatility_ma'] = get_volatility_from_atr(stocks_dict[ticker], 14)
    stocks_dict[ticker]['signal_type'] = ''
    stocks_dict[ticker]['signal_direction'] = ''
    stocks_dict[ticker]['indicators_mid_levels_signal'] = ''
    stocks_dict[ticker]['indicators_mid_level_direction'] = ''
    stocks_dict[ticker]['cross_20_signal'] = ''
    stocks_dict[ticker]['cross_20_direction'] = ''
    stocks_dict[ticker]['cross_50_signal'] = ''
    stocks_dict[ticker]['cross_50_direction'] = ''
    stocks_dict[ticker] = indicators_mid_levels_signal(stocks_dict[ticker], 'indicators_mid_level_direction', 'indicators_mid_levels_signal')
    stocks_dict[ticker] = cross_20_ma(stocks_dict[ticker], 'cross_20_direction', 'cross_20_signal')
    stocks_dict[ticker] = cross_50_ma(stocks_dict[ticker], 'cross_50_direction', 'cross_50_signal')
    stocks_dict[ticker] = joint_signal(stocks_dict[ticker], 'signal_direction', 'signal_type')
    # stocks_dict[ticker] = parabolic_trending_n_periods(stocks_dict[ticker], 3, 'signal_direction', 'signal_type')
    stocks_dict[ticker] = calculate_exits_column_by_atr_and_prev_max_min(stocks_dict[ticker], 35)
    stocks_dict[ticker] = stocks_dict[ticker].reset_index()
    stocks_dict[ticker].to_csv(f'stocks_csvs_new/{ticker}_engineered.csv', index=False)
    # stocks_dict[ticker].tail(1000).plot(x="Date", y=["Close", "50_ma"])
    # plt.show()

# add data to some whole stocks data df
all_stocks_data_df['average_action_p_l'] = ''
all_stocks_data_df['median_action_p_l'] = ''
all_stocks_data_df['min_action_p_l'] = ''
all_stocks_data_df['max_action_p_l'] = ''
all_stocks_data_df['total_p_l'] = ''
all_stocks_data_df['total_correct_actions'] = ''
all_stocks_data_df['total_wrong_actions'] = ''
all_stocks_data_df['total_actions'] = ''
all_stocks_data_df['total_periods'] = ''
all_stocks_data_df['pct_actions'] = ''
all_stocks_data_df['pct_correct_actions'] = ''
for index, ticker in enumerate(adjusted_tickers):
    all_stocks_data_df['average_action_p_l'][index] = stocks_dict[ticker]['action_return'].replace('', np.nan).mean()
    all_stocks_data_df['median_action_p_l'][index] = stocks_dict[ticker]['action_return'].replace('', np.nan).median()
    all_stocks_data_df['min_action_p_l'][index] = stocks_dict[ticker]['action_return'].replace('', np.nan).min()
    all_stocks_data_df['max_action_p_l'][index] = stocks_dict[ticker]['action_return'].replace('', np.nan).max()
    temp_series_cumprod = (1 + stocks_dict[ticker]['action_return'].replace('', np.nan)).cumprod()
    if temp_series_cumprod.dropna().empty:
        all_stocks_data_df['total_p_l'][index] = 0
    else:
        all_stocks_data_df['total_p_l'][index] = temp_series_cumprod.dropna().iloc[-1] - 1
    all_stocks_data_df['total_correct_actions'][index] = stocks_dict[ticker]['action_return'][stocks_dict[ticker]['action_return'].replace('', np.nan) > 0].count()
    all_stocks_data_df['total_wrong_actions'][index] = stocks_dict[ticker]['action_return'][stocks_dict[ticker]['action_return'].replace('', np.nan) < 0].count()
    all_stocks_data_df['total_actions'][index] = all_stocks_data_df['total_correct_actions'][index] + all_stocks_data_df['total_wrong_actions'][index]
    all_stocks_data_df['total_periods'][index] = len(stocks_dict[ticker])
    all_stocks_data_df['pct_actions'][index] = all_stocks_data_df['total_actions'][index] / len(stocks_dict[ticker])
    all_stocks_data_df['pct_correct_actions'][index] = all_stocks_data_df['total_correct_actions'][index] / all_stocks_data_df['total_actions'][index]
all_stocks_data_df.to_csv(f'stocks_csvs_new/all_stocks_data.csv', index=False)

all_actions_df = pd.DataFrame()
for index, ticker in enumerate(adjusted_tickers):
    current_actions_df = stocks_dict[adjusted_tickers[index]].loc[stocks_dict[adjusted_tickers[index]]['in_position'] != '']
    current_actions_df['ticker'] = ticker
    current_actions_df = current_actions_df[current_actions_df['action_return_on_signal_index'] != '']
    if index == 0:
        all_actions_df = current_actions_df
    else:
        all_actions_df = pd.concat([all_actions_df, current_actions_df])

all_actions_df.to_csv(f'stocks_csvs_new/all_actions_df.csv', index=False)

latest_actions_df = pd.DataFrame()
for index, ticker in enumerate(adjusted_tickers):
    if stocks_dict[ticker]['in_position'].iloc[-1] != True:
        continue
    current_actions_df = stocks_dict[ticker]
    current_actions_df['ticker'] = ticker
    last_position_enter_index = len(current_actions_df)
    for i in range(len(current_actions_df), 0, -1):
        if current_actions_df['in_position'][i] != True:
            last_position_enter_index = i
            break
    current_actions_df = current_actions_df.tail(len(current_actions_df) - last_position_enter_index)
    if index == 0:
        latest_actions_df = current_actions_df
    else:
        latest_actions_df = pd.concat([latest_actions_df, current_actions_df])

latest_actions_df.to_csv(f'stocks_csvs_new/latest_actions_df.csv', index=False)
finish = 1

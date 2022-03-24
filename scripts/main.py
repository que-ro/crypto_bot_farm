import cbpro
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import math
import numpy as np

##############################
# power ratio util functions #
#############################
def update_power_ratio_for_currency_pair_dict(currency_pair_stat_dict, lowest_price, highest_price, Q1, median, Q3):
    print("before log")
    print(abs(Q3 - median) / abs(Q1 - median))
    print(abs(highest_price - median) / abs(lowest_price - median))
    print(lowest_price, Q1, median, Q3, highest_price)

    #init power ratio
    power_ratio_highestlowest = None
    power_ratio_Q3Q1 = None

    #power ratio highest lowest
    diff_abs_highest_median = abs(highest_price - median)
    diff_abs_lowest_median = abs(lowest_price - median)

    if(diff_abs_highest_median == 0 and diff_abs_lowest_median == 0):
        power_ratio_highestlowest = 0
    elif(diff_abs_highest_median == 0):
        power_ratio_highestlowest = -10
    elif (diff_abs_lowest_median == 0):
        power_ratio_highestlowest = 10
    else:
        power_ratio_highestlowest = math.log10(abs(diff_abs_highest_median) / abs(diff_abs_lowest_median))

    #power ratio Q3 Q1
    diff_abs_Q3_median = abs(Q3 - median)
    diff_abs_Q1_median = abs(Q1 - median)

    if (diff_abs_Q3_median == 0 and diff_abs_Q1_median == 0):
        power_ratio_Q3Q1 = 0
    elif (diff_abs_Q3_median == 0):
        power_ratio_Q3Q1 = -10
    elif (diff_abs_Q1_median == 0):
        power_ratio_Q3Q1 = 10
    else:
        power_ratio_Q3Q1 = math.log10(abs(diff_abs_Q3_median) / abs(diff_abs_Q1_median))

    #update currency_pair_stat_dict
    currency_pair_stat_dict['power_ratio_Q3Q1'] = power_ratio_Q3Q1
    currency_pair_stat_dict['power_ratio_highestlowest'] = power_ratio_highestlowest

#############################
# trajectory util functions #
############################
def init_trajectory_dict(index_tick, current_sma3):
    trajectory = {'start_tick': index_tick,
                  'end_tick': None,
                  'start_price': current_sma3,
                  'end_price': None,
                  'nb_ticks': 1,
                  'coeff_dir_sense': None,
                  'coeff_dir': None,
                  'traj_cat': None}
    return trajectory

def update_start_trajectory_variables(trajectory, current_sma3, previous_sma3):
    trajectory['nb_ticks'] = trajectory['nb_ticks'] + 1
    diff_curr_prev_sma3 = current_sma3 - previous_sma3
    if (diff_curr_prev_sma3 < 0):
        trajectory['coeff_dir_sense'] = -1
    elif (diff_curr_prev_sma3 > 0):
        trajectory['coeff_dir_sense'] = 1

def update_end_trajectory_variables(trajectory, end_tick_index, previous_sma3):
    #set directional coefficient of the trajectory
    trajectory['end_tick'] = end_tick_index
    trajectory['end_price'] = previous_sma3
    trajectory['coeff_dir'] = (trajectory['end_price'] - trajectory['start_price']) / (trajectory['end_tick'] - trajectory['start_tick'])

    #init trajectory category
    traj_category = ''

    #short/long
    if(trajectory['nb_ticks'] < 5):
        traj_category += 'short_'
    else:
        traj_category += 'long_'

    #weak/strong
    if(abs(trajectory['coeff_dir']) < 0.1):
        traj_category += 'weak_'
    else:
        traj_category += 'strong_'

    #decrease/increase
    if (trajectory['coeff_dir'] < 0):
        traj_category += 'decrease'
    else:
        traj_category += 'increase'

    #set trajectory category
    trajectory['traj_cat'] = traj_category

def is_first_trajectory(trajectory, current_sma3):
    return trajectory is None and math.isnan(current_sma3) == False

def is_start_of_a_trajectory(trajectory):
    return trajectory is not None and trajectory['coeff_dir_sense'] is None

def is_end_of_a_trajectory(trajectory, current_sma3, previous_sma3):
    return trajectory is not None and (current_sma3 * trajectory['coeff_dir_sense']) < (previous_sma3 * trajectory['coeff_dir_sense'])

def is_continue_of_a_trajectory(trajectory):
    return trajectory is not None

def get_trajectories_df(df_product_historic_rates):
    #init lowest and highest sma3
    lowest_sma3 = df_product_historic_rates.describe().loc['min', 'sma3']
    highest_sma3 = df_product_historic_rates.describe().loc['max', 'sma3']

    #init list of trajectories and trajectory
    list_trajectories = []  # [{start_tick, end_tick, start_price, end_price, nb_ticks, coeff_dir_sense, coeff_dir, traj_cat}, ... ]
    trajectory = None

    # loop through the ticks
    previous_close_price = None
    previous_sma3 = None
    for index, row in df_product_historic_rates.iterrows():

        # init current price and sma3
        current_close_price = row['close']
        current_sma3 = 2 * ((row['sma3'] - lowest_sma3) / (highest_sma3 - lowest_sma3)) - 1

        # case first trajectory
        if (is_first_trajectory(trajectory, current_sma3)):
            trajectory = init_trajectory_dict(index, current_sma3)
            previous_sma3 = current_sma3

        # case start of a trajectory
        elif (is_start_of_a_trajectory(trajectory)):
            update_start_trajectory_variables(trajectory, current_sma3, previous_sma3)
            previous_sma3 = current_sma3

        # case end of trajectory
        elif (is_end_of_a_trajectory(trajectory, current_sma3, previous_sma3)):
            update_end_trajectory_variables(trajectory, index - 1, previous_sma3)
            list_trajectories.append(trajectory)
            trajectory = init_trajectory_dict(index, current_sma3)
            previous_sma3 = current_sma3

        # case continue of trajectory
        elif (is_continue_of_a_trajectory(trajectory)):
            trajectory['nb_ticks'] = trajectory['nb_ticks'] + 1
            previous_sma3 = current_sma3

    # close last trajectory
    if (trajectory['start_tick'] < index):
        update_end_trajectory_variables(trajectory, index, previous_sma3)
        list_trajectories.append(trajectory)

    return pd.DataFrame(list_trajectories)

def update_traj_stat_for_currency_pair_dict(currency_pair_stat_dict, df_list_trajectories):

    # traj stat to add
    traj_stat_cols = ['nb_short_weak_decrease',
                      'nb_short_weak_increase',
                      'nb_short_strong_decrease',
                      'nb_short_strong_increase',
                      'nb_long_weak_decrease',
                      'nb_long_weak_increase',
                      'nb_long_strong_decrease',
                      'nb_long_strong_increase']

    #init stat
    for stat in traj_stat_cols:
        currency_pair_stat_dict[stat] = 0

    #update stat
    for traj_cat, value in df_list_trajectories['traj_cat'].value_counts().iteritems():
        currency_pair_stat_dict['nb_' + traj_cat] = value

#############################
# util nb crossed functions #
############################

def update_nb_crossed_for_currency_pair_dict(currency_pair_stat_dict, df_product_historic_rates, Q1, median, Q3):
    #init nb of times crossed
    nb_Q1_was_crossed = 0
    nb_median_was_crossed = 0
    nb_Q3_was_crossed = 0

    #loop through ticks
    for index, row in df_product_historic_rates.iterrows():
        start_price = row['open']
        close_price = row['close']

        if ((start_price >= median > close_price) or (close_price >= median > start_price)):
            nb_median_was_crossed += 1
        elif ((start_price >= Q3 > close_price) or (close_price >= Q3 > start_price)):
            nb_Q3_was_crossed += 1
        elif ((start_price >= Q1 > close_price) or (close_price >= Q1 > start_price)):
            nb_Q1_was_crossed += 1

    #set value for currency_pair_stat_dict
    currency_pair_stat_dict['nb_Q1_was_crossed'] = nb_Q1_was_crossed
    currency_pair_stat_dict['nb_median_was_crossed'] = nb_median_was_crossed
    currency_pair_stat_dict['nb_Q3_was_crossed'] = nb_Q3_was_crossed


#########################################
# util product historic rates functions #
########################################

def get_df_from_product_historic_rates(product_historic_rates):

    #get dataframe
    df_product_historic_rates = pd.DataFrame(product_historic_rates)
    df_product_historic_rates.set_axis(['time', 'low', 'high', 'open', 'close', 'volume'], axis=1, inplace=True)
    df_product_historic_rates.sort_values(by=['time'], inplace=True)
    df_product_historic_rates.reset_index(inplace=True)
    df_product_historic_rates.drop(['index'], axis=1, inplace=True)
    df_product_historic_rates['datetime'] = df_product_historic_rates.apply(
        lambda row: datetime.fromtimestamp(row['time']), axis=1)

    #calculate simple moving average
    df_product_historic_rates['sma3'] = df_product_historic_rates['close'].rolling(3).mean()
    df_product_historic_rates['sma5'] = df_product_historic_rates['close'].rolling(5).mean()
    df_product_historic_rates['sma10'] = df_product_historic_rates['close'].rolling(10).mean()
    df_product_historic_rates['sma15'] = df_product_historic_rates['close'].rolling(15).mean()
    df_product_historic_rates['sma20'] = df_product_historic_rates['close'].rolling(20).mean()

    return df_product_historic_rates

################################
# util currency pair functions #
###############################

def get_currency_pair_stat_dict(currency_pair_id, df_product_historic_rates):
    #init of dict with id
    currency_pair_stat_dict = {}
    currency_pair_stat_dict['currency_pair_id'] = currency_pair_id

    #get median, Q1, Q3, lowest, highest close price
    Q1 = df_product_historic_rates.describe().loc['25%', 'close']
    median = df_product_historic_rates.describe().loc['50%', 'close']
    Q3 = df_product_historic_rates.describe().loc['75%', 'close']
    lowest_price = df_product_historic_rates.describe().loc['min', 'close']
    highest_price = df_product_historic_rates.describe().loc['max', 'close']

    #calculate power ratio adn raw differences
    currency_pair_stat_dict['raw_diff_Q3Q1'] = Q3 - Q1
    currency_pair_stat_dict['raw_diff_highestlowest'] = highest_price - lowest_price
    update_power_ratio_for_currency_pair_dict(currency_pair_stat_dict, lowest_price, highest_price, Q1, median, Q3)

    #get trajectories stats as dataframe
    df_list_trajectories = get_trajectories_df(df_product_historic_rates)
    update_traj_stat_for_currency_pair_dict(currency_pair_stat_dict, df_list_trajectories)

    #get nb times Q1, median and Q3 crossed:
    update_nb_crossed_for_currency_pair_dict(currency_pair_stat_dict, df_product_historic_rates, Q1, median, Q3)

    return currency_pair_stat_dict

def get_currency_pair_df():
    public_client = cbpro.PublicClient()

    # datetimes used
    date_now = datetime.now()
    date_31h_before = date_now - timedelta(hours=31, minutes=0)
    date_16_before = date_now - timedelta(hours=16, minutes=0)
    date_1h_before = date_now - timedelta(hours=1, minutes=0)

    # granularity used in seconds (60, 300, 900, 3600, 21600, 86400)
    granularity = 300

    # quote_currency used (with what I will pay the transaction)
    quote_currency = "USD"

    # list of currency pairs used
    list_currency_pairs = []                # [{'currency_pair_id', 'quote_increment'}]
    for product in public_client.get_products():
        if product['quote_currency'] == quote_currency:
            list_currency_pairs.append({'currency_pair_id' : product['id'], 'quote_increment' : float(product['quote_increment'])})

    #loop through all currency_pairs
    list_currency_pair_dict = []
    for currency_pair in list_currency_pairs:

        #init currency pair id
        currency_pair_id = currency_pair['currency_pair_id']

        #init coinbase pro public client
        product_historic_rates = public_client.get_product_historic_rates(currency_pair_id,
                                                                          start=date_31h_before.isoformat(),
                                                                          end=date_16_before.isoformat(),
                                                                          granularity=granularity)

        #if less than 180 ticks, we don't use the pair
        nb_of_ticks = len(product_historic_rates)
        if (nb_of_ticks < 180):
            continue

        #get dataframe of product historic rates with moving average
        df_product_historic_rates = get_df_from_product_historic_rates(product_historic_rates)

        #get currency_pair_dict
        currency_pair_dict = get_currency_pair_stat_dict(currency_pair_id, df_product_historic_rates)

        #add quote_increment
        currency_pair_dict['quote_increment'] = currency_pair['quote_increment']

        #add to list
        list_currency_pair_dict.append(currency_pair_dict)

    return pd.DataFrame(list_currency_pair_dict)

########
# Main #
#######




    #todo all calculations, statistics for the metrics with the 180 ticks



#test zone

public_client = cbpro.PublicClient()

# datetimes used
date_now = datetime.now()
date_31h_before = date_now - timedelta(hours=31, minutes=0)
date_16_before = date_now - timedelta(hours=16, minutes=0)
date_1h_before = date_now - timedelta(hours=1, minutes=0)

# granularity used in seconds (60, 300, 900, 3600, 21600, 86400)
granularity = 300

# quote_currency used (with what I will pay the transaction)
quote_currency = "USD"

product_historic_rates = public_client.get_product_historic_rates('GRT-USD',
                                                                          start=date_31h_before.isoformat(),
                                                                          end=date_16_before.isoformat(),
                                                                          granularity=granularity)

df_product_historic_rates = get_df_from_product_historic_rates(product_historic_rates)
df_product_historic_rates.plot(x='datetime', y=['close', 'sma3', 'sma5', 'sma10', 'sma15', 'sma20'])


date_test = datetime.fromtimestamp(1647784560)
date_test2 = datetime.fromtimestamp(1647783420)
date_test.isoformat()
date_test2.isoformat()

####still in the test zone
test = get_currency_pair_df()
public_client = cbpro.PublicClient()
currency_pair_id = 'ALGO-USD'
product_historic_rates = public_client.get_product_historic_rates(currency_pair_id,
                                                                          start=date_31h_before.isoformat(),
                                                                          end=date_16_before.isoformat(),
                                                                          granularity=granularity)

df_product_historic_rates = get_df_from_product_historic_rates(product_historic_rates)
Q1 = df_product_historic_rates.describe().loc['25%', 'close']
median = df_product_historic_rates.describe().loc['50%', 'close']
Q3 = df_product_historic_rates.describe().loc['75%', 'close']
index_of_currency_of_interest = test.index[test['currency_pair_id'] == currency_pair_id][0]
quote_increment = test.iloc[index_of_currency_of_interest]['quote_increment']
target_pct_profit_btwn_trades = 0.5
bank_quote_volume = 50
quote_volume_per_trade = 10
fees_rate = 0.006

product_future_rates = public_client.get_product_historic_rates(currency_pair_id,
                                                                          start=date_16_before.isoformat(),
                                                                          end=date_1h_before.isoformat(),
                                                                          granularity=granularity)

df_product_future_rates = get_df_from_product_historic_rates(product_future_rates)

df_product_future_rates.plot(x='datetime', y=['high', 'low'])
df_product_historic_rates.plot(x='datetime', y=['high', 'low'])

quote_increment_multiplier = get_quote_increment_multiplier(target_pct_profit_btwn_trades, quote_increment, quote_volume_per_trade, Q1, fees_rate)
is_strat_viable_over_Q1 = is_currency_pair_viable_for_over_Q1_buying(quote_increment, quote_increment_multiplier, median, Q3)
orders_scheme = get_orders_scheme(quote_increment, quote_increment_multiplier, Q1, median, Q3, is_strat_viable_over_Q1, nb_of_orders=20)
simulate_tradings(df_product_future_rates, orders_scheme, bank_quote_volume, quote_volume_per_trade, fees_rate)

def get_fees_of_trade(volume, fees_rate):
    return volume * fees_rate

def get_quote_increment_multiplier(target_pct_profit_btwn_trades, quote_increment, quote_volume_per_trade, Q1, fees_rate):

    quote_increment_multiplier = 0
    pct_profit_btwn_trades = -1
    while pct_profit_btwn_trades < target_pct_profit_btwn_trades:
        quote_increment_multiplier += 1

        # Init variables
        bank_quote_init = quote_volume_per_trade
        bank_quote = bank_quote_init
        bank_base = 0
        buying_price = Q1
        selling_price = Q1 + (quote_increment * quote_increment_multiplier)

        # Buying the base coin
        buying_fees = get_fees_of_trade(bank_quote, fees_rate)
        bank_base = (bank_quote - buying_fees) / buying_price
        bank_quote = bank_quote - bank_quote

        # Selling the base coin
        selling_fees = get_fees_of_trade(bank_base, fees_rate)
        bank_quote = (bank_base - selling_fees) * selling_price
        bank_base = bank_base - bank_base

        # Measure of pct_profit
        gain_loss = bank_quote - bank_quote_init
        pct_profit_btwn_trades = (gain_loss / bank_quote_init) * 100

    return quote_increment_multiplier

def is_currency_pair_viable(quote_increment, quote_increment_multiplier, Q1, Q3):
    return (Q1 + quote_increment * quote_increment_multiplier) < Q3

def is_currency_pair_viable_for_over_Q1_buying(quote_increment, quote_increment_multiplier, median, Q3):
    return (median + quote_increment * quote_increment_multiplier) < Q3

def get_orders_scheme(quote_increment, quote_increment_multiplier, Q1, median, Q3, is_strat_viable_over_Q1, nb_of_orders=20):
    #init orders scheme
    orders_scheme = []          # [{'order_id', 'buying_price', 'is_bought', 'selling_price', 'base_coin_traded_vol', 'just_bought'}, ...]

    #init starting price
    starting_price = Q1
    if(is_strat_viable_over_Q1):
        starting_price =  median

    #add orders to the scheme
    for idx in range(0, nb_of_orders):
        #init orders characteristics
        buying_price = starting_price - (quote_increment * quote_increment_multiplier * idx)
        selling_price = buying_price + (quote_increment * quote_increment_multiplier)
        is_bought = False
        base_coin_traded_vol = 0

        #add to orders scheme if it doesn't go over the Q3 price
        if(selling_price <= Q3):
            orders_scheme.append({'order_id' : idx,
                'buying_price': buying_price,
                'is_bought': is_bought,
                'selling_price': selling_price,
                'base_coin_traded_vol' : base_coin_traded_vol,
                'just_bought' : False})

    return pd.DataFrame(orders_scheme)


def simulate_tradings(df_product_future_rates, orders_scheme, bank_quote_volume, quote_volume_per_trade, fees_rate):

    #init varaibles
    bank_quote = bank_quote_volume
    bank_base = 0
    last_tick = df_product_future_rates.index[-1]

    for index, ticks in df_product_future_rates.iterrows():

        print('===== Tick ' + str(index) + " =====")

        #init high price
        high_price = ticks['high']
        low_price = ticks['low']

        #update just bought parameter to false
        orders_scheme['just_bought'] = False

        #check if there is orders that could be bought
        orders_with_buying_price_under_high_price = orders_scheme['buying_price'] < high_price
        orders_with_buying_price_over_low_price = orders_scheme['buying_price'] > low_price
        orders_not_bought_yet = orders_scheme['is_bought'] == False
        orders_that_could_be_bought = orders_scheme[orders_with_buying_price_under_high_price & orders_not_bought_yet & orders_with_buying_price_over_low_price]

        #buy those orders
        for idx_order, order in orders_that_could_be_bought.iterrows():

            #enough money?
            is_there_enough_money = (bank_quote - quote_volume_per_trade) >= 0

            #do the trade if there is enough money
            if(is_there_enough_money):

                #update bank
                bank_quote = bank_quote - quote_volume_per_trade
                base_coin_bought_volume = (quote_volume_per_trade - get_fees_of_trade(quote_volume_per_trade, fees_rate)) / order['buying_price']
                bank_base = bank_base + base_coin_bought_volume

                #update order status
                orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['is_bought']] = True
                orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['base_coin_traded_vol']] = base_coin_bought_volume
                orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['just_bought']] = True

                print('buying order | bank_quote : ' + str(bank_quote) + ' | bank_base : ' + str(bank_base) +
                        ' | highest_price : ' + str(high_price) + ' | buying price : ' + str(order['buying_price']))


        # check if there is orders that could be sold
        orders_with_selling_price_under_high_price = orders_scheme['selling_price'] < high_price
        orders_bought_already = orders_scheme['is_bought'] == True
        orders_not_just_bought = orders_scheme['just_bought'] == False
        orders_that_could_be_sold = orders_scheme[
            orders_with_selling_price_under_high_price & orders_bought_already & orders_not_just_bought]

        # sell those orders
        for idx_order, order in orders_that_could_be_sold.iterrows():
            # update bank
            quote_coin_bought_volume = (order['base_coin_traded_vol'] - get_fees_of_trade(
                order['base_coin_traded_vol'],
                fees_rate)) * order[
                                           'selling_price']
            bank_quote = bank_quote + quote_coin_bought_volume
            bank_base = bank_base - order['base_coin_traded_vol']

            # update order status
            orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['is_bought']] = False
            orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['base_coin_traded_vol']] = 0

            print('selling order | bank_quote : ' + str(bank_quote) + ' | bank_base : ' + str(bank_base)+
                        ' | highest_price : ' + str(high_price) + ' | selling price : ' + str(order['selling_price']))

        #close trade at the last tick
        if(index == last_tick):

            #get close price
            close_price = ticks['close']

            #get all orders waiting to be sold
            orders_that_need_to_be_closed = orders_scheme[orders_scheme['is_bought'] == True]

            for idx, order in orders_that_need_to_be_closed.iterrows():

                #update bank
                quote_coin_bought_volume = (order['base_coin_traded_vol'] * get_fees_of_trade(order['base_coin_traded_vol'], fees_rate)) * close_price
                bank_quote = bank_quote + quote_coin_bought_volume
                bank_base = bank_base - order['base_coin_traded_vol']

                #update order status
                orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['is_bought']] = False
                orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['base_coin_traded_vol']] = 0

                print('closing order | bank_quote : ' + str(bank_quote) + ' | bank_base : ' + str(bank_base))


    print('bank_quote_init : ' + str(bank_quote_volume) + ' | bank_quote_end : ' + str(bank_quote))


def get_best_pct_profit_btwn_trades(df_product_historic_rates, currency_pair_id):

    #Init variables
    Q1 = df_product_historic_rates.describe().loc['25%', 'close']
    median = df_product_historic_rates.describe().loc['50%', 'close']
    Q3 = df_product_historic_rates.describe().loc['75%', 'close']
    index_of_currency_of_interest = test.index[test['currency_pair_id'] == currency_pair_id][0]
    quote_increment = test.iloc[index_of_currency_of_interest]['quote_increment']
    bank_quote_volume = 50
    quote_volume_per_trade = 10
    fees_rate = 0.006
    pct_profit_btwn_trades_increment = 0.1
    pct_profit_btwn_trades = 0.1

    #Calculate first gain_loss

    #Loop on
    while is_increasing_pct_profit_more_viable:

    pass

def get_strategy_label_for_currency_pair(currency_pair_df, ):
    #init toutes les values, à voir si à mettre dans la méthode ou non
    #boucle sur toutes les paires de monnaies
    #maj du df avec le label
    pass

#get_quote_increment_multiplier(percent_profit_btween_trades)
#is_currency_pair_viable(quote_increment_multiplier) if I buy at Q1 is Q1 + quote_increment * multiplier < Q3? if not, not viable
#get_orders_scheme() #check if they are viable: buying not over median, selling point = price + quote_increment * multiplier < Q3
#simulate trade history, when you can buy, when you can sell, at the end sell everything that still is there to the current price.

#orders_schemes : [{'buying_price', 'is_bought', 'selling_price'}, ...]
#if trade price is under buying_price and is not already bought => buy
#if trade price is over selling_price and the and is already_bought => sell

#simulate_trade_history()
#foreach order check if start_price, close_price was passed
#after 120 ticks, stop_pacing_selling_orders
#close the sellings, by selling everything at the current price


product_future_rates = public_client.get_product_historic_rates(currency_pair_id,
                                                                          start=date_16_before.isoformat(),
                                                                          end=date_1h_before.isoformat(),
                                                                          granularity=granularity)

df_product_future_rates = get_df_from_product_historic_rates(product_future_rates)

df_product_future_rates.plot(x='datetime', y=['high', 'low'])
df_product_historic_rates.plot(x='datetime', y=['high', 'low'])
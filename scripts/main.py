import cbpro
from datetime import datetime, timedelta
import pandas as pd
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 300
import matplotlib.pyplot as plt
import math
import numpy as np

from basic_describer import BasicDescriber

date_start = datetime.now() - timedelta(hours=61)
granularity = 300
quote_currency = 'USD'

describer = BasicDescriber(date_start, granularity, quote_currency)
describer.get_df_product_with_description()






    #todo all calculations, statistics for the metrics with the 180 ticks

#######
# Simulating trade util functions
######

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

    #init variables
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


def to_delete(currency_pair_id):
    product_historic_rates = public_client.get_product_historic_rates(currency_pair_id,
                                                                      start=date_31h_before.isoformat(),
                                                                      end=date_16_before.isoformat(),
                                                                      granularity=granularity)

    df_product_historic_rates = get_df_from_product_historic_rates(product_historic_rates,
                                                                       date_31h_before,
                                                                       date_16_before,
                                                                       granularity)

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

    df_product_future_rates = get_df_from_product_historic_rates(product_future_rates,
                                                                       date_16_before,
                                                                       date_1h_before,
                                                                       granularity)

    df_product_historic_rates.plot(x='datetime', y=['high', 'low'])
    df_product_future_rates.plot(x='datetime', y=['high', 'low'])

    quote_increment_multiplier = get_quote_increment_multiplier(target_pct_profit_btwn_trades, quote_increment,
                                                                quote_volume_per_trade, Q1, fees_rate)
    is_strat_viable_over_Q1 = is_currency_pair_viable_for_over_Q1_buying(quote_increment, quote_increment_multiplier,
                                                                         median, Q3)
    orders_scheme = get_orders_scheme(quote_increment, quote_increment_multiplier, Q1, median, Q3,
                                      is_strat_viable_over_Q1, nb_of_orders=20)
    simulate_tradings(df_product_future_rates, orders_scheme, bank_quote_volume, quote_volume_per_trade, fees_rate)











#zone to delete de test:
date_start = datetime.now() - timedelta(hours=2)
date_end = date_start + timedelta(hours=1)

granularity = 300

# quote_currency used (with what I will pay the transaction)
quote_currency = "USD"

product_historic_rates = public_client.get_product_historic_rates('XRP-USD',
                                                                          start=date_start.isoformat(),
                                                                          end=date_end.isoformat(),
                                                                          granularity=granularity)

df_product_historic_rates = pd.DataFrame(product_historic_rates)




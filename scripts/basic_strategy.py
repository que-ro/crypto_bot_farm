from interfaces import StrategyRunnerInterface
from datetime import datetime, timedelta
import cbpro
import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd
from utils_df_product_historic_rates import UtilsDfProductHistoricRates

class BasicStrategyRunner(StrategyRunnerInterface):

    def __init__(self, date_start: datetime, date_prior_used_to_describe: datetime, granularity, df_products: object):

        #init dates
        self.date_start = date_start
        self.date_stop_active_trading = self.date_start + timedelta(hours=15)
        self.date_wait_until = self.date_stop_active_trading + timedelta(hours=30)
        self.date_prior_start = date_prior_used_to_describe

        #init granularity
        self.granularity = granularity

        #init products dataframe with their associated stats
        self.df_products = df_products

        #init value for the simulations
        self.FEES_RATE = 0.006
        self.BANK_QUOTE = 50
        self.VOLUME_PER_TRADE = 10


    #region Interface implemented method
    @staticmethod
    def check_parameter(date_start: datetime, granularity: int) -> None:
        if (granularity == 300):
            raise ValueError('Only 300s intervals are supported at the moment')
        if (date_start + timedelta(hours=45) > datetime.now()):
            raise ValueError('The strategy is spread on 45 hours. The start date should be thus be 45h anterior to now')

    def get_df_product_with_strat_result(self) -> object:

        #Initialisation of new cols
        self.df_products['gain_loss'] = None
        self.df_products['gain_loss_percentage'] = None
        self.df_products['nb_bought_order'] = None
        self.df_products['nb_sold_order'] = None

        #Loop through all products
        for index, product in self.df_products.iterrows():

            # get Q1, median, Q3, lowest, highest price, quote increment
            currency_pair_id = product['currency_pair_id']
            Q1 = product['Q1']
            median = product['median']
            Q3 = product['Q3']
            lowest_price = product['lowest_price']
            highest_price = product['highest_price']
            quote_increment = product['quote_increment']

            #Find best pct profit between trades
            target_pct_profit_btwn_trades = self.get_best_pct_profit_btwn_trades(product)

            #Find quote increment multiplier
            quote_increment_multiplier = self.get_quote_increment_multiplier(target_pct_profit_btwn_trades, quote_increment,
                                                                             Q1)
            #Get scheme of orders
            orders_scheme = self.get_orders_scheme(quote_increment, quote_increment_multiplier, Q1, median, Q3,
                                                   nb_of_orders=5)

            #Get price history dataframe
            df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(currency_pair_id,
                                                                         self.date_start,
                                                                         self.date_wait_until,
                                                                         self.granularity)

            #Get simulation variables
            gain_loss, gain_loss_percentage, nb_bought_order, nb_sold_order = \
                self.simulate_tradings(self.date_start, self.date_stop_active_trading, df_product_historic_rates, orders_scheme)

            #Add value to the specific row
            index = self.df_products.index[
                self.df_products['currency_pair_id'] == currency_pair_id]
            self.df_products.loc[index, ['gain_loss']] = gain_loss
            self.df_products.loc[index, ['gain_loss_percentage']] = gain_loss_percentage
            self.df_products.loc[index, ['nb_bought_order']] = nb_bought_order
            self.df_products.loc[index, ['nb_sold_order']] = nb_sold_order

        #Change type of cols
        self.df_products['gain_loss'] = self.df_products['gain_loss'].astype(float)
        self.df_products['gain_loss_percentage'] = self.df_products['gain_loss_percentage'].astype(float)
        self.df_products['nb_bought_order'] = self.df_products['nb_bought_order'].astype(int)
        self.df_products['nb_sold_order'] = self.df_products['nb_sold_order'].astype(int)

        #Return dataframe
        return self.df_products

    #endregion

    #region Dynamic initialisation of trading variables

    def get_best_pct_profit_btwn_trades(self, product_with_stats):

        currency_pair_id = product_with_stats['currency_pair_id']
        Q1 = product_with_stats['Q1']
        median = product_with_stats['median']
        Q3 = product_with_stats['Q3']
        quote_increment = product_with_stats['quote_increment']

        pct_profit_btwn_trades_increment = 0.1
        pct_profit_btwn_trades = 0.1

        # Get df historic rates of product
        df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(
            currency_pair_id,
            self.date_prior_start,
            self.date_start,
            self.granularity)

        # Calculate first gain and loss
        quote_increment_multiplier = self.get_quote_increment_multiplier(pct_profit_btwn_trades, quote_increment, Q1)

        orders_scheme = self.get_orders_scheme(quote_increment, quote_increment_multiplier, Q1, median, Q3, nb_of_orders=5)

        gain_loss, gain_loss_percentage, nb_bought_order, nb_sold_order = \
            self.simulate_tradings(self.date_prior_start, self.date_start, df_product_historic_rates, orders_scheme)

        # Set first best pct profit between trades and previous gain_loss
        best_pct_profit_btwn_trades = pct_profit_btwn_trades
        previous_gain_loss = gain_loss

        print('pct profit between trades : ' + str(pct_profit_btwn_trades) + ' | gainloss = ' + str(gain_loss))

        # Loop and check if pct profit between trades can be better
        is_gain_loss_better = True
        while is_gain_loss_better:
            pct_profit_btwn_trades = pct_profit_btwn_trades + pct_profit_btwn_trades_increment

            # Calculate first gain and loss
            quote_increment_multiplier = self.get_quote_increment_multiplier(pct_profit_btwn_trades, quote_increment, Q1)

            orders_scheme = self.get_orders_scheme(quote_increment, quote_increment_multiplier, Q1, median, Q3,
                                              nb_of_orders=5)

            gain_loss, gain_loss_percentage, nb_bought_order, nb_sold_order = \
                self.simulate_tradings(self.date_prior_start, self.date_start, df_product_historic_rates, orders_scheme)

            print('pct profit between trades : ' + str(pct_profit_btwn_trades) + ' | gainloss = ' + str(gain_loss))

            # Is current gain loss better tNonehan previous
            if (gain_loss - previous_gain_loss > 0):

                # Set best pct profit between trades and previous gain_loss
                best_pct_profit_btwn_trades = pct_profit_btwn_trades
                previous_gain_loss = gain_loss

            # If not, stop loop
            else:
                is_gain_loss_better = False

        return best_pct_profit_btwn_trades

    def get_quote_increment_multiplier(self, target_pct_profit_btwn_trades, quote_increment, Q1):

        quote_increment_multiplier = 0
        pct_profit_btwn_trades = -1
        while pct_profit_btwn_trades < target_pct_profit_btwn_trades:
            quote_increment_multiplier += 1

            # Init variables
            bank_quote_init = self.VOLUME_PER_TRADE
            bank_quote = bank_quote_init
            bank_base = 0
            buying_price = Q1
            selling_price = Q1 + (quote_increment * quote_increment_multiplier)

            # Buying the base coin
            buying_fees = self.get_fees_of_trade(bank_quote)
            bank_base = (bank_quote - buying_fees) / buying_price
            bank_quote = bank_quote - bank_quote

            # Selling the base coin
            selling_fees = self.get_fees_of_trade(bank_base)
            bank_quote = (bank_base - selling_fees) * selling_price
            bank_base = bank_base - bank_base

            # Measure of pct_profit
            gain_loss = bank_quote - bank_quote_init
            pct_profit_btwn_trades = (gain_loss / bank_quote_init) * 100

        return quote_increment_multiplier

    def get_fees_of_trade(self, volume):
        return volume * self.FEES_RATE

    def get_orders_scheme(self, quote_increment, quote_increment_multiplier, Q1, median, Q3, nb_of_orders=5):
        # init orders scheme
        orders_scheme = []  # [{'order_id', 'buying_price', 'is_bought', 'selling_price', 'base_coin_traded_vol', 'just_bought'}, ...]

        # init boolean checking if strategy is viable over Q1
        is_strat_viable_over_Q1 = self.is_currency_pair_viable_for_over_Q1_buying(quote_increment,
                                                                             quote_increment_multiplier,
                                                                             median, Q3)

        # init starting price
        starting_price = Q1
        if (is_strat_viable_over_Q1):
            starting_price = median

        # add orders to the scheme
        for idx in range(0, nb_of_orders):
            # init orders characteristics
            buying_price = starting_price - (quote_increment * quote_increment_multiplier * idx)
            selling_price = buying_price + (quote_increment * quote_increment_multiplier)
            is_bought = False
            base_coin_traded_vol = 0

            # add to orders scheme if it doesn't go over the Q3 price
            if (selling_price <= Q3):
                orders_scheme.append({'order_id': idx,
                                      'buying_price': buying_price,
                                      'is_bought': is_bought,
                                      'selling_price': selling_price,
                                      'base_coin_traded_vol': base_coin_traded_vol,
                                      'just_bought': False})

        return pd.DataFrame(orders_scheme)

    def is_currency_pair_viable_for_over_Q1_buying(self, quote_increment, quote_increment_multiplier, median, Q3):
        return (median + quote_increment * quote_increment_multiplier) < Q3

    def simulate_tradings(self, date_start, date_stop_active_trading, df_product_future_rates, orders_scheme):

        # init variables
        bank_quote = self.BANK_QUOTE
        bank_base = 0
        last_tick = df_product_future_rates.index[-1]
        nb_bought_order = 0
        nb_sold_order = 0

        for index, ticks in df_product_future_rates.iterrows():

            # print('===== Tick ' + str(index) + " =====")

            # init high price
            high_price = ticks['high']
            low_price = ticks['low']

            # update just bought parameter to false
            orders_scheme['just_bought'] = False

            # are we still in trading active timezone
            are_we_in_active_trading_timezone = date_start <= ticks['datetime'] <= date_stop_active_trading
            if(are_we_in_active_trading_timezone):

                # check if there is orders that could be bought
                orders_with_buying_price_under_high_price = orders_scheme['buying_price'] < high_price
                orders_with_buying_price_over_low_price = orders_scheme['buying_price'] > low_price
                orders_not_bought_yet = orders_scheme['is_bought'] == False
                orders_that_could_be_bought = orders_scheme[
                    orders_with_buying_price_under_high_price & orders_not_bought_yet & orders_with_buying_price_over_low_price]

                # buy those orders
                for idx_order, order in orders_that_could_be_bought.iterrows():

                    # enough money?
                    is_there_enough_money = (bank_quote - self.VOLUME_PER_TRADE) >= 0

                    # do the trade if there is enough money
                    if (is_there_enough_money):
                        # update bank
                        bank_quote = bank_quote - self.VOLUME_PER_TRADE
                        base_coin_bought_volume = (self.VOLUME_PER_TRADE - self.get_fees_of_trade(
                            self.VOLUME_PER_TRADE)) / order['buying_price']
                        bank_base = bank_base + base_coin_bought_volume

                        # update order status
                        orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['is_bought']] = True
                        orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], [
                            'base_coin_traded_vol']] = base_coin_bought_volume
                        orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['just_bought']] = True

                        # update nb of bought orders
                        nb_bought_order += 1

                        # print('buying order | bank_quote : ' + str(bank_quote) + ' | bank_base : ' + str(bank_base) +
                        #        ' | highest_price : ' + str(high_price) + ' | buying price : ' + str(order['buying_price']))


            # check if there is orders that could be sold
            orders_with_selling_price_under_high_price = orders_scheme['selling_price'] < high_price
            orders_bought_already = orders_scheme['is_bought'] == True
            orders_not_just_bought = orders_scheme['just_bought'] == False
            orders_that_could_be_sold = orders_scheme[
                orders_with_selling_price_under_high_price & orders_bought_already & orders_not_just_bought]

            # sell those orders
            for idx_order, order in orders_that_could_be_sold.iterrows():
                # update bank
                quote_coin_bought_volume = (order['base_coin_traded_vol'] - self.get_fees_of_trade(order['base_coin_traded_vol'])) * order['selling_price']
                bank_quote = bank_quote + quote_coin_bought_volume
                bank_base = bank_base - order['base_coin_traded_vol']

                # update order status
                orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['is_bought']] = False
                orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['base_coin_traded_vol']] = 0

                # update nb of sold orders
                nb_sold_order += 1

                # print('selling order | bank_quote : ' + str(bank_quote) + ' | bank_base : ' + str(bank_base)+
                #            ' | highest_price : ' + str(high_price) + ' | selling price : ' + str(order['selling_price']))

            # close trade at the last tick
            if (index == last_tick):

                # get close price
                close_price = ticks['close']

                # get all orders waiting to be sold
                orders_that_need_to_be_closed = orders_scheme[orders_scheme['is_bought'] == True]

                for idx, order in orders_that_need_to_be_closed.iterrows():
                    # update bank
                    quote_coin_bought_volume = (order['base_coin_traded_vol'] - self.get_fees_of_trade(order['base_coin_traded_vol'])) * close_price
                    bank_quote = bank_quote + quote_coin_bought_volume
                    bank_base = bank_base - order['base_coin_traded_vol']

                    # update order status
                    orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['is_bought']] = False
                    orders_scheme.loc[orders_scheme['order_id'] == order['order_id'], ['base_coin_traded_vol']] = 0

                    # print('closing order | bank_quote : ' + str(bank_quote) + ' | bank_base : ' + str(bank_base))

        print('bank_quote_init : ' + str(self.BANK_QUOTE) + ' | bank_quote_end : ' + str(bank_quote))

        # set returned values
        gain_loss = bank_quote - self.BANK_QUOTE
        gain_loss_percentage = ((bank_quote - self.BANK_QUOTE) / self.BANK_QUOTE) * 100

        return gain_loss, gain_loss_percentage, nb_bought_order, nb_sold_order

    #endregion
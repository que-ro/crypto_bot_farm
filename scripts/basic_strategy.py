from interfaces import ProductDescriberInterface
from datetime import datetime, timedelta
import cbpro
import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd

class BasicStrategyRunner(StrategyRunnerInterface):

    def __init__(self, date_start: datetime, date_prior_used_to_describe, df_products: object):

        #init dates
        self.date_start = self.date_start
        self.date_stop_active_trading = self.date_start_trading + timedelta(hours=15)
        self.date_wait_until = self.date_stop_active_trading + timedelta(hours=30)
        self.date_prior_start = date_prior_used_to_describe

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

        for index, product in df_products:

            # get Q1, median, Q3, lowest, highest price
            Q1 = product['Q1']
            median = product['median']
            Q3 = product['Q3']
            lowest_price = product['lowest_price']
            highest_price = product['highest_price']
            quote_increment = product['quote_increment']
            target_pct_profit_btwn_trades =


        pass
    #endregion

    #region Dynamic initialisation of trading variables

    def get_best_pct_profit_btwn_trades(self, df_product_historic_rates, currency_pair_id):

        # Init variables
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

        # Calculate first gain_loss

        # Loop on
        while is_increasing_pct_profit_more_viable:

        pass

    #endregion
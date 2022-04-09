from interfaces import StrategyRunnerInterface
from datetime import datetime, timedelta
import pandas as pd
from utils_df_product_historic_rates import UtilsDfProductHistoricRates
import matplotlib.pyplot as plt

class CustomStrategy1Runner(StrategyRunnerInterface):

    def __init__(self, date_start: datetime, granularity, df_products: object):

        # if granularity = 300
        self.time_needed_for_process = timedelta(hours=45)

        #init dates
        self.date_start = date_start
        self.date_stop_active_trading = self.date_start + timedelta(hours=15)
        self.date_wait_until = self.date_stop_active_trading + timedelta(hours=30)

        #date prior to start depending on granularity
        #if(granularity == 300):
        self.date_prior_start = self.date_start - timedelta(hours=15)

        #init granularity
        self.granularity = granularity

        #init products dataframe with their associated stats
        self.df_products = df_products

        #check if df_products contains the column needed
        assert 'y_support' in self.df_products.columns, 'The strategy runner dataframe should contain the "y_support" column'
        assert 'y_resistance' in self.df_products.columns, 'The strategy runner dataframe should contain the "y_resistance" column'

        #init value for the simulations
        self.FEES_RATE = 0.006
        self.BANK_QUOTE = 50
        self.VOLUME_PER_TRADE = 50

    # region Interface implemented method
    @staticmethod
    def check_parameter(date_start: datetime, granularity: int) -> None:
        if (granularity == 300):
            raise ValueError('Only 300s intervals are supported at the moment')
        if (date_start + timedelta(hours=45) > datetime.now()):
            raise ValueError(
                'The strategy is spread on 45 hours. The start date should be thus be 45h anterior to now')

    @staticmethod
    def time_needed_for_process(granularity):
        assert granularity == 300, 'Only 300s intervals are supported at the moment'

        # if granylarity = 300:
        return timedelta(hours=45)

    @staticmethod
    def get_name() -> str:
        return 'CustomStrategy1'

    def get_df_product_with_strat_result(self) -> object:
        # Initialisation of new cols
        self.df_products['gain_loss'] = None
        self.df_products['gain_loss_percentage'] = None
        self.df_products['nb_bought_order'] = None
        self.df_products['nb_sold_order'] = None

        # Loop through all products
        for index, product in self.df_products.iterrows():

            #Init variables used to simulate trading
            currency_pair_id = product['currency_pair_id']
            y_support = product['y_support']
            y_resistance = product['y_resistance']

            print('==========================================')
            print(currency_pair_id)
            print('==========================================')

            #Get price history dataframe
            df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(
                currency_pair_id,
                self.date_start,
                self.date_wait_until,
                self.granularity
            )
            # Get simulation variables
            gain_loss, gain_loss_percentage, nb_bought_order, nb_sold_order = \
                self.simulate_tradings(
                    df_price=df_product_historic_rates,
                    y_support=y_support,
                    y_resistance=y_resistance
                )

            # Add value to the specific row
            index = self.df_products.index[self.df_products['currency_pair_id'] == currency_pair_id]
            self.df_products.loc[index, ['gain_loss']] = gain_loss
            self.df_products.loc[index, ['gain_loss_percentage']] = gain_loss_percentage
            self.df_products.loc[index, ['nb_bought_order']] = nb_bought_order
            self.df_products.loc[index, ['nb_sold_order']] = nb_sold_order


        # Change type of cols
        self.df_products['gain_loss'] = self.df_products['gain_loss'].astype(float)
        self.df_products['gain_loss_percentage'] = self.df_products['gain_loss_percentage'].astype(float)
        self.df_products['nb_bought_order'] = self.df_products['nb_bought_order'].astype(int)
        self.df_products['nb_sold_order'] = self.df_products['nb_sold_order'].astype(int)

        # Return dataframe
        return self.df_products

    #endregion

    #region Trading simulation methods

    def simulate_tradings(self, df_price, y_support, y_resistance):

        #Init variables
        bank_quote = self.BANK_QUOTE
        bank_base = 0
        last_tick_index = df_price.index[-1]
        nb_bought_order = 0
        nb_sold_order = 0
        is_there_an_order_bought = False
        is_trading_closed = False
        y_risk = y_support - (y_resistance - y_support) * 1.5


        for index, ticks in df_price.iterrows():

            #Init price variables
            price_low = ticks['low']
            price_high = ticks['high']
            close_price = ticks['close']

            #Buying section
            are_we_in_active_trading_timezone = self.date_start <= ticks['datetime'] <= self.date_stop_active_trading
            is_price_under_support = price_low < y_support
            if(are_we_in_active_trading_timezone and not is_there_an_order_bought and is_price_under_support):

                #Update banks
                trade_volume = bank_quote
                bank_quote = bank_quote - trade_volume
                bank_base = (trade_volume - self.get_fees_of_trade(trade_volume)) / y_support

                #Save bought order
                is_there_an_order_bought = True
                nb_bought_order += 1


            #Selling section
            is_price_over_resistance = price_high > y_resistance
            if(is_price_over_resistance and is_there_an_order_bought):

                #Update banks
                trade_volume = bank_base
                bank_base = bank_base - trade_volume
                bank_quote = (trade_volume - self.get_fees_of_trade(trade_volume)) * y_resistance

                #Update sold order
                is_there_an_order_bought = False
                nb_sold_order += 1

            #Risk management section
            if(is_there_an_order_bought):
                if(close_price <= y_risk):
                    is_trading_closed = True

            #Closing trade section
            is_trading_closed = is_trading_closed or last_tick_index == index
            if(is_trading_closed):

                #If there is still an order
                if(is_there_an_order_bought):
                    #Update banks
                    trade_volume = bank_base
                    bank_base = bank_base - trade_volume
                    bank_quote = (trade_volume - self.get_fees_of_trade(trade_volume)) * close_price

                    #Update sold order
                    is_there_an_order_bought = False

                #In any case we break the loop when the trade session is closed
                break

        #Calculate gain loss
        gain_loss = bank_quote - self.BANK_QUOTE
        gain_loss_percentage = ((bank_quote - self.BANK_QUOTE) / self.BANK_QUOTE) * 100

        return gain_loss, gain_loss_percentage, nb_bought_order, nb_sold_order

    #endregion

    #region Utility methods
    def get_fees_of_trade(self, volume):
        return volume * self.FEES_RATE

    def plot_trading_visual(self, currency_pair_id):

        #Get y support and resistance from price history previous to the trading simulation
        df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(
            currency_pair_id,
            date_start=self.date_prior_start,
            date_end=self.date_start,
            granularity=self.granularity
        )
        y_support = df_product_historic_rates['close'].quantile(0.1)
        y_resistance = df_product_historic_rates['close'].quantile(0.9)

        #Get price history of the trading simulation
        df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(
            currency_pair_id,
            date_start=self.date_start,
            date_end=self.date_wait_until,
            granularity=self.granularity
        )

        #Add y support and y resistance
        df_product_historic_rates['y_support'] = y_support
        df_product_historic_rates['y_resistance'] = y_resistance

        #Plot the trading session
        ax = df_product_historic_rates[['close', 'y_support', 'y_resistance', 'datetime']].plot(x='datetime')
        ax.axvline(self.date_stop_active_trading, color="red", linestyle="dashed")
        plt.show()

    #endregion
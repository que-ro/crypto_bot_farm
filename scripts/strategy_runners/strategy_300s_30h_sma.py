from scripts.interfaces import StrategyRunnerInterface
from datetime import datetime, timedelta
from scripts.utilities.utils_df_product_historic_rates import UtilsDfProductHistoricRates
import matplotlib.pyplot as plt
import logging
from scripts.utilities.utils_logger import UtilitiesLogger
import math

class G300s30HSMAStrategyRunner(StrategyRunnerInterface):

    def __init__(self, granularity, df_products: object, log_lvl=logging.INFO):

        # init logger
        self.logger = UtilitiesLogger.get_logger(
            logger_name=G300s30HSMAStrategyRunner.get_name(),
            log_lvl=log_lvl
        )

        # if granularity = 300
        self.time_needed_for_process = timedelta(hours=30)

        #init granularity
        self.granularity = granularity

        #init products dataframe with their associated stats
        self.df_products = df_products

        #init value for the simulations
        self.FEES_RATE = 0.006
        self.BANK_QUOTE = 50
        self.VOLUME_PER_TRADE = 50

        # Log initisalization
        self.logger.info('strategy runner initialized with date_start : ' + self.date_start.isoformat())

    # region Interface implemented method
    @staticmethod
    def check_parameter(date_start: datetime, granularity: int) -> None:
        if (granularity == 300):
            raise ValueError('Only 300s intervals are supported at the moment')

    @staticmethod
    def time_needed_for_process(granularity):
        assert granularity == 300, 'Only 300s intervals are supported at the moment'

        # if granylarity = 300:
        return timedelta(hours=30)

    @staticmethod
    def get_name() -> str:
        return 'G300s30HSMAStrategy'

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
            date_start = datetime.fromisoformat(product['date_start_describer'])
            date_end = date_start + self.time_needed_for_process()

            self.logger.info('running strategy for ' + str(currency_pair_id))

            #Get price history dataframe
            df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(
                currency_pair_id,
                date_start,
                date_end,
                self.granularity
            )
            # Get simulation variables
            gain_loss, gain_loss_percentage, nb_bought_order, nb_sold_order = \
                self.simulate_tradings(
                    df_price=df_product_historic_rates
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

    def simulate_tradings(self, df_price):
        self.logger.debug('entering simulate_tradings(...)')

        #Get sma15 and sma3
        df_price['sma3'] = df_price['close'].rolling(3).mean()
        df_price['sma15'] = df_price['close'].rolling(15).mean()

        #Init variables
        bank_quote = self.BANK_QUOTE
        bank_base = 0
        last_tick_index = df_price.index[-1]
        nb_bought_order = 0
        nb_sold_order = 0
        is_there_an_order_bought = False
        previous_sma15 = None
        previous_sma3 = None


        for index, ticks in df_price.iterrows():

            if(math.isnan(ticks['sma15'])):
                continue

            #Init price variables
            price_low = ticks['low']
            price_high = ticks['high']
            close_price = ticks['close']
            sma15 = ticks['sma15']
            sma3 = ticks['sma3']
            is_bought_in_this_tick = False

            #Init previous sma
            if (previous_sma15 is None):
                previous_sma15 = sma15
                previous_sma3 = sma3
                continue



            #Buying section
            is_sma3_getting_over = (previous_sma3 <= previous_sma15) and (sma3 > sma15)
            if(is_there_an_order_bought == False and is_sma3_getting_over):

                #Update banks
                trade_volume = bank_quote
                bank_quote = bank_quote - trade_volume
                bank_base = (trade_volume - self.get_fees_of_trade(trade_volume)) / close_price

                #Save bought order
                is_there_an_order_bought = True
                is_bought_in_this_tick = True
                nb_bought_order += 1


            #Selling section
            is_sma3_getting_under = (previous_sma3 > previous_sma15) and (sma3 <= sma15)
            if(is_sma3_getting_under and is_there_an_order_bought and not is_bought_in_this_tick):

                #Update banks
                trade_volume = bank_base
                bank_base = bank_base - trade_volume
                bank_quote = (trade_volume - self.get_fees_of_trade(trade_volume)) * close_price

                #Update sold order
                is_there_an_order_bought = False
                nb_sold_order += 1


            #Closing trade section
            is_trading_closed = last_tick_index == index
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
        self.logger.debug('entering get_fees_of_trade(...)')
        return volume * self.FEES_RATE

    #endregion
from interfaces import ProductDescriberInterface
from utilities.utils_df_product_historic_rates import UtilsDfProductHistoricRates
from datetime import datetime, timedelta
import cbpro
import math
import pandas as pd
import logging

class BasicDescriber(ProductDescriberInterface):

    def __init__(self, date_start: datetime, granularity: int, quote_currency: str, log_lvl=logging.INFO):
        #if granularity = 300
        self.time_needed_for_process = timedelta(hours=15)
        self.date_start = date_start
        self.date_end = date_start + timedelta(hours=15)
        self.granularity = granularity
        self.quote_currency = quote_currency
        self.df_products_description = None

    #region Interface implemented method
    @staticmethod
    def check_parameter(date_start: datetime, granularity: int) -> None:
        if(granularity == 300):
            raise ValueError('Only 300s intervals are supported at the moment')
        if(date_start > datetime.now()):
            raise ValueError('The starting date must be anterior to now')

    @staticmethod
    def time_needed_for_process(granularity):
        assert granularity == 300, 'Only 300s intervals are supported at the moment'

        #if granylarity = 300:
        return timedelta(hours=15)

    @staticmethod
    def get_name() -> str:
        return 'BasicDescriber'

    """Return complete products dataframe with associated stats and parameters"""
    def get_df_product_with_description(self) -> object:

        public_client = cbpro.PublicClient()

        # list of currency pairs used
        list_currency_pairs = []            # [{'currency_pair_id', 'quote_increment'}]
        for product in public_client.get_products():
            if product['quote_currency'] == self.quote_currency:
                list_currency_pairs.append(
                    {'currency_pair_id': product['id'], 'quote_increment': float(product['quote_increment'])})

        # loop through all currency_pairs
        list_currency_pair_dict = []
        for currency_pair in list_currency_pairs:

            # init currency pair id
            currency_pair_id = currency_pair['currency_pair_id']

            # init coinbase pro public client
            product_historic_rates = public_client.get_product_historic_rates(currency_pair_id,
                                                                              start=self.date_start.isoformat(),
                                                                              end=self.date_end.isoformat(),
                                                                              granularity=self.granularity)

            # filter out product without any ticks
            nb_of_ticks = len(product_historic_rates)
            if (nb_of_ticks == 0):
                continue

            # get dataframe of product historic rates with moving average
            df_product_historic_rates = self.get_df_from_product_historic_rates(currency_pair_id)

            # get currency_pair_dict
            currency_pair_dict = self.get_currency_pair_stat_dict(currency_pair_id, df_product_historic_rates)

            # add quote_increment
            currency_pair_dict['quote_increment'] = currency_pair['quote_increment']

            # add to list
            list_currency_pair_dict.append(currency_pair_dict)

        self.df_products_description = pd.DataFrame(list_currency_pair_dict)
        return self.df_products_description

    #endregion

    #region Currency pair as dictionnary

    """For a currency pair, return stats of historic rates in a dictionnary"""
    def get_currency_pair_stat_dict(self, currency_pair_id, df_product_historic_rates):
        # init of dict with id
        currency_pair_stat_dict = {}
        currency_pair_stat_dict['currency_pair_id'] = currency_pair_id

        # get median, Q1, Q3, lowest, highest close price
        Q1 = df_product_historic_rates.describe().loc['25%', 'close']
        median = df_product_historic_rates.describe().loc['50%', 'close']
        Q3 = df_product_historic_rates.describe().loc['75%', 'close']
        lowest_price = df_product_historic_rates.describe().loc['min', 'close']
        highest_price = df_product_historic_rates.describe().loc['max', 'close']

        # add median, Q1, Q3, lowest, highst to currency pai
        currency_pair_stat_dict['Q1'] = Q1
        currency_pair_stat_dict['median'] = median
        currency_pair_stat_dict['Q3'] = Q3
        currency_pair_stat_dict['lowest_price'] = lowest_price
        currency_pair_stat_dict['highest_price'] = highest_price

        # calculate power ratio adn raw differences
        currency_pair_stat_dict['raw_diff_Q3Q1'] = Q3 - Q1
        currency_pair_stat_dict['raw_diff_highestlowest'] = highest_price - lowest_price
        self.update_power_ratio_for_currency_pair_dict(currency_pair_stat_dict, lowest_price, highest_price, Q1, median, Q3)

        # get trajectories stats as dataframe
        df_list_trajectories = self.get_trajectories_df(df_product_historic_rates)
        self.update_traj_stat_for_currency_pair_dict(currency_pair_stat_dict, df_list_trajectories)

        # get nb times Q1, median and Q3 crossed:
        self.update_nb_crossed_for_currency_pair_dict(currency_pair_stat_dict, df_product_historic_rates, Q1, median, Q3)

        return currency_pair_stat_dict

    #endregion

    #region Product historic rates

    def get_df_from_product_historic_rates(self, currency_pair_id):

        # get dataframe
        df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(
            currency_pair_id,
            date_start=self.date_start,
            date_end=self.date_end,
            granularity=self.granularity
        )

        # calculate simple moving average
        df_product_historic_rates['sma3'] = df_product_historic_rates['close'].rolling(3).mean()
        df_product_historic_rates['sma5'] = df_product_historic_rates['close'].rolling(5).mean()
        df_product_historic_rates['sma10'] = df_product_historic_rates['close'].rolling(10).mean()
        df_product_historic_rates['sma15'] = df_product_historic_rates['close'].rolling(15).mean()
        df_product_historic_rates['sma20'] = df_product_historic_rates['close'].rolling(20).mean()

        return df_product_historic_rates

    #endregion

    #region Description methods

    #region Trajectories description methods

    """Add stats abouth the trajectories of the past historic rate to a currency pair dict"""
    def update_traj_stat_for_currency_pair_dict(self, currency_pair_stat_dict, df_list_trajectories):

        # traj stat to add
        traj_stat_cols = ['nb_short_weak_decrease',
                          'nb_short_weak_increase',
                          'nb_short_strong_decrease',
                          'nb_short_strong_increase',
                          'nb_long_weak_decrease',
                          'nb_long_weak_increase',
                          'nb_long_strong_decrease',
                          'nb_long_strong_increase']

        # init stat
        for stat in traj_stat_cols:
            currency_pair_stat_dict[stat] = 0

        # update stat
        for traj_cat, value in df_list_trajectories['traj_cat'].value_counts().iteritems():
            currency_pair_stat_dict['nb_' + traj_cat] = value

    """Return a dataframe of the trajectories from a datafrale of historic rates"""
    def get_trajectories_df(self, df_product_historic_rates):
        # init lowest and highest sma3
        lowest_sma3 = df_product_historic_rates.describe().loc['min', 'sma3']
        highest_sma3 = df_product_historic_rates.describe().loc['max', 'sma3']

        # init list of trajectories and trajectory
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
            if (self.is_first_trajectory(trajectory, current_sma3)):
                trajectory = self.init_trajectory_dict(index, current_sma3)
                previous_sma3 = current_sma3

            # case start of a trajectory
            elif (self.is_start_of_a_trajectory(trajectory)):
                self.update_start_trajectory_variables(trajectory, current_sma3, previous_sma3)
                previous_sma3 = current_sma3

            # case end of trajectory
            elif (self.is_end_of_a_trajectory(trajectory, current_sma3, previous_sma3)):
                self.update_end_trajectory_variables(trajectory, index - 1, previous_sma3)
                list_trajectories.append(trajectory)
                trajectory = self.init_trajectory_dict(index, current_sma3)
                previous_sma3 = current_sma3

            # case continue of trajectory
            elif (self.is_continue_of_a_trajectory(trajectory)):
                trajectory['nb_ticks'] = trajectory['nb_ticks'] + 1
                previous_sma3 = current_sma3

        # close last trajectory
        if (trajectory is not None and trajectory['start_tick'] < index):
            self.update_end_trajectory_variables(trajectory, index, previous_sma3)
            list_trajectories.append(trajectory)

        return pd.DataFrame(list_trajectories)

    #region Update, Initialisation of one trajectory dictionnary

    """Return an initialized trajectory dictionnary with its characteristics"""
    def init_trajectory_dict(self, index_tick, current_sma3):
        trajectory = {'start_tick': index_tick,
                      'end_tick': None,
                      'start_price': current_sma3,
                      'end_price': None,
                      'nb_ticks': 1,
                      'coeff_dir_sense': None,
                      'coeff_dir': None,
                      'traj_cat': None}
        return trajectory

    """Update of the sense of the trajectory"""
    def update_start_trajectory_variables(self, trajectory, current_sma3, previous_sma3):
        trajectory['nb_ticks'] = trajectory['nb_ticks'] + 1
        diff_curr_prev_sma3 = current_sma3 - previous_sma3
        if (diff_curr_prev_sma3 < 0):
            trajectory['coeff_dir_sense'] = -1
        elif (diff_curr_prev_sma3 > 0):
            trajectory['coeff_dir_sense'] = 1

    """Update variables of trajectory when we got the start and the end of the said traj"""
    def update_end_trajectory_variables(self, trajectory, end_tick_index, previous_sma3):
        # set directional coefficient of the trajectory
        trajectory['end_tick'] = end_tick_index
        trajectory['end_price'] = previous_sma3
        trajectory['coeff_dir'] = (trajectory['end_price'] - trajectory['start_price']) / (
                    trajectory['end_tick'] - trajectory['start_tick'])

        # init trajectory category
        traj_category = ''

        # short/long
        if (trajectory['nb_ticks'] < 5):
            traj_category += 'short_'
        else:
            traj_category += 'long_'

        # weak/strong
        if (abs(trajectory['coeff_dir']) < 0.1):
            traj_category += 'weak_'
        else:
            traj_category += 'strong_'

        # decrease/increase
        if (trajectory['coeff_dir'] < 0):
            traj_category += 'decrease'
        else:
            traj_category += 'increase'

        # set trajectory category
        trajectory['traj_cat'] = traj_category

    #endregion

    #region Check trajectory status methods
    def is_first_trajectory(self, trajectory, current_sma3):
        return trajectory is None and math.isnan(current_sma3) == False

    def is_start_of_a_trajectory(self, trajectory):
        return trajectory is not None and trajectory['coeff_dir_sense'] is None

    def is_end_of_a_trajectory(self, trajectory, current_sma3, previous_sma3):
        return trajectory is not None and (current_sma3 * trajectory['coeff_dir_sense']) < (
                    previous_sma3 * trajectory['coeff_dir_sense'])

    def is_continue_of_a_trajectory(self, trajectory):
        return trajectory is not None

    #endregion

     #endregion

    #region  Power ratio description methods

    """Add stats about the power ratio of the past historic rate to a currency pair dict"""
    def update_power_ratio_for_currency_pair_dict(self, currency_pair_stat_dict, lowest_price, highest_price, Q1, median, Q3):

        # init power ratio
        power_ratio_highestlowest = None
        power_ratio_Q3Q1 = None

        # power ratio highest lowest
        diff_abs_highest_median = abs(highest_price - median)
        diff_abs_lowest_median = abs(lowest_price - median)

        if (diff_abs_highest_median == 0 and diff_abs_lowest_median == 0):
            power_ratio_highestlowest = 0
        elif (diff_abs_highest_median == 0):
            power_ratio_highestlowest = -2
        elif (diff_abs_lowest_median == 0):
            power_ratio_highestlowest = 2
        else:
            power_ratio_highestlowest = math.log10(abs(diff_abs_highest_median) / abs(diff_abs_lowest_median))

        # power ratio Q3 Q1
        diff_abs_Q3_median = abs(Q3 - median)
        diff_abs_Q1_median = abs(Q1 - median)

        if (diff_abs_Q3_median == 0 and diff_abs_Q1_median == 0):
            power_ratio_Q3Q1 = 0
        elif (diff_abs_Q3_median == 0):
            power_ratio_Q3Q1 = -2
        elif (diff_abs_Q1_median == 0):
            power_ratio_Q3Q1 = 2
        else:
            power_ratio_Q3Q1 = math.log10(abs(diff_abs_Q3_median) / abs(diff_abs_Q1_median))

        # update currency_pair_stat_dict
        currency_pair_stat_dict['power_ratio_Q3Q1'] = power_ratio_Q3Q1
        currency_pair_stat_dict['power_ratio_highestlowest'] = power_ratio_highestlowest

    #endregion

    #region Number times crossed description methods

    """Add stats about nb times historic rates crossed Q1, median and Q3 to the currency pair dict"""
    def update_nb_crossed_for_currency_pair_dict(self, currency_pair_stat_dict, df_product_historic_rates, Q1, median, Q3):
        # init nb of times crossed
        nb_Q1_was_crossed = 0
        nb_median_was_crossed = 0
        nb_Q3_was_crossed = 0

        # loop through ticks
        for index, row in df_product_historic_rates.iterrows():
            start_price = row['open']
            close_price = row['close']

            if ((start_price >= median > close_price) or (close_price >= median > start_price)):
                nb_median_was_crossed += 1
            elif ((start_price >= Q3 > close_price) or (close_price >= Q3 > start_price)):
                nb_Q3_was_crossed += 1
            elif ((start_price >= Q1 > close_price) or (close_price >= Q1 > start_price)):
                nb_Q1_was_crossed += 1

        # set value for currency_pair_stat_dict
        currency_pair_stat_dict['nb_Q1_was_crossed'] = nb_Q1_was_crossed
        currency_pair_stat_dict['nb_median_was_crossed'] = nb_median_was_crossed
        currency_pair_stat_dict['nb_Q3_was_crossed'] = nb_Q3_was_crossed
    #endregion

    #endregion
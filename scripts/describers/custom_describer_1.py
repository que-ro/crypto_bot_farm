from interfaces import ProductDescriberInterface
from utils_df_product_historic_rates import UtilsDfProductHistoricRates
from datetime import datetime, timedelta
import cbpro
import math
import pandas as pd
import ta

class CustomDescriber1(ProductDescriberInterface):

    def __init__(self, date_start: datetime, granularity: int, quote_currency: str):
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
        if (granularity == 300):
            raise ValueError('Only 300s intervals are supported at the moment')
        if (date_start > datetime.now()):
            raise ValueError('The starting date must be anterior to now')

    @staticmethod
    def time_needed_for_process(granularity):
        assert granularity == 300, 'Only 300s intervals are supported at the moment'

        # if granylarity = 300:
        return timedelta(hours=15)

    @staticmethod
    def get_name() -> str:
        return 'CustomDescriber1'

    """Return complete products dataframe with associated stats and parameters"""
    def get_df_product_with_description(self) -> object:

        public_client = cbpro.PublicClient()

        # list of currency pairs used
        list_currency_pairs = []  # [{'currency_pair_id', 'quote_increment'}]
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
            df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(
                currency_pair_id,
                date_start=self.date_start,
                date_end=self.date_end,
                granularity=self.granularity
            )

            # get currency_pair_dict
            currency_pair_dict = self.get_currency_pair_stat_dict(currency_pair_id, df_product_historic_rates)

            # add quote_increment
            currency_pair_dict['quote_increment'] = currency_pair['quote_increment']

            # add to list
            list_currency_pair_dict.append(currency_pair_dict)

        self.df_products_description = pd.DataFrame(list_currency_pair_dict)
        return self.df_products_description

    #endregion

    #region Currency pair Methods

    def get_currency_pair_stat_dict(self, currency_pair_id, df_product_historic_rates):
        # init of dict with id
        currency_pair_stat_dict = {}
        currency_pair_stat_dict['currency_pair_id'] = currency_pair_id

        # get median, Q1, Q3, lowest, highest close price
        Q1 = df_product_historic_rates.describe().loc['25%', 'close']
        Q3 = df_product_historic_rates.describe().loc['75%', 'close']
        median = df_product_historic_rates.describe().loc['50%', 'close']
        lowest_price = df_product_historic_rates.describe().loc['min', 'close']
        highest_price = df_product_historic_rates.describe().loc['max', 'close']

        # Add power ratio with same as basic describer
        self.update_power_ratio_for_currency_pair_dict(
            currency_pair_stat_dict=currency_pair_stat_dict,
            lowest_price=lowest_price,
            highest_price=highest_price,
            Q1=Q1,
            median=median,
            Q3=Q3
        )

        # Update sma analysis
        self.update_sma_analysis(currency_pair_stat_dict, df_product_historic_rates)

        # Update awesome oscillator analysis
        self.update_awesome_oscillator_analysis(currency_pair_stat_dict, df_product_historic_rates)

        # Update chaikin_money_flo analysis
        self.update_chaikin_money_flow_analysis(currency_pair_stat_dict, df_product_historic_rates)

        # Update aroon analysis
        self.update_aroon_analysis(currency_pair_stat_dict, df_product_historic_rates)

        # Update bollinger_pct_bands analysis
        self.update_bollinger_pct_bands(currency_pair_stat_dict, df_product_historic_rates)

        # Update global_trending_with_sma15 analysis
        self.update_global_trending_with_sma15(currency_pair_stat_dict, df_product_historic_rates)

        # Update trajectories analysis
        df_list_trajectories = self.get_trajectories_df(df_product_historic_rates)
        self.update_traj_stat_for_currency_pair_dict(currency_pair_stat_dict, df_list_trajectories)

        return currency_pair_stat_dict

    #endregion

    # region Trajectories description methods

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
        df_product_historic_rates['sma3'] = df_product_historic_rates['close'].rolling(3).mean()
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

    # region Update, Initialisation of one trajectory dictionnary

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

    # endregion

    # region Check trajectory status methods
    def is_first_trajectory(self, trajectory, current_sma3):
        return trajectory is None and math.isnan(current_sma3) == False

    def is_start_of_a_trajectory(self, trajectory):
        return trajectory is not None and trajectory['coeff_dir_sense'] is None

    def is_end_of_a_trajectory(self, trajectory, current_sma3, previous_sma3):
        return trajectory is not None and (current_sma3 * trajectory['coeff_dir_sense']) < (
                previous_sma3 * trajectory['coeff_dir_sense'])

    def is_continue_of_a_trajectory(self, trajectory):
        return trajectory is not None

    # endregion

    # endregion

    # region  Power ratio description methods

    """Add stats about the power ratio of the past historic rate to a currency pair dict"""
    def update_power_ratio_for_currency_pair_dict(self, currency_pair_stat_dict, lowest_price, highest_price, Q1,
                                                  median, Q3):

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

    # endregion

    #region Technical analysis

    def update_sma_analysis(self, currency_pair_stat_dict, df_product_historic_rates):

        # Add SMA5 and SMA15
        df_product_historic_rates['sma5'] = df_product_historic_rates['close'].rolling(5).mean()
        df_product_historic_rates['sma15'] = df_product_historic_rates['close'].rolling(15).mean()

        # Get nb crossover and pct
        pct_sma15_sma5_crossover, pct_sma15_over_sma5, pct_sma15_under_sma5 = self.get_pct_crossover_and_pct_factor1_overunder(
            'sma5', 'sma15', df_product_historic_rates)

        # Update currency pair stat
        currency_pair_stat_dict['pct_sma15_sma5_crossover'] = pct_sma15_sma5_crossover
        currency_pair_stat_dict['pct_sma15_over_sma5'] = pct_sma15_over_sma5
        currency_pair_stat_dict['pct_sma15_under_sma5'] = pct_sma15_under_sma5

    def update_awesome_oscillator_analysis(self, currency_pair_stat_dict, df_product_historic_rates):

        # Init a col y = 0
        df_product_historic_rates['zero'] = 0

        # Add awesome oscillator indicator to df
        df_product_historic_rates['awesome_oscillator'] = ta.momentum.AwesomeOscillatorIndicator(
            high=df_product_historic_rates['high'],
            low=df_product_historic_rates['low'],
            window1=5,
            window2=15).awesome_oscillator()

        # Get nb crossover and pct
        pct_crossover_ao_zero, pct_ao_over_zero, pct_ao_under_zero = self.get_pct_crossover_and_pct_factor1_overunder(
            'awesome_oscillator', 'zero', df_product_historic_rates)

        # Update currency pair stat
        currency_pair_stat_dict['pct_crossover_ao_zero'] = pct_crossover_ao_zero
        currency_pair_stat_dict['pct_ao_over_zero'] = pct_ao_over_zero
        currency_pair_stat_dict['pct_ao_under_zero'] = pct_ao_under_zero

    def update_chaikin_money_flow_analysis(self, currency_pair_stat_dict, df_product_historic_rates):

        # Init a col y = 0
        df_product_historic_rates['zero'] = 0

        # Add chaikin_money_flow indicator
        df_product_historic_rates['chaikin_money_flow'] = ta.volume.ChaikinMoneyFlowIndicator(
            high=df_product_historic_rates['high'],
            low=df_product_historic_rates['low'],
            close=df_product_historic_rates['close'],
            volume=df_product_historic_rates['close'],
            window=15).chaikin_money_flow()

        # Get nb crossover and pct
        pct_crossover_cmf_zero, pct_cmf_over_zero, pct_cmf_under_zero = self.get_pct_crossover_and_pct_factor1_overunder(
            'chaikin_money_flow', 'zero', df_product_historic_rates)

        # Update currency pair stat
        currency_pair_stat_dict['pct_crossover_cmf_zero'] = pct_crossover_cmf_zero
        currency_pair_stat_dict['pct_cmf_over_zero'] = pct_cmf_over_zero
        currency_pair_stat_dict['pct_cmf_under_zero'] = pct_cmf_under_zero

    def update_aroon_analysis(self, currency_pair_stat_dict, df_product_historic_rates):

        # Get aroon up
        df_product_historic_rates['aroon_up'] = ta.trend.AroonIndicator(close=df_product_historic_rates['close'],
                                                                        window=15).aroon_up()

        # Get aroon down
        df_product_historic_rates['aroon_down'] = ta.trend.AroonIndicator(close=df_product_historic_rates['close'],
                                                                          window=15).aroon_down()

        # Get nb crossover and pct
        pct_crossover_aroonup_aroondown, pct_aroonup_over_aroondown, pct_aroonup_under_aroondown = self.get_pct_crossover_and_pct_factor1_overunder(
            'aroon_up', 'aroon_down', df_product_historic_rates)

        # Update currency pair stat
        currency_pair_stat_dict['pct_crossover_aroonup_aroondown'] = pct_crossover_aroonup_aroondown
        currency_pair_stat_dict['pct_aroonup_over_aroondown'] = pct_aroonup_over_aroondown
        currency_pair_stat_dict['pct_aroonup_under_aroondown'] = pct_aroonup_under_aroondown

    def get_pct_crossover_and_pct_factor1_overunder(self, factor_one, factor_two, df_product_historic_rates):
        # returned value
        pct_crossover = 0
        pct_factor1_over = 0
        pct_factor1_under = 0

        # skip the first lines which don't have value for factor one or two
        skip_nb_lines_f1 = df_product_historic_rates[df_product_historic_rates[factor_one].isna()].shape[0]
        skip_nb_lines_f2 = df_product_historic_rates[df_product_historic_rates[factor_two].isna()].shape[0]
        skip_nb_lines = skip_nb_lines_f1 if skip_nb_lines_f1 > skip_nb_lines_f2 else skip_nb_lines_f2

        # get trimmed df of first lines
        df = df_product_historic_rates[skip_nb_lines:]

        previous_is_factor1_sup_to_factor2 = None
        nb_ticks_tot = 0
        nb_ticks_f1_sup = 0
        nb_crossover = 0
        for index, row in df_product_historic_rates.iterrows():
            # increment nb ticks tot
            nb_ticks_tot += 1

            # is factor one sup to factor two
            is_factor1_sup_to_factor2 = row[factor_one] > row[factor_two]

            # if f1 sup, increment nb_ticks_f1_sup
            if (is_factor1_sup_to_factor2):
                nb_ticks_f1_sup += 1

            # case first row and previous bool isn't yet initialized
            if (previous_is_factor1_sup_to_factor2 == None):
                previous_is_factor1_sup_to_factor2 = is_factor1_sup_to_factor2
                continue

            # check  if the two factors have crossed
            if (is_factor1_sup_to_factor2 != previous_is_factor1_sup_to_factor2):
                nb_crossover += 1

            previous_is_factor1_sup_to_factor2 = is_factor1_sup_to_factor2

        # Calculate pct
        pct_factor1_over = nb_ticks_f1_sup / nb_ticks_tot
        pct_factor1_under = 1 - pct_factor1_over
        pct_crossover = nb_crossover / nb_ticks_tot

        return pct_crossover, pct_factor1_over, pct_factor1_under

    def update_bollinger_pct_bands(self, currency_pair_stat_dict, df_product_historic_rates):

        # Add Bollinger pct bands
        df_product_historic_rates['bollinger_pct_bands'] = ta.volatility.BollingerBands(
            close=df_product_historic_rates['close'],
            window=15).bollinger_pband()

        # Skip first empty lines
        skip_nb_lines = df_product_historic_rates[df_product_historic_rates['bollinger_pct_bands'].isna()].shape[0]
        df = df_product_historic_rates[skip_nb_lines:]

        # Initialisation
        nb_overbought_signal = 0
        nb_oversold_signal = 0
        nb_ticks = 0

        # Through bollinger pct bands indicator
        for index, row in df.iterrows():

            if (row['bollinger_pct_bands'] > 1):
                nb_overbought_signal += 1

            if (row['bollinger_pct_bands'] < 0):
                nb_oversold_signal += 1

            nb_ticks += 1

        pct_overbought_signal = nb_overbought_signal / nb_ticks
        pct_oversold_signal = nb_oversold_signal / nb_ticks

        # Update stat of currency pair
        currency_pair_stat_dict['pct_overbought_signal'] = pct_overbought_signal
        currency_pair_stat_dict['pct_oversold_signal'] = pct_oversold_signal

    def update_global_trending_with_sma15(self, currency_pair_stat_dict, df_product_historic_rates):

        # Get sma15
        df_product_historic_rates['sma15'] = df_product_historic_rates['close'].rolling(15).mean()

        # Get sma start and end
        first_notna_value = df_product_historic_rates[df_product_historic_rates['sma15'].isna()].shape[0]
        sma_start = df_product_historic_rates.iloc[first_notna_value]['sma15']
        sma_end = df_product_historic_rates.iloc[-1]['sma15']

        # Calculate pct increase or decrease of price
        pct_global_sma15_trend = (sma_end - sma_start) / sma_start

        # Update stat of currency pair
        currency_pair_stat_dict['pct_global_sma15_trend'] = pct_global_sma15_trend

    #endregion
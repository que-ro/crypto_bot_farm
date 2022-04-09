import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 300

from datetime import datetime, timedelta
from describers.basic_describer import BasicDescriber
from strategy_runners.basic_strategy import BasicStrategyRunner
from basic_result_labeller import BasicResultLabeller
from data_accumulator import DataAccumulator

data_acc = DataAccumulator(
    describer_class=BasicDescriber,
    strategy_runner_class=BasicStrategyRunner,
    result_labeller_class=BasicResultLabeller,
    granularity=300,
    quote_currency='EUR',
    nb_of_process=5
)

data_acc.accumulate_data_for_X_nb_of_process()

data_acc2 = DataAccumulator(
    describer_class=BasicDescriber,
    strategy_runner_class=BasicStrategyRunner,
    result_labeller_class=BasicResultLabeller,
    granularity=300,
    quote_currency='USD',
    nb_of_process=5
)

data_acc2.accumulate_data_for_X_nb_of_process()

data_acc3 = DataAccumulator(
    describer_class=BasicDescriber,
    strategy_runner_class=BasicStrategyRunner,
    result_labeller_class=BasicResultLabeller,
    granularity=300,
    quote_currency='GBP',
    nb_of_process=5
)

data_acc3.accumulate_data_for_X_nb_of_process()



from utils_df_product_historic_rates import UtilsDfProductHistoricRates

date_test = datetime(2022, 3, 11, 17, 2, 45, 679691)
date_test_end = date_test + timedelta(hours=15)
df_test = UtilsDfProductHistoricRates.get_df_price_history('MANA-USD', date_test, date_test_end, 300)






####### SCORE TABLE ########
# All params from describer :
#       Accuracy: 0.8648648648648649
# Without ['raw_diff_highestlowest', 'raw_diff_Q3Q1', 'Q1', 'lowest_price', 'median', 'highest_price', 'Q3', 'quote_increment']
#       Accuracy: 0.8648648648648649
# Without ['raw_diff_highestlowest', 'raw_diff_Q3Q1', 'Q1', 'lowest_price', 'median', 'highest_price', 'Q3', 'quote_increment'
#             ,'power_ratio_highestlowest', 'power_ratio_Q3Q1']


#Filter features not used (from strat runner or labeller)
#Feature selection with random forest


from utils_df_product_historic_rates import UtilsDfProductHistoricRates
import ta
from describers.custom_describer_1 import CustomDescriber1
from datetime import datetime, timedelta
date_now = datetime.now()
date_start = date_now - timedelta(hours=60)

describer = CustomDescriber1(date_start=date_start, granularity=300, quote_currency='USD')

currency_pair_id = 'MANA-USD'
date_start = date_now - timedelta(hours=60)
date_end = date_start + timedelta(hours=15)
granularity=300

product_historic_rates = public_client.get_product_historic_rates(currency_pair_id,
                                                                              start=date_start.isoformat(),
                                                                              end=date_end.isoformat(),
                                                                              granularity=granularity)
from utils_df_product_historic_rates import UtilsDfProductHistoricRates
df_product_historic_rates = UtilsDfProductHistoricRates.get_df_price_history(
                currency_pair_id,
                date_start=date_start,
                date_end=date_end,
                granularity=granularity
            )






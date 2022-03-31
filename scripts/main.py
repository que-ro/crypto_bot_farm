import cbpro
from datetime import datetime, timedelta
import pandas as pd
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 300
import matplotlib.pyplot as plt
import math
import numpy as np


from datetime import datetime, timedelta
from basic_describer import BasicDescriber
from basic_strategy import BasicStrategyRunner
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


#Read data from tsv file
#Separate features and label
#Filter features not used (from strat runner or labeller)
#Feature selection with random forest

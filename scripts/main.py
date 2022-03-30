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

date_start = datetime.now() - timedelta(hours=61)
granularity = 300
quote_currency = 'EUR'

describer = BasicDescriber(date_start, granularity, quote_currency)
describer.get_df_product_with_description()

from basic_strategy import BasicStrategyRunner

strategy_runner = BasicStrategyRunner(date_start + timedelta(hours=15), date_start, granularity, describer.df_products_description)
strategy_runner.get_df_product_with_strat_result()


# import importlib, sys
# importlib.reload(sys.modules['data_accumulator'])

from scripts.describers.describer_300s_60h import Granularity300s60HDescriber
from scripts.strategy_runners.strategy_300s_30h_sma import G300s30HSMAStrategyRunner
from scripts.strategy_labellers.custom_labeller_1 import CustomLabeller1
from scripts.data_accumulator.data_accumulator_v2 import DataAccumulatorV2

data_acc = DataAccumulatorV2(
    describer_class=Granularity300s60HDescriber,
    strategy_runner_class=G300s30HSMAStrategyRunner,
    result_labeller_class=CustomLabeller1,
    granularity=300
)

data_acc.accumulate_data_for_X_nb_of_process()

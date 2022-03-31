from datetime import datetime
import pandas as pd

class ProductDescriberInterface:

    @staticmethod
    def check_parameter(date_start: datetime, granularity: int) -> None:
        """Assert if entry parameters are viable with the process"""
        pass

    def get_df_product_with_description(self) -> object:
        """Return dataframe of products with stats descriptions for each product"""
        pass

    @staticmethod
    def time_needed_for_process(granularity):
        """Return timedelta with nb of hours needed for the process of description"""
        pass

    @staticmethod
    def get_name() -> str:
        """Return the name of the describer"""
        pass


class StrategyRunnerInterface:

    @staticmethod
    def check_parameter(date_start: datetime, granularity: int) -> None:
        """Assert if entry parameters are viable with the process"""
        pass

    def get_df_product_with_strat_result(self) -> object:
        """Return dataframe of products with results of the strategy"""
        pass

    @staticmethod
    def time_needed_for_process(granularity):
        """Return timedelta with nb of hours needed for the process of running the trading simulation"""
        pass

    @staticmethod
    def get_name() -> str:
        """Return the name of the strategy runner"""
        pass


class StrategyResultLabellerInterface:

    @staticmethod
    def get_df_product_with_strat_result_label(self) -> object:
        """Return dataframe of products with label column ("result_label") containing 0 or 1
        which describe the success of the strategy"""
        pass

    @staticmethod
    def get_name() -> str:
        """Return the name of the labeller"""
        pass
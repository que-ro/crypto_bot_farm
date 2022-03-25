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


class StrategyRunnerInterface:

    @staticmethod
    def check_parameter(date_start: datetime, granularity: int) -> None:
        """Assert if entry parameters are viable with the process"""
        pass

    def get_df_product_with_strat_result(self) -> object:
        """Return dataframe of products with results of the strategy"""
        pass
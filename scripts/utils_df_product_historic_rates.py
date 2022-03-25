from datetime import datetime, timedelta
import cbpro
import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd

class UtilsDfProductHistoricRates:

    """Return dataframe from array of product historic rates from cbpro"""
    @staticmethod
    def get_df_from_product_historic_rates(product_historic_rates, date_start, date_end, granularity):
        df_product_historic_rates = pd.DataFrame(product_historic_rates)
        df_product_historic_rates.set_axis(['time', 'low', 'high', 'open', 'close', 'volume'], axis=1, inplace=True)
        df_product_historic_rates.sort_values(by=['time'], inplace=True)
        df_product_historic_rates.reset_index(inplace=True)
        df_product_historic_rates.drop(['index'], axis=1, inplace=True)
        df_product_historic_rates = UtilsDfProductHistoricRates.fill_df_historicrates_with_missing_timestamp(
            df_product_historic_rates,
            date_start,
            date_end,
            granularity)
        df_product_historic_rates['datetime'] = df_product_historic_rates.apply(
            lambda row: datetime.fromtimestamp(row['time']), axis=1)
        return df_product_historic_rates

    """Fill product historic rates dataframes with missing timestamp ticks"""
    @staticmethod
    def fill_df_historicrates_with_missing_timestamp(df_product_historic_rates, date_start, date_end, granularity):

        # get starting and ending timestamp
        start_timestamp, end_timestamp = UtilsDfProductHistoricRates.get_start_end_timestamp_of_api(
            date_start,
            date_end,
            granularity)

        # set index
        df_product_historic_rates.set_index('time', inplace=True)

        # add missing rows
        complete_timestamp_index = np.arange(start_timestamp, end_timestamp, 300)
        df_product_historic_rates = df_product_historic_rates.reindex(complete_timestamp_index, fill_value=-1)

        # get first row with values
        first_filled_row = None
        for timestamp_index, row in df_product_historic_rates.iterrows():
            first_filled_row = row
            if (row['low'] != -1):
                break

        # fill the first empty rows
        for timestamp_index, row in df_product_historic_rates.iterrows():
            if (row['low'] != -1):
                break
            df_product_historic_rates.loc[timestamp_index, 'low'] = first_filled_row['open']
            df_product_historic_rates.loc[timestamp_index, 'high'] = first_filled_row['open']
            df_product_historic_rates.loc[timestamp_index, 'open'] = first_filled_row['open']
            df_product_historic_rates.loc[timestamp_index, 'close'] = first_filled_row['open']
            df_product_historic_rates.loc[timestamp_index, 'volume'] = 0

        # fill empty rows after a first filled row
        previous_timestamp = -1
        for timestamp_index, row in df_product_historic_rates.iterrows():

            if (row['low'] == -1):
                df_product_historic_rates.loc[timestamp_index, 'low'] = df_product_historic_rates.loc[
                    previous_timestamp, 'close']
                df_product_historic_rates.loc[timestamp_index, 'high'] = df_product_historic_rates.loc[
                    previous_timestamp, 'close']
                df_product_historic_rates.loc[timestamp_index, 'open'] = df_product_historic_rates.loc[
                    previous_timestamp, 'close']
                df_product_historic_rates.loc[timestamp_index, 'close'] = df_product_historic_rates.loc[
                    previous_timestamp, 'close']
                df_product_historic_rates.loc[timestamp_index, 'volume'] = 0

            previous_timestamp = timestamp_index

        # reset index
        return df_product_historic_rates.reset_index()

    """Return start and end timestamp as the cbpro will return"""
    @staticmethod
    def get_start_end_timestamp_of_api(date_start, date_end, granularity):
        # Check if we are with a 5minutes interval
        assert (granularity == 300), "Only 300s granularity implemented at the moment"

        # Set seconds, microseconds to 0
        date_start = date_start.replace(second=0, microsecond=0)
        date_end = date_end.replace(second=0, microsecond=0)

        # Calculate minutes to add and substract
        minutes_to_substract_to_end_date = date_start.minute % 5
        minutes_to_add_to_start_date = 5 - minutes_to_substract_to_end_date

        # Get api start and ending timestamp
        api_start_timestamp = (date_start + timedelta(hours=1, minutes=minutes_to_add_to_start_date)).timestamp()
        api_end_timestamp = (date_end + timedelta(minutes=60 - minutes_to_substract_to_end_date)).timestamp()

        return api_start_timestamp, api_end_timestamp
from datetime import datetime, timedelta, timezone
import cbpro
import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd

class UtilsDfProductHistoricRates:

    @staticmethod
    def get_df_price_history(currency_pair_id, date_start, date_end, granularity):

        assert granularity==300, "At the moment only a granularity of 300s is implemented"

        #init cbpro api client
        public_client = cbpro.PublicClient()

        #init dataframe of price history
        df_price_history =None

        #get nb of hours between date
        hours_btwn_dates = (date_end - date_start).total_seconds() / 3600

        #get nb of times the loop should be called
        nb_times_loop = math.floor(hours_btwn_dates / 15)

        #loop 15h by 15h (get 180 ticks per 180 ticks) (max 200 ticks can be retrieved per call of the api)
        for idx in range (0, nb_times_loop):
            date1 = date_start + timedelta(hours=15 * idx)
            date2 = date_start + timedelta(hours=15 * (idx + 1))

            list_price_history = public_client.get_product_historic_rates(product_id=currency_pair_id,
                                                     start=date1.isoformat(),
                                                     end=date2.isoformat(),
                                                     granularity=granularity)

            if(df_price_history is None):
                df_price_history = UtilsDfProductHistoricRates.get_df_from_product_historic_rates(list_price_history, date1, date2, granularity)
            else:
                df_price_history = pd.concat([
                    df_price_history,
                    UtilsDfProductHistoricRates.get_df_from_product_historic_rates(
                        list_price_history, date1, date2, granularity)
                ])

        #get last ticks
        hours_not_yet_retrieved = hours_btwn_dates % 15
        if(hours_not_yet_retrieved != 0):
            date1 = date_end - timedelta(hours=hours_not_yet_retrieved)
            date2 = date_end
            list_price_history = public_client.get_product_historic_rates(product_id=currency_pair_id,
                                                                               start=date1,
                                                                               end=date2,
                                                                               granularity=granularity)
            df_price_history = pd.concat([
                df_price_history,
                UtilsDfProductHistoricRates.get_df_from_product_historic_rates(
                    list_price_history, date1, date2, granularity)
            ])

        #fill all missing timestamps
        df_price_history = UtilsDfProductHistoricRates.fill_df_historicrates_with_missing_timestamp(
            df_price_history,
            date_start,
            date_end,
            granularity)
        df_price_history['datetime'] = df_price_history.apply(
            lambda row: datetime.utcfromtimestamp(row['time']), axis=1)

        #get rid of biased index
        df_price_history = df_price_history.reset_index()
        df_price_history = df_price_history.drop('index', axis=1)

        #return complete dataframe
        return df_price_history





    """Return dataframe from array of product historic rates from cbpro"""
    @staticmethod
    def get_df_from_product_historic_rates(product_historic_rates, date_start, date_end, granularity):

        #Get dataframe
        if(len(product_historic_rates) == 0):
            df_product_historic_rates = pd.DataFrame(pd.np.empty((0, 6)))
        else:
            df_product_historic_rates = pd.DataFrame(product_historic_rates)

        df_product_historic_rates.set_axis(['time', 'low', 'high', 'open', 'close', 'volume'], axis=1, inplace=True)
        df_product_historic_rates.sort_values(by=['time'], inplace=True)
        df_product_historic_rates.reset_index(inplace=True)
        df_product_historic_rates.drop(['index'], axis=1, inplace=True)

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
        api_start_timestamp = (date_start + timedelta(minutes=minutes_to_add_to_start_date)).replace(tzinfo=timezone.utc).timestamp()
        api_end_timestamp = (date_end - timedelta(minutes=minutes_to_substract_to_end_date)).replace(tzinfo=timezone.utc).timestamp()

        return api_start_timestamp, api_end_timestamp
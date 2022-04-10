import importlib, sys
importlib.reload(sys.modules['data_accumulator'])
from data_accumulator import DataAccumulator
from describers.custom_describer_1 import CustomDescriber1
from strategy_runners.custom_strategy_1 import CustomStrategy1Runner
from strategy_labellers.custom_labeller_1 import CustomLabeller1
import logging


data_acc = DataAccumulator(
    describer_class=CustomDescriber1,
    strategy_runner_class=CustomStrategy1Runner,
    result_labeller_class=CustomLabeller1,
    granularity=300,
    quote_currency='EUR',
    nb_of_process=20,
    save_describer_df=True,
    log_lvl_describer=logging.DEBUG
)

data_acc.accumulate_data_for_X_nb_of_process()





#### Todelete zone

# from datetime import datetime, timedelta
# from utilities.utils_df_product_historic_rates import UtilsDfProductHistoricRates
#
# date_start = datetime.fromisoformat('2022-02-25T07:18:11.948516')
# date_end = date_start + timedelta(hours=45)
# currency_pair_id = 'DIA-EUR'
# granularity = 300
#
# df = UtilsDfProductHistoricRates.get_df_price_history(
#     date_start=date_start,
#     date_end=date_end,
#     granularity=granularity,
#     currency_pair_id=currency_pair_id
# )


#
# import cbpro
# public_client = cbpro.PublicClient()
# product_historic_rates = public_client.get_product_historic_rates(currency_pair_id,
#                                                                               start=date_start.isoformat(),
#                                                                               end=date_end.isoformat(),
#                                                                               granularity=granularity)
#

#
# from datetime import datetime, timedelta, timezone
#
# date_utc_now = datetime.utcnow()
# date_utc_start = date_utc_now - timedelta(hours=15)
# date_utc_end = date_utc_start + timedelta(hours=15)
#
# date_now = datetime.now()
# date_start = date_now - timedelta(hours=15)
# date_end = date_start + timedelta(hours=15)
#
# currency_pair_id = 'ETH-USD'
# granularity=300
#
# import cbpro
# public_client = cbpro.PublicClient()
#
# prod = public_client.get_product_historic_rates(currency_pair_id,
#                                                                               start=date_start.isoformat(),
#                                                                               end=date_end.isoformat(),
#                                                                               granularity=granularity)
#
# prod_utc = public_client.get_product_historic_rates(currency_pair_id,
#                                                                               start=date_utc_start.isoformat(),
#                                                                               end=date_utc_end.isoformat(),
#                                                                               granularity=granularity)
#
#
#
# date_start_iso = date_utc_now.replace(tzinfo=timezone.utc).isoformat()
# date_end_iso = date_utc_end.replace(tzinfo=timezone.utc).isoformat()
#
#
# prod_iso = public_client.get_product_historic_rates(currency_pair_id,
#                                                                               start=date_start_iso,
#                                                                               end=date_end_iso,
#                                                                               granularity=granularity)
#
#
#
# utc_date_start = datetime.utcnow() - timedelta(hours=60)
# utc_date_end = utc_date_start + timedelta(hours=15)
# currency_pair_id = 'ETH-USD'
# granularity=300
# utc_prods = public_client.get_product_historic_rates(currency_pair_id,
#                                                                               start=utc_date_start.isoformat(),
#                                                                               end=utc_date_end.isoformat(),
#                                                                               granularity=granularity)
#
# utc_date_start_from_cbpro = datetime.fromtimestamp(utc_prods[-1][0])
# utc_date_end_from_cbpro = datetime.fromtimestamp(utc_prods[0][0])
#
#
# date_utc_now =
#
#
#
# from datetime import datetime, timedelta, timezone
# import cbpro
#
# granularity=300
# currency_pair_id='BTC-USD'
#
# utc_date_now = datetime.utcnow()
# nor_date_now = datetime.now()
#
# utc_date_start = utc_date_now - timedelta(hours=60)
# utc_date_end = utc_date_start + timedelta(hours=15)
#
# nor_date_start = nor_date_now - timedelta(hours=60)
# nor_date_end =  nor_date_start + timedelta(hours=15)
#
# public_client = cbpro.PublicClient()
#
# utc_prods = public_client.get_product_historic_rates(
#     currency_pair_id,
#     start=utc_date_start.isoformat(),
#     end=utc_date_end.isoformat(),
#     granularity=granularity,
# )
#
# nor_prods = public_client.get_product_historic_rates(
#     currency_pair_id,
#     start=nor_date_start.isoformat(),
#     end=nor_date_end.isoformat(),
#     granularity=granularity,
# )
#
# utc_date_cbpro_start_ts = datetime.fromtimestamp(utc_prods[-1][0])
# utc_date_cbpro_end_ts = datetime.fromtimestamp(utc_prods[0][0])
#
# nor_date_cbpro_start_ts = datetime.fromtimestamp(nor_prods[-1][0])
# nor_date_cbpro_end_ts = datetime.fromtimestamp(nor_prods[0][0])
#
# import time
# utc_date_cbpro_start_
#
#
#
#
# from datetime import datetime, timedelta, timezone
# import time
# from time import mktime
# import cbpro
#
# public_client = cbpro.PublicClient()
#
# granularity=300
# currency_pair_id='BTC-USD'
# date_now = datetime.now()
# date_start = date_now - timedelta(hours=60)
# date_end = date_start + timedelta(hours=15)
#
# prods = public_client.get_product_historic_rates(
#     currency_pair_id,
#     start=date_start.isoformat(),
#     end=date_end.isoformat(),
#     granularity=granularity,
# )
#
# date_start_api = datetime.fromtimestamp(mktime(time.gmtime(prods[-1][0])))
# date_end_api = datetime.fromtimestamp(mktime(time.gmtime(prods[0][0])))



# from datetime import timezone, timedelta, datetime
# import cbpro
#
# public_client = cbpro.PublicClient()
#
# date_now = datetime.utcnow()
# date_start = date_now - timedelta(hours=60)
# date_end = date_start + timedelta(hours=15)
# granularity=300
# currency_pair_id='BTC-USD'
#
# prods = public_client.get_product_historic_rates(
#     currency_pair_id,
#     start=date_start.isoformat(),
#     end=date_end.isoformat(),
#     granularity=granularity
# )
#
# ts_cbpro_end = prods[0][0]
# ts_cbpro_start = prods[-1][0]
#
# from utilities.utils_df_product_historic_rates import UtilsDfProductHistoricRates
# ts_own_start, ts_own_end = UtilsDfProductHistoricRates.get_start_end_timestamp_of_api(
#     date_start,
#     date_end,
#     granularity
# )

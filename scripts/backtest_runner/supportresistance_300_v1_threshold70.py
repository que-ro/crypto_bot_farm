from scripts.describers.custom_describer_1 import CustomDescriber1
from scripts.strategy_runners.custom_strategy_1 import CustomStrategy1Runner
import logging
import os
from datetime import datetime, timedelta
import pandas as pd


######################
# Backtest script
######################

# This is done in procedural because I have to use tensorflow and cbpro which requires different package versions
# So impossible to make it a class, and I need to change environment for specific step of the script, sad.

# Set variables feeded by user
describer_class = CustomDescriber1
strategy_runner_class = CustomStrategy1Runner
granularity = 300
quote_currency = 'GBP'
nb_of_process = 20
is_save_describer_df_on = True
is_save_stratrunner_df_on = True
log_lvl_describer = logging.INFO
log_lvl_strat_runner = logging.INFO
model_folder_name = 'supportresistance_300_v1'                 #Need to be in models/ folder
model_probability_threshold = 0.77
bank_quote = 50

# Set variables calling other classes
timedelta_for_all_process = describer_class.time_needed_for_process(
    granularity) + strategy_runner_class.time_needed_for_process(granularity)

# Constant that should be written somewhere centralized
DATA_FOLDER_PATH = os.path.join(os.getcwd(), 'data', 'backtest', model_folder_name)
DESCRIBER_DATA_FOLDER_PATH = os.path.join(DATA_FOLDER_PATH, 'describer')
THRESHOLD_DATA_FOLDER_PATH = os.path.join(DATA_FOLDER_PATH, str(model_probability_threshold))


#######################
# Folder creation
#######################

# Create data folder if it doesn't exist
data_folder = os.path.join(os.getcwd(), 'data')
if (os.path.exists(data_folder) == False):
    os.mkdir(data_folder)

# Create backtest folder if it doesn't exist
backtest_folder = os.path.join(os.getcwd(), 'data', 'backtest')
if (os.path.exists(backtest_folder) == False):
    os.mkdir(backtest_folder)

# Create model folder if it doesn't exist
if (os.path.exists(DATA_FOLDER_PATH) == False):
    os.mkdir(DATA_FOLDER_PATH)

# Create describer folder if it doesn't exist
if (os.path.exists(DESCRIBER_DATA_FOLDER_PATH) == False):
    os.mkdir(DESCRIBER_DATA_FOLDER_PATH)

# Create describer folder if it doesn't exist
if (os.path.exists(THRESHOLD_DATA_FOLDER_PATH) == False):
    os.mkdir(THRESHOLD_DATA_FOLDER_PATH)


#################################
# Describer process
#################################
# Use of environment that is able to call cbpro
import cbpro

# First get starting dates
list_start_dates = []
first_start_date = datetime.utcnow() - timedelta_for_all_process
list_start_dates.append(first_start_date)
for i in range(nb_of_process):
    multiplier = i + 1
    new_start_date = first_start_date - (describer_class.time_needed_for_process(granularity) * multiplier)
    list_start_dates.append(new_start_date)

# Loop through each starting dates
df_describer = None
for start_date in list_start_dates:

    # Describer process
    describer = describer_class(date_start=start_date, granularity=granularity,
                                     quote_currency=quote_currency,
                                     log_lvl=log_lvl_describer)
    describer.get_df_product_with_description()
    if (describer.df_products_description.empty):
        continue

    #Add start date of describer
    describer.df_products_description['date_start_process'] = start_date.isoformat()

    if(df_describer is None):
        df_describer = describer.df_products_description
    else:
        df_describer = pd.concat([df_describer, describer.df_products_description])


# Save describer dataframe
dataframe_filename = 'df.tsv'
if (os.path.exists(os.path.join(DESCRIBER_DATA_FOLDER_PATH, dataframe_filename))):
    df_describer.to_csv(
        os.path.join(DESCRIBER_DATA_FOLDER_PATH, dataframe_filename),
        mode='a',
        header=False,
        sep='\t'
    )
else:
    df_describer.to_csv(
        os.path.join(DESCRIBER_DATA_FOLDER_PATH, dataframe_filename),
        header=True,
        sep='\t'
    )

###################
# Model prediction
###################
# Change of environment to be able to use tensorflow

import logging
import os
from datetime import datetime, timedelta
import pandas as pd
from sklearn.preprocessing import StandardScaler
import tensorflow as tf

# Load df data
df_describer = pd.read_csv(os.path.join(DESCRIBER_DATA_FOLDER_PATH, 'df.tsv'), sep='\t', index_col=[0])
df_describer = df_describer.reset_index(drop=True)

df = df_describer.drop(['currency_pair_id', 'date_start_process'
              , 'quote_increment'
              , 'date_start_process'], axis=1)

#Calcul the gain loss of a single trade
fees_rate = 0.006
quote_volume = 10
df['one_trade_gain_loss'] = ((((quote_volume - (fees_rate * quote_volume)) / df['y_support']) * (1 - fees_rate)) * df['y_resistance']) - quote_volume
df = df.drop(['y_support', 'y_resistance'], axis=1)


# Standardize
features = df.columns.to_numpy()
scaler = StandardScaler()
df = scaler.fit_transform(df)
df = pd.DataFrame(df)
df = df.set_axis(features, axis=1, inplace=False)

# Load model
model = tf.keras.models.load_model(os.path.join(os.getcwd(), 'models', model_folder_name))

# Predict
y_pred_proba = model.predict(df)
y_pred = y_pred_proba > model_probability_threshold

# Filter original df
df_describer['y_pred'] = y_pred
df_describer['one_trade_gain_loss'] = df['one_trade_gain_loss']
df_describer = df_describer[df_describer['one_trade_gain_loss'] > 0]
df_describer = df_describer[df_describer['y_pred'] == True]

# Save it in data/threshold/describer/df.tsv
df_describer.to_csv(
    os.path.join(THRESHOLD_DATA_FOLDER_PATH, 'df_describer.tsv'),
    header=True,
    sep='\t'
)

######################
# Strat Runner Process
######################
#Change env to be able to use cbpro client

# Get list start dates of process from df
df_describer = pd.read_csv(os.path.join(THRESHOLD_DATA_FOLDER_PATH, 'df_describer.tsv'), sep='\t', index_col=[0])

# Get date to loop through
list_start_dates = df_describer['date_start_process'].unique()

# For each date, for each currency pair of this date
df_strat_runner = None
for start_date in list_start_dates:

    # Get subdf with this starting date
    df = df_describer[df_describer['date_start_process'] == start_date].copy(deep=True)

    # Get start date of strat runner
    describer_start_date = datetime.fromisoformat(start_date)
    strat_runner_start_date = describer_start_date + describer_class.time_needed_for_process(granularity)

    # Get volume init by dividing bank_quote / nb of chosen currency from this start date
    bank_quote = 50 / df.shape[0]

    # Loop through the currency of the starting_date
    strategy_runner = strategy_runner_class(date_start=strat_runner_start_date, granularity=granularity,
                                                 df_products=df,
                                                 log_lvl=log_lvl_strat_runner
                                                 )
    strategy_runner.BANK_QUOTE = bank_quote
    strategy_runner.get_df_product_with_strat_result()

    # Concat df
    if(df_strat_runner is None):
        df_strat_runner = strategy_runner.df_products
    else:
        df_strat_runner = pd.concat([df_strat_runner, strategy_runner.df_products])


# Save runner strat df
df_strat_runner.to_csv(
    os.path.join(THRESHOLD_DATA_FOLDER_PATH, 'df_strat_runner.tsv'),
    header=True,
    sep='\t'
)

##########################
# Check results
##########################

# Juste à voir les résultats, on aurait perdu 20 euros sur l'ensemble des sessions.
# Echec complet.

# Plot gain_loss separated by start_date
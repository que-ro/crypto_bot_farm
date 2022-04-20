from scripts import interfaces
import os
import csv
from datetime import datetime, timedelta
import logging


class DataAccumulatorV2():

    def __init__(self, describer_class, strategy_runner_class, result_labeller_class, granularity,
                 nb_of_process=100,
                 list_quote_currencies=['EUR', 'USD', 'GBP'],
                 save_describer_df=True,
                 save_stratrunner_df=True,
                 save_labeller_df=True,
                 log_lvl_describer=logging.INFO,
                 log_lvl_strat_runner=logging.INFO,
                 use_saved_describer_df=False
                 ):

        # Set variables feeded by user
        self.describer_class = describer_class
        self.strategy_runner_class = strategy_runner_class
        self.result_labeller_class = result_labeller_class
        self.granularity = granularity
        self.nb_of_process = nb_of_process
        self.list_quote_currencies = list_quote_currencies
        self.is_save_describer_df_on = save_describer_df
        self.is_save_runner_df_on = save_stratrunner_df
        self.is_save_labeller_df_on = save_labeller_df
        self.log_lvl_describer = log_lvl_describer
        self.log_lvl_strat_runner = log_lvl_strat_runner
        self.use_saved_describer_df = use_saved_describer_df

        # Check parameters
        assert issubclass(describer_class,
                          interfaces.ProductDescriberInterface), 'Describer class needs to implement ProductDescriberInterface'
        assert issubclass(strategy_runner_class,
                          interfaces.StrategyRunnerInterface), 'Strategy runner class needs to inherits StrategyRunnerInterface'
        assert issubclass(result_labeller_class,
                          interfaces.StrategyResultLabellerInterface), 'Result labeller class needs to inherits StrategyResultLabellerInterface'
        assert self.is_time_needed_for_process_initialized(describer_class, strategy_runner_class,
                                                           granularity), 'Describer and strat runner should implement .time_needed_for_process(granularity): -> timedelta'
        assert self.is_get_name_method_callable(describer_class, strategy_runner_class,
                                                result_labeller_class), 'Describer, strat runner and labeller should implement static method .get_name() -> str:'

        # Set variables calling other classes
        self.timedelta_for_all_process = self.describer_class.time_needed_for_process(
            self.granularity) + self.strategy_runner_class.time_needed_for_process(self.granularity)

        # Constant that should be written somewhere centralized
        self.DATA_FOLDER_PATH = os.path.join(os.getcwd(), '../..', 'data')
        self.DESCRIBER_DATA_FOLDER_PATH = os.path.join(self.DATA_FOLDER_PATH, 'describer')
        self.STRATRUNNER_DATA_FOLDER_PATH = os.path.join(self.DATA_FOLDER_PATH, 'strat_runner')
        self.LABELLER_DATA_FOLDER_PATH = os.path.join(self.DATA_FOLDER_PATH, 'labeller')

        # Create folders if needed
        self.check_or_create_data_folder()
        self.check_or_create_describer_folder()
        self.check_or_create_stratrunner_folder()
        self.check_or_create_labeller_folder()

    # region Methods for initialisation of class

    def is_time_needed_for_process_initialized(self, describer_class, strategy_runner_class, granularity):
        describer_has_time_process = hasattr(describer_class, 'time_needed_for_process') and callable(
            getattr(describer_class, 'time_needed_for_process'))
        runner_has_time_process = hasattr(strategy_runner_class, 'time_needed_for_process') and callable(
            getattr(strategy_runner_class, 'time_needed_for_process'))
        return describer_has_time_process and runner_has_time_process

    def is_get_name_method_callable(self, describer_class, strategy_runner_class, result_labeller_class):
        describer_has_get_name_method = hasattr(describer_class, 'get_name') and callable(
            getattr(describer_class, 'get_name'))
        runner_has_get_name_method = hasattr(strategy_runner_class, 'get_name') and callable(
            getattr(strategy_runner_class, 'get_name'))
        labeller_has_get_name_method = hasattr(result_labeller_class, 'get_name') and callable(
            getattr(result_labeller_class, 'get_name'))
        return describer_has_get_name_method and runner_has_get_name_method and labeller_has_get_name_method

    # endregion

    # region Methods for files

    def check_or_create_data_folder(self):
        if (os.path.exists(self.DATA_FOLDER_PATH) == False):
            os.mkdir(self.DATA_FOLDER_PATH)

    def check_or_create_describer_folder(self):
        if (os.path.exists(self.DESCRIBER_DATA_FOLDER_PATH) == False):
            os.mkdir(self.DESCRIBER_DATA_FOLDER_PATH)

    def check_or_create_stratrunner_folder(self):
        if (os.path.exists(self.STRATRUNNER_DATA_FOLDER_PATH) == False):
            os.mkdir(self.STRATRUNNER_DATA_FOLDER_PATH)

    def check_or_create_labeller_folder(self):
        if (os.path.exists(self.LABELLER_DATA_FOLDER_PATH) == False):
            os.mkdir(self.LABELLER_DATA_FOLDER_PATH)

    # endregion

    # region Methods for data accumulation

    def accumulate_data_for_X_nb_of_process(self):

        # Describer process
        date_start = datetime.utcnow() - self.timedelta_for_all_process
        df_describer = None

        # Loop through nb of process users want
        for quote_currency in self.list_quote_currencies:
            for i in range(self.nb_of_process):
                date_start_current = date_start - (timedelta(hours=15) * i)
                describer = self.describer_class(date_start=date_start_current, granularity=self.granularity,
                                                 quote_currency=quote_currency,
                                                 log_lvl=self.log_lvl_describer)
                describer.get_df_product_with_description()

                if(df_describer is None):
                    df_describer = describer.df_products_description
                else:
                    df_describer = [*df_describer, *describer.df_products_description]

        # Save data
        if (self.is_save_describer_df_on):
            self.save_describer_df_in_data_folder(df_describer,
                                                  self.describer_class.get_name(),
                                                  self.nb_of_process,
                                                  date_start)


        # Runner process
        strategy_runner = self.strategy_runner_class(granularity=self.granularity,
                                                     df_products=df_describer,
                                                     log_lvl=self.log_lvl_strat_runner)
        strategy_runner.get_df_product_with_strat_result()

        # Save data
        if (self.is_save_runner_df_on):
            self.save_stratrunner_df_in_data_folder(strategy_runner.df_products,
                                                  self.describer_class.get_name(),
                                                  self.strategy_runner_class.get_name(),
                                                  self.nb_of_process,
                                                  date_start)

        # Labeller process
        result_labeller = self.result_labeller_class(df_products=strategy_runner.df_products)
        result_labeller.get_df_product_with_strat_result_label()

        # Save data
        if(self.is_save_labeller_df_on):
            self.save_labeller_df_in_data_folder(result_labeller.df_products,
                                                    self.describer_class.get_name(),
                                                    self.strategy_runner_class.get_name(),
                                                    self.result_labeller_class.get_name(),
                                                    self.nb_of_process,
                                                    date_start)


    def accumulate_data_with_previous_describer_df(self):
        pass  # todo

    # endregion

    # region Saving methods
    def save_describer_df_in_data_folder(self, df_describer, describer_name, nb_process, date_start):
        """Save the describer dataframe for further use"""

        # Save describer dataframe
        filename_df_describer = 'df_' + \
                                str(describer_name) + '_' + \
                                str(nb_process) + '_' + \
                                str(date_start.isoformat()) + '_' + \
                                '.tsv'

        df_describer.to_csv(
            os.path.join(self.DESCRIBER_DATA_FOLDER_PATH, filename_df_describer),
            header=True,
            sep='\t'
        )

    def save_stratrunner_df_in_data_folder(self, df_runner, describer_name, stratrunner_name, nb_process, date_start):
        """Save the describer dataframe for further use"""

        # Save describer dataframe
        filename_df_describer = 'df_' + \
                                str(describer_name) + '_' + \
                                str(stratrunner_name) + '_' + \
                                str(nb_process) + '_' + \
                                str(date_start.isoformat()) + '_' + \
                                '.tsv'

        df_runner.to_csv(
            os.path.join(self.STRATRUNNER_DATA_FOLDER_PATH, filename_df_describer),
            header=True,
            sep='\t'
        )

    def save_labeller_df_in_data_folder(self, df_labeller, describer_name, stratrunner_name, labeller_name,
                                        nb_process, date_start):
        """Save the describer dataframe for further use"""

        # Save describer dataframe
        filename_df_describer = 'df_' + \
                                str(describer_name) + '_' + \
                                str(stratrunner_name) + '_' + \
                                str(labeller_name) + '_' + \
                                str(nb_process) + '_' + \
                                str(date_start.isoformat()) + '_' + \
                                '.tsv'

        df_labeller.to_csv(
            os.path.join(self.LABELLER_DATA_FOLDER_PATH, filename_df_describer),
            header=True,
            sep='\t'
        )
    # endregion
import interfaces
import os
import csv
from datetime import datetime

class DataAccumulator():

    def __init__(self, describer_class, strategy_runner_class, result_labeller_class, granularity, quote_currency, nb_of_process):

        #Set variables feeded by user
        self.describer_class = describer_class
        self.strategy_runner_class = strategy_runner_class
        self.result_labeller_class = result_labeller_class
        self.granularity = granularity
        self.quote_currency = quote_currency
        self.nb_of_process = nb_of_process

        #Check parameters
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

        #Set variables calling other classes
        self.timedelta_for_all_process = self.describer_class.time_needed_for_process(
            self.granularity) + self.strategy_runner_class.time_needed_for_process(self.granularity)
        self.index_filename = self.describer_class.get_name() + self.strategy_runner_class.get_name() + self.result_labeller_class.get_name() + '_' + str(
            self.granularity) + '_index.tsv'
        self.dataframe_filename = self.describer_class.get_name() + self.strategy_runner_class.get_name() + self.result_labeller_class.get_name() + '_' + str(
            self.granularity) + '_dataframe.tsv'

        #Constant that should be written somewhere centralized
        self.DATA_FOLDER_PATH = os.path.join(os.getcwd(), '..', 'data')

        #Variables used during the process
        self.dict_indexes_processed = {}  # {'datetime' : 'quote'}
        self.dict_indexes_going_to_be_processed = {}  # {'datetime' : 'quote'}


    #region Methods for initialisation of class

    def is_time_needed_for_process_initialized(self, describer_class, strategy_runner_class, granularity):
        describer_has_time_process = hasattr(describer_class, 'time_needed_for_process') and callable(getattr(describer_class, 'time_needed_for_process'))
        runner_has_time_process = hasattr(strategy_runner_class, 'time_needed_for_process') and callable(getattr(strategy_runner_class, 'time_needed_for_process'))
        return describer_has_time_process and runner_has_time_process

    def is_get_name_method_callable(self, describer_class, strategy_runner_class, result_labeller_class):
        describer_has_get_name_method = hasattr(describer_class, 'get_name') and callable(getattr(describer_class, 'get_name'))
        runner_has_get_name_method = hasattr(strategy_runner_class, 'get_name') and callable(getattr(strategy_runner_class, 'get_name'))
        labeller_has_get_name_method = hasattr(result_labeller_class, 'get_name') and callable(getattr(result_labeller_class, 'get_name'))
        return describer_has_get_name_method and runner_has_get_name_method and labeller_has_get_name_method

    #endregion

    #region Methods for files

    def check_or_create_data_folder(self):
        if (os.path.exists(self.DATA_FOLDER_PATH) == False):
            os.mkdir(self.DATA_FOLDER_PATH)

    def does_index_file_exist(self):
        return os.path.exists(os.path.join(self.DATA_FOLDER_PATH, self.index_filename))

    def does_dataframe_file_exist(self):
        return os.path.exists(os.path.join(self.DATA_FOLDER_PATH, self.dataframe_filename))

    #endregion

    #region Methods for datetime quote indexes

    def get_index_to_process(self):
        if (self.does_index_file_exist()):
            self.fill_dict_indexes_from_file()
            if (self.is_quote_present_in_dict_indexes_processed()):
                self.get_indexes_for_existant_quote()
            else:
                self.get_indexes_for_inexistant_quote()
        else:
            self.create_new_index()

    def create_new_index(self):
        date_end = datetime.now()
        date_start = date_end
        for index_process in range(1, self.nb_of_process + 1):
            date_start = date_start - self.timedelta_for_all_process
            self.dict_indexes_going_to_be_processed[date_start] = self.quote_currency

    def fill_dict_indexes_from_file(self):
        with open(os.path.join(self.DATA_FOLDER_PATH, self.index_filename)) as file:
            tsv_file = csv.reader(file, delimiter='\t')
            for line in tsv_file:
                self.dict_indexes_processed[datetime.fromisoformat(line[0])] = line[1]

    def is_quote_present_in_dict_indexes_processed(self):
        return self.quote_currency in self.dict_indexes_processed.values()

    def get_indexes_for_inexistant_quote(self):
        most_recent_date = max([key for key in self.dict_indexes_processed.keys()])
        date_start = most_recent_date
        for index_process in range(1, self.nb_of_process + 1):
            date_start = date_start - self.timedelta_for_all_process
            self.dict_indexes_going_to_be_processed[date_start] = self.quote_currency

    def get_indexes_for_existant_quote(self):
        nb_of_process_added_in_method = 0

        # Add more recent datetime index if possible
        most_recent_datetime = max([k for k in {key: value for key, value in self.dict_indexes_processed.items() if
                                                value == self.quote_currency}.keys()])
        date_start_index = most_recent_datetime + self.timedelta_for_all_process
        while (date_start_index < (datetime.now() - self.timedelta_for_all_process) and (nb_of_process_added_in_method < self.nb_of_process)):
            self.dict_indexes_going_to_be_processed[date_start_index] = self.quote_currency
            date_start_index = date_start_index + self.timedelta_for_all_process
            nb_of_process_added_in_method += 1

        # Add after the oldest datetime index
        oldest_datetime = min([k for k in {key: value for key, value in self.dict_indexes_processed.items() if value == self.quote_currency}.keys()])
        date_start_index = oldest_datetime - self.timedelta_for_all_process
        while nb_of_process_added_in_method < self.nb_of_process:
            self.dict_indexes_going_to_be_processed[date_start_index] = self.quote_currency
            date_start_index = date_start_index - self.timedelta_for_all_process
            nb_of_process_added_in_method += 1

    #endregion

    #region Methods for data accumulation

    def accumulate_data_for_X_nb_of_process(self):

        # get index to process
        self.get_index_to_process()

        for date_start, quote_currency in self.dict_indexes_going_to_be_processed.items():

            # Describer process
            describer = self.describer_class(date_start=date_start, granularity=self.granularity, quote_currency=quote_currency)
            describer.get_df_product_with_description()

            # Runner process
            date_start_runner = date_start + self.describer_class.time_needed_for_process(self.granularity)
            strategy_runner = self.strategy_runner_class(date_start=date_start_runner, granularity=self.granularity,
                                                    df_products=describer.df_products_description)
            strategy_runner.get_df_product_with_strat_result()

            # Labeller process
            result_labeller = self.result_labeller_class(df_products=strategy_runner.df_products)
            result_labeller.get_df_product_with_strat_result_label()

            # Add dataframe to df file
            result_labeller.df_products['date_start_process'] = date_start.isoformat()
            if (self.does_dataframe_file_exist()):
                result_labeller.df_products.to_csv(
                    os.path.join(self.DATA_FOLDER_PATH, self.dataframe_filename),
                    mode='a',
                    header=False,
                    sep='\t'
                )
            else:
                result_labeller.df_products.to_csv(
                    os.path.join(self.DATA_FOLDER_PATH, self.dataframe_filename),
                    header=True,
                    sep='\t'
                )

            # Add indexes to index file
            with open(os.path.join(self.DATA_FOLDER_PATH, self.index_filename), 'a+') as file:
                file.write(str(date_start.isoformat()) + '\t' + quote_currency + '\n')

            # Add to processed indexes
            self.dict_indexes_processed[date_start] = quote_currency

        #Remove indexes going to be removed
        self.dict_indexes_going_to_be_processed = {}

    #endregion
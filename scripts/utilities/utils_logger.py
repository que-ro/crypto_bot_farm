import os, logging, sys

class UtilitiesLogger:

    @staticmethod
    def get_file_handler(file_path, log_lvl):

        # create file handler
        file_handler = logging.FileHandler(filename=file_path)
        file_handler.setLevel(log_lvl)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        return file_handler

    @staticmethod
    def get_console_handler(log_lvl):

        # create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_lvl)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        return console_handler


    @staticmethod
    def get_logger(logger_name, log_lvl, is_on_file=True, is_on_console=True,
                   logs_folder=os.path.join(os.getcwd(), '..', 'bin'),
                   logs_filename = 'app.logs'):

        # create or get existing logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_lvl)

        # check if log folder exist
        if (os.path.exists(logs_folder) == False):
            os.mkdir(logs_folder)

        # add handlers
        if (logger.hasHandlers()):
            logger.handlers.clear()

        logger.addHandler(UtilitiesLogger.get_file_handler(
            file_path=os.path.join(logs_folder, logs_filename),
            log_lvl=log_lvl
        ))
        logger.addHandler(UtilitiesLogger.get_console_handler(
            log_lvl=log_lvl
        ))

        # turn off propagation to parent logger
        logger.propagate = False

        return logger


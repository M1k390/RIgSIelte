#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logger central

Some features of this module:
-   Creation and setting of Python loggers 
        (see: https://docs.python.org/3/library/logging.html)
-   Storing of information about the loggers in use
-   Managing of log files
-   Log formatting
"""

import logging
from typing import Dict, Optional

from rigproc.params import conf_values, cli
from rigproc.commons.helper import helper


MAIN_FILE_HANDLER_NAME = 'main_file'
SHARED_FILE_HANDLER_NAME = 'shared_file'


################################################################################
#
#   LOGGER SPECS
#
################################################################################


class LoggerSpecs:
    """
    Object to store information about loggers.
    
    Automatically generates the log file path from dir and file name.
    """

    def __init__(
        self,
        name: str,
        format_code: str,
        console_level: int,
        file_level: int,
        log_file_prefix: str,
        log_file_dir: str,
        log_file_mode: str,
        root_log_file_prefix: str,
        root_log_dir: str,
        print_to_console: bool,
        formatter_setting: Optional[str],
        session_timestamp: str,
        is_root: bool
    ) -> None:
        """
        Parameters
        ----------
        `name` : str
            logger name
        `format_code` : str
            logger formatter string
            e.g.: 

`%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s`
        
        `console_level` : int
            level of console's logs

                -   0: NOTSET
                -   10: DEBUG
                -   20: INFO
                -   30: WARNING
                -   40: ERROR
                -   50: CRITICAL

        `file_level` : int
            level of file's logs
        `log_file_name` : str
        `log_file_dir` : str
        `log_file_mode` : str
            `append`: append logs to the end of the existing file, or create it
            `write`: overwrite or create file
        `print_to_console` : bool
            write logs to console
        `formatter_setting` : str | None
            `None`: normal formatter
            `color`: apply colors to log levels
            `alt`: apply different colors for DEBUG and INFO
            `custom`: allow the log creator to choose the color
        `session_timestamp` : str
            readable timestamp of logger creation
        `is_root` : bool
            determines if this is the root logger

        Creating LoggerSpecs initializes the Python logger
        """

        self.name= name
        self.format_code= format_code
        self.console_level= console_level
        self.file_level= file_level
        self.log_file_prefix= log_file_prefix
        self.log_file_dir= log_file_dir
        self.log_file_mode= log_file_mode
        self.root_log_file_prefix = root_log_file_prefix
        self.root_log_dir = root_log_dir
        self.print_to_console= print_to_console
        self.formatter_setting= formatter_setting
        self.is_root= is_root

        # Store timestamp and generate log file path
        self.set_session_timestamp(session_timestamp)

        self.log_file_path = None
        self.root_log_file_path = None
        
        self._generate_handlers()

    def _generate_handlers(self):
        # Get the Logger object with the desired name
        logger= logging.getLogger(self.name)

        # Clear the existing handlers
        logger.handlers.clear()

        # Generate stream handler
        if self.print_to_console:
            print(f'Adding log console stream handler to logger "{self.name}", ' +\
                f'level: {self.console_level}')

            # Get correct formatter based on `formatter_setting`
            formatter= _get_formatter(
                format_code=self.format_code, 
                formatter_setting=self.formatter_setting
            )

            console_handler= logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(self.console_level)
            logger.addHandler(console_handler)

        # Generate log file path
        self.log_file_path = _get_log_file_path(
            self.log_file_prefix,
            self.log_file_dir,
            self.session_timestamp
        )
        
        # Generate file handler if the file path was correctly generated
        if self.log_file_path is not None:
            print(f'Adding log file handler to logger "{self.name}", ' +\
                f'level: {self.file_level}')
            
            if self.log_file_mode == conf_values.log_file_mode.append:
                init_mode= 'a'
            elif self.log_file_mode == conf_values.log_file_mode.write:
                init_mode= 'w'
            else:
                init_mode= 'a'
            try:
                with open(self.log_file_path, init_mode) as log_file:
                    log_file.write(f'\n\nLOG SESSION {self.session_timestamp}\n\n')
            except:
                print('ERROR initializing log file')
            
            file_handler= logging.FileHandler(self.log_file_path, mode='a')
            file_handler.setFormatter(logging.Formatter(self.format_code))
            file_handler.setLevel(self.file_level)
            file_handler.set_name('main_file')
            logger.addHandler(file_handler)

        if self.root_log_file_prefix and self.root_log_dir:
            self.root_log_file_path = _get_log_file_path(
                self.root_log_file_prefix,
                self.root_log_dir,
                self.session_timestamp
            )

            if self.root_log_file_path:
                # Add the new file handler to the source logger
                print(
                    f'Adding shared log file to {self.name} to the root log file'
                )
                shared_file_handler= logging.FileHandler(self.root_log_file_path, mode='a')
                shared_file_handler.setFormatter(logging.Formatter(self.format_code))
                shared_file_handler.setLevel(self.file_level)
                shared_file_handler.set_name('shared_file')
                logger.addHandler(shared_file_handler)
        
        # Set logger level
        logger.setLevel(self.console_level)

    def get_logger(self):
        return logging.getLogger(self.name)

    def set_session_timestamp(self, timestamp: str):
        """
        Store timestamp and generate log file path

        Change all file handlers.
        """

        self.session_timestamp= timestamp
        
        # Regenerate handlers
        self._generate_handlers()


################################################################################
#
#   LOGGING MANAGER
#
################################################################################


class LoggingManager:
    """
    Manages the creation and stores information about the loggers in use.
    """

    def __init__(self) -> None:
        """
        Generating a LoggingManager initiate its session timestamp to the current timestamp
        """
        self.m_loggers: list[LoggerSpecs]= []
        self.m_session_timestamp = helper.timestampNowFormatted()

    def get_logger_specs(self, logger_name: str) -> Optional[LoggerSpecs]:
        for logger_specs in self.m_loggers:
            if logger_specs.name == logger_name:
                return logger_specs
        return None

    def get_root_logger(self) -> logging.Logger:
        """
        Returns the first root logger in the loggers list.
        """
        for logger_specs in self.m_loggers:
            if logger_specs.is_root:
                return logging.getLogger(logger_specs.name)
        return logging.getLogger()

    def get_session_timestamp(self):
        return self.m_session_timestamp

    def set_session_timestamp(self, ts: str):
        """
        Changing the session timestamp will renew all the File Handlers for 
        each logger.
        """
        self.m_session_timestamp = ts
        for logger_specs in self.m_loggers:
            logger_specs.set_session_timestamp(ts)

    def generate_logger(
        self,
        logger_name: str,
        format_code: str,
        console_level: int,
        file_level: int,
        log_file_name: str,
        log_file_dir: str,
        log_file_mode: str,
        root_log_file_prefix: str,
        root_log_dir: str,
        print_to_console=True,
        formatter_setting: str='',
        is_root=False,
        overwrite=False
    ) -> logging.Logger:
        """
        Creates a logger with desired parameters, adding stream and file handlers.

        File handlers use the prefix specified in the configuration,
        adding the session timestamp to the file's name.

        To renew the log files, you must change the session timestamp.
        """

        # If the logger was already created, use that one
        for logger_specs in self.m_loggers:
            if logger_specs.name == logger_name:
                if overwrite:
                    self.m_loggers.remove(logger_specs)
                else:
                    print(
                        'Returning a logger already created. ' +\
                            'The new parameters will be ignored!'
                    )
                    return logging.getLogger(logger_name)

        # Create a LoggerSpecs object
        logger_specs= LoggerSpecs(
            name=logger_name,
            format_code=format_code,
            console_level=console_level,
            file_level=file_level,
            log_file_prefix=log_file_name,
            log_file_dir=log_file_dir,
            log_file_mode=log_file_mode,
            root_log_file_prefix=root_log_file_prefix,
            root_log_dir=root_log_dir,
            print_to_console=print_to_console,
            formatter_setting=formatter_setting,
            session_timestamp=self.m_session_timestamp,
            is_root=is_root
        )

        logger= logger_specs.get_logger()

        # Save LoggerSpecs
        self.m_loggers.append(logger_specs)

        return logger
        

################################################################################
#
#   UTILITY
#
################################################################################


def _get_log_file_path(log_file_prefix, log_file_dir, timestamp=None) -> Optional[str]:
    """
    Generate the log file path, test if it is writable and returns its path.

    Parameters
    ----------
    - `log_file_prefix`: the first part of the file name. It cannot be empty.
    If `timestamp` is not None, it is added to the file name.
    The name terminates with ".log".
    - `log_file_dir`
    - `timestamp`

    Returns
    -------
    "{log_file_dir}{_{timestamp}?}.log" | `None`
    """
    if log_file_prefix == '':
        return None
    log_file_writable= False
    log_file_path= None
    log_file_dir= helper.abs_path(log_file_dir)
    log_dir_exists= helper.dir_exists_create(log_file_dir)
    
    if log_dir_exists:
        # Join dir and file name
        log_file_path= helper.join_paths(log_file_dir, log_file_prefix)

        # Add timestamp
        if timestamp is not None:
            # CAUTION!! This format influences the `clean_log_folder` method of LoggingManager
            log_file_path = f'{log_file_path}_{timestamp}'

        # Add extension
        log_file_path += '.log'

        # Check log file
        log_file_writable= _check_log_file(log_file_path)
    
    if log_file_writable:
        return log_file_path
    else:
        return None


def _check_log_file(log_file_path: str) -> bool:
    try:
        log_file= open(log_file_path, 'a+')
        log_file.close()
        return True
    except:
        print(f'ERROR: Cannot open the log file {log_file_path}')
        return False


def _get_formatter(format_code: str, formatter_setting: Optional[str]):
    if formatter_setting == conf_values.log_formatter.color:
        return _ColorFormatter(format_code)
    elif formatter_setting == conf_values.log_formatter.alt:
        return _AltColorFormatter(format_code)
    elif formatter_setting == conf_values.log_formatter.custom:
        return _CustomColorFormatter(format_code)
    else:
        return logging.Formatter(format_code)


################################################################################
#
#   FORMATTERS
#
################################################################################


class _ColorFormatter(logging.Formatter):
    """Colored Formatter"""

    def __init__(self, format_code):
        self.format_code= format_code
        self.COLOR_WRAPPERS= {
            logging.DEBUG:      cli.color.forw_gray.value +     '{}' + cli.color.regular.value,
            logging.INFO:       cli.color.regular.value +       '{}' + cli.color.regular.value,
            logging.WARNING:    cli.color.forw_yellow.value +   '{}' + cli.color.regular.value,
            logging.ERROR:      cli.color.forw_red.value +      '{}' + cli.color.regular.value,
            logging.CRITICAL:   cli.color.back_red.value +      '{}' + cli.color.regular.value
        }

    def _apply_color(self, record: logging.LogRecord, color_wrap: str) -> logging.Formatter:
        try:
            lines= record.getMessage().split('\n')
            record.msg= '\n'.join([color_wrap.format(line) for line in lines])
            log_format= color_wrap.format(self.format_code)
            return logging.Formatter(log_format)
        except:
            return logging.Formatter(self.format_code)

    def format(self, record: logging.LogRecord):
        color_wrap= self.COLOR_WRAPPERS.get(record.levelno)
        formatter= self._apply_color(record, color_wrap)
        return formatter.format(record)


class _AltColorFormatter(_ColorFormatter):
    """Special colored formatter (e.g.: flow messages)"""

    def __init__(self, format_code):
        super().__init__(format_code)
        self.COLOR_WRAPPERS= {
            logging.DEBUG:      cli.color.forw_green.value +    '{}' + cli.color.regular.value,
            logging.INFO:       cli.color.back_green.value +    '{}' + cli.color.regular.value,
            logging.WARNING:    cli.color.forw_yellow.value +   '{}' + cli.color.regular.value,
            logging.ERROR:      cli.color.forw_red.value +      '{}' + cli.color.regular.value,
            logging.CRITICAL:   cli.color.back_red.value +      '{}' + cli.color.regular.value
        }


color_delimiter= '&%$'


class _CustomColorFormatter(_ColorFormatter):
    """ Custom color formatter: allows to specify custom colors (e.g.: Rigcam) """
    def format(self, record: logging.LogRecord):
        record_msg= record.getMessage()
        if color_delimiter in record_msg:
            color, msg= record_msg.split(color_delimiter)[0:2]
            record.msg= msg
            if record.levelno == logging.INFO:
                color_wrap= color + '{}' + cli.color.regular.value
                formatter= self._apply_color(record, color_wrap)
                return formatter.format(record)
            else:
                return super().format(record)
        else:
            return super().format(record)


# SINGLETON

logging_manager= LoggingManager()

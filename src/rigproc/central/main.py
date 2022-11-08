#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main RIG process

"""

import logging
import sys
import os
from pathlib import Path
import json

from rigproc import __version__ as version
from . import mainprocess as mp
from rigproc.commons.logger import logging_manager
from rigproc.commons import keywords

from rigproc.params import internal


g_config= {}


def _set_config(l_confFile):
    """
    Cofig load from json
    """
    global g_config
    try:
        with open(l_confFile,"r") as l_jsonF:
            g_config= json.load(l_jsonF)
    except IOError as e:
        print("ERROR: exception opening conf " + str(e))
        sys.exit()
    except ValueError as j:
        print("ERROR: exception reading json format " + str(j))        
        sys.exit()
            

def runrig(p_configFile, p_main_dir=None):
    """
    Avvia il processo di gestione
    
    p_configFile: path file di configurazione
    """
    # Read config json
    _set_config(p_configFile)
    
    # Set logger. The parameters are directly read from the config json
    try:
        l_rootLog= logging_manager.generate_logger(
            logger_name='root',
            format_code=g_config['logging']['root']['format'],
            console_level=g_config['logging']['root']['console_level'],
            file_level=g_config['logging']['root']['file_level'],
            log_file_name=g_config['logging']['root']['file_name'],
            log_file_dir=g_config['logging']['root']['file_dir'],
            log_file_mode=g_config['logging']['root']['file_mode'],
            root_log_file_prefix=None,
            root_log_dir=None,
            formatter_setting=g_config['logging']['root']['formatter'],
            is_root=True
        )
    except Exception as e:
        logging.getLogger('root').critical(f'Conf json does not contain the necessary logging parameters (logging -> root). {type(e)}: {e}')
        sys.exit()
    l_rootLog.info(f"Starting rig version {version}")
    # Set datadir in env variable
    if isinstance(p_main_dir, str):
        l_rootLog.info(f'Setting environment variable for main directory to: {p_main_dir}')
        os.environ[internal.env.rig_dir]= p_main_dir
    # logging ready
    l_mp= mp.MainProcess(g_config)      
    l_mp.configure()
    

    
    

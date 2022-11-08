#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test io bus higher level
"""

import pytest
import serial
import threading
import os
import sys
import time
import logging
import pdb
import json

from rigproc.commons.config import init_configuration, get_config
from rigproc.io import iocomm
from rigproc.commons import keywords
from rigproc.fake_modules import fakebus
from rigproc.commons.logger import logging_manager
from rigproc.params import bus


" ------------- PRE LUANCH -------- "

def closeCat():
    """ Chisura di ogni test """
    fakebus.fakebus.close()
    fakebus.closeFakeSerialBus()

g_config= None

def _set_config(l_confFile):
    """
    Cofig load from json
    """
    global g_config
    try:
        with open(l_confFile,"r") as l_jsonF:
            l_conf_dict= json.load(l_jsonF)
    except IOError as e:
        print("ERROR: exception opening conf " + str(e))
        sys.exit()
    except ValueError as j:
        print("ERROR: exception reading json format " + str(j))        
        sys.exit()
    init_configuration(l_conf_dict)
    g_config= get_config()

@pytest.fixture(autouse= True)
def pre_launch(request):
    """ 
    lancio pre test, socat
    colleghi anche la funzione di chiusura
    Quest fixture viene lanciata priam di ogni test,
    yield lascia eseguire il test
    finalize lo chiude
    """
    "Loading config file"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    _set_config( os.path.join(dir_path,'config/test.json'))
    " io fake + serial internal ports"
    fakebus.initFakeSerialBus()
    " Logger "
    logging_manager.generate_logger(
        logger_name='root',
        format_code=get_config().logging.root.format.get(),
        console_level=get_config().logging.root.console_level.get(),
        file_level=get_config().logging.root.file_level.get(),
        log_file_name=get_config().logging.root.file_name.get(),
        log_file_dir=get_config().logging.root.file_dir.get(),
        log_file_mode=get_config().logging.root.file_mode.get(),
		root_log_file_prefix=None,
		root_log_dir=None,
        formatter_setting=get_config().logging.root.formatter.get()
    )
    " io comm "
    pytest.log= logging.getLogger('root')
    pytest.io_comm= iocomm.IOComm()
    pytest.io_comm.run()
    " sessione .."
    yield
    pytest.log.info("clsoing fixture")
    " Closing "
    request.addfinalizer(closeCat)

" ------------- TESTS -------- "

" SYSTEM "

def test_aliveAndOk():
    """tutto attivo ?"""
    assert pytest.io_comm.isOk() == True
    assert pytest.io_comm.cmdThreadIsRunning() == True
    assert fakebus.fakebus.isOk() == True

" MTX "

def test_answVersionPrrA():
    """ MOSF_TX A Versione """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mtx_ver_a
    cmd['data']=''
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert l_ansKey != None
    assert list(l_ansKey.keys())[0] == keywords.cmd_mtx_ver_a
    assert l_ansKey[keywords.cmd_mtx_ver_a][keywords.data_mtx_vers_key] == 12

def test_answSpeedPrrA():
    """ MOSF_TX A Velocità/Allarmi """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mtx_vel_a
    cmd['data']=''
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mtx_vel_a
    assert l_ansKey[keywords.cmd_mtx_vel_a][keywords.data_mtx_velo_key] == 12
    assert l_ansKey[keywords.cmd_mtx_vel_a][keywords.data_mtx_direction_key] == keywords.bin_pari
    assert l_ansKey[keywords.cmd_mtx_vel_a][keywords.data_mtx_event_key] == keywords.mtx_event_attesa_trigger

def test_answVersionPrrB():
    """ MOSF_TX B Versione """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mtx_ver_b
    cmd['data']=''
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mtx_ver_b
    assert l_ansKey[keywords.cmd_mtx_ver_b][keywords.data_mtx_vers_key] == 12

def test_answSpeedPrrB():
    """ MOSF_TX B Velocità/Allarmi """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mtx_vel_b
    cmd['data']=''
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mtx_vel_b
    assert l_ansKey[keywords.cmd_mtx_vel_b][keywords.data_mtx_velo_key] == 12
    assert l_ansKey[keywords.cmd_mtx_vel_b][keywords.data_mtx_direction_key] == keywords.bin_pari
    assert l_ansKey[keywords.cmd_mtx_vel_b][keywords.data_mtx_event_key] == keywords.mtx_event_attesa_trigger


def test_answOnOffPrrA():
    """ MOSF_TX A ON/OFF """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']= keywords.cmd_mtx_on_off_a
    cmd['data']= keywords.status_on
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mtx_on_off_a
    assert l_ansKey[keywords.cmd_mtx_on_off_a][keywords.data_mtx_onoff_key] == keywords.status_on

def test_answOnOffPrrB():
    """ MOSF_TX B ON/OFF """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']= keywords.cmd_mtx_on_off_b
    cmd['data']= keywords.status_on
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mtx_on_off_b
    assert l_ansKey[keywords.cmd_mtx_on_off_b][keywords.data_mtx_onoff_key] == keywords.status_on

" MRX "

def test_answVersionMRX_A():
    """ MOSF_RX A Versione """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mrx_ver_a
    cmd['data']=''
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert l_ansKey != None
    assert list(l_ansKey.keys())[0] == keywords.cmd_mrx_ver_a
    assert l_ansKey[keywords.cmd_mrx_ver_a][keywords.data_mrx_vers_key] == 12

def test_answVersionMRX_B():
    """ MOSF_RX B Versione """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mrx_ver_b
    cmd['data']=''
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert l_ansKey != None
    assert list(l_ansKey.keys())[0] == keywords.cmd_mrx_ver_b
    assert l_ansKey[keywords.cmd_mrx_ver_b][keywords.data_mrx_vers_key] == 12

def test_answWireT0PrrA():
    """ MOSF_RX A Altezza """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mrx_wire_t0_a
    cmd['data']=''
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mrx_wire_t0_a
    assert l_ansKey[keywords.cmd_mrx_wire_t0_a][keywords.data_mosf_wire_t0_key] == 32
    assert l_ansKey[keywords.cmd_mrx_wire_t0_a][keywords.data_mrx_event_key] == keywords.mrx_event_attesa_trigger
    assert l_ansKey[keywords.cmd_mrx_wire_t0_a][keywords.data_mrx_direction_key] == keywords.bin_pari

def test_answWireT0PrrB():
    """ MOSF_RX B Altezza """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mrx_wire_t0_b
    cmd['data']=''
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mrx_wire_t0_b
    assert l_ansKey[keywords.cmd_mrx_wire_t0_b][keywords.data_mosf_wire_t0_key] == 32
    assert l_ansKey[keywords.cmd_mrx_wire_t0_b][keywords.data_mrx_event_key] == keywords.mrx_event_attesa_trigger
    assert l_ansKey[keywords.cmd_mrx_wire_t0_b][keywords.data_mrx_direction_key] == keywords.bin_pari

def test_answTmosPrrA():
    """ MOSF_RX A TMOS """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mrx_tmos_a
    cmd['data']={}
    cmd['data'][keywords.data_mosf_tpre_key]=int(25)
    cmd['data'][keywords.data_mosf_tpost_key]=int(25)
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mrx_tmos_a
    assert l_ansKey[keywords.cmd_mrx_tmos_a][keywords.data_mosf_tpre_key] == int(25)
    assert l_ansKey[keywords.cmd_mrx_tmos_a][keywords.data_mosf_tpost_key] == int(25)

def test_answTmosPrrB():
    """ MOSF_RX B TMOS """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mrx_tmos_b
    cmd['data']={}
    cmd['data'][keywords.data_mosf_tpre_key]=int(25)
    cmd['data'][keywords.data_mosf_tpost_key]=int(25)
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mrx_tmos_b
    assert l_ansKey[keywords.cmd_mrx_tmos_b][keywords.data_mosf_tpre_key] == int(25)
    assert l_ansKey[keywords.cmd_mrx_tmos_b][keywords.data_mosf_tpost_key] == int(25)

def test_answWireDataPrrA():
    """ MOSF_RX A DatiGrafico """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mrx_wire_data_a
    cmd['data']={}
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mrx_wire_data_a
    assert l_ansKey[keywords.cmd_mrx_wire_data_a][keywords.data_mosf_wire_data_ok_key] == keywords.status_ok
    assert len(l_ansKey[keywords.cmd_mrx_wire_data_a][keywords.data_mosf_wire_data_key]) == 512
    assert sum(l_ansKey[keywords.cmd_mrx_wire_data_a][keywords.data_mosf_wire_data_key]) == 0


def test_answWireDataPrrB():
    """ MOSF_RX B DatiGrafico """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_mrx_wire_data_b
    cmd['data']={}
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_mrx_wire_data_b
    assert l_ansKey[keywords.cmd_mrx_wire_data_b][keywords.data_mosf_wire_data_ok_key] == keywords.status_ok
    assert len(l_ansKey[keywords.cmd_mrx_wire_data_b][keywords.data_mosf_wire_data_key]) == 512
    assert sum(l_ansKey[keywords.cmd_mrx_wire_data_b][keywords.data_mosf_wire_data_key]) == 0


" TRIGGER "

def test_answTrigSettPrrA():
    """ TRIGGER A Setting """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_trig_setting_a
    cmd['data']= {}
    cmd['data'][keywords.data_trig_latency]= 4
    cmd['data'][keywords.data_trig_exposure]= 20
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_trig_setting_a
    assert l_ansKey[keywords.cmd_trig_setting_a][keywords.data_trig_latency] == 4
    assert l_ansKey[keywords.cmd_trig_setting_a][keywords.data_trig_exposure] == 20

def test_answTrigSettPrrB():
    """ TRIGGER B Setting """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_trig_setting_b
    cmd['data']= {}
    cmd['data'][keywords.data_trig_latency]= 4
    cmd['data'][keywords.data_trig_exposure]= 20
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_trig_setting_b
    assert l_ansKey[keywords.cmd_trig_setting_b][keywords.data_trig_latency] == 4
    assert l_ansKey[keywords.cmd_trig_setting_b][keywords.data_trig_exposure] == 20

def test_answTrigOnOffPrrA():
    """ TRIGGER A ON/OFF """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']= keywords.cmd_trig_on_off_a
    cmd['data']= keywords.status_on
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_trig_on_off_a
    assert l_ansKey[keywords.cmd_trig_on_off_a][bus.data_key.trig_flash_onoff] == keywords.status_on
    assert l_ansKey[keywords.cmd_trig_on_off_a][bus.data_key.trig_cam_onoff] == keywords.status_on

def test_answTrigOnOffPrrB():
    """ TRIGGER B ON/OFF """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_trig_on_off_b
    cmd['data']= keywords.status_on
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_trig_on_off_b
    assert l_ansKey[keywords.cmd_trig_on_off_b][bus.data_key.trig_flash_onoff] == keywords.status_on
    assert l_ansKey[keywords.cmd_trig_on_off_b][bus.data_key.trig_cam_onoff] == keywords.status_on

def test_answTrigStatusPrrA():
    """ TRIGGER A Allarmi """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_trig_status_a
    cmd['data']= {}
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_trig_status_a
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_1_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_2_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_3_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_4_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_5_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_6_status] == keywords.status_error
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_1_efficiency] == keywords.flash_100
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_2_efficiency] == keywords.flash_100
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_3_efficiency] == keywords.flash_80
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_4_efficiency] == keywords.flash_100
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_5_efficiency] == keywords.flash_100
    assert l_ansKey[keywords.cmd_trig_status_a][keywords.data_trig_flash_6_efficiency] == keywords.flash_0


def test_answTrigStatusPrrB():
    """ TRIGGER B Allarmi """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_trig_status_b
    cmd['data']={}
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_trig_status_b
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_1_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_2_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_3_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_4_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_5_status] == keywords.status_ok
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_6_status] == keywords.status_error
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_1_efficiency] == keywords.flash_100
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_2_efficiency] == keywords.flash_100
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_3_efficiency] == keywords.flash_80
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_4_efficiency] == keywords.flash_100
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_5_efficiency] == keywords.flash_100
    assert l_ansKey[keywords.cmd_trig_status_b][keywords.data_trig_flash_6_efficiency] == keywords.flash_0


def test_answIoStatus():
    """ I/O Allarmi """
    fakebus.fakebus.setLoopBackMode(False)
    cmd={}
    cmd['io_cmd']=keywords.cmd_io
    cmd['data']={}
    pytest.io_comm.queueCmd(cmd)
    l_ansKey= pytest.io_comm.dequeueAnswsers()
    verifyExecution(cmd)
    assert list(l_ansKey.keys())[0] == keywords.cmd_io
    assert l_ansKey[keywords.cmd_io][keywords.data_io_sw_armadio_key]== keywords.status_ko
    assert l_ansKey[keywords.cmd_io][keywords.data_io_ntc_c_key]== 22

" ------ HELPERS ------ "

def verifyExecution(p_cmd):
    """ Verifica le proprietà di pytest.io_comm dopo la tx """
    l_iocommErrors= pytest.io_comm.getErrors()
    l_sentCmds= pytest.io_comm.getSentCommands()
    l_reqCnt= pytest.io_comm.getReqCnt()
    l_missed= pytest.io_comm.getMissed()
    assert  len(l_iocommErrors) == 0
    assert l_reqCnt != 0
    assert l_missed == 0
    assert len(l_sentCmds) != 0
    assert l_sentCmds[-1] == p_cmd['io_cmd']
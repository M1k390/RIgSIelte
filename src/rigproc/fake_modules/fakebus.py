#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
comm bus fake helper
simula gli elementi sul bus
"""

import serial
import logging
import threading
import os
import time
import json

from rigproc.commons import keywords
from rigproc.commons.helper import helper

class FakeBus():
    """
    Simulatore bus 485
    """

    def __init__(self, p_config):
        self.m_config= p_config
        self.m_logger= logging.getLogger('root')
        " serial port per questo modulo "
        self.m_port= serial.Serial()
        self.m_port.port= self.m_config['device']
        self.m_port.baudrate= self.m_config['speed']
        self.m_port.parity= self.m_config['parity']
        self.m_port.timeout= self.m_config['timeout']
        self.m_port.exclusive= True        
        self._openPort()        
        self._launchthread()
        "json con i messaggi già pronti"
        self._decodeMsgs()

    def _decodeMsgs(self):
        " Msg prescritti test com "
        with open(helper.data_file_path('fakebus_messages.json')) as f:
            l_msgs = json.load(f)
        " conversione stringhe double backslash"
        for device in l_msgs['command'].keys():
            for msgs in l_msgs['command'][device].keys():
                v= l_msgs['command'][device][msgs]
                l_msgs['command'][device][msgs]= bytearray.fromhex(v)
        for device in l_msgs['answers'].keys():
            for msgs in l_msgs['answers'][device].keys():
                v= l_msgs['answers'][device][msgs]
                l_msgs['answers'][device][msgs]= bytearray.fromhex(v)
        self.m_msgs= l_msgs

    def isOk(self):
        """ init ok ?"""
        return (self.m_msgs != None) and (self.m_port.isOpen() == True ) \
            and (os.path.exists('/tmp/ttyV0') and os.path.exists('/tmp/ttyV1'))

    def setLoopBackMode(self, p_lo):
        """ setta loop back mode """
        self.m_loMode= p_lo
        self.close()
        " lancio di nuovo "
        self._openPort()
        self._launchthread()

    def close(self):
        """ chiusura operazioni """
        self.m_stop= True
        self.m_thread.join()
        self.m_port.close()
        self.m_logger.info("fake bus thread closed")

    def _openPort(self):
        l_error= False
        self.m_is_open= self.m_port.isOpen()
        if self.m_is_open:
            self.m_logger.warning("Port alredy opened, skipping opening")
        else:
            try:
                self.m_port.open()
            except Exception as e:
                self.m_logger.error("error opening serial port : "  +str(e))
                l_error= True
        self.m_is_open= self.m_port.isOpen()
        self.m_logger.info("Port opened ? : " + str(self.m_is_open))
        self.m_logger.info("Port error ? : " + str(l_error))                

    def _launchthread(self):
        self.m_stop= False
        self.m_thread= threading.Thread(target=self._run)
        self._openPort()
        self.m_thread.start()

    def _run(self):
        """ Runnable, gestione bus, risposte ai comandi"""
        self.m_logger.info("thread started")
        self.m_port.flush()
        while not self.m_stop:
            l_data_in= None
            try:
                l_data_in= self.m_port.readline()
            except:
                pass
            if not l_data_in:
                continue
            self.m_logger.info(l_data_in)
            " Loop back mode "
            if self.m_loMode:
                self.m_port.write(l_data_in)
                self.m_logger.info("loopback answer")
            else:
                " predefined answers "
                self._findAnsw(l_data_in)
                self.m_logger.info("fake answer")
        self.m_logger.info("Exiting fake bus thread...")

    def _findAnsw(self, p_cmd):
        """ 
        Gestione msg di risposta 

        p_cmd: bytearray
            msg come reso da radline
        """
        " MosfTx_p "
        self.m_logger.info(type(p_cmd))
        self.m_logger.info(p_cmd)
        " mosf tx a "
        if p_cmd == self.m_msgs['command'][keywords.name_mtx_a][keywords.cmd_mtx_ver_a]:
            l_answ= self.m_msgs['answers'][keywords.name_mtx_a][keywords.cmd_mtx_ver_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mtx_a][keywords.cmd_mtx_vel_a]:
            l_answ= self.m_msgs['answers'][keywords.name_mtx_a][keywords.cmd_mtx_vel_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mtx_a][keywords.cmd_mtx_on_off_a]:
            l_answ= self.m_msgs['answers'][keywords.name_mtx_a][keywords.cmd_mtx_on_off_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        " mosf tx b"
        if p_cmd == self.m_msgs['command'][keywords.name_mtx_b][keywords.cmd_mtx_ver_b]:
            l_answ= self.m_msgs['answers'][keywords.name_mtx_b][keywords.cmd_mtx_ver_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mtx_b][keywords.cmd_mtx_vel_b]:
            l_answ= self.m_msgs['answers'][keywords.name_mtx_b][keywords.cmd_mtx_vel_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mtx_b][keywords.cmd_mtx_on_off_b]:
            l_answ= self.m_msgs['answers'][keywords.name_mtx_b][keywords.cmd_mtx_on_off_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        "mosf rx a "
        if p_cmd == self.m_msgs['command'][keywords.name_mrx_a][keywords.cmd_mrx_ver_a]:
            l_answ= self.m_msgs['answers'][keywords.name_mrx_a][keywords.cmd_mrx_ver_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mrx_a][keywords.cmd_mrx_wire_t0_a]:
            l_answ= self.m_msgs['answers'][keywords.name_mrx_a][keywords.cmd_mrx_wire_t0_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mrx_a][keywords.cmd_mrx_tmos_a]:
            l_answ= self.m_msgs['answers'][keywords.name_mrx_a][keywords.cmd_mrx_tmos_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mrx_a][keywords.cmd_mrx_wire_data_a]:
            l_answ= self.m_msgs['answers'][keywords.name_mrx_a][keywords.cmd_mrx_wire_data_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        "mosf rx b "
        if p_cmd == self.m_msgs['command'][keywords.name_mrx_b][keywords.cmd_mrx_ver_b]:
            l_answ= self.m_msgs['answers'][keywords.name_mrx_b][keywords.cmd_mrx_ver_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mrx_b][keywords.cmd_mrx_wire_t0_b]:
            l_answ= self.m_msgs['answers'][keywords.name_mrx_b][keywords.cmd_mrx_wire_t0_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mrx_b][keywords.cmd_mrx_tmos_b]:
            l_answ= self.m_msgs['answers'][keywords.name_mrx_b][keywords.cmd_mrx_tmos_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_mrx_b][keywords.cmd_mrx_wire_data_b]:
            l_answ= self.m_msgs['answers'][keywords.name_mrx_b][keywords.cmd_mrx_wire_data_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        "trigger  a "
        if p_cmd == self.m_msgs['command'][keywords.name_trig_a][keywords.cmd_trig_ver_a]:
            l_answ= self.m_msgs['answers'][keywords.name_trig_a][keywords.cmd_trig_ver_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_trig_a][keywords.cmd_trig_setting_a]:
            l_answ= self.m_msgs['answers'][keywords.name_trig_a][keywords.cmd_trig_setting_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_trig_a][keywords.cmd_trig_status_a]:
            l_answ= self.m_msgs['answers'][keywords.name_trig_a][keywords.cmd_trig_status_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_trig_a][keywords.cmd_trig_on_off_a]:
            l_answ= self.m_msgs['answers'][keywords.name_trig_a][keywords.cmd_trig_on_off_a]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        "trigger  b "
        if p_cmd == self.m_msgs['command'][keywords.name_trig_b][keywords.cmd_trig_ver_b]:
            l_answ= self.m_msgs['answers'][keywords.name_trig_b][keywords.cmd_trig_ver_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_trig_b][keywords.cmd_trig_setting_b]:
            l_answ= self.m_msgs['answers'][keywords.name_trig_b][keywords.cmd_trig_setting_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_trig_b][keywords.cmd_trig_status_b]:
            l_answ= self.m_msgs['answers'][keywords.name_trig_b][keywords.cmd_trig_status_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_trig_b][keywords.cmd_trig_on_off_b]:
            l_answ= self.m_msgs['answers'][keywords.name_trig_b][keywords.cmd_trig_on_off_b]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        " io "
        if p_cmd == self.m_msgs['command'][keywords.name_io][keywords.cmd_io_ver]:
            l_answ= self.m_msgs['answers'][keywords.name_io][keywords.cmd_io_ver]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_io][keywords.cmd_io]:
            l_answ= self.m_msgs['answers'][keywords.name_io][keywords.cmd_io]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        if p_cmd == self.m_msgs['command'][keywords.name_io][keywords.cmd_io_test_batt]:
            l_answ= self.m_msgs['answers'][keywords.name_io][keywords.cmd_io_test_batt]
            self.m_logger.debug("sending back " + str(l_answ))
            self.m_port.write(l_answ)
            return
        " default "
        self.m_logger.info("sent back default ")
        self.m_port.write(p_cmd)

" ------------- INIT SYSTEM ---------- "

" Conf moduli esterni "
modules_conf= {
        "device": "/tmp/ttyV1",
        "speed": 9600,
        "timeout": 0.5,
        "parity": serial.PARITY_NONE,
        "cts":False,
        "timeoutAnswer":0.3,
        "stopbits":2
}
socat_command= "socat -d -d pty,raw,echo=0,link=/tmp/ttyV0  pty,raw,echo=0,link=/tmp/ttyV1 &"

socat_thread= None
fakebus= None

def catPorts():
    """ Attivazione loop seriali"""
    if not os.path.isfile('/tmp/ttyV0') or not os.path.isfile('/tmp/ttyV0'):
        os.system(socat_command)

def initFakeSerialBus():
    global socat_thread
    global fakebus
    socat_thread= threading.Thread(target= catPorts)
    socat_thread.start()    
    " check seriali create "
    while not os.path.exists('/tmp/ttyV0') or not os.path.exists('/tmp/ttyV1'):
        time.sleep(1)    
    fakebus= FakeBus(modules_conf)
    fakebus.setLoopBackMode(False)

def closeFakeSerialBus():
    os.system('killall socat')
    #pytest.socat_thread.join()
    global socat_thread
    global fakebus
    socat_thread.join()
    while os.path.exists('/tmp/ttyV0') : pass
    while os.path.exists('/tmp/ttyV1') : pass
    assert os.path.exists('/tmp/ttyV0') == False
    assert os.path.exists('/tmp/ttyV1') == False
    #pytest.fakebus.close()
    fakebus.close()
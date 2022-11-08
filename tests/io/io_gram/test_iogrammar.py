#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_iogrammar.py
Testing grammatica
"""

import pytest
import logging
from rigproc.io import  iogrammar
from rigproc.commons import keywords
from rigproc.params import bus
import pdb
import copy

g_cmd_vers= bytearray(b'\x02\x40\x42\x60\x30\x30\x30\x30\x50\xF2\x03\x0D\x0A')
g_cmd_velo= bytearray(b'\x02\x40\x42\x61\x30\x30\x30\x30\x50\xF3\x03\x0D\x0A')
g_answ_vers=  bytearray(b'\x02\x42\x40\x60\x30\x31\x32\x30\x50\xF5\x03\x0D\x0A')
g_answ_velo=  bytearray(b'\x02\x42\x40\x61\x30\x31\x32\x30\x50\xF6\x03\x0D\x0A')
g_sftx_garb=  bytearray(b'\x54\x0d\x0a') + g_answ_vers
g_sftx_2 = g_answ_vers + bytearray(b'\x0d\x0a')+ g_answ_velo
g_sftx_3 = g_answ_vers + bytearray(b'\x03\x0d\x0a')+ g_answ_velo
g_sftx_4 = g_answ_vers + bytearray(b'\x73\xC2\x50\x03\x0D\x03\x0d\x0a')+ g_answ_velo

g_answ_vers_data={
    'valid': True,
    'src': bus.module.mosf_tx_a,
    'dest': bus.module.videoserver,
    'data_size': 4,
    'io_cmd': bus.cmd.mtx_ver_a,
    'msg': g_answ_vers,
    'data': [48, 49, 50, 48],
    'pos': 10
    }

g_answ_velo_data={
    'valid': True,
    'src': bus.module.mosf_tx_a,
    'dest': bus.module.videoserver,
    'data_size': 4,
    'io_cmd': bus.cmd.mtx_vel_a,
    'msg': g_answ_velo,
    'data': [48, 49, 50, 48],
    'pos': 10
    }


""" -- INNER FUNCTIONS --- """

def test_start():
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_start= l_gram._start(bus.module.mosf_tx_a)
    assert l_start == bytearray([2,64,66])


def test_close():
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_msg= l_gram._close()
    assert l_msg== bytearray([3,13,10])

def test_recordsize():
    global g_sftx
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_pos= l_gram._checkRecordsize(g_answ_vers[:-3])
    assert l_pos == len(g_answ_vers)-3


def test_crc():
    global g_sftx
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_crc= l_gram._crc(g_answ_vers[:-3])
    assert l_crc == int(g_answ_vers[-4])


def test_decode():
    global g_sftx
    global g_answ_vers_data
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_out= l_gram._decode(g_answ_vers[:-3])
    assert l_out == g_answ_vers_data

""" -- RX  --- """

def test_findmsg():
    global g_sftx
    global g_sftxData
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_out= l_gram.findMsg(g_sftx_garb)
    assert (l_out[0] == g_answ_vers_data)


def test_findmsg2():
    l_veloData= g_answ_velo_data.copy()
    l_versData= g_answ_vers_data.copy()
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_out= l_gram.findMsg(g_sftx_2)           
    assert len(l_out) == 2
    assert (l_out[0] == l_versData)
    assert (l_out[1] == l_veloData)


def test_findmsg3():
    l_veloData= g_answ_velo_data.copy()
    l_versData= g_answ_vers_data.copy()
    l_bufIn = copy.deepcopy(g_sftx_3)
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_out= l_gram.findMsg(l_bufIn)
    assert len(l_out) == 2
    assert (l_out[0] == l_versData)
    assert (l_out[1] == l_veloData)
    assert len(l_bufIn) == 0

def test_findmsg4():
    l_veloData= g_answ_velo_data.copy()
    l_versData= g_answ_vers_data.copy()
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_bufIn = copy.deepcopy(g_sftx_4)
    l_out= l_gram.findMsg(l_bufIn)
    assert len(l_out) == 2
    assert (l_out[0] == l_versData)
    assert (l_out[1] == l_veloData)
    assert len(l_bufIn) == 0        

""" -- TX -- """

def test_build():
    global g_sftx
    global g_sftxData
    l_gram= iogrammar.IoGrammar(logging.getLogger())
    l_versP= l_gram.buildCommand(bus.module.mosf_tx_a,bus.cmd.mtx_vel_a,b'0000')
    assert l_versP == g_cmd_velo

""" Interferenze """

def test_malformed_1():
    l_gram = iogrammar.IoGrammar(logging.getLogger())
    l_malf_msg = [
        0x6e, 0x03, 0x0d, 0x0a
    ]
    l_buf = bytearray(l_malf_msg)
    l_msgs = l_gram.findMsg(l_buf)
    assert len(l_msgs) == 0

def test_malformed_2():
    l_gram = iogrammar.IoGrammar(logging.getLogger())
    l_malf_msg = [
        0x6e, 0x03, 0x0d, 0x0a, 
        0x02, 0x41, 0x40, 0x6b, 0x34, 0x3f, 0x32, 0x39, 0x50, 0x9a, 0x03, 0x0d, 0x0a
    ]
    l_buf = bytearray(l_malf_msg)
    l_msgs = l_gram.findMsg(l_buf)
    assert len(l_msgs) == 1
    assert l_msgs == [{
        'valid': True, 
        'src': 'io', 
        'dest': 'videoserver', 
        'io_cmd': 'io', 
        'data_size': 4, 
        'data': [52, 63, 50, 57], 
        'pos': 10, 
        'msg': bytearray(b'\x02A@k4?29P\x9a\x03\r\n')
    }]
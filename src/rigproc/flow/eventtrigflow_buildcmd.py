#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trig flow helper per il build dei comandi bus
"""

from rigproc.commons import keywords
from rigproc.params import internal


def  _buildCmdMosfTxAVer(p_flow, p_data= None):
    " Creazione richeista versione mtx a"
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mtx_ver_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd


def  _buildCmdMosfTxBVer(p_flow, p_data= None):
    " Creazione richeista versione mtx b"
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mtx_ver_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdTrainSpeedA(p_flow, p_data= None):
    """
    Creazione richiesta info Train speed
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mtx_vel_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdTrainSpeedB(p_flow, p_data= None):
    """
    Creazione richiesta info Train speed
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mtx_vel_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def  _buildCmdMosfTxAOff(p_flow, p_data= None):
    """ Creazione richeista off modualo tx a 
    p_data on, off
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mtx_on_off_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= p_data
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def  _buildCmdMosfTxBOff(p_flow, p_data= None):
    """ Creazione richeista off modualo tx b
    p_data on, off
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mtx_on_off_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= p_data
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdMosfRxAVer(p_flow, p_data= None):
    """
    Creazione richeista versione mtx a
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mrx_ver_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdMosfRxBVer(p_flow, p_data= None):
    """
    Creazione richeista versione mtx a
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mrx_ver_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdMosfRxATmos(p_flow, p_data= None):
    """
    Creazione richeista versione mtx a
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mrx_tmos_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= p_data
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdMosfRxBTmos(p_flow, p_data= None):
    """
    Creazione richeista versione mtx a
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mrx_tmos_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= p_data
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdWireT0A(p_flow, p_data= None):
    """
    Creazione richiesta info altezza filo T0
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mrx_wire_t0_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd


def _buildCmdWireT0B(p_flow, p_data= None):
    """
    Creazione richiesta info altezza filo T0
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mrx_wire_t0_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdTriggerVerA(p_flow, p_data= None):
    """
    Creazione richiesta versione trigger A
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_trig_ver_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdTriggerVerB(p_flow, p_data= None):
    """
    Creazione richiesta versione trigger B
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_trig_ver_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdTriggerAOff(p_flow, p_data= None):
    """
    Creazione richiesta spegnimento trigger a    
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_trig_on_off_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= p_data
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdTriggerBOff(p_flow, p_data= None):
    """
    Creazione richiesta spegnimento trigger b
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_trig_on_off_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= p_data
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdTriggerAStatus(p_flow, p_data= None):
    """
    Creazione richiesta diagnosi trigger A
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_trig_status_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdTriggerBStatus(p_flow, p_data= None):
    """
    Creazione richiesta diagnosi trigger B
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_trig_status_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdMosfDataA(p_flow, p_data= None):
    """
    Comando mosf data ready
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mrx_wire_data_a
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdIOVer(p_flow, p_data= None):
    """
    Creazione richiesta versione IO
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_io_ver
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= p_data
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdMosfDataB(p_flow, p_data= None):
    """
    Comando mosf data ready
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_mrx_wire_data_b
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdDiagIo(p_flow, p_data= None):
    """
    Comando richiesta diagnosi
    No data required
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_io
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

def _buildCmdPipeEnded(p_flow):
    """Comando pipe terminata"""
    l_cmd= {}    
    l_cmd[internal.cmd_key.says]=keywords.info_pipe_ended
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    l_cmd[internal.cmd_key.data]= ''
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.trig_flow
    return l_cmd

" ------ ACTIONS ----- "

def _buildActionStartupDone():
    l_cmd={}
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.action
    l_cmd[internal.cmd_key.action_type]= keywords.action_startup_done
    return l_cmd

def _buildActionShutDownFlow():
    """ Building system shutdown request """
    l_cmd={}
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.action
    l_cmd[internal.cmd_key.action_type]= keywords.action_shut_down_flow
    return l_cmd

def _buildActionShutDown():
    """ Building system shutdown request """
    l_cmd={}
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.action
    l_cmd[internal.cmd_key.action_type]= keywords.action_shut_down
    return l_cmd

def _buildActionFlowShutdownAborted():
    """ Building shutdown aborted """
    l_cmd={}
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.action
    l_cmd[internal.cmd_key.action_type]= keywords.action_shut_down_aborted_flow
    return l_cmd

def _buildActionPausePeriodic():
    """ Building shutdown aborted """
    l_cmd={}
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.action
    l_cmd[internal.cmd_key.action_type]= keywords.action_pause_periodic
    return l_cmd

def _buildActionResumePeriodic():
    """ Building shutdown aborted """
    l_cmd={}
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.action
    l_cmd[internal.cmd_key.action_type]= 'resume_periodic'
    return l_cmd

def _buildCmdFlowWakeUp(p_flow):
    """ Richiesta wake up flow """
    l_cmd= {}
    l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.action
    l_cmd[internal.cmd_key.action_type]= keywords.action_wake_up
    l_cmd[internal.cmd_key.trigflow_instance]= p_flow
    return l_cmd

" ----- STOP ----- "

def _buildIoCmdStop(p_flow, p_data= None):
    """
    Comando richiesta uscita
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_stop
    l_cmd[internal.cmd_key.data]= b'0000'
    return l_cmd

def _buildIoCmdRestart(p_flow, p_data=None):
    """
    Comando richiesta riavvio
    """
    l_cmd={}
    l_cmd[internal.cmd_key.io_cmd]= keywords.cmd_restart
    l_cmd[internal.cmd_key.data]= b'0000'
    return l_cmd
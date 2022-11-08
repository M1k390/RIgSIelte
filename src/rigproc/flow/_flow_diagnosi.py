#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnosi
"""

import os
from rigproc.commons import keywords
from rigproc.commons.wrappers import wrapkeys
from rigproc.flow import eventtrigflow_buildcmd as buildcmd
from rigproc.commons.helper import helper
from rigproc.params import bus, general, internal, conf_values
from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI


def _buildFlowDiagnosis(self):
    """ Tasklist builder per richiesta diagnosi """
    self.m_taskAll= {
        **self.m_taskBegin,
        **self.m_taskDiagnostica,
        **self.m_taskTopicDiag,
        **self.m_taskClosePipe
        }
    " indicizzazione taskAll entries"
    l_idx= 0
    for task in self.m_taskAll:
        self.m_taskAll[task]['id']= l_idx
        l_idx += 1
    " lista funzioni registrate realtive ai task "
    self.m_taskFuncList={
        'id': 0,
        'tasks':[self._prepareWork,
                self._workDiagMosfTxA,
                self._workDiagMosfTxAAnswer,
                self._workDiagMosfRxA,
                self._workDiagMosfRxAAnswer,
                self._workDiagMosfTxB,
                self._workDiagMosfTxBAnswer,
                self._workDiagMosfRxB,
                self._workDiagMosfRxBAnswer,
                self._workDiagTriggerAStatus,
                self._workDiagTriggerAStatusAnswer,
                self._workDiagTriggerBStatus,
                self._workDiagTriggerBStatusAnswer,
                self._workDiagIo,
                self._workDiagIoAnswer,
                self._checkTrigAVer,
                self._checkTrigAVerAnswer,
                self._checkTrigBVer,
                self._checkTrigBVerAnswer,
                self._workIoVer,
                self._workIoVerAnswer,
                self._workTopicDiagnosis,
                self._workTopicDiagnosisAnswer,
                self._closePipe],
        'continue': True
        }


def _workDiagMosfTxA(self, p_data= None):
    """
    Diag
    """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfTxAVer(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workDiagMosfTxAAnswer(self, p_data= None):
    """ Analisi risposta dal modulo mosf tx  pari al comando di stato """   
    if p_data != None:
        self.m_data[keywords.evdata_mosfTXp_status]= keywords.status_ok
    else:
        self.m_data[keywords.evdata_mosfTXp_status]= keywords.status_ko
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_p,
        keywords.mosf_tx_p,
        self.m_data[keywords.evdata_mosfTXp_status]
    )
    l_vers= wrapkeys.getValue(p_data, keywords.data_mtx_vers_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_p,
        keywords.data_mtx_vers_key,
        l_vers
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workDiagMosfRxA(self, p_data= None):
    """
    Diag
    """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfRxAVer(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workDiagMosfRxAAnswer(self, p_data= None):
    """ Analisi risposta dal modulo mosf rx pari al comando di stato """
    if p_data != None:
        self.m_data[keywords.evdata_mosfRXp_status]= keywords.status_ok
    else:
        self.m_data[keywords.evdata_mosfRXp_status]= keywords.status_ko
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_p,
        keywords.mosf_rx_p,
        self.m_data[keywords.evdata_mosfRXp_status]
    )
    l_vers= wrapkeys.getValue(p_data, keywords.data_mrx_vers_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_p,
        keywords.data_mrx_vers_key,
        l_vers
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workDiagMosfTxB(self, p_data= None):
    """
    Diag
    """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfTxBVer(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workDiagMosfTxBAnswer(self, p_data= None):
    """ Analisi risposta dal modulo mosf tx dispari al comando di stato """
    if p_data != None:
        self.m_data[keywords.evdata_mosfTXd_status]= keywords.status_ok
    else:
        self.m_data[keywords.evdata_mosfTXd_status]= keywords.status_ko
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_d,
        keywords.mosf_tx_d,
        self.m_data[keywords.evdata_mosfTXd_status]
    )
    l_vers= wrapkeys.getValue(p_data, keywords.data_mtx_vers_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_d,
        keywords.data_mtx_vers_key,
        l_vers
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workDiagMosfRxB(self, p_data= None):
    """
    Diag
    """
    l_bin_conf= wrapkeys.getValueDefault(self.m_data, conf_values.binario.doppio, internal.flow_data.conf_binario)
    if l_bin_conf == keywords.binario_conf_doppio:
        # Binario doppio
        self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfRxBVer(self))
        self.m_taskFuncList['continue']= False
    else:
        # Binario singolo
        " non inviare richiesta (modulo assente) "
        self.m_taskFuncList['continue']= True
    self._incTaskId()
    return True


def _workDiagMosfRxBAnswer(self, p_data= None):
    " Analisi risposta dal modulo mosf rx dispari al comando di stato "
    l_bin_conf= wrapkeys.getValueDefault(self.m_data, conf_values.binario.doppio, internal.flow_data.conf_binario)
    if l_bin_conf == keywords.binario_conf_doppio:
        # Binario doppio
        if p_data != None:
            self.m_data[keywords.evdata_mosfRXd_status]= keywords.status_ok
        else:
            self.m_data[keywords.evdata_mosfRXd_status]= keywords.status_ko
        l_vers= wrapkeys.getValue(p_data, keywords.data_mrx_vers_key)
    else:
        # Binario singolo
        " inserisci valori di default "
        self.m_data[keywords.evdata_mosfRXd_status]= keywords.dato_non_disp
        l_vers= keywords.dato_non_disp
    # Update Redis status
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_d,
        keywords.mosf_rx_d,
        self.m_data[keywords.evdata_mosfRXd_status])
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_d,
        keywords.data_mrx_vers_key,
        l_vers
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workDiagTriggerAStatus(self, p_data= None):
    """
    Diag
    """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTriggerAStatus(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workDiagTriggerAStatusAnswer(self, p_data= None):
    """
    Analisi risposta ricevuta dal trigger dispari al comando stato allarmi
    """
    if p_data != None:
        self.m_data[keywords.evdata_triggerA_status]= keywords.status_ok
    else:
        self.m_data[keywords.evdata_triggerA_status]= keywords.status_ko    
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.trigger_p,\
        self.m_data[keywords.evdata_triggerA_status]
    )
    l_flash= {}
    " flash 1 status "
    l_flash[keywords.data_trig_flash_1_status] = wrapkeys.getValue(p_data, keywords.data_trig_flash_1_status)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_1_status,\
        l_flash[keywords.data_trig_flash_1_status]
    )
    " flash 2 status "
    l_flash[keywords.data_trig_flash_2_status]= wrapkeys.getValue(p_data, keywords.data_trig_flash_2_status)    
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_2_status,\
        l_flash[keywords.data_trig_flash_2_status]
    )
    " flash 3 status "
    l_flash[keywords.data_trig_flash_3_status]= wrapkeys.getValue(p_data, keywords.data_trig_flash_3_status)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_3_status,\
        l_flash[keywords.data_trig_flash_3_status]
    )
    " flash 4 status "
    l_flash[keywords.data_trig_flash_4_status]= wrapkeys.getValue(p_data, keywords.data_trig_flash_4_status)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_4_status,\
        l_flash[keywords.data_trig_flash_4_status]
    )
    " flash 5 status "
    l_flash[keywords.data_trig_flash_5_status]= wrapkeys.getValue(p_data, keywords.data_trig_flash_5_status)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_5_status,\
        l_flash[keywords.data_trig_flash_5_status]
    )
    " flash 6 status "
    l_flash[keywords.data_trig_flash_6_status]= wrapkeys.getValue(p_data, keywords.data_trig_flash_6_status)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_6_status,\
        l_flash[keywords.data_trig_flash_6_status]
    )
    " flash 1 efficiency "
    l_flash[keywords.data_trig_flash_1_efficiency]= wrapkeys.getValue(p_data, keywords.data_trig_flash_1_efficiency)  
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_1_efficiency,\
        l_flash[keywords.data_trig_flash_1_efficiency]
    )  
    " flash 2 efficiency "
    l_flash[keywords.data_trig_flash_2_efficiency]= wrapkeys.getValue(p_data, keywords.data_trig_flash_2_efficiency)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_2_efficiency,\
        l_flash[keywords.data_trig_flash_2_efficiency]
    )  
    " flash 3 efficiency "
    l_flash[keywords.data_trig_flash_3_efficiency]= wrapkeys.getValue(p_data, keywords.data_trig_flash_3_efficiency)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_3_efficiency,\
        l_flash[keywords.data_trig_flash_3_efficiency]
    )  
    " flash 4 efficiency "
    l_flash[keywords.data_trig_flash_4_efficiency]= wrapkeys.getValue(p_data, keywords.data_trig_flash_4_efficiency)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_4_efficiency,\
        l_flash[keywords.data_trig_flash_4_efficiency]
    )  
    " flash 5 efficiency "
    l_flash[keywords.data_trig_flash_5_efficiency]= wrapkeys.getValue(p_data, keywords.data_trig_flash_5_efficiency)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_5_efficiency,\
        l_flash[keywords.data_trig_flash_5_efficiency]
    )  
    " flash 6 efficiency "
    l_flash[keywords.data_trig_flash_6_efficiency]= wrapkeys.getValue(p_data, keywords.data_trig_flash_6_efficiency)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,\
        keywords.data_trig_flash_6_efficiency,\
        l_flash[keywords.data_trig_flash_6_efficiency]
    )  
    " "
    self.m_data[keywords.evdata_flash_A]= l_flash    
    " "
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workDiagTriggerBStatus(self, p_data= None):
    """
    Diag
    """
    l_bin_conf= wrapkeys.getValueDefault(self.m_data, conf_values.binario.doppio, internal.flow_data.conf_binario)
    if l_bin_conf == keywords.binario_conf_doppio:
        # Binario doppio
        self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTriggerBStatus(self))
        self.m_taskFuncList['continue']= False
    else:
        # Binario singolo
        self.m_taskFuncList['continue']= True
    self._incTaskId()
    return True

def _workDiagTriggerBStatusAnswer(self, p_data= None):
    """
    Analisi risposta ricevuta dal trigger dispari al comando stato allarmi
    """
    l_bin_conf= wrapkeys.getValueDefault(self.m_data, conf_values.binario.doppio, internal.flow_data.conf_binario)
    if l_bin_conf == keywords.binario_conf_doppio:
        # Binario doppio
        if p_data != None:
            self.m_data[keywords.evdata_triggerB_status]= keywords.status_ok
        else:
            self.m_data[keywords.evdata_triggerB_status]= keywords.status_ko    
        l_flash= {}
        " flash 1 status "
        l_flash[keywords.data_trig_flash_1_status] = wrapkeys.getValue(p_data, keywords.data_trig_flash_1_status)
        " flash 2 status "
        l_flash[keywords.data_trig_flash_2_status] = wrapkeys.getValue(p_data, keywords.data_trig_flash_2_status)
        " flash 3 status "
        l_flash[keywords.data_trig_flash_3_status] = wrapkeys.getValue(p_data, keywords.data_trig_flash_3_status)
        " flash 4 status "
        l_flash[keywords.data_trig_flash_4_status] = wrapkeys.getValue(p_data, keywords.data_trig_flash_4_status)
        " flash 5 status "
        l_flash[keywords.data_trig_flash_5_status] = wrapkeys.getValue(p_data, keywords.data_trig_flash_5_status)
        " flash 6 status "
        l_flash[keywords.data_trig_flash_6_status] = wrapkeys.getValue(p_data, keywords.data_trig_flash_6_status)
        " flash 1 efficiency "
        l_flash[keywords.data_trig_flash_1_efficiency] = wrapkeys.getValue(p_data, keywords.data_trig_flash_1_efficiency)
        " flash 2 efficiency "
        l_flash[keywords.data_trig_flash_2_efficiency] = wrapkeys.getValue(p_data, keywords.data_trig_flash_2_efficiency)
        " flash 3 efficiency "
        l_flash[keywords.data_trig_flash_3_efficiency] = wrapkeys.getValue(p_data, keywords.data_trig_flash_3_efficiency)
        " flash 4 efficiency "
        l_flash[keywords.data_trig_flash_4_efficiency] = wrapkeys.getValue(p_data, keywords.data_trig_flash_4_efficiency)
        " flash 5 efficiency "
        l_flash[keywords.data_trig_flash_5_efficiency] = wrapkeys.getValue(p_data, keywords.data_trig_flash_5_efficiency)
        " flash 6 efficiency "
        l_flash[keywords.data_trig_flash_6_efficiency] = wrapkeys.getValue(p_data, keywords.data_trig_flash_6_efficiency)
        " "
        self.m_data[keywords.evdata_flash_B]= l_flash    
        ""
    else:
        # Binario singolo
        " Inserisco valori di default "
        self.m_data[keywords.evdata_triggerB_status] = keywords.dato_non_disp
        l_flash= {
            keywords.data_trig_flash_1_status: keywords.dato_non_disp,
            keywords.data_trig_flash_1_efficiency: keywords.dato_non_disp,
            keywords.data_trig_flash_2_status: keywords.dato_non_disp,
            keywords.data_trig_flash_2_efficiency: keywords.dato_non_disp,
            keywords.data_trig_flash_3_status: keywords.dato_non_disp,
            keywords.data_trig_flash_3_efficiency: keywords.dato_non_disp,
            keywords.data_trig_flash_4_status: keywords.dato_non_disp,
            keywords.data_trig_flash_4_efficiency: keywords.dato_non_disp,
            keywords.data_trig_flash_5_status: keywords.dato_non_disp,
            keywords.data_trig_flash_5_efficiency: keywords.dato_non_disp,
            keywords.data_trig_flash_6_status: keywords.dato_non_disp,
            keywords.data_trig_flash_6_efficiency: keywords.dato_non_disp,
        }
        self.m_data[keywords.evdata_flash_B]= l_flash
    # Update Redis status
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.trigger_d,\
        self.m_data[keywords.evdata_triggerB_status]
    )
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_1_status,\
        l_flash[keywords.data_trig_flash_1_status]
    )    
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_2_status,\
        l_flash[keywords.data_trig_flash_2_status]
    )
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_3_status,\
        l_flash[keywords.data_trig_flash_3_status]
    )
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_4_status,\
        l_flash[keywords.data_trig_flash_4_status]
    )
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_5_status,\
        l_flash[keywords.data_trig_flash_5_status]
    )
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_6_status,\
        l_flash[keywords.data_trig_flash_6_status]
    )  
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_1_efficiency,\
        l_flash[keywords.data_trig_flash_1_efficiency]
    )  
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_2_efficiency,\
        l_flash[keywords.data_trig_flash_2_efficiency]
    )  
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_3_efficiency,\
        l_flash[keywords.data_trig_flash_3_efficiency]
    )  
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_4_efficiency,\
        l_flash[keywords.data_trig_flash_4_efficiency]
    )  
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_5_efficiency,\
        l_flash[keywords.data_trig_flash_5_efficiency]
    )  
    get_redisI().updateStatusInfo(
        keywords.trigger_d,\
        keywords.data_trig_flash_6_efficiency,\
        l_flash[keywords.data_trig_flash_6_efficiency]
    )  
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workDiagIo(self, p_data= None):
    """
    Diag
    """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdDiagIo(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workDiagIoAnswer(self, p_data= None):
    """
    Analisi risposta del modulo IO al comando di stato
    """
    if p_data != None:
        self.m_data[keywords.evdata_io]= keywords.status_ok
    else: 
        self.m_data[keywords.evdata_io]= keywords.status_ko
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.io,\
        self.m_data[keywords.evdata_io]
        )

    " Batteria presente "
    self.m_data[keywords.evdata_battery] = wrapkeys.getValue(p_data, keywords.data_io_alim_batt_key)
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_alim_batt_key,\
        self.m_data[keywords.evdata_battery]
    )

    " Alimentazione 24vcc presente "
    self.m_data[keywords.evdata_24vcc] = wrapkeys.getValue(p_data, keywords.data_io_alim_24_key)
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_alim_24_key,\
        self.m_data[keywords.evdata_24vcc]
    )

    " IVIP tipo di alimentazione "
    l_ivip=''
    if self.m_data[keywords.evdata_24vcc] ==  keywords.status_ok :
        l_ivip= keywords.alim_alim
    else:
        l_ivip= keywords.alim_batt
    self.m_data[keywords.evdata_IVIP_power]= l_ivip
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_IVIP_power_key,\
        self.m_data[keywords.evdata_IVIP_power]
    )
    " Switch prr pari/dispari "
    self.m_data[keywords.evdata_switch_prrA] = wrapkeys.getValue(p_data, keywords.data_io_sw_prr_pari_key)   
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_switch_prr_p_key,\
        self.m_data[keywords.evdata_switch_prrA]
    ) 
    self.m_data[keywords.evdata_switch_prrB] = wrapkeys.getValue(p_data, keywords.data_io_sw_prr_dispari_key)
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_switch_prr_d_key,\
        self.m_data[keywords.evdata_switch_prrB]
    )
    " LDC pari/dispari "
    self.m_data[keywords.evdata_ldc_prrA] = wrapkeys.getValue(p_data, keywords.data_io_rv_pari_key )
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_ldc_p_key,\
        self.m_data[keywords.evdata_ldc_prrA]
    )
    self.m_data[keywords.evdata_ldc_prrB] = wrapkeys.getValue(p_data, keywords.data_io_rv_dispari_key )
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_ldc_d_key,\
        self.m_data[keywords.evdata_ldc_prrB]
    )
    " Porte armadio aperte "
    self.m_data[keywords.evdata_door_opened] =  wrapkeys.getValue(p_data, keywords.data_io_sw_armadio_key)
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_doors_key,\
        self.m_data[keywords.evdata_door_opened])
    " Errore RIP "
    self.m_data[internal.flow_data.rip_status] =  wrapkeys.getValue(p_data, bus.data_key.io_rip_status)
    get_redisI().updateStatusInfo(
        keywords.io,\
        bus.data_key.io_rip_status,\
        self.m_data[internal.flow_data.rip_status])
    " Ntc "
    self.m_data[internal.flow_data.io_ntc] = wrapkeys.getValue(p_data, bus.data_key.io_ntc_c)
    get_redisI().updateStatusInfo(
        bus.module.io,
        bus.data_key.io_ntc_c,
        self.m_data[internal.flow_data.io_ntc]
    )
    # Update temperatures history
    l_cpu_temp = helper.get_cpu_temperature()
    if l_cpu_temp is None:
        l_cpu_temp = general.dato_non_disp
    get_redisI().add_temp_measure(self.m_data[internal.flow_data.io_ntc], l_cpu_temp)
    " Alim batt "
    self.m_data[internal.flow_data.alim_batt] = wrapkeys.getValue(p_data, bus.data_key.io_alim_batt)
    get_redisI().updateStatusInfo(
        bus.module.io,
        bus.data_key.io_alim_batt,
        self.m_data[internal.flow_data.alim_batt]
    )
    
    ""
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


" TRIGGER "

def _checkTrigAVer(self, p_data=None):
    """ TRIGGER A Versione """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTriggerVerA(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkTrigAVerAnswer(self, p_data=None):
    l_ver= wrapkeys.getValue(p_data, keywords.data_trig_vers_key)
    l_flash_onoff = wrapkeys.getValue(p_data, bus.data_key.trig_flash_onoff)
    l_cam_onoff = wrapkeys.getValue(p_data, bus.data_key.trig_cam_onoff)
    get_redisI().updateStatusInfo(
        keywords.trigger_p,
        keywords.data_trig_vers_key,
        l_ver
    )
    get_redisI().updateStatusInfo(
        bus.module.trigger_a,
        bus.data_key.trig_flash_onoff,
        l_flash_onoff
    )
    get_redisI().updateStatusInfo(
        bus.module.trigger_a,
        bus.data_key.trig_cam_onoff,
        l_cam_onoff
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _checkTrigBVer(self, p_data=None):
    """ TRIGGER B Versione """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTriggerVerB(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkTrigBVerAnswer(self, p_data=None):
    l_ver= wrapkeys.getValue(p_data, keywords.data_trig_vers_key)
    l_flash_onoff = wrapkeys.getValue(p_data, bus.data_key.trig_flash_onoff)
    l_cam_onoff = wrapkeys.getValue(p_data, bus.data_key.trig_cam_onoff)
    get_redisI().updateStatusInfo(
        keywords.trigger_d,
        keywords.data_trig_vers_key,
        l_ver
    )
    get_redisI().updateStatusInfo(
        bus.module.trigger_b,
        bus.data_key.trig_flash_onoff,
        l_flash_onoff
    )
    get_redisI().updateStatusInfo(
        bus.module.trigger_b,
        bus.data_key.trig_cam_onoff,
        l_cam_onoff
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _workIoVer(self, p_data= None):
    """ Comunico lo stato dei led di alimentazione dopo la diagnostica (io_ver)"""
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdIOVer(self))
    #
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workIoVerAnswer(self, p_data= None):
    """ Attesa risposta comando setting led alimentazione (io_ver) """
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_vers_key,\
        wrapkeys.getValue(p_data, keywords.data_io_vers_key)
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workTopicDiagnosis(self, p_data= None):
    """
    Organizzazione dati per topic diagnosi
    """
    if self.m_flow == keywords.flow_type_diagnosis:
        l_jsonEvt= self.m_jmodel.getDiagModel(self.m_data)
    else:
        self.m_logger.error("flow type not managed for this task")
        self.m_error= True

    self.m_data[keywords.evdata_topic_evt_diag]= {
        internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
        internal.cmd_key.topic_type:'trigger_topic_diag',
        internal.cmd_key.topic: keywords.topic_diag_rip_to_stg,
        internal.cmd_key.evt_name: self.m_data[keywords.evdata_evt_name],
        internal.cmd_key.json: l_jsonEvt,
        internal.cmd_key.trigflow_instance: self
        }
    self.m_logger.info("Json diag on trigger to broker [topic]: "
            + self.m_data[keywords.evdata_topic_evt_diag][internal.cmd_key.topic])
    # Check rete
    # TODO inserire nella configurazione l'indirizzo del broker STG
    l_server_ip= 'N/A'
    l_server_online= True
    if l_server_online:
        self.m_logger.debug(f'Broker online at {l_server_ip}')
        self.m_mainCore['cmd_q'].put(self.m_data[keywords.evdata_topic_evt_diag])
    else:
        self.m_logger.error(f'Connection error, broker not online: could not reach {l_server_ip}')            
        self.m_recovering= True
        self.m_error= True            
        # TODO tirare un eccezione!
        self._incTaskId()
        self.m_taskFuncList['continue']= True
        return True     
    #
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workTopicDiagnosisAnswer(self, p_data= None):
    """
    Verifica corretta trasmissione topic diagnosi
    """
    if not p_data:
        self.m_logger.error("Got empty data to parse")
        self.m_recovering= True
        self.m_error= True
    elif wrapkeys.getValue(p_data, keywords.topic_cmd_key) == keywords.status_ko:
        self.m_logger.error("Got KO ")
        self.m_recovering= True
        self.m_error= True
    elif wrapkeys.getValue(p_data, keywords.topic_cmd_key) == keywords.status_ok:
        self.m_logger.info("Got Ok ")
    else:
        self.m_logger.error("Unknown data to parse")
        self.m_recovering= True
        self.m_error= True
    " si prosegue lo stesso "
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True
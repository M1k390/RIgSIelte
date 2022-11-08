#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
shutdown task per il flow
"""

import threading
import time

from rigproc.commons.config import get_config
from rigproc.commons import keywords
from rigproc.flow import eventtrigflow_buildcmd as buildcmd
from rigproc.commons.wrappers import wrapkeys

from rigproc.params import bus, conf_values, general


def _buildFlowShutDown(self):
    """Flow builder richieta di shutdown 
    
        - Disabilito i moduli 
        - Attendo t_alim
        - controllo se l'alimentazione è tornata
            - si riaccendo i moduli
            - no controllo se ci sono acq in progress
                - attendo fine acq e mi spengo fisicamente
        NOTA: se alim è tornata creo un altro trig flow denominato cancel shutdown
    """
    self.m_taskAll= {
        **self.m_taskBegin,
        **self.m_taskBusOff,        
        **self.m_taskWait,
        **self.m_taskDiagReduced,
        **self.m_taskEvaluateActions,        
        **self.m_taskShutDown,
        **self.m_taskClosePipe
        }
    " indicizzazione taskAll entries"
    l_idx= 0
    for task in self.m_taskAll:
        self.m_taskAll[task]['id']= l_idx
        l_idx += 1
    " lista funzioni registrate realtive ai task "
    self.m_taskFuncList= {
        'id': 0,
        'tasks':[self._prepareWork,
                 self._workMosfTXp_off,
                 self._workMosfTXp_onoff_answer,
                 self._workMosfTXd_off,
                 self._workMosfTXd_onoff_answer,
                 self._workTrigp_off,
                 self._workTrigp_onoff_answer,
                 self._workTrigd_off,
                 self._workTrigd_onoff_answer,
                 self._workIoVer,
                 self._workIoVerAnswer,
                 
                 self._workWait_t_alim,
                 self._workWakeUp,
                 
                 self._workDiagIo,
                 self._workDiagIoAnswer,                 
                                  
                 self._evaluateActionsShutDown,
                 self._workShutDown,
                self._closePipe],
        'continue': True
        }

def _workMosfTXp_off(self, p_data= None):
    """ Richiesta off mosf tx p """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfTxAOff(self, keywords.status_off))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workMosfTXp_onoff_answer(self, p_data= None):
    " Risposta Diag "
    l_status= wrapkeys.getValueDefault(p_data, keywords.status_error, keywords.data_mtx_onoff_key)
    self.m_data[keywords.evdata_mtxp_on_off]= l_status
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workMosfTXd_off(self, p_data= None):
    """ Richiesta off mosf tx d """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfTxBOff(self, keywords.status_off))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workMosfTXd_onoff_answer(self, p_data= None):
    " Risposta Diag "
    l_status= wrapkeys.getValueDefault(p_data, keywords.status_error, keywords.data_mtx_onoff_key)
    self.m_data[keywords.evdata_mtxd_on_off]= l_status
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workTrigp_off(self, p_data= None):
    """ Richiesta off trig p """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTriggerAOff(self, keywords.status_off))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workTrigp_onoff_answer(self, p_data= None):
    " Risposta Diag "
    l_flash_status= wrapkeys.getValueDefault(p_data, keywords.status_error, bus.data_key.trig_flash_onoff)
    l_cam_status= wrapkeys.getValueDefault(p_data, keywords.status_error, bus.data_key.trig_cam_onoff)
    self.m_data[bus.data_key.trig_flash_onoff]= l_flash_status
    self.m_data[bus.data_key.trig_cam_onoff]= l_cam_status
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workTrigd_off(self, p_data= None):
    """ Richiesta on trig d """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTriggerBOff(self, keywords.status_off))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workTrigd_onoff_answer(self, p_data= None):
    " Risposta Diag "
    if get_config().main.implant_data.configurazione.get() == conf_values.binario.doppio:
        l_flash_status= wrapkeys.getValueDefault(p_data, keywords.status_error, bus.data_key.trig_flash_onoff)
        l_cam_status= wrapkeys.getValueDefault(p_data, keywords.status_error, bus.data_key.trig_cam_onoff)
        self.m_data[bus.data_key.trig_flash_onoff]= l_flash_status
        self.m_data[bus.data_key.trig_cam_onoff]= l_cam_status
    else:
        self.m_data[bus.data_key.trig_flash_onoff]= general.dato_non_disp
        self.m_data[bus.data_key.trig_cam_onoff]= general.dato_non_disp
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True
    
def _workWait_t_alim(self, p_data= None):
       """ attesa tempo assestamento  prima di un altro controllo 
       alimentazionea bttaria"""
       t_sleep= 10.0
       try:
           # TODO t_off_ivip?
           " prendere il dato distinto in A e B "
       except KeyError as e:
           self.m_logger.error("Missing key {}".format(e))
       self.m_data[keywords.evdata_sleeping_for]= t_sleep
       self.m_logger.info("Sleeping for {}".format(t_sleep))
       # Wake up dal timer
       l_cmd_wake= buildcmd._buildCmdFlowWakeUp(self)
       threading.Timer(t_sleep, sendWakeUp, [self, l_cmd_wake]).start()
       self._incTaskId()
       self.m_taskFuncList['continue']= False
       return True

def sendWakeUp(self, *args, **kwargs):
    """ Accoda al main il wake up cmd """
    # TODO non mi piace così meglio con il self
    try:
        p_cmd_dict= args[0]
        p_cmd_dict['trigflow_instance'].m_mainCore['cmd_q'].put(p_cmd_dict)
    except Exception as e:
        self.m_logger.critical("VERY CRITICAL : Wake up flow failed {}".format(e))

def _workWakeUp(self, p_data= None):
    """ Non un task ma una metodo pubblico di risveglio se siamo in attesa (tipo timer t_alim) """
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _evaluateActionsShutDown(self, p_data= None):
    """ Valutazione avanzamento shutdown"""    
    if wrapkeys.getValue(self.m_data, keywords.evdata_IVIP_power) == keywords.alim_batt:
        l_confirmed= True
        self.m_logger.info("Running from battery power: we need shutdown procedure")
    elif wrapkeys.getValueDefault(self.m_data, None, keywords.evdata_IVIP_power) is None:
        # Con mancata risposta da parte di IO status spengo lo stesso
        l_confirmed= True
    else:
        l_confirmed= False
    # Valuti lo stato confirmed
    self.m_data[keywords.evdata_shutdown_confirmed]= l_confirmed
    if not  l_confirmed:
        # Resume periodic task
        self.m_mainCore['cmd_q'].put(buildcmd._buildActionPausePeriodic())
    #
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workShutDown(self,p_data= None):
    """ Avvio spegnimento definitivo 
    con shutdown confermato continuo
    altrimenti richiedo un trig flow di riaccensione moduli esterni
    """
    if wrapkeys.getValueDefault(self.m_data, False, keywords.evdata_shutdown_confirmed):
        # Confermato, attendo n secondi che completi le acq in corso
        # TODO punto cablato di attesa, rivederlo manca l'interazione con
        # il main proc secondo me
        l_count= 30
        while len(self.m_mainCore['trigs']) and l_count:
            time.sleep(1)
            l_count = l_count- 1
        # shutdown anche con trig a metà
        self.m_mainCore['cmd_q'].put(buildcmd._buildActionShutDown())
    else:
        # Riabilito la ricezione dei nuovo flows
        self.m_mainCore['block_new_flows']= False
        self.m_mainCore['cmd_q'].put(buildcmd._buildActionFlowShutdownAborted())
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True
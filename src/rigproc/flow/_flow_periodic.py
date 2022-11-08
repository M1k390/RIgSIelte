#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task periodici
"""

from rigproc.commons import keywords
from rigproc.flow import eventtrigflow_buildcmd as buildcmd
from rigproc.commons.wrappers import wrapkeys

def _buildFlowPeriodic(self):
    """Flow builder per i task periodici """
    self.m_taskAll= {
        **self.m_taskBegin,
        **self.m_taskDiagnostica,
        **self.m_taskEvaluateActions,
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
                 self._evaluateActionsPeriodic,
                self._closePipe],
        'continue': True
        }

def _evaluateActionsPeriodic(self, p_data= None):
    """ Controllo se alcune delle informazioni dei dati raccolti necessitano
    azioni
    es: Se è attiva l'alimentazione a batteria devo spegnere la macchina
    """
    if keywords.evdata_IVIP_power in self.m_data.keys():
        if wrapkeys.getValue(self.m_data, keywords.evdata_IVIP_power) == keywords.alim_batt:
            self.m_logger.warning("Shutdown action requested, main power is missing!")
            self.m_mainCore['cmd_q'].put(buildcmd._buildActionShutDownFlow())
    #
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True



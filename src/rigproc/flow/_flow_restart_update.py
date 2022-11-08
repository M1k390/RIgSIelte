#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
richiesta uscita programma per update
"""

from rigproc.commons import keywords
from rigproc.flow import eventtrigflow_buildcmd as buildcmd
from rigproc.commons.wrappers import wrapkeys
from rigproc.commons.redisi import get_redisI

def _buildExitUpdate(self):
    """Flow builder per i task periodici """
    self.m_taskAll= {
        **self.m_taskBegin,
        **self.m_taskBusOff,        
        **self.m_taskExitForUpdate,
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
                 self._workTaskExitProcess,
                self._closePipe],
        'continue': True
        }

def _workTaskExitProcess(self, p_data= None):
    """ Build comando stop
        Se il riavvio è a seguito di un update,
        Segnalo in redis pers che ci siamo riavviati per aggiornamento
    """
    # Riavvio per update ?
    if self.m_input_data['restart_for_update'] == True:
        # Mark update as waiting
        l_res= get_redisI().pers.hset(keywords.sw_update_hash_key, keywords.sw_update_mark_as_waiting, 'True')
        if l_res == keywords.redis_error:
            self.m_logger.error("Error marking update as pending on Redis persistent cache")
        else:
            self.m_logger.warning("Marking scheduled sw update as pending")
        # Set last software version
        l_last_version_key= wrapkeys.getValueDefault(self.m_input_data, None, keywords.flin_last_version_key)
        l_last_version= get_redisI().pers.hget(keywords.sw_update_hash_key, keywords.sw_update_version, p_default=None)
        if l_last_version_key is not None and l_last_version is not None:
            l_res= get_redisI().pers.set(l_last_version_key, l_last_version)
            if l_res == keywords.redis_error:
                self.m_logger.error('Error setting the last version on Redis persistent cache')
        else:
            self.m_logger.error('Restarting for update but new program version is not specified')
        
    # comando di riavvio
    self.m_mainCore['io_q'].put(buildcmd._buildIoCmdRestart(self))
    #
    self.m_taskFuncList['continue']= True
    self._incTaskId()
    return True

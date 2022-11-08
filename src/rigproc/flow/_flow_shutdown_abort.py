#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shutdown abort
"""


def _buildFlowShutDownAborted(self):
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
        **self.m_taskBusOn,
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
                 self._workMosfTXp_on,
                 self._workMosfTXp_onoff_answer,
                 self._workMosfTXd_on,
                 self._workMosfTXd_onoff_answer,
                 self._workTrigp_on,
                 self._workTrigp_onoff_answer,
                 self._workTrigd_on,
                 self._workTrigd_onoff_answer,
                self._closePipe],
        'continue': True
        }

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accordatore eventi trig
    evt_trig
    evt_trig with measures
    evt diagnostica
"""

import logging
import uuid

from rigproc.commons.config import get_config
from rigproc.commons import  keywords
from rigproc.commons.helper import helper
from rigproc.commons import jsonmodel
from rigproc.flow import eventtrigflow_buildcmd as buildcmd
from rigproc.commons.redisi import get_redisI
from rigproc.commons.wrappers import wrapkeys
from rigproc.params import internal, conf_values


class EventTrigFlow:
    """
    Gestione evento trigger in tutte le sue componenti
        - trigger ricevuto
        - creazione oggetto evento ( istanza di this )
        - preparazione comandi da e verso il main process
            - richiesta dati via bus 485
        - gestione fallimenti comadni
        - gestione salvataggio recover

        NOTA: Le informazioni necessarie alla compilazione dei json
            sono in prima istanza sulla cache, ed in copia all'interno di
            questa classe.
            Con la cache produci il json, il restò è per comodità
    """

    def __init__(
        self,
        p_main_core,
        p_evt_name,
        p_flow,
        p_data= None,
        p_request_id= None
    ):
        """
        Init componenti di base

        Parameters
        ----------
        p_main_core: dict
            queues, redis, evt hnd del main proc
        p_evt_name: string
            nome o id evento es: evt_trigger_timestamp
        p_flow: string
            Tipo di evento che richiede il flow (trigger, diagnostica, recovering ..)
        p_data: dict
            dati utili al task flow
        """
        self.m_logger= logging.getLogger('root')
        self.m_flow_logger= logging.getLogger('flow')
        self.m_mainCore= p_main_core
        self.m_input_data= p_data
        self.m_jmodel= jsonmodel.JsonModels()
        self.m_redisI= get_redisI()
        self.m_recovering= False
        self.m_evt= str(p_evt_name)
        self.m_flow= p_flow
        self.m_done= False
        self.m_error= False
        self.m_criticalError= False
        self.m_stop= False
        self.m_stopOnError= False
        self.m_internalTime= helper.timeNowObj()

        " Flow ID (non mutabile) "
        self.__m_flow_id= f'{self.m_internalTime}_{self.m_flow}_{uuid.uuid4()}'
        self.__m_request_id= p_request_id
        if p_request_id is not None:
            self.__m_flow_id += f'_{p_request_id}'

        # Check abort del flow se abbiamo un blocco ad alta priorità
        # Il flow rimane pendente e verrà eliminato dal main process dopo
        # un tempo t rispetto ad internal time
        if self.m_mainCore['block_new_flows']== True:
            return
        # Preparazione task list
        self._taskList()
        # Avvio task loop
        self.m_flow_logger.info(f'Event: {self.m_evt}. {self.m_flow} created')
        self._executeLoop()

    " ---- IMPORT, CLASS IS PLITTED IN MULTIPLE FILES ----- "

    # SUBSCRIPTION
    from ._flow_subscription import _buildFlowSubscription, _workTopicSub, _workTopicSubAnswer

    # STARTUP
    from ._flow_startup import _buildFlowStartup, _workPrintVersion, _workIsUpdated, \
        _workTopicUpdateDone, _workTopicUpdateDoneAnswer, _workSetUpNtp, _workMountSshfsFolder, \
            _workNotifyStartupDone, _workMosfTXp_on, _workMosfTXd_on,\
                _workTrigp_on, _workTrigd_on

    # EXIT FOR UPDATE
    from ._flow_restart_update import _buildExitUpdate, _workTaskExitProcess

    # SW UPDATE
    from ._flow_sw_update import _buildFlowUpdate, _workGetSwUpdatePackage, _workScheduleUpdate, \
        _workTopicSwUpdateScheduled, _workTopicSwUpdateScheduledAnswer

    # SHUTDOWN
    from ._flow_shutdown import  _buildFlowShutDown, _workMosfTXp_off, _workMosfTXp_onoff_answer,\
        _workMosfTXd_off, _workMosfTXd_onoff_answer, _workTrigp_off, _workTrigp_onoff_answer,\
        _workTrigd_off, _workTrigd_onoff_answer, _workWait_t_alim, _workWakeUp, sendWakeUp, _evaluateActionsShutDown,\
        _workShutDown

    # SHUTDOWN ABORT
    from ._flow_shutdown_abort import _buildFlowShutDownAborted

    # DIAGNOSI
    from ._flow_diagnosi import _buildFlowDiagnosis, _workDiagMosfTxA, _workDiagMosfTxAAnswer,\
        _workDiagMosfRxA, _workDiagMosfRxAAnswer, _workDiagMosfTxB, _workDiagMosfTxBAnswer,\
            _workDiagMosfRxB, _workDiagMosfRxBAnswer, _workDiagTriggerAStatus, _workDiagTriggerAStatusAnswer,\
            _workDiagTriggerBStatus, _workDiagTriggerBStatusAnswer, _workDiagIo,\
            _workDiagIoAnswer, _checkTrigAVer, _checkTrigAVerAnswer,\
                _checkTrigBVer, _checkTrigBVerAnswer, _workIoVer, _workIoVerAnswer, \
                    _workTopicDiagnosis, _workTopicDiagnosisAnswer

    # IMPLANT STATUS
    from ._flow_implant_status import _buildFlowImplantStatus, _workRemoveStatusInfo, _checkMosfTxASpeedStatus, _checkMosfTxASpeedStatusAnswer,\
        _checkMosfTxBSpeedStatus, _checkMosfTxBSpeedStatusAnswer, _workMosfTxAOn, _workMosfTxAOnAnswer,\
            _workMosfTxBOn, _workMosfTxBOnAnswer, _checkMosfRxAt0, _checkMosfRxAt0Answer,\
                _checkMosfRxBt0, _checkMosfRxBt0Answer, _checkMosfRxAData, _checkMosfRxADataAnswer,\
                    _checkMosfRxBData, _checkMosfRxBDataAnswer, _checkIoVer, _checkIoVerAnswer, _checkImgsToRecover,\
                                _checkSshfsConnection, _checkBrokerConnection, _checkCamerasConnection

    # ANOMALY
    from ._flow_anomaly import _buildFlowAnomaly, _workTopicAnomaly, _workTopicAnomalyAnswer

    # INTERNAL SETTINGS UPDATE
    from ._flow_internal_settings_update import _buildFlowInternalSettingsUpdate,\
        _workMosfRxA_mosf, _workMosfRxA_mosfAnswer, _workMosfRxB_mosf, _workMosfRxB_mosfAnswer,\
            _workSetResetTime, _workStoreInternalSettings, _workTopicIntSettUpdate, _workTopicIntSettUpdateAnswer

    # TEMPORAL WINDOW UPDATE
    from ._flow_time_window_settings_update import _buildFlowTimeWindowSettingsUpdate,\
        _workStoreTimeWinSettings, _workTopicTimeWinUpdate, _workTopicTimeWinUpdateAnswer

    # PERIODIC TASK
    from ._flow_periodic import _buildFlowPeriodic, _evaluateActionsPeriodic


    " ------ PUBLIC METHODS ---- "

    def stop(self):
        self.m_stop= True

    def stopOnError(self):
        self.m_flow_logger.warning("Stop on error enabled")
        self.m_stopOnError= True

    def isDone(self):
        """
        Getter stato workflow
        True se è completato
        Se ha eseguito il recovering di tutti i componenti
        nonostante errori di processing si considera completato
        @todo se ci sono problemi di bus? che si fa?

        Returns
        -------
        True completato (anche con errori)
        """
        return self.m_done

    def hasErrors(self):
        """ Getter variabile errore esecuzione task pipeline """
        return self.m_error

    def hasCriticalErrors(self):
        """GEtter errori critici """
        return self.m_criticalError

    def getEvtName(self):
        """ Getter event name """
        return self.m_evt

    def getAdvancement(self) -> int:
        """ Ritorna l'indice di avanzamento 0 - 100 %
        Viene calcolato rispetto all'indice di avanzamento ed al numero di task
        """
        l_numTasks=  len(self.m_taskFuncList['tasks'])
        l_pos=  self.m_taskFuncList['id']
        return int((l_pos/l_numTasks)*100)

    def getCreationTime(self):
        """ Get object creation time """
        return self.m_internalTime

    def getFlowId(self):
        """ Get Flow ID """
        return self.__m_flow_id

    def getRequestId(self):
        """ Get request ID
        Useful to identify a flow triggered by a specific request (e.g.: console)
        """
        return self.__m_request_id

    def parseAnswer(self, p_cmd, p_data):
        """
        I comandi che necessitano un feed back dal main
        ad esempio:
            - messaggi di risposta dal bus
            ( i topic li gestisci internamente ?)
        Si valuta la risposta e si avanza nella pipeline
        NOTA : si avanza anche con errore nella risposta!

        Flow :
            Richiesto un comando io, mi metto in attesa
            Rispsota arrivata : ok riprendo il loop
            Rispsota non arrivata ( timeout o errore ): riprendo il loop e
                lascio vuoto il dato
        Parameters
        ----------
        p_cmd : str
            id del comando in processing es mrx_wire_t0_b
        p_cmd : str
            data del comando in processing
        """
        # Per ogni task della pipeline
        if not p_data: p_data= 'empty'
        self.m_flow_logger.debug(f'Received answer. Command: {p_cmd}. Data: {p_data}')
        l_found= False
        for task in self.m_taskAll.keys():
            # Verifico se la key ricevuta è attinente
            if self.m_taskAll[task]['id'] == self.m_taskFuncList['id']:
                self.m_flow_logger.debug("looking for [task]: " + self.m_taskAll[task]['msg'] )
                if self.m_taskAll[task]['msg'] in p_cmd :
                    self.m_taskFuncList['continue']= True
                    self._executeLoop(p_data)
                    l_found = True
                    break
        # Corrispondenza non trovata, avanzo e segno errore
        if not l_found:
            self.m_flow_logger.error("corresponding task not found: [id] = " + str(self.m_taskFuncList['id']))
            self.m_error = True
            if not self.m_taskFuncList['continue']:
                self.m_flow_logger.warning('Assuming missed answer')
                self.gotMissedAnswerContinue()
            else:
                self.m_flow_logger.warning('Ignoring wrong answer')

    def gotMissedAnswerContinue(self):
        """ Se ottengo una mancata risposta proseguo ugualmente """
        self._incTaskId()
        self.m_error = True
        self.m_flow_logger.error("Skipping id {}".format(self.m_taskFuncList['id']))
        self.m_taskFuncList['continue']= True
        self._executeLoop(None)

    " ----- PRIVATE ----- "

    def _taskList(self):
        """
        Creazione task list evento trigger
        """
        " Gruppo ordinato delle operazioni da compiere"
        self.m_taskBegin={
            'prepareWorkEvtTrigger': { 'id' : 0, 'msg': ''},
            }
        self.m_taskSubscribe={
            'topicSub': { 'id' : 0, 'msg': ''},
            'topicSubAnswer': { 'id' : 0, 'msg': ''},
        }
        self.m_taskCheckUpdate={
            '_workIsUpdated':{ 'id' : 0, 'msg': ''},
            '_workTopicUpdateDone':{ 'id' : 0, 'msg': ''},
            '_workTopicUpdateDoneAnswer':{ 'id' : 0, 'msg': keywords.topic_cmd_key},
            }
        self.m_timeSync={
            '_workSetUpNtp': { 'id' : 0, 'msg': ''}
        }
        self.m_taskMountRemote={
            '_workMountSshfsFolder': { 'id' : 0, 'msg': ''}
        }
        self.m_taskNotifyStartupDone={
            '_workNotifyStartupDone': { 'id': 0, 'msg': ''}
        }
        self.m_taskImg={
            'imagesRemote':{ 'id' : 0, 'msg': ''},
            }
        self.m_taskPrr={
            'wireT0': { 'id' : 0, 'msg': ''},
            'wireT0Answer': { 'id' : 0, 'msg': keywords.cmd_mrx_wire_t0_generic},
            'trainSpeed': { 'id' : 0, 'msg': ''},
            'trainSpeedAnswer': { 'id' : 0, 'msg': keywords.cmd_mtx_vel_generic}
            }
        self.m_taskTopicT0= {
            'topicEvent': { 'id' : 0, 'msg': ''},
            'topicEventAnsw': { 'id' : 0, 'msg': keywords.topic_cmd_key},
            }
        self.m_taskDiagnostica={
            'diag_mosfTxA': { 'id' : 0, 'msg': ''},
            'diag_mosfTxAAnswer': { 'id' : 0, 'msg': keywords.cmd_mtx_ver_a},
            'diag_mosfRxA': { 'id' : 0, 'msg': ''},
            'diag_mosfRxAAnswer': { 'id' : 0, 'msg': keywords.cmd_mrx_ver_a},
            'diag_mosfTxB': { 'id' : 0, 'msg': ''},
            'diag_mosfTxBAnswer': { 'id' : 0, 'msg': keywords.cmd_mtx_ver_b},
            'diag_mosfRxB': { 'id' : 0, 'msg': ''},
            'diag_mosfRxBAnswer': { 'id' : 0, 'msg': keywords.cmd_mrx_ver_b},
            'diag_triggerA': { 'id' : 0, 'msg': ''},
            'diag_triggerAAnswer': { 'id' : 0, 'msg': keywords.cmd_trig_status_a},
            'diag_triggerB': { 'id' : 0, 'msg': ''},
            'diag_triggerBAnswer': { 'id' : 0, 'msg': keywords.cmd_trig_status_b},
            'diag_io': { 'id' : 0, 'msg': ''},
            'diag_ioAnswer': { 'id' : 0, 'msg': keywords.cmd_io},
            'trigPVer': { 'id' : 0, 'msg': ''},
            'trigPVerAnswer': { 'id' : 0, 'msg': keywords.cmd_trig_ver_a},
            'trigDVer': { 'id' : 0, 'msg': ''},
            'trigDVerAnswer': { 'id' : 0, 'msg': keywords.cmd_trig_ver_b},
            'diag_IoVer': { 'id' : 0, 'msg': ''},
            'diag_IoVerAnswer': { 'id' : 0, 'msg': keywords.cmd_io_ver}
            }
        self.m_taskTopicDiag= {
            'topicDiagnosis': { 'id' : 0, 'msg': ''},
            'topicDiagnosisAnsw': { 'id' : 0, 'msg': keywords.topic_cmd_key}
            }
        self.m_taskImplantStatus={
            'ioVer': { 'id' : 0, 'msg': ''},
            'ioVerAnswer': { 'id' : 0, 'msg': keywords.cmd_io_ver},
            'diag_io': { 'id' : 0, 'msg': ''},
            'diag_ioAnswer': { 'id' : 0, 'msg': keywords.cmd_io},
            'diag_mosfTxA': { 'id' : 0, 'msg': ''},
            'diag_mosfTxAAnswer': { 'id' : 0, 'msg': keywords.cmd_mtx_ver_a},
            'mosfTxASpeedStatus': { 'id': 0, 'msg': '' },
            'mosfTxASpeedStatusAnswer': { 'id': 0, 'msg': keywords.cmd_mtx_vel_a },
            'mosfTxAOnOff': { 'id': 0, 'msg': '' },
            'mosfTxAOnOffAnswer': { 'id': 0, 'msg': keywords.cmd_mtx_on_off_a },
            'diag_mosfTxB': { 'id' : 0, 'msg': ''},
            'diag_mosfTxBAnswer': { 'id' : 0, 'msg': keywords.cmd_mtx_ver_b},
            'mosfTxBSpeedStatus': { 'id': 0, 'msg': '' },
            'mosfTxBSpeedStatusAnswer': { 'id': 0, 'msg': keywords.cmd_mtx_vel_b },
            'mosfTxBOnOff': { 'id': 0, 'msg': '' },
            'mosfTxBOnOffAnswer': { 'id': 0, 'msg': keywords.cmd_mtx_on_off_b },
            'diag_mosfRxA': { 'id' : 0, 'msg': ''},
            'diag_mosfRxAAnswer': { 'id' : 0, 'msg': keywords.cmd_mrx_ver_a},
            'mosfRxAt0': { 'id' : 0, 'msg': '' },
            'mosfRxAt0Answer': { 'id' : 0, 'msg': keywords.cmd_mrx_wire_t0_a },
            'mosfRxAData': { 'id' : 0, 'msg': '' },
            'mosfRxADataAnswer': { 'id' : 0, 'msg': keywords.cmd_mrx_wire_data_a },
            'diag_mosfRxB': { 'id' : 0, 'msg': ''},
            'diag_mosfRxBAnswer': { 'id' : 0, 'msg': keywords.cmd_mrx_ver_b},
            'mosfRxBt0': { 'id' : 0, 'msg': '' },
            'mosfRxBt0Answer': { 'id' : 0, 'msg': keywords.cmd_mrx_wire_t0_b },
            'mosfRxBData': { 'id' : 0, 'msg': '' },
            'mosfRxBDataAnswer': { 'id' : 0, 'msg': keywords.cmd_mrx_wire_data_b },
            'trigAVer': { 'id' : 0, 'msg': '' },
            'trigAVerAnswer': { 'id' : 0, 'msg': keywords.cmd_trig_ver_a },
            'diag_triggerA': { 'id' : 0, 'msg': ''},
            'diag_triggerAAnswer': { 'id' : 0, 'msg': keywords.cmd_trig_status_a},
            'trigBVer': { 'id' : 0, 'msg': '' },
            'trigBVerAnswer': { 'id' : 0, 'msg': keywords.cmd_trig_ver_b },
            'diag_triggerB': { 'id' : 0, 'msg': ''},
            'diag_triggerBAnswer': { 'id' : 0, 'msg': keywords.cmd_trig_status_b},
            'imgsToRecover': { 'id' : 0, 'msg': ''},
            'sshfsConnection': { 'id' : 0, 'msg': ''},
            'brokerConnection': { 'id' : 0, 'msg': ''},
            'camerasConnection': { 'id' : 0, 'msg': ''},
        }
        self.m_taskData={
            'mosf': { 'id' : 0, 'msg': ''},
            'mosfAnswer': { 'id' : 0, 'msg': keywords.cmd_mrx_wire_data_gneric}
            }
        self.m_taskTopicWireData= {
            'topicData': { 'id' : 0, 'msg': ''},
            'topicDataAnsw': { 'id' : 0, 'msg': keywords.topic_cmd_key}
            }
        self.m_store= {
            'storeForRecovering': { 'id' : 0, 'msg': ''}
            }
        self.m_taskBusOff= {
            'mosfTXp_off': { 'id' : 0, 'msg': ''},
            'mosfTXp_onoff_answer': { 'id' : 0, 'msg': ''},
            'mosfTXd_off': { 'id' : 0, 'msg': ''},
            'mosfTXd_onoff_answer': { 'id' : 0, 'msg': ''},
            'trigp_off': { 'id' : 0, 'msg': ''},
            'trigp_onoff_answer': { 'id' : 0, 'msg': ''},
            'trigd_off': { 'id' : 0, 'msg': ''},
            'trigd_onoff_answer': { 'id' : 0, 'msg': ''},
            'diag_IoVer': { 'id' : 0, 'msg': ''},
            'diag_IoVerAnswer': { 'id' : 0, 'msg': keywords.cmd_io_ver}
            }
        self.m_taskBusOn= {
            'mosfTXp_on': { 'id' : 0, 'msg': ''},
            'mosfTXp_onoff_answer': { 'id' : 0, 'msg': ''},
            'mosfTXd_on': { 'id' : 0, 'msg': ''},
            'mosfTXd_onoff_answer': { 'id' : 0, 'msg': ''},
            'trigp_on': { 'id' : 0, 'msg': ''},
            'trigp_onoff_answer': { 'id' : 0, 'msg': ''},
            'trigd_on': { 'id' : 0, 'msg': ''},
            'trigd_onoff_answer': { 'id' : 0, 'msg': ''},            
            }
        self.m_taskWait={
            'wait_time': { 'id' : 0, 'msg': ''},
            'wake_up': { 'id' : 0, 'msg': 'wake_up'}
            }        
        self.m_taskDiagReduced={
            'diag_io': { 'id' : 0, 'msg': ''},
            'diag_ioAnswer': { 'id' : 0, 'msg': keywords.cmd_io},            
            }     
        self.m_taskShutDown={
            'check_ready': { 'id' : 0, 'msg': ''},
            'shutdown': { 'id' : 0, 'msg': ''}
            }        
        self.m_taskEvaluateActions={
            'evaluateActions': { 'id' : 0, 'msg': ''}
            }
        self.m_taskAnomaly= {
            'topicAnomlay': { 'id' : 0, 'msg': ''},
            'topicAnomalyAnsw': { 'id' : 0, 'msg': ''},
        }
        self.m_taskIntSettUpdate= {
            'mosfRxAtmosf': { 'id' : 0, 'msg': ''},
            'mosfRxAtmosfAnsw': { 'id' : 0, 'msg': keywords.cmd_mrx_tmos_a},
            'mosfRxBtmosf': { 'id' : 0, 'msg': ''},
            'mosfRxBtmosfAnsw': { 'id' : 0, 'msg': keywords.cmd_mrx_tmos_b},
            'setResetTime': { 'id' : 0, 'msg': ''},
            'storeIntSett': { 'id' : 0, 'msg': ''},
            'topicIntSettUpd': { 'id' : 0, 'msg': ''},
            'topicIntSettUpdAnsw': { 'id' : 0, 'msg': ''},
        }
        self.m_taskTimeWinUpdate= {
            'storeTimeWinSettings': { 'id' : 0, 'msg': ''},
            'topicTimeWinUpdate': { 'id' : 0, 'msg': ''},
            'topicTimeWinUpdateAnswer': { 'id' : 0, 'msg': ''},
        }
        self.m_task_schedule_update={
            'getSwUpdatePackage': { 'id' : 0, 'msg': ''},
            'scheduleUpdate': { 'id' : 0, 'msg': ''},
            'topicSwUpdateScheduled': { 'id' : 0, 'msg': ''},
            'topicSwUpdateScheduledAnswer': { 'id' : 0, 'msg': ''}
            }
        self.m_taskExitForUpdate={
            'exitForUpdate': { 'id' : 0, 'msg': ''}
            }
        self.m_taskClosePipe= {
            'closePipe': { 'id' : 0, 'msg': ''}
            }
        " FACTORY tasklist in base al tipo di flow richiesto "
        if self.m_flow == keywords.flow_type_startup:
            self._buildFlowStartup()
        elif self.m_flow == keywords.flow_type_subscription:
            self._buildFlowSubscription()
        elif self.m_flow == keywords.flow_type_diagnosis:
            self._buildFlowDiagnosis()
        elif self.m_flow == keywords.flow_type_implant_status:
            self._buildFlowImplantStatus()
        elif self.m_flow == keywords.flow_type_shutdown:
            self._buildFlowShutDown()
        elif self.m_flow == keywords.flow_type_shutdown_aborted:
            self._buildFlowShutDownAborted()
        elif self.m_flow == keywords.flow_type_power_check:
            self._buildFlowPeriodic()
        elif self.m_flow == keywords.flow_type_anomaly:
            self._buildFlowAnomaly()
        elif self.m_flow == keywords.flow_type_int_sett_upd:
            self._buildFlowInternalSettingsUpdate()
        elif self.m_flow == keywords.flow_type_time_win_upd:
            self._buildFlowTimeWindowSettingsUpdate()
        elif self.m_flow == keywords.flow_type_sw_update:
            self._buildFlowUpdate()
        elif self.m_flow == keywords.flow_type_exit_update:
            self._buildExitUpdate()
        else:
            self.m_flow_logger.error(f'Lanching the flow {self.m_flow} without the building operation')

    def _incTaskId(self):
        """Incremento task id nella lista """
        # Ho ancora margine per l'incremento? close pipe deve essere esguito
        try:
            l_tasks_len= len(self.m_taskFuncList['tasks'])
            l_id= self.m_taskFuncList['id']
            if l_tasks_len >= l_id + 2:
                self.m_taskFuncList['id']= self.m_taskFuncList['id'] + 1
            else:
                # Non c'è spazio per incrementare..
                self.m_flow_logger.warning("Can't increment flow task list!")
        except KeyError as e:
            self.m_flow_logger.critical("Critical exception on key {}".format(e))
        

    def _setDefaultValues(self) ->None:
        """
        Ritorna un dictionary con le key relative al bus objs con valori
        di default

        Returns
        -------
        Dizionario
        """
        self.m_data[keywords.evdata_prr]= keywords.status_error
        self.m_data[keywords.evdata_mosf_wire_t0]= keywords.status_error
        self.m_data[keywords.evdata_train_speed]= keywords.status_error
        self.m_data[keywords.evdata_train_direction]= keywords.status_error
        self.m_data[keywords.evdata_mosfTXp_status]= keywords.status_error
        self.m_data[keywords.evdata_mosfRXp_status]= keywords.status_error
        self.m_data[keywords.evdata_mosfTXd_status]= keywords.status_error
        self.m_data[keywords.evdata_mosfRXd_status]= keywords.status_error

        l_flash_A= {}
        l_flash_A[keywords.data_trig_flash_1_status]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_2_status]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_3_status]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_4_status]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_5_status]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_6_status]= keywords.status_error
        " flash efficiency "
        l_flash_A[keywords.data_trig_flash_1_efficiency]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_2_efficiency]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_3_efficiency]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_4_efficiency]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_5_efficiency]= keywords.status_error
        l_flash_A[keywords.data_trig_flash_6_efficiency]= keywords.status_error
        self.m_data[keywords.evdata_flash_A]= l_flash_A

        l_flash_B= {}
        l_flash_B[keywords.data_trig_flash_1_status]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_2_status]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_3_status]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_4_status]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_5_status]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_6_status]= keywords.status_error
        " flash efficiency "
        l_flash_B[keywords.data_trig_flash_1_efficiency]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_2_efficiency]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_3_efficiency]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_4_efficiency]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_5_efficiency]= keywords.status_error
        l_flash_B[keywords.data_trig_flash_6_efficiency]= keywords.status_error

        self.m_data[keywords.evdata_flash_B]= l_flash_B
        self.m_data[keywords.evdata_name]= keywords.status_error
        self.m_data[keywords.evdata_battery]= 'todo'
        self.m_data[keywords.evdata_IVIP_power]= keywords.status_error
        self.m_data[keywords.evdata_switch_prrA]=keywords.status_error
        self.m_data[keywords.evdata_switch_prrB]=keywords.status_error
        self.m_data[keywords.evdata_ldc_prrA]=keywords.status_error
        self.m_data[keywords.evdata_ldc_prrB]=keywords.status_error
        self.m_data[keywords.evdata_t_mosf_prrA]=keywords.status_error
        self.m_data[keywords.evdata_t_mosf_prrB]=keywords.status_error
        self.m_data[keywords.evdata_t_off_ivip_prrA]=keywords.status_error
        self.m_data[keywords.evdata_t_off_ivip_prrB]=keywords.status_error
        self.m_data[keywords.evdata_door_opened]=keywords.status_error
        self.m_data[keywords.evdata_sens1]=keywords.status_error
        self.m_data[keywords.evdata_sens2]=''
        self.m_data[keywords.evdata_vent1]=''
        self.m_data[keywords.evdata_vent2]=''
        self.m_data[keywords.evdata_mrx_wire_data_A]= keywords.status_error
        self.m_data[keywords.evdata_mrx_wire_data_B]= keywords.status_error

    " ---- TASK EXECUTION ---- "

    def _executeLoop(self,p_data= None):
        """
        Loop state machine relativamente ai task
        Esegue i micro task in ordine, gestendo l'avanzamento delle
        operazioni
        """
        l_consecutive=0
        self.m_flow_logger.debug(f'{self.m_flow}. Entering with data: {p_data}')
        while self.m_taskFuncList['continue'] and not self.m_stop:
            l_consecutive += 1
            taskId= self.m_taskFuncList['id']
            self.m_flow_logger.debug("TaskId - func name: {}-{}".format(taskId,
                                                                  self.m_taskFuncList['tasks'][taskId].__name__))
            self.m_flow_logger.debug("Consecutive tasks : " + str(l_consecutive))
            l_ret= self.m_taskFuncList['tasks'][taskId](p_data)
            p_data= None
            if not l_ret:
                # Non si esce , si continua senza una parte di task presente
                # dove possibile lo valuta il task stesso
                self.m_error= True
                self.m_flow_logger.debug("Task returned False")
                if self.m_stopOnError:
                    self.m_stop= True
            

    " ------ TASKS ----- "

    def _prepareWork(self, p_data=None):
        """
        Prepara i dati di lavoro:
            - json
            - prepara il recovering

        m_data {
            "evt_name":e event id,
            "json": json evt trigger,
            "imgs": struttura dati nome immagine : binario
            "remoteDir": direcotry remota
            "localDir": directory locale
            }
        """
        # @TODO timestamp formattato?
        l_timestamp= helper.timestampNowFormatted()
        l_float_timestamp= helper.timestampNowFloat()
        l_plant_name= get_config().main.implant_data.nome_ivip.get()
        # Pausa periodic task
        self.m_mainCore['cmd_q'].put(buildcmd._buildActionPausePeriodic())
        # Configurazione
        self.m_data= {}
        # Valori default dati che recupererò dal bus
        self._setDefaultValues()
        # Common set up
        self.m_data[keywords.evdata_on_trigger]= str(False)
        self.m_data[keywords.evdata_uuid]= helper.new_trans_id()
        self.m_data[keywords.evdata_timestamp]= l_timestamp
        self.m_data[keywords.evdata_float_timestamp]= l_float_timestamp
        self.m_data[keywords.evdata_date]= helper.dateNow()
        self.m_data[keywords.evdata_time]= helper.timeNow()
        self.m_data[keywords.evdata_recovered]= str(False)
        self.m_data[keywords.evdata_id]= f'{l_float_timestamp}_{l_plant_name}'
        # Configurazione binario
        self.m_data[internal.flow_data.conf_binario]= get_config().main.implant_data.configurazione.get()
        # Evt Diagnosi richiesta esplicitamente
        if self.m_flow == keywords.flow_type_diagnosis:
            self.m_data[keywords.evdata_evt_name] = self.m_evt
            # Rispondo alla transazione identificata dal topic in arrivo
            if keywords.flin_trans_id in self.m_input_data:
                self.m_data[keywords.evdata_uuid]= self.m_input_data[keywords.flin_trans_id]
            if keywords.flin_id in self.m_input_data:
                self.m_data[keywords.evdata_id]= self.m_input_data[keywords.flin_id]
        # Shut down
        if self.m_flow == keywords.flow_type_shutdown:
            self.m_mainCore['block_new_flows']= True
        # Abort shutdown 
        if self.m_flow == keywords.flow_type_shutdown_aborted:
            " "
        # Alarm anomaly
        if self.m_flow == keywords.flow_type_anomaly:
            self._input_to_data(internal.flow_input.id, internal.flow_data.id)
            self._input_to_data(internal.flow_input.alarm_id, internal.flow_data.alarm_id)
            self._input_to_data(internal.flow_input.alarm_descr, internal.flow_data.alarm_descr)
            self._input_to_data(internal.flow_input.alarm_status, internal.flow_data.alarm_status)
        # Implant check
        if self.m_flow == internal.flow_type.implant_status:
            # "Simula" binario doppio
            self.m_data[internal.flow_data.conf_binario]= conf_values.binario.doppio
        # Kafka requests
        if self.m_flow in [keywords.flow_type_sw_update, keywords.flow_type_int_sett_upd, keywords.flow_type_time_win_upd]:
            " Salva il json della richiesta "
            self.m_data[keywords.evdata_json_from_stg]= wrapkeys.getValue(self.m_input_data, keywords.flin_json_dict)
        # Internal settings update
        if self.m_flow == keywords.flow_type_int_sett_upd:
            self.m_data[keywords.evdata_t_mosf_prrA]= wrapkeys.getValue(self.m_input_data, keywords.flin_t_mosf_prrA)
            self.m_data[keywords.evdata_t_mosf_prrB]= wrapkeys.getValue(self.m_input_data, keywords.flin_t_mosf_prrB)
            self.m_data[keywords.evdata_t_off_ivip_prrA]= wrapkeys.getValue(self.m_input_data, keywords.flin_t_off_ivip_prrA)
            self.m_data[keywords.evdata_t_off_ivip_prrB]= wrapkeys.getValue(self.m_input_data, keywords.flin_t_off_ivip_prrB)
        # Time window update
        if self.m_flow == keywords.flow_type_time_win_upd:
            self.m_data[keywords.evdata_fin_temp_pic_pari]= wrapkeys.getValue(self.m_input_data, keywords.flin_fin_temp_pic_pari)
            self.m_data[keywords.evdata_fin_temp_pic_dispari]= wrapkeys.getValue(self.m_input_data, keywords.flin_fin_temp_pic_dispari)
        # Sw update
        if self.m_flow == keywords.flow_type_sw_update:
            self.m_data[keywords.evdata_schedule_date]= wrapkeys.getValue(self.m_input_data, keywords.flin_schedule_date)
            self.m_data[keywords.evdata_schedule_time]= wrapkeys.getValue(self.m_input_data, keywords.flin_schedule_time)
            self.m_data[keywords.evdata_update_version]= wrapkeys.getValue(self.m_input_data, keywords.flin_update_version)
            self.m_data[keywords.evdata_transaction_id]= wrapkeys.getValue(self.m_input_data, keywords.flin_trans_id)
        # Restart ( example for update by schedule )
        if self.m_flow == keywords.flow_type_exit_update:
            self.m_mainCore['block_new_flows']= True
        # Startup
        if self.m_flow == keywords.flow_type_startup:
            pass
        # Salva log di inizio flow in Redis cache
        self.m_redisI.startFlow(self.getFlowId(), self.m_flow)
        #
        self.m_taskFuncList['continue']= True
        self._incTaskId()
        return True

    def _input_to_data(self, p_input_key, p_data_key):
        """ Sposta un dato dall'input del flow (input_data) ai dati interni (data) 
        Ritorna None se l'operazione è andata a buon fine, 
        altrimenti restituisce un messaggio di errore """
        self.m_data[p_data_key], l_err= wrapkeys.getValueError(self.m_input_data, p_input_key)
        return l_err


    " ----- CLOSE PIPE ------ "

    def _closePipe(self, p_data= None):
        """ Chiusura pipe
        Informo il main processing che abbiamo terminato
        """
        self.m_flow_logger.info(f'Closing pipe for {self.m_flow}. Errors: {self.m_error}')
        # Riabilito i task periodici se non sono in spegnimento
        if not keywords.evdata_shutdown_confirmed in self.m_data.keys():
            # Resume periodic task
            self.m_mainCore['cmd_q'].put(buildcmd._buildActionResumePeriodic())
        elif self.m_data[keywords.evdata_shutdown_confirmed]== False:
            self.m_mainCore['cmd_q'].put(buildcmd._buildActionResumePeriodic())
        #
        self.m_stop= True
        self.m_done= True
        self.m_data.clear()
        self.m_mainCore['cmd_q'].put(buildcmd._buildCmdPipeEnded(self))
        self.m_redisI.stopFlow(self.getFlowId(), self.m_error)
        " "
        return True




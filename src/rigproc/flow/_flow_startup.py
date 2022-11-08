#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start up flow
"""

import subprocess
from rigproc import __version__ as version

from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI

from rigproc.commons.helper import helper
from rigproc.commons.wrappers import wrapkeys

from rigproc.commons import keywords
from rigproc.params import bus, conf_values, general, internal, redis_keys

from rigproc.flow import eventtrigflow_buildcmd as buildcmd


def _buildFlowStartup(self):
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
        'printVersion': { 'id' : 0, 'msg': keywords.cmd_io_ver},
        **self.m_taskCheckUpdate,
        **self.m_timeSync,
        **self.m_taskMountRemote,
        **self.m_taskBusOn,
        **self.m_taskClosePipe,
        **self.m_taskNotifyStartupDone
        }
    # Indicizzazione taskAll entries
    l_idx= 0
    for task in self.m_taskAll:
        self.m_taskAll[task]['id']= l_idx
        l_idx += 1
    # Lista funzioni registrate realtive ai task
    self.m_taskFuncList= {
        'id': 0,
        'tasks':[self._prepareWork,
                 self._workPrintVersion,
                 self._workIsUpdated,
                 self._workTopicUpdateDone,
                 self._workTopicUpdateDoneAnswer,
                 self._workSetUpNtp,
                 self._workMountSshfsFolder,
                 self._workMosfTXp_on,
                 self._workMosfTXp_onoff_answer,
                 self._workMosfTXd_on,
                 self._workMosfTXd_onoff_answer,
                 self._workTrigp_on,
                 self._workTrigp_onoff_answer,
                 self._workTrigd_on,
                 self._workTrigd_onoff_answer,
                self._workNotifyStartupDone,
                self._closePipe],
        'continue': True
        }


def _workPrintVersion(self, p_data= None):
    self.m_data[keywords.evdata_sw_version]= ''
    try:
        self.m_data[keywords.evdata_sw_version]= version
    except Exception as e:
        self.m_logger.error("Can't get package version: {}".format(e))
    self.m_logger.info("Package version : {}".format(self.m_data[keywords.evdata_sw_version]))
    #
    self.m_taskFuncList['continue']= True
    self._incTaskId()
    return True


def _workIsUpdated(self, p_data= None):
    """ Verifica se siamo usciti da un update 
    Nel caso invio topic update completato 
    """
    # Controllo se ho una key di update attiva, ovvero ci siamo riavviati con schedulazione positiva
    l_update_pending= get_redisI().pers.hget(keywords.sw_update_hash_key, keywords.sw_update_mark_as_waiting)
    l_update_version_requested= get_redisI().pers.hget(keywords.sw_update_hash_key, keywords.sw_update_version, p_default=None)
    l_current_version= wrapkeys.getValueDefault(self.m_data, None, keywords.evdata_sw_version)
    if l_current_version is not None and l_current_version == l_update_version_requested:
        l_update_outcome= 'successed'
        l_error= 'none'
    else: 
        l_update_outcome= 'failed'
        l_error= f'Impossibile avviare la versione aggiornata: eseguita invece la versione di default ({l_current_version})'
    if l_update_pending == 'True':
        self.m_update_hash= {
            'update_start_date': get_redisI().pers.hget(keywords.sw_update_hash_key, keywords.sw_update_date, p_default=None),
            'update_start_time': get_redisI().pers.hget(keywords.sw_update_hash_key, keywords.sw_update_time, p_default=None),
            'transaction_id': get_redisI().pers.hget(keywords.sw_update_hash_key, keywords.sw_update_transaction_id, p_default=None),
            'update_end_date': helper.dateNow(),
            'update_end_time': helper.timeNow(),
            'update_version_requested': l_update_version_requested,
            'updated_version': l_current_version,
            'update_status': l_update_outcome,
            'error': l_error
        }
        if None in self.m_update_hash.values():
            " errore "
            self.m_logger.error(f"Error preparing startup flow update infos: {self.m_update_hash}")
            self.m_update_hash= {}
        else:
            self.m_data[keywords.evdata_sw_update]= self.m_update_hash
            self.m_logger.info("Sw updated requested forversion {} ".format(self.m_update_hash['updated_version']))
        # In ogni caso elimino le informazioni di aggiornamento dalla cache persistente per evitare un ulterirore riavvio
        get_redisI().pers.delete(keywords.sw_update_hash_key)
    else:
        self.m_update_hash= {}
    #
    self.m_taskFuncList['continue']= True
    self._incTaskId()
    return True

def _workTopicUpdateDone(self, p_data= None):
    """ Invio messaggio di sw updated, se necessario """
    # Ho eseguito un update ?
    if self.m_update_hash:
        # Model
        l_jsonEvt= self.m_jmodel.getSwUpdateDoneModel(self.m_data)
        # Topic dict with data
        self.m_data[keywords.evdata_topic_sw_update_done]= {
            internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
            internal.cmd_key.topic_type:'sw_update_done',
            internal.cmd_key.topic: keywords.topic_sw_update_to_stg,
            internal.cmd_key.evt_name: self.m_evt,
            internal.cmd_key.json: l_jsonEvt,
            internal.cmd_key.trigflow_instance: self
            }
        self.m_logger.info("Sw update done to broker [topic]: "
                   + self.m_data[keywords.evdata_topic_sw_update_done][internal.cmd_key.topic])
        self.m_mainCore['cmd_q'].put(self.m_data[keywords.evdata_topic_sw_update_done])
        #
        self._incTaskId()
        self.m_taskFuncList['continue']= False
        return True
    else:
        # Avvio normale senza update
        self._incTaskId()
        self.m_taskFuncList['continue']= True
        return True

def _workTopicUpdateDoneAnswer(self, p_data= None):
    """ Se ho eseguito un update lavoro la risposta altrimenti passo oltre """
    # Cancello i dati del topic se ho risposta affermativa dal borker
    if self.m_update_hash:
        if not p_data:
            self.m_logger.error("Got empty data to parse")
            self.m_error= True
        elif wrapkeys.getValueDefault(p_data, None, keywords.topic_cmd_key) == keywords.status_error:
            self.m_logger.error("Got KO ")
            self.m_error= True
        elif wrapkeys.getValueDefault(p_data, None, keywords.topic_cmd_key) == keywords.status_ok:
            self.m_logger.info("Got Ok ")
        else:
            self.m_logger.error("Unknown data to parse")
            self.m_error= True
        if self.m_error:
            self.m_logger.error("Got error sending topic {}, proceeding anyway".format(keywords.topic_sw_update_to_stg))
        # Cancellazione chiave redis update hash
        l_res= get_redisI().pers.delete(keywords.sw_update_hash_key)
        if l_res != keywords.redis_error:
            self.m_logger.info("Deleting sw update persistent hash")
        else:
            self.m_logger.error("Can't delete sw update persistent hash key, next request will overwrite this hash")

    # Nothing to do
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _workSetUpNtp(self, p_data=None):
    """Configuro il sistema per la sincronizzazione ntp"""
    if get_config().main.ntp.enabled.get():
        l_timezone = get_config().main.ntp.timezone.get()
        helper.set_timezone(l_timezone)
        self.m_logger.info(f'NTP timezone set up: {l_timezone}')
        get_redisI().updateStatusInfo(
            bus.module.videoserver,
            redis_keys.rip_status_field.ntp_synced,
            general.dato_non_disp
        )
    else:
        self.m_logger.info('NTP not enabled: skipping...')
        get_redisI().updateStatusInfo(
            bus.module.videoserver,
            redis_keys.rip_status_field.ntp_synced,
            general.status_inactive
        )
    
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True
    


def _workMountSshfsFolder(self, p_data=None):
    """Monto la cartella remota tramite sshfs"""
    get_redisI().set_sshfs_mounted(False)
    if get_config().main.sshfs.stg_folder.get() != '':
        l_mounted = helper.mount_sshfs_folder(
            ip= get_config().main.sshfs.ip.get(),
            user= get_config().main.sshfs.user.get(),
            ssh_key= get_config().main.sshfs.ssh_key.get(),
            their_folder= get_config().main.sshfs.stg_folder.get(),
            my_folder= get_config().main.sshfs.rip_folder.get()
        )
        get_redisI().set_sshfs_mounted(l_mounted)
        if not l_mounted:
            self.m_logger.error('SSHFS remote folder was not mounted')
            self.m_error = True
    else:
        self.m_logger.warning('No remote stg folder was specified in the configuration: the sshfs folder will not be mounted')

    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _workNotifyStartupDone(self, p_data=None):
    self.m_mainCore['cmd_q'].put(buildcmd._buildActionStartupDone())

    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


" ----- MODULES ON ---- "

def _workMosfTXp_on(self, p_data= None):
    """ Richiesta on mosf tx p """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfTxAOff(self, keywords.status_on))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workMosfTXd_on(self, p_data= None):
    """ Richiesta on mosf tx d """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfTxBOff(self, keywords.status_on))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workTrigp_on(self, p_data= None):
    """ Richiesta on trig p """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTriggerAOff(self, keywords.status_on))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True

def _workTrigd_on(self, p_data= None):
    """ Richiesta on trig d """
    if get_config().main.implant_data.configurazione.get() == conf_values.binario.doppio:
        self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTriggerBOff(self, keywords.status_on))
        self._incTaskId()
        self.m_taskFuncList['continue']= False
        return True
    else:
        self._incTaskId()
        self.m_taskFuncList['continue']= True
        return True

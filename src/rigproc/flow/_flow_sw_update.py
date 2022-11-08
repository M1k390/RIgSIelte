#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raccolta sw update methods

from _flow_sw_update import ..., ...
"""
import os
import shutil

from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons import keywords
from rigproc.commons.wrappers import wrapkeys
from rigproc.commons.helper import helper
from rigproc.params import internal


def _buildFlowUpdate(self):
    """ Creazione task scheduling sw update """
    self.m_taskAll= {
        **self.m_taskBegin,
        **self.m_task_schedule_update,
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
             self._workGetSwUpdatePackage,
             self._workScheduleUpdate,
             self._workTopicSwUpdateScheduled,
             self._workTopicSwUpdateScheduledAnswer,
            self._closePipe],
    'continue': True
}


def _workGetSwUpdatePackage(self, p_data= None):
    """ Prendo il package e lo preparo per l'eventuale aggiornamento
    Il nuovo package va in:
        'package_local_folder'/sw_update_files
    """
    self.m_data[keywords.evdata_scheduled_confirmed]= False

    " cartella locale degli aggiornamenti "
    l_local_folder= wrapkeys.getValueDefault(self.m_input_data, None, keywords.flin_local_update_folder)

    " cartella in cui sono contenuti gli eseguibili "
    l_exec_folder= wrapkeys.getValueDefault(self.m_input_data, None, keywords.flin_exec_folder)

    " cartella remota degli aggiornamenti "
    l_remote_folder= wrapkeys.getValueDefault(self.m_input_data, None, keywords.flin_remote_update_folder)

    " percorso dell'aggiornamento richiesto nella cartella remota "
    l_remote_file_path= wrapkeys.getValueDefault(self.m_input_data, None, keywords.flin_remote_update_path)

    if None in [l_local_folder, l_exec_folder, l_remote_folder, l_remote_file_path]:
        self.m_logger.error('Error in reading folder information to unzip sw update.' + ','.join([
            f' {l_var}: {l_val}' for l_var, l_val in zip(
                ['Local folder', 'Executables folder', 'Remote folder', 'Remote file path'],
                [l_local_folder, l_exec_folder, l_remote_folder, l_remote_file_path]
            )
        ]))
        self.m_error= True
        # Ending task
        self._incTaskId()
        self.m_taskFuncList['continue']= True
        return True

    " percorso dello zip di aggiornamento dal punto di vista del RIP (cartella remota + path) "
    l_remote_zip= helper.join_paths(l_remote_folder, l_remote_file_path)

    " nome del file zip "
    l_file_name= helper.file_name_from_path(l_remote_file_path)

    " variabili di stato dell'operazione "
    l_server_online= False
    l_remote_folder_exists= False
    l_local_folder_exists= False
    l_copy_success= False
    l_extraction_success= False
    l_chmod_success= False

    " verifico la connessione col server "
    l_server_ip= get_config().main.sshfs.ip.get()
    l_server_online= helper.ping(l_server_ip)

    " verifico l'esistenza della cartella remota "
    if l_server_online:
        self.m_logger.debug(f'Server online at {l_server_ip}')
        l_remote_folder_exists= helper.dir_exists(l_remote_folder)
    else:
        self.m_logger.error(f'Connection error: could not reach {l_server_ip}')

    " verifico l'esistenza della cartella locale, e all'occorrenza la creo "
    if l_remote_folder_exists:
        self.m_logger.debug(f'Remote folder found: {l_remote_folder}')
        l_local_folder_exists= helper.dir_exists_create(l_local_folder)
    else:
        self.m_logger.error(f'Remote folder {l_remote_folder} does not exist: cannot download the update zip')
    
    if l_local_folder_exists:
        " copio lo zip dalla cartella remota a quella locale "
        l_local_zip= helper.join_paths(l_local_folder + l_file_name)
        try:
            self.m_logger.debug(f'Copying... Local: {l_local_zip}. Remote: {l_remote_zip}')
            l_copy_success= helper.copy_file(l_remote_zip, l_local_zip)
        except Exception as e:
            self.m_logger.error(f'Impossible to copy the zip file locally: {e}')

    " unzip "
    if l_copy_success:
        self.m_logger.debug("Unzipping {}".format(l_local_zip))
        l_extraction_success= helper.unzip_file(l_local_zip, l_exec_folder)

    " make executable "
    if l_extraction_success:
        self.m_logger.debug('Changing permission of extracted files (making executable)')
        l_conversions= []
        for file_name in helper.get_zip_members(l_local_zip):
            file_path= helper.join_paths(l_exec_folder, file_name)
            l_converted= helper.make_file_executable(file_path)
            l_conversions.append(l_converted)
            if not l_converted:
                break
        l_chmod_success= len(l_conversions) > 0 and all(l_conversions)
        if not l_chmod_success:
            # Try removing extracted files
            for file_name in helper.get_zip_members(l_local_zip):
                file_path= helper.join_paths(l_exec_folder, file_name)
                helper.remove_file(file_path)

    " confirm "
    if l_chmod_success:
        self.m_logger.info(f'Update zip successfully extracted in {l_exec_folder}')
        self.m_data[keywords.evdata_scheduled_confirmed]= True
    else:
        self.m_logger.error('Update preparation failed')
        self.m_error= True

    # Ending task
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _workScheduleUpdate(self, p_data= None):
    """ Salvataggio dati schedulazione aggiornamento """

    if self.m_data[keywords.evdata_scheduled_confirmed]== True:
        l_sched_date= wrapkeys.getValueDefault(self.m_data, None, keywords.flin_schedule_date)
        l_sched_time= wrapkeys.getValueDefault(self.m_data, None, keywords.flin_schedule_time)
        l_version= wrapkeys.getValueDefault(self.m_data, None, keywords.flin_update_version)
        l_trans_id= wrapkeys.getValueDefault(self.m_data, None, keywords.flin_trans_id)
        if None in [l_sched_date, l_sched_time, l_version, l_trans_id]:
            self.m_logger.error(f'Bad update data. Date: {l_sched_date}, time: {l_sched_time}, vers: {l_version}, trans. ID: {l_trans_id}')
            self.m_error= True
        # Scrittura in redis pers.
        # TODO controlloare anche version.. ?
        if l_sched_date and l_sched_time and l_trans_id:
            l_res = [] # variabile per verificare che tutte le scritture in Redis abbiano successo
            l_redisI= get_redisI()
            l_res.append(l_redisI.pers.hset(keywords.sw_update_hash_key, keywords.sw_update_date, l_sched_date))
            l_res.append(l_redisI.pers.hset(keywords.sw_update_hash_key, keywords.sw_update_time, l_sched_time))
            l_res.append(l_redisI.pers.hset(keywords.sw_update_hash_key, keywords.sw_update_version, l_version))
            l_res.append(l_redisI.pers.hset(keywords.sw_update_hash_key, keywords.sw_update_transaction_id, l_trans_id))
            l_res.append(l_redisI.pers.hset(keywords.sw_update_hash_key, keywords.sw_update_mark_as_waiting, 'False'))
            if keywords.redis_error not in l_res:
                self.m_logger.info("Scheduling sw update at {} - {}".format(l_sched_date, l_sched_time))
            else:
                self.m_logger.error(f"Can't set redis persistent data hashes for sw update")
                self.m_error= True
        else:
            self.m_logger.error("Missing basic data from stg sw update topic request")
            self.m_error= True

        if self.m_error or self.m_criticalError:
            self.m_data[keywords.evdata_scheduled_confirmed]= False
            # Clear eventuale chiavi di aggiornamento
            if get_redisI().persistent_deleteField(keywords.sw_update_hash_key) == keywords.redis_error:
                self.m_logger.critical(f"Can't delete redis persistent hashes for sw update on error")
                self.m_error= True
                self.m_criticalError= True
    else:
        self.m_logger.warning("Can't schedule sw update..i'm sorry")

    # Ending task
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _workTopicSwUpdateScheduled(self, p_data= None):
    """
    Invio topic che informa stg riguardo all'operazione di scheduling
    """
    l_jsonEvt= self.m_jmodel.getSwUpdateScheduledModel(self.m_data)
    self.m_data[keywords.evdata_topic_evt_sw_to_stg]= {
        internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
        internal.cmd_key.topic_type:'topic_sw_update',
        internal.cmd_key.topic: keywords.topic_sw_update_to_stg,
        internal.cmd_key.evt_name: self.m_evt,
        internal.cmd_key.json: l_jsonEvt,
        internal.cmd_key.trigflow_instance: self
        }
    self.m_logger.info("Json model to asnwer sw update schedule request")
    self.m_mainCore['cmd_q'].put(self.m_data[keywords.evdata_topic_evt_sw_to_stg])
    # End task
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _workTopicSwUpdateScheduledAnswer(self, p_data= None):
    """ Check invio json al topic conferma schedulazione sw update """
    if not p_data:
        self.m_logger.error("Got empty data to parse")
        self.m_error= True
    elif wrapkeys.getValueDefault(p_data, None, keywords.topic_cmd_key) == keywords.status_error:
        self.m_logger.error("Got KO")
        self.m_error= True
    elif wrapkeys.getValueDefault(p_data, None, keywords.topic_cmd_key) == keywords.status_ok:
        self.m_logger.info("Got OK")
    else:
        self.m_logger.error("Unknown data to parse")
        self.m_error= True
    " si prosegue lo stesso "
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

    
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server data handling
"""

from collections.abc import Iterable
import pdb
import json

from rigproc.commons.redisi import get_redisI
from rigproc.commons import keywords
from rigproc.commons.helper import helper
from rigproc.commons.wrappers import wrapkeys
from rigproc.params import anomalies, internal, redis_keys


def bus_build_cmd(p_data) -> dict:
    """ Invio di comando tramite l funzioni io di build 
    con dentro i dati p_data """
    l_ret={}
    l_ret['io_cmd']= p_data['io_cmd']
    l_ret['data']= p_data['data']
    return l_ret

def flow_build_cmd(p_data) -> dict:
    """ Geenrazione dizionario comando creazione trig flow """
    l_ret={}
    l_ret[internal.cmd_key.cmd_type]= p_data['cmd_type']
    l_ret[internal.cmd_key.action_type]= p_data['action_type']
    l_ret[internal.cmd_key.request_id]= f'client_{helper.timestampNow()}'
    return l_ret

def reset_conf_build_cmd(p_data) -> dict:
    """ Genrazione dizionario comando reset configurazione """
    l_ret= {
        internal.cmd_key.cmd_type: internal.cmd_type.reset_conf
    }
    return l_ret

def reboot_rigcam_build_cmd(p_data) -> dict:
    """ Generazione dizionario comando riavvio rigcam """
    l_ret = {
        internal.cmd_key.cmd_type: internal.cmd_type.reboot_rigcam
    }
    return l_ret


def handleData(p_mainCore, p_decData, p_logger) -> dict:
    """ Gestice la richiesta deserializzata ed inietta i dati richiesti 
    sulle code del main proc
    dict{
        req_type: [bus_cmd, ]
            io_cmd: io_cmd (cmd_mtx_vel_a ...)
            data: data 
        }
    """
    l_redisI= get_redisI()
    l_ret={}
    # Non dict input data
    if not isinstance(p_decData, dict):
        l_ret['res']= False
        l_ret['infos']= "Desiarilized data is not a dictionary "
        return l_ret

    # Richiesta invio cmd su bus 485
    if p_decData['req_type'] == keywords.client_req_bus_cmd:
        # Controlli formattazione comando
        if 'io_cmd' not in p_decData.keys():
            l_ret['res']= False
            l_ret['infos']= "io_cmd key not found"
            return l_ret
        if 'io_q' not in p_mainCore.keys():
            l_ret['res']= False
            l_ret['infos']= "io_cmd key not found"
            return l_ret
        # Creazione comando inserimento sulla coda io_q
        l_cmd = bus_build_cmd(p_decData)
        p_mainCore['io_q'].put(l_cmd)
        l_ret['res']= True
        return l_ret

    # Richiesta trig eventtrigflow
    if p_decData['req_type'] == keywords.client_req_trig_flow:
        # Controlli formattazione comando
        if 'cmd_type' not in p_decData.keys():
            l_ret['res']= False
            l_ret['infos']= "cmd_type key not found"
            p_logger.error('Ricevuta richiesta avvio flow senza campo "cmd_type"')
            return l_ret
        if 'action_type' not in p_decData.keys():
            l_ret['res']= False
            l_ret['infos']= "action_type key not found"
            p_logger.error('Ricevuta richiesta avvio flow senza campo "action_type"')
            return l_ret
        # Creazione comando ed inserimento sulla coda main proc comandi
        l_cmd= flow_build_cmd(p_decData)
        p_mainCore['cmd_q'].put(l_cmd)
        p_logger.debug(f'Inserita in coda richiesta di esecuzione flow {p_decData["cmd_type"]}, {p_decData["action_type"]} da parte del client')
        l_ret['res']= True
        l_ret['infos']= l_cmd[internal.cmd_key.request_id]
        return l_ret

    # Richesta simulation
    if p_decData['req_type'] == keywords.client_req_simulation:
        if p_decData['sim_type'] == 'camera_trig':
            # Lancio manuale evento simulato acq camera
            # Ha senso se hai anche il bus simulato o fake collegato
            p_mainCore['fake_camera'].fakeEventTrig()
            return {'req_type': 'simulation', 'sim_type': 'camera_trig'}
        
    # Richiesta controllo terminazione flow
    if p_decData['req_type'] == keywords.client_req_check_term:
        """
        Cerca in Redis il flow corrispondende alla request ID
        e verifica se è presente un timestamp di stop
        In caso affermativo ritorna "ok", altrimenti "ko"
        """
        l_ret['res']= False
        if 'data' not in p_decData.keys():
            l_ret['infos']= 'Error: key "data" containing the request_id is missing in the request'
            return l_ret
        l_request_id= p_decData['data']
        l_flow_keys= l_redisI.cache.hkeys(keywords.key_flow_log)
        l_stop= False
        for l_key in l_flow_keys:
            if l_request_id in l_key:
                l_flow_data= l_redisI.cache.hget(keywords.key_flow_log, l_key)
                try:
                    l_flow_data= json.loads(l_flow_data)
                except Exception as e:
                    l_ret['infos']= f'Server error reading flow data from Redis cache: {e}'
                    return l_ret
                l_stop_time= wrapkeys.getValueDefault(l_flow_data, None, keywords.flow_stop_time)
                l_stop= l_stop_time is not None
                break
        l_ret['infos']= keywords.status_ok if l_stop else keywords.status_ko
        l_ret['res']= True
        return l_ret

    # Richiesta parametri nella cache di Redis
    if p_decData['req_type'] == keywords.client_req_get_cache_data:
        """
        Il parametro 'data' è un dict contenente hash e key del dato che si richiede al server
        {
            'hash': HASH,
            'key': KEY
        }
        Può essere inserita solo la key se si richiede un dato senza hash
        Se sono inseriti i parametri zrange_start e zrange_end, il server cerca i dati con zrange
        """        
        try:
            l_data= p_decData['data']
            if 'key' in l_data.keys():
                if 'hash' in l_data.keys():
                    l_res= l_redisI.cache.hget(l_data['hash'], l_data['key'])
                elif 'zrange_start' in l_data.keys() and 'zrange_end' in l_data.keys():
                    l_res= l_redisI.cache.zrange(
                        l_data['key'], 
                        l_data['zrange_start'],
                        l_data['zrange_end']
                    )
                else:
                    l_res= l_redisI.cache.get(l_data['key'])
            elif 'hash' in l_data.keys():
                l_res= l_redisI.cache.hkeys(l_data['hash'])
            else:
                l_res= None
        except Exception as e:
            l_ret['res']= False
            l_ret['infos']= f"Error parsing cache data request: {e}"
            return l_ret
        if l_res is None:
            l_ret['res']= False
            l_ret['infos']= 'Malformed cache data request'
            return l_ret
        l_ret['infos']= l_res
        l_ret['res']= True
        return l_ret

    # Richiesta eliminazione dati in cache
    if p_decData['req_type'] == keywords.client_req_delete_cache_data:
        """ Elimina una key o una hash-key sulla cache di Redis """
        try:
            l_data= p_decData['data']
            if 'key' in l_data.keys():
                if 'hash' in l_data.keys():
                    l_res= l_redisI.cache.hdel(l_data['hash'], l_data['key'])
                else:
                    l_res= l_redisI.cache.delete(l_data['key'])
            elif 'hash' in l_data.keys():
                l_res= l_redisI.cache.delete(l_data['hash'])
            else:
                l_res= None
        except Exception as e:
            l_ret['res']= False
            l_ret['infos']= f"Error parsing cache data delete request: {e}"
            return l_ret
        if l_res is None:
            l_ret['res']= False
            l_ret['infos']= 'Malformed cache data delete request'
            return l_ret
        l_ret['infos']= l_res
        l_ret['res']= True
        return l_ret

    # Richiesta controllo msg_sorted in Redis (inviare il dato intero al client può superare il limite della connessione socket)
    if p_decData['req_type'] == keywords.client_req_check_msg_sorted:
        """ Controlla l'esistenza di un parametro in msg sorted """
        try:
            l_command= p_decData['cmd']
        except Exception as e:
            l_ret['infos']= f'msg_sorted check request badly formatted: {e}'
            l_ret['res']= False
            return l_ret
        msg_sorted= l_redisI.cache.zrange(keywords.key_redis_msg_sorted_set, 0, -1)   
        for msg_data in reversed(msg_sorted):
            try:
                msg= json.loads(msg_data)
                if msg is not None and msg['valid'] and msg['io_cmd'] == l_command:
                    l_ret['res']= True
                    l_ret['infos']= True
                    return l_ret
            except:
                continue
        l_ret['infos']= False
        l_ret['res']= True
        return l_ret

    # Richiesta parametro di stato
    if p_decData['req_type'] == keywords.client_req_status_param:
        """ Restituisce il parametro di stato richiesto (da Redis) """
        try:
            l_module= p_decData['data']['module']
            l_status_key= p_decData['data']['status_key']
        except Exception as e:
            l_ret['infos']= f'status parameter request badly formatted: {e}'
            l_ret['res']= False
            return l_ret
        l_status= l_redisI.getStatusInfo(l_module, l_status_key)
        l_ret['infos']= l_status
        l_ret['res']= True
        return l_ret

    # Richiesta di reset dello stato del sistema su Redis
    if p_decData['req_type'] == keywords.client_req_reset_status:
        """ Resetta tutti i parametri di stato """
        for l_module, l_params_data in anomalies.status_default.items():
            for l_param, l_value in l_params_data.items():
                l_redisI.updateStatusInfo(l_module, l_param, l_value)
        l_ret['infos']= True
        l_ret['res']= True
        return l_ret

    # Richiesta parametri di configurazione
    if p_decData['req_type'] == keywords.client_req_conf:
        l_conf= l_redisI.getImplantData()
        if l_conf != {}:
            l_ret['res']= True
            l_ret['infos']= l_conf
        else:
            l_ret['res']= False
            l_ret['infos']= 'impossibile acquisire la configurazione, riprovare'
        return l_ret

    # Richiesta per il reset della configurazione
    if p_decData['req_type'] == keywords.client_req_reset_conf:
        l_cmd= reset_conf_build_cmd(p_decData)
        p_mainCore['cmd_q'].put(l_cmd)
        l_ret['res']= True
        l_ret['info']= keywords.status_ok
        return l_ret

    # Richiesta iscrizione a STG
    if p_decData['req_type'] == keywords.client_req_subscription:
        l_cmd= flow_build_cmd({
            'cmd_type': 'cmd_action',
            'action_type': keywords.action_subscribe
        })
        p_mainCore['cmd_q'].put(l_cmd)
        l_ret['res']= True
        l_ret['info']= keywords.status_ok
        return l_ret
    
    # Richiesta cronologia messaggi bus
    if p_decData['req_type'] == internal.client_req.bus_history:
        l_history= l_redisI.get_bus_history_formatted()
        if isinstance(l_history, str):
            l_ret['res']= True
            l_ret['info']= l_history
        else:
            l_ret['res']= False
            l_ret['info']= 'error'
        return l_ret

    # Richiesta riavvio rigcam
    if p_decData['req_type'] == internal.client_req.reboot_rigcam:
        l_cmd= reboot_rigcam_build_cmd(p_decData)
        p_mainCore['cmd_q'].put(l_cmd)
        l_ret['res']= True
        l_ret['info']= keywords.status_ok
        return l_ret

    # Richiesta memoria in uso
    if p_decData['req_type'] == internal.client_req.mem_usage:
        l_rigproc_ts, l_rigproc_mem = l_redisI.get_rigproc_mem_usage()
        l_rigcam_ts, l_rigcam_mem = l_redisI.get_rigcam_mem_usage()
        l_mem_report = \
            f'rigproc: {l_rigproc_ts} {l_rigproc_mem} MB\n' +\
            f'rigcam:  {l_rigcam_ts} {l_rigcam_mem} MB'
        l_ret['res'] = True
        l_ret['info'] = l_mem_report
        return l_ret

    # Richiesta uptime
    if p_decData['req_type'] == internal.client_req.uptime:
        l_uptime = l_redisI.get_rigproc_uptime()
        l_uptime_formatted = helper.seconds_to_formatted(l_uptime)
        if l_uptime_formatted is not None:
            l_ret['res'] = True
            l_ret['info'] = l_uptime_formatted
        else:
            l_ret['res'] = False
            l_ret['info'] = 'error'
        return l_ret

    # Richiesta conteggio scatti
    if p_decData['req_type'] == internal.client_req.shoot_count:
        l_shoot_count = l_redisI.get_shoot_count()
        if l_shoot_count is not None:
            l_ret['res'] = True
            l_ret['info'] = f'Total shoots: {l_shoot_count}'
        else:
            l_ret['res'] = False
            l_ret['info'] = 'error'
        return l_ret
    
    # Richiesta storico temperature
    if p_decData['req_type'] == internal.client_req.temp_hist:
        l_temp_hist = l_redisI.get_temp_measures_formatted()
        if l_temp_hist is not None:
            l_ret['res'] = True
            l_ret['info'] = l_temp_hist
        else:
            l_ret['res'] = False
            l_ret['info'] = 'error'
        return l_ret

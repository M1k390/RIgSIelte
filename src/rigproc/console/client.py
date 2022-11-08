#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
socket terminal client per la console di iniezione comandi
"""

import argparse
import socket
import pickle
import struct
import json

from rigproc.commons import keywords
from rigproc.params import internal


trig_list={
    keywords.flow_type_diagnosis: keywords.action_diagnosis_flow,
    keywords.flow_type_implant_status: keywords.action_implant_status_flow,
    keywords.flow_type_sw_update: keywords.action_update_flow,
    keywords.flow_type_shutdown: keywords.action_shut_down_flow,
    keywords.flow_type_shutdown_aborted: keywords.action_shut_down_aborted_flow,
    keywords.flow_type_power_check: keywords.action_periodic_flow
}

simulation_list={
    'camera_trig',
}

cmd_list={
    'bus':[keywords.cmd_stop, keywords.cmd_restart] + list(keywords.bus_cmds.keys()),
    'flows': trig_list,
    'sim': simulation_list,
}



def list_all_cmd():
    """ print di tutti i comandi disponibili """
    for types in cmd_list.keys():
        print(types)
        for cmd in cmd_list[types]:
            print("  {}".format(cmd))

def list_bus_cmd():
    """ print di tutti i comandi disponibili """
    for cmd in cmd_list['bus']:
        print("  {}".format(cmd))

def list_sim_cmd():
    """ Lsita simulazioni esterne disponibili """
    for cmd in cmd_list['sim']:
        print("  {}".format(cmd))

def connect_and_send(p_data, ip='127.0.0.1', port=9999):
    """ Connetto, invio, attendo risposta, esco """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        try:
            sock.connect((ip, port))
            sock.sendall(p_data)
            # Answer
            l_buf= b''
            while len(l_buf) < 4:
                l_rec = sock.recv(4 - len(l_buf))
                if len(l_rec) > 0:
                    #print('Leggo la lunghezza della risposta...')
                    l_buf += l_rec
            l_dataLen= struct.unpack('!I', l_buf)[0]
            #print(f'Lunghezza risposta: {l_dataLen}')
            data= b''
            while len(data) < l_dataLen:
                l_rec= sock.recv(l_dataLen - len(data))
                if len(l_rec) > 0:
                    data += l_rec
                    #print(f'Scarico la risposta... ({len(data)}/{l_dataLen} bytes)')
            decoded_data= pickle.loads(data)
            return decoded_data
        except Exception as e:
            print(f'Errore di connessione al server ({type(e)}): {e}')
    return None

def packData(p_data) -> bytes:
    """ Packing dati """
    l_serialized= pickle.dumps(p_data)
    l_len= struct.pack('!I', len(l_serialized))
    l_serialized= l_len+ l_serialized
    return l_serialized

def build_bus_cmd(p_cmd, p_data):
    """ Parso e preparo il comando bus  da iniettare nel main proc """
    if p_cmd not in cmd_list['bus']:
        print("unknown bus cmd requested")
        return None
    # preparo il cmd
    l_cmd={}
    l_cmd['req_type']= keywords.client_req_bus_cmd
    l_cmd['io_cmd']= p_cmd
    if p_data == None:
        p_data= b'0000'
    l_cmd['data']= p_data
    return l_cmd

def build_trig_cmd(p_cmd, p_data):
    """ Creazione comando richeista trig flow """
    if p_cmd not in trig_list:
        print(f"unknown trig cmd requested: {p_cmd}")
        return None
    l_cmd={}
    l_cmd['req_type']= keywords.client_req_trig_flow
    l_cmd['cmd_type']= 'cmd_action'
    l_cmd['action_type']= trig_list[p_cmd]
    l_cmd['data']= ''
    return l_cmd

def build_sim_cmd(p_cmd, p_data):
    """ Build comando simulazione evento esterno """
    if p_cmd not in simulation_list:
        print(f"unknown sim cmd requested: {p_cmd}")
        return None
    l_cmd={}
    l_cmd['req_type']= keywords.client_req_simulation
    l_cmd['sim_type']= 'camera_trig'
    l_cmd['data']= ''
    return l_cmd

def build_flow_termination_request(p_cmd, p_data):
    """ comando per verificare la terminazione di un flow sul server """
    l_cmd={}
    l_cmd['req_type']= keywords.client_req_check_term
    l_cmd['data']= p_data # Request ID
    return l_cmd

def build_cache_data_request(p_cmd, p_data):
    """ comando per richiedere dei dati dalla cache di Redis sul server 
    p_data deve indicare gli hash e le chiavi per trovare i dati su Redis,
    che possono essere individuati in commons.keywords
    p_data è formattato così: [{'hash': HASH, 'key': KEY}, ...]
    """
    l_cmd= {}
    l_cmd['req_type']= keywords.client_req_get_cache_data
    l_cmd['data']= p_data
    return l_cmd

def build_delete_cache_data_request(p_cmd, p_data):
    """ comando per richiedere dei dati dalla cache di Redis sul server 
    p_data deve indicare gli hash e le chiavi per trovare i dati su Redis,
    che possono essere individuati in commons.keywords
    p_data è formattato così: [{'hash': HASH, 'key': KEY}, ...]
    """
    l_cmd= {}
    l_cmd['req_type']= keywords.client_req_delete_cache_data
    l_cmd['data']= p_data
    return l_cmd

def build_check_msg_sorted_request(p_cmd, p_data):
    """ comando per richiedere il check della presenza di un cmd in msg_sorted, nella cache di Redis
    """
    l_cmd= {}
    l_cmd['req_type']= keywords.client_req_check_msg_sorted
    l_cmd['cmd']= p_data
    return l_cmd

def build_status_param_request(p_cmd, p_data):
    """ comando per richiedere un parametro di stato """
    l_cmd= {}
    l_cmd['req_type']= keywords.client_req_status_param
    l_cmd['data']= p_data
    return l_cmd

def build_reset_status_request(p_cmd, p_data):
    """ comando per richiedere il reset dei parametri di stato """
    l_cmd= {}
    l_cmd['req_type']= keywords.client_req_reset_status
    return l_cmd

def build_conf_request(p_cmd, p_data):
    """ comando per ottenere la configurazione
    """
    l_cmd= {
        'req_type': keywords.client_req_conf
    }
    return l_cmd

def build_reset_conf_request(p_cmd, p_data):
    """ comando per resettare la configurazione
    è possibile inserire una configurazione nuova come dict in p_data
    """
    l_cmd= {
        'req_type': keywords.client_req_reset_conf
    }
    return l_cmd

def build_subscription_request(p_cmd, p_data):
    """ comando per inviare una richiesta di iscrizione sul topic apposito a STG """
    l_cmd= {
        'req_type': keywords.client_req_subscription
    }
    return l_cmd

def build_bus_history_request(p_cmd, p_data):
    l_cmd= {
        'req_type': internal.client_req.bus_history
    }
    return l_cmd

def build_reboot_rigcam_request(p_cmd, p_data):
    l_cmd= {
        'req_type': internal.client_req.reboot_rigcam
    }
    return l_cmd

def build_memory_usage_request(p_cmd, p_data):
    l_cmd= {
        'req_type': internal.client_req.mem_usage
    }
    return l_cmd

def build_uptime_request(p_cmd, p_data):
    l_cmd= {
        'req_type': internal.client_req.uptime
    }
    return l_cmd

def build_shoot_count_request(p_cmd, p_data):
    l_cmd= {
        'req_type': internal.client_req.shoot_count
    }
    return l_cmd

def build_temp_hist_request(p_cmd, p_data):
    l_cmd= {
        'req_type': internal.client_req.temp_hist
    }
    return l_cmd


if __name__ == "__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument("-s","--serverip", help= "server ip", default= "127.0.0.1", type =str)
    parser.add_argument("-p","--serverport", help= "server port", default=9999 ,type =int)
    parser.add_argument("-cbus","--cmdbus", help= "identificicativo comando da eseguire", type =str)
    parser.add_argument("-cflow","--cmdflow", help= "identificicativo trig flow da eseguire", type =str)
    parser.add_argument("-csim","--cmdsim", help= "identificicativo simulazione da eseguire", type =str)
    parser.add_argument("-la","--listall", help= "lista tutti i comandi disponibili", action= "store_true")
    parser.add_argument("-lb","--listbus", help= "lista i comandi per il bus seriale", action= "store_true")
    parser.add_argument("-lt","--listtrig", help= "lista i comandi trig flows", action= "store_true")
    parser.add_argument("-ls","--listsim", help= "lista i comandi simulazione esterne", action= "store_true")
    parser.add_argument("-rs", "--resetstatus", help= "reset parametri di stato", action= "store_true")
    parser.add_argument("-rc","--resetconf", help= "reset configurazione", action= "store_true")
    parser.add_argument("-sc","--setconf", help= "reset configurazione", type= str)
    parser.add_argument("-i", "--iscrizione", help="iscrizione al server STG", action="store_true")
    parser.add_argument("-bh", "--bushistory", help="lista messaggi bus", action="store_true")
    parser.add_argument("-rrc", "--rebootrigcam", help= "riavvia rigcam", action="store_true")
    parser.add_argument("-mem", "--memory", help= "memoria usata", action="store_true")
    parser.add_argument("-ut", "--uptime", help= "uptime di rigproc", action="store_true")
    parser.add_argument("-shc", "--shootcount", help= "conteggio scatti dal boot", action="store_true")
    parser.add_argument("-th", "--temphist", help="storico delle temperature rilevate", action="store_true")
    parser.add_argument("-o", "--output", help="file di output", type=str)
    parser.add_argument("-t", "--terminal", help="stampa risposta a terminale", action="store_true")
    
    args= parser.parse_args()
    # Listing cmds
    if args.listall:
        list_all_cmd()
    if args.listbus:
        list_bus_cmd()
    if args.listsim:
        list_sim_cmd()

    # cmds
    l_serData= b''
    if args.cmdbus != None:
        l_serData= build_bus_cmd(args.cmdbus, None)
    if args.cmdflow != None:
        l_serData= build_trig_cmd(args.cmdflow, None)
    if args.cmdsim != None:
        l_serData= build_sim_cmd(args.cmdsim, None)
    if args.resetstatus:
        l_serData= build_reset_status_request(None, None)
    if args.resetconf:
        l_serData= build_reset_conf_request(None, None)
    if args.setconf != None:
        l_serData= build_reset_conf_request(None, json.loads(args.setconf))
    if args.iscrizione:
        l_serData= build_subscription_request(None, None)
    if args.bushistory:
        l_serData= build_bus_history_request(None, None)
    if args.rebootrigcam:
        l_serData= build_reboot_rigcam_request(None, None)
    if args.memory:
        l_serData = build_memory_usage_request(None, None)
    if args.uptime:
        l_serData = build_uptime_request(None, None)
    if args.shootcount:
        l_serData = build_shoot_count_request(None, None)
    if args.temphist:
        l_serData = build_temp_hist_request(None, None)

    if l_serData:
        l_serData= packData(l_serData)
        l_res= connect_and_send(l_serData, args.serverip, args.serverport)
        if l_res and args.output:
            with open(args.output, 'w') as f:
                f.write(l_res['info'])
        if l_res and args.terminal:
            print(l_res['info'])







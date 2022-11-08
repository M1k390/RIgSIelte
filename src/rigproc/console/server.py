#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Console di accesso esecuzione task asincroni
Accesso :
    - soket 
        permette connessioni dall'esterno

Comandi :
    - tutti i comandi bus
        con verifica risposte
    - creazione trig flow
        - con immagini?
        - con invocazione fake camera?


Arch:

    Server:
        si aggancia al main proc ed alle code comandi
        attende i comandi dal client
        ripete i dati di lavoro e le risposte al client
        quindi potrebbe fare anche da debugger

    Client:
        programma autonomo di invio comandi al server

"""

import threading
import socket
import pickle
import struct
import sys
import time

from rigproc.commons.config import get_config
from rigproc.console import handledata
from rigproc.commons.logger import logging_manager

class ConsoleServer():
    """ TCP console server """

    def __init__(self) -> None:
        """
        Config dal conf.json con indirizzi e parametri vari
        """
        self.m_config= get_config().main.console
        self.m_ip= self.m_config.server.ip.get()
        self.m_port= int(self.m_config.server.port.get())
        self.m_stop= False
        self.m_logger= logging_manager.generate_logger(
            logger_name='console',
            format_code=get_config().logging.console.format.get(),
            console_level=get_config().logging.console.console_level.get(),
            file_level=get_config().logging.console.file_level.get(),
            log_file_name=get_config().logging.console.file_name.get(),
            log_file_dir=get_config().logging.console.file_dir.get(),
            log_file_mode=get_config().logging.console.file_mode.get(),
            root_log_file_prefix=get_config().logging.root.file_name.get() \
                if get_config().logging.console.log_to_root.get() else None,
            root_log_dir=get_config().logging.root.file_dir.get() \
                if get_config().logging.console.log_to_root.get() else None,
            formatter_setting=get_config().logging.console.formatter.get()
        )
        self.m_logger.info("Instance created")
        self.m_thread= threading.Thread(target= self._run)

    " --- PUBLIC IFACE --- "

    def start(self, p_mainCore) -> None:
        """ Start runnable
            
        p_mainCore: dict
            Dizionario con tutti gli elementi importati del main proc
            per accedere alle code comandi ecc..
        """
        self.m_mainCore= p_mainCore
        self.m_thread.start()

    def close(self) -> None:
        """ Chiusura server"""
        self.m_stop= True

    def wait(self) -> None:
        self.m_thread.join()
        self.m_logger.info("Thread joined")

    " ---- THREADING ---- "

    def _run(self) -> None:
        """Avvia il server e rimane in ascolto"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            socket_connected= False
            attempts_timeout= 5
            while not socket_connected and not self.m_stop:
                try:
                    sock.bind((self.m_ip, self.m_port))
                    socket_connected= True
                except Exception as e:
                    self.m_logger.error(f'Cannot connect socket to {self.m_ip}:{self.m_port} ({type(e)}): {e}')
                    self.m_logger.debug(f'Trying again in {attempts_timeout} seconds')
                    time.sleep(attempts_timeout)
            sock.settimeout(2)
            sock.listen(1)
            self.m_logger.info("Server started at {}:{}".format(self.m_ip, self.m_port))
            while not self.m_stop:
                try:
                    conn, addr= sock.accept()
                    l_buf= b''
                    while len(l_buf) < 4:
                        l_buf += conn.recv(4 - len(l_buf))
                    l_dataLen= struct.unpack('!I', l_buf)[0]
                    data= b''
                    while len(data) < l_dataLen:
                        data= conn.recv(l_dataLen - len(data))
                    decoded_data= self.decodeServerData(data)
                    self.m_logger.info(f'Received request from client: {decoded_data}')
                    # gestisce i dati in arrivo deserializzati
                    l_ret = handledata.handleData(self.m_mainCore, decoded_data, self.m_logger)
                    l_ret_dumped= pickle.dumps(l_ret)
                    l_len= len(l_ret_dumped)
                    l_len_dumped= struct.pack('!I', l_len)
                    conn.sendall(l_len_dumped + l_ret_dumped)
                    self.m_logger.info(f'Answer sent to console client ({l_len} bytes)')
                except KeyError as e:
                    self.m_logger.error("Key error, ignoring: {}".format(str(e)))
                except EOFError as e:
                    self.m_logger.error("EOF error, ignoring: {}".format(str(e)))
                except socket.timeout:
                    pass
                except Exception as e:
                    self.m_logger.error("Uknown error, ignoring: {}".format(str(e)))

        # uscita
        self.m_logger.info("Exiting server from listening")

    " ----- DATA ----- "

    def decodeServerData(self,p_data) -> dict:
        """ Deserializza il buffer ricevuto """
        return pickle.loads(p_data)







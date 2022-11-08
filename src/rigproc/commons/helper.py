#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
helpers on msgs ed altre funzioni
"""

import platform
import subprocess
import logging
import os
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile
import json
import time
import json
import string
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple, Union, List
import uuid
import asyncio
from confluent_kafka.admin import AdminClient
import ntplib
import socket

import psutil

from rigproc.params import general, internal


# Initialize MAIN and DATA DIRECTORY
try:
    # Se la variabile d'ambiente è stata impostata, usa quella
    MAIN_DIR= os.environ[internal.env.rig_dir]
except:
    # Altrimenti cerca il path relativo
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in bundled executable file
        FILE_DIR = Path(sys.executable).parent
        PARENT_DIR = FILE_DIR.parent
        MAIN_DIR = PARENT_DIR
    else:
        # Running in Python script
        FILE_DIR = Path(__file__).parent
        PARENT_DIR= FILE_DIR.parent
        if os.path.basename(PARENT_DIR) == 'rigproc':
            SRC_DIR= PARENT_DIR.parent
        else:
            SRC_DIR= PARENT_DIR
        MAIN_DIR= SRC_DIR.parent
    MAIN_DIR= str(MAIN_DIR)
DATA_DIR= str(os.path.join(MAIN_DIR, 'data'))


class Helper:
    """
    Wrapper di metodi utili per attività riguardanti gestione di file, logging, networking, ecc...
    Si accede alla classe tramite oggetto singleton.
    I metodi catturano eventuali eccezioni e non le rilanciano.
    """

    def __init__(self):
        self.m_logger= logging.getLogger('root')

    def set_logger(self, logger_name):
        """Imposta un logger specifico se non sto utilizzando helper da rigproc (es: rigcam).
        Se utilizzo l'oggetto singleton, questa operazione va fatta una volta sola."""
        self.m_logger= logging.getLogger(logger_name)

    ############################################################################
    #
    #   SYSTEM
    #
    ############################################################################

    def check_command_existance(self, command: str) -> bool:
        return os.system(f'{command} >/dev/null') == 0

    def get_my_pid(self) -> Optional[int]:
        try:
            return os.getpid()
        except Exception as e:
            self.m_logger.error(f'Error getting process pid ({type(e)}): {e}')
            return None

    def get_process_mem_usage(self, pid) -> Optional[Union[int, float]]:
        try:
            l_process = psutil.Process(pid)
            mem_mb = l_process.memory_info().rss/ (1024*1024)
            return mem_mb
        except Exception as e:
            self.m_logger.error(
                f'Error getting process {pid} memory usage ({type(e)}): {e}'
            )
            return None

    def _parse_elapsed_time_str(self, et_str: str) -> Optional[int]:
        try:
            et_str = et_str.replace('\n', '', -1).replace('ELAPSED', '', -1)
            et_str = et_str.strip()
            if '-' in et_str:
                # Separate days from the rest
                l_days, et_str = et_str.split('-')
                l_days = int(l_days)
                #         0123456789
                # Format: HH:MM:SS
                l_hours = int(et_str[0:2])
                l_mins = int(et_str[3:5])
                l_secs = int(et_str[6:])
                return l_days * 60 * 60 * 24 + l_hours * 60 * 60 + l_mins * 60 + l_secs
            elif et_str.count(':') == 2:
                #         0123456789
                # Format: HH:MM:SS
                l_hours = int(et_str[0:2])
                l_mins = int(et_str[3:5])
                l_secs = int(et_str[6:])
                return l_hours * 60 * 60 + l_mins * 60 + l_secs
            elif et_str.count(':') == 1:
                #         0123456789
                # Format: MM:SS
                l_mins = int(et_str[0:2])
                l_secs = int(et_str[3:])
                return l_mins * 60 + l_secs
            else:
                self.m_logger.error(
                    f'Cannot recognize the "elapsed time" string: {et_str}'
                )
                return None
        except Exception as e:
            self.m_logger.error(
                f'Error parsing "elapsed time" string ({type(e)}): {e}'
            )
            return None

    def get_process_uptime(self, pid) -> Optional[int]:
        """
        Restituisce il tempo di esecuzione del processo corrispondente al pid,
        in secondi.
        """
        try:
            l_cp = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'etime'],
                capture_output=True,
                text=True
            )
        except Exception as e:
            self.m_logger.error(f'Error asking system for uptime ({type(e)}): {e}')
            return None
        return self._parse_elapsed_time_str(l_cp.stdout)

    def kill_process(self, exec_path: str) -> bool:
        try:
            ret_code = os.system(f'killall {exec_path}')
            return ret_code == 0
        except Exception as e:
            self.m_logger.error(
                f'Error killing process {exec_path} ({type(e)}): {e}'
            )
            return False

    def get_cpu_temperature(self) -> Optional[float]:
        """
        This function was tested for the motherboard AAEON EMB-APL1.

        Returns
        -------
        The CPU's temperature in Celsius degrees.
        
        None in case of error.
        """
        SENSOR1 = '/sys/class/thermal/thermal_zone0/temp'
        try:
            with open(SENSOR1, 'r') as f:
                temp = float(f.read()) / 1000
            return temp
        except Exception as e:
            self.m_logger.error(
                f'Error reading the temperature sensor file ({type(e)}): {e}')
            return None

    ############################################################################
    #
    #   FILES AND DIRECTORIES
    #
    ############################################################################

    def relative_to_abs_path(self, relative_path: str, s_file: str) -> str:
        """Genera il percorso di un file a partire dal suo percorso relativo
        (relative_path) rispetto ad un altro file (s_file).\n
        Restituisce una stringa vuota in caso di errore.\n
        Si consiglia di filtrare il percorso di uno script (__file__) 
        con my_path, per trattare correttamente il caso in cui 
        il programma si trovi all'interno di un unico file eseguibile.
        
        Arguments
        ---------
        relative_path: percorso relativo a rispetto a s_file
        s_file: percorso assoluto di un file
        """
        try:
            if os.path.isabs(relative_path):
                return relative_path
            s_file_dir= Path(s_file).parent
            new_path = s_file_dir / relative_path
            return str(new_path)
        except Exception as e:
            self.m_logger.error(f'Error forming relative path ({type(e)}): {e}')
            return ''

    def my_path(self, my_file: str) -> str:
        """Restituisce la posizione del modulo chiamante.
        Se il programma si trova in un file eseguibile, ritorna la posizione del file eseguibile.
        
        Arguments
        ---------
        my_file: path del modulo chiamante (__file__)
        """
        try:
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Sono in un file eseguibile, restituisco la sua posizione
                return str(Path(sys.executable))
            else:
                # Sono in uno script Python: __file__ riporta la posizione corretta
                return my_file
        except Exception as e:
            self.m_logger.error(f'Error determining if the program is running in an executable file ({type(e)}): {e}')
            return my_file

    def file_name_from_path(self, file_path: str) -> str:
        """Restituisce il nome di un file dal suo percorso."""
        try:
            return os.path.basename(file_path)
        except Exception as e:
            self.m_logger.error(f'Error getting file base name from {file_path} ({type(e)}): {e}')
            return file_path

    def dir_from_path(self, file_path: str) -> str:
        """Restituisce la cartella contenente il file al percorso specificato.
        In caso di errore, ritorna una stringa vuota."""
        try:
            if self.dir_exists(file_path):
                return file_path
            else:
                return str(Path(file_path).parent)
        except Exception as e:
            self.m_logger.error(f'Cannot get directory of file {file_path} ({type(e)}): {e}')
            return ''

    def abs_path(self, file_path: str) -> str:
        """Restituisce il percorso assoluto di un file.
        Se il percorso fornito è già assoluto, lo restituisce inalterato.
        Se si tratta di un percorso relativo, lo concatena alla directory principale del programma."""
        try:
            if os.path.isabs(file_path):
                return file_path
            else:
                return os.path.join(MAIN_DIR, file_path)
        except Exception as e:
            self.m_logger.error(f'Error determining absolute path of {file_path} ({type(e)}): {e}')
            return file_path

    def join_paths(self, *paths) -> str:
        """Unisce più percorsi.
        Ritorna una stringa vuota se si verifica un errore"""
        try:
            return os.path.join(*paths)
        except Exception as e:
            self.m_logger.error(f'Error joining paths ({type(e)}): {e}')
            return ''

    def universal_path(self, path: str):
        """Converte il carattere "/" all'interno di un percorso in un carattere universale"""
        try:
            parts= path.split('/')
        except Exception as e:
            self.m_logger.error(f'Error splitting path {path} ({type(e)}): {e}')
            return path
        try:
            if path.startswith('/'):
                path= os.path.join('/', *parts)
            else:
                path= os.path.join(*parts)
            return path
        except Exception as e:
            self.m_logger.error(f'Error rejoining parts of path ({type(e)}): {e}')
            return path

    def clean_file_name(self, file_name: str) -> str:
        """Rimuove o sostituisce da una stringa i caratteri che possono causare problemi al filesystem """
        whitelist= string.ascii_letters + string.digits + '-_.()'
        replace= {
            ' ': '_',
            ':': '-'
        }
        char_limit= 255
        try:
            for src, dst in replace.items():
                file_name= file_name.replace(src, dst)
            file_name= ''.join([c for c in file_name if c in whitelist])
            if len(file_name) > char_limit:
                self.m_logger.warning(f'File name longer than {char_limit} characters: may cause problems with some filesystems.')
        except Exception as e:
            self.m_logger.error(f'Error cleaning file name {file_name} ({type(e)}): {e}')
        return file_name

    def data_file_path(self, file_name: str) -> str:
        """ Ritorna il percorso di un file nella DATA_DIR, dato il suo nome """
        try:
            return os.path.join(DATA_DIR, file_name)
        except Exception as e:
            self.m_logger.error(f'Error forming data file path ({type(e)}): {e}')
            return file_name

    def dir_exists(self, dir_path: str) -> bool:
        """ Verifica l'esistenza di una cartella """
        try:
            return os.path.isdir(dir_path)
        except Exception as e:
            self.m_logger.error(f'Error checking if {dir_path} is a directory ({type(e)}): {e}')
            return False

    def dir_exists_create(self, dir_path: str) -> bool:
        """ Verifica l'esistenza di una cartella 
        Se la cartella non esiste, ne crea il percorso ricorsivamente
        Ritorna True se la cartella esiste o è stata creata correttamente
        Ritorna False se non è stato possibile creare la cartella """
        if dir_path == '':
            return False
        l_exists= self.dir_exists(dir_path)
        if l_exists:
            return True
        else:
            self.m_logger.warning(f'Folder {dir_path} does not exist: creating it')
            try:
                os.makedirs(dir_path)
                return True
            except Exception as e:
                self.m_logger.error(f'Impossible to create dir {dir_path} ({type(e)}): {e}')
                return False

    def file_exists(self, file_path: str) -> bool:
        try:
            return os.path.isfile(file_path)
        except Exception as e:
            self.m_logger.error(f'Error checking if {file_path} is a file ({type(e)}): {e}')

    def file_is_readable(self, file_path: str) -> bool:
        try:
            f= open(file_path, 'r')
            f.close()
            return True
        except:
            return False

    def list_file_names(self, dir_path: str) -> List[str]:
        """Restituisce la lista dei nomi dei file presenti in una cartella.
        Restituisce una lista vuota se si verificano errori"""
        try:
            file_names= []
            for file_name in os.listdir(dir_path):
                file_path= self.join_paths(dir_path, file_name)
                if os.path.isfile(file_path):
                    file_names.append(file_name)
            self.m_logger.debug(f'Found {len(file_names)} files in {dir_path}')
            return file_names
        except Exception as e:
            self.m_logger.error(f'Cannot list files in {dir_path} ({type(e)}): {e}')
            return []

    def count_files(self, dir_path: str) -> int:
        """ Restituisce il numero di files in una cartella """
        return len(self.list_file_names(dir_path))

    def copy_file(self, source_path, dest_path) -> bool:
        """Copia un file"""
        if not self.file_exists(source_path):
            self.m_logger.error(f'Cannot copy {source_path}: the file does not exist')
            return False
        try:
            shutil.copyfile(source_path, dest_path)
            self.m_logger.debug(f'Copied file from {source_path} to {dest_path}')
            return True
        except Exception as e:
            self.m_logger.error(f'Cannot copy {source_path} to {dest_path} ({type(e)}): {e}')
            return False

    def read_file(self, file_path: str) -> List[str]:
        try:
            with open(file_path, 'r') as f:
                return f.readlines()
        except Exception as e:
            self.m_logger.error(
                f'Error reading file {file_path} ({type(e)}): {e}'
            )
            return []

    def write_file(self, file_path: str, content, binary=False) -> bool:
        """ Scrive "content" su file """
        file_dir= str(Path(file_path).parent)
        file_name= self.file_name_from_path(file_path)
        if not self.dir_exists_create(file_dir):
            self.m_logger.error(f'Cannot write file to folder {file_dir}')
            return None
        file_mode= 'wb' if binary else 'w'
        try:
            with open(file_path, file_mode) as f:
                f.write(content)
            if os.path.isfile(file_path):
                self.m_logger.debug(f'Written file {file_name} in folder {file_dir}' + (' (binary mode)' if binary else ''))
                return file_path
            else:
                self.m_logger.error('The written file does not exist')
                return None
        except Exception as e:
            self.m_logger.error(f'Error writing file ({type(e)}): {e}')
            return None

    def get_file_size(self, file_path) -> Optional[int]:
        """ Restituisce la dimensione di un file in bytes """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            self.m_logger.error(f'Cannot read file size of {file_path} ({type(e)}): {e}')
            return None

    def move_file(self, src: str, dest: str, su=False) -> bool:
        cmd_args = []
        if su:
            cmd_args.append('sudo')
        cmd_args += ['mv', src, dest]
        try:
            mv_proc = subprocess.run(cmd_args)
            return mv_proc.returncode == 0
        except Exception as e:
            self.m_logger.error(
                f'Error moving file from "{src}" to "{dest}" ({type(e)}): {e}'
            )
            return False

    def remove_file(self, file_path, su=False) -> bool:
        """Cancella un file"""
        try:
            if su:
                del_proc = subprocess.run(['sudo', 'rm', file_path])
                return del_proc.returncode == 0
            else:          
                os.remove(file_path)
                self.m_logger.debug(f'Deleted file: {file_path}')
                return True
        except Exception as e:
            self.m_logger.error(f'Cannot remove file {file_path} ({type(e)}): {e}')
            return False

    def remove_dir(self, dir_path) -> bool:
        """Elimina una cartella"""
        try:
            os.rmdir(dir_path)
            self.m_logger.debug(f'Deleted directory: {dir_path}')
            return True
        except Exception as e:
            self.m_logger.error(f'Cannot remove directory {dir_path} ({type(e)}): {e}')
            return False

    def unzip_file(self, zip_path: str, dst: str) -> bool:
        """Estrate un file zip nella cartella di destinazione"""
        try:
            with ZipFile(zip_path) as zf:
                zf.extractall(path=dst)
            return True
        except Exception as e:
            self.m_logger.error(f'Impossible to unzip {zip_path} to {dst}: {e}')
            return False

    def get_zip_members(self, zip_path: str) -> List[str]:
        """Restituisce i nomi dei file contenuti in un file zip.
        Se ci sono errori, ritorna una lista vuota"""
        try:
            with ZipFile(zip_path) as zf:
                return zf.namelist()
        except Exception as e:
            self.m_logger.error(f'Error getting members of zip file {zip_path} ({type(e)}): {e}')
            return []

    def make_file_executable(self, file_path: str) -> bool:
        """Esegue chmod +x su un file"""
        try:
            command= f'sudo chmod +x {file_path}'
            self.m_logger.info(f'Executing: {command}')
            res= os.system(command)
            return res == 0
        except Exception as e:
            self.m_logger.error(f'Cannot make file {file_path} executable ({type(e)}): {e}')
            return False

    def give_file_max_permissions(self, file_path: str) -> bool:
        """Esegue chmod 777 su un file"""
        try:
            command= f'sudo chmod 777 {file_path}'
            self.m_logger.info(f'Executing: {command}')
            res= os.system(command)
            return res == 0
        except Exception as e:
            self.m_logger.error(f'Cannot give {file_path} max permissions ({type(e)}): {e}')
            return False

    def get_file_size(self, file_path: str) -> Optional[int]:
        """ Ritorna la dimensione in byte di un file. 
        Ritorna None is caso di fallimento. """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            self.m_logger.error(f'Cannot get size of file {file_path} ({type(e)}): {e}')
            return None

    def get_tmp_folder(self) -> Optional[str]:
        if platform.system() == 'Linux':
            return '/tmp'
        else:
            self.m_logger.error('Tmp folder available only in Linux')
            return None

    ############################################################################
    #
    #   NETWORK
    #
    ############################################################################

    def ping(self, ip_addr: str) -> bool:
        try:
            res= os.system(f'ping -c 1 {ip_addr} 2>&1 >/dev/null')
            return res == 0
        except Exception as e:
            self.m_logger.error(f'Error pinging {ip_addr} ({type(e)}): {e}')
            return False

    def check_kafka_broker(self, broker: str) -> bool:
        try:
            admin_client= AdminClient({
                'bootstrap.servers': broker
            })
            topics= admin_client.list_topics(timeout=2).topics
            return bool(topics)
        except:
            return False
    
    def ip_int_to_str(self, ip_int: int, vimba_std=False) -> str:
        """Converts an integer into a readable string representing an IP adress.
        
        Arguments
        ---------
        vimba_std: use Vimba API standard, which puts the numbers in reverse order."""
        try:
            ip1= ip_int // 16777216
            ip2= (ip_int - ip1 * 16777216) // 65536
            ip3= (ip_int - ip1 * 16777216 - ip2 * 65536) // 256
            ip4= ip_int - ip1 * 16777216 - ip2 * 65536 - ip3 * 256
            if vimba_std:
                ip_str= f'{ip4}.{ip3}.{ip2}.{ip1}'
            else:
                ip_str= f'{ip1}.{ip2}.{ip3}.{ip4}'
            return ip_str
        except Exception as e:
            self.m_logger.error(f'Cannot convert IP address to string ({type(e)}): {e}')
            return ''

    def mount_sshfs_folder(self, ip, user, ssh_key, their_folder, my_folder) -> bool:
        """Unmounts the local path, then mounts the remote folder to the local path via sshfs.
        
        Arguments
        ---------
        ip: the sshfs server address
        user: the username authenticated by the sshfs server
        ssh_key: the absolute path to the used ssh key file
        their_folder: the folder path on the sshfs server
        my_folder: the folder path on this machine
        """
        try:
            clean_command= f'sudo umount {my_folder}'
            self.m_logger.info(f'Executing: {clean_command}')
            res= os.system(clean_command)
            # mount_command= f'sudo sshfs -o allow_other,default_permissions,nonempty,IdentityFile={ssh_key}  {user}@{ip}:{their_folder} {my_folder}'
            mount_command= f'sudo sshfs -o allow_other,nonempty,IdentityFile={ssh_key}  {user}@{ip}:{their_folder} {my_folder}'

            self.m_logger.info(f'Executing: {mount_command}')
            res= os.system(mount_command)
            return res == 0
        except Exception as e:
            self.m_logger.error(f'Error trying to mount sshfs folder ({type(e)}): {e}')
            return False

    ############################################################################
    #
    #   NTP
    #
    ############################################################################

    def set_timezone(self, timezone: str) -> bool:
        try:
            self.m_logger.info(f'Setting timezone to {timezone}...')
            change_ntp_proc = subprocess.run(
                ['sudo', 'timedatectl', 'set-timezone', timezone]
            )
            return change_ntp_proc.returncode == 0
        except Exception as e:
            self.m_logger.error(
                f'Error setting timezone ({type(e)}): {e}'
            )
            return False

    def chrony_one_shot(self, ntp_addr=None) -> bool:
        try:
            self.m_logger.info('Syncing NTP with chrony...')
            retcode = os.system(f"sudo chronyd -q 'server {ntp_addr} iburst'")
            return retcode == 0
        except Exception as e:
            self.m_logger.error(f'Error syncing NTP with chrony ({type(e)}): {e}')
            return False

    ############################################################################
    #
    #   JSON
    #
    ############################################################################

    def _removeNotJasonable(self, p_dict):
        """ 
        Ritorna una copia del dizionario in ingresso ma senza le keyword non json compatibili
        """

        def _isJsonable(p_value):
            try:
                json.dumps(p_value)
                return True
            except:
                return False
        
        p_dict_copy= p_dict.copy()
        for key,value in p_dict.items():
            if not _isJsonable(value):
                if type(value) is bytearray:
                    p_dict_copy[key]= list(value)
                else:
                    p_dict_copy.pop(key, None)
        return p_dict_copy

    def check_dict_keys(self, p_dict1: dict, p_dict2: dict) -> bool:
        """ controlla che tutte le chiavi in dict2 siano anche in dict1 """
        try:
            for l_key, l_val in p_dict2.items():
                if l_key not in p_dict1.keys():
                    logging.error(f'"{l_key}" non è tra le chiavi di {p_dict1}')
                    return False
                if isinstance(l_val, dict):
                    if not isinstance(p_dict1[l_key], dict):
                        logging.error(f'{l_val} è un dict mentre {p_dict1[l_key]} non lo è')
                        return False
                    else:
                        l_res= self.check_dict_keys(p_dict1[l_key], l_val)
                        if not l_res:
                            logging.error('il check annidato è fallito')
                            return False
        except Exception as e:
            self.m_logger.error(f'Cannot compare two dicts ({type(e)}): {e}')
            return False
        return True

    ############################################################################
    #
    #   LOGGING
    #
    ############################################################################

    def prettify(self, obj, ind=1, pre=None) -> str:
        """
        Formatta un oggetto per mostrarlo chiaramente nel log
        """
        try:
            def decorate(obj) -> str:
                res= ''
                if isinstance(obj, str):
                    res += f'"{obj}"'
                else:
                    res += str(obj)
                return res
            TAB= '    '

            # Init return value
            res= ''
            
            # Prefix
            if pre is None:
                prefix= ''
                suffix= ''
            else:
                prefix= self.prettify(pre, ind) + ': '
                suffix= ''
                
            # Check if json, load if necessary
            if isinstance(obj, str):
                try:
                    loaded_obj= json.loads(obj)
                    if isinstance(loaded_obj, list) or isinstance(loaded_obj, dict):
                        obj= loaded_obj
                        prefix= 'JSON<' + prefix
                        suffix += '>'
                except:
                    pass
            
            # Prettify
            if len(str(obj)) <= 100:
                res += decorate(obj)
            elif isinstance(obj, list):
                oneline= len(obj) > 30
                if oneline:
                    res += str(obj)
                else:
                    res += '[\n'
                    for el in obj:
                        res += TAB * (ind + 1) + self.prettify(el, ind+1) + ',\n'
                    res += TAB * ind + ']'
            elif isinstance(obj, dict):
                oneline= len(obj.keys()) > 30
                if oneline:
                    res += str(obj)
                else:
                    res += '{\n'
                    for key, val in obj.items():
                        res += TAB * (ind + 1) + self.prettify(val, ind+1, key) + ',\n'
                    res += TAB * ind + '}'
            else:
                res += decorate(obj)

            return prefix + res + suffix
        except Exception as e:
            self.m_logger.error(f'Error prettifying {obj} ({type(e)}): {e}')
            return ''

    def format_bytearray(self, ba: Union[bytearray, List[int]]) -> str:
        try:
            return ' '.join(['0x{:02x}'.format(b) for b in ba])
        except Exception as e:
            self.m_logger.error(f'Error formatting bytearray {ba} ({type(e)}): {e}')
            try:
                return str(ba)
            except Exception as e2:
                self.m_logger.error(
                    f'Error converting bytearray to string while managing formatting error ({type(e)}): {e}'
                )
                return general.dato_errato

    ############################################################################
    #
    #   TIMESTAMP
    #
    ############################################################################

    TIME_FORMAT= '%H:%M:%S'
    DATE_FORMAT= '%d-%m-%Y'

    def timeNowObj(self) -> datetime:
        """Ritorna un oggetto datetime che rappresenta l'istante corrente"""
        return datetime.now()

    def timestampNowFloat(self) -> int:
        """Ritorna un timestamp intero nell'ordine dei centesimi di secondo"""
        return int(time.time() * 100)
        
    def timestampNow(self) -> str:
        """Ritorna la stringa del timestamp intero attuale nell'ordine dei centesimi di secondo"""
        l_now= int(time.time() * 100)
        s= str(l_now)
        return s

    def timestampNowFormatted(self) -> str:
        """Ritorna il timestamp attuale formattato per essere leggibile"""
        return str(datetime.fromtimestamp(time.time())) 

    def timeNow(self) -> str:
        """Ritorna la stringa dell'orario attuale"""
        l_now= datetime.now()
        s= l_now.strftime(self.TIME_FORMAT)
        return s

    def dateNow(self) -> str:
        """Ritorna la stringa della data di oggi"""
        l_now= datetime.now()
        s= l_now.strftime(self.DATE_FORMAT)
        return s

    def onlyTimeNowObj(self) -> datetime:
        """Ritorna un oggetto datetime contenente solo l'orario attuale (utile per confronti)"""
        time_now_str= self.timeNow()
        return self.str_to_time(time_now_str, time_format=self.TIME_FORMAT)

    def timestamp_to_formatted(self, timestamp: str) -> str:
        """Converte un timestamp in forma di stringa nell'ordine dei centesimi di secondo 
        in un timestamp formattato e leggibile"""
        try:
            return str(datetime.fromtimestamp(int(timestamp)/100))
        except Exception as e:
            self.m_logger.error(f'Cannot convert {timestamp} to formatted timestamp ({type(e)}): {e}')
            return general.dato_non_disp

    def timestamp_to_date(self, timestamp: str) -> str:
        """Ricava da un timestamp in forma di stringa nell'ordine dei centesimi di secondo 
        la data di oggi"""
        try:
            return datetime.fromtimestamp(int(timestamp)/100).strftime(self.DATE_FORMAT)
        except Exception as e:
            self.m_logger.error(f'Cannot convert {timestamp} to date ({type(e)}): {e}')
            return general.dato_non_disp

    def timestamp_to_time(self, timestamp: str) -> str:
        """Ricava da un timestamp in forma di stringa nell'ordine dei centesimi di secondo 
        l'orario attuale"""
        try:
            return datetime.fromtimestamp(int(timestamp)/100).strftime(self.TIME_FORMAT)
        except Exception as e:
            self.m_logger.error(f'Cannot convert {timestamp} to time ({type(e)}): {e}')
            return general.dato_non_disp

    def str_to_time(self, time_str: str, time_format=None) -> Optional[datetime]:
        """Converte un orario formattato (es: "20:30:00") in un oggetto datetime.
        Si può indicare la formattazione tramite time_format"""
        if time_format is None:
            time_format= self.TIME_FORMAT
        try:
            return datetime.strptime(time_str, time_format)
        except Exception as e:
            self.m_logger.error(f'Cannot convert {time_str} to datetime object using format {time_format}')
            return None

    def str_to_datetime(self, ts_str: str) -> Optional[datetime]:
        """ 
        Converte una data completa formattata in un oggetto datetime.
        
        La stringa deve essere nel formato che si ottiene in uno dei seguenti modi:
            - str(dt_obj)
            - dt_obj.isoformat()
        """

        try:
            return datetime.fromisoformat(ts_str)
        except:
            self.m_logger.error(f'Cannot convert to datetime object: {ts_str}')
            return None

    def int_date_to_str(self, p_year: int, p_month: int, p_day: int, p_format: str=None) -> Optional[str]:
        """
        Converte anno, giorno, mese in una stringa formattata
        """
        if p_format is None:
            p_format = self.DATE_FORMAT
        try:
            l_dt = datetime(year=p_year, month=p_month, day=p_day)
        except Exception as e:
            self.m_logger.error(f'Error creating datetime from year, month, day ({type(e)}): {e}')
            return None
        try:
            return l_dt.strftime(p_format)
        except Exception as e:
            self.m_logger.error(f'Error formatting datetime ({type(e)}): {e}')
            return None

    def seconds_to_formatted(self, secs: int) -> Optional[str]:
        try:
            l_days = secs // (60 * 60 * 24)
            l_mod = secs % (60 * 60 * 24)
            l_hours = l_mod // (60 * 60)
            l_mod = l_mod % (60 * 60)
            l_mins = l_mod // 60
            l_mod = l_mod % 60
            l_secs = l_mod
            l_out = ''
            if l_days > 0:
                l_out += f'{l_days} day'
                if l_days > 1:
                    l_out += 's'
                l_out += ', '
            l_out += f'{l_hours:02d}:{l_mins:02d}:{l_secs:02d}'
            return l_out
        except Exception as e:
            self.m_logger.error(
                f'Error converting seconds - {secs} - to formatted ({type(e)}): {e} '
            )
            return None

    ############################################################################
    #
    #   CAMERA/KAFKA
    #
    ############################################################################

    def new_trans_id(self) -> str:
        """Ritorna un nuovo ID univoco"""
        return str(uuid.uuid4())

    ############################################################################
    #
    #   ASYNCIO
    #
    ############################################################################

    async def wait_first(self, aws: List[asyncio.Task], timeout=None) -> Tuple[List[asyncio.Task], List[asyncio.Task]]:
        """Attende la terminazione del primo oggetto awaitable in aws,
        poi restituisce subito la lista dei task terminati e quella dei task in corso.
        Se indicato, ritorna subito le due liste allo scadere di un timeout."""
        try:
            return await asyncio.wait(
                [asyncio.create_task(aw) if asyncio.iscoroutine(aw) else aw for aw in aws],
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED
            )
        except Exception as e:
            self.m_logger.error(f'Error waiting for {aws} ({type(e)}): {e} ')
            return [], []



" ISTANZE "

helper= Helper()
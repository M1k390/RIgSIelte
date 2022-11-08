#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main central workflow
I moduli sono autonomi nella gestione degli errori gravi, escono dal programma
"""


import threading
import time
import sys
import os
import logging
import queue
import datetime
import traceback
import gc
from typing import Dict, Optional

from rigproc import __version__ as version
from rigproc.commons.utils import ExecutionDelayer
from rigproc.flow.flow_renew_logs import FlowRenewLogs

from rigproc.io import iocomm
from rigproc.console import server

from rigproc.flow import eventtrigflow
from rigproc.flow.flow_recovery import FlowRecovery
from rigproc.flow.flow_camera_event import FlowCameraEvent
from rigproc.flow import eventtrigflow_buildcmd as buildcmd

from rigproc.central.kafka_broker import BrokerInterface, FakeBroker, KafkaBroker
from rigproc.central.anomaly_detector import AnomalyDetector
from rigproc.central.recovery_manager import RecoveryManager
from rigproc.central.routines_manager import RoutinesManager

from rigproc.commons.interpreter import interpreter, CameraEvent, CameraError
from rigproc.commons import keywords, config, redisi, scheduler
from rigproc.commons.logger import logging_manager
from rigproc.commons.wrappers import wrapkeys
from rigproc.commons.helper import helper

from rigproc.params import internal, bus, anomalies, conf_values, redis_keys, general

from rigproc.fake_modules.fakecamera import _procFakeCamera
from rigproc.fake_modules.fakebus import initFakeSerialBus, closeFakeSerialBus


class MainProcess():
    """
    Interfaccia di avvio e gestione componenti di lavoro
    """
    
    def __init__(self, p_config):
        self.m_conf_dict= p_config
        self.m_config= None
        self.m_conf_integrity= False
        self.m_logger= logging.getLogger('root')
        self.m_logger.info("processing")      
        # thread di lavoro
        self.m_procCamera= None
        self.m_procThreds: Dict[str, threading.Thread] = {
            'subscriber':       '',
            'central':          '',
            'rigcam':           '',
            'rigcam_manager':   '',
            'io':               '',
            'broker':           '',
            'periodic_check':   ''
        }
        self.m_queue= queue.Queue() # coda principale scambio comandi
        self.m_topicQ= queue.Queue()
        self.m_ioQ= queue.Queue()
        self.m_trigs: list[eventtrigflow.EventTrigFlow]= [] # flows eventi passaggio treno (con time stamp per annullamento a tempo)
        self.m_otherFlows: list[eventtrigflow.EventTrigFlow]= [] # flows di altro tipo
        self.m_trig_timeout= 90 #timeout default attesa completamento trigger evt flows
        self.m_periodic_check_period= 20
        self.m_periodic_paused= False
        self.m_barrier= threading.Barrier(10) # Barrier users:
            #  1. spawn_processes
            #  2. redis_subscriber_rigcam
            #  3. proc_anomaly_check
            #  4. proc_heartbeat
            #  5. proc_central
            #  6. proc_periodic_check
            #  7. proc_rigcam
            #  8. proc_rigcam_manager
            #  9. proc_io
            # 10. proc_broker
        self.m_barrier_counter = 0
        self.m_barrier_counter_lock = threading.Lock()
        self.m_startup_done= threading.Event()
        self.m_procFakeCamera= None

        self.m_kafkaBroker: Optional[BrokerInterface] = None

        # rigcam status
        self.m_rigcam_exec_path: Optional[str] = None # Percorso dell'eseguibile di rigcam
        self.m_start_rigcam = threading.Event() # Evento per regolare l'avvio di rigcam attraverso rigcam_manager
        self.m_rigcam_ready = False             # Flag per determinare se rigcam sia pronto
        self.m_rigcam_late = False              # Flag che indica che rigcam non è pronto ed è scattato il timeout
        self.m_rigcam_running = False           # Flag per determinare se rigcam è stato avviato e non è terminato
        self.m_rigcam_crash = False             # Flag: rigcam crash (in genere si interrompe anche l'esecuzione)
        self.m_rigcam_error = False             # Flag: errore senza interruzione dell'esecuzione
        self.m_restart_rigcam = False           # Flag per scatenare il riavvio di rigcam
        self.m_rigcam_closing = False           # Flag per determinare se rigcam si stia chiudendo
        self.m_rigcam_last_start = helper.timeNowObj() # Timestamp dell'ultimo avvio di rigcam
        self.m_rigcam_last_term = helper.timeNowObj() # Timestamp dell'ultima terminazione di rigcam

        self.m_block_new_flows= False
        self.m_critical= False
        self.m_recovery_manager= None
        self.m_redisI= None
        self.m_stop_event= threading.Event()
        self.m_stop= False
        self.m_rebooting= False

    def configure(self):
        """
        Fasi di configurazione e lancio sub componenti
        """
        threading.current_thread().name= 'main'

        # Set configuration and Redis
        config.init_configuration(self.m_conf_dict)
        self.m_config= config.get_config()
        self.m_conf_integrity= self.m_config.check_configuration_integrity()
        self._connect_to_redis()
        self.m_config.sync_with_redis()

        # Set flow logger (root logger has already been set)
        logging_manager.generate_logger(
            logger_name='flow',
            format_code=self.m_config.logging.flow.format.get(),
            console_level=self.m_config.logging.flow.console_level.get(),
            file_level=self.m_config.logging.flow.file_level.get(),
            log_file_name=self.m_config.logging.flow.file_name.get(),
            log_file_dir=self.m_config.logging.flow.file_dir.get(),
            log_file_mode=self.m_config.logging.flow.file_mode.get(),
            root_log_file_prefix=self.m_config.logging.root.file_name.get() \
                if self.m_config.logging.flow.log_to_root.get() else None,
            root_log_dir=self.m_config.logging.root.file_dir.get() \
                if self.m_config.logging.flow.log_to_root.get() else None,
            formatter_setting=self.m_config.logging.flow.formatter.get()
        )
            
        # Init scheduler
        scheduler.init_scheduler(self.m_queue)

        # Fake camera è sempre attivo NON è un thread, al limite non viene usato, ha le sue conf interne!!
        self.m_procFakeCamera= _procFakeCamera()
        #
        self.m_core= {# utilizzato per passare le vie di comunicazione
                      # ai component del main proc
                    'cmd_q': self.m_queue,
                    'topic_q': self.m_topicQ,
                    'io_q': self.m_ioQ,
                    'stop': self.m_stop,
                    'trigs': self.m_trigs,
                    'fake_camera': self.m_procFakeCamera,
                    'block_new_flows': self.m_block_new_flows
                    }

        # Recovery manager e Routines manager hanno i loro thread interni
        self.m_recovery_manager= RecoveryManager(self.m_core)
        self.m_routines_manager= RoutinesManager(self.m_core)

        self.m_consoleServer= server.ConsoleServer()
        # Config extras
        l_conf_sw_upd= self.m_config.main.sw_update
        if l_conf_sw_upd.update_date_format.integrity() and l_conf_sw_upd.update_time_format.integrity():
            self.m_update_date_format= self.m_config.main.sw_update.update_date_format.get()
            self.m_update_time_format= self.m_config.main.sw_update.update_time_format.get()
        else:
            self.m_update_date_format= '%Y_%m_%d'
            self.m_update_time_format= '%H_%M_%S'
            self.m_logger.error("Loading default sw update date/time format")
        # Reset msg_sorted
        self.m_redisI.cache.delete(keywords.key_redis_msg_sorted_set)
        # blocking call
        self._spawn_processes()

    def close(self, term_msg=None):
        # Flag di stop
        self.m_stop= True
        # Evento di stop
        self.m_stop_event.set()
        # Sblocco eventuali operazioni in attesa
        self.m_startup_done.set()
        self.m_start_rigcam.set()
        # Informo il processo di gestione delle cam che deve uscire
        if self.m_rigcam_running:
            self.m_redisI.send_exit_rigcam()
        # Eliminazione oggetti pendenti
        for el in self.m_trigs:
            self._deleteFlow(el)
        for el in self.m_otherFlows:
            self._deleteFlow(el)
        # Richiesta chisura threads
        self.m_consoleServer.close()
        if self.m_kafkaBroker is not None:
            self.m_kafkaBroker.close()
        self.m_routines_manager.close()
        self.m_recovery_manager.close()
        # Eventuale chiusura oggetti simulati
        if self.m_config.main.modules_enabled.bus485.get() == conf_values.module.fake:
            closeFakeSerialBus()
        # Metto il log di terminazione in Redis
        if term_msg is not None:
            try:
                self.m_redisI.cache.set(self.m_config.boot.rig_termination_key.get(), term_msg)
            except:
                self.m_logger.error('Impossible to log program termination')

    def _wait_for_barrier(self, who: str):
        self.m_barrier_counter_lock.acquire()
        self.m_barrier_counter += 1
        l_id = self.m_barrier_counter
        self.m_barrier_counter_lock.release()
        try:
            self.m_logger.info(f'{who} (#{l_id}) is waiting for barrier')
            self.m_barrier.wait()
        except Exception as e:
            self.m_logger.error(
                f'Error waiting for barrier by {who} (#{l_id}) ({type(e)}): {e}. ' +\
                'Continuing execution...'
            )

    " --------- Private --------  "

    def _connect_to_redis(self):
        """
        Attivazione connessione al redis
        """
        redisi.initialize_redis(
            self.m_config.main.redis.cache.host.get(),
            self.m_config.main.redis.cache.port.get(),
            self.m_config.main.redis.pers.host.get(),
            self.m_config.main.redis.pers.port.get()
        )
        self.m_redisI= redisi.get_redisI()
        if not self.m_redisI.m_initialized:
            self.m_logger.critical('Error initializing Redis: exit...')
            sys.exit(-1)

        # Reset Redis cache
        self.m_redisI.clear_rigproc_pid()
        self.m_redisI.clear_rigcam_pid()
        rigproc_pid = helper.get_my_pid()
        if rigproc_pid is not None:
            self.m_redisI.set_rigproc_pid(rigproc_pid)
        else:
            self.m_logger.error('Cannot get rigproc pid')
        self.m_redisI.clear_rigproc_uptime()
        self.m_redisI.clear_shoot_counter()

    def _spawn_processes(self):
        """
        Lancia i processi collaterali al main process:
            - subscriber, eventi via redis, trig camere ( python thread )
            - central, coda comandi condivida tra i proc (python thread)
            - camera (external program)
            - io com (spython module)
            - broker, kafka interface (python module)
        Archiettura:
            Spawn di un thread per ogni processo in modo da controllare
            separatamente il processo stesso
        """
        
        # Server external command console
        self.m_consoleServer.start(self.m_core)

        # Internal threads
        self.m_procThreds['subscriber']= threading.Thread(
                        target= self._redis_subscriber_rigcam,
                        name= 'subscriber',
                        daemon= True
                        )
        self.m_procThreds['central']= threading.Thread(
                        target= self._proc_central,
                        name= 'central',
                        daemon= True
                        )

        self.m_procThreds['rigcam']= threading.Thread(
                        target= self._proc_rigcam,
                        name= 'camera',
                        daemon= True
                        )

        self.m_procThreds['rigcam_manager']= threading.Thread(
                        target= self._proc_rigcam_manager,
                        name= 'rigcam_manager',
                        daemon= True
                        )

        self.m_procThreds['io']= threading.Thread(
                        target= self._proc_io,
                        name= 'io',
                        daemon= True
                        )
        self.m_procThreds['broker']= threading.Thread(
                        target= self._proc_broker,
                        name= 'broker',
                        daemon= True
                        )
        self.m_procThreds['periodic_check']= threading.Thread(
                        target= self._proc_periodic_check,
                        name= 'periodic_check',
                        daemon= True
                        )
        self.m_procThreds['anomaly_check']= threading.Thread(
                        target= self._proc_anomaly_check,
                        name= 'anomaly_check',
                        daemon= True
                        )
        self.m_procThreds['heartbeat']= threading.Thread(
                        target= self._proc_heartbeat,
                        name= 'heartbeat',
                        daemon= True
                        )
        
        # Join threads
        [p.start() for p in self.m_procThreds.values()]

        # Task iniziale
        self._wait_for_barrier('spawn_processes')
        # TODO check

        # Inserisco il timestamp di avvio in Redis ed elimino il vecchio messaggio di terminazione
        l_start_timestamp_key= self.m_config.boot.rig_start_timestamp_key
        if l_start_timestamp_key.integrity():
            self.m_redisI.cache.set(l_start_timestamp_key.get(), helper.timestampNowFormatted())
        else:
            self.m_logger.error('Cannot write start timestamp because the Redis because I do not know the key')

        # Invio anomalia se ci sono errori nella configurazione
        if not self.m_conf_integrity:
            l_config_anomaly= anomalies.definition.rip_config
            scheduler.get_scheduler().request_topic_anomaly(
                faulty_device=  l_config_anomaly.device, 
                alarm_id=       l_config_anomaly.id, 
                alarm_descr=    l_config_anomaly.descr, 
                alarm_status=   l_config_anomaly.status
            )

        # Reset barrier
        self.m_barrier.reset()
        self.m_barrier.abort()

        # Startup
        l_startup = eventtrigflow.EventTrigFlow(
                self.m_core, 
                'startup', 
                keywords.flow_type_startup
            )
        self.m_otherFlows.append(l_startup)

        # Start extra threads after startup is done
        self.m_startup_launcher= ExecutionDelayer(
            delayer= self.m_startup_done,
            functions=[
                self.m_routines_manager.start,
                self.m_recovery_manager.start
            ],
            name='startup_launcher',
            abort=self.m_stop_event
        )
        self.m_startup_launcher.start()

        # Test reboot
        #self.m_logger.warning('Test rebooting!')
        #self.close('reboot')
        #self.m_ioQ.put(buildcmd._buildIoCmdRestart(None))

        try:
            [p.join() for p in self.m_procThreds.values() ]
        except KeyboardInterrupt:
            # TODO il crtl c va gestito a parte non così!
            self.m_stop= True
            [p.join() for p in self.m_procThreds.values() ]
            self.m_recovery_manager.wait()
            self.m_consoleServer.wait()
            self.m_routines_manager.wait()
            self.m_logger.info("Exiting main processing, rig terminating")
            return

        self.m_logger.info("Internal threas joined")
        self.m_recovery_manager.wait()
        self.m_consoleServer.wait()
        self.m_routines_manager.wait()
        self.m_logger.info("Exiting main processing, rig terminating")

    " --------- Process controls ---------- "

    def _redis_subscriber_rigcam(self):
        """
        Subscriber Redis per la ricezione di messaggi da rigcam
        Messaggi riconosciuti:
            -   Startup report
            -   Crash report
            -   Camera error report
            -   Event data
        """

        self.m_logger.info('Starting Redis subscriber for rigcam...')

        # Subscribe
        l_sub= self.m_redisI.subscribe_to_rigcam_messages()
        if l_sub is None:
            self.m_logger.critical('Cannot subscribe to rigcam messages on Redis')
            self.m_critical= True
            self._wait_for_barrier('redis_subscriber_rigcam')
            return

        l_camera_ids= [
            self.m_config.camera.ids.prrA.id_1.get(),
            self.m_config.camera.ids.prrA.id_2.get(),
            self.m_config.camera.ids.prrA.id_3.get(),
            self.m_config.camera.ids.prrA.id_4.get(),
            self.m_config.camera.ids.prrA.id_5.get(),
            self.m_config.camera.ids.prrA.id_6.get(),
            self.m_config.camera.ids.prrB.id_1.get(),
            self.m_config.camera.ids.prrB.id_2.get(),
            self.m_config.camera.ids.prrB.id_3.get(),
            self.m_config.camera.ids.prrB.id_4.get(),
            self.m_config.camera.ids.prrB.id_5.get(),
            self.m_config.camera.ids.prrB.id_6.get(),
        ]
        l_camera_modules= [
            bus.module.cam1_a,
            bus.module.cam2_a,
            bus.module.cam3_a,
            bus.module.cam4_a,
            bus.module.cam5_a,
            bus.module.cam6_a,
            bus.module.cam1_b,
            bus.module.cam2_b,
            bus.module.cam3_b,
            bus.module.cam4_b,
            bus.module.cam5_b,
            bus.module.cam6_b,
        ]
        l_cameras_scheme= {
            l_camera_id: l_camera_module
            for l_camera_id, l_camera_module
            in zip(l_camera_ids, l_camera_modules)
        }
        
        #
        self._wait_for_barrier('redis_subscriber_rigcam')

        # Listen
        while not self.m_stop:
            try:
                l_msg= l_sub.get_message(p_timeout= 1.0)                    
                if not l_msg:                
                    continue
                
                if l_msg['data'] == 'set' :
                    self.m_logger.info(f'New message from rigcam detected')
                    l_key= str(l_msg['channel']).replace('__keyspace@0__:', '')

                    if l_key == redis_keys.cam_startup.key:
                        self.m_logger.info('Startup detected')
                        startup_msg= self.m_redisI.cache.get(l_key)
                        camera_process_running= interpreter.decode_running_state(startup_msg)
                        opened_cameras = interpreter.decode_opened_cameras(startup_msg)
                        startup_errors = interpreter.decode_startup_errors(startup_msg)
                        rigcam_pid = interpreter.decode_startup_pid(startup_msg)
                        self.m_logger.info(
                            'CAMERA PROCESS STARTUP\n' +\
                            f'Running:        {camera_process_running}\n' +\
                            f'Opened cameras: {opened_cameras}\n' +\
                            f'Errors:         {startup_errors}\n' +\
                            f'PID:            {rigcam_pid}\n'
                        )
                        if camera_process_running:
                            self.m_rigcam_ready= True
                        else:
                            self.m_logger.critical('Negative startup report received: Rigcam is not running')
                            self.m_rigcam_crash = True

                        # Salva PID rigcam in Redis
                        if rigcam_pid is not None:
                            self.m_redisI.set_rigcam_pid(rigcam_pid)

                    elif l_key == redis_keys.cam_crash.key:
                        self.m_logger.critical('Rigcam crashed')
                        self.m_rigcam_crash = True

                    elif l_key.startswith(redis_keys.cam_error.key_prefix):
                        self.m_logger.warning('Camera error detected')
                        error_msg= self.m_redisI.cache.get(l_key)
                        cam_error= interpreter.decode_camera_error(error_msg)
                        if isinstance(cam_error, CameraError):
                            self.m_logger.info(repr(cam_error))
                            if cam_error.cam_id in l_cameras_scheme.keys():
                                l_module= l_cameras_scheme[cam_error.cam_id]
                                if cam_error.error_msg == internal.cam_error.cam_lost:
                                    self.m_redisI.updateStatusInfo(l_module, l_module, general.status_ko)
                                    self.m_redisI.updateStatusInfo(
                                        l_module, 
                                        redis_keys.cam_status_field.status, 
                                        redis_keys.cam_status_field.disconnected
                                    )
                                if cam_error.error_msg == internal.cam_error.unexpected_data:
                                    self.m_redisI.updateStatusInfo(
                                        l_module, 
                                        redis_keys.cam_status_field.status, 
                                        redis_keys.cam_status_field.error
                                    )
                                if cam_error.error_msg == internal.cam_error.exec_error:
                                    self.m_redisI.updateStatusInfo(
                                        l_module, 
                                        redis_keys.cam_status_field.status, 
                                        redis_keys.cam_status_field.error
                                    )
                                if cam_error.error_msg == internal.cam_error.less_triggers:
                                    self.m_redisI.updateStatusInfo(
                                        l_module, 
                                        redis_keys.cam_status_field.status, 
                                        redis_keys.cam_status_field.missing_trigger
                                    )
                                if cam_error.error_msg == internal.cam_error.missed_trigger:
                                    self.m_redisI.updateStatusInfo(
                                        l_module, 
                                        redis_keys.cam_status_field.status, 
                                        redis_keys.cam_status_field.missing_trigger
                                    )
                                if cam_error.error_msg == internal.cam_error.missed_frame:
                                    self.m_redisI.updateStatusInfo(
                                        l_module, 
                                        redis_keys.cam_status_field.status, 
                                        redis_keys.cam_status_field.missing_frame
                                    )
                                
                                self.m_rigcam_error = True
                            else:
                                self.m_logger.critical('Unexpected camera ID!')

                        else:
                            self.m_logger.error('Cannot read camera error')

                    elif l_key.startswith(redis_keys.cam_event.key_prefix):
                        self.m_logger.info('New camera event detected')
                        event_msg= self.m_redisI.cache.get(l_key, p_default=None)
                        if event_msg is not None:
                            event_data= interpreter.decode_event(event_msg)
                            if isinstance(event_data, CameraEvent):
                                self.m_logger.info(f'Event received:\n{repr(event_data)}')

                                # Update camera status (ok if frame is present)
                                for shoot_array in event_data.shoot_arrays:
                                    for shoot in shoot_array.shoots:
                                        if shoot.cam_id in l_cameras_scheme.keys():
                                            l_module= l_cameras_scheme[shoot.cam_id]
                                            self.m_redisI.updateStatusInfo(l_module, l_module, general.status_ok)
                                            self.m_redisI.updateStatusInfo(
                                                l_module, 
                                                redis_keys.cam_status_field.status, 
                                                general.status_ok
                                            )
                                        else:
                                            self.m_logger.critical('Unexpected camera ID!')

                                evt_cmd= {
                                    internal.cmd_key.cmd_type: internal.cmd_type.camera_evt,
                                    internal.cmd_key.evt_data: event_data
                                }
                                self.m_queue.put(evt_cmd)
                            else:
                                self.m_logger.error('Error decoding camera event: event lost!')
                        else:
                            self.m_logger.error('Error reading camera event from Redis: event lost!')
                    self.m_redisI.cache.delete(l_key)
            except Exception as e:
                self.m_logger.error(f'Error handling camera process message ({type(e)}): {e}. Message lost!')

    
    def _proc_anomaly_check(self, p_config=None):
        """ Thread per il rilevamento delle anomalie e l'invio di Topic a STG """
        try:
            l_sub= self.m_redisI.pers.pubsub()
            l_sub.psubscribe('__keyspace@0__:status_*')     
            self.m_logger.info("Registering to set__keyspace@0__:status_*")
        except Exception as e:
            self.m_logger.critical("Exception subscribing redis event, prepare to exit process {}".format(e))
            self.m_critical= True
            self._wait_for_barrier('proc_anomaly_check')
            return

        l_detector= AnomalyDetector()

        self._wait_for_barrier('proc_anomaly_check')

        while not self.m_stop:
            try:
                l_msg= l_sub.get_message(p_timeout= 1.0)                    
                if not l_msg:                
                    continue            
            except Exception as e:
                self.m_logger.error("Exception handling redis event, skipping.. {}".format(e))
            if wrapkeys.getValue(l_msg, 'data') == 'set':
                self.m_logger.info(f'Set Redis status operation detected by the subscriber: {l_msg}')
                l_modified_param= l_msg['channel'].replace('__keyspace@0__:','')
                l_detector.detect_anomaly(l_modified_param)


    def _proc_heartbeat(self, p_config=None):
        """ Thread per l'invio periodico di un heartbeat 
        L'invio consiste nell'aggiornamento di un parametro in Redis con un timestamp aggiornato """
        l_alive_key= self.m_config.boot.alive_key
        if not l_alive_key.integrity():
            self.m_logger.error('I do not know the Redis key for heartbeat')
        l_alive_interval= self.m_config.boot.exec_watch_interval
        if not l_alive_interval.integrity():
            self.m_logger.error('Cannot read heartbeat interval')

        self._wait_for_barrier('proc_heartbeat')

        while not self.m_stop:
            if all([l_alive_key.integrity(), l_alive_interval.integrity()]) and l_alive_key.get() != '':
                self.m_redisI.cache.set(l_alive_key.get(), helper.timestampNowFormatted())
                time.sleep(l_alive_interval.get())
            elif l_alive_key.get() == '':
                time.sleep(10)
            else:
                self.m_logger.warning('Skipping heartbeat due to missing data')
                time.sleep(10)
            

    def _proc_central(self):
        """
        Accentratore comandi/eventi
        Processing comandi condivisi tra i proc 
        via queue

        """
        # Parametri di configurazione
        try:
            self.m_remoteDir = self.m_config.main.recovering.remote_folder.get()
        except KeyError as e:
            self.m_logger.critical("Mandatory keys missing from config: " + str(e))
            self.m_critical= True
        self._wait_for_barrier('proc_central')
        # Processing comandi
        self.m_logger.info("Central process started")
        while not self.m_stop:
            try:
                l_cmd= self.m_queue.get(block= True, timeout= 1.0)
            except queue.Empty:
                continue  
            # Processing queue internal cmd
            self._cmdProcessing(l_cmd)

    def _proc_periodic_check(self) :
        """ Thread periodico task continui del main proc """

        def _checkScheduledUpdate(p_date_format, p_time_format) -> None:
            """ Esegue un check dell'orario attuale e delle chiavi del redis 
            relative allo scheduling update sw"""
            l_sched_date= self.m_redisI.pers.hget(keywords.sw_update_hash_key, keywords.sw_update_date, p_default=None)
            l_sched_time= self.m_redisI.pers.hget(keywords.sw_update_hash_key, keywords.sw_update_time, p_default=None)
            # Controllo valori letti, se non ci sono update schedulati si passa oltre
            if l_sched_date and l_sched_time:
                self.m_logger.debug("Scheduled update for {} at {}".format(l_sched_date, l_sched_time))
                try:
                    l_str_date= l_sched_date + ' ' + l_sched_time
                    l_format= p_date_format + ' ' +p_time_format
                    l_obj_date= datetime.datetime.strptime(l_str_date, l_format)
                except:
                    self.m_logger.error("Bad time format for scheduled sw updated: {} - {} ".format(l_str_date, l_format))
                    return False
            else:
                # No key date, exit
                self.m_logger.debug('No scheduled update')
                return False
            # Se l'orario è sorpassato ( e le chiavi sono sulla cache richiedi il riavvio del process)
            if l_obj_date < datetime.datetime.now():
                self.m_logger.warning("Update time!")
                return True
            else:
                self.m_logger.debug("Update is scheduled but for another time")
            return False

        def _cleanOlderFlows() -> None:
            """ Pulizia memorai trigger e flows """
            # Revisione eventi trigger pendenti, elimino i flows se sono
            # più vecchi di evt_flows_timeout
            # Potrebbero essere incompleti o corrotti, in ogni caso se anche
            # fossero in essere sarebbero oltre il tempo ammesso per il processing dei dati
            now= helper.timeNowObj()
            for flow in self.m_trigs:
                l_flowTime= flow.getCreationTime()
                l_delta= now - l_flowTime
                if isinstance(l_delta, datetime.timedelta):
                    if l_delta.total_seconds() > self.m_trig_timeout:
                        self.m_logger.debug('A trig flow has exceded the timeout')
                        self._deleteFlow(flow)
                        continue
                else:
                    # Se non recupero la data..elimino subito, flow corrotto
                    self.m_logger.debug('A trig flow has no valid start timestamp')
                    self._deleteFlow(flow)
            for flow in self.m_otherFlows:
                l_flowTime= flow.getCreationTime()
                l_delta= now - l_flowTime
                if isinstance(l_delta, datetime.timedelta):
                    if l_delta.total_seconds() > self.m_trig_timeout:
                        self.m_logger.debug('A flow has exceded the timeout')
                        self._deleteFlow(flow)
                        continue
                else:
                    # Se non recupero la data..elimino subito, flow corrotto
                    self.m_logger.debug('A flow has no valid start timestamp')
                    self._deleteFlow(flow)


        self.m_logger.info("Proc periodic check started")
        self.m_periodic_paused= False
        self.m_trig_timeout=            self.m_config.main.periodic.evt_flows_timeout.get()
        self.m_proc_periodic_enabled=   self.m_config.main.periodic.enabled.get()
        try:
            self.m_periodic_check_period = \
                int(self.m_config.main.periodic.periodic_check_period.get())
        except:
            self.m_logger.error(
                'Cannot parse power check period from config: using default 60 seconds'
            )
            self.m_periodic_check_period = 60
        
        # Check status
        if self.m_proc_periodic_enabled:
            self.m_logger.info("Proc periodic is enabled")
        else:
            self.m_logger.info("Proc periodic is disabled")
        
        # Check tempo minimo
        if self.m_periodic_check_period < 5:
            self.m_periodic_check_period= 5
        self.m_logger.info("Flow evt timeout  {}".format(self.m_trig_timeout))
        self.m_logger.info("Power check period  {}".format(self.m_periodic_check_period))
        
        l_counter = 0

        #
        self._wait_for_barrier('proc_periodic_check')
        
        # Check task abilitato
        while not self.m_stop:
                
            if l_counter > self.m_periodic_check_period:
                l_counter = 0
            
            # ----------1 second tasks -----------
            # Check critical error
            if self.m_critical:
                if not self.m_rebooting:
                    self.m_rebooting= True
                    self.m_logger.critical("Critical error, prepare to exit process")
                    # Richiedo il riavvio del processo
                    l_restart_update= eventtrigflow.EventTrigFlow(
                        self.m_core, 
                        'restart',
                        keywords.flow_type_exit_update,
                        p_data={'restart_for_update': False}
                    )
                    self.m_otherFlows.append(l_restart_update)
            
            # ----------5 second tasks -----------
            if (l_counter % 5 == 0) and l_counter >= 5:
                _cleanOlderFlows()
            
            # ---- periodic period time tasks ----
            if l_counter == 0:
                # Mi accerto di non avere i task periodici in pausa (es shutdown procedure)
                if self.m_periodic_paused:
                    continue
                
                if self.m_startup_done.is_set():
                    # Check update scheduled
                    l_need_update = _checkScheduledUpdate(self.m_update_date_format, self.m_update_time_format)
                else:
                    l_need_update = False
                
                # Se non è programmato un'update...
                if not l_need_update:
                    # Eseguo i task periodici interni solo se sono abilitati
                    if self.m_proc_periodic_enabled:
                        # Diagnosi periodica destinazione principale power_check
                        l_cmd= {}
                        l_cmd[internal.cmd_key.cmd_type]= internal.cmd_type.action
                        l_cmd[internal.cmd_key.action_type]= keywords.action_periodic_flow
                        self.m_queue.put(l_cmd)
                else:
                    # Atrimenti richiedo il riavvio del processo
                    l_restart_update= eventtrigflow.EventTrigFlow(
                        self.m_core, 
                        'restart',
                        keywords.flow_type_exit_update,
                        p_data={
                            'restart_for_update': True,
                            keywords.flin_last_version_key: self.m_config.boot.last_version_key.get()
                        }
                    )
                    self.m_otherFlows.append(l_restart_update)

            l_counter += 1
            
            # Cycle common operation
            time.sleep(1)

        self.m_logger.info("Proc power check exiting")

    def _proc_rigcam(self):
        """
        Avvia rigcam e rimane in attesa durante l'esecuzione.    

        Invia la configurazione di rigcam attraverso Redis.
        Viene schedulato da proc_rigcam_manager.
        """
        self.m_logger.info("rigcam thread running")
        
        # Cameras conf
        l_processType= self.m_config.camera.process_type.get()
        l_exec_dir= self.m_config.boot.exec_dir.get()
        l_exec_dir= helper.universal_path(helper.abs_path(l_exec_dir))
        l_redis_host= self.m_config.main.redis.cache.host.get()
        l_redis_port= self.m_config.main.redis.cache.port.get()

        if not config.get_config().main.ping.enabled.get():
            for i in range(1, 7):
                self.m_redisI.cache.set(redis_keys.camera.prrA_status + str(i), general.status_ok)
                self.m_redisI.cache.set(redis_keys.camera.prrB_status + str(i), general.status_ok)

        self.m_start_rigcam.set() # Primo avvio

        #
        self._wait_for_barrier('proc_rigcam')
        
        while not self.m_stop:
            # Attendi il segnale di partenza
            self.m_start_rigcam.wait()
            self.m_start_rigcam.clear()

            # Interrompi il loop se bisogna uscire
            if self.m_stop:
                break

            # Resetta i flag
            self.m_rigcam_ready = False
            self.m_rigcam_late = False
            self.m_rigcam_error = False
            self.m_rigcam_crash = False
            self.m_restart_rigcam = False
            self.m_rigcam_closing = False

            if l_processType == 'subprocess':
                # Invia la configurazione attraverso Redis
                l_setup_message = interpreter.encode_setup_message()
                self.m_redisI.send_setup_rigcam(l_setup_message)

                # Determina il percorso dell'eseguibile
                self.m_rigcam_exec_path= helper.join_paths(l_exec_dir, f'rigcam_{version}')
                if not helper.file_exists(self.m_rigcam_exec_path):
                    l_default_exec = self.m_config.camera.default_path.get()
                    self.m_logger.error(f'Rigcam executable {self.m_rigcam_exec_path} does not exist: using default ({l_default_exec})')
                    self.m_rigcam_exec_path = l_default_exec
                
                # Crea il comando per eseguire rigcam
                l_rigcam_cmd = self.m_rigcam_exec_path
                if self.m_rigcam_exec_path.endswith('.py'):
                    l_rigcam_cmd = 'python ' + l_rigcam_cmd
                else:
                    self.m_logger.info('Making rigcam file executable')
                    helper.make_file_executable(self.m_rigcam_exec_path)
                l_rigcam_cmd += f' -host {l_redis_host} -port {l_redis_port}'

                self.m_logger.warning(f'Launching rigcam with command: {l_rigcam_cmd}')
                
                # Set process start
                self.m_rigcam_last_start = helper.timeNowObj()
                self.m_rigcam_running = True

                # Run process
                try:
                    os.system(l_rigcam_cmd)
                except Exception as e:
                    self.m_logger.critical(f'Camera process error ({type(e)}): {e}')
                finally:
                    # Set process termination
                    self.m_rigcam_last_term = helper.timeNowObj()
                    self.m_rigcam_running = False

            elif l_processType == 'fake':
                self.m_rigcam_last_start = helper.timeNowObj()
                self.m_rigcam_running = True
                self.m_rigcam_ready = True
                while not self.m_stop:
                    if self.m_rigcam_closing:
                        break
                    time.sleep(1)
                self.m_rigcam_last_term = helper.timeNowObj()
                self.m_rigcam_running = False

        
        self.m_logger.warning('rigcam process terminated')

    def _proc_rigcam_manager(self):
        """
        Gestisci l'esecuzione di rigcam:
            -   riavvia rigcam quando richiesto;
                -   forza il riavvio dopo un timeout, se necessario;
            -   all'avvio di rigcam, controlla la corretta esecuzione, e al 
                termine di un timeout, se necessario, richiedi il riavvio;
        """
        self.m_logger.info('rigcam_manager thread running')

        # Timeout di attesa che rigcam segnali di essere pronto
        try:
            l_rigcam_ready_timeout = datetime.timedelta(
                seconds=int(self.m_config.camera.ready_timeout.get())
            )
        except:
            self.m_logger.error(
                'Error reading camera timeout from conf: applying default timeout of 60 seconds'
            )
            l_rigcam_ready_timeout = datetime.timedelta(seconds=60)

        # Intervallo tra un tentativo di chiusura e una chiusura forzata successiva
        l_rigcam_kill_interval = datetime.timedelta(seconds=10)

        # Intervallo tra la chiusura di rigcam e la successiva riapertura
        l_rigcam_stop_start_interval = datetime.timedelta(seconds=10)

        # Intervallo minimo tra due riavii successivi
        l_rigcam_restarts_interval = l_rigcam_ready_timeout

        # Memorizza il timestamp dell'ultimo riavvio
        l_rigcam_last_restart = helper.timeNowObj()

        self._wait_for_barrier('proc_rigcam_manager')

        while not self.m_stop:
            try:
                # rigcam avviato e non in fase di chiusura
                if self.m_rigcam_running and not self.m_rigcam_closing:
                    # Startup report NON ricevuto
                    if not self.m_rigcam_ready:
                        l_start_delta = helper.timeNowObj() - self.m_rigcam_last_start

                        # rigcam ha ecceduto il timeout per essere pronto
                        if l_start_delta >= l_rigcam_ready_timeout:
                            self.m_logger.info('rigcam startup timeout')
                            self.m_rigcam_late = True

                # Situazione che richiede il riavvio
                if not self.m_rigcam_closing and (
                    self.m_rigcam_late or 
                    self.m_rigcam_error or
                    self.m_rigcam_crash
                ):
                    self.m_logger.info(
                        f'Closing rigcam. Late: {self.m_rigcam_late}. ' +\
                            f'Error: {self.m_rigcam_error}. Crash: {self.m_rigcam_crash}'
                    )
                    self.m_restart_rigcam = True

                # Richiesto il riavvio di rigcam
                if self.m_restart_rigcam and not self.m_rigcam_closing:
                    l_last_restart_delta = helper.timeNowObj() - l_rigcam_last_restart

                    # Ferma rigcam se è passato tempo sufficiente dall'ultimo riavvio
                    if l_last_restart_delta >= l_rigcam_restarts_interval:
                        self.m_logger.info('Sending exit request to rigcam')
                        self.m_rigcam_closing = True
                        l_rigcam_last_restart = helper.timeNowObj()
                        self.m_redisI.send_exit_rigcam()
                    else:
                        l_close_eta = l_rigcam_restarts_interval - l_last_restart_delta
                        self.m_logger.info(
                            f'Closing rigcam in {l_close_eta.seconds} seconds'
                        )
    
                # Messaggio di chiusura inviato a rigcam, che è ancora in esecuzione
                if self.m_rigcam_closing and self.m_rigcam_running:
                    l_last_close_delta = helper.timeNowObj() - l_rigcam_last_restart

                    # Chiusura forzata per timeout
                    if l_last_close_delta >= l_rigcam_kill_interval:
                        if self.m_rigcam_exec_path is not None:
                            self.m_logger.warning(
                                f'Camera proc did not exit after {l_rigcam_kill_interval.seconds} ' +\
                                    'seconds: forcing termination'
                            )
                            l_rigcam_last_restart = helper.timeNowObj()
                            helper.kill_process(self.m_rigcam_exec_path)
                        else:
                            self.m_logger.error(
                                'Cannot force rigcam termination because I do not know ' +\
                                    'its exec path'
                            )

                # Riavvia rigcam dopo un periodo di tempo a seguito della chiusura (evita errori Vimba)
                if not self.m_rigcam_running and not self.m_start_rigcam.is_set():
                    l_term_delta = helper.timeNowObj() - self.m_rigcam_last_term

                    # Riavvia rigcam se è passato tempo sufficiente dalla chiusura
                    if l_term_delta >= l_rigcam_stop_start_interval:
                        self.m_logger.info('Restarting rigcam')
                        self.m_start_rigcam.set()
                    else:
                        l_restart_eta = l_rigcam_stop_start_interval - l_term_delta
                        self.m_logger.info(
                            f'Restarting rigcam in {l_restart_eta.seconds} seconds'
                        )

            except Exception as e:
                self.m_logger.error(f'Error in rigcam_manager loop({type(e)}): {e}')
            
            time.sleep(1)

        self.m_logger.warning('rigcam_manager process terminated')

    def _getProcCameraFake(self):
        return self.m_procCamera

    def _proc_io(self):
        """
        Runanble controllo io,
        ha il suo listener per i topic di intaresse

        Parameters
        ----------
        p_config : json dict
            configurazione io
        """
        self.m_logger.info("IO control thread running")
        l_timeout= 1.0
        try:
            l_timeout= self.m_config.io.timeout.get()
        except KeyError as e:
            self.m_logger.error("Invalid key : " + str(e))
        # Fake seriale enbled
        if self.m_config.main.modules_enabled.bus485.get() == conf_values.module.fake:
            initFakeSerialBus()
        # Init gestore delle comunicazioni sul  bus
        l_comm= iocomm.IOComm()     
        self.m_procIo= l_comm
        if not l_comm.isOk():
            self.m_logger.critical("Can't start io comm module")
            self.m_redisI.setProcError("proc_io", "Can't init iocomm")
            self.m_critical= True
            return
        l_comm.run()
        #
        self._wait_for_barrier('proc_io')
        # Attesa richieste coda io ( ccon timeout, non bloccante )
        self.m_logger.info("IO control thread  operative")
        while not self.m_stop:
            try:
                # Estrazione del prossimo comando da inviare sul bus dalla coda del main proc
                l_cmd= self.m_ioQ.get(block= True, timeout= l_timeout)
            except queue.Empty: continue
            # cmd processing
            if not l_cmd: continue
            # cmd present
            self.m_logger.info("Io commands to be processed: "+ l_cmd[internal.cmd_key.io_cmd])
            # I comandi STOP e RESTART sono cmd interni per la chiusura del proc io
            if l_cmd[internal.cmd_key.io_cmd] == keywords.cmd_stop:
                self.m_logger.info("proc_io request to exit control thread")
                self.close(term_msg=keywords.term_msg_exit)
                break
            if l_cmd[internal.cmd_key.io_cmd] == keywords.cmd_restart:
                self.m_logger.info("proc_io request to exit control thread and reboot")
                self.close(term_msg=keywords.term_msg_reboot)
                break
            # TX - RX BLOCK START
            # Invio e ricezioni devono rimanere confinati all'interno della visibilità
            # di un singolo comando
            # Invio il comando alla coda di invio del bus io
            self.m_procIo.queueCmd(l_cmd)
            # Ottengo sempre una risposta dai livelli inferiori
            # anche quando rx è in timeout o riceve una risposta errata missed answer
            # la rispsota può anche essere un msg boradcast slegato dalla mia richiesta..
            l_ansKey= {}
            while not l_ansKey and not self.m_stop:
                l_ansKey= l_comm.dequeueAnswsers()
            # TX - RX BLOCK END
            # Analisi risposta
            self.m_logger.debug("Got answer to process")
            if isinstance(l_ansKey, dict):
                # Controllo mancata risposta, faccio avanzare il trig flow connesso se presente
                if 'missed_answer' in l_ansKey.keys():
                    if isinstance(l_cmd, dict) and internal.cmd_key.trigflow_instance in l_cmd.keys():
                        if self._checkFlowInstance(l_cmd[internal.cmd_key.trigflow_instance]):
                            l_flow_instance= l_cmd[internal.cmd_key.trigflow_instance]
                            l_flow_instance.gotMissedAnswerContinue()
                else:
                    # Risposta corretta
                    for key, data in l_ansKey.items():
                        if key == keywords.key_bus_error:
                            continue
                        #self.m_logger.info("Got answer " + str(key) + " " + str(data))
                        # storage msg intero decodificato, solo dell'ultimo ricevuto, sulla cache
                        l_entireMsg= l_comm.getReceiveddecodedMsgs()[-1]
                        # Considero la rispsota come ottenuta ( dovrei controllare il comando )
                        # la risposta va riportata al richiedente (trigflow_instance, console_instance)
                        self.m_logger.debug(str(l_entireMsg))
                        if isinstance(l_cmd, dict) and internal.cmd_key.trigflow_instance in l_cmd.keys():
                            if self._checkFlowInstance(l_cmd[internal.cmd_key.trigflow_instance]):
                                l_flow_instance= l_cmd[internal.cmd_key.trigflow_instance]
                                l_flow_instance.parseAnswer(key, data)
                        elif 'console_instance' in l_cmd.keys():
                            if self._checkFlowInstance(l_cmd['console_instance']):
                                l_cmd['console_instance'].sendAnswer(key, data) # TODO
        " uscita thread io "
        l_comm.close()
        self.m_logger.info("proc_io exiting control thread")
        self.m_redisI.setProcError("proc_io", "exited normally")

    def _proc_broker(self):
        """
        Runanble controllo processo kafka broker
        """
        self.m_logger.info("proc broker starting")
        # Rela broker process
        if self.m_config.main.modules_enabled.broker.get() == conf_values.module.deploy:
            while not self.m_stop:
                l_broker= KafkaBroker(
                    self.m_topicQ,
                    self.m_queue
                )
                self.m_kafkaBroker= l_broker
                if not l_broker.is_ok():
                    self.m_logger.error("Proc broker starting failed!")
                else:
                    self.m_logger.info("Broker object started correctly")
                #
                self._wait_for_barrier('proc_broker')
                # Lasciamo in esecuzione questo thread
                while not self.m_stop and self.m_kafkaBroker.is_ok():
                    time.sleep(1)
                if not self.m_kafkaBroker.is_ok() and not self.m_stop:
                    self.m_logger.warning('Resetting Kafka broker...')
                    self.m_kafkaBroker.close()

        # Fake proc broker (always says OK)
        elif self.m_config.main.modules_enabled.broker.get() == conf_values.module.fake:
            self.m_kafkaBroker = FakeBroker(self.m_topicQ, self.m_queue)
            self._wait_for_barrier('proc_broker')
            while not self.m_stop:
                time.sleep(1)
        
        else:
            self.m_logger.critical('Broker module not "deploy" nor "fake"')
            self._wait_for_barrier('proc_broker')
        #
        self.m_logger.warning("Proc broker exiting..")
        
    """ ----- CMD PROCESSING ----- """
    
    def _cmdProcessing(self, p_cmd: dict):
        """
        Processing comandi coda interna al main process
        Ricevo un dict del tipo :
            {
            cmd_type: 'evt'
            evt_type: 'type', [se è evt avrai evt type]
            }
            {
            cmd_type: 'trig_flow ',
            trig_inst: istanza work flow di un evento trigger treno
            trig_cmd: comando da eseguire da parte del flow handler
            }       
            {
             cmd_type: 'topic_evt'   
             ...
            }
        """
        try:
            if not internal.cmd_key.cmd_type in p_cmd.keys():
                self.m_logger.error('Internal error: found a command in the command queue without the field "cmd_type"')
                return

            # Camera event
            if p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.camera_evt:
                if internal.cmd_key.evt_data in p_cmd.keys():
                    if not self.m_conf_integrity:
                        self.m_logger.critical('Camera event stopped because the configuration contains errors!')
                        return

                    def start_trig_flow():
                        l_event_data= wrapkeys.getValueDefault(p_cmd, None, internal.cmd_key.evt_data)
                        l_trig_flow= FlowCameraEvent(self.m_core, l_event_data)
                        l_trig_flow.start()

                        # in caso di test trig flow stop on error
                        if self.m_config.main.modules_enabled.camera == conf_values.module.fake:
                            self.m_logger.warning('Stopping the trigger event flow because the camera process is fake')
                            l_trig_flow.stopOnError()

                        # accodo il trig flow
                        self.m_trigs.append(l_trig_flow)

                        # Richiesta di messa in pausa del recovering
                        self.m_recovery_manager.pause()

                    # Comincia subito il flow camera event se il flow startup è
                    # già stato eseguito
                    if self.m_startup_done.is_set():
                        self.m_logger.info('Starting flow camera event immediately')
                        start_trig_flow()
                    # Altrimenti, ritarda l'inizio del flow camera event
                    else:
                        self.m_logger.warning(
                            'Delaying flow camera event after the startup'
                        )
                        l_trig_flow_delayer = ExecutionDelayer(
                            delayer= self.m_startup_done,
                            functions=[
                                start_trig_flow
                            ],
                            name=f'trig_launcher_{helper.timestampNow()}',
                            abort=self.m_stop_event
                        )
                        l_trig_flow_delayer.start()

            # Comandi e richieste interne ai flows
            elif p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.trig_flow:
                self.m_logger.debug('trig_flow command received')
                
                # Comando per il bus seriale
                if internal.cmd_key.io_cmd in p_cmd.keys():
                    # Accodo in invio seriale
                    self.m_logger.debug(f'Command to bus queue: {helper.prettify(p_cmd)}')
                    self.m_ioQ.put(p_cmd)
                    
                # Info dal flow per il main proc
                if internal.cmd_key.says in p_cmd.keys():
                    if p_cmd[internal.cmd_key.says]== keywords.info_pipe_ended:
                        if internal.cmd_key.trigflow_instance in p_cmd.keys():
                            self.m_logger.debug("Got pipe ended, it will be cleared by periodic process")                                     
                        # Update memory usage
                        # rigproc
                        l_rigproc_pid = self.m_redisI.get_rigproc_pid()
                        if isinstance(l_rigproc_pid, int):
                            l_rigproc_mem = helper.get_process_mem_usage(l_rigproc_pid)
                            if l_rigproc_mem is not None:
                                self.m_redisI.set_rigproc_mem_usage(l_rigproc_mem)
                                self.m_logger.info(f'rigproc mem usage: {l_rigproc_mem} MB')
                            else:
                                self.m_logger.error(
                                    f'Error getting rigproc mem usage: will not update'
                                )
                        else:
                            self.m_logger.error(f'Error getting saved rigproc pid: getting from os')
                            l_rigproc_pid = helper.get_my_pid()
                            if isinstance(l_rigproc_pid, int):
                                self.m_redisI.set_rigproc_pid(l_rigproc_pid)
                        # rigcam
                        if self.m_config.camera.process_type.get() == 'subprocess':
                            l_rigcam_pid = self.m_redisI.get_rigcam_pid()
                            if isinstance(l_rigcam_pid, int):
                                l_rigcam_mem = helper.get_process_mem_usage(l_rigcam_pid)
                                if l_rigcam_mem is not None:
                                    self.m_redisI.set_rigcam_mem_usage(l_rigcam_mem)
                                    self.m_logger.info(f'rigcam mem usage: {l_rigcam_mem} MB')
                                else:
                                    self.m_logger.error(
                                        f'Error getting rigcam mem usage: will not update'
                                    )
                            else:
                                self.m_logger.error(
                                    f'Error getting saved rigcam pid: will not print mem usage'
                                )                

            # Invio topic
            elif p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.topic_evt:
                if internal.cmd_key.topic_type in p_cmd.keys():
                    # richiesta invio topic
                    self.m_logger.debug("topic : " + p_cmd[internal.cmd_key.topic_type])
                    self.m_topicQ.put(p_cmd)
                else:
                    self.m_logger.error('Unspecified topic type in topic evt')

            # Risposta invio topic
            elif p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.topic_response:
                if internal.cmd_key.trigflow_instance in p_cmd.keys():
                    # ritorno il comando ricevuto con in aggiunta lo stato del tx topic
                    # Il flow trigger vive all'interno del recovery quindi non devo tenerne traccia?
                    # TODO verificare ch sia sensato
                    #if self._checkFlowInstance(l_trigFlow):
                    l_topicAnswer= {}
                    l_topicAnswer['topic_response']= p_cmd[internal.cmd_type.topic_response]
                    l_trigFlow: eventtrigflow.EventTrigFlow= p_cmd[internal.cmd_key.trigflow_instance]
                    try:
                        l_trigFlow.parseAnswer('topic_response', p_cmd)
                    except Exception as e:
                        self.m_logger.critical(f'Error executing Kafka flow callback ({type(e)}): {e}')
                        self.m_critical= True
                else:
                    self.m_logger.error(" expecting trig_instance..not found ")

            # Store evt for recovering
            elif p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.store_for_recovery:
                if internal.cmd_key.evt_to_recover in p_cmd.keys():
                    self.m_recovery_manager.store_event(p_cmd[internal.cmd_key.evt_to_recover])
                else:
                    self.m_logger.error('Malformed recovery store request')
            
            # Recovery flow
            elif p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.recovery_flow:
                if internal.cmd_key.evt_to_recover in p_cmd.keys():
                    recovery_flow= FlowRecovery(
                        core=self.m_core,
                        event_to_recover=p_cmd[internal.cmd_key.evt_to_recover]
                    )
                    recovery_flow.start()
                    self.m_otherFlows.append(recovery_flow)
                else:
                    self.m_logger.error('Malformed recovery flow request')

            # Recovery success
            elif p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.recovery_success:
                if internal.cmd_key.evt_to_recover in p_cmd.keys():
                    self.m_recovery_manager.recovery_success(p_cmd[internal.cmd_key.evt_to_recover])
                else:
                    self.m_logger.error('Malformed recovery success request')

            # Recovery failure
            elif p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.recovery_failure:
                if internal.cmd_key.evt_to_recover in p_cmd.keys():
                    self.m_recovery_manager.recovery_failure(p_cmd[internal.cmd_key.evt_to_recover])
                else:
                    self.m_logger.error('Malformed recovery failure request')

            # Rinnovo file di log
            elif p_cmd[internal.cmd_key.cmd_type] == internal.cmd_type.renew_logs_flow:
                renew_log_flow = FlowRenewLogs(core=self.m_core)
                renew_log_flow.start()
                self.m_otherFlows.append(renew_log_flow)

            # Actions seguenti a rielvamenti (ad esempio alimentazione mancante)
            elif p_cmd[internal.cmd_key.cmd_type]== internal.cmd_type.action:
                if internal.cmd_key.action_type not in p_cmd.keys():
                    self.m_logger.error("malformed action command {}".format(p_cmd))
                else:
                    # Startup done
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_startup_done:
                        self.m_logger.info('Startup flow is done')
                        self.m_startup_done.set()
                    # Shut down
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_shut_down_flow:
                        if self.m_startup_done.is_set():
                            # Creo il trig flow per lo shut down
                            # TODO t_off_ivip?
                            l_flowShutDown= eventtrigflow.EventTrigFlow(self.m_core,
                                                        p_cmd[internal.cmd_key.action_type],
                                                        keywords.flow_type_shutdown)
                            self.m_otherFlows.append(l_flowShutDown)
                        else:
                            self.m_logger.warning(
                                'Shutdown action ignored because startup is not done yet'
                            )
                    # Abort shut down procedure
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_shut_down_aborted_flow:
                        l_flowShutDownAbort= eventtrigflow.EventTrigFlow(self.m_core,
                                                p_cmd[internal.cmd_key.action_type],
                                                keywords.flow_type_shutdown_aborted)
                        self.m_otherFlows.append(l_flowShutDownAbort)
                    # Vero comando di shutdown dell'intero sistema
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_shut_down:
                        # Bye Bye world
                        self.m_stop = True
                        time.sleep(10)
                        self.m_logger.warning("shutting down system")
                        # os.system("sudo shutdown -h now")
                        self.close(term_msg=keywords.term_msg_shutdown)
                    # Iscrizione RIP
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_subscribe:
                        l_subscribe= eventtrigflow.EventTrigFlow(
                            self.m_core,
                            'subscription',
                            keywords.flow_type_subscription
                        )
                        self.m_otherFlows.append(l_subscribe)
                    # Trig flow (TEST)
                    if p_cmd[internal.cmd_key.action_type] == keywords.action_trig:
                        l_evt_name= keywords.evt_trigger_test_name
                        # Imposta trigger palo A su Redis: 
                        # il subscriber rileverà l'evento e inserirà il comando in code
                        self.m_redisI.cache.hset(
                            l_evt_name, 
                            keywords.key_evt_trig_which_prr,
                            keywords.key_prrA
                        )
                    # Power check ed analisi periodica
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_periodic_flow:
                        l_pwr_check= eventtrigflow.EventTrigFlow(
                            self.m_core,
                            'power_check',
                            keywords.flow_type_power_check
                        )
                        self.m_otherFlows.append(l_pwr_check)
                    # Pausa task periodici
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_pause_periodic:
                        self.m_periodic_paused= True
                        self.m_logger.warning("Periodic task paused")
                    if p_cmd[internal.cmd_key.action_type]== 'resume_periodic':
                        self.m_periodic_paused= False
                        self.m_logger.warning("Periodic task resumed")
                    # Richiesta diagnosi del sistema
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_diagnosis_flow:
                        # Estrazione dati transizione dal topic in arrivo
                        l_diag_data= {}
                        if internal.cmd_key.data in p_cmd.keys():
                            l_diag_data= p_cmd[internal.cmd_key.data]
                        l_diagnosis= eventtrigflow.EventTrigFlow(
                            self.m_core,
                            'diagnosis',
                            keywords.flow_type_diagnosis,
                            l_diag_data
                        )
                        self.m_otherFlows.append(l_diagnosis)
                    # Richiesta raccolta dati impianto
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_implant_status_flow:
                        l_implant_status= eventtrigflow.EventTrigFlow(
                            self.m_core,
                            'implant_status',
                            keywords.flow_type_implant_status,
                            p_request_id= wrapkeys.getValueDefault(p_cmd, None, internal.cmd_key.request_id)
                        )
                        self.m_otherFlows.append(l_implant_status)
                    # Send anomaly request
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_anomaly_flow:
                        l_int_set_upd= eventtrigflow.EventTrigFlow(
                            self.m_core,
                            'anomaly',
                            keywords.flow_type_anomaly,
                            p_data= wrapkeys.getValueDefault(p_cmd, None, internal.cmd_key.data)
                        )
                        self.m_otherFlows.append(l_int_set_upd)
                    # Int set update request
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_int_set_upd_flow:
                        l_int_set_upd= eventtrigflow.EventTrigFlow(
                            self.m_core,
                            'int_set_upd',
                            keywords.flow_type_int_sett_upd,
                            p_data= wrapkeys.getValueDefault(p_cmd, None, internal.cmd_key.data)
                        )
                        self.m_otherFlows.append(l_int_set_upd)
                    # Time win update request
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_time_win_upd_flow:
                        l_time_win_upd= eventtrigflow.EventTrigFlow(
                            self.m_core,
                            'time_win_upd',
                            keywords.flow_type_time_win_upd,
                            p_data= wrapkeys.getValueDefault(p_cmd, None, internal.cmd_key.data)
                        )
                        self.m_otherFlows.append(l_time_win_upd)
                    # Sw update request
                    if p_cmd[internal.cmd_key.action_type]== keywords.action_update_flow:
                        l_diag_data= {}
                        if internal.cmd_key.data in p_cmd.keys():
                            l_diag_data= p_cmd[internal.cmd_key.data]
                            try:
                                l_diag_data[keywords.flin_remote_update_folder]= \
                                    self.m_config.main.sw_update.package_remote_folder.get()
                                l_diag_data[keywords.flin_local_update_folder]= \
                                    self.m_config.main.sw_update.package_local_folder.get()
                                l_diag_data[keywords.flin_exec_folder]= \
                                    self.m_config.boot.exec_dir.get()
                            except KeyError as e:
                                self.m_logger.error('Remote, local or executable folder information missing in the configuration')
                                return
                            # Creazione sw update flow se ci sono i dati di input necessari
                            l_sw_update= eventtrigflow.EventTrigFlow(
                                self.m_core, 
                                'update',
                                keywords.flow_type_sw_update,
                                l_diag_data,
                            )
                            self.m_otherFlows.append(l_sw_update)

                    # Wake up flow
                    if p_cmd[internal.cmd_key.action_type] == keywords.action_wake_up :
                        if internal.cmd_key.trigflow_instance in p_cmd.keys():
                            p_cmd[internal.cmd_key.trigflow_instance].parseAnswer(keywords.action_wake_up,None)
                        else:
                            self.m_logger.critical("Missing isntance in flow request wake up")

                    # Stop dai thread inferiori, via comando seriale
                    # TODO dovrei riportare lo stop come action...
                    if p_cmd[internal.cmd_key.action_type] == keywords.action_stop :
                        self.m_logger.warning("Got internal stop request, ask to exit")
                        l_stop_cmd={}
                        l_stop_cmd[internal.cmd_key.io_cmd]= keywords.cmd_stop
                        self.m_ioQ.put(l_stop_cmd)

            # Reset configurazione al file json
            elif p_cmd[internal.cmd_key.cmd_type] == internal.cmd_type.reset_conf:
                self.m_config.reset_configuration()

            # Riavvio rigcam
            elif p_cmd[internal.cmd_key.cmd_type] == internal.cmd_type.reboot_rigcam:
                self.m_logger.info('Reboot rigcam request')
                self.m_restart_rigcam = True

            # Comando sconosciuto
            else:
                self.m_logger.error(f'Trovato in coda "cmd_type" scunosciuto: {p_cmd[internal.cmd_key.cmd_type]}')

        # Exceptions..
        except KeyError as k:
            self.m_logger.error("key error : " + str(k))
            traceback.print_exc()

    " ---- FLOWs ---- "

    def _checkFlowInstance(self, p_flow) -> bool:
        """ Controllo se il flow è tra quelli tracciati dal main proc 
        Il flow in oggetto potrebbe essere stati eliminato per timeout o per
        richiesta di uscita dal programma
        """
        if p_flow in self.m_trigs or p_flow in self.m_otherFlows:
            return True
        return False

    def _deleteFlow(self, p_flow) -> None:
        """ Eliminazine flow dalle liste interne """        
            # Rimuovo il trig flow dalle liste di riferimento
        if p_flow.isDone():
            if p_flow in self.m_trigs:
                self.m_logger.warning('Removing one flow from trig flows list')
                self.m_trigs.remove(p_flow)
                if len(self.m_trigs) == 0:
                    self.m_recovery_manager.resume()
            if p_flow in self.m_otherFlows:
                self.m_logger.warning('Removing one flow from other flows list')
                self.m_otherFlows.remove(p_flow)
        else:
            self.m_logger.debug('The flow is not done yet')
        gc.collect()

    "  ---- HELPERS ----- "

        
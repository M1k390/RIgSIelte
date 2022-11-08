#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestione comunicazione su bus io
"""
import serial
import queue
import threading
import traceback

from rigproc.io import  iogrammar
from rigproc.io import  ioanswers

from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI

from rigproc.commons.logger import logging_manager
from rigproc.commons.wrappers import wrapkeys
from rigproc.commons.helper import helper

from rigproc.params import general, internal, bus




class IOComm():
    """
    Gestione protocollo di comunicazione verso l'io
    """
    
    def __init__(self):
        """
        Init ed attivazione sottomoduli di parsing
        
        p_config configurazione modulo        
        """
        " init "
        self.m_config= get_config().io
        self.m_logger= logging_manager.generate_logger(
            logger_name='bus',
            format_code=get_config().logging.bus.format.get(),
            console_level=get_config().logging.bus.console_level.get(),
            file_level=get_config().logging.bus.file_level.get(),
            log_file_name=get_config().logging.bus.file_name.get(),
            log_file_dir=get_config().logging.bus.file_dir.get(),
            log_file_mode=get_config().logging.bus.file_mode.get(),
            root_log_file_prefix=get_config().logging.root.file_name.get() \
                if get_config().logging.bus.log_to_root.get() else None,
            root_log_dir=get_config().logging.root.file_dir.get() \
                if get_config().logging.bus.log_to_root.get() else None,
            formatter_setting=get_config().logging.bus.formatter.get()
        )
        self.m_ok= False
        self.rxBufer= bytearray()
        self.m_decodedMsgs= []
        self.m_errorList=[]
        self.m_sentList=[]
        self.m_requestCnt= 0
        self.m_missed = 0
        self.m_retries= 2
        " Lettura conf "
        l_speed=""
        l_parity=""
        l_cts=""
        l_device=""
        self.m_timeout=""
        l_timeoutMsg=""
        try:
            l_device= self.m_config.device.get()
            l_speed= self.m_config.speed.get()
            self.m_timeout= self.m_config.timeout.get()
            l_parity= self.m_config.parity.get()
            l_cts= self.m_config.cts.get()
            l_timeoutMsg= self.m_config.timeoutAnswer.get()
            l_stopB= self.m_config.stopbits.get()

            # Log serial port info
            self.m_logger.info(
                'SERIAL PORT CONF\n' +\
                f'    Device:    {l_device}\n' +\
                f'    Speed:     {l_speed}\n' +\
                f'    Timeout:   {self.m_timeout}\n' +\
                f'    Parity:    {l_parity}\n' +\
                f'    CTS:       {l_cts}\n' +\
                f'    Stop bits: {l_stopB}\n'
            )

            # Give serial port permissions
            if self.m_config.set_linux_permissions.get():
                self.m_logger.info(f'Giving {l_device} max Linux permissions...')
                if not helper.give_file_max_permissions(l_device):
                    self.m_logger.error(f'Cannot give {l_device} max Linux permissions')
            
            # Open serial port 
            self.m_port= serial.Serial(
                port=l_device, 
                baudrate=l_speed, 
                parity= self._parity(l_parity),
                timeout= self.m_timeout,
                rtscts= l_cts,
                exclusive= True,
                stopbits= l_stopB
            )
            self.m_retries= self.m_config.retries.get()
        except KeyError as e:
            l_err="Error reading conf [exc]: " + str(e)
            self.m_logger.error(l_err)
            self.m_errorList.append(l_err)
            return
        except Exception as e:
            l_err= "Exception opening serial port [exc]: " + str(e)
            self.m_logger.error(l_err)
            self.m_errorList.append(l_err)
            return
        " Check port opened "
        if not self.m_port.isOpen():
            l_err="Serial port not opened [dev]: "+ l_device
            self.m_logger.error(l_err)
            self.m_errorList.append(l_err)
        " ok "
        self.m_ansDecoder= ioanswers.IOAnswers(self.m_logger)
        self.m_timeoutMsg= l_timeoutMsg
        self.m_commands= self._setCommands()
        self.m_commandsQ= queue.Queue()
        self.m_answersQ= queue.Queue()
        self.m_grammar= iogrammar.IoGrammar(self.m_logger)        
        self.m_exEnabled= True
        self.events= threading.Event()
        self.m_cmdIsRunning= False
        self.m_ok= self.m_port.isOpen()
        self.m_expectedAnswer= ''
        self.m_redisI= get_redisI()
        

    " ---- INTERFACE ---- "        
        
    def run(self):
        """
        Launcher thread comandi
        """
        self.m_thCmd= threading.Thread(target= self._executeCmd)
        self.m_thCmd.daemon= True
        self.m_thCmd.start()     
        self.m_rx= threading.Thread(target= self._rxThread)
        self.m_rx.daemon= True
        self.m_rx.start()

    def isOk(self):
        """
        Ritorna il flag m_ok
        """
        return self.m_ok            
                                      
    def queueCmd(self, p_cmd):
        """
        Entry point principale per l'esecuzione comandi ed attività
        io bus
        """                        
        self.m_commandsQ.put(p_cmd)        
        
    def dequeueAnswsers(self):
        """
        Attende la risposta al comando, timeotut

        Returns
        -------
        (None,None) o ppure (key,value)

        """
        l_ans={}
        try:
            l_ans= self.m_answersQ.get(timeout= self.m_timeout)
        except queue.Empty:
            return None
        except ValueError as e:
            self.m_logger.error("Error getting answer from queue: " + str(e))
            l_ans={}
            l_ans[bus.error]=''
        self.m_logger.debug(f'Dequeuing answer')
        return l_ans

    def _informExit(self):
        """ invia il comando di stop al main proc """
        l_action={}
        l_action[internal.cmd_key.cmd_type]= internal.cmd_type.action
        l_action[internal.cmd_key.action_type]= internal.action.stop
        # self.m_outQ.put(l_action)
        # TODO ricevere la coda comandi generale ed inviare action cmd queue ? 

    def close(self):
        """
        Esegue il join sul thread dei comandi ed il thread rx
        """
        self.m_exEnabled= False
        self.m_thCmd.join()
        self.m_rx.join()

    def cmdThreadIsRunning(self):
        """ GEtter thread tx running flag """
        return self.m_cmdIsRunning

    def getErrors(self):
        """ getter error list """
        return self.m_errorList

    def getSentCommands(self):
        """ getter lista comandi inviati """
        return self.m_sentList

    def getReceiveddecodedMsgs(self):
        """ Getter msg ricevuti con destinatario videserver """
        return self.m_decodedMsgs

    def getReqCnt(self):
        """ Getter contatore richieste di invio comandi """
        return self.m_requestCnt

    def getMissed(self):
        """ Getter contatore mancate risposte """
        return self.m_missed

    " ----- RX  ----- "
            
    def _rxThread(self):
        """
        Rx thread
        """
        self.m_inputMsg= bytearray()
        self.m_port.flush()
        while self.m_exEnabled:
            try:                
                l_new= bytearray(self.m_port.readline())
            except Exception as e:
                self.m_logger.critical(
                    f'Serial port readline got errors!! Unmanaged exception {type(e)}: {e}'
                )
                #TODO exit!
                continue
            try:
                if l_new:
                    self.m_logger.info('Incoming msg: ' + helper.format_bytearray(l_new))
                self.m_inputMsg.extend(l_new)
                self._parseInputMsg(self.m_inputMsg)
            except Exception as e:
                self.m_logger.error(f'Error parsing bus msg: resetting buffer! ({type(e)}): {e}')
                self.m_inputMsg = bytearray()
                pass
               
                      
    def _parseInputMsg(self, p_buf):
        """
        Input data parser, controlla i msg in arrivo
        il msg correttamente decodficiato è un dict
        Se il buffer è vuoto questa func non interviene
        {
         'valid': 'true false'
         'src': 'src',
         'dest': 'dest',
         'io_cmd': 'cmd',
         'data': 'data',
         'pos': 'pos stx al momento del decode'         
         'msg': 'msg intero'
         }
        """
        # Estrazione messaggi dal buffer
        l_msgs= self.m_grammar.findMsg(p_buf)
        # Se non ho nessun comando in attesa di risposta esco
        if not self.m_expectedAnswer:
                # TODO inserire una gestione per i msg ricevuti di tipo broad cast ?
                return
        # Analisi messaggi estratti, sto attendendo risposta da qualcuno
        for l_msg in l_msgs:
            # inserimento chiave in cache con score su timestamp
            if self.m_redisI:                
                self.m_redisI.storeMsgWithScore(l_msg)            
            # Chec destinatario
            if l_msg['dest'] != bus.module.videoserver:
                # TODO inserire una gestione per i msg ricevuti di tipo broad cast ?
                self.m_logger.warning('Last IO message was not for me')
                continue
            # Tengo traccie del messaggio decodificato se è per me
            self.m_decodedMsgs.append(l_msg)
            #" Estraggo tipo di dato - valore "
            self.m_logger.debug("Msg incoming : " + str(l_msg))
            l_req, l_dataValueDict= self.m_ansDecoder.getKeyValue(l_msg['src'], l_msg['io_cmd'], l_msg['data'])
            # Se la decodifica non va buon fine passo oltre
            if not l_req:
                self.m_logger.warning("Missed incoming msg data decoded")
                continue
            #self.m_logger.debug("Got [key,value]: " +str(l_req) + " " + str(l_dataValueDict))
            # Se il msg è differente da quello per cui attendo risposta lo considero missed answer
            if l_req != self.m_expectedAnswer:
                self.m_logger.warning(f'Unexpected incoming message. Expected was: {self.m_expectedAnswer}, received was: {l_req}')
                continue
            self.m_logger.info("Expected answer to : "  + self.m_expectedAnswer
                                      + " got :" + str(l_req))
            # Risposta attesa ottenuta
            l_ans={}
            l_ans[l_req]=l_dataValueDict
            self.m_answersQ.put(l_ans)
            self.m_expectedAnswer = None
            # Segnalo ai livelli superiori che la richiesta è stata processata
            self.events.set()
            self.events.clear()

    " ---- TX ---- "
    
    def _executeCmd(self):
        """
        Runnable esecuzione comandi io
        Processa la coda dei comandi
        Eseguo un comando alla volta
        L'invio del comando attiva l'attesa della risposta ( con timeout )

        Parameters
        ---------

        p_dataDict: dicrionary
            Dict con i dati utili a completare il comando richiesto
        """
        self.m_logger.info("thread started")
        l_error= ""
        while self.m_exEnabled:
            self.m_cmdIsRunning= True
            try:
                l_cmd= self.m_commandsQ.get(block= True,timeout=1.0)
            except queue.Empty:
                continue            
            try:       
                #pdb.set_trace()
                self.m_requestCnt += 1
                l_msg= l_cmd['io_cmd']
                l_data= l_cmd['data']
                if l_msg in self.m_commands.keys():
                    self.m_logger.info("msg to sent: {}".format(l_msg))
                    # Esecuzione comando con dato numero di retries
                    l_attempts= self.m_retries
                    # eccezione alla regola del retry
                    if l_msg == bus.cmd.trig_click_a or l_msg == bus.cmd.trig_click_b:
                        l_attempts= 1    
                    l_got_it= False
                    while l_attempts and not l_got_it:
                        # Invio comando sul bus
                        l_sent= self.m_commands[l_msg](l_data)
                        # Inserimento msg in cache
                        if self.m_redisI:
                            self.m_redisI.storeMsgWithScore(l_cmd)
                        l_attempts = l_attempts- 1
                        if not l_sent:
                            continue
                        # Cmd sent
                        self.m_sentList.append(l_msg)
                        self.m_expectedAnswer = l_msg
                        # Attendo l'esito del comando, verifico il timeout
                        l_gotAnswer= self.events.wait(self.m_timeoutMsg)                    
                        if not l_gotAnswer:
                            # Se l'attesa evento è arrivata per timeout sono qui
                            # Quindi la risposta che attendo non è pervenuta
                            # nei tempi stabiliti
                            continue
                        else:
                            # Ho ottenuto la risposta che cerco, i livelli inferiori
                            # hanno inserito la risposta nella coda di uscita in autonomia
                            l_got_it= True
                    # Ho ottenuta la risposta che cerco ?
                    if not l_got_it:
                        # No, creo una risposta stub con indicazione del 'miss'
                        # e la inserisco nella coda di uscita
                        self.m_logger.error(f'Missed answer to: {helper.prettify(l_cmd)}')
                        l_cmd['missed_answer']= 'missed'
                        self.m_answersQ.put(l_cmd)
                        self.m_expectedAnswer = None
                        self.m_missed += 1
                else:
                    # Risposta di tipo sconosciuto
                    l_error= "Unknown request: "+ l_msg
                    self.m_logger.error(l_error)
                    self.m_errorList.append(l_error)
            except Exception as e:
                # Eccezione processo di invio - risposta 
                l_excp="Exception for command : " + l_msg+ " [exc] " + str(e)
                self.m_logger.error(l_excp)                
                self.m_logger.error(traceback.format_exc())                
                self.m_errorList.append(l_error)

        self.m_cmdIsRunning= False
    " ---- HELPER ---- "
           
    def _setCommands(self):
        """
        Costruzione tabella comandi funzioni
        """        
        l_commands={}
        l_commands[bus.cmd.stop]= self._stop
        l_commands[bus.cmd.mtx_ver_a]= self._sftxVersioneP
        l_commands[bus.cmd.mtx_ver_b]= self._sftxVersioneD
        l_commands[bus.cmd.mtx_vel_a]= self._sftxVelocitaP
        l_commands[bus.cmd.mtx_vel_b]= self._sftxVelocitaD
        l_commands[bus.cmd.mtx_on_off_a]= self._sftxOnOffP
        l_commands[bus.cmd.mtx_on_off_b]= self._sftxOnOffd
        l_commands[bus.cmd.mrx_ver_a]= self._sfrxVerP
        l_commands[bus.cmd.mrx_ver_b]= self._sfrxVerD
        l_commands[bus.cmd.mrx_wire_t0_a]= self._sfrxWireT0P
        l_commands[bus.cmd.mrx_wire_t0_b]= self._sfrxWireT0D
        l_commands[bus.cmd.mrx_tmos_a]= self._sfrxTmosfP
        l_commands[bus.cmd.mrx_tmos_b]= self._sfrxTmosfD
        l_commands[bus.cmd.mrx_wire_data_a]= self._sfrxWireDataP
        l_commands[bus.cmd.mrx_wire_data_b]= self._sfrxWireDataD
        l_commands[bus.cmd.trig_ver_a]= self._trigVerP
        l_commands[bus.cmd.trig_ver_b]= self._trigVerD
        l_commands[bus.cmd.trig_setting_a]= self._triggerSettingP
        l_commands[bus.cmd.trig_setting_b]= self._triggerSettingD
        l_commands[bus.cmd.trig_on_off_a]= self._triggerOnOffP
        l_commands[bus.cmd.trig_on_off_b]= self._triggerOnOffD
        l_commands[bus.cmd.trig_click_a]= self._triggerClickP
        l_commands[bus.cmd.trig_click_b]= self._triggerClickD
        l_commands[bus.cmd.trig_status_a]= self._triggerStatusP
        l_commands[bus.cmd.trig_status_b]= self._triggerStatusD
        l_commands[bus.cmd.io_ver]= self._ioVer
        l_commands[bus.cmd.io_test_batt]= self._ioTestBatt
        l_commands[bus.cmd.io]= self._ioStatus
        return l_commands

    def _parity(self, p_parity):
        """
        decodifica la parità da conf
        """
        if p_parity == 'none':
            return serial.PARITY_NONE
        if p_parity == 'even':
            return serial.PARITY_EVEN
        if p_parity == 'odd':
            return serial.PARITY_ODD

    " COMMANDS "

    def _stop(self):
        self.m_logger.debug("cmd stop")
        # TODO

    # MOSF_TX
        
    def _sftxVersioneP(self, p_data):
        self.m_logger.debug("cmd stfx version p")
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_tx_a, bus.cmd.mtx_ver_a, None)
        return self._sendCmdToPort(l_cmd)
        
    def _sftxVersioneD(self, p_data):
        self.m_logger.debug("cmd stfx version d")
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_tx_b, bus.cmd.mtx_ver_b, None)
        return self._sendCmdToPort(l_cmd)

    def _sftxVelocitaP(self, p_data):
        self.m_logger.debug("cmd stfx Speed p")
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_tx_a, bus.cmd.mtx_vel_a, None)
        return self._sendCmdToPort(l_cmd)

    def _sftxVelocitaD(self, p_data):
        self.m_logger.debug("cmd stfx Speed d")
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_tx_b, bus.cmd.mtx_vel_b, None)
        return self._sendCmdToPort(l_cmd)

    def _sftxOnOffP(self, p_data):
        """
        RECORD_RISPOSTA/RICHIESTA "COMANDO"0x62 Campo "DATI" MOSF_TX_On_Off:
        ch1 30h..3Fh riserva
        ch2 30h..3Fh riserva
        ch3 30h..3Fh MOSF_TX_On_Off , AutoTest
                     bit0=0 MOSF_TX_Off , bit0=1 MOSF_TX_On
                     bit3,2,1 AutoTest 000x=Null 001x=8,1kmh, 010x=10,3kmh , 011x=16,3kmh ,
                                       100x=32,7kmh , 101x=??kmh , 110x=??kmh , 111x=??kmh;
        ch4 30h..3Fh riserva
        """
        self.m_logger.debug("cmd myx on off p")
        l_data=b'0000'
        if p_data == general.status_on: l_data=b'0010'
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_tx_a, bus.cmd.mtx_on_off_a, l_data)
        return self._sendCmdToPort(l_cmd)

    def _sftxOnOffd(self, p_data):
        self.m_logger.debug("cmd mtx on off d")
        l_data=b'0000'
        if p_data == general.status_on: l_data=b'0010'
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_tx_b, bus.cmd.mtx_on_off_b, l_data)
        return self._sendCmdToPort(l_cmd)

    def _encodeTmosf(self, p_dTmosf):
        l_tPre= wrapkeys.getValueDefault(p_dTmosf, bus.mosf_data.default, bus.data_key.mosf_tpre)
        l_tPost= wrapkeys.getValueDefault(p_dTmosf, bus.mosf_data.default, bus.data_key.mosf_tpost)
        if not isinstance(l_tPre, int):
            try:
                l_tPre= int(l_tPre)
            except:
                self.m_logger.error(f'Tmosf time is not an integer: {l_tPre} ({type(l_tPre)})')
                l_tPre= bus.mosf_data.default
        if not isinstance(l_tPost, int):
            try:
                l_tPost= int(l_tPost)
            except:
                self.m_logger.error(f'Tmosf time is not an integer: {l_tPost} ({type(l_tPost)})')
                l_tPost= bus.mosf_data.default
        l_encoded= [l_tPre /10, l_tPre % 10, l_tPost /10, l_tPost % 10]
        l_encoded= [48+ int(x) for x in l_encoded]
        return l_encoded

    def _sfrxVerP(self, p_data):
        """
        comando version msof rx a
        """
        self.m_logger.debug("cmd strx version p")
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_rx_a, bus.cmd.mrx_ver_a, None)
        return self._sendCmdToPort(l_cmd)

    def _sfrxVerD(self, p_data):
        """
        comando version mosf rx a
        """
        self.m_logger.debug("cmd strx version d")
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_rx_b, bus.cmd.mrx_ver_b, None)
        return self._sendCmdToPort(l_cmd)    

    def _sfrxTmosfP(self, p_data):
        l_cmdstr="mrx tmosf p"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= self._encodeTmosf(p_data)
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_rx_a, bus.cmd.mrx_tmos_a, l_data)
        return self._sendCmdToPort(l_cmd)

    def _sfrxTmosfD(self, p_data):
        l_cmdstr="mrx tmosf d"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= self._encodeTmosf(p_data)
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_rx_b, bus.cmd.mrx_tmos_b, l_data)
        return self._sendCmdToPort(l_cmd)

    def _sfrxWireT0P(self, p_data):
        l_cmdstr="mrx twire T0 P"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_rx_a, bus.cmd.mrx_wire_t0_a, None)
        return self.m_port.write(l_cmd)

    def _sfrxWireT0D(self, p_data):
        l_cmdstr="mrx twire T0 P"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_rx_b, bus.cmd.mrx_wire_t0_b, None)
        return self._sendCmdToPort(l_cmd)

    def _sfrxWireDataP(self, p_data):
        l_cmdstr="mrx twire Data P"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_rx_a, bus.cmd.mrx_wire_data_a, None)
        return self._sendCmdToPort(l_cmd)

    def _sfrxWireDataD(self, p_data):
        l_cmdstr="mrx twire Data D"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.mosf_rx_b, bus.cmd.mrx_wire_data_b, None)
        return self._sendCmdToPort(l_cmd)

    def _encodeTriggerSettings(self, p_sets):
        """
        RECORD_RICHIESTA "COMANDO"=0x66 Campo "DATI" Trigger_Setting:
        ch1 30h..39h  Decine us	Trigger latency*jitter1 (Manta G-1236C default 96 us)
        ch2 30h..39h  Unità us   "     "  
        ch3 30h..39h  Decine us	exposure time           (Manta G-1236C default 42 us) 
        ch4 30h..39h  Unità us    
        """
        try:
            l_latency = p_sets[bus.data_key.trig_latency]
            l_exposure = p_sets[bus.data_key.trig_exposure]
            l_encoded = [
                l_latency // 10,
                l_latency % 10,
                l_exposure // 10,
                l_exposure % 10
            ]
        except KeyError as e:
            self.m_logger.error('Key error {}'.format(e))
            l_encoded= [0] * 4
        except Exception as e:
            self.m_logger.error('Unexpected error {}'.format(e))
            l_encoded= [0] * 4
        l_encoded= [bus.binary.decimal_zero + x for x in l_encoded]
        return l_encoded

    def _trigVerP(self, p_data):
        l_cmdstr="trigger ver P"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_a, bus.cmd.trig_ver_a, None)
        return self._sendCmdToPort(l_cmd)

    def _trigVerD(self, p_data):
        l_cmdstr="trigger ver D"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_b, bus.cmd.trig_ver_b, None)
        return self._sendCmdToPort(l_cmd)

    def _triggerSettingP(self, p_data):
        l_cmdstr="trigger setting P"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= self._encodeTriggerSettings(p_data)
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_a, bus.cmd.trig_setting_a, l_data)
        return self._sendCmdToPort(l_cmd)

    def _triggerSettingD(self, p_data):
        l_cmdstr="trigger setting D"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= self._encodeTriggerSettings(p_data)
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_b, bus.cmd.trig_setting_b, l_data)
        return self._sendCmdToPort(l_cmd)

    def _triggerOnOffP(self, p_data):
        """ 
        RECORD_RICHIESTA "COMANDO"=0x67 Campo "DATI" Trigger_On_Off: 
        ch1 30h..3Fh riserva
        ch2 30h..3Fh riserva
        ch3 30h..3Fh bit0=0 Trigger_Off   ;  bit0=1 Trigger_On        
        ch4 30h..3Fh riserva
        """
        l_cmdstr="trigger on off P"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= b'0000' if p_data == general.status_off else b'0030'
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_a, bus.cmd.trig_on_off_a, l_data)
        return self._sendCmdToPort(l_cmd)

    def _triggerOnOffD(self, p_data):
        l_cmdstr="trigger on off  D"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= b'0000' if p_data == general.status_off else b'0030'
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_b, bus.cmd.trig_on_off_b, l_data)
        return self._sendCmdToPort(l_cmd)

    def _triggerClickP(self, p_data):
        """ 
        RECORD_RICHIESTA "COMANDO"=0x68 Campo "DATI" Trigger_Scatto:
        ch1 30h..3Fh riserva
        ch2 30h..3Fh riserva
        ch3 30h..3Fh bit0=0 Trigger_Off   ;  bit0=1 Trigger_On        
        ch4 30h..3Fh riserva
        """
        l_cmdstr="trigger Click P"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= b'0000'
        if p_data == general.status_on: l_data=b'0010'
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_a, bus.cmd.trig_click_a, l_data)
        return self._sendCmdToPort(l_cmd)

    def _triggerClickD(self, p_data):
        l_cmdstr="trigger Click D"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= b'0000'
        if p_data == general.status_on: l_data=b'0010'
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_b, bus.cmd.trig_click_b, l_data)
        return self._sendCmdToPort(l_cmd)

    def _triggerStatusP(self, p_data):
        l_cmdstr="trigger Status P"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_a, bus.cmd.trig_status_a, None)
        return self._sendCmdToPort(l_cmd)

    def _triggerStatusD(self, p_data):
        l_cmdstr="trigger status D"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.trigger_b, bus.cmd.trig_status_b, None)
        return self._sendCmdToPort(l_cmd)

    # Modulo I/O

    def _ioVer(self, p_data):
        l_cmdstr="IO ver"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.io, bus.cmd.io_ver, None)
        return self._sendCmdToPort(l_cmd)

    def _ioTestBatt(self, p_data):
        """
        RECORD_RICHIESTA "COMANDO"0x6A  Campo "DATI" I_O_TestBatt (per stato batt.vedi "COMANDO"=0x6B);
        ch1 30h..3Fh riserva
        ch2 30h..3Fh riserva
        ch3 30h..3Fh bit0=0 TestBatt_Off   ;  bit0=1 TestBatt_On        
        ch4 30h..3Fh riserva
        """
        l_cmdstr="io test battery"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_data= b'0000'
        if p_data == general.status_on: l_data=b'0010'
        l_cmd= self.m_grammar.buildCommand(bus.module.io, bus.cmd.io_test_batt, l_data)
        return self._sendCmdToPort(l_cmd)

    def _ioStatus(self, p_data):
        l_cmdstr="io status"
        self.m_logger.debug("cmd " + l_cmdstr)
        l_cmd= self.m_grammar.buildCommand(bus.module.io, bus.cmd.io, None)
        return self._sendCmdToPort(l_cmd)

    " HELPER "

    def _sendCmdToPort(self, l_cmd):
        """ Invio msg in serial port con controllo errori """
        self.m_logger.info("Sending msg :" + helper.format_bytearray(l_cmd))
        if not len(l_cmd):
            l_err= "Empty command!"
            self.m_logger.error(l_err)
            self.m_errorList.append(l_err)
            return False
        try:
            self.m_port.write(l_cmd)
        except Exception as e:
            l_excp= "Exception writing command on serial port " + str(e) + \
                    " [command]: " + str(l_cmd)
            self.m_errorList.append(l_excp)
            return False
        return True

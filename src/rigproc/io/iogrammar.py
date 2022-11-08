#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grammatica protocollo io
"""

from rigproc.params import bus

class IoGrammar():
    """
    Gestione grammatica protocolloe
    """
    
    def __init__(self, p_logger):
        """
        Init elementi gramatica
        """
        self.m_logger= p_logger
        self.m_players={
            bus.module.videoserver: bus.addr.videoserver,
            bus.module.io: bus.addr.io,
            bus.module.mosf_tx_a: bus.addr.mtx_a,
            bus.module.mosf_tx_b: bus.addr.mtx_b,
            bus.module.mosf_rx_a: bus.addr.mrx_a,
            bus.module.mosf_rx_b: bus.addr.mrx_b,
            bus.module.trigger_a: bus.addr.trig_a,
            bus.module.trigger_b: bus.addr.trig_b,
            }

        self.m_fieldsPos={
                'stx':0,
                'src':1,
                'dst':2,
                'io_cmd':3,
                'data':4
            }

        self.m_struct={
            'stx': {
                'fixed_size':True,
                'size':1,
                'values':{
                    'value':2
                    }
                },
            'source':{
                'fixed_size':True,
                'size':1,
                'values': self.m_players
                },
            'dest':{
                'fixed_size':True,
                'size':1,
                'values': self.m_players
                },
            'io_cmd':{
                'fixed_size':True,
                'size':1,
                'values':{
                    'value':bus.cmd_codes
                    }
                },
            'data':{
                'fixed_size':False,
                'size_max':512
                },
            'data_len': {
                'fixed_size':True,
                'size':1,
                'values':bus.data_len
                },
            'crc': {
                'fixed_size':True,
                'size':1,
                'values':{}
                },
            'endx': {
                'fixed_size':True,
                'size':3,
                'values':{
                    'value':[3,13,10]
                    }
                }
            }
        self.m_commands={
            bus.cmd.mtx_ver_a:{
                'code': bus.cmd_codes[bus.cmd.mtx_ver_a],
                'size': 1
                },
            bus.cmd.mtx_ver_b:{
                'code': bus.cmd_codes[bus.cmd.mtx_ver_a],
                'size': 1
                },
            bus.cmd.mtx_vel_a:{
                'code': bus.cmd_codes[bus.cmd.mtx_vel_a],
                'size': 1
                },
            bus.cmd.mtx_vel_b:{
                'code': bus.cmd_codes[bus.cmd.mtx_vel_b],
                'size': 1
                },
            bus.cmd.mtx_on_off_a:{
                'code': bus.cmd_codes[bus.cmd.mtx_on_off_a],
                'size': 1
                },
            bus.cmd.mtx_on_off_b:{
                'code': bus.cmd_codes[bus.cmd.mtx_on_off_b],
                'size': 1
                },
            bus.cmd.mrx_ver_a:{
                'code': bus.cmd_codes[bus.cmd.mrx_ver_a],
                'size': 1
                },
            bus.cmd.mrx_ver_b:{
                'code': bus.cmd_codes[bus.cmd.mrx_ver_b],
                'size': 1
                },
            bus.cmd.mrx_tmos_a:{
                'code': bus.cmd_codes[bus.cmd.mrx_tmos_a],
                'size': 1
                },
            bus.cmd.mrx_tmos_b:{
                'code': bus.cmd_codes[bus.cmd.mrx_tmos_b],
                'size': 1
                },
            bus.cmd.mrx_wire_t0_a:{
                'code': bus.cmd_codes[bus.cmd.mrx_wire_t0_a],
                'size': 1
                },
            bus.cmd.mrx_wire_t0_b:{
                'code': bus.cmd_codes[bus.cmd.mrx_wire_t0_b],
                'size': 1
                },
            bus.cmd.mrx_wire_data_a:{
                'code': bus.cmd_codes[bus.cmd.mrx_wire_data_a],
                'size': 1
                },
            bus.cmd.mrx_wire_data_b:{
                'code': bus.cmd_codes[bus.cmd.mrx_wire_data_b],
                'size': 1
                },
            bus.cmd.trig_ver_a:{
                'code': bus.cmd_codes[bus.cmd.trig_ver_a],
                'size': 1
                },
            bus.cmd.trig_ver_b:{
                'code': bus.cmd_codes[bus.cmd.trig_ver_b],
                'size': 1
                },
            bus.cmd.trig_setting_a:{
                'code': bus.cmd_codes[bus.cmd.trig_setting_a],
                'size': 1
                },
            bus.cmd.trig_setting_b:{
                'code': bus.cmd_codes[bus.cmd.trig_setting_b],
                'size': 1
                },
            bus.cmd.trig_on_off_a:{
                'code': bus.cmd_codes[bus.cmd.trig_on_off_a],
                'size': 1
                },
            bus.cmd.trig_on_off_b:{
                'code': bus.cmd_codes[bus.cmd.trig_on_off_b],
                'size': 1
                },
            bus.cmd.trig_click_a:{
                'code': bus.cmd_codes[bus.cmd.trig_click_a],
                'size': 1
                },
            bus.cmd.trig_click_b:{
                'code': bus.cmd_codes[bus.cmd.trig_click_b],
                'size': 1
                },
            bus.cmd.trig_status_a:{
                'code': bus.cmd_codes[bus.cmd.trig_status_a],
                'size': 1
                },
            bus.cmd.trig_status_b:{
                'code': bus.cmd_codes[bus.cmd.trig_status_b],
                'size': 1
                },
            bus.cmd.io_ver:{
                'code': bus.cmd_codes[bus.cmd.io_ver],
                'size': 1
                },
            bus.cmd.io_test_batt:{
                'code': bus.cmd_codes[bus.cmd.io_test_batt],
                'size': 1
                },
            bus.cmd.io:{
                'code': bus.cmd_codes[bus.cmd.io],
                'size': 1
                }
            }
        self.m_data={
            bus.cmd.mtx_ver_a:{
                'data': [48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mtx_ver_b:{
                'data': [48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mtx_vel_a:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mtx_vel_b:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mtx_on_off_a:{
                'data':[48,48,48,48], # @todo campo dati come lo riempio ?
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mtx_on_off_b:{
                'data':[48,48,48,48], # @todo campo dati come lo riempio ?
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mrx_ver_a:{
                'data': [48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mrx_ver_b:{
                'data': [48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mrx_tmos_a:{
                'data':[48,48,48,48], # riempire in fase di richiesta
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mrx_tmos_b:{
                'data':[48,48,48,48], # riempire in fase di richiesta
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mrx_wire_t0_a:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mrx_wire_t0_b:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mrx_wire_data_a:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.mrx_wire_data_b:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_ver_a:{
                'data': [48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_ver_b:{
                'data': [48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_setting_a:{
                'data':[48,48,48,48], #riempire in fase di richiesta
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_setting_b:{
                'data':[48,48,48,48], #riempire in fase di richiesta
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_on_off_a:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_on_off_b:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_click_a:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_click_b:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_status_a:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.trig_status_b:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.io_ver:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.io_test_batt:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            bus.cmd.io:{
                'data':[48,48,48,48],
                'size': 4,
                'size_code': bus.data_len[4]
                },
            }
  
    """ --- BUILD COMMANDS --- """      
    
    def buildCommand(self, p_dest, p_cmd, p_data):
        """
        Comando build byte array

        Parameters
        ----------
        p_dest : string
            codice destinatario.
        p_cmd : string
            codice comando.
        p_data : list
            n byte list con i dati per il comando

        Returns
        -------
        byte array da inviare sul bus
        """
        l_msg= bytearray()
        l_start= self._start(p_dest)
        if not len(l_start): return bytearray()
        l_msg.extend(l_start)
        l_cmd= self._command(p_cmd)
        if not len(l_cmd): return bytearray()
        l_msg.extend(l_cmd)
        l_data=self._data(p_cmd)
        if not len(l_data): return bytearray()
        " data filling "
        if p_data != None:
            l_data= bytearray(p_data)
        l_msg.extend(l_data)
        l_cmdSize =self._dataSize(p_cmd)
        if not l_cmdSize: return bytearray()
        l_msg.extend(l_cmdSize)
        " inserimento vero crc "
        l_crc =self._crc(l_msg, tx= True)
        if not l_crc: return bytearray()
        l_msg.append(l_crc)
        " chiusura"
        l_close = self._close()
        if not len(l_close): return bytearray()
        l_msg.extend(l_close)
        return l_msg


    def _command(self, p_command):
        """
        Creazione campi in base al comando
        
        Returns
        -------
        comando + lunghezza comando
        """
        l_msg= bytearray()
        try:
            l_msg.append(ord(self.m_commands[p_command]['code']))
        except KeyError as e:
            self.m_logger.error("Error with key: " + str(e))
            return bytearray()
        return l_msg 

    def _data(self, p_command):
        """
        Creazione campo dati in base al comando
        
        Returns
        -------
        comando + lunghezza comando
        """
        l_msg= bytearray()
        try:
            l_msg.extend(self.m_data[p_command]['data'])
        except KeyError as e:
            self.m_logger.error("Error with key: " + str(e))
            return bytearray()
        return l_msg

    def _dataSize(self, p_command):
        """
        Creazione campo lunghezza record dati
        
        Returns
        -------
        comando + lunghezza comando
        """
        l_msg= bytearray()
        try:            
            l_msg.append(ord(self.m_data[p_command]['size_code']))
        except KeyError as e:
            self.m_logger.error("Error with key: " + str(e))
            return bytearray()
        return l_msg 
                
    " ----- DECODING ----- "
  
    def findMsg(self, p_buf ):
        """
        Parsa un buffer e cerca i messaggi validi
        Svuota il buffer della parte decodificata di messaggio

        Parameters
        ----------
        p_buf : bytearray
            array messaggi

        Returns
        -------
        Lista di Tuple [(chi,cosa),(chi,cosa)..]

        """
        l_end= False
        l_data=[]
        while not l_end:
            l_pos = p_buf.find(self._close())
            if l_pos == -1: 
                l_end= True
                break
            #pdb.set_trace()
            " decodifico meno la chiusura "
            l_decodedMsg= self._decode(p_buf[0:l_pos])
            " il find trova la prima occorrenza quindi devo passare oltre"
            " posso cancellare il msg se lo decodifico correttamente"
            " posso lasciarlo nel caso di messaggio ricevuto a chunk"
            " se decode fallsice cancello il msg non decodificato"
            if l_decodedMsg:                
                #pdb.set_trace()
                l_start= l_decodedMsg['pos']                            
                l_data.append(l_decodedMsg) 
                #pdb.set_trace()                
                del p_buf[l_pos - l_start: l_pos+ len(self._close())]
            else:
                del p_buf[0:l_pos + len(self._close())]                    
        return l_data
    
    def _decode(self, p_buf):
        """
        Decodifica il potenziale messaggio      
        verifica dimensione del record dati
        a seguire src dest 
        
        Parameters
        ----------
        p_buf : bytearray
            potenziale messaggio
        
        Returns
        -------
        dizionario (mittente,dati,pos dato iniziale) 
        'pos' è la posizione all'interno del buffer intero nella
        quale si trova il carattere di start del messaggio trovato
        
        """            
        "Verifica dimensionale"
        " è una posizione dalla fine da operare con il -"
        l_posStx= self._checkRecordsize(p_buf)
        if not l_posStx:
            return {}
        " crc, posizione  -1 dal p_buf (senza chiusura) "
        l_msg= p_buf[-l_posStx:]
        l_crc= p_buf[-1]
        l_calc= self._crc(l_msg)
        if l_crc != l_calc:
            self.m_logger.error(f'CRC actual/expected: {l_crc}/{l_calc}. Message: {l_msg}')
            return {}
        " src, dest"
        l_info= self._getData(l_msg)
        l_info['pos']= l_posStx  
        l_info['msg']=l_msg
        l_info['msg'].extend(self._close())
        return l_info.copy()
            
    " ----- HELPER ----- "

    def _start(self,p_dest):
        """
        crea i primi byte del msg che parte da me
        
        Parameters
        ----------
        p_dest : string
            codice destinatario.
            
        Returns
        -------
        stx+mittente+dest

        """
        l_msg= bytearray()
        try:
            l_msg.append(self.m_struct['stx']['values']['value'])
            l_msg.append(ord(self.m_struct['source']['values'][bus.module.videoserver]))
            l_msg.append(ord(self.m_struct['dest']['values'][p_dest]))
        except KeyError as e:
            self.m_logger.error("Error with key: " + str(e))
            return bytearray()
        return l_msg    
    
    
    def _crc(self, p_msg, tx= False):
        """
        Calcolo crc src+dest+data+datalen
        Su messaggeio completo meno chiusura
        
        Parameters
        ----------
        p_msg :  bytearray
            msg su cui eseguire il crc

        Returns
        -------
        dato crc 

        """
        l_sum=0
        if tx:
            for l_el in p_msg[1:]:
                l_sum = l_sum + l_el
        else:
            for l_el in p_msg[1:-1]:
                l_sum = l_sum + l_el
        l_sum = l_sum & 0xff
        l_sum = l_sum | 0x80
        return l_sum
    
    def _close(self):
        """
        chisurua msg
            
        Returns
        -------
        stingha di chiusura

        """
        l_msg= bytearray()
        try:
            l_msg.extend(self.m_struct['endx']['values']['value'])                
        except KeyError as e:
            self.m_logger.error("Error with key: " + str(e))
            return bytearray()
        return l_msg

    def _checkRecordsize(self,p_buf):
        """

        Verifica se la dim del record è coerente
        Vede se con il record size fornito
        trova start char al posto giusto
        Se trovo chunk di messaggio di lunghezza inferiore all'attesa esco
        
        Parameters
        ----------        
        p_buf :  bytearray
            buffer msg escluso di closing chars

        Returns
        -------
        0 non trovato, altrimenti indice di slice relativo aquesto buf

        """
        l_stx= self.m_struct['stx']['size']
        l_srcDest= 2*self.m_struct['dest']['size']
        l_cmdSize= self.m_struct['io_cmd']['size']
        l_recSize= self.m_struct['data_len']['size']
        l_crcSize= self.m_struct['crc']['size']
        if len(p_buf) < 2: return 0
        l_recLen= self._getDictKey(self.m_struct['data_len']['values'], chr(p_buf[-2]))
        if l_recLen == None:
            self.m_logger.error("Campo dimensione record con valore sconosciuto")
            return 0
        l_len= l_stx+ l_srcDest + l_cmdSize + l_recLen + l_recSize + l_crcSize        
        
        " Verifico che stx sia al posto giusto "
        if len(p_buf) < l_len: return 0

        # Ignoro il carattere stx iniziale: questo carattere è facilemente
        # disturbato e non viene considerato nel calcolo del crc
        l_expected_stx = self.m_struct['stx']['values']['value']
        if p_buf[-l_len] != l_expected_stx:
            self.m_logger.warning(
                f'Byte iniziale errato. Atteso: {l_expected_stx}. Trovato: {p_buf[-l_len]}. Ignoro...'
            )
        
        return l_len
               
    def _getData(self,p_buf):
        """
        Verifica campi ammissimibli src dest
        Il buffer msg qui inizia con stx

        Parameters
        ----------
        p_buf : bytearray
            buffer meno la chisura 
        Returns
        -------
        {
            valid:
            src:
            dest:
            cmd:
            data:
        }

        """
        l_out={}
        l_out['valid']= True
        l_out['src']= chr(p_buf[self.m_fieldsPos['src']])
        l_out['dest']=  chr(p_buf[self.m_fieldsPos['dst']])
        " src, verifica e conversione nome "
        if not l_out['src'] in self.m_players.values():
            self.m_logger.error("Invalid src")
            l_out['valid']= False
        else:
            l_out['src']= self._getDictKey(self.m_players, l_out['src'])
        " dest, verifica e conversione nome "
        if not l_out['dest'] in self.m_players.values():                
            self.m_logger.error("Invalid dest")    
            l_out['valid']= False
            return l_out
        else:
            l_out['dest']= self._getDictKey(self.m_players, l_out['dest'])
        " data field "
        l_dataLen= self._getDictKey(self.m_struct['data_len']['values'],
                                   chr(p_buf[-2]))
        if l_dataLen == None:
            l_out['valid']= False
            self.m_logger.error("Invalid data len")
            return l_out
        l_cmd= chr(p_buf[self.m_fieldsPos['io_cmd']])
        l_out['io_cmd']= self._findCommand(l_out['src'], l_cmd)
        l_out['data_size']= l_dataLen
        l_out['data']= list(p_buf[self.m_fieldsPos['data']: self.m_fieldsPos['data'] + l_dataLen])
        return l_out
                                        
    def _getDictKey(self,p_dict, p_value):
        """
        preleva il nome di src dest dal value

        Parameters
        ----------
        p_value : int
            value sr dst

        Returns
        -------
        nome src dest

        """
        for key, value in p_dict.items(): 
            if p_value == value: 
                return key
        return None

    def _findCommand(self, p_src, p_cmd):
        """Trova il comando in funzione anche del sender """
        self.m_logger.debug("finding command from answ: " + p_src + " "+ str(p_cmd))
        try:
            for cmd in bus.cmd_codes_reverted[p_src].keys():
                if cmd == str(p_cmd):
                    self.m_logger.debug(cmd)
                    self.m_logger.debug(bus.cmd_codes_reverted[p_src][str(p_cmd)])
                    return bus.cmd_codes_reverted[p_src][str(p_cmd)]
        except:
            pass
        return ''
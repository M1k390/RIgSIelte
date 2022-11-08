#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
traduzioen risposte protocollo io
"""

from logging import Logger
from typing import Tuple

from rigproc.params import bus, general
from rigproc.commons.helper import helper

class IOAnswers():
    """
    Helper traduttore risposte
    """
    
    def __init__(self, p_logger: Logger):
        self.m_logger= p_logger
        " Assegni il decoder delle rispsote"
        self.m_answerType={
            # MOSF TX A
            bus.module.mosf_tx_a : { # Prr A, pari P
               bus.cmd.mtx_ver_a: {
                            'decode': self._getMTXp_ver,
                            'io_cmd':bus.cmd.mtx_ver_a
                    },
                bus.cmd.mtx_vel_a:{
                            'decode': self._getMTXp_vel,
                            'io_cmd':bus.cmd.mtx_vel_a
                    },
                bus.cmd.mtx_on_off_a: {
                            'decode': self._getMTXp_onoff,
                            'io_cmd':bus.cmd.mtx_on_off_a
                    },
                },
            # MOSF RX A
            bus.module.mosf_rx_a:{
                bus.cmd.mrx_ver_a: {
                            'decode': self._getMRXp_ver,
                            'io_cmd':bus.cmd.mrx_ver_a
                    },
                bus.cmd.mrx_tmos_a: {
                            'decode': self._getMRXp_tmosf,
                            'io_cmd':bus.cmd.mrx_tmos_a
                    },
                bus.cmd.mrx_wire_t0_a: { # MOSF_RX_Altezza
                            'decode': self._getMRXp_wire_t0,
                            'io_cmd':bus.cmd.mrx_wire_t0_a
                    },
                bus.cmd.mrx_wire_data_a: {
                            'decode': self._getMRXp_wire_data, # MOSF_RX_DatiGrafico
                            'io_cmd':bus.cmd.mrx_wire_data_a
                    },
                },
            # TRIGGER A
            bus.module.trigger_a:{
                bus.cmd.trig_ver_a: {
                            'decode': self._getTrigp_ver,
                            'io_cmd':bus.cmd.trig_ver_a
                    },
                bus.cmd.trig_setting_a: {
                            'decode': self._getTrigp_settings,
                            'io_cmd':bus.cmd.trig_setting_a
                    },
                bus.cmd.trig_on_off_a: {
                            'decode': self._getTrigp_on_off,
                            'io_cmd':bus.cmd.trig_on_off_a
                    },
                bus.cmd.trig_click_a: {
                            'decode': self._getTrigp_click,
                            'io_cmd':bus.cmd.trig_click_a
                    },
                bus.cmd.trig_status_a: {
                            'decode': self._getTrigp_status,
                            'io_cmd':bus.cmd.trig_status_a
                    },
                },
            # MOSF TX B
            bus.module.mosf_tx_b:{ # Prr B, dispari D
                bus.cmd.mtx_ver_b: {
                            'decode': self._getMTXd_ver,
                            'io_cmd':bus.cmd.mtx_ver_b
                    },
                bus.cmd.mtx_vel_b: {
                            'decode': self._getMTXd_vel,
                            'io_cmd':bus.cmd.mtx_vel_b
                    },
                bus.cmd.mtx_on_off_b: {
                            'decode': self._getMTXd_onoff,
                            'io_cmd':bus.cmd.mtx_on_off_b
                    },
                },
            # MOSF RX B
            bus.module.mosf_rx_b:{
                bus.cmd.mrx_ver_b: {
                            'decode': self._getMRXd_ver,
                            'io_cmd':bus.cmd.mrx_ver_b
                    },
                bus.cmd.mrx_tmos_b: {
                            'decode': self._getMRXd_tmosf,
                            'io_cmd':bus.cmd.mrx_tmos_b
                    },
                bus.cmd.mrx_wire_t0_b: { # MOSF_RX_Altezza
                            'decode': self._getMRXd_wire_t0,
                            'io_cmd':bus.cmd.mrx_wire_t0_b
                    },
                bus.cmd.mrx_wire_data_b: { # MOSF_RX_DatiGrafico
                            'decode': self._getMRXd_wire_data,
                            'io_cmd':bus.cmd.mrx_wire_data_b
                    },
                },
            # TRIGGER B
            bus.module.trigger_b:{
                bus.cmd.trig_ver_b: {
                            'decode': self._getTrigd_ver,
                            'io_cmd':bus.cmd.trig_ver_b
                    },
                bus.cmd.trig_setting_b: {
                            'decode': self._getTrigd_settings,
                            'io_cmd':bus.cmd.trig_setting_b
                    },
                bus.cmd.trig_on_off_b: {
                            'decode': self._getTrigd_on_off,
                            'io_cmd':bus.cmd.trig_on_off_b
                    },
                bus.cmd.trig_click_b: {
                            'decode': self._getTrigd_click,
                            'io_cmd':bus.cmd.trig_click_b
                    },
                bus.cmd.trig_status_b: {
                            'decode': self._getTrigp_status,
                            'io_cmd':bus.cmd.trig_status_b
                    },
                },
            # I/O
             bus.module.io:{ # IO
               bus.cmd.io_ver: {
                            'decode': self._getIO_ver,
                            'io_cmd':bus.cmd.io_ver
                    },
                bus.cmd.io_test_batt: {
                            'decode': self._getIOTestBattery,
                            'io_cmd':bus.cmd.io_test_batt
                    },
                bus.cmd.io: { # I/O Allarmi
                            'decode': self._getIOStatus,
                            'io_cmd':bus.cmd.io
                    },
                }
            }
        self.m_answerExp={
            
            }        

    def getKeyValue(self, p_sender, p_cmd, p_data):
        """
        legge la risposta e ritorna key - value 
        le risposte nel campo dati riportano 
        "richiesta"[4byte] "dati"[n-bytes]

        Parameters
        ----------
        p_sender : byte
            indirizzo mittente
        p_cmd : byte
            comando a cui si sta rispondendo
        p_cmd : bytearray
            campo dati del msg            

        Returns
        -------
        richiesta, valore campo dati
        """
        l_ansToWhat=''
        l_data=''
        #self.m_logger.debug("{}-{}-{}".format(p_sender, p_cmd, p_data))
        if p_cmd in self.m_answerType[p_sender].keys():
            l_data= self.m_answerType[p_sender][p_cmd]['decode'](p_data)
            l_ansToWhat= self.m_answerType[p_sender][p_cmd]['io_cmd']
        return l_ansToWhat, l_data


    " ---- DECODING ---- "

    def _todecimal(self, *p_chs):
        """
        converte una serie di caratteri binari in un numero supponendo si tratti di centinaia, decine, unità
        (argomenti dal più grande al più piccolo)
        suppone che i valori si trovino tra un minimo (0x30 - corrispondente a 0) e un massimo (0x39), altrimenti ritorna "dato errato"
        """
        decimal = 0
        coeff = 1
        try:
            for p_ch in reversed(p_chs):
                if p_ch in range(bus.binary.decimal_zero, bus.binary.decimal_max + 1):
                    decimal += (p_ch - bus.binary.decimal_zero) * coeff
                    coeff *= 10
                else:
                    self.m_logger.error(f'Decimal value out of range: {p_ch}')
                    return general.dato_errato
        except Exception as e:
            self.m_logger.error(f'Unexpected error converting bytes to decimal number ({type(e)}): {e}')
            return general.dato_errato
        return decimal

    def _to_date(self, p_year_ch, p_month_ch, p_day_ch):
        l_year = bus.binary.year_offset
        l_month = 1
        l_day = 1

        # Parse year
        try:
            if p_year_ch in range(bus.binary.year_zero, bus.binary.year_max + 1):
                l_year = bus.binary.year_offset + (p_year_ch - bus.binary.year_zero)
            else:
                self.m_logger.error(f'Year out of range: {p_year_ch}')
                return general.dato_errato
        except Exception as e:
            self.m_logger.error(f'Unexpected error converting bytes to date ({type(e)}): {e}')
            return general.dato_errato

        # Parse month
        try:
            if p_month_ch in range(bus.binary.month_one, bus.binary.month_max + 1):
                l_month = p_month_ch - bus.binary.month_one + 1
            else:
                self.m_logger.error(f'Month out of range: {p_month_ch}')
                return general.dato_errato
        except Exception as e:
            self.m_logger.error(f'Unexpected error converting bytes to date ({type(e)}): {e}')
            return general.dato_errato

        # Parse day
        try:
            if p_day_ch in range(bus.binary.day_one, bus.binary.day_max + 1):
                l_day = p_day_ch - bus.binary.day_one + 1
            else:
                self.m_logger.error(f'Day out of range: {p_day_ch}')
                return general.dato_errato
        except Exception as e:
            self.m_logger.error(f'Unexpected error converting bytes to date ({type(e)}): {e}')
            return general.dato_errato

        l_date_f = helper.int_date_to_str(l_year, l_month, l_day)
        if l_date_f is not None:
            return l_date_f
        else:
            return general.dato_errato

    def _getMTXp_ver(self, p_data):
        """
        RECORD_RISPOSTA "COMANDO"=0x60 Campo "DATI" MOSF_TX_Versione:
        ch1 30h..4Fh day 0x31..4F 0x31=Day 01.....0x4F=Day 31 (0123456789:;<=>?@ABCDEFGHIJKLMNO) Ascii
        ch2 30h..3Ch month 0x31..3C 0x31=gennaio..0x3C=DICEMBRE (0123456789:;<)
        ch3 30h..39h year 0x30..39 0x30=2020.....0x39=2029 (0123456789)
        ch4 30h..3Fh Stato On,Off
                     bit0=0 Led IF Off bit0=1 Led IF On
        Il quarto byte viene ignorato (ex riserva)
        """
        l_out={}
        l_out[bus.data_key.mtx_vers]= self._to_date(
            p_year_ch=p_data[2],
            p_month_ch=p_data[1],
            p_day_ch=p_data[0]
        )
        return l_out

    def _getMTXd_ver(self, p_data):
        """
        vedi _getMTXp_ver
        """
        return self._getMTXp_ver(p_data)

    def _getMTXp_vel(self, p_data):
        """
        RECORD_RISPOSTA "COMANDO"0x61 Campo "DATI" MOSF_TX_Velocita/Allarm1: 
        ch1VelCent 	30h..39h  VelCentinaia Kmh    
        ch2VelDeci	30h..39h  VelDecine    Kmh    
        ch3VelUnit 	30h..39h  VelUnità     Kmh    
        Ch4VelEvent 
                    30h=DirezioneTreno PARI    Treno senza Pant.(ch1,ch2,ch3=Kmh) (AttesaEventodalModuloTrigger)           
                    31h=DirezioneTreno DISPARI Treno senza Pant.(ch1,ch2,ch3=Kmh) (AttesaEventodalModuloTrigger)
                    32h=DirezioneTreno PARI    Treno con   Pant.(ch1,ch2,ch3=Kmh) (OkEventodalModuloTrigger)
                    33h=DirezioneTreno DISPARI Treno con   Pant.(ch1,ch2,ch3=Kmh) (OkEventodalModuloTrigger)  
                    3Fh=stato attesa treno          (ch1,ch2,ch3=0)
                    40h=errore Rimbalzo  1          (ch1,ch2,ch3=0) 
                    41h=errore Rimbalzo  2,         (ch1,ch2,ch3=0)
                    42h=errore Velocità0 > 470 kmh  (ch1,ch2,ch3=0)
                    43h=errore Velocità1 > 470 kmh  (ch1,ch2,ch3=0)                         
                    44h=errore Velocità0 <   7 kmh  (ch1,ch2,ch3=0)
                    45h=errore Velocità1 <   7 kmh  (ch1,ch2,ch3=0)
                    46h=;errore Trigger0            (ch1,ch2,ch3=0) (Pant.SenzaTreno DirezioneTreno PARI)
                    47h=;errore Trigger1            (ch1,ch2,ch3=0) (Pant.SenzaTreno DirezioneTreno DISPARI)
                    48h=;errore SensoreVelocita1    (ch1,ch2,ch3=0)      
                    49h=;errore SensoreVelocita2    (ch1,ch2,ch3=0)  
                    4Ah=;errore SensoreVelocita1-2  (ch1,ch2,ch3=0)
        """
        l_out= {}
        l_event= {
            0x30: bus.mtx_event.attesa_trigger,
            0x31: bus.mtx_event.attesa_trigger,
            0x32: bus.mtx_event.ok_trigger,
            0x33: bus.mtx_event.ok_trigger,
            0x3f: bus.mtx_event.attesa_treno,
            0x40: bus.mtx_event.err_rimbalzo1,
            0x41: bus.mtx_event.err_rimbalzo2,
            0x42: bus.mtx_event.err_vel0_high,
            0x43: bus.mtx_event.err_vel1_high,
            0x44: bus.mtx_event.err_vel0_low,
            0x45: bus.mtx_event.err_vel1_low,
            0x46: bus.mtx_event.err_trigger0,
            0x47: bus.mtx_event.err_trigger1,
            0x48: bus.mtx_event.err_sens_vel1,
            0x49: bus.mtx_event.err_sens_vel2,
            0x4a: bus.mtx_event.err_sens_vel1_2
        }
        l_dire= {
            0x30: general.binario.pari,
            0x31: general.binario.dispari,
            0x32: general.binario.pari,
            0x33: general.binario.dispari
        }

        if p_data[3] in [0x30, 0x31, 0x32, 0x33, 0x3f]: # conosco velocità (attuale o passata)
            l_out[bus.data_key.mtx_velo]= self._todecimal(p_data[0], p_data[1], p_data[2])
        else:
            l_out[bus.data_key.mtx_velo]= 0

        if p_data[3] in [0x30, 0x31, 0x32, 0x33]: # conosco direzione
            try:
                l_out[bus.data_key.mtx_direction]= l_dire[p_data[3]]
            except KeyError as e:
                self.m_logger.error("Bad value {}: {}. Allowed keys: {}".format(p_data[3], e, ', '.join(l_dire.keys())))
                l_out[bus.data_key.mtx_direction]= general.dato_errato
        else:
            l_out[bus.data_key.mtx_direction]= general.dato_non_disp
        
        try:
            l_out[bus.data_key.mtx_event]= l_event[p_data[3]]
        except KeyError as e:
            self.m_logger.error("Bad value {}: {}. Allowed keys: {}".format(p_data[3], e, ', '.join(l_event.keys())))
            l_out[bus.data_key.mtx_event]= general.dato_errato
        return l_out

    def _getMTXd_vel(self, p_data):
        """
        vedi _getMTXp_vel
        """
        return self._getMTXp_vel(p_data)

    def _getMTXp_onoff(self, p_data):
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
        l_out={}
        if p_data[2]:
            l_out[bus.data_key.mtx_onoff]= general.status_on
        else:
            l_out[bus.data_key.mtx_onoff]= general.status_off
        return l_out

    def _getMTXd_onoff(self, p_data):
        """
        vedi _getMTXp_onoff
        """
        return self._getMTXp_onoff(p_data)

    def _getMRXp_ver(self, p_data):
        """
        RECORD_RISPOSTA "COMANDO"=0x60 Campo "DATI" MOSF_RX_Versione:
        ch1 30h..4Fh day 0x31..4F 0x31=Day 01.....0x4F=Day 31 (0123456789:;<=>?@ABCDEFGHIJKLMNO) Ascii
        ch2 30h..3Ch month 0x31..3C 0x31=gennaio..0x3C=DICEMBRE (0123456789:;<)
        ch3 30h..39h year 0x30..39 0x30=2020.....0x39=2029 (0123456789)
        ch4 30h..3Fh Riserva
        """
        l_out={}
        l_out[bus.data_key.mrx_vers]= self._to_date(
            p_year_ch=p_data[2],
            p_month_ch=p_data[1],
            p_day_ch=p_data[0]
        )
        return l_out

    def _getMRXd_ver(self, p_data):
        """
        vedi _getMRXp_ver
        """
        return self._getMRXp_ver(p_data)

    def _getMRXp_tmosf(self, p_data):
        """
        RECORD_RISPOSTA/RICHIESTA "COMANDO"=0x63 Campo "DATI" MOSF_RX_TMOS: 
        ch1,ch2 Tempo TMOSF prima Evento Pantografo Valore Max 25" (valore default 25")
        ch3,cha Tempo TMOSF dopo Evento Pantografo  Valore Max 25" (valore default 25")  
        """
        l_out={}

        #TODO verificare come sono rappresentati i dati

        # Decine, unità (0x30 - 0x39)
        l_pre= self._todecimal(p_data[0], p_data[1])
        l_post= self._todecimal(p_data[0], p_data[1])

        # 8 bit
        #l_pre= (p_data[0] << 4) + p_data[1]
        #l_post= (p_data[2] << 4) + p_data[3]

        if l_pre <= bus.mosf_data.max_pre_time:
            l_out[bus.data_key.mosf_tpre]= l_pre
        else:
            self.m_logger.error("Bad value {}: max allowed value = {}".format(l_pre, bus.mosf_data.max_pre_time))
            l_out[bus.data_key.mosf_tpre]= general.dato_errato
        if l_post <= bus.mosf_data.max_post_time:
            l_out[bus.data_key.mosf_tpost]= l_post
        else:
            self.m_logger.error("Bad value {}: max allowed value = {}".format(l_post, bus.mosf_data.max_post_time))
            l_out[bus.data_key.mosf_tpost]= general.dato_errato
        return l_out

    def _getMRXd_tmosf(self, p_data):
        """ 
        vedi _getMRXp_tmosf
        """
        return self._getMRXp_tmosf(p_data)

    def _getMRXp_wire_t0(self, p_data):
        """
        RECORD_RISPOSTA "COMANDO"=0x64 Campo "DATI" MOSF_RX_Altezza:                         
        ;ch1 30h        Riserva
        ;ch2 30h        Riserva
        ;ch3 20h..7F    ;*Posizione linea di contatto (96 pixel)
        Ch4             30h=DirezioneTreno PARI   Treno senza Pant.(ch3 20h..7F) (AttesaEventodalModuloTrigger)           
                        31h=DirezioneTreno DISPARI Treno senza Pant.(ch3 20h..7F) (AttesaEventodalModuloTrigger)
                        32h=DirezioneTreno PARI   Treno con   Pant.(ch3 20h..7F) (OkEventodalModuloTrigger)
                        33h=DirezioneTreno DISPARI Treno con   Pant.(ch3 20h..7F) (OkEventodalModuloTrigger)
                        3Fh=stato attesa treno/Pant.           (ch3 20h..7F) (posizione linea di contatto a riposo )
                        40h=errore MOSF_RX Allineamento OutAll    (ch3=20h posizione unavailable)
                        41h=errore MOSF_RX Allineamento OutHigh   (ch3=20h posizione unavailable)
                        42h=errore MOSF_RX Allineamento OutLow    (ch3=20h posizione unavailable)
                        43h=errore MOSF_RX Allineamento Unreliable(ch3=20h posizione unavailable)    		
        ;*ESEMPIO:con punto di Fulcro,come da schema "19-01-MOSF-RX-R0 pag7.pdf",
        ;        Il Fattore di intensificazione è di 1,46
        ;        e il livello di dettaglio (granularità) diventà 3,4mm Pixel
        """
        l_event= { # decoder eventi
            0x30: bus.mrx_event.attesa_trigger,
            0x31: bus.mrx_event.attesa_trigger,
            0x32: bus.mrx_event.ok_trigger,
            0x33: bus.mrx_event.ok_trigger,
            0x3f: bus.mrx_event.attesa_treno,
            0x40: bus.mrx_event.err_all_outall,
            0x41: bus.mrx_event.err_all_outhigh,
            0x42: bus.mrx_event.err_all_outlow,
            0x43: bus.mrx_event.err_all_unreliable
        }
        l_direction= { # decoder direzione treno
            0x30: general.binario.pari,
            0x31: general.binario.dispari,
            0x32: general.binario.pari,
            0x33: general.binario.dispari
        }
        l_t0_availables = [0x30, 0x31, 0x32, 0x33, 0x3f] # altezza disponibile solo per questi valori "evento"

        l_out={}

        if p_data[3] in l_t0_availables: # altezza filo disponibile
            try:
                if p_data[2] > bus.mosf_data.zero_value and \
                    p_data[2] <= bus.mosf_data.max_value:
                        l_out[bus.data_key.mosf_wire_t0]= p_data[2] - bus.mosf_data.zero_value   
                else:
                    l_out[bus.data_key.mosf_wire_t0]= general.dato_errato                
            except Exception as e:
                self.m_logger.error("Bad data {}: {}".format(p_data, e))
                l_out[bus.data_key.mosf_wire_t0]= general.dato_errato
        else:
            l_out[bus.data_key.mosf_wire_t0] = general.dato_non_disp
        
        if p_data[3] in l_direction.keys(): # direzione treno disponibile
            try:
                l_out[bus.data_key.mrx_direction]= l_direction[p_data[3]]
            except KeyError as e:
                l_out[bus.data_key.mrx_direction]= general.dato_errato
                self.m_logger.error('Bad value {}: {}. Allowed values: {}'.format(p_data[3], e, ', '.join(l_direction.keys())))
        else:
            l_out[bus.data_key.mrx_direction]= general.dato_non_disp

        try: # legge event 
            l_out[bus.data_key.mrx_event]= l_event[p_data[3]]
        except KeyError as e:
            self.m_logger.error('Bad value {}: {}. Allowed values: {}'.format(p_data[3], e, l_event.keys()))
            l_out[bus.data_key.mrx_event]= general.dato_errato

        return l_out

    def _getMRXd_wire_t0(self, p_data):
        """
        vedi _getMRXp_wire_t0
        """
        return self._getMRXp_wire_t0(p_data)


    def _getMRXp_wire_data(self, p_data):
        """ 
        RECORD_RISPOSTA "COMANDO"0x65 Campo "DATI" MOSF_RX_DatiGrafico:
        "Modulo Risponde al RIP "  
            STX "MITTENTE" , “DESTINATARIO” , "COMANDO" , "  D A T I 512 Chr ", "DIMENSIONE"  CRC8  ETX cr  lf
            02H  0x40..47     0x40             65h        ch1.........ch512    0x57          xxh   03h 0Dh 0Ah
                |---------------calcolo CRC8---------------------------------------------/		
        ;ch1..ch512 valore 20h..7F    ;*Posizione linea di contatto (96 pixel)	
        ;Posizione altezza posizione pantografo al ch256
        ;*ESEMPIO:con punto di Fulcro,come da schema "19-01-MOSF-RX-R0 pag7.pdf",
        ;        Il Fattore di intensificazione è di 1,46
        ;        e il livello di dettaglio (granularità) diventà 3,4mm Pixel          
        """
        l_out={}
        l_out[bus.data_key.mosf_wire_data_ok]= general.status_ok
        l_out[bus.data_key.mosf_wire_data]= []
        l_missing_pixels= []
        for i in range(512):
            l_corrupted= False
            try:
                l_datum = p_data[i]
                if l_datum in range(bus.mosf_data.zero_value, bus.mosf_data.max_value + 1):
                    l_out[bus.data_key.mosf_wire_data].append(l_datum - bus.mosf_data.zero_value)
                else:
                    self.m_logger.error(f'Bad data for pixel {i}: {p_data[i]}')
                    l_corrupted= True
            except KeyError:
                l_missing_pixels.append(i)
                l_corrupted= True
            if l_corrupted:
                l_out[bus.data_key.mosf_wire_data_ok]= general.status_error
                # Setto il dato a zero se è corrotto
                l_out[bus.data_key.mosf_wire_data].append(0)
        if len(l_missing_pixels) > 0:
            self.m_logger.error('Graph data is corrupted or incomplete. The following pixels were set to zero: ' + ', '.join(l_missing_pixels))
        return l_out


    def _getMRXd_wire_data(self, p_data):
        """ 
        vedi _getMRXp_wire_data 
        """
        return self._getMRXp_wire_data(p_data)

    def _decode_trig_on_off(self, p_ch) -> Tuple[str, str]:
        """ Return status flash, status cameras """
        l_flash_onoff = general.status_on if p_ch & 0b01 else general.status_off
        l_cam_onoff = general.status_on if p_ch & 0b10 else general.status_off
        return l_flash_onoff, l_cam_onoff

    def _getTrigp_ver(self, p_data):
        """
        RECORD_RISPOSTA "COMANDO"=0x60 Campo "DATI" Trigger_Versione:
        ch1 30h..4Fh day 0x31..4F 0x31=Day 01.....0x4F=Day 31 (0123456789:;<=>?@ABCDEFGHIJKLMNO) Ascii
        ch2 30h..3Ch month 0x31..3C 0x31=gennaio..0x3C=DICEMBRE (0123456789:;<)
        ch3 30h..39h year 0x30..39 0x30=2020.....0x39=2029 (0123456789)
        ch4 30h..3Fh Stato On,Off
                     bit0=1 Flash_On
                     bit1=1 Camere_On
        Il quarto byte viene ignorato (ex riserva)
        """
        l_out={}
        l_out[bus.data_key.trig_vers]= self._to_date(
            p_year_ch=p_data[2],
            p_month_ch=p_data[1],
            p_day_ch=p_data[0]
        )
        l_flash_onoff, l_cam_onoff = self._decode_trig_on_off(p_data[3])
        l_out[bus.data_key.trig_flash_onoff] = l_flash_onoff
        l_out[bus.data_key.trig_cam_onoff] = l_cam_onoff
        return l_out

    def _getTrigd_ver(self, p_data):
        """
        vedi _getTrigp_ver
        """
        return self._getTrigp_ver(p_data)

    def _getTrigp_settings(self, p_data):
        """ 
        RECORD_RICHIESTA "COMANDO"=0x66 Campo "DATI" Trigger_Setting:
        ch1 30h..39h  Decine us	Trigger latency*jitter1 (Manta G-1236C default 96 us)
        ch2 30h..39h  Unità  us   "     "  
        ch3 30h..39h  Decine us	exposure time           (Manta G-1236C default 42 us) 
        ch4 30h..39h  Unità  us    
        """
        l_out= {}
        l_out[bus.data_key.trig_latency] = self._todecimal(p_data[0], p_data[1])
        l_out[bus.data_key.trig_exposure] = self._todecimal(p_data[2], p_data[3])
        return l_out

    def _getTrigd_settings(self, p_data):
        """ 
        vedi _getTrigp_settings 
        """
        return self._getTrigp_settings(p_data)

    def _getTrigp_on_off(self, p_data):
        """ 
        RECORD_RICHIESTA "COMANDO"=0x67 Campo "DATI" Trigger_On_Off: 
        ch1 30h..3Fh riserva
        ch2 30h..3Fh riserva
        ch3 30h..3Fh bit0=0 Trigger_Off   ;  bit0=1 Trigger_On        
        ch4 30h..3Fh riserva
        """
        l_out={}
        l_flash_onoff, l_cam_onoff = self._decode_trig_on_off(p_data[2])
        l_out[bus.data_key.trig_flash_onoff] = l_flash_onoff
        l_out[bus.data_key.trig_cam_onoff] = l_cam_onoff
        return l_out

    def _getTrigd_on_off(self, p_data):
        """ 
        vedi _getTrigp_on_off
        """
        return self._getTrigp_on_off(p_data)

    def _getTrigp_click(self, p_data):
        """ 
        RECORD_RICHIESTA "COMANDO"=0x68 Campo "DATI" Trigger_Scatto:
        ch1 30h..3Fh riserva
        ch2 30h..3Fh riserva
        ch3 30h..3Fh bit0=0 Trigger_Off   ;  bit0=1 Trigger_On        
        ch4 30h..3Fh riserva
        """
        l_out={}
        if p_data[2] & 0b1:
            l_out[bus.data_key.trig_click]= general.status_on
        else:
            l_out[bus.data_key.trig_click]= general.status_off
        return l_out

    def _getTrigd_click(self, p_data):
        """ 
        vedi _getTrigp_click
        """
        return self._getTrigp_click(p_data)

    def _decodeFlashStatus(self, p_nibbleFlash):
        '''
        riceve 2 bit
        ritorna status, efficiency
        '''
        if p_nibbleFlash == 0b00:
            return general.status_ok, bus.data_val.flash_100
        if p_nibbleFlash == 0b01:
            return general.status_ok, bus.data_val.flash_50
        if p_nibbleFlash == 0b10:
            return general.status_ok, bus.data_val.flash_80
        if p_nibbleFlash == 0b11:
            return general.status_ko, bus.data_val.flash_0
        return general.dato_errato, general.dato_errato

    def _getTrigp_status(self, p_data):
        """ 
        RECORD_RISPOSTA "COMANDO"0x69 Campo "DATI" Trigger_Allarmi (Binario Pari/DISPARI)
        ch1 30h..3Fh    bit0,1= 00=Ok  01,10=50%80%  11=Guasto Stato Flash 1
                        bit2,3= 00=Ok  01,10=50%80%  11=Guasto Stato Flash 2
        ch2 30h..3Fh    bit0,1= 00=Ok  01,10=50%80%  11=Guasto Stato Flash 3
                        bit2,3= 00=Ok  01,10=50%80%  11=Guasto Stato Flash 4
        ch3 30h..3Fh    bit0,1= 00=Ok  01,10=50%80%  11=Guasto Stato Flash 5
                        bit2,3= 00=Ok  01,10=50%80%  11=Guasto Stato Flash 6 
        ch4 30h..3Fh    Eventi/Allarmi
        """
        l_out={}    
        l_out[bus.data_key.trig_flash_1_status], l_out[bus.data_key.trig_flash_1_efficiency]= \
            self._decodeFlashStatus(p_data[0] & 0b0011)
        l_out[bus.data_key.trig_flash_2_status], l_out[bus.data_key.trig_flash_2_efficiency]= \
            self._decodeFlashStatus((p_data[0] & 0b1100) >> 2)
        l_out[bus.data_key.trig_flash_3_status], l_out[bus.data_key.trig_flash_3_efficiency]= \
            self._decodeFlashStatus(p_data[1] & 0b0011)
        l_out[bus.data_key.trig_flash_4_status], l_out[bus.data_key.trig_flash_4_efficiency]= \
            self._decodeFlashStatus((p_data[1] & 0b1100) >> 2)
        l_out[bus.data_key.trig_flash_5_status], l_out[bus.data_key.trig_flash_5_efficiency]= \
            self._decodeFlashStatus(p_data[2] & 0b0011)
        l_out[bus.data_key.trig_flash_6_status], l_out[bus.data_key.trig_flash_6_efficiency]= \
            self._decodeFlashStatus((p_data[2] & 0b1100) >> 2)
        return l_out

    def _getTrigd_status(self, p_data):
        """ 
        vedi _getTrigp_status
        """
        return self._getTrigp_status(p_data)

    def _getIO_ver(self, p_data):
        """
        RECORD_RISPOSTA/RICHIESTA "COMANDO"=0x60 Campo "DATI" I_O_Versione:
        ch1 30h..4Fh day 0x31..4F 0x31=Day 01.....0x4F=Day 31 (0123456789:;<=>?@ABCDEFGHIJKLMNO) Ascii
        ch2 30h..3Ch month 0x31..3C 0x31=gennaio..0x3C=DICEMBRE (0123456789:;<)
        ch3 30h..39h year 0x30..39 0x30=2020.....0x39=2029 (0123456789)
        ch4 30h..3Fh
                     bit0=0 RIP_Off , bit0=1 RIP_On STATO RIP_OnOff ;
                     ;bit1,2,3 riserva
        Il quarto byte viene ignorato (ex riserva)
        """
        l_out={}
        l_out[bus.data_key.io_vers]= self._to_date(
            p_year_ch=p_data[2],
            p_month_ch=p_data[1],
            p_day_ch=p_data[0]
        )        
        return l_out

    def _getIOTestBattery(self, p_data):
        """
        RECORD_RICHIESTA "COMANDO"0x6A  Campo "DATI" I_O_TestBatt (per stato batt.vedi "COMANDO"=0x6B);
        ch1 30h..3Fh riserva
        ch2 30h..3Fh riserva
        ch3 30h..3Fh bit0=0 TestBatt_Off   ;  bit0=1 TestBatt_On        
        ch4 30h..3Fh riserva
        """
        l_out= {}
        if p_data[2] & 0b1:
            l_out[bus.data_key.io_test_batt]= general.status_on
        else:
            l_out[bus.data_key.io_test_batt]= general.status_off
        return l_out

    def _decode_bit(self, p_ch, bit_pos):
        """Returns KO if bit=1, OK if bit=0"""
        mask = {
            0: 0b1,
            1: 0b10,
            2: 0b100,
            3: 0b1000
        }
        if p_ch & mask[bit_pos]:
            return general.status_ko
        else:
            return general.status_ok

    def _getIOStatus(self, p_data):
        """
        RECORD_RISPOSTA "COMANDO"=0x6B Campo "DATI" I_O_Allarmi: 
        ch1 30h..3Fh bit0=0 Ok, =1 All.Batt.     ;  bit1=0 Ok, =1 All.24vcc        ;  bit2=0 Ok, =1 SW_ARMADIO Open ;  bit3=0 Ok, =1 STATO AllARME RIP
        ch2 30h..3Fh bit0=0 Ok, =1 RV_PARI Open  ;  bit1=0 Ok, =1 SW_PRR_PARI Open ;  bit2=0 Ok, =1 RV_DISPARI Open ;  bit3=0 Ok, =1 SW_PRR_DISPARI Open.        
        ch3 30h..3Fh Decine NTC-C°             
        ch4 30h..3Fh Unità  NTC-C°
        """
        l_out= {}      
        " Allarmi "  
        l_out[bus.data_key.io_alim_batt]=  self._decode_bit(p_data[0], 0)
        l_out[bus.data_key.io_alim_24]= self._decode_bit(p_data[0], 1)
        l_out[bus.data_key.io_sw_armadio]= self._decode_bit(p_data[0], 2)
        l_out[bus.data_key.io_rip_status]= self._decode_bit(p_data[0], 3)
        l_out[bus.data_key.io_rv_pari]= self._decode_bit(p_data[1], 0)
        l_out[bus.data_key.io_sw_prr_pari]= self._decode_bit(p_data[1], 1)
        l_out[bus.data_key.io_rv_dispari]= self._decode_bit(p_data[1], 2)
        l_out[bus.data_key.io_sw_prr_dispari]= self._decode_bit(p_data[1], 3)
        " Ntc "
        l_out[bus.data_key.io_ntc_c]= self._todecimal(p_data[2], p_data[3])

        return l_out


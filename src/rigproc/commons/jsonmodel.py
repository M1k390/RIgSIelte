#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creazione modelli json 
Aggiornato alle specifiche Kafka_v1.1
"""

import logging
import json

import rigproc
from rigproc.commons import keywords
from rigproc.commons.redisi import get_redisI
from rigproc.commons.wrappers import wrapkeys
from rigproc.commons.config import get_config

from rigproc.params import bus, internal, kafka, general


class JsonModels():

    def __init__(self):
        """ 
        """
        self.m_logger= logging.getLogger('root')

    def _format_dict_values(self, p_dict: dict) -> dict:
        l_res= {}
        for key, val in p_dict.items():
            if isinstance(val, dict):
                l_res[key]= self._format_dict_values(val)
            elif str(val) == 'True':
                l_res[key]= 'true'
            elif str(val) == 'False':
                l_res[key]= 'false'
            elif str(val) == 'None':
                l_res[key]= 'none'
            else:
                l_res[key]= val
        return l_res

    def _dump_model(self, p_model):
        l_dump= None
        try:
            l_dump= json.dumps(p_model)
        except Exception as e:
            self.m_logger.error(f"Json exception dumping {p_model}: {e}")
            l_dump= json.dumps({"problem": "data model dump went wrong"})
        return l_dump

    def _jsonEventHeader(self, p_data):
        """
        Generazione parti comuni evento json model

        Parameters
        ----------
            p_data: dict
                Dati del flow che richiede il modello
            p_id: str
                Valore campo id (opzionale)

        Returns
        -------
        Dizionario campi evento
        """
        l_implant_conf= get_config().main.implant_data
        l_model_header= {          
            keywords.json_id: wrapkeys.getValue(p_data, keywords.evdata_id),
            keywords.json_trans_id: wrapkeys.getValue(p_data, keywords.evdata_uuid),
            keywords.json_event_date: wrapkeys.getValue(p_data, keywords.evdata_date),
            keywords.json_event_time: wrapkeys.getValue(p_data, keywords.evdata_time),
            keywords.json_event_ts: wrapkeys.getValue(p_data, keywords.evdata_float_timestamp),
            keywords.json_nome_rip: l_implant_conf.nome_rip.get()
        }
        return l_model_header

    def _jsonInstallationParams(self, p_additional_params={}):
        """
        Generazione parametri impianto json model
        Acquisizione dati dalla cache di Redis

        Returns
        -------
        Dizionario parametri impianto
        """
        l_implant_conf= get_config().main.implant_data
        l_model_params= {
            kafka.rip_key.parameters: {
                kafka.rip_key.nome_imp: l_implant_conf.nome_ivip.get(), 
                kafka.rip_key.nome_linea: l_implant_conf.nome_linea.get(),
                kafka.rip_key.ip_rip: l_implant_conf.ip_remoto.get(),
                # BINARIO            
                kafka.rip_key.prrA_bin: l_implant_conf.prrA_bin.get(),
                kafka.rip_key.prrB_bin: l_implant_conf.prrB_bin.get(),              
                # LINEA
                kafka.rip_key.loc_tratta_inizio: l_implant_conf.loc_tratta_pari_inizio.get(), # to remove
                kafka.rip_key.loc_tratta_fine: l_implant_conf.loc_tratta_pari_fine.get(), # to remove
                kafka.rip_key.loc_tratta_pari_inizio: l_implant_conf.loc_tratta_pari_inizio.get(),
                kafka.rip_key.loc_tratta_pari_fine: l_implant_conf.loc_tratta_pari_fine.get(),
                kafka.rip_key.loc_tratta_dispari_inizio: l_implant_conf.loc_tratta_dispari_inizio.get(),
                kafka.rip_key.loc_tratta_dispari_fine: l_implant_conf.loc_tratta_dispari_fine.get(),
                kafka.rip_key.cod_tratta_pari: l_implant_conf.cod_pic_tratta_pari.get(), # to remove
                kafka.rip_key.cod_tratta_dispari: l_implant_conf.cod_pic_tratta_dispari.get(), # to remove
                kafka.rip_key.cod_pic_tratta_pari: l_implant_conf.cod_pic_tratta_pari.get(),
                kafka.rip_key.cod_pic_tratta_dispari: l_implant_conf.cod_pic_tratta_dispari.get(),
                # SETTINGS
                kafka.rip_key.wire_calib_pari: l_implant_conf.wire_calib_pari.get(),
                kafka.rip_key.wire_calib_dispari: l_implant_conf.wire_calib_dispari.get(),
                kafka.rip_key.fin_temp_pic_pari: l_implant_conf.distanza_prr_IT_pari.get(), # to remove
                kafka.rip_key.fin_temp_pic_dispari: l_implant_conf.distanza_prr_IT_dispari.get(), # to remove
                kafka.rip_key.distanza_prr_IT_pari: l_implant_conf.distanza_prr_IT_pari.get(),
                kafka.rip_key.distanza_prr_IT_dispari: l_implant_conf.distanza_prr_IT_dispari.get(),
                # ADDITIONAL PARAMETERS
                **p_additional_params
            }
        }
        return l_model_params

    def _getStatusKey(self, p_module, p_binario):
        """ Ritorna la chiave che memorizza lo stato del modulo a seconda del binario 

        Parameters
        ----------
        p_module: modulo (keywords.module.MODULO)
        p_binario: pari/dispari

        Returns
        -------
        la chiave del modulo
        None se il modulo o il binario sono scorretti
        """
        l_module_bin= None
        if p_binario == keywords.bin_pari or p_binario == keywords.bin_unico:
            if p_module == keywords.module.mosf_tx:
                l_module_bin= keywords.mosf_tx_p
            elif p_module == keywords.module.mosf_rx:
                l_module_bin= keywords.mosf_rx_p
            elif p_module == keywords.module.trigger:
                l_module_bin= keywords.trigger_p
            else:
                self.m_logger.error(f'Modulo non valido: {p_module}')
        elif p_binario == keywords.bin_dispari:
            if p_module == keywords.module.mosf_tx:
                l_module_bin= keywords.mosf_tx_d
            elif p_module == keywords.module.mosf_rx:
                l_module_bin= keywords.mosf_rx_d
            elif p_module == keywords.module.trigger:
                l_module_bin= keywords.trigger_d
            else:
                self.m_logger.error(f'Modulo non valido: {p_module}')
        else:
            self.m_logger.error(f'Binario non valido: {p_binario}')
        return l_module_bin

    def getTrigModel(self, p_data):
        """
        Prepara il json 'event_model' a partire dai dati cache e dall
        p_id : id evento

        Returns
        -------
        Json model event trigger   

        TOPIC 1: EventoPassaggioTreno
        """
        l_implant_conf= get_config().main.implant_data

        l_id= wrapkeys.getValue(p_data, keywords.evdata_id) # timestamp_nomeimpianto_binario_direzione
        l_binario= wrapkeys.getValue(p_data, keywords.evdata_binario)

        l_model= {
            keywords.json_event_type: 'trigger',
            keywords.json_recovered: wrapkeys.getValue(p_data, keywords.evdata_recovered),
            **self._jsonEventHeader(p_data),
            **self._jsonInstallationParams(p_additional_params={
                keywords.json_tmosf_f: l_implant_conf.t_mosf_prrA.get(),
                keywords.json_tmosf_l: l_implant_conf.t_mosf_prrB.get(),
            }),
            # IMAGES
            keywords.json_images: {
                keywords.json_inizio_upload: wrapkeys.getValue(p_data, keywords.evdata_upload_started),
                keywords.json_fine_upload: wrapkeys.getValue(p_data, keywords.evdata_upload_finished),
                keywords.json_path: wrapkeys.getValue(p_data, keywords.evdata_remote_dir_json),
                keywords.json_names: wrapkeys.getValueDefault(p_data, [], internal.flow_data.img_files),
                # EXIF DATA (implant data from Redis cache)
                keywords.json_exif: {
                    keywords.json_exif_fov: l_implant_conf.fov.get(),
                    keywords.json_exif_sensor_width: l_implant_conf.sensor_width.get(),
                    keywords.json_exif_focal_distance: l_implant_conf.focal_distance.get(),
                    keywords.json_exif_camera_brand: l_implant_conf.camera_brand.get(),
                    keywords.json_exif_camera_model: l_implant_conf.camera_model.get()
                }
            },
            # MEASURES
            keywords.json_measures: {
                keywords.json_wire_meas_t0: get_redisI().getStatusInfo(
                    self._getStatusKey(keywords.module.mosf_rx, l_binario), 
                    keywords.data_mosf_wire_t0_key
                ),
                keywords.json_train_speed: get_redisI().getStatusInfo(
                    self._getStatusKey(keywords.module.mosf_tx, l_binario), 
                    keywords.data_mtx_velo_key
                ),
                keywords.json_train_direction: get_redisI().getStatusInfo(
                    self._getStatusKey(keywords.module.mosf_tx, l_binario), 
                    keywords.data_mtx_direction_key
                ),
                keywords.json_bin: l_binario
            }
        }

        return self._dump_model(self._format_dict_values(l_model))

    def recoverTrigModel(self, p_json_model, p_data) -> str:
        """ update modello json evt t0
        Restituisce un json model aggiornato per il recovering

        p_model: string
            stringa json da modificare 
        p_data: dict
            dict con i nuovi dati utili per il modello
        
        Returns
        -------
        Modello json t0 updated (string)
        """
        try:
            l_model= json.loads(p_json_model)
        except Exception as e:
            self.m_logger.error(f'Error loading json {p_json_model}: {e}')
            return p_json_model
        # Update "On Recover"
        wrapkeys.setValue(
            l_model,
            'true',
            kafka.rip_key.recovered
        )
        # Update start and end upload times
        wrapkeys.setValue(
            l_model,
            wrapkeys.getValue(p_data, keywords.evdata_upload_started),
            keywords.json_images, keywords.json_inizio_upload # keys
        )
        wrapkeys.setValue(
            l_model,
            wrapkeys.getValue(p_data, keywords.evdata_upload_finished),
            keywords.json_images, keywords.json_fine_upload # keys
        )
        return self._dump_model(self._format_dict_values(l_model))

    def getDiagModel(self, p_data):
        """
        Json modello diagnostico

        Ritorna il dict del modello diagnostico

        TOPIC 2: DiagnosiSistemiIVIP_RIPtoSTG
        """        
        l_implant_conf= get_config().main.implant_data
        l_prrA_conf= get_config().camera.ids.prrA
        l_prrB_conf= get_config().camera.ids.prrB
        l_prrA_ids= [
            l_prrA_conf.id_1.get(),
            l_prrA_conf.id_2.get(),
            l_prrA_conf.id_3.get(),
            l_prrA_conf.id_4.get(),
            l_prrA_conf.id_5.get(),
            l_prrA_conf.id_6.get()
        ]
        l_prrB_ids= [
            l_prrB_conf.id_1.get(),
            l_prrB_conf.id_2.get(),
            l_prrB_conf.id_3.get(),
            l_prrB_conf.id_4.get(),
            l_prrB_conf.id_5.get(),
            l_prrB_conf.id_6.get()
        ]

        l_id= wrapkeys.getValue(p_data, keywords.evdata_id)

        l_model= {
            keywords.json_event_type: 'diagnosis',
            keywords.json_recovered: wrapkeys.getValue(p_data, keywords.evdata_recovered),
            keywords.json_on_trigger: wrapkeys.getValue(p_data, keywords.evdata_on_trigger),
            keywords.json_trigger_id: l_id,
            **self._jsonEventHeader(p_data),
            **self._jsonInstallationParams(p_additional_params={
                keywords.json_tmosf_f: l_implant_conf.t_mosf_prrA.get(),
                keywords.json_tmosf_l: l_implant_conf.t_mosf_prrB.get(),
            }),
            # STATUS
            keywords.json_status: {
                # CAMERAS
                keywords.json_cameras: {
                    # prrA
                    keywords.json_cam_prrA: [
                        {
                            'id': cam_id,
                            'status': get_redisI().cache.get(
                                keywords.prrA_cam_status_key + str(i),
                                p_default=keywords.status_error
                            )
                        }
                        for cam_id, i in zip(l_prrA_ids, range(1, 7))
                    ],
                    # prrB
                    keywords.json_cam_prrB: [
                        {
                            'id': cam_id,
                            'status': get_redisI().cache.get(
                                keywords.prrB_cam_status_key + str(i),
                                p_default=keywords.status_error
                            )
                        }
                        for cam_id, i in zip(l_prrB_ids, range(1, 7))
                    ]
                }
            },
            # I/O
            keywords.json_io: {
                keywords.json_io_status: get_redisI().getStatusInfo(keywords.io, keywords.io),
                keywords.json_io_battery: get_redisI().getStatusInfo(keywords.io, keywords.data_io_alim_batt_key),
                keywords.json_io_ivip_alim: get_redisI().getStatusInfo(keywords.io, keywords.data_io_IVIP_power_key),
                keywords.json_io_swc_prrA: get_redisI().getStatusInfo(keywords.io, keywords.data_io_switch_prr_p_key),
                keywords.json_io_swc_prrB: get_redisI().getStatusInfo(keywords.io, keywords.data_io_switch_prr_d_key),
                keywords.json_io_ldc_prrA: get_redisI().getStatusInfo(keywords.io, keywords.data_io_ldc_p_key),
                keywords.json_io_ldc_prrB: get_redisI().getStatusInfo(keywords.io, keywords.data_io_ldc_d_key),
                keywords.json_t_off_ivip_prrA: l_implant_conf.t_off_ivip_prrA.get(),
                keywords.json_t_off_ivip_prrB: l_implant_conf.t_off_ivip_prrB.get(),
                keywords.json_io_door: get_redisI().getStatusInfo(keywords.io, keywords.data_io_doors_key),
                # TEMPERATURES
                keywords.json_io_temperatures: {
                    keywords.json_io_sens1: get_redisI().getStatusInfo(keywords.io, keywords.data_io_sens1_key),
                    keywords.json_io_sens2: get_redisI().getStatusInfo(keywords.io, keywords.data_io_sens2_key)
                },
                # VENTILATION
                keywords.json_io_ventilation: {
                    keywords.json_io_vent1: get_redisI().getStatusInfo(keywords.io, keywords.data_io_vent1_key),
                    keywords.json_io_vent2: get_redisI().getStatusInfo(keywords.io, keywords.data_io_vent2_key)
                },
                # TRIGGER A
                keywords.json_triggerA: {
                    keywords.json_trigger_status: get_redisI().getStatusInfo(keywords.trigger_p, keywords.trigger_p),
                    # FLASHES
                    keywords.json_flashes: [
                        {
                            keywords.json_fl_id: fl_id,
                            keywords.json_fl_status: get_redisI().getStatusInfo(
                                keywords.trigger_p, 
                                fl_status_key
                            ),
                            keywords.json_fl_eff: get_redisI().getStatusInfo(
                                keywords.trigger_p,
                                fl_eff_key
                            )
                        }
                        for fl_id, fl_status_key, fl_eff_key in zip(
                            keywords.json_flash_ids,
                            [
                                keywords.data_trig_flash_1_status, 
                                keywords.data_trig_flash_2_status, 
                                keywords.data_trig_flash_3_status, 
                                keywords.data_trig_flash_4_status, 
                                keywords.data_trig_flash_5_status, 
                                keywords.data_trig_flash_6_status
                            ],
                            [
                                keywords.data_trig_flash_1_efficiency, 
                                keywords.data_trig_flash_2_efficiency, 
                                keywords.data_trig_flash_3_efficiency, 
                                keywords.data_trig_flash_4_efficiency, 
                                keywords.data_trig_flash_5_efficiency, 
                                keywords.data_trig_flash_6_efficiency
                            ]
                        )
                    ]
                },
                # TRIGGER B
                keywords.json_triggerB: {
                    keywords.json_trigger_status: get_redisI().getStatusInfo(keywords.trigger_d, keywords.trigger_d),
                    # FLASHES
                    keywords.json_flashes: [
                        {
                            keywords.json_fl_id: fl_id,
                            keywords.json_fl_status: get_redisI().getStatusInfo(
                                keywords.trigger_d, 
                                fl_status_key
                            ),
                            keywords.json_fl_eff: get_redisI().getStatusInfo(
                                keywords.trigger_d,
                                fl_eff_key
                            )
                        }
                        for fl_id, fl_status_key, fl_eff_key in zip(
                            keywords.json_flash_ids,
                            [
                                keywords.data_trig_flash_1_status, 
                                keywords.data_trig_flash_2_status, 
                                keywords.data_trig_flash_3_status, 
                                keywords.data_trig_flash_4_status, 
                                keywords.data_trig_flash_5_status, 
                                keywords.data_trig_flash_6_status
                            ],
                            [
                                keywords.data_trig_flash_1_efficiency, 
                                keywords.data_trig_flash_2_efficiency, 
                                keywords.data_trig_flash_3_efficiency, 
                                keywords.data_trig_flash_4_efficiency, 
                                keywords.data_trig_flash_5_efficiency, 
                                keywords.data_trig_flash_6_efficiency
                            ]
                        )
                    ]
                },
                # MOSF
                keywords.json_mosf: [
                    {
                        keywords.json_ms_id: "TxA",
                        keywords.json_ms_status: get_redisI().getStatusInfo(keywords.mosf_tx_p, keywords.mosf_tx_p)
                    },
                    {
                        keywords.json_ms_id: "RxA",
                        keywords.json_ms_status: get_redisI().getStatusInfo(keywords.mosf_rx_p, keywords.mosf_rx_p)
                    },
                    {
                        keywords.json_ms_id: "TxB",
                        keywords.json_ms_status: get_redisI().getStatusInfo(keywords.mosf_tx_d, keywords.mosf_tx_d)
                    },
                    {
                        keywords.json_ms_id: "RxB",
                        keywords.json_ms_status: get_redisI().getStatusInfo(keywords.mosf_rx_d, keywords.mosf_rx_d)
                    },
                    {
                        keywords.json_ms_id: "T_mosfxA",
                        keywords.json_ms_status: l_implant_conf.t_mosf_prrA.get() # Tempo mosf?
                    },
                    {
                        keywords.json_ms_id: "T_mosfxB",
                        keywords.json_ms_status: l_implant_conf.t_mosf_prrB.get()
                    }
                ]
            }
        }
        return self._dump_model(self._format_dict_values(l_model))

    def recoverDiagModel(self, p_json_model, p_data) -> str:
        """ update modello json diag
        Restituisce un json model aggiornato per il recovering

        p_model: string
            stringa json da modificare 
        p_data: dict
            dict con i nuovi dati utili per il modello
        
        Returns
        -------
        Modello json updated (string)
        """
        try:
            l_model= json.loads(p_json_model)
        except Exception as e:
            self.m_logger.error(f'Error loading json {p_json_model}: {e}')
            return p_json_model
        # Update "On Recover"
        wrapkeys.setValue(
            l_model,
            'true',
            kafka.rip_key.on_trigger
        )
        return self._dump_model(self._format_dict_values(l_model))

    def getMosfDataModel(self, p_data):
        """
        Json modello mosf data
        
        Ritorna il json del modello mosf data 

        TOPIC 3: MOSFvalues
        """
        l_implant_conf= get_config().main.implant_data

        l_id= wrapkeys.getValue(p_data, keywords.evdata_id)
        l_binario= wrapkeys.getValue(p_data, keywords.evdata_binario)

        l_model= {
            keywords.json_event_type: 'mosf',
            keywords.json_recovered: wrapkeys.getValue(p_data, keywords.evdata_recovered),
            keywords.json_on_trigger: True,
            keywords.json_trigger_id: l_id,
            **self._jsonEventHeader(p_data),
            **self._jsonInstallationParams(p_additional_params={
                keywords.json_tmosf_f: l_implant_conf.t_mosf_prrA.get(),
                keywords.json_tmosf_l: l_implant_conf.t_mosf_prrB.get(),
            }),          
            # MEASURES
            keywords.json_measures: {
                keywords.json_wire_t0: wrapkeys.getValueDefault(
                    p_data,
                    general.dato_non_disp,
                    internal.flow_data.mosf_wire_data, 
                    bus.data_key.mosf_wire_t0
                ),
                keywords.json_wire_data: wrapkeys.getValueDefault(
                    p_data, 
                    general.dato_non_disp, 
                    keywords.evdata_mosf_wire_data, keywords.data_mosf_wire_data_key
                )
            }
        }
        return self._dump_model(self._format_dict_values(l_model))

    def recoverMosfModel(self, p_json_model, p_data) -> str:
        """ update modello json mosf
        Restituisce un json model aggiornato per il recovering

        p_model: string
            stringa json da modificare 
        p_data: dict
            dict con i nuovi dati utili per il modello
        
        Returns
        -------
        Modello json updated (string)
        """
        try:
            l_model= json.loads(p_json_model)
        except Exception as e:
            self.m_logger.error(f'Error loading json {p_json_model}: {e}')
            return p_json_model
        # Update "On Recover"
        wrapkeys.setValue(
            l_model,
            'true',
            kafka.rip_key.on_trigger
        )
        return self._dump_model(self._format_dict_values(l_model))

    # K1.1: EVENTO AllarmeAnomaliaIVIP
    def getAnomalyAlarmModel(self, p_data):
        """ 
        Json model per la segnalazione del malfunzionamento di uno dei componenti del sistema di sensoristica del singolo PRR 
        
        TOPIC 4: AllarmeAnomaliaIVIP
        """

        l_model= {
            keywords.json_event_type: 'anomaly',
            **self._jsonEventHeader(
                p_data
            ),
            keywords.json_alarm: { # K1.1 @TODO
                keywords.json_alarm_id: wrapkeys.getValue(p_data, keywords.evdata_alarm_id),
                keywords.json_alarm_decr: wrapkeys.getValue(p_data, keywords.evdata_alarm_descr),
                keywords.json_alarm_status: wrapkeys.getValue(p_data, keywords.evdata_alarm_status),
            }
        }
        return self._dump_model(self._format_dict_values(l_model))
    
    # K1.1: EVENTO AggiornamentoImpostazioni_RIPtoSTG
    def getInternalSettingsUpdateModel(self, p_data):
        """
        Json model per segnalare l'avvenuto cambio di impostazioni
        (aggiornamento dell impostazioni interne: tempi MOSF, intervallo di spegnimento in caso di mancanza di corrente)

        TOPIC 6: AggiornamentoImpostazioni_RIPtoSTG
        """
        l_implant_conf= get_config().main.implant_data

        # Parto dal dict della richiesta e aggiungo i campi necessari (una sorta di ACK)
        l_request_json_dict= wrapkeys.getValue(p_data, keywords.evdata_json_from_stg)
        l_update_ok= True
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            'rip_settings_update',
            keywords.json_event_type
        )
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            l_implant_conf.nome_rip.get(),
            keywords.json_nome_rip
        )
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            wrapkeys.getValueDefault(p_data, False, keywords.evdata_int_sett_upd_confirmed),
            keywords.json_check
        )
        if l_update_ok:
            return self._dump_model(self._format_dict_values(l_request_json_dict))
        else:
            self.m_logger.error(f'Error updating dict {l_request_json_dict}')
            return json.dumps({'error': 'malformed request'})
    
    # K1.1: EVENTO AggiornamentoFinestraInizioTratta_RIPtoSTG
    def getTimeWindowSettingsUpdateModel(self, p_data):
        """
        Json model per segnalare l'avvenuto cambio di impostazioni
        (intervallo temporale di inizio tratta per binario pari/dispari)

        TOPIC 8: AggiornamentoFinestraInizioTratta_RIPtoSTG
        """
        l_implant_conf= get_config().main.implant_data

        # Parto dal dict della richiesta e aggiungo i campi necessari (una sorta di ACK)
        l_request_json_dict= wrapkeys.getValue(p_data, keywords.evdata_json_from_stg)
        l_update_ok= True
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            'rip_finestra_temp_update_check',
            keywords.json_event_type
        )
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            l_implant_conf.nome_rip.get(),
            keywords.json_nome_rip
        )
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            wrapkeys.getValueDefault(p_data, False, keywords.evdata_time_win_upd_confirmed),
            keywords.json_check
        )
        if l_update_ok:
            return self._dump_model(self._format_dict_values(l_request_json_dict))
        else:
            self.m_logger.error(f'Error updating dict {l_request_json_dict}')
            return json.dumps({'error': 'malformed request'})

    def getSwUpdateScheduledModel(self, p_data):
        """ 
        Json model in risposta alla richiesta di aggiornamento sw 
        
        TOPIC 10: AggiornamentoSW_RIPtoSTG (Fase 1)
        """
        l_implant_conf= get_config().main.implant_data

        # Parto dal dict della richiesta e aggiungo i campi necessari (una sorta di ACK)
        l_request_json_dict= wrapkeys.getValue(p_data, keywords.evdata_json_from_stg)
        l_update_ok= True
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            'update_check',
            keywords.json_event_type
        )
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            l_implant_conf.nome_rip.get(),
            keywords.json_nome_rip
        )
        l_update_ok= l_update_ok and wrapkeys.setValue(
            l_request_json_dict,
            wrapkeys.getValueDefault(p_data, False, keywords.evdata_scheduled_confirmed),
            keywords.json_check
        )
        if l_update_ok:
            return self._dump_model(self._format_dict_values(l_request_json_dict))
        else:
            self.m_logger.error(f'Error updating dict {l_request_json_dict}')
            return json.dumps({'error': 'malformed request'})

    def getSwUpdateDoneModel(self, p_data):
        """ 
        Json model che informa che l'update è andato a buon fine 
        
        TOPIC 10: AggiornamentoSW_RIPtoSTG (Fase 2)
        """

        l_model= {
            # Instestazione dati evento
            keywords.json_event_type: 'update_info',
            **self._jsonEventHeader(p_data),
            keywords.json_scheduled_id: wrapkeys.getValue(p_data, keywords.evdata_sw_update, 'transaction_id'),
            # Risultato update
            keywords.json_update_result: {
                keywords.json_upd_start_date: wrapkeys.getValue(p_data, keywords.evdata_sw_update, 'update_start_date'),
                keywords.json_upd_start_time: wrapkeys.getValue(p_data, keywords.evdata_sw_update, 'update_start_time'),
                keywords.json_upd_end_date: wrapkeys.getValue(p_data, keywords.evdata_sw_update, 'update_end_date'),
                keywords.json_upd_end_time: wrapkeys.getValue(p_data, keywords.evdata_sw_update, 'update_end_time'),
                keywords.json_upd_version: wrapkeys.getValue(p_data, keywords.evdata_sw_update, 'update_version_requested'),
                keywords.json_upd_status: wrapkeys.getValue(p_data, keywords.evdata_sw_update, 'update_status'),
                keywords.json_upd_error: wrapkeys.getValue(p_data, keywords.evdata_sw_update, 'error'),
            }
        }
        return self._dump_model(self._format_dict_values(l_model))

    # K1.1: EVENTO IscrizioneRip_RIPtoSTG
    def getRipSubscriptionModel(self, p_data):
        """ 
        Json model per l'iscrizione all'STG di riferimento al momento dell'installazione 
        
        TOPIC 11: IscrizioneRip_RIPtoSTG
        """
        l_implant_conf= get_config().main.implant_data

        l_version= str(rigproc.__version__)

        l_model= {
            keywords.json_event_type: 'rip_subscription',
            **self._jsonEventHeader(p_data),
            **self._jsonInstallationParams(p_additional_params={
                keywords.json_t_mosf_prrA: l_implant_conf.t_mosf_prrA.get(),
                keywords.json_t_mosf_prrB: l_implant_conf.t_mosf_prrB.get(),
                keywords.json_t_off_ivip_prrA: l_implant_conf.t_off_ivip_prrA.get(),
                keywords.json_t_off_ivip_prrB: l_implant_conf.t_off_ivip_prrB.get(),
                keywords.json_sw_version: l_version
            })
        }
        return self._dump_model(self._format_dict_values(l_model))


# SINGLETON

json_models= JsonModels()
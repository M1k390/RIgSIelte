"""
Implant anomalies parameters (module, status key, anomaly value, id, description, etc...)
"""

from rigproc.params import bus, general, redis_keys


class Anomaly:
    def __init__(self, device: bus.module, id: str, descr: str, status: str) -> None:
        self.device= device
        self.id= id
        self.descr= descr
        self.status= status
    def __repr__(self) -> str:
        return f'device: {self.device} - id: {self.id} - descr: {self.descr} - status: {self.status}'


class definition:
    """ Raccoglie la definizione di tutte le anomalie """

    # MOSF TX A

    mtx_a_fault= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_guasto',
        descr=  'Modulo MOSF TX pari guasto',
        status= 'error'
    )
    mtx_a_rimb1= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_err_rimbalzo1',
        descr=  'Modulo MOSF TX pari errore rimbalzo 1',
        status= 'error'
    )
    mtx_a_rimb2= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_err_rimbalzo2',
        descr=  'Modulo MOSF TX pari errore rimbalzo 2',
        status= 'error'
    )
    mtx_a_vel0_h= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_vel0_high',
        descr=  'Modulo MOSF TX pari errore velocità0 > 470 km/h',
        status= 'error'
    )
    mtx_a_vel1_h= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_vel1_high',
        descr=  'Modulo MOSF TX pari errore velocità1 > 470 km/h',
        status= 'error'
    )
    mtx_a_vel0_l= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_vel0_low',
        descr=  'Modulo MOSF TX pari errore velocità0 < 7 km/h',
        status= 'error'
    )
    mtx_a_vel1_l= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_vel1_low',
        descr=  'Modulo MOSF TX pari errore velocità1 < 7 km/h',
        status= 'error'
    )
    mtx_a_err_trig0= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_err_trigger0',
        descr=  'Pant. senza treno, direzione treno pari',
        status= 'error'
    )
    mtx_a_err_trig1= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_err_trigger1',
        descr=  'Pant. senza treno, direzione treno dispari',
        status= 'error'
    )
    mtx_a_err_sens1= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_err_sens_vel1',
        descr=  'Errore sensore velocità 1',
        status= 'error'
    )
    mtx_a_err_sens2= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_err_sens_vel2',
        descr=  'Errore sensore velocità 2',
        status= 'error'
    )
    mtx_a_err_sens1_2= Anomaly(
        device= bus.module.mosf_tx_a,
        id=     'mosf_tx_pari_err_sens_vel1_2',
        descr=  'Errore sensore velocità 1-2',
        status= 'error'
    )

    # MOSF TX B
    
    mtx_b_fault= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_guasto',
        descr=  'Modulo MOSF TX dispari guasto',
        status= 'error'
    )
    mtx_b_rimb1= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_err_rimbalzo1',
        descr=  'Modulo MOSF TX dispari errore rimbalzo 1',
        status= 'error'
    )
    mtx_b_rimb2= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_err_rimbalzo2',
        descr=  'Modulo MOSF TX dispari errore rimbalzo 2',
        status= 'error'
    )
    mtx_b_vel0_h= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_vel0_high',
        descr=  'Modulo MOSF TX dispari errore velocità0 > 470 km/h',
        status= 'error'
    )
    mtx_b_vel1_h= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_vel1_high',
        descr=  'Modulo MOSF TX dispari errore velocità1 > 470 km/h',
        status= 'error'
    )
    mtx_b_vel0_l= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_vel0_low',
        descr=  'Modulo MOSF TX dispari errore velocità0 < 7 km/h',
        status= 'error'
    )
    mtx_b_vel1_l= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_vel1_low',
        descr=  'Modulo MOSF TX dispari errore velocità1 < 7 km/h',
        status= 'error'
    )
    mtx_b_err_trig0= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_err_trigger0',
        descr=  'Pant. senza treno, direzione treno dispari',
        status= 'error'
    )
    mtx_b_err_trig1= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_err_trigger1',
        descr=  'Pant. senza treno, direzione treno disdispari',
        status= 'error'
    )
    mtx_b_err_sens1= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_err_sens_vel1',
        descr=  'Errore sensore velocità 1',
        status= 'error'
    )
    mtx_b_err_sens2= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_err_sens_vel2',
        descr=  'Errore sensore velocità 2',
        status= 'error'
    )
    mtx_b_err_sens1_2= Anomaly(
        device= bus.module.mosf_tx_b,
        id=     'mosf_tx_dispari_err_sens_vel1_2',
        descr=  'Errore sensore velocità 1-2',
        status= 'error'
    )

    # MOSF RX A

    mrx_a_fault= Anomaly(
        device= bus.module.mosf_rx_a,
        id=     'mosf_rx_pari_guasto',
        descr=  'Modulo MOSF RX pari guasto',
        status= 'error'
    )

    # MOSF RX B

    mrx_b_fault= Anomaly(
        device= bus.module.mosf_rx_b,
        id=     'mosf_rx_dispari_guasto',
        descr=  'Modulo MOSF RX dispari guasto',
        status= 'error'
    )

    # TRIGGER A

    trig_a_fault= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_guasto',
        descr=  'Modulo TRIGGER pari guasto',
        status= 'error'
    )
    trig_a_fl1_80= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash1_eff80',
        descr=  'Trigger pari, flash 1: efficienza 80%',
        status= 'warning'
    )
    trig_a_fl1_50= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash1_eff50',
        descr=  'Trigger pari, flash 1: efficienza 50%',
        status= 'warning'
    )
    trig_a_fl1_0= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash1_eff0',
        descr=  'Trigger pari, flash 1: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_a_fl2_80= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash2_eff80',
        descr=  'Trigger pari, flash 2: efficienza 80%',
        status= 'warning'
    )
    trig_a_fl2_50= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash2_eff50',
        descr=  'Trigger pari, flash 2: efficienza 50%',
        status= 'warning'
    )
    trig_a_fl2_0= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash2_eff0',
        descr=  'Trigger pari, flash 2: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_a_fl3_80= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash3_eff80',
        descr=  'Trigger pari, flash 3: efficienza 80%',
        status= 'warning'
    )
    trig_a_fl3_50= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash3_eff50',
        descr=  'Trigger pari, flash 3: efficienza 50%',
        status= 'warning'
    )
    trig_a_fl3_0= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash3_eff0',
        descr=  'Trigger pari, flash 3: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_a_fl4_80= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash4_eff80',
        descr=  'Trigger pari, flash 4: efficienza 80%',
        status= 'warning'
    )
    trig_a_fl4_50= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash4_eff50',
        descr=  'Trigger pari, flash 4: efficienza 50%',
        status= 'warning'
    )
    trig_a_fl4_0= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash4_eff0',
        descr=  'Trigger pari, flash 4: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_a_fl5_80= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash5_eff80',
        descr=  'Trigger pari, flash 5: efficienza 80%',
        status= 'warning'
    )
    trig_a_fl5_50= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash5_eff50',
        descr=  'Trigger pari, flash 5: efficienza 50%',
        status= 'warning'
    )
    trig_a_fl5_0= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash5_eff0',
        descr=  'Trigger pari, flash 5: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_a_fl6_80= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash6_eff80',
        descr=  'Trigger pari, flash 6: efficienza 80%',
        status= 'warning'
    )
    trig_a_fl6_50= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash6_eff50',
        descr=  'Trigger pari, flash 6: efficienza 50%',
        status= 'warning'
    )
    trig_a_fl6_0= Anomaly(
        device= bus.module.trigger_a,
        id=     'trigger_pari_flash6_eff0',
        descr=  'Trigger pari, flash 6: efficienza 0% (guasto)',
        status= 'error'
    )

    # TRIGGER B

    trig_b_fault= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_guasto',
        descr=  'Modulo TRIGGER dispari guasto',
        status= 'error'
    )
    trig_b_fl1_80= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash1_eff80',
        descr=  'Trigger dispari, flash 1: efficienza 80%',
        status= 'warning'
    )
    trig_b_fl1_50= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash1_eff50',
        descr=  'Trigger dispari, flash 1: efficienza 50%',
        status= 'warning'
    )
    trig_b_fl1_0= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash1_eff0',
        descr=  'Trigger dispari, flash 1: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_b_fl2_80= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash2_eff80',
        descr=  'Trigger dispari, flash 2: efficienza 80%',
        status= 'warning'
    )
    trig_b_fl2_50= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash2_eff50',
        descr=  'Trigger dispari, flash 2: efficienza 50%',
        status= 'warning'
    )
    trig_b_fl2_0= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash2_eff0',
        descr=  'Trigger dispari, flash 2: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_b_fl3_80= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash3_eff80',
        descr=  'Trigger dispari, flash 3: efficienza 80%',
        status= 'warning'
    )
    trig_b_fl3_50= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash3_eff50',
        descr=  'Trigger dispari, flash 3: efficienza 50%',
        status= 'warning'
    )
    trig_b_fl3_0= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash3_eff0',
        descr=  'Trigger dispari, flash 3: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_b_fl4_80= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash4_eff80',
        descr=  'Trigger dispari, flash 4: efficienza 80%',
        status= 'warning'
    )
    trig_b_fl4_50= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash4_eff50',
        descr=  'Trigger dispari, flash 4: efficienza 50%',
        status= 'warning'
    )
    trig_b_fl4_0= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash4_eff0',
        descr=  'Trigger dispari, flash 4: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_b_fl5_80= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash5_eff80',
        descr=  'Trigger dispari, flash 5: efficienza 80%',
        status= 'warning'
    )
    trig_b_fl5_50= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash5_eff50',
        descr=  'Trigger dispari, flash 5: efficienza 50%',
        status= 'warning'
    )
    trig_b_fl5_0= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash5_eff0',
        descr=  'Trigger dispari, flash 5: efficienza 0% (guasto)',
        status= 'error'
    )
    trig_b_fl6_80= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash6_eff80',
        descr=  'Trigger dispari, flash 6: efficienza 80%',
        status= 'warning'
    )
    trig_b_fl6_50= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash6_eff50',
        descr=  'Trigger dispari, flash 6: efficienza 50%',
        status= 'warning'
    )
    trig_b_fl6_0= Anomaly(
        device= bus.module.trigger_b,
        id=     'trigger_dispari_flash6_eff0',
        descr=  'Trigger dispari, flash 6: efficienza 0% (guasto)',
        status= 'error'
    )

    # I/O

    io_fault= Anomaly(
        device= bus.module.io,
        id=     'io_guasto',
        descr=  'Modulo IO guasto',
        status= 'error'
    )
    io_alim_batt= Anomaly(
        device= bus.module.io,
        id=     'io_alim_batt',
        descr=  'Modulo I/O: errore alim. batteria',
        status= 'error'
    )
    io_alim_24v= Anomaly(
        device= bus.module.io,
        id=     'io_alim_24v',
        descr=  'Modulo I/O: errore alim. 24vcc',
        status= 'error'
    )
    io_sw_armadio= Anomaly(
        device= bus.module.io,
        id=     'io_sw_armadio',
        descr=  'Modulo I/O: armadio aperto',
        status= 'warning'
    )
    io_rv_pari= Anomaly(
        device= bus.module.io,
        id=     'io_rv_pari_open',
        descr=  'Modulo I/O: rilevatore tensione linea di contatto pari aperto',
        status= 'warning'
    )
    io_sw_prr_pari= Anomaly(
        device= bus.module.io,
        id=     'io_sw_prr_pari_open',
        descr=  'Modulo I/O: switch manuale di disattivazione binario pari aperto',
        status= 'warning'
    )
    io_rv_dispari= Anomaly(
        device= bus.module.io,
        id=     'io_rv_dispari_open',
        descr=  'Modulo I/O: rilevatore tensione linea di contatto dispari aperto',
        status= 'warning'
    )
    io_sw_prr_dispari= Anomaly(
        device= bus.module.io,
        id=     'io_sw_prr_dispari_open',
        descr=  'Modulo I/O: switch manuale di disattivazione binario dispari aperto',
        status= 'warning'
    )

    # VIDEOSERVER (RIP)

    rip_config= Anomaly(
        device= bus.module.videoserver,
        id=     'rip_config_err',
        descr=  'Errore nella configurazione del RIP',
        status= 'error'
    )
    rip_sshfs= Anomaly(
        device= bus.module.videoserver,
        id=     'rip_sshfs_connection_err',
        descr=  'Errore di connessione verso il server sshfs',
        status= 'error'
    )
    rip_kafka= Anomaly(
        device= bus.module.videoserver,
        id=     'rip_kafka_connection_err',
        descr=  'Errore di connessione: impossibile raggiongere il broker di Kafka',
        status= 'error'
    )

    # CAMERAS

    cam1_a_missing= Anomaly(
        device= bus.module.cam1_a,
        id=     'cam1_1_mancante',
        descr=  'Camera 1 prr 1 mancante',
        status= 'error'
    )
    cam1_a_fault= Anomaly(
        device= bus.module.cam1_a,
        id=     'cam1_1_guasta',
        descr=  'Camera 1 prr 1 guasta',
        status= 'error'
    )
    cam_1_a_error= Anomaly(
        device= bus.module.cam1_a,
        id=     'cam1_pari_error',
        descr=  'Camera 1 prr pari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_1_a_missing_frame= Anomaly(
        device= bus.module.cam1_a,
        id=     'cam1_pari_frame_mancante',
        descr=  'Camera 1 prr pari: frame mancante',
        status= 'error'
    )
    cam_1_a_missing_trigger= Anomaly(
        device= bus.module.cam1_a,
        id=     'cam1_pari_trigger_mancante',
        descr=  'Camera 1 prr pari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam1_b_missing= Anomaly(
        device= bus.module.cam1_b,
        id=     'cam1_1_mancante',
        descr=  'Camera 1 prr 1 mancante',
        status= 'error'
    )
    cam1_b_fault= Anomaly(
        device= bus.module.cam1_b,
        id=     'cam1_1_guasta',
        descr=  'Camera 1 prr 1 guasta',
        status= 'error'
    )
    cam_1_b_error= Anomaly(
        device= bus.module.cam1_b,
        id=     'cam1_dispari_error',
        descr=  'Camera 1 prr dispari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_1_b_missing_frame= Anomaly(
        device= bus.module.cam1_b,
        id=     'cam1_dispari_frame_mancante',
        descr=  'Camera 1 prr dispari: frame mancante',
        status= 'error'
    )
    cam_1_b_missing_trigger= Anomaly(
        device= bus.module.cam1_b,
        id=     'cam1_dispari_trigger_mancante',
        descr=  'Camera 1 prr dispari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam2_a_missing= Anomaly(
        device= bus.module.cam2_a,
        id=     'cam2_2_mancante',
        descr=  'Camera 2 prr 2 mancante',
        status= 'error'
    )
    cam2_a_fault= Anomaly(
        device= bus.module.cam2_a,
        id=     'cam2_2_guasta',
        descr=  'Camera 2 prr 2 guasta',
        status= 'error'
    )
    cam_2_a_error= Anomaly(
        device= bus.module.cam2_a,
        id=     'cam2_pari_error',
        descr=  'Camera 2 prr pari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_2_a_missing_frame= Anomaly(
        device= bus.module.cam2_a,
        id=     'cam2_pari_frame_mancante',
        descr=  'Camera 2 prr pari: frame mancante',
        status= 'error'
    )
    cam_2_a_missing_trigger= Anomaly(
        device= bus.module.cam2_a,
        id=     'cam2_pari_trigger_mancante',
        descr=  'Camera 2 prr pari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam2_b_missing= Anomaly(
        device= bus.module.cam2_b,
        id=     'cam2_2_mancante',
        descr=  'Camera 2 prr 2 mancante',
        status= 'error'
    )
    cam2_b_fault= Anomaly(
        device= bus.module.cam2_b,
        id=     'cam2_2_guasta',
        descr=  'Camera 2 prr 2 guasta',
        status= 'error'
    )
    cam_2_b_error= Anomaly(
        device= bus.module.cam2_b,
        id=     'cam2_dispari_error',
        descr=  'Camera 2 prr dispari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_2_b_missing_frame= Anomaly(
        device= bus.module.cam2_b,
        id=     'cam2_dispari_frame_mancante',
        descr=  'Camera 2 prr dispari: frame mancante',
        status= 'error'
    )
    cam_2_b_missing_trigger= Anomaly(
        device= bus.module.cam2_b,
        id=     'cam2_dispari_trigger_mancante',
        descr=  'Camera 2 prr dispari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam3_a_missing= Anomaly(
        device= bus.module.cam3_a,
        id=     'cam3_3_mancante',
        descr=  'Camera 3 prr 3 mancante',
        status= 'error'
    )
    cam3_a_fault= Anomaly(
        device= bus.module.cam3_a,
        id=     'cam3_3_guasta',
        descr=  'Camera 3 prr 3 guasta',
        status= 'error'
    )
    cam_3_a_error= Anomaly(
        device= bus.module.cam3_a,
        id=     'cam3_pari_error',
        descr=  'Camera 3 prr pari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_3_a_missing_frame= Anomaly(
        device= bus.module.cam3_a,
        id=     'cam3_pari_frame_mancante',
        descr=  'Camera 3 prr pari: frame mancante',
        status= 'error'
    )
    cam_3_a_missing_trigger= Anomaly(
        device= bus.module.cam3_a,
        id=     'cam3_pari_trigger_mancante',
        descr=  'Camera 3 prr pari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam3_b_missing= Anomaly(
        device= bus.module.cam3_b,
        id=     'cam3_3_mancante',
        descr=  'Camera 3 prr 3 mancante',
        status= 'error'
    )
    cam3_b_fault= Anomaly(
        device= bus.module.cam3_b,
        id=     'cam3_3_guasta',
        descr=  'Camera 3 prr 3 guasta',
        status= 'error'
    )
    cam_3_b_error= Anomaly(
        device= bus.module.cam3_b,
        id=     'cam3_dispari_error',
        descr=  'Camera 3 prr dispari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_3_b_missing_frame= Anomaly(
        device= bus.module.cam3_b,
        id=     'cam3_dispari_frame_mancante',
        descr=  'Camera 3 prr dispari: frame mancante',
        status= 'error'
    )
    cam_3_b_missing_trigger= Anomaly(
        device= bus.module.cam3_b,
        id=     'cam3_dispari_trigger_mancante',
        descr=  'Camera 3 prr dispari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam4_a_missing= Anomaly(
        device= bus.module.cam4_a,
        id=     'cam4_4_mancante',
        descr=  'Camera 4 prr 4 mancante',
        status= 'error'
    )
    cam4_a_fault= Anomaly(
        device= bus.module.cam4_a,
        id=     'cam4_4_guasta',
        descr=  'Camera 4 prr 4 guasta',
        status= 'error'
    )
    cam_4_a_error= Anomaly(
        device= bus.module.cam4_a,
        id=     'cam4_pari_error',
        descr=  'Camera 4 prr pari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_4_a_missing_frame= Anomaly(
        device= bus.module.cam4_a,
        id=     'cam4_pari_frame_mancante',
        descr=  'Camera 4 prr pari: frame mancante',
        status= 'error'
    )
    cam_4_a_missing_trigger= Anomaly(
        device= bus.module.cam4_a,
        id=     'cam4_pari_trigger_mancante',
        descr=  'Camera 4 prr pari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam4_b_missing= Anomaly(
        device= bus.module.cam4_b,
        id=     'cam4_4_mancante',
        descr=  'Camera 4 prr 4 mancante',
        status= 'error'
    )
    cam4_b_fault= Anomaly(
        device= bus.module.cam4_b,
        id=     'cam4_4_guasta',
        descr=  'Camera 4 prr 4 guasta',
        status= 'error'
    )
    cam_4_b_error= Anomaly(
        device= bus.module.cam4_b,
        id=     'cam4_dispari_error',
        descr=  'Camera 4 prr dispari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_4_b_missing_frame= Anomaly(
        device= bus.module.cam4_b,
        id=     'cam4_dispari_frame_mancante',
        descr=  'Camera 4 prr dispari: frame mancante',
        status= 'error'
    )
    cam_4_b_missing_trigger= Anomaly(
        device= bus.module.cam4_b,
        id=     'cam4_dispari_trigger_mancante',
        descr=  'Camera 4 prr dispari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam5_a_missing= Anomaly(
        device= bus.module.cam5_a,
        id=     'cam5_5_mancante',
        descr=  'Camera 5 prr 5 mancante',
        status= 'error'
    )
    cam5_a_fault= Anomaly(
        device= bus.module.cam5_a,
        id=     'cam5_5_guasta',
        descr=  'Camera 5 prr 5 guasta',
        status= 'error'
    )
    cam_5_a_error= Anomaly(
        device= bus.module.cam5_a,
        id=     'cam5_pari_error',
        descr=  'Camera 5 prr pari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_5_a_missing_frame= Anomaly(
        device= bus.module.cam5_a,
        id=     'cam5_pari_frame_mancante',
        descr=  'Camera 5 prr pari: frame mancante',
        status= 'error'
    )
    cam_5_a_missing_trigger= Anomaly(
        device= bus.module.cam5_a,
        id=     'cam5_pari_trigger_mancante',
        descr=  'Camera 5 prr pari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam5_b_missing= Anomaly(
        device= bus.module.cam5_b,
        id=     'cam5_5_mancante',
        descr=  'Camera 5 prr 5 mancante',
        status= 'error'
    )
    cam5_b_fault= Anomaly(
        device= bus.module.cam5_b,
        id=     'cam5_5_guasta',
        descr=  'Camera 5 prr 5 guasta',
        status= 'error'
    )
    cam_5_b_error= Anomaly(
        device= bus.module.cam5_b,
        id=     'cam5_dispari_error',
        descr=  'Camera 5 prr dispari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_5_b_missing_frame= Anomaly(
        device= bus.module.cam5_b,
        id=     'cam5_dispari_frame_mancante',
        descr=  'Camera 5 prr dispari: frame mancante',
        status= 'error'
    )
    cam_5_b_missing_trigger= Anomaly(
        device= bus.module.cam5_b,
        id=     'cam5_dispari_trigger_mancante',
        descr=  'Camera 5 prr dispari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam6_a_missing= Anomaly(
        device= bus.module.cam6_a,
        id=     'cam6_6_mancante',
        descr=  'Camera 6 prr 6 mancante',
        status= 'error'
    )
    cam6_a_fault= Anomaly(
        device= bus.module.cam6_a,
        id=     'cam6_6_guasta',
        descr=  'Camera 6 prr 6 guasta',
        status= 'error'
    )
    cam_6_a_error= Anomaly(
        device= bus.module.cam6_a,
        id=     'cam6_pari_error',
        descr=  'Camera 6 prr pari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_6_a_missing_frame= Anomaly(
        device= bus.module.cam6_a,
        id=     'cam6_pari_frame_mancante',
        descr=  'Camera 6 prr pari: frame mancante',
        status= 'error'
    )
    cam_6_a_missing_trigger= Anomaly(
        device= bus.module.cam6_a,
        id=     'cam6_pari_trigger_mancante',
        descr=  'Camera 6 prr pari: segnale di trigger non rilevato',
        status= 'error'
    )

    cam6_b_missing= Anomaly(
        device= bus.module.cam6_b,
        id=     'cam6_6_mancante',
        descr=  'Camera 6 prr 6 mancante',
        status= 'error'
    )
    cam6_b_fault= Anomaly(
        device= bus.module.cam6_b,
        id=     'cam6_6_guasta',
        descr=  'Camera 6 prr 6 guasta',
        status= 'error'
    )
    cam_6_b_error= Anomaly(
        device= bus.module.cam6_b,
        id=     'cam6_dispari_error',
        descr=  'Camera 6 prr dispari: errore interno, ma ancora in funzione',
        status= 'error'
    )
    cam_6_b_missing_frame= Anomaly(
        device= bus.module.cam6_b,
        id=     'cam6_dispari_frame_mancante',
        descr=  'Camera 6 prr dispari: frame mancante',
        status= 'error'
    )
    cam_6_b_missing_trigger= Anomaly(
        device= bus.module.cam6_b,
        id=     'cam6_dispari_trigger_mancante',
        descr=  'Camera 6 prr dispari: segnale di trigger non rilevato',
        status= 'error'
    )


"""
La seguente struttura dati raccoglie tutte le possibilii anomalie riscontrabili
osservando lo stato dei componenti ivip su Redis
La chiave Redis si ottiene a partire dal modulo e dal parametro interessato
La struttura è la seguente:
{
    modulo: {
        parametro: {
            valore_che_triggera_errore: anomalia
            ...
        }
        ...
    }
    ...
}
"""
status_errors_reference = {

    # MOSF TX A
    bus.module.mosf_tx_a: {
        bus.module.mosf_tx_a: {
            general.status_ko: definition.mtx_a_fault
        },
        bus.data_key.mtx_event: {
            bus.mtx_event.err_rimbalzo1: definition.mtx_a_rimb1,
            bus.mtx_event.err_rimbalzo2: definition.mtx_a_rimb2,
            bus.mtx_event.err_vel0_high: definition.mtx_a_vel0_h,
            bus.mtx_event.err_vel1_high: definition.mtx_a_vel1_h,
            bus.mtx_event.err_vel0_low: definition.mtx_a_vel0_l,
            bus.mtx_event.err_vel1_low: definition.mtx_a_vel1_l,
            bus.mtx_event.err_trigger0: definition.mtx_a_err_trig0,
            bus.mtx_event.err_trigger1: definition.mtx_a_err_trig1,
            bus.mtx_event.err_sens_vel1: definition.mtx_a_err_sens1,
            bus.mtx_event.err_sens_vel2: definition.mtx_a_err_sens2,
            bus.mtx_event.err_sens_vel1_2: definition.mtx_a_err_sens1_2
        }
    },

    # MOSF TX B
    bus.module.mosf_tx_b: {
        bus.module.mosf_tx_b: {
            general.status_ko: definition.mtx_b_fault
        },
        bus.data_key.mtx_event: {
            bus.mtx_event.err_rimbalzo1: definition.mtx_b_rimb1,
            bus.mtx_event.err_rimbalzo2: definition.mtx_b_rimb2,
            bus.mtx_event.err_vel0_high: definition.mtx_b_vel0_h,
            bus.mtx_event.err_vel1_high: definition.mtx_b_vel1_h,
            bus.mtx_event.err_vel0_low: definition.mtx_b_vel0_l,
            bus.mtx_event.err_vel1_low: definition.mtx_b_vel1_l,
            bus.mtx_event.err_trigger0: definition.mtx_b_err_trig0,
            bus.mtx_event.err_trigger1: definition.mtx_b_err_trig1,
            bus.mtx_event.err_sens_vel1: definition.mtx_b_err_sens1,
            bus.mtx_event.err_sens_vel2: definition.mtx_b_err_sens2,
            bus.mtx_event.err_sens_vel1_2: definition.mtx_b_err_sens1_2
        }
    },

    # MOSF RX
    bus.module.mosf_rx_a: {
        bus.module.mosf_rx_a: {
            general.status_ko: definition.mrx_a_fault
        },
    },
    bus.module.mosf_rx_b: {
        bus.module.mosf_rx_b: {
            general.status_ko: definition.mrx_b_fault
        },
    },

    # TRIGGER A
    bus.module.trigger_a: {
        bus.module.trigger_a: {
            general.status_ko: definition.trig_a_fault
        },
        bus.data_key.trig_flash_1_efficiency: {
            bus.data_val.flash_80: definition.trig_a_fl1_80,
            bus.data_val.flash_50: definition.trig_a_fl1_50,
            bus.data_val.flash_0: definition.trig_a_fl1_0,
        },
        bus.data_key.trig_flash_2_efficiency: {
            bus.data_val.flash_80: definition.trig_a_fl2_80,
            bus.data_val.flash_50: definition.trig_a_fl2_50,
            bus.data_val.flash_0: definition.trig_a_fl2_0,
        },
        bus.data_key.trig_flash_3_efficiency: {
            bus.data_val.flash_80: definition.trig_a_fl3_80,
            bus.data_val.flash_50: definition.trig_a_fl3_50,
            bus.data_val.flash_0: definition.trig_a_fl3_0,
        },
        bus.data_key.trig_flash_4_efficiency: {
            bus.data_val.flash_80: definition.trig_a_fl4_80,
            bus.data_val.flash_50: definition.trig_a_fl4_50,
            bus.data_val.flash_0: definition.trig_a_fl4_0,
        },
        bus.data_key.trig_flash_5_efficiency: {
            bus.data_val.flash_80: definition.trig_a_fl5_80,
            bus.data_val.flash_50: definition.trig_a_fl5_50,
            bus.data_val.flash_0: definition.trig_a_fl5_0,
        },
        bus.data_key.trig_flash_6_efficiency: {
            bus.data_val.flash_80: definition.trig_a_fl6_80,
            bus.data_val.flash_50: definition.trig_a_fl6_50,
            bus.data_val.flash_0: definition.trig_a_fl6_0,
        }
    },

    # TRIGGER B
    bus.module.trigger_b: {
        bus.module.trigger_b: {
            general.status_ko: definition.trig_b_fault
        },
        bus.data_key.trig_flash_1_efficiency: {
            bus.data_val.flash_80: definition.trig_b_fl1_80,
            bus.data_val.flash_50: definition.trig_b_fl1_50,
            bus.data_val.flash_0: definition.trig_b_fl1_0,
        },
        bus.data_key.trig_flash_2_efficiency: {
            bus.data_val.flash_80: definition.trig_b_fl2_80,
            bus.data_val.flash_50: definition.trig_b_fl2_50,
            bus.data_val.flash_0: definition.trig_b_fl2_0,
        },
        bus.data_key.trig_flash_3_efficiency: {
            bus.data_val.flash_80: definition.trig_b_fl3_80,
            bus.data_val.flash_50: definition.trig_b_fl3_50,
            bus.data_val.flash_0: definition.trig_b_fl3_0,
        },
        bus.data_key.trig_flash_4_efficiency: {
            bus.data_val.flash_80: definition.trig_b_fl4_80,
            bus.data_val.flash_50: definition.trig_b_fl4_50,
            bus.data_val.flash_0: definition.trig_b_fl4_0,
        },
        bus.data_key.trig_flash_5_efficiency: {
            bus.data_val.flash_80: definition.trig_b_fl5_80,
            bus.data_val.flash_50: definition.trig_b_fl5_50,
            bus.data_val.flash_0: definition.trig_b_fl5_0,
        },
        bus.data_key.trig_flash_6_efficiency: {
            bus.data_val.flash_80: definition.trig_b_fl6_80,
            bus.data_val.flash_50: definition.trig_b_fl6_50,
            bus.data_val.flash_0: definition.trig_b_fl6_0,
        }
    },

    # I/O
    bus.module.io: {
        bus.module.io: {
            general.status_ko: definition.io_fault
        },
        bus.data_key.io_alim_batt: {
            general.status_ko: definition.io_alim_batt
        },
        bus.data_key.io_alim_24: {
            general.status_ko: definition.io_alim_24v
        },
        bus.data_key.io_sw_armadio: {
            general.status_ko: definition.io_sw_armadio
        },
        # @TODO completare questi campi
        bus.data_key.io_rv_pari: {
            general.status_ko: definition.io_rv_pari
        },
        bus.data_key.io_sw_prr_pari: {
            general.status_ko: definition.io_sw_prr_pari
        },
        bus.data_key.io_rv_dispari: {
            general.status_ko: definition.io_rv_dispari
        },
        bus.data_key.io_sw_prr_dispari: {
            general.status_ko: definition.io_sw_prr_dispari
        }
    },

    # VIDEOSERVER
    bus.module.videoserver: {
        redis_keys.rip_status_field.sshfs_connected: {
            general.status_ko: definition.rip_sshfs
        },
        redis_keys.rip_status_field.broker_connected: {
            general.status_ko: definition.rip_kafka
        }
    },

    # CAMERAS
    bus.module.cam1_a: {
        bus.module.cam1_a: {
            general.status_ko: definition.cam1_a_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam1_a_fault,
            redis_keys.cam_status_field.error: definition.cam_1_a_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_1_a_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_1_a_missing_trigger,
        }
    },

    bus.module.cam1_b: {
        bus.module.cam1_b: {
            general.status_ko: definition.cam1_b_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam1_b_fault,
            redis_keys.cam_status_field.error: definition.cam_1_b_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_1_b_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_1_b_missing_trigger,
        }
    },

    bus.module.cam2_a: {
        bus.module.cam2_a: {
            general.status_ko: definition.cam2_a_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam2_a_fault,
            redis_keys.cam_status_field.error: definition.cam_2_a_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_2_a_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_2_a_missing_trigger,
        }
    },

    bus.module.cam2_b: {
        bus.module.cam2_b: {
            general.status_ko: definition.cam2_b_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam2_b_fault,
            redis_keys.cam_status_field.error: definition.cam_2_b_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_2_b_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_2_b_missing_trigger,
        }
    },

    bus.module.cam3_a: {
        bus.module.cam3_a: {
            general.status_ko: definition.cam3_a_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam3_a_fault,
            redis_keys.cam_status_field.error: definition.cam_3_a_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_3_a_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_3_a_missing_trigger,
        }
    },

    bus.module.cam3_b: {
        bus.module.cam3_b: {
            general.status_ko: definition.cam3_b_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam3_b_fault,
            redis_keys.cam_status_field.error: definition.cam_3_b_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_3_b_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_3_b_missing_trigger,
        }
    },

    bus.module.cam4_a: {
        bus.module.cam4_a: {
            general.status_ko: definition.cam4_a_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam4_a_fault,
            redis_keys.cam_status_field.error: definition.cam_4_a_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_4_a_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_4_a_missing_trigger,
        }
    },

    bus.module.cam4_b: {
        bus.module.cam4_b: {
            general.status_ko: definition.cam4_b_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam4_b_fault,
            redis_keys.cam_status_field.error: definition.cam_4_b_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_4_b_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_4_b_missing_trigger,
        }
    },

    bus.module.cam5_a: {
        bus.module.cam5_a: {
            general.status_ko: definition.cam5_a_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam5_a_fault,
            redis_keys.cam_status_field.error: definition.cam_5_a_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_5_a_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_5_a_missing_trigger,
        }
    },

    bus.module.cam5_b: {
        bus.module.cam5_b: {
            general.status_ko: definition.cam5_b_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam5_b_fault,
            redis_keys.cam_status_field.error: definition.cam_5_b_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_5_b_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_5_b_missing_trigger,
        }
    },

    bus.module.cam6_a: {
        bus.module.cam6_a: {
            general.status_ko: definition.cam6_a_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam6_a_fault,
            redis_keys.cam_status_field.error: definition.cam_6_a_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_6_a_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_6_a_missing_trigger,
        }
    },

    bus.module.cam6_b: {
        bus.module.cam6_b: {
            general.status_ko: definition.cam6_b_missing
        },
        redis_keys.cam_status_field.status: {
            general.status_ko: definition.cam6_b_fault,
            redis_keys.cam_status_field.error: definition.cam_6_b_error,
            redis_keys.cam_status_field.missing_frame: definition.cam_6_b_missing_frame,
            redis_keys.cam_status_field.missing_trigger: definition.cam_6_b_missing_trigger,
        }
    },
}


""" 
Dati di default per consentire il reset dei parametri di stato in Redis 
(anche quelli che non generano anomalie) 
"""
status_default = {
    bus.module.mosf_tx_a: {
        bus.module.mosf_tx_a: general.dato_non_disp,
        bus.data_key.mtx_vers: general.dato_non_disp,
        bus.data_key.mtx_event: general.dato_non_disp,
        bus.data_key.mtx_velo: general.dato_non_disp,
        bus.data_key.mtx_onoff: general.dato_non_disp
    },
    bus.module.mosf_tx_b: {
        bus.module.mosf_tx_b: general.dato_non_disp,
        bus.data_key.mtx_vers: general.dato_non_disp,
        bus.data_key.mtx_event: general.dato_non_disp,
        bus.data_key.mtx_velo: general.dato_non_disp,
        bus.data_key.mtx_onoff: general.dato_non_disp
    },
    bus.module.mosf_rx_a: {
        bus.module.mosf_rx_a: general.dato_non_disp,
        bus.data_key.mrx_vers: general.dato_non_disp,
        bus.data_key.mrx_event: general.dato_non_disp,
        bus.data_key.mosf_wire_t0: general.dato_non_disp,
        bus.data_key.mosf_wire_data_ok: general.dato_non_disp
    },
    bus.module.mosf_rx_b: {
        bus.module.mosf_rx_b: general.dato_non_disp,
        bus.data_key.mrx_vers: general.dato_non_disp,
        bus.data_key.mrx_event: general.dato_non_disp,
        bus.data_key.mosf_wire_t0: general.dato_non_disp,
        bus.data_key.mosf_wire_data_ok: general.dato_non_disp
    },
    bus.module.trigger_a: {
        bus.module.trigger_a: general.dato_non_disp,
        bus.data_key.trig_vers: general.dato_non_disp,
        bus.data_key.trig_flash_onoff: general.dato_non_disp,
        bus.data_key.trig_cam_onoff: general.dato_non_disp,
        bus.data_key.trig_flash_1_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_2_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_3_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_4_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_5_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_6_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_1_status: general.dato_non_disp,
        bus.data_key.trig_flash_2_status: general.dato_non_disp,
        bus.data_key.trig_flash_3_status: general.dato_non_disp,
        bus.data_key.trig_flash_4_status: general.dato_non_disp,
        bus.data_key.trig_flash_5_status: general.dato_non_disp,
        bus.data_key.trig_flash_6_status: general.dato_non_disp
    },
    bus.module.trigger_b: {
        bus.module.trigger_b: general.dato_non_disp,
        bus.data_key.trig_vers: general.dato_non_disp,
        bus.data_key.trig_flash_onoff: general.dato_non_disp,
        bus.data_key.trig_cam_onoff: general.dato_non_disp,
        bus.data_key.trig_flash_1_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_2_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_3_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_4_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_5_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_6_efficiency: general.dato_non_disp,
        bus.data_key.trig_flash_1_status: general.dato_non_disp,
        bus.data_key.trig_flash_2_status: general.dato_non_disp,
        bus.data_key.trig_flash_3_status: general.dato_non_disp,
        bus.data_key.trig_flash_4_status: general.dato_non_disp,
        bus.data_key.trig_flash_5_status: general.dato_non_disp,
        bus.data_key.trig_flash_6_status: general.dato_non_disp
    },
    bus.module.io: {
        bus.module.io: general.dato_non_disp,
        bus.data_key.io_vers: general.dato_non_disp,
        bus.data_key.io_alim_batt: general.dato_non_disp,
        bus.data_key.io_alim_24: general.dato_non_disp,
        bus.data_key.io_sw_armadio: general.dato_non_disp,
        bus.data_key.io_rv_pari: general.dato_non_disp,
        bus.data_key.io_sw_prr_pari: general.dato_non_disp,
        bus.data_key.io_rv_dispari: general.dato_non_disp,
        bus.data_key.io_sw_prr_dispari: general.dato_non_disp,
    },
    bus.module.videoserver: {
        redis_keys.rip_status_field.imgs_to_recover: general.dato_non_disp,
        redis_keys.rip_status_field.sshfs_connected: general.dato_non_disp,
        redis_keys.rip_status_field.broker_connected: general.dato_non_disp
    },
    bus.module.cam1_a: {
        bus.module.cam1_a: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam2_a: {
        bus.module.cam2_a: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam3_a: {
        bus.module.cam3_a: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam4_a: {
        bus.module.cam4_a: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam5_a: {
        bus.module.cam5_a: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam6_a: {
        bus.module.cam6_a: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam1_b: {
        bus.module.cam1_b: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam2_b: {
        bus.module.cam2_b: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam3_b: {
        bus.module.cam3_b: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam4_b: {
        bus.module.cam4_b: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam5_b: {
        bus.module.cam5_b: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    },
    bus.module.cam6_b: {
        bus.module.cam6_b: general.dato_non_disp,
        redis_keys.cam_status_field.status: general.dato_non_disp
    }
}


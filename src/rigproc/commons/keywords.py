#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lista stringhe ed elementi comuni
"""

from enum import Enum, unique, auto
import uuid


" VARIABILI D'AMBIENTE "

env_var_data_dir = f'RIG_DATA_DIR_{uuid.uuid4()}'


" TEMPORANEE "

cmd_ping= 'ping -c 1 192.168.2.101 2>&1 >/dev/null'


########################################
# KEYWORDS GENERICHE
########################################

" MODULI DEL SISTEMA "

mosf_tx_p= 'mosf_tx_pari'
mosf_tx_d= 'mosf_tx_dispari'

mosf_rx_p= 'mosf_rx_pari'
mosf_rx_d= 'mosf_rx_dispari'

trigger_p= 'trigger_pari'
trigger_d= 'trigger_dispari'

io= 'io'


" TIPO MODULI (senza binario) "

@unique
class module(Enum):
    mosf_tx= 'mosf_tx'
    mosf_rx= 'mosf_rx'
    trigger= 'trigger'
    io= 'io'


" KAFKA TOPICS "

topic_evt_trigger= 'EventoPassaggioTreno'
topic_diag_rip_to_stg= 'DiagnosiSistemiIVIP_RIPtoSTG'
topic_mosf_data= 'MOSFvalues'
topic_anomaly_alarm= 'AllarmeAnomaliaIVIP'
topic_int_set_upd_from_stg= 'AggiornamentoImpostazioni_STGtoRIP'
topic_int_set_upd_to_stg= 'AggiornamentoImpostazioni_RIPtoSTG'
topic_time_win_upd_from_stg= 'AggiornamentoFinestraInizioTratta_STGtoRIP'
topic_time_win_upd_to_stg= 'AggiornamentoFinestraInizioTratta_RIPtoSTG'
topic_sw_update_to_stg= 'AggiornamentoSW_RIPtoSTG'
topic_sw_update_from_stg= 'AggiornamentoSW_STGtoRIP'
topic_rip_subscription= 'IscrizioneRip_RIPtoSTG'


" ACTIONS INTERNE "

action_startup_done= 'startup_done'
action_shut_down_flow= 'shut_down_flow'
action_shut_down_aborted_flow= 'shut_down_aborted_flow'
action_shut_down= 'shut_down'
action_subscribe= 'subscribe'
action_periodic_flow= 'periodic_flow'
action_pause_periodic= 'pause_periodic'
action_diagnosis_flow= 'diagnosis_flow'
action_implant_status_flow= 'implant_status_flow'
action_anomaly_flow= 'anomaly_flow'
action_int_set_upd_flow= 'int_set_upd_flow'
action_time_win_upd_flow= 'time_win_upd_flow'
action_update_flow= 'update_flow'
action_wake_up= 'wake_up'
action_stop= 'stop'

action_trig= 'trig'


" CHIAVI AD USO GENERICO "

status_error= 'error'
status_ko= 'err'
status_ok= 'ok'
status_on= 'on' #
status_off= 'off' #
status_active= 'active' #
status_inactive= 'inactive' #

dato_non_disp= "not_available" #
dato_errato= "invalid" #

" CHIAVI DI TEST "

evt_trigger_test_name= 'evt_trigger_test_locale'


########################################
# CONFIGURAZIONE IMPIANTO
########################################

conf_data_hash_key= 'implant_data'
conf_data_status_key= 'status'
"RIP"
conf_rip_password= 'password'
conf_rip_config= 'configurazione'
conf_rip_name_key= 'nome_rip'
conf_plant_name_key= 'nome_ivip'
conf_plant_coord_key= 'coord_impianto'
conf_ip_remoto_key= 'ip_remoto'
" BINARIO E LINEA "
conf_line_name_key= 'nome_linea'
conf_prrA_key= 'prrA_bin'
conf_prrB_key= 'prrB_bin'
conf_loc_tratta_inizio_key= "loc_tratta_inizio"
conf_loc_tratta_fine_key= "loc_tratta_fine"
conf_cod_tratta_pari_key= 'cod_tratta_pari'
conf_cod_tratta_dispari_key= 'cod_tratta_dispari'
" SETTINGS "
conf_finestra_temp_pic_pari_key= 'finestra_temp_pic_pari'
conf_finestra_temp_pic_dispari_key= 'finestra_temp_pic_dispari'
conf_wire_calib_pari_key= 'wire_calib_pari'
conf_wire_calib_dispari_key= 'wire_calib_dispari'
conf_t_mosf_prrA_key= 't_mosf_prrA'
conf_t_mosf_prrB_key= 't_mosf_prrB'
conf_t_off_ivip_prrA_key= 't_off_ivip_prrA'
conf_t_off_ivip_prrB_key= 't_off_ivip_prrB'
" Configurazine camere "
conf_camera_fov_key='fov'
conf_camera_sensor_width_key= 'sensor_width'
conf_camera_focal_distance_key= 'focal_distance'
conf_camera_brand_key= 'camera_brand'
conf_camera_model_key= 'camera_model'

@unique
class bin_conf(str, Enum):
    doppio= 'binario_doppio'
    A= 'binario_prrA'
    B= 'binario_prrB'


########################################
# VALORI DI CONFIGURAZIONE
########################################

binario_conf_doppio= 'binario_doppio'
binario_conf_singolo= 'binario_singolo'



########################################
# JSON (RIP TO STG)
########################################

" COMMON MODEL "

" Event "
json_id= 'id'
json_recovered= 'recovered'
json_trans_id= 'transaction_id'
json_event_date= 'event_date'
json_event_time= 'event_time'
json_event_ts= 'event_timestamp'
json_trigger_id= 'trigger_id'
" Parameters "
json_parameters= 'parameters'
" RIP "
json_nome_rip= 'nome_rip'
json_ip_rip= 'ip_rip'
json_nome_imp= 'nome_impianto'
" Linea "
json_nome_linea= 'nome_linea'
json_loc_tratta_inizio= 'loc_tratta_inizio'
json_loc_tratta_fine= 'loc_tratta_fine'
json_cod_tratta_pari= 'cod_tratta_pari'
json_cod_tratta_dispari= 'cod_tratta_dispari'
" Binario "
json_prrA_bin= 'prrA_bin'
json_prrB_bin= 'prrB_bin'
" Settings "
json_wire_calib_pari= 'wire_calib_pari'
json_wire_calib_dispari= 'wire_calib_dispari'
json_tmosf_f= 'tmosf_f'
json_tmosf_l= 'tmosf_l'
json_fin_temp_pic_pari= 'finestra_temp_pic_pari'
json_fin_temp_pic_dispari= 'finestra_temp_pic_dispari'
" Cameras "
json_camera_fov= 'fov'
json_camera_sensor_width= 'sensor_width'
json_camera_focal_distance= 'focal_distance'
json_camera_brand= 'camera_brand'
json_camera_model= 'camera_model'
" t_mosf "
json_t_mosf_prrA= 't_mosf_prrA'
json_t_mosf_prrB= 't_mosf_prrB'
" t_off_ivip "
json_t_off_ivip_prrA= 't_off_ivip_prrA'
json_t_off_ivip_prrB= 't_off_ivip_prrB'

" FLOW MODEL (SUBSCRIPTION, TRIG, DIAGNOSIS, SW UPDATE) "

json_event_type= 'event_type'
json_on_trigger= 'on_trigger'
" Sw "
json_sw_version= 'sw_version'
" Images "
json_images= 'images'
json_inizio_upload= 'inizio_upload'
json_fine_upload= 'fine_upload'
json_names= 'names'
json_path= 'path'
" Images - EXIF "
json_exif= 'exif'
json_exif_fov= 'fov'
json_exif_sensor_width= 'sensor_width'
json_exif_focal_distance= 'focal_distance'
json_exif_camera_brand= 'camera_brand'
json_exif_camera_model= 'camera_model'
" Measure "
json_measures= 'measures'
json_wire_meas_t0= 'wire_measure_t0'
json_train_speed= 'train_speed'
json_train_direction= 'train_direction'
json_bin= 'binario'
" Status "
json_status= 'status'
" Cameras "
json_cameras= 'cameras'
json_cam_prrA= 'prrA'
json_cam_prrB= 'prrB'
" I/O "
json_io= 'io'
json_io_status= 'status'
json_io_name= 'name'
json_io_battery= 'battery'
json_io_ivip_alim= 'IVIP_power'
json_io_swc_prrA= 'switch_prrA'
json_io_swc_prrB= 'switch_prrB'
json_io_ldc_prrA= 'LdC_prrA'
json_io_ldc_prrB= 'LdC_prrB'
json_t_off_ivip_prrA= 't_off_ivip_prrA'
json_t_off_ivip_prrB= 't_off_ivip_prrB'
json_io_door= 'door_opened'
" I/O temperatures "
json_io_temperatures= 'temperatures'
json_io_sens1= 'sens1'
json_io_sens2= 'sens2'
" I/O ventilation "
json_io_ventilation= 'ventilation'
json_io_vent1= 'vent1'
json_io_vent2= 'vent2'
" Trigger A "
json_triggerA= 'triggerA'
json_trA_name= 'name'
" Trigger B "
json_triggerB= 'triggerB'
" Trigger "
json_trigger_status= 'status'
" Trigger flash "
json_fl_id= 'id'
json_flashes= 'flashes'
json_fl_status= 'status'
json_fl_eff= 'efficiency'
json_flash_1= 'flash_1'
json_flash_2= 'flash_2'
json_flash_3= 'flash_3'
json_flash_4= 'flash_4'
json_flash_5= 'flash_5'
json_flash_6= 'flash_6'
json_flash_ids= [json_flash_1, json_flash_2, json_flash_3,\
    json_flash_4, json_flash_5, json_flash_6]
" I/O MOSF "
json_mosf= 'mosf'
json_ms_id= 'id'
json_ms_status= 'status'

json_wire_t0= 'wire_measure_t0'
json_wire_data= 'wire_measures'
" Anomaly alarm "
json_alarm= 'allarme'
json_alarm_id= 'id_allarme'
json_alarm_decr= 'descrizione'
json_alarm_status= 'status'
" Settings update "
json_setupd_source= 'source'
json_dashboard_place= 'dashboard_place'
json_setupd_user_id= 'user_id'
json_rip_of_interest= 'rip_of_interest'
json_check= 'check'
json_update_settings= 'update_settings'
json_t_mosf_prrA= 't_mosf_prrA'
json_t_mosf_prrB= 't_mosf_prrB'
json_t_off_ivip_prrA= 't_off_ivip_prrA'
json_t_off_ivip_prrB= 't_off_ivip_prrB'
" SW Update "
json_scheduled_id= 'scheduled_id'
json_coord_imp= 'coord_imp'
" Update result "
json_update_result= 'update_result'
json_upd_start_date= 'start_date'
json_upd_start_time= 'start_time'
json_upd_end_date= 'end_date'
json_upd_end_time= 'end_time'
json_upd_version= 'update_version'
json_upd_status= 'status'
json_upd_error= 'error'


########################################
# JSON (STG TO RIP)
########################################

stg_event_type= 'event_type'
stg_source= 'source'
stg_dashboard_place= 'dashboard_place'
stg_user_id= 'user_id'
stg_id= 'id'
stg_transaction_id= 'transaction_id'
stg_event_date= 'event_date'
stg_event_time= 'event_time'
stg_event_timestamp= 'event_timestamp'
stg_rip_of_interest= 'rip_of_interest'
stg_update_settings= 'update_settings'
" Update internal settings "
stg_t_mosf_prrA= 't_mosf_prrA'
stg_t_mosf_prrB= 't_mosf_prrB'
stg_t_off_ivip_prrA= 't_off_ivip_prrA'
stg_t_off_ivip_prrB= 't_off_ivip_prrB'
" Update time window "
stg_fin_temp_pic_pari= 'finestra_temp_pic_pari'
stg_fin_temp_pic_dispari= 'finestra_temp_pic_dispari'
" Software update "
stg_update_parameters= 'update_parameters'
stg_update_date= 'date'
stg_update_time= 'time'
stg_update_package= 'package'
stg_update_version= 'version'


########################################
# FLOW INPUT DATA
########################################

# @TODO applicare ai vecchi riferimenti

flin_trans_id= 'transaction_id'
flin_id= 'id'

" Startup "
flin_start_timestamp_key= 'start_timestamp_key'
flin_term_msg_key= 'term_msg_key'

" Anomaly "
flin_alarm_id= 'alarm_id'
flin_alarm_descr= 'alarm_descr'
flin_alarm_status= 'alarm_status'

" Update internal settings "
flin_t_mosf_prrA= 't_mosf_prrA'
flin_t_mosf_prrB= 't_mosf_prrB'
flin_t_off_ivip_prrA= 't_off_ivip_prrA'
flin_t_off_ivip_prrB= 't_off_ivip_prrB'

" Update temporal window "
flin_fin_temp_pic_pari= 'finestra_temp_pic_pari'
flin_fin_temp_pic_dispari= 'finestra_temp_pic_dispari'

" Software update "
flin_schedule_date= 'schedule_date'
flin_schedule_time= 'schedule_time'
flin_remote_update_path= 'update_path'
flin_update_version= 'update_version'
flin_remote_update_folder= 'remote_update_folder'
flin_local_update_folder= 'local_update_folder'
flin_exec_folder= 'exec_folder'

" Restart for update "
flin_last_version_key= 'last_version_key'

" Request message "
flin_json_dict= 'json_dict'

" Trig flow testing "
flin_testing= 'testing'


########################################
# EVENT DATA (FLOW M_DATA)
########################################

" default values keys "

evdata_testing= 'testing'

evdata_prr= 'prr'
evdata_mosf_wire_t0= 'mosf_wire_t0'
evdata_train_speed= 'train_speed'
evdata_train_direction= 'train_direction'

evdata_mosfTXp_status= 'mosfTXp_status'
evdata_mosfRXp_status= 'mosfRXp_status'
evdata_mosfTXd_status= 'mosfTXd_status'
evdata_mosfRXd_status= 'mosfRXd_status'
evdata_t_mosfxA= 't_mosfxA'
evdata_t_mosfxB= 't_mosfxB'

evdata_triggerA_status= 'triggerA_status'
evdata_triggerB_status= 'triggerB_status'
evdata_flash_A= 'flash_A'
evdata_flash_B= 'flash_B'
evdata_io= 'io'
evdata_name= 'name'
evdata_battery= 'battery'
evdata_24vcc= '24vcc'
evdata_IVIP_power= 'IVIP_power'
evdata_switch_prrA= 'switch_prrA'
evdata_switch_prrB= 'switch_prrB'
evdata_ldc_prrA= 'ldc_prrA'
evdata_ldc_prrB= 'ldc_prrB'
evdata_t_mosf_prrA= 't_mosf_prrA'
evdata_t_mosf_prrB= 't_mosf_prrB'
evdata_t_off_ivip_prrA= 't_off_ivip_prrA'
evdata_t_off_ivip_prrB= 't_off_ivip_prrB'
evdata_fin_temp_pic_pari= 'fin_temp_pic_pari'
evdata_fin_temp_pic_dispari= 'fin_temp_pic_dispari'
evdata_door_opened= 'door_opened'
evdata_sens1= 'sens1'
evdata_sens2= 'sens2'
evdata_vent1= 'vent1'
evdata_vent2= 'vent2'
evdata_mosf_wire_data= 'mrx_wire_data'
evdata_mrx_wire_data_A= 'mrx_wire_data_A'
evdata_mrx_wire_data_B= 'mrx_wire_data_B'

" preliminary data keys "

evdata_on_trigger= 'on_trigger'
evdata_uuid= 'uuid'
evdata_timestamp= 'timestamp'
evdata_float_timestamp= 'float_timestamp'
evdata_date= 'date'
evdata_time= 'time'
evdata_recovered= 'recovered'
evdata_id= 'id'
evdata_binario= 'binario'
evdata_remoteDir= 'remoteDir'
evdata_localDir= 'localDir'
evdata_remote_dir_json= 'remote_dir_json'
evdata_evt_name= 'evt_name'
evdata_json_from_stg= 'json_from_stg'

" closing keys "

evdata_shutdown_confirmed= 'shutdown_confirmed'
evdata_restart_for_update= 'restart_for_update'

" diagnosi keys "

evdata_trig_status_A= 'trig_status_A'
evdata_trig_status_B= 'trig_status_B'
evdata_topic_evt_diag= 'topic_evt_diag'

" recover keys "

evdata_upload_started= 'upload_started'
evdata_upload_finished= 'upload_finished'
evdata_upload_is_completed= 'upload_is_completed'

" shutdown keys "

evdata_mtx_on_off= 'mtx_on_off'
evdata_mtxp_on_off= 'mtxp_on_off'
evdata_mtxd_on_off= 'mtxd_on_off'
evdata_sleeping_for= 'sleeping_for'

" startup keys "

evdata_sw_version= 'sw_version'
evdata_sw_update= 'sw_update'
evdata_topic_sw_update_done= 'topic_sw_update_done'

" settings update keys "

evdata_int_sett_upd_confirmed= 'int_sett_upd_confirmed'
evdata_time_win_upd_confirmed= 'time_win_upd_confirmed'

" sw update keys "

evdata_schedule_date= 'schedule_date'
evdata_schedule_time= 'schedule_time'
evdata_update_version= 'update_version'
evdata_transaction_id= 'transaction_id'

evdata_scheduled_confirmed= 'scheduled_confirmed'
evdata_topic_evt_sw_to_stg= 'topic_evt_sw_to_stg'
evdata_topic_anomaly_alarm= 'topic_anomaly_alarm'
evdata_topic_evt_intsettupd_to_stg= 'topic_evt_intsettupd_to_stg'
evdata_topic_evt_time_win_to_stg= 'topic_evt_time_win_to_stg'

" trig keys "

evdata_img= 'img'
evdata_imgs= 'imgs'
evdata_topic_evt= 'topic_evt'
evdata_topic_evt_mosf= 'topic_evt_mosf'

" anomaly keys "

evdata_alarm_id= 'id_allarme'
evdata_alarm_descr= 'descrizione'
evdata_alarm_status= 'status'

" subscription keys "

evdata_topic_subscription= 'topic_subscription'


########################################
# REDIS
########################################

" Stringhe di errore "
redis_error= dato_errato
redis_not_found= dato_non_disp

# Store msg in/out rilevati sul bus di comunicazione

key_cam_ready= 'camera_ready'

key_redis_msg_sorted_set= 'msg_sorted'
key_redis_msg_in=  'msg_in'
key_redis_msg_out= 'msg_out'

" FLOW START/STOP LOG "
key_flow_log= 'flow_log'
flow_start_time= 'flow_start_time'
flow_type= 'flow_type'
flow_stop_time= 'flow_end_time'
flow_errors= 'flow_errors'

" ERRORI "
key_bus_error= 'error'

" EVENTO "
key_cam_ready= 'camera_ready'

key_evt_trig_which_prr= 'which_prr'
key_prrA= 'prrA'
key_prrB= 'prrB'

key_evt_tr_id= "transaction_id"

key_evt_data= "event_date"
key_evt_time= "event_time"
key_img_name_0= "img_name_0"
key_img_data_0= "img_data_0"
key_img_name_1= "img_name_1"
key_img_data_1= "img_data_1"
key_img_name_2= "img_name_2"
key_img_data_2= "img_data_2"
key_img_name_3= "img_name_3"
key_img_data_3= "img_data_3"
key_img_name_4= "img_name_4"
key_img_data_4= "img_data_4"
key_img_name_5= "img_name_5"
key_img_data_5= "img_data_5"

topic_cmd_key= 'topic_response'

" IO "

key_io_missed_answer= 'missed'
key_io_another_answer= 'another'

" indirizzi moduli "

name_videoserver= "Videoserver"
name_io= "IO"
name_mtx_a= "MosfTX_p"
name_mtx_b= "MosfTX_d"
name_mrx_a= "MosfRX_p"
name_mrx_b= "MosfRX_d"
name_trig_a= "Trig_p"
name_trig_b= "Trig_d"

addr_videoserver= '@'
addr_io= 'A'
addr_mtx_a= 'B'
addr_mtx_b= 'C'
addr_mrx_a= 'D'
addr_mrx_b= 'E'
addr_trig_a= 'F'
addr_trig_b= 'G'

" start/stop/update RIG "
key_last_version= 'last_version'
key_start_timestamp= 'start_timestamp'

term_msg_exit= 'exit'
term_msg_reboot= 'reboot'
term_msg_shutdown= 'shutdown'


########################################
# BUS - COMANDI
########################################

"cmd generici, prefissi senza distinzione prr"
cmd_mrx_wire_t0_generic= 'mrx_wire_t0_'
cmd_mtx_vel_generic= 'mrx_vel_'
cmd_mrx_wire_data_gneric= 'mrx_wire_data_'

" cmd mnemonici, ad uso interno "
cmd_stop ='stop'
cmd_restart= 'restart'
cmd_mtx_vel_a= 'mtx_vel_a'
cmd_mtx_ver_a= 'mtx_ver_a'
cmd_mrx_ver_a= 'mrx_ver_a'
cmd_mtx_on_off_a= 'mtx_on_off_a'
cmd_mrx_wire_t0_a= 'mrx_wire_t0_a'
cmd_mrx_tmos_a= 'mrx_tmos_a'
cmd_mrx_wire_data_a = 'mrx_wire_data_a'
cmd_trig_ver_a= 'trig_ver_a'
cmd_trig_setting_a= 'trig_setting_a'
cmd_trig_on_off_a= 'trig_on_off_a'
cmd_trig_click_a= 'trig_click_a'
cmd_trig_status_a= 'trig_status_a'

cmd_mtx_vel_b= 'mtx_vel_b'
cmd_mtx_ver_b= 'mtx_ver_b'
cmd_mrx_ver_b= 'mrx_ver_b'
cmd_mtx_on_off_b= 'mtx_on_off_b'
cmd_mrx_wire_t0_b= 'mrx_wire_t0_b'
cmd_mrx_tmos_b= 'mrx_tmos_b'
cmd_mrx_wire_data_b = 'mrx_wire_data_b'
cmd_trig_ver_b= 'trig_ver_b'
cmd_trig_setting_b= 'trig_setting_b'
cmd_trig_on_off_b= 'trig_on_off_b'
cmd_trig_click_b= 'trig_click_b'
cmd_trig_status_b= 'trig_status_b'

cmd_mtx_vel_generic= 'mtx_vel_'

cmd_io_ver= 'io_ver'
cmd_io_test_batt= 'io_test_batt'
cmd_io= 'io'

static_remote_folder = '/data/shared/'

bus_data_len={
    4: 'P',
    8: 'Q',
    16: 'R',
    32: 'S',
    64: 'T',
    128: 'U',
    256: 'V',
    512: 'W',
    1024: 'X'
}

bus_cmds={
    cmd_mtx_ver_a: chr(96),
    cmd_mtx_vel_a: 'a',
    cmd_mtx_on_off_a: 'b',

    cmd_mrx_ver_a: chr(96),
    cmd_mrx_tmos_a: 'c',
    cmd_mrx_wire_t0_a: 'd',
    cmd_mrx_wire_data_a: 'e',

    cmd_trig_ver_a: chr(96),
    cmd_trig_setting_a: 'f',
    cmd_trig_on_off_a: 'g',
    cmd_trig_click_a: 'h',
    cmd_trig_status_a: 'i',

    cmd_mtx_ver_b: chr(96),
    cmd_mtx_vel_b: 'a',
    cmd_mtx_on_off_b: 'b',

    cmd_mrx_ver_b: chr(96),
    cmd_mrx_tmos_b: 'c',
    cmd_mrx_wire_t0_b: 'd',
    cmd_mrx_wire_data_b: 'e',

    cmd_trig_ver_b: chr(96),
    cmd_trig_setting_b: 'f',
    cmd_trig_on_off_b: 'g',
    cmd_trig_click_b: 'h',
    cmd_trig_status_b: 'i',

    cmd_io_ver: chr(96),
    cmd_io_test_batt: 'j',
    cmd_io: 'k'
}

bus_cmds_reverted= {
    name_videoserver:{},
    name_io: {
        chr(96):cmd_io_ver,
        'j': cmd_io_test_batt,
        'k': cmd_io
    },
    name_mtx_a: {
        chr(96):cmd_mtx_ver_a,
        'a' : cmd_mtx_vel_a,
        'b' : cmd_mtx_on_off_a
    },
    name_mtx_b: {
        chr(96):cmd_mtx_ver_b,
        'a' : cmd_mtx_vel_b,
        'b' : cmd_mtx_on_off_b
    },
    name_mrx_a: {
        chr(96):cmd_mrx_ver_a,
        'c': cmd_mrx_tmos_a,
        'd': cmd_mrx_wire_t0_a,
        'e': cmd_mrx_wire_data_a,
    },
    name_mrx_b: {
        chr(96):cmd_mrx_ver_b,
        'c': cmd_mrx_tmos_b,
        'd': cmd_mrx_wire_t0_b,
        'e': cmd_mrx_wire_data_b,
    },
    name_trig_a: {
        chr(96):cmd_trig_ver_a,
        'f': cmd_trig_setting_a,
        'g': cmd_trig_on_off_a,
        'h': cmd_trig_click_a,
        'i': cmd_trig_status_a,
    },
    name_trig_b: {
        chr(96):cmd_trig_ver_b,
        'f': cmd_trig_setting_b,
        'g': cmd_trig_on_off_b,
        'h': cmd_trig_click_b,
        'i': cmd_trig_status_b,
    },
}

" ASSOCIAZIONE DEVICES IO - CHIAVI "

" utilizzo la seguente struttura per definire le chiavi del redis "
" @todo che però non uso più giusto ? cmq da compeltare così non va mancano pari e dispari"
io_devices_keys= {
    'mosfTxA':[cmd_mtx_vel_a, cmd_mtx_ver_a,cmd_mtx_on_off_a],
    'mosfRxA':[cmd_mrx_ver_a,cmd_mrx_wire_t0_a, cmd_mrx_tmos_a, cmd_mrx_wire_data_a],
    'mosfTxB':[cmd_mtx_vel_b, cmd_mtx_ver_b ,cmd_mtx_on_off_b],
    'mosfRxB':[cmd_mrx_ver_b, cmd_mrx_wire_t0_b, cmd_mrx_tmos_b, cmd_mrx_wire_data_b],
    'triggerA':[cmd_trig_ver_a, cmd_trig_setting_a, cmd_trig_on_off_a, cmd_trig_click_a, cmd_trig_status_a],
    'triggerB':[cmd_trig_ver_b, cmd_trig_setting_b, cmd_trig_on_off_b, cmd_trig_click_b, cmd_trig_status_b],
    'io':[cmd_io_ver, cmd_io_test_batt, cmd_io],
}


########################################
# BUS 485 - CAMPI REQ/RES
########################################

" Dati rilevati dal bus485 "

data_mtx_vers_key= 'mtx_vers'
data_mtx_velo_key= 'mtx_velo'
data_mtx_direction_key= 'mtx_direction'
data_mtx_status_key= 'mtx_status' # Inutilizzato, status=ok se ricevo risposta a MOSF_TX Verisione (stessa cosa per MOSF_RX)
data_mtx_onoff_key= 'mtx_on_off'
data_mtx_event_key = 'mtx_event' #

data_mrx_vers_key= 'mrx_vers' #
data_mrx_direction_key = 'mrx_direction' #
data_mrx_event_key = 'mrx_event' #

data_mosf_tpre_key= 'mosf_tPre'
data_mosf_tpost_key= 'mosf_tPost'
data_mosf_wire_t0_key= 'mrx_wire_t0'
data_mosf_wire_data_key= 'mosf_wire_data'
data_mosf_wire_data_ok_key= 'mosf_wire_data_ok' #

data_trig_vers_key= 'trig_vers'
data_trig_latency= 'trig_flash_latency' #
data_trig_exposure= 'trig_flash_exposure' #
data_trig_click_key= 'trig_click'
data_trig_flash_1_status = 'flash_1_status'
data_trig_flash_2_status = 'flash_2_status'
data_trig_flash_3_status = 'flash_3_status'
data_trig_flash_4_status = 'flash_4_status'
data_trig_flash_5_status = 'flash_5_status'
data_trig_flash_6_status = 'flash_6_status'
data_trig_flash_1_efficiency = 'efficiency_flash_1' #
data_trig_flash_2_efficiency = 'efficiency_flash_2' #
data_trig_flash_3_efficiency = 'efficiency_flash_3' #
data_trig_flash_4_efficiency = 'efficiency_flash_4' #
data_trig_flash_5_efficiency = 'efficiency_flash_5' #
data_trig_flash_6_efficiency = 'efficiency_flash_6' #

data_io_vers_key = 'io_vers' # REV-4
data_io_key= 'io'
data_io_battery_key= 'io_battery'
data_io_alim_batt_key= 'alim_batt'
data_io_alim_24_key= 'alim_24vcc'
data_io_sw_armadio_key= 'sw_armadio'
data_io_rv_pari_key= 'rv_pari'
data_io_sw_prr_pari_key= 'sw_prr_pari'
data_io_rv_dispari_key= 'rv_dispari'
data_io_sw_prr_dispari_key= 'sw_prr_dispari'
data_io_ntc_c_key= 'ntc-c'
data_io_test_batt_key = 'io_test_batt' #

data_io_IVIP_power_key= 'io_ivip_power'# 
data_io_switch_prr_p_key= 'switch_prr_pari' #
data_io_switch_prr_d_key= 'switch_prr_dispari' #
data_io_ldc_p_key= 'ldc_prr_pari' # 
data_io_ldc_d_key= 'ldc_prr_dispari' # 
data_io_doors_key= 'door_opend' #
data_io_sens1_key= 'sens1' #
data_io_sens2_key= 'sens2' #
data_io_vent1_key= 'vent1' #
data_io_vent2_key= 'vent2' #


########################################
# BUS 485 - VALORI CAMPI REQ/RES
########################################

" COM data decoded keywords "

direction_legal= "legale"
direction_illegal= "illegale"
bin_pari= "pari"
bin_dispari= "dispari"
bin_unico= 'unico'

alim_batt= 'alim_battery'
alim_alim= 'alim_24vcc'

flash_0= '0' #
flash_50= '50' #
flash_80= '80' #
flash_100= '100' #

" event flow types "
flow_type_startup= 'flow_type_startup'
flow_type_subscription= 'flow_type_subscription'
flow_type_evt_trigger= 'flow_type_evt_trigger'
flow_type_diagnosis= 'flow_type_diagnosis'
flow_type_implant_status= 'flow_type_implant_status'
flow_type_recover= 'flow_type_recover'
flow_type_anomaly= 'flow_type_anomaly'
flow_type_int_sett_upd= 'flow_type_int_sett_upd'
flow_type_time_win_upd= 'flow_type_time_win_upd'
flow_type_sw_update= 'flow_type_update'
flow_type_shutdown= 'flow_type_shutdown'
flow_type_shutdown_aborted= 'flow_type_shutdown_aborted'
flow_type_power_check= 'flow_type_power_check'
flow_type_exit_update= 'flow_restart_process'

info_pipe_ended ='pipe_ended'

" flow data "
flow_start_key= 'flow_start'
flow_stop_key= 'flow_stop'

" Sw update schedule "

sw_update_hash_key= 'sw_update_schedule'
sw_update_date= 'update_date'
sw_update_time= 'update_time'
sw_update_version= 'update_version'
sw_update_transaction_id= 'transaction_id'
sw_update_req_id= 'request_id'
sw_update_mark_as_waiting= 'sw_update_waiting'

" MOSF TX events "
mtx_event_attesa_trigger= 'mtx_event_attesa_trigger' #
mtx_event_ok_trigger= 'mtx_event_ok_trigger' #
mtx_event_attesa_treno= 'mtx_event_attesa_treno' #
mtx_event_err_rimbalzo1= 'mtx_event_err_rimbalzo1' #
mtx_event_err_rimbalzo2= 'mtx_event_err_rimbalzo2' #
mtx_event_err_vel0_high= 'mtx_event_err_vel0_high' #
mtx_event_err_vel1_high= 'mtx_event_err_vel1_high' #
mtx_event_err_vel0_low= 'mtx_event_err_vel0_low' #
mtx_event_err_vel1_low= 'mtx_event_err_vel1_low' #
mtx_event_err_trigger0= 'mtx_event_err_trigger0' #
mtx_event_err_trigger1= 'mtx_event_err_trigger1' #
mtx_event_err_sens_vel1= 'mtx_event_err_sens_vel1' #
mtx_event_err_sens_vel2= 'mtx_event_err_sens_vel2' #
mtx_event_err_sens_vel1_2= 'mtx_event_err_sens_vel1_2' #

mtx_event_errors= [
    mtx_event_err_rimbalzo1,
    mtx_event_err_rimbalzo2,
    mtx_event_err_vel0_high,
    mtx_event_err_vel1_high,
    mtx_event_err_vel0_low,
    mtx_event_err_vel1_low,
    mtx_event_err_trigger0,
    mtx_event_err_trigger1,
    mtx_event_err_sens_vel1,
    mtx_event_err_sens_vel2,
    mtx_event_err_sens_vel1_2
]

" MOSF RX events "
mrx_event_attesa_trigger= 'mrx_event_attesa_trigger' #
mrx_event_ok_trigger= 'mrx_event_ok_trigger' #
mrx_event_attesa_treno= 'mrx_event_attesa_treno' #
mrx_event_err_all_outall= 'mrx_event_err_all_outall' #
mrx_event_err_all_outhigh= 'mrx_event_err_all_outhigh' #
mrx_event_err_all_outlow= 'mrx_event_err_all_outlow' #
mrx_event_err_all_unreliable= 'mrx_event_err_all_unreliable' #

" MOSF RX default TMOSF values "
default_tmosf_time= 25

" decoding binary decimals "
binary_decimal_zero = 0x30
binary_decimal_max = 0x39

" default values "
mosf_data_zero_value= 0x20
mosf_data_max_value= 0x7f
mosf_data_max_pre_time= 25 # secondi
mosf_data_max_post_time= 25 #


########################################
# MODULI - STATUS SU REDIS
########################################

" Status camere ? "

prrA_cam_id_key= 'camera_prrA_id_'
prrA_cam_status_key= 'camera_prrA_status_'
prrA_cam_ip_key= 'camera_prrA_ip_'

prrB_cam_id_key= 'camera_prrB_id_'
prrB_cam_status_key= 'camera_prrB_status_'
prrB_cam_ip_key= 'camera_prrB_ip_'


########################################
# CONSOLE
########################################

" CLIENT "
# Attenzione! Alcuni comandi corrispondono a delle stringhe presenti nel codice:
# NON cambiare i valori di queste keywords!
client_req_bus_cmd= 'bus_cmd'
client_req_trig_flow= 'trig_flow'
client_req_simulation= 'simulation'
client_req_check_term= 'check_term'
client_req_get_cache_data= 'get_cache_data'
client_req_delete_cache_data= 'delete_cache_data'
client_req_check_msg_sorted= 'check_msg_sorted'
client_req_status_param= 'status_param'
client_req_reset_status= 'reset_status'
client_req_conf= 'get_conf'
client_req_reset_conf= 'reset_conf'
client_req_subscription= 'subscription'

"""
Kafka parameters and keys
"""

from enum import Enum, unique


# TODO
@unique
class rip_topic(str, Enum):
	evt_trigger= 'EventoPassaggioTreno'
	diag_vip_to_stg= 'DiagnosiSistemiIVIP_RIPtoSTG'
	mosf_data= 'MOSFvalues'
	anomaly_alarm= 'AllarmeAnomaliaIVIP'
	int_set_upd_to_stg= 'AggiornamentoImpostazioni_RIPtoSTG'
	time_win_upd_to_stg= 'AggiornamentoFinestraInizioTratta_RIPtoSTG'
	sw_update_to_stg= 'AggiornamentoSW_RIPtoSTG'
	rip_subscription= 'IscrizioneRip_RIPtoSTG'


# TODO
@unique
class stg_topic(str, Enum):
	int_set_upd_from_stg= 'AggiornamentoImpostazioni_STGtoRIP'
	time_win_upd_from_stg= 'AggiornamentoFinestraInizioTratta_STGtoRIP'
	sw_update_from_stg= 'AggiornamentoSW_STGtoRIP'


# TODO
class rip_key(str, Enum):
	" COMMON MODEL "

	" Event "
	id= 'id'
	recovered= 'recovered'
	trans_id= 'transaction_id'
	event_date= 'event_date'
	event_time= 'event_time'
	event_ts= 'event_timestamp'
	trigger_id= 'trigger_id'
	" Parameters "
	parameters= 'parameters'
	" RIP "
	nome_rip= 'nome_rip'
	ip_rip= 'ip_rip'
	nome_imp= 'nome_impianto'
	" Linea "
	nome_linea= 'nome_linea'
	loc_tratta_inizio= 'loc_tratta_inizio' # to remove
	loc_tratta_fine= 'loc_tratta_fine' # to remove
	loc_tratta_pari_inizio= 'loc_tratta_pari_inizio'
	loc_tratta_pari_fine= 'loc_tratta_pari_fine'
	loc_tratta_dispari_inizio= 'loc_tratta_dispari_inizio'
	loc_tratta_dispari_fine= 'loc_tratta_dispari_fine'
	cod_tratta_pari= 'cod_tratta_pari' # to remove
	cod_tratta_dispari= 'cod_tratta_dispari' # to remove
	cod_pic_tratta_pari= 'cod_pic_tratta_pari'
	cod_pic_tratta_dispari= 'cod_pic_tratta_dispari'
	" Binario "
	prrA_bin= 'prrA_bin'
	prrB_bin= 'prrB_bin'
	" Settings "
	wire_calib_pari= 'wire_calib_pari'
	wire_calib_dispari= 'wire_calib_dispari'
	tmosf_f= 'tmosf_f'
	tmosf_l= 'tmosf_l'
	fin_temp_pic_pari= 'finestra_temp_pic_pari' # to remove
	fin_temp_pic_dispari= 'finestra_temp_pic_dispari' # to remove
	distanza_prr_IT_pari = 'distanza_prr_IT_pari'
	distanza_prr_IT_dispari = 'distanza_prr_IT_dispari'
	" Cameras "
	camera_fov= 'fov'
	camera_sensor_width= 'sensor_width'
	camera_focal_distance= 'focal_distance'
	camera_brand= 'camera_brand'
	camera_model= 'camera_model'

	" FLOW MODEL (SUBSCRIPTION, TRIG, DIAGNOSIS, SW UPDATE) "

	event_type= 'event_type'
	on_trigger= 'on_trigger'
	" Sw "
	sw_version= 'sw_version'
	" Images "
	images= 'images'
	inizio_upload= 'inizio_upload'
	fine_upload= 'fine_upload'
	names= 'names'
	path= 'path'
	" Images - EXIF "
	exif= 'exif'
	exif_fov= 'fov'
	exif_sensor_width= 'sensor_width'
	exif_focal_distance= 'focal_distance'
	exif_camera_brand= 'camera_brand'
	exif_camera_model= 'camera_model'
	" Measure "
	measures= 'measures'
	wire_meas_t0= 'wire_measure_t0'
	train_speed= 'train_speed'
	train_direction= 'train_direction'
	bin= 'binario'
	" Status "
	status= 'status'
	" Cameras "
	cameras= 'cameras'
	cam_prrA= 'prrA'
	cam_prrB= 'prrB'
	" I/O "
	io= 'io'
	io_status= 'status'
	io_name= 'name'
	io_battery= 'battery'
	io_ivip_alim= 'IVIP_power'
	io_swc_prrA= 'switch_prrA'
	io_swc_prrB= 'switch_prrB'
	io_ldc_prrA= 'LdC_prrA'
	io_ldc_prrB= 'LdC_prrB'
	t_off_ivip_prrA= 't_off_ivip_prrA'
	t_off_ivip_prrB= 't_off_ivip_prrB'
	io_door= 'door_opened'
	" I/O temperatures "
	io_temperatures= 'temperatures'
	io_sens1= 'sens1'
	io_sens2= 'sens2'
	" I/O ventilation "
	io_ventilation= 'ventilation'
	io_vent1= 'vent1'
	io_vent2= 'vent2'
	" Trigger A "
	triggerA= 'triggerA'
	trA_name= 'name'
	" Trigger B "
	triggerB= 'triggerB'
	" Trigger "
	trigger_status= 'status'
	" Trigger flash "
	fl_id= 'id'
	flashes= 'flashes'
	fl_status= 'status'
	fl_eff= 'efficiency'
	flash_1= 'flash_1'
	flash_2= 'flash_2'
	flash_3= 'flash_3'
	flash_4= 'flash_4'
	flash_5= 'flash_5'
	flash_6= 'flash_6'
	flash_ids= [flash_1, flash_2, flash_3,\
		flash_4, flash_5, flash_6]
	" I/O MOSF "
	mosf= 'mosf'
	ms_id= 'id'
	ms_status= 'status'

	wire_t0= 'wire_measure_t0'
	wire_data= 'wire_measures'
	" Anomaly alarm "
	alarm= 'allarme'
	alarm_id= 'id_allarme'
	alarm_decr= 'descrizione'
	alarm_status= 'status'
	" Settings update "
	setupd_source= 'source'
	dashboard_place= 'dashboard_place'
	setupd_user_id= 'user_id'
	rip_of_interest= 'rip_of_interest'
	check= 'check'
	update_settings= 'update_settings'
	t_mosf_prrA= 't_mosf_prrA'
	t_mosf_prrB= 't_mosf_prrB'
	" SW Update "
	scheduled_id= 'scheduled_id'
	coord_imp= 'coord_imp'
	" Update result "
	update_result= 'update_result'
	upd_start_date= 'start_date'
	upd_start_time= 'start_time'
	upd_end_date= 'end_date'
	upd_end_time= 'end_time'
	upd_version= 'update_version'
	upd_status= 'status'
	upd_error= 'error'


# TODO
@unique
class stg_key(str, Enum):
	event_type= 'event_type'
	source= 'source'
	dashboard_place= 'dashboard_place'
	user_id= 'user_id'
	id= 'id'
	transaction_id= 'transaction_id'
	event_date= 'event_date'
	event_time= 'event_time'
	event_timestamp= 'event_timestamp'
	rip_of_interest= 'rip_of_interest'
	update_settings= 'update_settings'
	" Update internal settings "
	t_mosf_prrA= 't_mosf_prrA'
	t_mosf_prrB= 't_mosf_prrB'
	t_off_ivip_prrA= 't_off_ivip_prrA'
	t_off_ivip_prrB= 't_off_ivip_prrB'
	" Update time window "
	fin_temp_pic_pari= 'finestra_temp_pic_pari'
	fin_temp_pic_dispari= 'finestra_temp_pic_dispari'
	" Software update "
	update_parameters= 'update_parameters'
	update_date= 'date'
	update_time= 'time'
	update_package= 'package'
	update_version= 'version'
"""
Internal keys (commands, flows, etc...)
"""

from enum import Enum, unique
import uuid


# TODO

" VARIABILI D'AMBIENTE "
class env(str, Enum):
	data_dir = f'RIG_DATA_DIR_{uuid.uuid4()}'
	rig_dir= f'RIG_DIR_{uuid.uuid4()}'

" CHIAVI DI TEST "
evt_trigger_test_name= 'evt_trigger_test_locale'


@unique
class cmd_key(str, Enum):
	cmd_type= 'cmd_type'
	evt_type= 'evt_type'
	evt_test= 'evt_test'
	evt_data= 'evt_data'
	io_cmd= 'io_cmd'
	says= 'says'

	# Topic cmds
	topic_type= 'topic_type'
	topic= 'topic'
	evt_name= 'evt_name'
	json= 'json'
	topic_response= 'topic_response'

	trigflow_instance= 'trigflow_instance'
	evt_to_recover= 'evt_to_recover'
	action_type= 'action_type'
	request_id= 'request_id'
	data= 'data'
	conf= 'conf'


@unique
class cmd_type(str, Enum):
	camera_evt= 'camera_evt'
	trig_flow= 'trig_flow'
	topic_evt= 'topic_evt'
	topic_response= 'topic_response'
	store_for_recovery= 'cmd_recover'
	recovery_flow= 'recovery_flow'
	recovery_success= 'recovery_success'
	recovery_failure= 'recovery_failure'
	action= 'cmd_action'
	reset_conf= 'reset_conf'
	reboot_rigcam= 'reboot_rigcam'
	renew_logs_flow= 'renew_logs'


# TODO
@unique
class action(str, Enum):
	shut_down_flow= 'shut_down_flow'
	shut_down_aborted_flow= 'shut_down_aborted_flow'
	shut_down= 'shut_down'
	subscribe= 'subscribe'
	periodic_flow= 'periodic_flow'
	pause_periodic= 'pause_periodic'
	diagnosis_flow= 'diagnosis_flow'
	implant_status_flow= 'implant_status_flow'
	anomaly_flow= 'anomaly_flow'
	int_set_upd_flow= 'int_set_upd_flow'
	time_win_upd_flow= 'time_win_upd_flow'
	update_flow= 'update_flow'
	wake_up= 'wake_up'
	stop= 'stop'
	trig= 'trig'


# TODO
@unique
class flow_input(str, Enum):
	trans_id= 'transaction_id'
	id= 'id'

	" Startup "
	start_timestamp_key= 'start_timestamp_key'
	term_msg_key= 'term_msg_key'

	" Anomaly "
	alarm_id= 'alarm_id'
	alarm_descr= 'alarm_descr'
	alarm_status= 'alarm_status'

	" Update internal settings "
	t_mosf_prrA= 't_mosf_prrA'
	t_mosf_prrB= 't_mosf_prrB'
	t_off_ivip_prrA= 't_off_ivip_prrA'
	t_off_ivip_prrB= 't_off_ivip_prrB'

	" Update temporal window "
	fin_temp_pic_pari= 'finestra_temp_pic_pari'
	fin_temp_pic_dispari= 'finestra_temp_pic_dispari'

	" Software update "
	schedule_date= 'schedule_date'
	schedule_time= 'schedule_time'
	remote_update_path= 'update_path'
	update_version= 'update_version'
	remote_update_folder= 'remote_update_folder'
	local_update_folder= 'local_update_folder'
	exec_folder= 'exec_folder'

	" Restart for update "
	last_version_key= 'last_version_key'

	" Request message "
	json_dict= 'json_dict'

	" Trig flow testing "
	testing= 'testing'

	event_data= 'event_data'


# TODO
@unique
class flow_data(str, Enum):
	" default values keys "

	testing= 'testing'

	prr= 'prr'
	mosf_wire_t0= 'mosf_wire_t0'
	train_speed= 'train_speed'
	train_direction= 'train_direction'

	mosfTXp_status= 'mosfTXp_status'
	mosfRXp_status= 'mosfRXp_status'
	mosfTXd_status= 'mosfTXd_status'
	mosfRXd_status= 'mosfRXd_status'
	t_mosfxA= 't_mosfxA'
	t_mosfxB= 't_mosfxB'

	triggerA_status= 'triggerA_status'
	triggerB_status= 'triggerB_status'
	flash_A= 'flash_A'
	flash_B= 'flash_B'
	io= 'io'
	name= 'name'
	battery= 'battery'
	IVIP_power= 'IVIP_power'
	switch_prrA= 'switch_prrA'
	switch_prrB= 'switch_prrB'
	ldc_prrA= 'ldc_prrA'
	ldc_prrB= 'ldc_prrB'
	t_mosf_prrA= 't_mosf_prrA'
	t_mosf_prrB= 't_mosf_prrB'
	t_off_ivip_prrA= 't_off_ivip_prrA'
	t_off_ivip_prrB= 't_off_ivip_prrB'
	fin_temp_pic_pari= 'fin_temp_pic_pari'
	fin_temp_pic_dispari= 'fin_temp_pic_dispari'
	door_opened= 'door_opened'
	rip_status= 'rip_status'
	io_ntc = 'io_ntc'
	alim_batt = 'alim_batt'
	sens1= 'sens1'
	sens2= 'sens2'
	vent1= 'vent1'
	vent2= 'vent2'
	mosf_wire_data= 'mrx_wire_data'
	mrx_wire_data_A= 'mrx_wire_data_A'
	mrx_wire_data_B= 'mrx_wire_data_B'

	" preliminary data keys "

	on_trigger= 'on_trigger'
	uuid= 'uuid'
	timestamp= 'timestamp'
	float_timestamp= 'float_timestamp'
	date= 'date'
	time= 'time'
	recovered= 'recovered'
	id= 'id'
	binario= 'binario'
	remoteDir= 'remoteDir'
	localDir= 'localDir'
	remote_dir_json= 'remote_dir_json'
	evt_name= 'evt_name'
	led= 'led'
	json_from_stg= 'json_from_stg'

	event_data= 'event_data'

	" closing keys "

	shutdown_confirmed= 'shutdown_confirmed'
	restart_for_update= 'restart_for_update'

	" diagnosi keys "

	conf_binario= 'conf_binario'
	trig_status_A= 'trig_status_A'
	trig_status_B= 'trig_status_B'
	topic_evt_diag= 'topic_evt_diag'

	" recover keys "

	upload_started= 'upload_started'
	upload_finished= 'upload_finished'
	upload_is_completed= 'upload_is_completed'

	" shutdown keys "

	mtx_on_off= 'mtx_on_off'
	mtxp_on_off= 'mtxp_on_off'
	mtxd_on_off= 'mtxd_on_off'
	trig_on_off= 'trig_on_off'
	trigp_on_off= 'trigp_on_off'
	trigd_on_off= 'trigd_on_off'
	sleeping_for= 'sleeping_for'

	" startup keys "

	sw_version= 'sw_version'
	sw_update= 'sw_update'
	topic_sw_update_done= 'topic_sw_update_done'

	" implant check keys "

	bin_setting= 'bin_setting'

	" settings update keys "

	int_sett_upd_confirmed= 'int_sett_upd_confirmed'
	time_win_upd_confirmed= 'time_win_upd_confirmed'

	" sw update keys "

	schedule_date= 'schedule_date'
	schedule_time= 'schedule_time'
	update_version= 'update_version'
	transaction_id= 'transaction_id'

	scheduled_confirmed= 'scheduled_confirmed'
	topic_evt_sw_to_stg= 'topic_evt_sw_to_stg'
	topic_anomaly_alarm= 'topic_anomaly_alarm'
	topic_evt_intsettupd_to_stg= 'topic_evt_intsettupd_to_stg'
	topic_evt_time_win_to_stg= 'topic_evt_time_win_to_stg'

	" trig keys "

	img= 'img'
	imgs= 'imgs'
	topic_evt= 'topic_evt'
	topic_evt_mosf= 'topic_evt_mosf'
	img_files= 'img_files'

	" anomaly keys "

	alarm_id= 'id_allarme'
	alarm_descr= 'descrizione'
	alarm_status= 'status'

	" subscription keys "

	topic_subscription= 'topic_subscription'


# TODO
@unique
class flow_type(str, Enum):
	startup= 'flow_type_startup'
	subscription= 'flow_type_subscription'
	evt_trigger= 'flow_type_evt_trigger'
	diagnosis= 'flow_type_diagnosis'
	implant_status= 'flow_type_implant_status'
	recover= 'flow_type_recover'
	anomaly= 'flow_type_anomaly'
	int_sett_upd= 'flow_type_int_sett_upd'
	time_win_upd= 'flow_type_time_win_upd'
	sw_update= 'flow_type_update'
	shutdown= 'flow_type_shutdown'
	shutdown_aborted= 'flow_type_shutdown_aborted'
	power_check= 'flow_type_power_check'
	exit_update= 'flow_restart_process'
	renew_logs = 'flow_type_renew_logs'


#TODO

info_pipe_ended ='pipe_ended'


# TODO
@unique
class client_req(str, Enum):
	# Attenzione! Alcuni comandi corrispondono a delle stringhe presenti nel codice:
	# NON cambiare i valori di queste keywords!
	bus_cmd= 'bus_cmd'
	trig_flow= 'trig_flow'
	simulation= 'simulation'
	check_term= 'check_term'
	get_cache_data= 'get_cache_data'
	delete_cache_data= 'delete_cache_data'
	check_msg_sorted= 'check_msg_sorted'
	status_param= 'status_param'
	reset_status= 'reset_status'
	conf= 'get_conf'
	reset_conf= 'reset_conf'
	subscription= 'subscription'
	bus_history= 'bus_history'
	reboot_rigcam= 'reboot_rigcam'
	mem_usage = 'mem_usage'
	uptime = 'uptime'
	shoot_count = 'shoot_count'
	temp_hist = 'temp_hist'


@unique
class cam_startup_error(str, Enum):
	conf_error= 'error_reading_configuration'
	

@unique
class cam_crash(str, Enum):
	no_cam_conn= 'no_camera_connected'			# No camera was detected during setup
	all_cam_lost= 'all_cameras_disconnected'	# All cameras disconnected during execution


@unique
class cam_error(str, Enum):
	cam_lost= 'camera_disconnected'				# The camera disconnected and its thread terminated
	unexpected_data= 'unexpected_data'			# The camera delivered data without announcing the trigger (impossible?)
	exec_error= 'exec_error'					# An error occurred during the camera loop execution (probably Vimba API error)
	less_triggers= 'less_triggers'				# The camera announced less triggers than the others
	missed_trigger= 'missed_trigger'			# The camera did not announce a trigger during this event
	missed_frame= 'missed_frame'				# The camera announced at least one trigger, but did not deliver the frame




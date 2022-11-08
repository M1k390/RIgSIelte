from enum import Enum, unique, auto
from typing import List, Dict, Optional
from rigproc.commons.redisi import get_redisI

from rigproc.flow.flow import Flow
from rigproc.flow.flow_diagnosis import FlowDiagnosis

from rigproc.commons.entities import CameraEvent, CameraShootArray, EventToRecover

from rigproc.commons.config import get_config

from rigproc.commons.wrappers import wrapkeys
from rigproc.commons.helper import helper
from rigproc.commons.jsonmodel import json_models

from rigproc.params import bus, general, internal, kafka

from rigproc.flow import eventtrigflow_buildcmd as buildcmd


@unique
class EventState(Enum):
	""" Represents the processing state of a shoot event """
	READY= 		auto()
	TO_RECOVER= auto()
	PROCESSED= 	auto()


class FlowCameraEvent(FlowDiagnosis, Flow):
	""" 
	Flow to process a camera event. 
	Can process more than one shoot event at once.
	"""
	def __init__(self, core, event_data: CameraEvent, request_id=None) -> None:
		Flow.__init__(self, internal.flow_type.evt_trigger, core, request_id)
		self.m_tasks= [
			# Cam stats
			self._increment_shoot_counter,
			# Event data
			self._bus_wire_t0,
			self._bus_wire_t0_response,
			self._bus_train_speed,
			self._bus_train_speed_response,
			# Diagnosis
			FlowDiagnosis._bus_io_alarms,
			FlowDiagnosis._bus_io_alarms_response,
			FlowDiagnosis._bus_io_ver,
			FlowDiagnosis._bus_io_ver_response,
			# Bus loop
			FlowDiagnosis._set_loop_diagnosis,
			FlowDiagnosis._set_bus_data,
			FlowDiagnosis._bus_mosf_tx_ver,
			FlowDiagnosis._bus_mosf_tx_ver_response,
			FlowDiagnosis._bus_mosf_rx_ver,
			FlowDiagnosis._bus_mosf_rx_ver_response,
			FlowDiagnosis._bus_trigger_alarms,
			FlowDiagnosis._bus_trigger_alarms_response,
			FlowDiagnosis._evaluate_loop_diagnosis,
			# Event data (continue)
			self._wait_mosf_data,
			self._bus_mosf_data,
			self._bus_mosf_data_response,
			# Shoot events loop
			self._set_loop_events,
			self._set_event_data,
			self._check_server_connection,
			self._create_remote_folder,
			self._copy_images,
			self._topic_event,
			self._topic_event_response,
			self._topic_diagnosis,
			self._topic_diagnosis_response,
			self._topic_mosf,
			self._topic_mosf_response,
			self._conclude_event,
			self._evaluate_loop_events,
			#
			Flow._close_pipe
		]
		FlowDiagnosis._set_data(self)
		self._set_data(event_data)

	def _set_data(self, event_data: CameraEvent):
		if isinstance(event_data, CameraEvent):
			self.m_event_data= event_data
			if event_data.pole == general.pole.prrA:
				self.m_binary= general.binario.pari
			else:
				self.m_binary= general.binario.dispari
		else:
			self.m_logger.critical(f'Tried to create a Camera Event Flow with an object that is not a Camera Event: {event_data}')
			self._error('Bad initialization')
			self.stop()
			return

		# Bus data
		self.m_wire_t0= general.dato_non_disp
		self.m_train_speed= general.dato_non_disp
		self.m_train_direction= general.dato_non_disp
		self.m_mosf_wire_data: Optional[list]= general.dato_non_disp

		# Events loop
		self.m_event_state= {shoot_array: EventState.READY for shoot_array in event_data.shoot_arrays}
		self.m_start_upload_time= {shoot_array: general.dato_non_disp for shoot_array in event_data.shoot_arrays}
		self.m_finish_upload_time= {shoot_array: general.dato_non_disp for shoot_array in event_data.shoot_arrays}
		self.m_remote_folder_name= {shoot_array: general.dato_non_disp for shoot_array in event_data.shoot_arrays}
		self.m_remote_folder_path= {shoot_array: general.dato_non_disp for shoot_array in event_data.shoot_arrays}
		self.m_trig_json_model= {shoot_array: general.dato_non_disp for shoot_array in event_data.shoot_arrays}
		self.m_diag_json_model= {shoot_array: general.dato_non_disp for shoot_array in event_data.shoot_arrays}
		self.m_mosf_json_model= {shoot_array: general.dato_non_disp for shoot_array in event_data.shoot_arrays}
		
		self.m_shoot_array: Optional[CameraShootArray]= None # Current shoot array
		self.m_events_loop_index= None						# Task index to perform the loop

		 # {timestamp: folder_path}
		self.m_events_to_recover: List[str]= []
		self.m_events_completed: List[str]= []

	
	# Event info generation

	def _get_event_id(self, shoot_array= None):
		if isinstance(shoot_array, CameraShootArray):
			ivip_name= get_config().main.implant_data.nome_ivip.get()
			return helper.clean_file_name(
				f'{shoot_array.timestamp}_{ivip_name}_{self.m_binary}_{self.m_train_direction}')
		else:
			return self.m_id
		
	def _get_event_uuid(self, shoot_array=None) -> str:
		if isinstance(shoot_array, CameraShootArray):
			return shoot_array.trans_id
		else:
			return self.m_uuid

	def _get_event_name(self, shoot_array= None) -> str:
		return f'evt_trigger_{self._get_event_uuid(shoot_array)}'


	# Tasks

	def _increment_shoot_counter(self):
		l_total_shoots = sum([len(s_a.shoots) for s_a in self.m_event_state.keys()])
		l_new_amount = get_redisI().increment_shoot_counter(l_total_shoots)
		if l_new_amount is not None:
			self.m_logger.info(f'Total shoots from boot: {l_new_amount}')
		else:
			self.m_logger.error('Error incrementing the shoot counter')
		self._step()

	def _bus_wire_t0(self):
		if self.m_event_data.pole == general.pole.prrA:
			bus_cmd= buildcmd._buildCmdWireT0A(self)
		else:
			bus_cmd= buildcmd._buildCmdWireT0B(self)
		self.m_command_queue.put(bus_cmd)
		self._step()
		self.pause()

	def _bus_wire_t0_response(self):
		if self._answer is not self._MISSED:
			self.m_wire_t0= wrapkeys.getValueDefault(
				self._answer,
				general.dato_non_disp,
				bus.data_key.mosf_wire_t0
			)
		else:
			self._warning(f'Missed answer to: bus_wire_t0')
		self._step()

	def _bus_train_speed(self):
		if self.m_event_data.pole == general.pole.prrA:
			bus_cmd= buildcmd._buildCmdTrainSpeedA(self)
		else:
			bus_cmd= buildcmd._buildCmdTrainSpeedB(self)
		self.m_command_queue.put(bus_cmd)
		self._step()
		self.pause()

	def _bus_train_speed_response(self):
		if self._answer is not self._MISSED:
			self.m_train_speed= wrapkeys.getValueDefault(
				self._answer,
				general.dato_non_disp,
				bus.data_key.mtx_velo
			)
			self.m_train_direction= wrapkeys.getValueDefault(
				self._answer,
				general.dato_non_disp,
				bus.data_key.mtx_direction
			)
		else:
			self._warning(f'Missed answer to: train_speed')
		self._step()

	def _wait_mosf_data(self):
		if get_config().main.settings.wait_mosf.get():
			mosf_time= 25
			latest_timestamp= max([shoot_array.timestamp for shoot_array in self.m_event_data.shoot_arrays])
			elapsed_time= (helper.timestampNowFloat() - int(latest_timestamp)) / 100
			if elapsed_time < mosf_time:
				self.m_logger.debug('Waiting for the mosf data to be ready...')
				self._sleep(mosf_time - elapsed_time)
			else:
				self.m_logger.debug(f'More than {mosf_time} seconds elapsed: mosf data is already available')
		else:
			self.m_logger.debug('Skipping due to configuration')
		self._step()

	def _bus_mosf_data(self):
		if self.m_event_data.pole == general.pole.prrA:
			bus_cmd= buildcmd._buildCmdMosfDataA(self)
		else:
			bus_cmd= buildcmd._buildCmdMosfDataB(self)
		self.m_command_queue.put(bus_cmd)
		self._step()
		self.pause()

	def _bus_mosf_data_response(self):
		if self._answer is not self._MISSED:
			mosf_data= wrapkeys.getValueDefault(self._answer, None, bus.data_key.mosf_wire_data)
			if get_config().main.settings.trim_mosf_data.get():
				if isinstance(mosf_data, list) and len(mosf_data) == 512:
					self.m_logger.debug('Trimming mosf data')
					if self.m_event_data.pole == general.pole.prrA:
						interval= get_config().main.implant_data.t_mosf_prrA.get()
					else:
						interval= get_config().main.implant_data.t_mosf_prrB.get()
					samples= int(interval * 10)
					if samples > 256:
						samples= 256
					self.m_logger.debug(f'Interval data type = {type(interval)}')
					self.m_logger.debug(f'Collecting {samples * 2} samples (interval = {interval})')
					mosf_data= mosf_data[256 - samples: 256 + samples]
				else:
					self.m_logger.error(f'Cannot trim mosf data. Leaving as it is: {mosf_data}')
			else:
				self.m_logger.debug('Skipping due to configuration')
			self.m_mosf_wire_data= mosf_data
		else:
			self._warning(f'Missed answer to: mosf_data')
		self._step()

	def _set_loop_events(self):
		self.m_events_loop_index= self._get_current_task() + 1
		self._start_looping()
		self._step()

	def _set_event_data(self):
		self.m_shoot_array= None
		self.m_logger.info(f'Current event state: {self.m_event_state}')
		for shoot_array, state in self.m_event_state.items():
			if state is not EventState.PROCESSED:
				self.m_shoot_array= shoot_array
				break
		if self.m_shoot_array is None:
			self.m_logger.error('No ready event found! Maybe no frame was downloaded?')

		self._step()

	def _check_server_connection(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return

		server_ip= get_config().main.sshfs.ip.get()
		server_online= helper.ping(server_ip)
		if not server_online:
			self.m_logger.error('The remote server is not online: cannot copy the images in the remote folder!')
			self.m_event_state[self.m_shoot_array] = EventState.TO_RECOVER
			self._error('Server offline')
			self._step()
			return

		self._step()

	def _create_remote_folder(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return

		# Check that SSHFS folder is mounted
		if not get_redisI().is_sshfs_mounted():
			self.m_logger.error('SSHFS not mounted: cannot copy images. Event to recover!')
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._step()
			return

		event_id= self._get_event_id(self.m_shoot_array)
		# Create remote folder
		remote_folder_name= event_id
		remote_folder_path= helper.join_paths(
			get_config().main.recovering.remote_folder.get(),
			remote_folder_name
		)
		self.m_remote_folder_name[self.m_shoot_array]= remote_folder_name
		self.m_remote_folder_path[self.m_shoot_array]= remote_folder_path
		remote_folder_exists= helper.dir_exists_create(remote_folder_path)
		if not remote_folder_exists:
			self.m_logger.error(f'Cannot create remote folder: {remote_folder_path}')
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._error('Cannot create remote folder')

		self._step()

	def _copy_images(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return

		# Check that SSHFS folder is mounted
		if not get_redisI().is_sshfs_mounted():
			self.m_logger.error('SSHFS not mounted: cannot copy images. Event to recover!')
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._step()
			return
		
		self.m_start_upload_time[self.m_shoot_array]= helper.timeNow()
		
		timestamp= self.m_shoot_array.timestamp
		event_id= self._get_event_id(self.m_shoot_array)
		remote_folder_path= self.m_remote_folder_path.get(self.m_shoot_array)

		files_copied= []
		for shoot in self.m_shoot_array.shoots:
			if not helper.file_exists(shoot.img_path):
				self.m_logger.error(f'The local image file {shoot.img_path} does not exist: it will be removed')
				self.m_shoot_array.shoots.remove(shoot)
				continue
			file_name= f'{event_id}_cam_{shoot.cam_num}'
			file_path= helper.join_paths(remote_folder_path, file_name)
			file_copied= helper.copy_file(shoot.img_path, file_path)
			files_copied.append(file_copied)
			if file_copied:
				self.m_logger.info(f'Image {shoot.img_path} copied to {file_path}')
				shoot.set_copy_path(file_path)
			else:
				self.m_logger.error(f'Cannot copy image file to {file_path}')
				break
		# Se non ci sono immagini da copiare, i dettagli dell'evento vengono inviati comunque
		if len(files_copied) > 0 and not all(files_copied):
			self.m_logger.error(f'Event {helper.timestamp_to_formatted(timestamp)} to recover because some errors occured copying the images')
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._error('Error copying files')
			
		self.m_finish_upload_time[self.m_shoot_array]= helper.timeNow()
		self._step()

	def _topic_event(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		
		data_dict= self._get_data_dict(self.m_shoot_array)
		json_model= json_models.getTrigModel(data_dict)
		self.m_trig_json_model[self.m_shoot_array]= json_model

		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping Kafka event sending')
			self._step()
			return

		topic_request_dict= {
			internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
			internal.cmd_key.topic_type:'trigger_topic_t0',
			internal.cmd_key.topic: kafka.rip_topic.evt_trigger,
			internal.cmd_key.evt_name: self._get_event_name(self.m_shoot_array),
			internal.cmd_key.json: json_model,
			internal.cmd_key.trigflow_instance: self
		}

		broker_address= get_config().broker.consume.broker.get()
		broker_online= helper.check_kafka_broker(broker_address)
		if broker_online:
			self.m_command_queue.put(topic_request_dict)
		else:
			self.m_logger.error('Cannot connect to Kafka broker: event to recover!')
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._step()
			return
		self._step()
		self.pause()

	def _topic_event_response(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return
		
		topic_sent= False
		if self._answer is not self._MISSED:
			response= wrapkeys.getValue(self._answer, internal.cmd_key.topic_response)
			if response == general.status_ok:
				self.m_logger.info('Topic correctly sent')
				topic_sent= True
			elif response == general.status_ko:
				self.m_logger.error('Error sending topic: event to recover!')
			else:
				self.m_logger.critical(f'Unknows response from Kafka broker: {self._answer}. Event to recover!')
		else:
			self.m_logger.critical(f'Missed answer to topic: event to recover!')
		if not topic_sent:
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._error('Missed answer to Kafka topic')
		self._step()

	def _topic_diagnosis(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		
		data_dict= self._get_data_dict(self.m_shoot_array)
		json_model= json_models.getDiagModel(data_dict)
		self.m_diag_json_model[self.m_shoot_array]= json_model

		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping Kafka event sending')
			self._step()
			return

		topic_request_dict= {
			internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
			internal.cmd_key.topic_type:'trigger_topic_diag',
			internal.cmd_key.topic: kafka.rip_topic.diag_vip_to_stg,
			internal.cmd_key.evt_name: self._get_event_name(self.m_shoot_array),
			internal.cmd_key.json: json_model,
			internal.cmd_key.trigflow_instance: self
		}
		broker_address= get_config().broker.consume.broker.get()
		broker_online= helper.check_kafka_broker(broker_address)
		if broker_online:
			self.m_command_queue.put(topic_request_dict)
		else:
			self.m_logger.error('Cannot connect to Kafka broker: event to recover!')
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._step()
			return
		self._step()
		self.pause()

	def _topic_diagnosis_response(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return
		
		topic_sent= False
		if self._answer is not self._MISSED:
			response= wrapkeys.getValue(self._answer, internal.cmd_key.topic_response)
			if response == general.status_ok:
				self.m_logger.info('Topic correctly sent')
				topic_sent= True
			elif response == general.status_ko:
				self.m_logger.error('Error sending topic: event to recover!')
			else:
				self.m_logger.critical(f'Unknows response from Kafka broker: {self._answer}. Event to recover!')
		else:
			self.m_logger.critical(f'Missed answer to topic: event to recover!')
		if not topic_sent:
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._error('Missed answer to Kafka topic')
		self._step()

	def _topic_mosf(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		
		data_dict= self._get_data_dict(self.m_shoot_array)
		json_model= json_models.getMosfDataModel(data_dict)
		self.m_mosf_json_model[self.m_shoot_array]= json_model

		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping Kafka event sending')
			self._step()
			return
		
		topic_request_dict= {
			internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
			internal.cmd_key.topic_type:'trigger_topic_evt',
			internal.cmd_key.topic: kafka.rip_topic.mosf_data,
			internal.cmd_key.evt_name: self._get_event_name(self.m_shoot_array),
			internal.cmd_key.json: json_model,
			internal.cmd_key.trigflow_instance: self
		}
		broker_address= get_config().broker.consume.broker.get()
		broker_online= helper.check_kafka_broker(broker_address)
		if broker_online:
			self.m_command_queue.put(topic_request_dict)
		else:
			self.m_logger.error('Cannot connect to Kafka broker: event to recover!')
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._step()
			return

		self._step()
		self.pause()

	def _topic_mosf_response(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return
		
		topic_sent= False
		if self._answer is not self._MISSED:
			response= wrapkeys.getValue(self._answer, internal.cmd_key.topic_response)
			if response == general.status_ok:
				self.m_logger.info('Topic correctly sent')
				topic_sent= True
			elif response == general.status_ko:
				self.m_logger.error('Error sending topic: event to recover!')
			else:
				self.m_logger.critical(f'Unknows response from Kafka broker: {self._answer}. Event to recover!')
		else:
			self.m_logger.critical(f'Missed answer to topic: event to recover!')
		if not topic_sent:
			self.m_event_state[self.m_shoot_array]= EventState.TO_RECOVER
			self._error('Missed answer to Kafka topic')
		self._step()

	def _conclude_event(self):
		if self.m_event_state.get(self.m_shoot_array) is EventState.READY:
			for shoot in self.m_shoot_array.shoots:
				helper.remove_file(shoot.img_path)
		elif self.m_event_state.get(self.m_shoot_array) is EventState.TO_RECOVER:
			self._error(f'Event {self.m_shoot_array.timestamp} to recover')

			# Remove remote files/dirs if already created
			for shoot in self.m_shoot_array.shoots:
				if shoot.copy_path is not None and helper.file_exists(shoot.copy_path):
					helper.remove_file(shoot.copy_path)
			remote_folder_path= self.m_remote_folder_path.get(self.m_shoot_array)
			if helper.dir_exists(remote_folder_path):
				helper.remove_dir(remote_folder_path)
		
			# Send recovery request
			recovery_store_request= {
				internal.cmd_key.cmd_type: internal.cmd_type.store_for_recovery,
				internal.cmd_key.evt_to_recover: EventToRecover(
					self.m_shoot_array,
					self._get_event_id(self.m_shoot_array),
					self.m_remote_folder_name.get(self.m_shoot_array),
					self.m_trig_json_model.get(self.m_shoot_array),
					self.m_diag_json_model.get(self.m_shoot_array),
					self.m_mosf_json_model.get(self.m_shoot_array)
				)
			}
			self.m_command_queue.put(recovery_store_request)
		self.m_event_state[self.m_shoot_array]= EventState.PROCESSED
		self._step()

	def _evaluate_loop_events(self):
		for state in self.m_event_state.values():
			if state is EventState.READY:
				self._jump(self.m_events_loop_index)
				return
		self._stop_looping()
		self._step()

	
	# Compatibility

	def _get_data_dict(self, shoot_array: Optional[CameraShootArray]=None) -> dict:
		""" Generates Flow internal data dict (compatibility with old implementation and json models) """
		data_dict= super()._get_data_dict()
		data_dict.update({
			internal.flow_data.id: self._get_event_id(shoot_array),
			internal.flow_data.uuid: self._get_event_uuid(shoot_array),
			internal.flow_data.binario: self.m_binary,
			internal.flow_data.recovered: 'false',
			internal.flow_data.upload_started: wrapkeys.getValueDefault(
				self.m_start_upload_time,
				general.dato_non_disp,
				shoot_array
			),
			internal.flow_data.upload_finished: wrapkeys.getValueDefault(
				self.m_finish_upload_time,
				general.dato_non_disp,
				shoot_array
			),
			internal.flow_data.img_files: [
				helper.file_name_from_path(shoot.copy_path)
				for shoot in shoot_array.shoots 
				if shoot.copy_path is not None
			] if isinstance(shoot_array, CameraShootArray) else [],
			internal.flow_data.remote_dir_json: wrapkeys.getValueDefault(
				self.m_remote_folder_name, general.dato_non_disp, shoot_array),
			internal.flow_data.on_trigger: True,
			internal.flow_data.mosf_wire_data: {
				bus.data_key.mosf_wire_t0: self.m_wire_t0,
				bus.data_key.mosf_wire_data: self.m_mosf_wire_data
			}
		})
		return data_dict
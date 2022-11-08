from typing import Optional

from rigproc.flow.flow import Flow
from rigproc.flow.flow_camera_event import FlowCameraEvent, EventState

from rigproc.commons.entities import CameraEvent, CameraShootArray, EventToRecover

from rigproc.commons.config import get_config
from rigproc.commons.jsonmodel import json_models
from rigproc.commons.helper import helper

from rigproc.params import internal, kafka


class FlowRecovery(FlowCameraEvent, Flow):
	"""
	Flow to execute a shoot event recovery.
	"""
	def __init__(self, core, event_to_recover: EventToRecover, request_id=None) -> None:
		Flow.__init__(self, internal.flow_type.recover, core, request_id)
		self.m_tasks= [
			FlowCameraEvent._create_remote_folder,
			FlowCameraEvent._copy_images,
			self._topic_event_recover,
			FlowCameraEvent._topic_event_response,
			self._topic_diagnosis_recover,
			FlowCameraEvent._topic_diagnosis_response,
			self._topic_mosf_recover,
			FlowCameraEvent._topic_mosf_response,
			self._conclude_recovery,
			#
			Flow._close_pipe
		]
		FlowCameraEvent._set_data(self, CameraEvent(None, [event_to_recover.shoot_array]))
		self._set_data(event_to_recover)

	def _set_data(self, event_to_recover: EventToRecover):
		self.m_event_to_recover= event_to_recover
		self.m_shoot_array= event_to_recover.shoot_array
		self.m_event_id= event_to_recover.event_id
		self.m_remote_folder_name[self.m_shoot_array]= event_to_recover.remote_folder_name
		self.m_remote_folder_path[self.m_shoot_array]= helper.join_paths(
			get_config().main.recovering.remote_folder.get(),
			event_to_recover.remote_folder_name
		)
		self.m_trig_json_model= event_to_recover.trig_json_model
		self.m_diag_json_model= event_to_recover.diag_json_model
		self.m_mosf_json_model= event_to_recover.mosf_json_model

	def _get_event_id(self, shoot_array=None):
		return self.m_event_id

	def _topic_event_recover(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state[self.m_shoot_array] is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return
		
		json_model= json_models.recoverTrigModel(
			self.m_trig_json_model,
			self._get_data_dict(self.m_shoot_array)
		)
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

	def _topic_diagnosis_recover(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state[self.m_shoot_array] is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return
		
		json_model= json_models.recoverDiagModel(
			self.m_diag_json_model,
			self._get_data_dict(self.m_shoot_array)
		)
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

	def _topic_mosf_recover(self):
		if not isinstance(self.m_shoot_array, CameraShootArray):
			self.m_logger.error('Internal error: skipping task')
			self._step()
			return
		if self.m_event_state[self.m_shoot_array] is EventState.TO_RECOVER:
			self.m_logger.error('Event to recover: skipping task')
			self._step()
			return
		
		json_model= json_models.recoverMosfModel(
			self.m_mosf_json_model,
			self._get_data_dict(self.m_shoot_array)
		)
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

	def _conclude_recovery(self):
		if self.m_event_state[self.m_shoot_array] is EventState.TO_RECOVER:
			self.m_logger.warning('Recovery failed: asking to keep the event to recover')
			self.m_warnings.append(f'Event {self.m_shoot_array.timestamp} to recover')
			recovery_outcome= {
				internal.cmd_key.cmd_type: internal.cmd_type.recovery_failure,
				internal.cmd_key.evt_to_recover: self.m_event_to_recover
			}
		else:
			self.m_logger.info('Recovery succeded: asking to remove the event to recover')
			for shoot in self.m_shoot_array.shoots:
				helper.remove_file(shoot.img_path)
			recovery_outcome= {
				internal.cmd_key.cmd_type: internal.cmd_type.recovery_success,
				internal.cmd_key.evt_to_recover: self.m_event_to_recover
			}
		self.m_command_queue.put(recovery_outcome)
		self._step()


	# Compatibility

	def _get_data_dict(self, shoot_array: Optional[CameraShootArray]=None) -> dict:
		""" Generates Flow internal data dict (compatibility with old implementation and json models) """
		data_dict= FlowCameraEvent._get_data_dict(self, shoot_array)
		data_dict.update({
			internal.flow_data.recovered: True
		})
		return data_dict
	
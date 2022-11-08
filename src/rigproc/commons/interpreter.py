"""
This module provides the methods to encode and decode messages to/from the camera process.
"""


from dataclasses import dataclass
import logging
import json
from typing import Optional, Tuple, List

from rigproc.commons.config import get_config

from rigproc.commons.helper import helper
from rigproc.commons.wrappers import wrapkeys
from rigproc.commons.logger import logging_manager

from rigproc.commons.entities import CameraShoot, CameraShootArray, CameraEvent
from rigproc.params import redis_keys, conf_values


#
# COMMUNICATION ENTITIES
#

class ProcConf:
	def __init__(
		self, 
		local_dir, 
		simultaneous_dls, 
		trigger_timeout, 
		max_frame_dl_time, 
		event_timeout
	):
		self.local_dir= local_dir
		self.simultaneous_dls= simultaneous_dls
		self.trigger_timeout= trigger_timeout
		self.max_frame_dl_time= max_frame_dl_time
		self.event_timeout= event_timeout

@dataclass
class LoggingConf:
	format_code: str
	formatter: str
	console_level: int
	file_level: int
	file_dir: str
	file_name: str
	file_mode: str
	log_to_root: bool
	root_file_prefix: str
	root_dir: str
	session_ts: str

class CameraConf:
	def __init__(self, id, ip, pole, num, xml):
		self.id= id
		self.ip= ip
		self.pole= pole
		self.num= num
		self.xml= xml


class CameraError:
	def __init__(self, cam_id, running, error_msg):
		self.cam_id= cam_id
		self.running= running
		self.error_msg= error_msg
	def __repr__(self) -> str:
		return f'Error cam {self.cam_id}: {"still running" if self.running else "stop"} -> {self.error_msg}'


#
# THE INTERPRETER
#

class Interpreter:

	def __init__(self) -> None:
		self.m_logger= logging.getLogger('root')

	def set_logger(self, logger_name):
		self.m_logger= logging.getLogger(logger_name)

	
	# SETUP

	def encode_setup_message(self) -> Optional[str]:
		l_config= get_config()
		if l_config is None:
			self.m_logger.error('The configuration was not initialized: cannot encode setup message for the camera process')
			return None
		proc_conf_dict= {
			redis_keys.cam_setup.local_dir: l_config.main.recovering.local_folder.get(),
			redis_keys.cam_setup.simultaneous_dls: l_config.camera.simultaneous_dls.get(),
			redis_keys.cam_setup.trigger_timeout: l_config.camera.trigger_timeout.get(),
			redis_keys.cam_setup.max_frame_dl_time: l_config.camera.max_frame_dl_time.get(),
			redis_keys.cam_setup.event_timeout: l_config.camera.event_timeout.get()
		}

		logging_conf_dict= {
			redis_keys.cam_setup.format_code: l_config.logging.camera.format.get(),
			redis_keys.cam_setup.formatter: l_config.logging.camera.formatter.get(),
			redis_keys.cam_setup.console_level: l_config.logging.camera.console_level.get(),
			redis_keys.cam_setup.file_level: l_config.logging.camera.file_level.get(),
			redis_keys.cam_setup.file_dir: l_config.logging.camera.file_dir.get(),
			redis_keys.cam_setup.file_name: l_config.logging.camera.file_name.get(),
			redis_keys.cam_setup.file_mode: l_config.logging.camera.file_mode.get(),
			redis_keys.cam_setup.log_to_root: l_config.logging.camera.log_to_root.get(),
			redis_keys.cam_setup.root_file_prefix: l_config.logging.root.file_name.get(),
			redis_keys.cam_setup.root_dir: l_config.logging.root.file_dir.get(),
			redis_keys.cam_setup.session_ts: logging_manager.get_session_timestamp()
		}
		cameras= []
		prrA_info= l_config.camera.ids.prrA
		prrA_ids= [
			prrA_info.id_1.get(), prrA_info.id_2.get(), prrA_info.id_3.get(), 
			prrA_info.id_4.get(), prrA_info.id_5.get(), prrA_info.id_6.get()
		]
		prrA_ips= [
			prrA_info.ip_1.get(), prrA_info.ip_2.get(), prrA_info.ip_3.get(), 
			prrA_info.ip_4.get(), prrA_info.ip_5.get(), prrA_info.ip_6.get()
		]
		prrA_xml = l_config.camera.xml_files.prrA
		prrA_xml_files=[
			prrA_xml.xml_1.get(), prrA_xml.xml_2.get(), prrA_xml.xml_3.get(), 
			prrA_xml.xml_4.get(), prrA_xml.xml_5.get(), prrA_xml.xml_6.get()
		]
		for cam_idx, (cam_id, cam_ip, xml_file) in enumerate(zip(prrA_ids, prrA_ips, prrA_xml_files)):
			if cam_id != '':
				cameras.append({
					redis_keys.cam_setup.cam_id: cam_id,
					redis_keys.cam_setup.cam_ip: cam_ip,
					redis_keys.cam_setup.cam_pole: conf_values.prr.prrA,
					redis_keys.cam_setup.cam_num: cam_idx + 1,
					redis_keys.cam_setup.cam_xml: xml_file,
				})
		if l_config.main.implant_data.configurazione.get() == conf_values.binario.doppio:
			prrB_info= l_config.camera.ids.prrB
			prrB_ids= [
				prrB_info.id_1.get(), prrB_info.id_2.get(), prrB_info.id_3.get(), 
				prrB_info.id_4.get(), prrB_info.id_5.get(), prrB_info.id_6.get()
			]
			prrB_ips= [
				prrB_info.ip_1.get(), prrB_info.ip_2.get(), prrB_info.ip_3.get(), 
				prrB_info.ip_4.get(), prrB_info.ip_5.get(), prrB_info.ip_6.get()
			]
			prrB_xml = l_config.camera.xml_files.prrB
			prrB_xml_files=[
				prrB_xml.xml_1.get(), prrB_xml.xml_2.get(), prrB_xml.xml_3.get(), 
				prrB_xml.xml_4.get(), prrB_xml.xml_5.get(), prrB_xml.xml_6.get()
			]
			for cam_idx, (cam_id, cam_ip, xml_file) in enumerate(zip(prrB_ids, prrB_ips, prrB_xml_files)):
				if cam_id != '':
					cameras.append({
						redis_keys.cam_setup.cam_id: cam_id,
						redis_keys.cam_setup.cam_ip: cam_ip,
						redis_keys.cam_setup.cam_pole: conf_values.prr.prrB,
						redis_keys.cam_setup.cam_num: cam_idx + 1,
						redis_keys.cam_setup.cam_xml: xml_file
					})
		cameras_conf_dict= {
			redis_keys.cam_setup.cameras: cameras
		}
		setup_dict= {
			redis_keys.cam_setup.proc_key: proc_conf_dict,
			redis_keys.cam_setup.logging_key: logging_conf_dict,
			redis_keys.cam_setup.cam_key: cameras_conf_dict
		}
		try:
			return json.dumps(setup_dict)
		except Exception as e:
			self.m_logger.error(f'An error occurred dumping the setup message for the camera process ({type(e)}): {e}')
			return None

	def decode_proc_conf(self, setup_msg: str) -> Optional[ProcConf]:
		try:
			setup_dict= json.loads(setup_msg)
			proc_dict= setup_dict[redis_keys.cam_setup.proc_key]
			proc_conf= ProcConf(
				local_dir= 			proc_dict[redis_keys.cam_setup.local_dir],
				simultaneous_dls= 	proc_dict[redis_keys.cam_setup.simultaneous_dls],
				trigger_timeout= 	proc_dict[redis_keys.cam_setup.trigger_timeout],
				max_frame_dl_time= 	proc_dict[redis_keys.cam_setup.max_frame_dl_time],
				event_timeout= 	proc_dict[redis_keys.cam_setup.event_timeout]
			)
		except Exception as e:
			self.m_logger.error(f'Error decoding camera process configuration ({type(e)}): {e}')
			proc_conf= None
		return proc_conf

	def decode_logging_conf(self, setup_msg: str) -> Optional[LoggingConf]:
		try:
			setup_dict= json.loads(setup_msg)
			log_dict: dict= setup_dict[redis_keys.cam_setup.logging_key]
			log_conf= LoggingConf(
				format_code= 	log_dict[redis_keys.cam_setup.format_code],
				formatter= 		log_dict[redis_keys.cam_setup.formatter],
				console_level= 	log_dict[redis_keys.cam_setup.console_level],
				file_level=		log_dict[redis_keys.cam_setup.file_level],
				file_dir= 		log_dict[redis_keys.cam_setup.file_dir],
				file_name= 		log_dict[redis_keys.cam_setup.file_name],
				file_mode= 		log_dict[redis_keys.cam_setup.file_mode],
				log_to_root= 	log_dict[redis_keys.cam_setup.log_to_root],
				root_file_prefix= log_dict[redis_keys.cam_setup.root_file_prefix],
				root_dir=		log_dict[redis_keys.cam_setup.root_dir],
				session_ts=		log_dict[redis_keys.cam_setup.session_ts]
			)
		except Exception as e:
			self.m_logger.error(f'Error decoding logging configuration ({type(e)}): {e}')
			log_conf= None
		return log_conf

	def decode_camera_conf(self, setup_msg: str) -> Optional[List[CameraConf]]:
		try:
			setup_dict= json.loads(setup_msg)
			cam_dicts: List[dict]= setup_dict[redis_keys.cam_setup.cam_key][redis_keys.cam_setup.cameras]
			camera_conf= [
				CameraConf(
					id= 	cam_dict[redis_keys.cam_setup.cam_id],
					ip= 	cam_dict[redis_keys.cam_setup.cam_ip],
					pole= 	cam_dict[redis_keys.cam_setup.cam_pole],
					num= 	cam_dict[redis_keys.cam_setup.cam_num],
					xml= 	cam_dict[redis_keys.cam_setup.cam_xml]
				)
				for cam_dict in cam_dicts
			]
		except Exception as e:
			self.m_logger.error(f'Error decoding camera configuration ({type(e)}): {e}')
			camera_conf= None
		return camera_conf

	
	# STARTUP

	def encode_startup_message(self, running: bool, opened_cameras: List[str], errors: List[str], pid: int) -> Optional[str]:
		try:
			startup_message= json.dumps({
				redis_keys.cam_startup.running: running,
				redis_keys.cam_startup.opened_cameras: opened_cameras,
				redis_keys.cam_startup.errors: errors,
				redis_keys.cam_startup.pid: pid
			})
		except Exception as e:
			self.m_logger.error(f'Cannot encode the startup message for the camera process ({type(e)}): {e}')
			startup_message= None
		return startup_message

	def decode_running_state(self, startup_msg: str) -> Optional[bool]:
		try:
			startup_dict= json.loads(startup_msg)
			running_state= startup_dict[redis_keys.cam_startup.running]
			if not isinstance(running_state, bool):
				self.m_logger.error(f'Error decoding running state: a boolean was expected')
				running_state= None
		except Exception as e:
			self.m_logger.error(f'Error decoding running state ({type(e)}): {e}')
			running_state= None
		return running_state
	
	def decode_opened_cameras(self, startup_msg: str) -> Optional[List[str]]:
		try:
			startup_dict= json.loads(startup_msg)
			opened_cameras= startup_dict[redis_keys.cam_startup.opened_cameras]
			if not isinstance(opened_cameras, list):
				self.m_logger.error(f'Error decoding opened cameras: a list was expected')
				opened_cameras= None
		except Exception as e:
			self.m_logger.error(f'Error decoding opened cameras ({type(e)}): {e}')
			opened_cameras= None
		return opened_cameras

	def decode_startup_errors(self, startup_msg: str) -> Optional[List[str]]:
		try:
			startup_dict= json.loads(startup_msg)
			errors= startup_dict[redis_keys.cam_startup.errors]
			if not isinstance(errors, list):
				self.m_logger.error(f'Error decoding startup errors: a list was expected')
				errors= None
		except Exception as e:
			self.m_logger.error(f'Error decoding startup errors ({type(e)}): {e}')
			errors= None
		return errors

	def decode_startup_pid(self, startup_msg: str) -> Optional[int]:
		try:
			startup_dict = json.loads(startup_msg)
			pid = startup_dict[redis_keys.cam_startup.pid]
			return int(pid)
		except Exception as e:
			self.m_logger.error(f'Error decoding startup pid ({type(e)}): {e}')
			return None

	
	# CAMERA ERROR

	def encode_camera_error(self, cam_id, running, error_msg) -> Optional[str]:
		try:
			cam_error_message= json.dumps({
				redis_keys.cam_error.cam_id: cam_id,
				redis_keys.cam_error.running: running,
				redis_keys.cam_error.error_msg: error_msg
			})
		except Exception as e:
			self.m_logger.error(f'Cannot encode camera error ({type(e)}): {e}')
			cam_error_message= None
		return cam_error_message

	def decode_camera_error(self, cam_error_message: str) -> Optional[CameraError]:
		try:
			cam_error_dict= json.loads(cam_error_message)
			cam_error= CameraError(
				cam_error_dict[redis_keys.cam_error.cam_id],
				cam_error_dict[redis_keys.cam_error.running],
				cam_error_dict[redis_keys.cam_error.error_msg]
			)
		except Exception as e:
			self.m_logger.error(f'Error decoding camera error ({type(e)}): {e}')
			cam_error= None
		return cam_error


	# EVENT

	def encode_event(self, camera_event: CameraEvent) -> Optional[str]:
		pole_name= camera_event.pole
		shoot_arrays= camera_event.shoot_arrays
		try:
			event_message= json.dumps({
				redis_keys.cam_event.pole: pole_name,
				redis_keys.cam_event.shoot_arrays: [{
					redis_keys.cam_event.timestamp: shoot_array.timestamp,
					redis_keys.cam_event.shoots: [{
						redis_keys.cam_event.cam_id: shoot.cam_id,
						redis_keys.cam_event.cam_num: shoot.cam_num,
						redis_keys.cam_event.img_path: shoot.img_path
					} for shoot in shoot_array.shoots],
					redis_keys.cam_event.trans_id: shoot_array.trans_id
				} for shoot_array in shoot_arrays]
			})
		except Exception as e:
			self.m_logger.error(f'Cannot encode event ({type(e)}): {e}')
			event_message= None
		return event_message

	def decode_event(self, event_message) -> Optional[CameraEvent]:
		try:
			event_dict= json.loads(event_message)
			pole_name= event_dict[redis_keys.cam_event.pole]
			shoot_arrays_dicts= event_dict[redis_keys.cam_event.shoot_arrays]
			shoot_arrays= []
			for shoot_array_dict in shoot_arrays_dicts:
				shoot_dicts= shoot_array_dict[redis_keys.cam_event.shoots]
				shoots= [CameraShoot(
					shoot_dict[redis_keys.cam_event.cam_id],
					shoot_dict[redis_keys.cam_event.cam_num],
					shoot_dict[redis_keys.cam_event.img_path]
				) for shoot_dict in shoot_dicts]
				shoot_arrays.append(CameraShootArray(
					shoot_array_dict[redis_keys.cam_event.timestamp],
					shoots,
					shoot_array_dict[redis_keys.cam_event.trans_id]
				))
			event= CameraEvent(pole_name, shoot_arrays)
		except Exception as e:
			self.m_logger.error(f'Error decoding event {event_message} ({type(e)}): {e}')
			event= None
		return event


# SINGLETON

interpreter= Interpreter()
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import threading
from typing import Optional, Tuple, List

from rigproc.commons.redisi import RedisManager
from rigproc.commons.interpreter import Interpreter, ProcConf, LoggingConf, CameraConf
from rigproc.commons.entities import CameraEvent
from rigproc.params import general, redis_keys
from rigproc.commons.helper import helper
from rigproc.commons.logger import logging_manager


class RigBroker:
	""" Manages communication with rigproc """
	def __init__(self, redis_host: str, redis_port: int):
		self.m_logger= logging.getLogger('camera')
		self.m_redisI= RedisManager('cache', 'camera', redis_host, redis_port)
		self.m_interpreter= Interpreter()
		self.m_interpreter.set_logger('camera')

	def ping_redis(self) -> bool:
		return self.m_redisI.ping()

	def get_setup_message(self) -> Optional[str]:
		return self.m_redisI.get(redis_keys.cam_setup.key, p_default=None)

	def read_setup(self, setup_message: str) -> Tuple[ProcConf, LoggingConf, List[CameraConf]]:
		proc_conf= self.m_interpreter.decode_proc_conf(setup_message)
		log_conf= self.m_interpreter.decode_logging_conf(setup_message)
		cams_conf= self.m_interpreter.decode_camera_conf(setup_message)
		return proc_conf, log_conf, cams_conf

	# EXIT MESSAGE

	async def watch_log_session_ts(self, stop_event: asyncio.Event, log_conf: LoggingConf):
		with ThreadPoolExecutor() as executor:
			await asyncio.get_running_loop().run_in_executor(
				executor, 
				self._watch_log_session_ts_blocking, 
				stop_event, log_conf
			)

	def _watch_log_session_ts_blocking(self, stop_event: asyncio.Event, log_conf: LoggingConf):
		threading.current_thread().setName('CamRLF')

		self.m_redisI.delete(redis_keys.cam_msgs.log_session_ts)

		try:
			l_sub= self.m_redisI.pubsub()
			l_sub.psubscribe(f'__keyspace@0__:{redis_keys.cam_msgs.log_session_ts}')
			while not stop_event.is_set():
				l_msg= l_sub.get_message(p_timeout=1)
				if stop_event.is_set():
					break
				if not l_msg:
					continue
				if l_msg['data'] == 'set':
					self.m_logger.info(
						f'"Log session timestamp" message detected: {l_msg}')
					l_log_session_ts = self.m_redisI.get(
						redis_keys.cam_msgs.log_session_ts, p_default=None)
					if l_log_session_ts is not None:
						self.m_logger.info(
							f'Changing log session timestamp to {l_log_session_ts}')
						logging_manager.set_session_timestamp(l_log_session_ts)
					else:
						self.m_logger.error('Error reading root log file from Redis')
		except Exception as e:
			self.m_logger.error(
				f'Redis subscriber exception {type(e)}: {e}. Will not change root log file anymore.')

	async def wait_exit_message(self):
		with ThreadPoolExecutor() as executor:
			await asyncio.get_running_loop().run_in_executor(executor, self._wait_exit_blocking)

	def _wait_exit_blocking(self):
		threading.current_thread().setName('CamExit')

		# Clear Redis key
		self.m_redisI.delete(redis_keys.cam_msgs.exit)

		# Subscribe to Redis key
		try:
			l_sub= self.m_redisI.pubsub()
			l_sub.psubscribe(f'__keyspace@0__:{redis_keys.cam_msgs.exit}')
			exit_now= False
			while not exit_now:
				l_msg= l_sub.get_message(p_timeout=1)
				if not l_msg:
					continue
				if l_msg['data'] == 'set':
					self.m_logger.info(f'Exit message detected: {l_msg}')
					exit_now= True
		except Exception as e:
			self.m_logger.error(f'Redis subscriber exception {type(e)}: {e}. Exiting...')

	# SEND MESSAGES

	def send_startup_report(self, running, opened_cameras, errors, pid):
		startup_msg= self.m_interpreter.encode_startup_message(running, opened_cameras, errors, pid)
		self.m_redisI.set(redis_keys.cam_startup.key, startup_msg)

	def send_crash_report(self, crash_reason):
		self.m_redisI.set(redis_keys.cam_crash.key, crash_reason)

	def send_cam_error_report(self, cam_id, running, error_msg):
		cam_error_msg= self.m_interpreter.encode_camera_error(cam_id, running, error_msg)
		if cam_error_msg is not None:
			l_key= f'{redis_keys.cam_error.key_prefix}{cam_id}_{helper.timestampNow()}'
			self.m_redisI.set(l_key, cam_error_msg)
		else:
			self.m_logger.error('Cannot encode and send camera error report')

	def send_event_data(self, event_timestamp, pole_name, shoot_arrays) -> str:
		event_msg= self.m_interpreter.encode_event(CameraEvent(pole_name, shoot_arrays))
		if event_msg is not None:
			l_key= f'{redis_keys.cam_event.key_prefix}{pole_name}_{event_timestamp}'
			l_res= self.m_redisI.set(l_key, event_msg)
			if l_res == general.redis.error or l_res is None:
				self.m_logger.error(f'Error setting key {l_key} with event data')
				return None
			else:
				self.m_logger.debug(f'Event stored at key {l_key}')
				return l_key
		else:
			self.m_logger.error('Cannot encode and send event data')
			return None


# SINGLETON

_broker: Optional[RigBroker]= None

def init_rig_broker(redis_host, redis_port):
	global _broker
	_broker= RigBroker(redis_host, redis_port)

def get_rig_broker() -> RigBroker:
	if _broker is None:
		logging.getLogger('camera').error('Rig broker not initialized!')
		return None
	else:
		return _broker

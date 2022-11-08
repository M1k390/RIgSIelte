import os
import json
import socket, pickle, struct
import threading

from rigproc.commons.redisi import RedisManager
from rigproc.commons.logger import logging_manager
from rigproc.commons.interpreter import Interpreter, CameraError
from rigproc.commons.helper import helper

from rigproc.params import redis_keys


REDIS_HOST= 'localhost'
REDIS_PORT= 6379
m_redisI= RedisManager('cache', 'root', REDIS_HOST, REDIS_PORT)


m_logger= logging_manager.generate_logger(
	logger_name='root', 
	format_code='%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s',
	console_level=10,
	file_level=10,
	log_file_name='log_launcher',
	log_file_dir='tmp/log',
	log_file_mode='append',
	root_log_file_prefix=None,
	root_log_dir=None,
	formatter_setting= 'color'
)

m_interpreter= Interpreter()


def setup_redis():
	setup_dict= {
		redis_keys.cam_setup.proc_key: {
			redis_keys.cam_setup.local_dir: helper.universal_path('tmp/imgs'),
			redis_keys.cam_setup.simultaneous_dls: 1,
			redis_keys.cam_setup.trigger_timeout: 5,
			redis_keys.cam_setup.max_frame_dl_time: 2,
			redis_keys.cam_setup.event_timeout: 60
		},
		redis_keys.cam_setup.logging_key: {
			redis_keys.cam_setup.format_code: '%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s',
			redis_keys.cam_setup.formatter:'entity',
			redis_keys.cam_setup.console_level: 10,
			redis_keys.cam_setup.file_dir: 'tmp/log',
			redis_keys.cam_setup.file_name: 'log_camera_launcher',
			redis_keys.cam_setup.file_mode: 'append',
			redis_keys.cam_setup.log_to_root: False,
			redis_keys.cam_setup.root_file_dir: '',
			redis_keys.cam_setup.root_file_name: '',
		},
		redis_keys.cam_setup.cam_key: {
			redis_keys.cam_setup.cameras: [
				{
					redis_keys.cam_setup.cam_id: 'DEV_000F314E56D2',
					redis_keys.cam_setup.cam_ip: '192.168.1.16',
					redis_keys.cam_setup.cam_pole: 'prrA',
					redis_keys.cam_setup.cam_num: 1,
					redis_keys.cam_setup.cam_xml: 'data/conf.xml'
				}
			]
		}
	}
	m_redisI.set(redis_keys.cam_setup.key, json.dumps(setup_dict))


def clean_redis():
	m_redisI.delete(redis_keys.cam_crash.key)
	m_redisI.delete(redis_keys.cam_startup.key)


def watch_redis(stop_event: threading.Event):
	l_sub= m_redisI.pubsub()
	l_sub.psubscribe(
		f'__keyspace@0__:{redis_keys.cam_startup.key}', 
		f'__keyspace@0__:{redis_keys.cam_crash.key}', 
		f'__keyspace@0__:{redis_keys.cam_error.key_prefix}*', 
		f'__keyspace@0__:{redis_keys.cam_event.key_prefix}*'
	)
	while not stop_event.is_set():
		l_msg= l_sub.get_message(p_timeout=1)
		if not l_msg:
			continue
		if l_msg['data'] == 'set':
			l_key= str(l_msg['channel']).replace('__keyspace@0__:', '')
			if l_key == redis_keys.cam_startup.key:
				m_logger.info('Startup detected')
				startup_msg= m_redisI.get(l_key)
				print(
					'STARTUP\n' +\
					f'Running:        {m_interpreter.decode_running_state(startup_msg)}\n' +\
					f'Opened cameras: {m_interpreter.decode_opened_cameras(startup_msg)}\n' +\
					f'Errors:         {m_interpreter.decode_startup_errors(startup_msg)}\n'
				)
			elif l_key == redis_keys.cam_crash.key:
				m_logger.error('The camera process crashed')
				stop_event.set()
			elif l_key.startswith(redis_keys.cam_error.key_prefix):
				error_msg= m_redisI.get(l_key)
				cam_error= m_interpreter.decode_camera_error(error_msg)
				if isinstance(cam_error, CameraError):
					m_logger.info(repr(cam_error))
				else:
					m_logger.error('Cannot read camera error')
			elif l_key.startswith(redis_keys.cam_event.key_prefix):
				event_msg= m_redisI.get(l_key)
				event= m_interpreter.decode_event(event_msg)
				print(repr(event))
	m_logger.warning('Redis subscriber thread terminated')


def send_exit_command():
	m_redisI.set(redis_keys.cam_msgs.exit, 'now')


def listen_socket(stop_event: threading.Event) -> str:
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.bind(('127.0.0.1', 9998))
		sock.settimeout(2)
		sock.listen(1)
		while not stop_event.is_set():
			try:
				conn, addr= sock.accept()
				l_buf= b''
				while len(l_buf) < 4:
					l_buf += conn.recv(4 - len(l_buf))
				l_dataLen= struct.unpack('!I', l_buf)[0]
				data= b''
				while len(data) < l_dataLen:
					data= conn.recv(l_dataLen - len(data))
				decoded_data= pickle.loads(data)
				if decoded_data == 'STOP':
					m_logger.info('Stop command received')
					stop_event.set()
			except socket.timeout:
				pass
			except Exception as e:
				print(f'Socket listen error: {e}')


def run_rigcam():
	my_path= helper.my_path(__file__)
	exec_path= helper.relative_to_abs_path('main.py', my_path)
	command= exec_path
	if exec_path.endswith('.py'):
		command= 'python ' + command
	os.system(f'{command} -host {REDIS_HOST} -port {REDIS_PORT}')
	m_logger.warning('Subprocess launcher thread terminated')


def launch():
	setup_redis()
	clean_redis()
	stop_event= threading.Event()
	socket_thread= threading.Thread(target=listen_socket, args=[stop_event])
	socket_thread.start()
	redis_thread= threading.Thread(target=watch_redis, args=[stop_event])
	redis_thread.start()
	launch_thread= threading.Thread(target=run_rigcam)
	launch_thread.start()
	stop_event.wait()
	send_exit_command()
	m_logger.warning('Launcher terminated')


if __name__ == '__main__':
	launch()
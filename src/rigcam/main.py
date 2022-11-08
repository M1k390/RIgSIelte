from argparse import ArgumentParser
import logging
import vimba
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple
import socket, pickle, struct
import tracemalloc

from rigcam.rig_broker import init_rig_broker, get_rig_broker
from rigcam.pole import PoleScheduler, CameraObject

from rigproc.commons.logger import logging_manager
from rigproc.commons.helper import helper

from rigproc.params import conf_values, internal


async def detect_cameras() -> Tuple[List[vimba.Camera], List[str]]:
	""" Returns a list of detected cameras and a list of errors """
	cam_detection_retries= 3
	cameras= []
	errors= []
	while cam_detection_retries > 0:
		try:
			with vimba.Vimba.get_instance() as vimba_instance:
				cameras= vimba_instance.get_all_cameras()
		except Exception as e:
			if repr(e) not in errors:
				errors.append(repr(e))
		if len(cameras) == 0:
			cam_detection_retries -= 1
			if cam_detection_retries > 0:
				await asyncio.sleep(3)
		else:
			cam_detection_retries= 0
	return cameras, errors
	


#
# MAIN/TEST
#

def listen_socket() -> str:
	""" Listen for a message on the socket. Return the message """
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.bind(('127.0.0.1', 9998))
		sock.settimeout(2)
		sock.listen(1)
		running= True
		while running:
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
				return decoded_data
			except socket.timeout:
				pass
			except Exception as e:
				print(f'Socket listen error: {e}')


def send_socket(msg):
	""" Send a message on the socket """
	msg= pickle.dumps(msg)
	msg_len= struct.pack('!I', len(msg))
	msg= msg_len + msg
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.settimeout(3.0)
		try:
			sock.connect(('127.0.0.1', 9998))
			sock.sendall(msg)
		except Exception as e:
			print(f'Socket send error: {e}')


async def exec_socket_commands(pole_sched_list: List[PoleScheduler]):
	"""
	Execute an operation requested by socket.
		- STOP: interrupt rigcam execution;
		- NET_X: set the simultanous downloads to X.
	"""
	l_logger= logging.getLogger('camera')
	with ThreadPoolExecutor() as executor:
		running= True
		while running:
			cmd= await asyncio.get_running_loop().run_in_executor(executor, listen_socket)
			if cmd == 'STOP':
				for pole_sched in pole_sched_list:
					pole_sched.stop_loop()
				running= False
			elif cmd.startswith('NET'):
				try:
					_, num= cmd.split('_')
					num= int(num)
					for pole_sched in pole_sched_list:
						pole_sched.set_network_semaphore(num)
				except:
					pass
	l_logger.warning('Command executer terminated')


async def monitor_memory():
	""" Monitor memory usage and print data periodically """
	l_logger= logging.getLogger('camera')
	tracemalloc.start()
	try:
		while True:
			await asyncio.sleep(10)
			current, peak= tracemalloc.get_traced_memory()
			l_logger.info(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")
	except asyncio.CancelledError:
		l_logger.warning('Memory tracer cancelled')
	tracemalloc.stop()


#
# MAIN TEST
#

async def main_test(xml_file: str):
	"""
	Main body for debug/testing purposes.
	Does not require a configuration in Redis.

	Arguments
	---------
	xml_file: path of the Vimba configuration file for the cameras.
	"""
	threading.current_thread().setName('Rigcam')
	# Set logger
	l_logger= logging_manager.generate_logger(
		logger_name='camera',
		format_code='%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)-10.10s::%(funcName)-15.15s} %(message)s',
		console_level=10,
		file_level=10,
		log_file_name='log_camera',
		log_file_dir='tmp/log',
		log_file_mode='append',
		root_log_file_prefix=None,
		root_log_dir=None,
		print_to_console=True,
		formatter_setting=conf_values.log_formatter.custom
	)
	helper.set_logger('camera')
	init_rig_broker('localhost', 6379)
	
	l_logger.info('Detecting cameras...')
	det_cams, errors= await detect_cameras()
	if len(errors) > 0:
		l_logger.warning('Errors detecting cameras:\n' + '\n'.join([str(err) for err in errors]))

	l_logger.info('Detected cameras:\n' + '\n'.join([str(cam) for cam in det_cams]))
	if len(det_cams) == 0:
		l_logger.error('No camera detected! Terminating...')
		return
	cams= []
	pole_name= 'prrA'
	for i, cam in enumerate(det_cams):
		cams.append(CameraObject(
			id= 			cam.get_id(),
			vimba_camera= 	cam,
			pole=			pole_name,
			num= 			i + 1,
			ip= 			'unknown',
			xml_file= 		xml_file
		))
	network_semaphore= asyncio.Semaphore(1)
	pole_sched= PoleScheduler(pole_name, cams, network_semaphore, 5, 2, 30, helper.abs_path(helper.join_paths('tmp', 'imgs')))
	pole_task= asyncio.create_task(pole_sched.loop())
	memory_tracer_task= asyncio.create_task(monitor_memory())
	cmd_executer_task= asyncio.create_task(exec_socket_commands([pole_sched]))
	await pole_task
	l_logger.warning('All pole tasks terminated')
	if not cmd_executer_task.done():
		send_socket('STOP')
	memory_tracer_task.cancel()
	await memory_tracer_task
	await cmd_executer_task
	l_logger.warning('Camera process terminated')


#
# MAIN
#

async def main(redis_host, redis_port):
	"""
	Main body for usage with rigproc.
	Requires rigproc to store the configuration in Redis.

	Arguments
	---------
	redis_host: ip address of the Redis server;
	redis_port: port of the Redis service.
	"""
	threading.current_thread().setName('Rigcam')
	
	# Set temporary logger
	l_logger= logging_manager.generate_logger(
		logger_name='camera',
		format_code='%(asctime)s >> %(message)s',
		console_level=10,
		file_level=10,
		log_file_name='',
		log_file_dir='',
		log_file_mode='append',
		root_log_file_prefix=None,
		root_log_dir=None,
		print_to_console=True,
		formatter_setting=conf_values.log_formatter.color,
		is_root=True
	)

	l_logger.info(f'Starting Rigcam with Redis host {redis_host} and port {redis_port}')
	
	init_rig_broker(redis_host, redis_port)
	m_broker= get_rig_broker()

	# Get process pid to send in the startup report: if error, send None
	pid = helper.get_my_pid()

	setup_msg= m_broker.get_setup_message()
	if setup_msg is None:
		l_logger.error('Camera process >> ERROR! Cannot find the setup message on Redis')
		m_broker.send_startup_report(False, [], [internal.cam_startup_error.conf_error], pid)
		return

	proc_conf, log_conf, cams_conf= m_broker.read_setup(setup_msg)
	if proc_conf is None:
		l_logger.error('Camera process >> ERROR! Cannot read the process configuration in the setup message')
		m_broker.send_startup_report(False, [], [internal.cam_startup_error.conf_error], pid)
		return
	if log_conf is None:
		l_logger.error('Camera process >> ERROR! Cannot read the logging configuration in the setup message')
		m_broker.send_startup_report(False, [], [internal.cam_startup_error.conf_error], pid)
		return
	if cams_conf is None:
		l_logger.error('Camera process >> ERROR! Cannot read the camera configuration in the setup message')
		m_broker.send_startup_report(False, [], [internal.cam_startup_error.conf_error], pid)
		return

	# Set logger
	logging_manager.set_session_timestamp(log_conf.session_ts)
	l_logger= logging_manager.generate_logger(
		logger_name='camera',
		format_code=log_conf.format_code,
		console_level=log_conf.console_level,
		file_level=log_conf.file_level,
		log_file_name=log_conf.file_name,
		log_file_dir=log_conf.file_dir,
		log_file_mode=log_conf.file_mode,
		root_log_file_prefix=log_conf.root_file_prefix if log_conf.log_to_root else None,
		root_log_dir=log_conf.root_dir if log_conf.log_to_root else None,
		print_to_console=True,
		formatter_setting=log_conf.formatter,
		is_root=True,
		overwrite=True
	)

	# Detect and recognize cameras
	l_logger.info('Detecting cameras...')
	det_cams, errors= await detect_cameras()
	if len(errors) > 0:
		l_logger.warning('Errors detecting cameras:\n' + '\n'.join([str(err) for err in errors]))

	l_logger.info('Detected cameras:\n' + '\n'.join([str(cam) for cam in det_cams]))
	det_id_cams= {}
	for cam in det_cams:
		det_id_cams[cam.get_id()]= cam
	recognized_pole_cameras: Dict[str, List[CameraObject]]= {}
	for cam_conf in cams_conf:
		if cam_conf.id in det_id_cams.keys():
			if cam_conf.pole not in recognized_pole_cameras.keys():
				recognized_pole_cameras[cam_conf.pole]= []
			recognized_pole_cameras[cam_conf.pole].append(CameraObject(
				id= cam_conf.id,
				vimba_camera= det_id_cams[cam_conf.id],
				pole= cam_conf.pole,
				num= cam_conf.num,
				ip= cam_conf.ip,
				xml_file= cam_conf.xml
			))
	if len(recognized_pole_cameras.keys()) < len(det_id_cams.keys()):
		l_logger.warning('Some cameras were ignored because their ID is not in the current configuration')
	if len(recognized_pole_cameras.keys()) == 0:
		l_logger.error('No camera detected! Terminating...')
		m_broker.send_crash_report(internal.cam_crash.no_cam_conn)
		return
	
	# Initialize poles and distribute cameras
	pole_schedulers: List[PoleScheduler]= []
	pole_tasks: List[asyncio.Task]= []
	network_semaphore= asyncio.Semaphore(proc_conf.simultaneous_dls)
	for pole_name, cams in recognized_pole_cameras.items():
		pole_sched= PoleScheduler(
			pole_name= 			pole_name,
			cameras= 			cams,
			network_semaphore= 	network_semaphore,
			trigger_timeout= 	proc_conf.trigger_timeout,
			max_frame_dl_time= 	proc_conf.max_frame_dl_time,
			event_timeout= 	proc_conf.event_timeout,
			local_dir= 			proc_conf.local_dir
		)
		pole_task= asyncio.create_task(pole_sched.loop())
		pole_schedulers.append(pole_sched)
		pole_tasks.append(pole_task)

	# Send startup report
	opened_cameras= []
	for pole_sched in pole_schedulers:
		opened_cameras += await pole_sched.get_opened_cameras()
	if len(opened_cameras) > 0:
		m_broker.send_startup_report(True, opened_cameras, [], pid)
	else:
		m_broker.send_startup_report(False, [], [], pid)
		return

	# Create exit task
	exit_task= asyncio.create_task(m_broker.wait_exit_message())
	exit_event = asyncio.Event()
	root_log_file_task = asyncio.create_task(m_broker.watch_log_session_ts(exit_event, log_conf))

	# Wait for pole tasks or exit task termination
	while len(pole_tasks) > 0:
		to_wait= pole_tasks.copy()
		if not exit_event.is_set():
			to_wait.append(exit_task)
			to_wait.append(root_log_file_task)
		l_logger.info(
			f'Waiting for {len(to_wait)} tasks' +
			(' (exit task and root file task included)' if not exit_event.is_set() else '')
		)
		done, _= await helper.wait_first(to_wait)
		if exit_task in done:
			l_logger.info('Exiting...')
			exit_event.set()
			for pole_sched in pole_schedulers:
				pole_sched.stop_loop()
		for task in done:
			if task in pole_tasks:
				task_id= pole_tasks.index(task)
				pole_tasks.pop(task_id)
				pole_schedulers.pop(task_id)
	l_logger.warning('All pole tasks terminated')

	# Send crash if terminating without stop command
	if not exit_event.is_set():
		m_broker.send_crash_report(internal.cam_crash.all_cam_lost)

	l_logger.warning('Camera process terminated')




if __name__ == '__main__':
	parser= ArgumentParser()
	parser.add_argument('-t', '--test', help='modalità test (senza rigproc)', action='store_true')
	parser.add_argument('-c', '--conf', help='file xml di configurazione camere', default='', type=str)
	parser.add_argument('-host', '--host', help='Redis host', default='localhost', type=str)
	parser.add_argument('-port', '--port', help='Redis port', default='6379', type=str)
	args= parser.parse_args()
	if args.test:
		asyncio.run(main_test(args.conf), debug=False)
	else:
		asyncio.run(main(args.host, int(args.port)), debug=False)
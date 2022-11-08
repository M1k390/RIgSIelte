"""
Launches the Rig Python process and manages its execution
By default, searches for the executable file in a directory structured in this way:
EXEC_FOLDER			<-- the executable main directory
	rig_VERSION			<-- the executable file, specifying its version (e.g.: rig_1.1.2)
	other...			<-- other files, ignored, like the Camera executable (launched by Rigproc)
Checks Redis cache to monitor Rigproc execution:
	-	key "start_timestamp" contains the timestamp of Rigproc execution start.
			If the key is missing or the timestamp is old, the boot has failed.
	-	key "termination_message" is written by Rigproc when exiting.
			Rigboot watches this key periodically after a successful boot
			determines, for istance, if a reboot is needed.
	-	key "heartbeat" is written by Rigproc periodically.
			If Rigproc did not write a heartbeat for some time, Rigboot presumes it crashed.
Exit codes:
 0 -> 	OK
 1 -> 	Configuration error
 2 -> 	Redis error
In case of crash or unknown termination, rigboot tries to restart the program.
It tries instantly and then every 3 hours.
"""


import logging
import argparse
import platform
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import os
import sys
import json
from pathlib import Path
import time
from datetime import datetime
from enum import Enum, unique, auto
from redis import StrictRedis


# TYPES

@unique
class ExecType(Enum):
	""" Defines the executable file type """
	EXEC= auto() # no extension (Pyinstaller --onefile)
	PYTHON= auto()


@unique
class ExecOutcome(Enum):
	""" Defines the detected outcome of a Rig termination """
	REBOOT= auto()
	SHUTDOWN= auto()
	EXIT= auto()
	CRASH= auto()


@unique
class TermMsg(str, Enum):
	""" Defines the termination messages that can be read on the Redis cache 
	These are the strings that Rig should put into cache at shutdown """
	REBOOT= 'reboot'
	SHUTDOWN= 'shutdown'
	EXIT= 'exit'


# CONSTANTS

RIGPROC_KEYWORD = 'rigproc'
REDIS_ATTEMPTS = 3
REDIS_ENCODING= 'utf8'
EXEC_PREFIX= 'rigproc_'
BOOT_TIMESTAMP= time.time()
HOT_RESTART_AVAILABLE = True
RESTART_INTERVAL = 60
SYSTEMD_SERVICE_NAME= 'runrig'
MINIMUM_REBOOTS_INTERVAL= 1200
LAST_REBOOT_TIMESTAMP_KEY= 'last_reboot_timestamp'


# VARIABLES

debug_mode= False
check_heartbeat= True
exec_type= ExecType.EXEC # Determines the command to execute to launch the program
conda_path= '/opt/miniconda3/bin'
conda_env= 'base' # Rigboot launches a Python file in a Conda environment with all RIG dependencies
test_launcher= False # if True, rigboot is launching a run.py file in rigtests. If False, it's launching rigproc's __main__.py


# LOGGER

_logger= logging.getLogger('boot')

class _CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    def __init__(self, format_code):

        grey = "\x1b[1;30;40m"
        yellow = "\x1b[1;33;40m"
        red = "\x1b[1;31;40m"
        bold_red = "\x1b[0;30;41m"
        reset = "\x1b[0m"

        self.FORMATS = {
            logging.debug: grey + format_code + reset,
            logging.INFO: reset + format_code + reset,
            logging.WARNING: yellow + format_code + reset,
            logging.ERROR: red + format_code + reset,
            logging.CRITICAL: bold_red + format_code + reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# CONFIGURATION

def _read_conf_value(conf_dict: dict, *keys):
	""" Read a value in the configuration dict
	Exits if a value is not found """
	for i, key in enumerate(keys):
		conf_dict= conf_dict.get(key)
		if conf_dict is None or (i < (len(keys) - 1) and not isinstance(conf_dict, dict)):
			_logger.critical('Configuration file ' +\
				f'is missing the value for [{", ".join(keys[0:i+1])}]: exiting...')
			sys.sys.exit(1)
	return conf_dict


class _BootConfig:
	""" Configuration wrapper """

	def __init__(self, conf_dict: dict):

		# Logger
		self.logging_format= _read_conf_value(conf_dict, 'logging', 'root', 'format')

		# Redis conf
		self.redis_cache_host= _read_conf_value(conf_dict, 'main', 'redis', 'cache', 'host')
		self.redis_cache_port= _read_conf_value(conf_dict, 'main', 'redis', 'cache', 'port')
		self.redis_pers_host= _read_conf_value(conf_dict, 'main', 'redis', 'pers', 'host')
		self.redis_pers_port= _read_conf_value(conf_dict, 'main', 'redis', 'pers', 'port')

		# Paths
		self.exec_dir= Path(_read_conf_value(conf_dict, 'boot', 'exec_dir')).absolute()
		self.defualt_exec_path= Path(_read_conf_value(conf_dict, 'boot', 'default_exec_path')).absolute()

		# Redis keys
		self.last_version_key= _read_conf_value(conf_dict, 'boot', 'last_version_key')
		self.rig_start_timestamp_key= _read_conf_value(conf_dict, 'boot', 'rig_start_timestamp_key')
		self.rig_termination_key= _read_conf_value(conf_dict, 'boot', 'rig_termination_key')

		# Timeouts
		self.boot_check_timeout= _read_conf_value(conf_dict, 'boot', 'boot_check_timeout')
		self.exec_watch_interval= _read_conf_value(conf_dict, 'boot', 'exec_watch_interval')

		# Heartbeat
		self.alive_key= _read_conf_value(conf_dict, 'boot', 'alive_key')


# OPERATIONS

def _get_redis_cache(config: _BootConfig) -> StrictRedis:
	""" Generates a reference to the Redis cache (port 6379) """
	host=config.redis_cache_host
	port=config.redis_cache_port
	cache= StrictRedis(host, port)
	attempts = REDIS_ATTEMPTS
	connected = False
	while attempts > 0 and not connected:
		try:
			cache.ping()
			connected = True
		except Exception as e:
			_logger.error(f'Redis connection error to host: {host}, port: {port} ({type(e)}): {e}')
		attempts -= 1
		if not connected and attempts > 0:
			_logger.info('Trying again in 1 second...')
			time.sleep(1)
	if not connected:
		_logger.error('Unable to connect to Redis cache: exiting...')
		sys.exit(2)
	return cache


def _get_redis_persistent(config: _BootConfig) -> StrictRedis:
	""" Generates a reference to the Redis persistent cache (port 6380) """
	host=config.redis_pers_host
	port=config.redis_pers_port
	persistent= StrictRedis(host, port)
	attempts = REDIS_ATTEMPTS
	connected = False
	while attempts > 0 and not connected:
		try:
			persistent.ping()
			connected = True
		except Exception as e:
			_logger.error(f'Redis connection error to host: {host}, port: {port} ({type(e)}): {e}')
		attempts -= 1
		if not connected and attempts > 0:
			_logger.info('Trying again in 1 second...')
			time.sleep(1)
	if not connected:
		_logger.error('Unable to connect to Redis persistent: exiting...')
		sys.exit(2)
	return persistent


def _get_last_version(config: _BootConfig, persistent: StrictRedis) -> str:
	""" Gets the last version number from Redis persistent cache
	Returns None if the last version is not specified """
	last_version= persistent.get(config.last_version_key)
	if last_version is not None:
		last_version= last_version.decode(REDIS_ENCODING)
		_logger.info(f'Last Rig version specified in Redis persistent cache is {last_version}')
	else:
		_logger.warning(f'Last version number not found in Redis persistent cache: starting default')
	return last_version


def _get_last_exec_path(config: _BootConfig, last_version: str) -> str:
	""" Checks if the executable for the last version exists and returns its path.
	Returns None if the file does not exist or the exec dir is not specified """
	global exec_type
	if config.exec_dir == '':
		return None
	exec_file_path= str(config.exec_dir / f'{EXEC_PREFIX}{last_version}')
	if os.path.isfile(exec_file_path):
		exec_type= ExecType.EXEC
		return exec_file_path
	else:
		_logger.error('Rigproc version specified in Redis persistent cache does not exist: using default')
		return None


def _kill_running_executables(keyword: str):
	_logger.info(f'Killing pending {keyword} processes...')
	ps_aux = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
	processes = ps_aux.stdout.splitlines()
	rigprocs = [p for p in processes if keyword in p]
	_logger.info(f'Found {len(rigprocs)} pending {keyword} processes')
	for p in rigprocs:
		parts = p.split()
		try:
			pid = int(parts[1])
			os.system(f'kill {pid}')
			_logger.warning(f'Process {pid} killed')
		except Exception as e:
			_logger.error(f'Error killing process ({type(e)}): {e}')


def _start_executable(exec_path: str, conf_path: str, config: _BootConfig, cache: StrictRedis):
	""" Executes a command to launch the program """
	global BOOT_TIMESTAMP
	BOOT_TIMESTAMP= time.time()
	commands= []
	_logger.info(f'Booting\nEXECUTABLE:    {exec_path}\nCONFIGURATION: {conf_path}')
	cache.delete(config.rig_termination_key)
	if exec_type == ExecType.EXEC:
		commands.append(f'chmod +x {exec_path}') # Make the file executable
		commands.append(f'{exec_path} {conf_path} &') # Execute the file
	elif exec_type == ExecType.PYTHON:
		commands.append(f'{conda_path}/bin/activate {conda_env}') # Activate the Conda environment
		if test_launcher:
			commands.append(f'python {exec_path} -c {conf_path} &')
		else:
			commands.append(f'python {exec_path} {conf_path} &')
	for cmd in commands:
		os.system(cmd)


def _check_correct_boot(config: _BootConfig, cache: StrictRedis, term_event: threading.Event):
	""" Waits for a predefined timeout. 
	Then, it checks if the program left a start timestamp in Redis cache """
	threading.current_thread().setName('boot_b')
	term_event.wait(timeout=config.boot_check_timeout)
	if term_event.is_set():
		_logger.warning('Rigproc exited before writing the start timestamp')
		return False
	start_timestamp= cache.get(config.rig_start_timestamp_key)
	try:
		# The timestamp must be generated with helper.timestampNowFormatted()
		start_timestamp= start_timestamp.decode(REDIS_ENCODING) # str format
		start_timestamp= datetime.fromisoformat(start_timestamp) # datetime format
		start_timestamp= datetime.timestamp(start_timestamp) # float format
	except Exception as e:
		_logger.error(f'Cannot read start timestamp on Redis cache {start_timestamp}: {e}')
		return False
	if start_timestamp is not None and start_timestamp > BOOT_TIMESTAMP:
		_logger.info('Boot success!')
		return True
	else:
		_logger.warning(f'Boot failed. Start timestamp: {start_timestamp}')
		return False


def _check_termination(config: _BootConfig, cache: StrictRedis, term_event: threading.Event) -> ExecOutcome:
	""" Checks at periodic intervals if the program left a termination message in Redis cache.
	Also, if the "check heartbeat" flag is True, checks the timestamp of the last heartbeat from Rig.
	Returns the corresponding execution outcome to be processed when the program terminates or a crash is assumed """
	threading.current_thread().setName('boot_t')
	_logger.debug('Watching program execution...')
	while not term_event.is_set():
		# Check RIG termination
		# The rig_termination_key should be deleted by Rig at startup
		term_msg= cache.get(config.rig_termination_key)
		if term_msg is not None:
			term_event.set()
			term_msg= term_msg.decode(REDIS_ENCODING)
			if term_msg == TermMsg.REBOOT:
				return ExecOutcome.REBOOT
			if term_msg == TermMsg.SHUTDOWN:
				return ExecOutcome.SHUTDOWN
			if term_msg == TermMsg.EXIT:
				return ExecOutcome.EXIT
			_logger.warning(f'The program shut down with an unknown termination message: {term_msg}')
			return ExecOutcome.CRASH
		term_event.wait(timeout=config.exec_watch_interval * .9)
	return ExecOutcome.CRASH


def _check_heartbeat(config: _BootConfig, cache: StrictRedis, term_event: threading.Event):
	threading.current_thread().setName('boot_h')
	_logger.debug('Checking heartbeat...')
	missing_heartbeat_counter= 3
	# Check RIG heartbeat
	while not term_event.is_set():
		if check_heartbeat and config.alive_key != '':
			alive_timestamp= cache.get(config.alive_key)
			if alive_timestamp is None:
				missing_heartbeat_counter -= 1
				if missing_heartbeat_counter <= 0:
					_logger.error('Missing heartbeat from Rig process: assuming crash')
					term_event.set()
					return
			else:
				try:
					# The timestamp must be generated by the RIG using helper.timestampNowFormatted()
					alive_timestamp= alive_timestamp.decode(REDIS_ENCODING)
					alive_timestamp= datetime.fromisoformat(alive_timestamp)
					alive_timestamp= datetime.timestamp(alive_timestamp)
				except:
					_logger.error(f'Malformed alive timestamp, assuming crash: {alive_timestamp}')
					term_event.set()
					return
				current_timestamp= time.time()
				elapsed_time_from_hearbeat= current_timestamp - alive_timestamp
				if elapsed_time_from_hearbeat > (config.exec_watch_interval * 3):
					_logger.error(f'Last heartbeat is from {elapsed_time_from_hearbeat} seconds ago: assuming crash')
					term_event.set()
					return
				else:
					_logger.debug(f'Last heartbeat: {datetime.fromtimestamp(alive_timestamp)} ({elapsed_time_from_hearbeat} seconds ago)')
		term_event.wait(config.exec_watch_interval * .9)


def _reboot(redisi: StrictRedis):
	""" If not in debug mode, reboots the system """
	try:
		last_reboot_timestamp= redisi.get(LAST_REBOOT_TIMESTAMP_KEY)
		last_reboot_timestamp= last_reboot_timestamp.decode(REDIS_ENCODING)
		last_reboot_timestamp= float(last_reboot_timestamp)
	except:
		last_reboot_timestamp= None
	if last_reboot_timestamp is not None:	
		now= time.time()
		elapsed_time_from_reboot= now - last_reboot_timestamp
		if elapsed_time_from_reboot < MINIMUM_REBOOTS_INTERVAL:
			time_to_wait= MINIMUM_REBOOTS_INTERVAL - elapsed_time_from_reboot
			_logger.info(f'Waiting {time_to_wait} seconds before rebooting')
			if debug_mode:
				_logger.info('Debug mode: avoiding waiting')
			else:
				time.sleep(time_to_wait)
	reboot_time= time.time()
	_logger.info(f'Setting reboot time: {datetime.fromtimestamp(reboot_time)}')
	redisi.set(LAST_REBOOT_TIMESTAMP_KEY, reboot_time)
	if debug_mode:
		_logger.info('Debug mode: avoiding reboot')
	else:
		_logger.info('Rebooting...')
		reboot_command= 'sudo shutdown -r now'
		os.system(reboot_command)
	sys.exit(0)


def _shutdown(redisi: StrictRedis):
	""" If not in debug mode, shutdown the system """
	try:
		last_reboot_timestamp= redisi.get(LAST_REBOOT_TIMESTAMP_KEY)
		last_reboot_timestamp= last_reboot_timestamp.decode(REDIS_ENCODING)
		last_reboot_timestamp= float(last_reboot_timestamp)
	except:
		last_reboot_timestamp= None
	if last_reboot_timestamp is not None:	
		now= time.time()
		elapsed_time_from_reboot= now - last_reboot_timestamp
		if elapsed_time_from_reboot < MINIMUM_REBOOTS_INTERVAL:
			time_to_wait= MINIMUM_REBOOTS_INTERVAL - elapsed_time_from_reboot
			_logger.info(f'Waiting {time_to_wait} seconds before shutting down')
			if debug_mode:
				_logger.info('Debug mode: avoiding waiting')
			else:
				time.sleep(time_to_wait)
	reboot_time= time.time()
	_logger.info(f'Setting reboot time (for shutdown): {datetime.fromtimestamp(reboot_time)}')
	redisi.set(LAST_REBOOT_TIMESTAMP_KEY, reboot_time)
	if debug_mode:
		_logger.info('Debug mode: avoiding shutdown')
	else:
		_logger.info('Shutting down...')
		shutdown_command= 'sudo shutdown -h now'
		os.system(shutdown_command)
	sys.exit(0)


def _react_to_stop(redisi: StrictRedis, exec_outcome: ExecOutcome):
	""" 
	Calls the right method depending on the execution outcome.

	It is in charge to stop the execution of rigboot when necessary.
	"""
	if exec_outcome == ExecOutcome.REBOOT:
		_logger.info('The program terminated asking for a reboot: rebooting...')
		_reboot(redisi)
	elif exec_outcome == ExecOutcome.SHUTDOWN:
		_logger.info('The program terminated asking to shutdown: turning off...')
		_shutdown(redisi)
	elif exec_outcome == ExecOutcome.EXIT:
		_logger.info('The program terminated: exiting...')
		sys.exit(0)
	elif exec_outcome == ExecOutcome.CRASH:
		_logger.info('The program crashed: restarting the program...')
		return
	else:
		_logger.error('Unknown execution outcome: restarting the program...')
		return


def _boot_routine(config: _BootConfig, exec_path: str, conf_path: str, cache: StrictRedis, persistent: StrictRedis) -> bool:
	""" START PROGRAM -> CHECK BOOT -> WATCH EXECUTION -> TERMINATE AND EXIT
	Returns if the program booted correctly or not """
	global HOT_RESTART_AVAILABLE

	# Unless explicit exit, keep trying to restart the program
	while(True):
		_kill_running_executables(RIGPROC_KEYWORD)
		_start_executable(exec_path, conf_path, config, cache)
		term_event= threading.Event()
		with ThreadPoolExecutor() as executor:
			boot_check= executor.submit(_check_correct_boot, config, cache, term_event)
			exec_outcome= executor.submit(_check_termination, config, cache, term_event)
			if boot_check.result():
				executor.submit(_check_heartbeat, config, cache, term_event)
			else:
				term_event.set()
			
			# If necessary, _react_to_stop will terminate rigboot
			_react_to_stop(persistent, exec_outcome.result())

			if HOT_RESTART_AVAILABLE:
				HOT_RESTART_AVAILABLE = False
			else:
				# Wait interval before restarting
				_logger.info(f'Waiting {RESTART_INTERVAL} seconds before restart')
				while (time.time() - BOOT_TIMESTAMP) < RESTART_INTERVAL:
					time.sleep(1)


def main(conf_path: str):
	global _logger

	# Rename current thread for logging legibility
	threading.current_thread().name= 'boot'

	# Load configuration
	with open(conf_path, 'r') as f:
		conf_dict= json.load(f)
	config= _BootConfig(conf_dict)

	# Configure logger
	log_formatter= _CustomFormatter(config.logging_format)
	console_handler= logging.StreamHandler()
	console_handler.setFormatter(log_formatter)
	console_handler.setLevel(logging.DEBUG)
	_logger.addHandler(console_handler)
	_logger.setLevel(logging.DEBUG)

	# Check platform
	if platform.system() != 'Linux':
		_logger.warning('This script is supposed to work only in Linux')

	# Load Redis cache and persistent cache
	cache= _get_redis_cache(config)
	persistent= _get_redis_persistent(config)

	# Read last version to execute on persistent cache
	last_version= _get_last_version(config, persistent)
	if last_version is not None:
		exec_path= _get_last_exec_path(config, last_version)
		if exec_path is not None:
			boot_success= _boot_routine(config, exec_path, conf_path, cache, persistent)
	if last_version is None or exec_path is None or not boot_success:
		_boot_routine(config, config.defualt_exec_path, conf_path, cache, persistent)
	
	sys.exit(0)


if __name__ == '__main__':
	parser= argparse.ArgumentParser()
	parser.add_argument('-c', '--conf', help='configuration file path', type=str)
	parser.add_argument('-d', '--debug', help='debug mode', action='store_true')
	parser.add_argument('-ch', '--checkheartbeat', help='check rigproc heartbeat', action='store_true')
	parser.add_argument('-tl', '--testlauncher', help='launch rigproc from test launcher', action='store_true')
	parser.add_argument('-et', '--exectype', help='type of executable file (executable/python)', default='executable', type=str)
	parser.add_argument('-cp', '--condapath', help='path of conda executable (only for python file)', default='/opt/miniconda3', type=str)
	parser.add_argument('-ce', '--condaenv', help='name of conda environment (only for python file)', default='base', type=str)

	args= parser.parse_args()

	if not args.conf:
		print('Must specify a configuration file!')
		exit()

	if args.exectype not in ['executable', 'python']:
		print('Exec type must be "executable" or "python"')

	debug_mode= bool(args.debug)
	check_heartbeat= bool(args.checkheartbeat)
	test_launcher= bool(args.testlauncher)
	
	if args.exectype == 'executable':
		exec_type= ExecType.EXEC
	else:
		exec_type= ExecType.PYTHON

	conda_path= args.condapath
	conda_env= args.condaenv

	main(args.conf)
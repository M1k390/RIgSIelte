from datetime import datetime
from enum import auto
import logging
from typing import Optional

from rigproc.commons import redisi
from rigproc.commons.wrappers import wrapkeys
from rigproc.params import redis_keys, conf_values


_logger= logging.getLogger('root')
_redisI: redisi.DualRedis= None


# Placeholder for missing values
_MISSING= auto()


# EXCEPTIONS

class ConfMissingError(Exception):
	def __init__(self, keys: list):
		l_path= ', '.join(keys)
		self.message= f'The following configuration value is missing: {l_path}'
		super().__init__(self.message)

class ConfTypeError(Exception):
	def __init__(self, keys: list, expected_type, value):
		l_path= ', '.join(keys)
		self.message= f'Error with config value {l_path} -> {value}: expected {expected_type}, is {type(value)}'
		super().__init__(self.message)

class ConfForbiddenError(Exception):
	def __init__(self, keys: list, values, value):
		l_path= ', '.join(keys)
		self.message= f'Error with config value {l_path} -> {value}: expected one of {values}'
		super().__init__(self.message)

class ConfGenericError(Exception):
	def __init__(self, keys: list, value) -> None:
		l_path= ', '.join(keys)
		self.message= f'The config value {l_path} -> {value} did not pass a check'
		super().__init__(self.message)

class CheckFuncError(Exception):
	def __init__(self, keys: list, value) -> None:
		l_path= ', '.join(keys)
		self.message= f'Tried to call an invalid checking function on the config value {l_path} -> {value}'
		super().__init__(self.message)


# COMMON METHODS

def _init_redis():
	global _redisI
	if isinstance(_redisI, redisi.DualRedis):
		return True
	_redisI= redisi.get_redisI()
	return isinstance(_redisI, redisi.DualRedis)

def cast(obj, type):
	try:
		types= list(type)
		if float in types:
			try:
				return float(obj)
			except:
				pass
		for obj_type in types:
			try:
				return obj_type(obj)
			except:
				pass
		raise Exception('Object cannot be cast')
	except:
		try:
			return type(obj)
		except:
			raise Exception('Object cannot be cast')	


# CHECK FUNCTIONS

def _check_positive(value):
	try:
		if value >= 0:
			return True
		else:
			_logger.critical(
				f'{value} is not positive'
			)
	except:
		_logger.critical(
			f'Cannot check if {value} is positive'
		)
	return False

def _check_time(value):
	time_format = '%H:%M'
	try:
		datetime.strptime(value, time_format)
		return True
	except:
		_logger.critical(
			f'Value does not respect the time format: {value}, {time_format}')
		return False


# CONFIGURATION OBJECTS

class _ConfItem():
	"""
	Represents a single configuration parameter.
	"""
	
	def __init__(self) -> None:
		self._value= _MISSING
		self._bak_value= _MISSING
		self._integrity= _MISSING
	
	def init(self, conf_dict: dict, *keys: str, type=None, values=None, check_func=None) -> None:
		"""
		Initialization method called after the object construction.

		Arguments
		---------
		conf_dict: 	the loaded json
		keys: 		the keys to find the parameter in the dict
		type: 		the expected value type
		values: 	the ammitted values
		check_func: a function to execute to ensure the parameter's validity
		"""
		self.__keys= keys
		self._type= type
		
		try:
			# Check if the value is in the dict
			value= wrapkeys.getValueDefault(conf_dict, _MISSING, *keys)
			if value is _MISSING:
				raise ConfMissingError(keys)
			
			# Check if the value respects the restrictions
			if type is not None and not isinstance(value, type):
				raise ConfTypeError(keys, type, value)
			if values is not None and value not in values:
				raise ConfForbiddenError(keys, values, value)
			if check_func is not None:
				try:
					if not check_func(value):
						raise ConfGenericError(keys, value)
				except:
					raise CheckFuncError(keys, value)
			
			self._value= value
			self._bak_value= value
			self._integrity= True
		
		except (ConfMissingError, ConfTypeError, ConfForbiddenError, ConfGenericError, CheckFuncError) as e:
			self._set_default_value(type=type)
			_logger.critical(f'{e}. Skipping...')
			self._integrity= False

	def path(self):
		return ' -> '.join(self.__keys)

	def integrity(self):
		if self._integrity is _MISSING:
			_logger.critical(
				'Checking integrity before initializing item: returning False. '
				'Check that config is correctly initialized (every _ConfItem must be initialized!)'
			)
			return False
		return self._integrity
	
	def get(self):
		return self._value

	def set(self, p_value) -> bool:
		if self._type is not None:
			if not isinstance(p_value, self._type):
				try:
					p_value= cast(p_value, self._type)
				except:
					_logger.error(f'Cannot set {self.__keys} to {p_value}: wrong data type (expected {self._type})')
					return False
		_logger.debug(f'Changing {self.path()} from {self._value} to {p_value}')
		self._value= p_value
		return True

	def reset(self):
		_logger.debug(f'Resetting {self.path()} from current value {self._value} to original value {self._bak_value}')
		self._value= self._bak_value

	def _set_default_value(self, type=None):
		default_values= ['', 0, [], {}, False]
		self._value= ''
		if type is not None:
			for val in default_values:
				if isinstance(val, type):
					self._value= val
					break
		self._bak_value= self._value


class _PlantConfItem(_ConfItem):
	"""
	Represents an implant configuration parameter.
	Keeps the value synched with Redis.
	"""
	def init(self, redis_key, conf_dict, *keys, type= None, values= None, check_func=None) -> None:
		self._redis_key= redis_key
		super().init(conf_dict, *keys, type=type, values=values, check_func=check_func)

	def get(self):
		if _init_redis():
			redis_value= _redisI.getImplantParam(self._redis_key, p_default=super().get())
			if self._type is not None and not isinstance(redis_value, self._type):
				try:
					return cast(redis_value, self._type)
				except:
					_logger.error(f'Error casting Redis value: returning {type(redis_value)}')
					return redis_value
			else:
				return redis_value
		else:
			return super().get()

	def set(self, p_value) -> bool:
		if not super().set(p_value):
			return False
		l_redis_updated= False
		if _init_redis():
			l_redis_updated= _redisI.updateImplantParam(self._redis_key, p_value)
		return l_redis_updated

	def reset(self) -> bool:
		l_redis_updated= False
		if _init_redis():
			l_redis_updated= _redisI.updateImplantParam(self._redis_key, self._bak_value)
		super().reset()
		return l_redis_updated

	def sync(self):
		if _init_redis():
			_logger.debug(f'Syncing {self.path()} with Redis')
			_redisI.updateImplantParam(self._redis_key, self._value)
		else:
			_logger.error(f'Cannot sync {self.path()} with Redis because Redis instance is not initialized')


class _EditablePlantConfItem(_PlantConfItem):
	"""
	Represents a special implant configuration parameter that can be changed during the execution.
	During the initialization, searches for a more updated value in Redis.
	"""
	def sync(self):
		if _init_redis():
			_logger.debug(f'Syncing {self.path()} with Redis')
			l_redis_value= _redisI.getImplantParam(self._redis_key, p_default=_MISSING)
			if l_redis_value is _MISSING:
				_redisI.updateImplantParam(self._redis_key, self._value)
			else:
				_logger.debug(f'Overwriting current conf value {self.path()} -> {self._value} with value from Redis pers: {l_redis_value}')
				self._value= l_redis_value
				self._integrity= True
		else:
			_logger.error(f'Cannot sync {self.path()} with Redis because Redis instance is not initialized')


class _SubConf():
	"""
	Represents a piece of the configuration.
	It is necessary to build the configuration object's structure.
	Provides methods to execute operations on the children (sub-configurations or parameters).
	"""
	def to_dict(self) -> dict:
		self_dict= {}
		l_items= list(filter(lambda a: not a.startswith('__') and not callable(getattr(self, a)), dir(self)))
		for l_item in l_items:
			l_item_key= l_item
			l_item= getattr(self, l_item)
			if isinstance(l_item, _SubConf):
				self_dict[l_item_key]= l_item.to_dict()
			elif isinstance(l_item, _ConfItem):
				self_dict[l_item_key]= l_item.get()
		return self_dict

	def check_integrity(self) -> bool:
		l_items= list(filter(lambda a: not a.startswith('__') and not callable(getattr(self, a)), dir(self)))
		for l_item in l_items:
			l_item= getattr(self, l_item)
			if isinstance(l_item, _SubConf) and not l_item.check_integrity():
				return False
			elif isinstance(l_item, _ConfItem) and not l_item.integrity():
				return False
		return True

	def sync_items(self):
		l_items= list(filter(lambda a: not a.startswith('__') and not callable(getattr(self, a)), dir(self)))
		for l_item in l_items:
			l_item= getattr(self, l_item)
			if isinstance(l_item, _SubConf):
				l_item.sync_items()
			elif isinstance(l_item, _PlantConfItem):
				l_item.sync()

	def reset_items(self):
		l_items= list(filter(lambda a: not a.startswith('__') and not callable(getattr(self, a)), dir(self)))
		for l_item in l_items:
			l_item= getattr(self, l_item)
			if isinstance(l_item, _SubConf):
				l_item.reset_items()
			elif isinstance(l_item, _ConfItem):
				l_item.reset()


# CONFIGURATION CLASSES
# Used to define the configuration structure
# Every class represent a sub-configuration
# Config is the main class: it includes all the sub-configurations

# MAIN / REDIS

class _conf_main_redis_cache(_SubConf):
	host= _ConfItem()
	port= _ConfItem()
	io_expire_s= _ConfItem()

class _conf_main_redis_pers(_SubConf):
	host= _ConfItem()
	port= _ConfItem()

class _conf_main_redis(_SubConf):
	cache= _conf_main_redis_cache
	pers= _conf_main_redis_pers

# MAIN / RECOVERING

class _conf_main_recovering(_SubConf):
	enabled= _ConfItem()
	remote_folder= _ConfItem()
	local_folder= _ConfItem()
	massive_start= _ConfItem()
	massive_finish= _ConfItem()
	timer_massive= _ConfItem()
	timer_normal= _ConfItem()
	recovery_timeout= _ConfItem()
	threshold= _ConfItem()

# MAIN / SW_UPDATE

class _conf_main_sw_update(_SubConf):
	package_remote_folder= _ConfItem()
	package_local_folder= _ConfItem()
	update_date_format= _ConfItem()
	update_time_format= _ConfItem()

# MAIN / MODULES_ENABLED

class _conf_main_modules_enabled(_SubConf):
	camera= _ConfItem()
	bus485= _ConfItem()
	broker= _ConfItem()

# MAIN / CONSOLE

class _conf_main_console_server(_SubConf):
	ip= _ConfItem()
	port= _ConfItem()

class _conf_main_console(_SubConf):
	server= _conf_main_console_server

# MAIN / PERIODIC

class _conf_main_periodic(_SubConf):
	enabled= _ConfItem()
	evt_flows_timeout= _ConfItem()
	periodic_check_period= _ConfItem()

# MAIN / IMPLANT_DATA

class _conf_main_implant_data(_SubConf):
	password= _PlantConfItem()
	configurazione= _PlantConfItem()
	nome_rip= _PlantConfItem()
	nome_ivip= _PlantConfItem()
	nome_linea= _PlantConfItem()
	coord_impianto= _PlantConfItem()
	prrA_bin= _PlantConfItem()
	prrB_bin= _PlantConfItem()
	wire_calib_pari= _PlantConfItem()
	wire_calib_dispari= _PlantConfItem()
	ip_remoto= _PlantConfItem()
	loc_tratta_pari_inizio = _PlantConfItem()
	loc_tratta_pari_fine = _PlantConfItem()
	loc_tratta_dispari_inizio = _PlantConfItem()
	loc_tratta_dispari_fine = _PlantConfItem()
	cod_pic_tratta_pari= _PlantConfItem()
	cod_pic_tratta_dispari= _PlantConfItem()
	distanza_prr_IT_pari= _EditablePlantConfItem()
	distanza_prr_IT_dispari= _EditablePlantConfItem()
	t_mosf_prrA= _EditablePlantConfItem()
	t_mosf_prrB= _EditablePlantConfItem()
	t_off_ivip_prrA= _EditablePlantConfItem()
	t_off_ivip_prrB= _EditablePlantConfItem()
	fov= _PlantConfItem()
	sensor_width= _PlantConfItem()
	focal_distance= _PlantConfItem()
	camera_brand= _PlantConfItem()
	camera_model= _PlantConfItem()

# MAIN / SSHFS

class _conf_main_sshfs(_SubConf):
	ip= _ConfItem()
	user= _ConfItem()
	ssh_key= _ConfItem()
	stg_folder= _ConfItem()
	rip_folder= _ConfItem()

# MAIN / NTP

class _conf_main_ntp(_SubConf):
	enabled= _ConfItem()
	ip= _ConfItem()
	timezone= _ConfItem()
	sync_interval= _ConfItem()

# MAIN / PING

class _conf_main_ping(_SubConf):
	enabled= _ConfItem()
	cameras_ping_interval= _ConfItem()
	servers_ping_interval= _ConfItem()

class _conf_main_settings(_SubConf):
	wait_mosf= _ConfItem()
	trim_mosf_data= _ConfItem()

# MAIN

class _conf_main(_SubConf):
	redis= _conf_main_redis()
	recovering= _conf_main_recovering()
	sw_update= _conf_main_sw_update()
	modules_enabled= _conf_main_modules_enabled()
	console= _conf_main_console()
	periodic= _conf_main_periodic()
	implant_data= _conf_main_implant_data()
	sshfs= _conf_main_sshfs()
	ntp= _conf_main_ntp()
	ping= _conf_main_ping()
	settings= _conf_main_settings()

# CAMERA / IDS

class _conf_camera_ids_prrA(_SubConf):
	id_1= _ConfItem()
	id_2= _ConfItem()
	id_3= _ConfItem()
	id_4= _ConfItem()
	id_5= _ConfItem()
	id_6= _ConfItem()
	ip_1= _ConfItem()
	ip_2= _ConfItem()
	ip_3= _ConfItem()
	ip_4= _ConfItem()
	ip_5= _ConfItem()
	ip_6= _ConfItem()

class _conf_camera_ids_prrB(_SubConf):
	id_1= _ConfItem()
	id_2= _ConfItem()
	id_3= _ConfItem()
	id_4= _ConfItem()
	id_5= _ConfItem()
	id_6= _ConfItem()
	ip_1= _ConfItem()
	ip_2= _ConfItem()
	ip_3= _ConfItem()
	ip_4= _ConfItem()
	ip_5= _ConfItem()
	ip_6= _ConfItem()

class _conf_camera_ids(_SubConf):
	prrA= _conf_camera_ids_prrA()
	prrB= _conf_camera_ids_prrB()

# CAMERA / XML_FILES

class _conf_camera_xml_files_prrA(_SubConf):
	xml_1= _ConfItem()
	xml_2= _ConfItem()
	xml_3= _ConfItem()
	xml_4= _ConfItem()
	xml_5= _ConfItem()
	xml_6= _ConfItem()

class _conf_camera_xml_files_prrB(_SubConf):
	xml_1= _ConfItem()
	xml_2= _ConfItem()
	xml_3= _ConfItem()
	xml_4= _ConfItem()
	xml_5= _ConfItem()
	xml_6= _ConfItem()

class _conf_camera_xml_files(_SubConf):
	prrA= _conf_camera_xml_files_prrA()
	prrB= _conf_camera_xml_files_prrB()

# CAMERA

class _conf_camera(_SubConf):
	ids= _conf_camera_ids()
	xml_files= _conf_camera_xml_files()
	process_type= _ConfItem()
	default_path= _ConfItem()
	simultaneous_dls= _ConfItem()
	trigger_timeout= _ConfItem()
	max_frame_dl_time= _ConfItem()
	event_timeout= _ConfItem()
	restart_attempts= _ConfItem()
	ready_timeout = _ConfItem()

# IO

class _conf_io(_SubConf):
	device= _ConfItem()
	speed= _ConfItem()
	timeout= _ConfItem()
	parity= _ConfItem()
	stopbits= _ConfItem()
	cts= _ConfItem()
	timeoutAnswer= _ConfItem()
	retries= _ConfItem()
	set_linux_permissions = _ConfItem()

# BROKER

class _conf_broker_consume(_SubConf):
	broker= _ConfItem()
	group= _ConfItem()
	topic_req= _ConfItem()

class _conf_broker_produce(_SubConf):
	broker= _ConfItem()
	group= _ConfItem()
	timeout= _ConfItem()

class _conf_broker(_SubConf):
	consume= _conf_broker_consume()
	produce= _conf_broker_produce()

# BOOT

class _conf_boot(_SubConf):
	exec_dir= _ConfItem()
	default_exec_path= _ConfItem()
	last_version_key= _ConfItem()
	rig_start_timestamp_key= _ConfItem()
	rig_termination_key= _ConfItem()
	boot_check_timeout= _ConfItem()
	exec_watch_interval= _ConfItem()
	alive_key= _ConfItem()

# LOGGING / BUS

class _conf_logging_bus(_SubConf):
	format= _ConfItem()
	formatter= _ConfItem()
	console_level= _ConfItem()
	file_level= _ConfItem()
	file_dir= _ConfItem()
	file_name= _ConfItem()
	file_mode= _ConfItem()
	memory_threshold= _ConfItem()
	log_to_root= _ConfItem()

# LOGGING / CAMERA

class _conf_logging_camera(_SubConf):
	format= _ConfItem()
	formatter= _ConfItem()
	console_level= _ConfItem()
	file_level= _ConfItem()
	file_dir= _ConfItem()
	file_name= _ConfItem()
	file_mode= _ConfItem()
	memory_threshold= _ConfItem()
	log_to_root= _ConfItem()

# LOGGING / CONSOLE

class _conf_logging_console(_SubConf):
	format= _ConfItem()
	formatter= _ConfItem()
	console_level= _ConfItem()
	file_level= _ConfItem()
	file_dir= _ConfItem()
	file_name= _ConfItem()
	file_mode= _ConfItem()
	memory_threshold= _ConfItem()
	log_to_root= _ConfItem()

# LOGGING / FLOW

class _conf_logging_flow(_SubConf):
	format= _ConfItem()
	formatter= _ConfItem()
	console_level= _ConfItem()
	file_level= _ConfItem()
	file_dir= _ConfItem()
	file_name= _ConfItem()
	file_mode= _ConfItem()
	memory_threshold= _ConfItem()
	log_to_root= _ConfItem()

# LOGGING / KAFKA

class _conf_logging_kafka(_SubConf):
	format= _ConfItem()
	formatter= _ConfItem()
	console_level= _ConfItem()
	file_level= _ConfItem()
	file_dir= _ConfItem()
	file_name= _ConfItem()
	file_mode= _ConfItem()
	memory_threshold= _ConfItem()
	log_to_root= _ConfItem()

# LOGGING / ROOT

class _conf_logging_root(_SubConf):
	format= _ConfItem()
	formatter= _ConfItem()
	console_level= _ConfItem()
	file_level= _ConfItem()
	file_dir= _ConfItem()
	file_name= _ConfItem()
	file_mode= _ConfItem()
	memory_threshold= _ConfItem()

# LOGGING

class _conf_logging(_SubConf):
	renew_log_files = _ConfItem()
	renewal_time = _ConfItem()
	delete_older_logs = _ConfItem()
	days_to_keep = _ConfItem()
	bus= _conf_logging_bus()
	camera= _conf_logging_camera()
	console= _conf_logging_console()
	flow= _conf_logging_flow()
	kafka= _conf_logging_kafka()
	root= _conf_logging_root()


# CONFIGURATION OBJECT

class Config():
	"""
	Contains all the configuration parameters in nested objects.
	It is organized like a tree, where the leaves are the configuration's parameters.
	"""
	def __init__(self, conf_dict: dict) -> None:
		# CONFIGURATION MAIN CATEGORIES
		self.main= _conf_main()
		self.camera= _conf_camera()
		self.io= _conf_io()
		self.broker= _conf_broker()
		self.boot= _conf_boot()
		self.logging= _conf_logging()
		self._subconfs: list[_SubConf]= [self.main, self.camera, self.io, self.broker, self.boot]

		# MAIN
			# REDIS
				# CACHE
		self.main.redis.cache.host.init(conf_dict, 'main', 'redis', 'cache', 'host')
		self.main.redis.cache.port.init(conf_dict, 'main', 'redis', 'cache', 'port')
		self.main.redis.cache.io_expire_s.init(conf_dict, 'main', 'redis', 'cache', 'io_expire_s', type=int)
				# PERS
		self.main.redis.pers.host.init(conf_dict, 'main', 'redis', 'pers', 'host')
		self.main.redis.pers.port.init(conf_dict, 'main', 'redis', 'pers', 'port')
			# RECOVERING
		self.main.recovering.enabled.init(conf_dict, 'main', 'recovering', 'enabled', type=bool)
		self.main.recovering.remote_folder.init(conf_dict, 'main', 'recovering', 'remote_folder')
		self.main.recovering.local_folder.init(conf_dict, 'main', 'recovering', 'local_folder')
		self.main.recovering.massive_start.init(conf_dict, 'main', 'recovering', 'massive_start')
		self.main.recovering.massive_finish.init(conf_dict, 'main', 'recovering', 'massive_finish')
		self.main.recovering.timer_massive.init(conf_dict, 'main', 'recovering', 'timer_massive', type=(int, float))
		self.main.recovering.timer_normal.init(conf_dict, 'main', 'recovering', 'timer_normal', type=(int, float))
		self.main.recovering.recovery_timeout.init(conf_dict, 'main', 'recovering', 'recovery_timeout', type=(int, float))
		self.main.recovering.threshold.init(conf_dict, 'main', 'recovering', 'threshold', type=int)
			# SW UPDATE
		self.main.sw_update.package_remote_folder.init(conf_dict, 'main', 'sw_update', 'package_remote_folder')
		self.main.sw_update.package_local_folder.init(conf_dict, 'main', 'sw_update', 'package_local_folder')
		self.main.sw_update.update_date_format.init(conf_dict, 'main', 'sw_update', 'update_date_format')
		self.main.sw_update.update_time_format.init(conf_dict, 'main', 'sw_update', 'update_time_format')
			# MODULES ENABLED
		self.main.modules_enabled.camera.init(conf_dict, 'main', 'modules_enabled', 'camera')
		self.main.modules_enabled.bus485.init(conf_dict, 'main', 'modules_enabled', '485')
		self.main.modules_enabled.broker.init(conf_dict, 'main', 'modules_enabled', 'broker')
			# CONSOLE
				# SERVER
		self.main.console.server.ip.init(conf_dict, 'main', 'console', 'server', 'ip')
		self.main.console.server.port.init(conf_dict, 'main', 'console', 'server', 'port')
			# PERIODIC
		self.main.periodic.enabled.init(conf_dict, 'main', 'periodic', 'enabled')
		self.main.periodic.evt_flows_timeout.init(conf_dict, 'main', 'periodic', 'evt_flows_timeout', type=int)
		self.main.periodic.periodic_check_period.init(conf_dict, 'main', 'periodic', 'periodic_check_period', type=int)
			# IMPLANT DATA
		self.main.implant_data.password.init(redis_keys.implant.rip_password, conf_dict, 'main', 'implant_data', 'password')
		self.main.implant_data.configurazione.init(redis_keys.implant.rip_config, conf_dict, 'main', 'implant_data', 'configurazione', values=list(conf_values.binario))
		self.main.implant_data.nome_rip.init(redis_keys.implant.rip_name, conf_dict, 'main', 'implant_data', 'nome_rip')
		self.main.implant_data.nome_ivip.init(redis_keys.implant.plant_name, conf_dict, 'main', 'implant_data', 'nome_ivip')
		self.main.implant_data.nome_linea.init(redis_keys.implant.line_name, conf_dict, 'main', 'implant_data', 'nome_linea')
		self.main.implant_data.coord_impianto.init(redis_keys.implant.plant_coord, conf_dict, 'main', 'implant_data', 'coord_impianto')
		self.main.implant_data.prrA_bin.init(redis_keys.implant.prrA, conf_dict, 'main', 'implant_data', 'prrA_bin')
		self.main.implant_data.prrB_bin.init(redis_keys.implant.prrB, conf_dict, 'main', 'implant_data', 'prrB_bin')
		self.main.implant_data.wire_calib_pari.init(redis_keys.implant.wire_calib_pari, conf_dict, 'main', 'implant_data', 'wire_calib_pari')
		self.main.implant_data.wire_calib_dispari.init(redis_keys.implant.wire_calib_dispari, conf_dict, 'main', 'implant_data', 'wire_calib_dispari')
		self.main.implant_data.ip_remoto.init(redis_keys.implant.ip_remoto, conf_dict, 'main', 'implant_data', 'ip_remoto')
		self.main.implant_data.loc_tratta_pari_inizio.init(redis_keys.implant.loc_tratta_pari_inizio, conf_dict, 'main', 'implant_data', 'loc_tratta_pari_inizio')
		self.main.implant_data.loc_tratta_pari_fine.init(redis_keys.implant.loc_tratta_pari_fine, conf_dict, 'main', 'implant_data', 'loc_tratta_pari_fine')
		self.main.implant_data.loc_tratta_dispari_inizio.init(redis_keys.implant.loc_tratta_dispari_inizio, conf_dict, 'main', 'implant_data', 'loc_tratta_dispari_inizio')
		self.main.implant_data.loc_tratta_dispari_fine.init(redis_keys.implant.loc_tratta_dispari_fine, conf_dict, 'main', 'implant_data', 'loc_tratta_dispari_fine')
		self.main.implant_data.cod_pic_tratta_pari.init(redis_keys.implant.cod_pic_tratta_pari, conf_dict, 'main', 'implant_data', 'cod_pic_tratta_pari')
		self.main.implant_data.cod_pic_tratta_dispari.init(redis_keys.implant.cod_pic_tratta_dispari, conf_dict, 'main', 'implant_data', 'cod_pic_tratta_dispari')
		self.main.implant_data.distanza_prr_IT_pari.init(redis_keys.implant.distanza_prr_IT_pari, conf_dict, 'main', 'implant_data', 'distanza_prr_IT_pari', type=int)
		self.main.implant_data.distanza_prr_IT_dispari.init(redis_keys.implant.distanza_prr_IT_dispari, conf_dict, 'main', 'implant_data', 'distanza_prr_IT_dispari', type=int)
		self.main.implant_data.t_mosf_prrA.init(redis_keys.implant.t_mosf_prrA, conf_dict, 'main', 'implant_data', 't_mosf_prrA', type=int)
		self.main.implant_data.t_mosf_prrB.init(redis_keys.implant.t_mosf_prrB, conf_dict, 'main', 'implant_data', 't_mosf_prrB', type=int)
		self.main.implant_data.t_off_ivip_prrA.init(redis_keys.implant.t_off_ivip_prrA, conf_dict, 'main', 'implant_data', 't_off_ivip_prrA', type=int)
		self.main.implant_data.t_off_ivip_prrB.init(redis_keys.implant.t_off_ivip_prrB, conf_dict, 'main', 'implant_data', 't_off_ivip_prrB', type=int)
		self.main.implant_data.fov.init(redis_keys.implant.camera_fov, conf_dict, 'main', 'implant_data', 'fov')
		self.main.implant_data.sensor_width.init(redis_keys.implant.camera_sensor_width, conf_dict, 'main', 'implant_data', 'sensor_width')
		self.main.implant_data.focal_distance.init(redis_keys.implant.camera_focal_distance, conf_dict, 'main', 'implant_data', 'focal_distance')
		self.main.implant_data.camera_brand.init(redis_keys.implant.camera_brand, conf_dict, 'main', 'implant_data', 'camera_brand')
		self.main.implant_data.camera_model.init(redis_keys.implant.camera_model, conf_dict, 'main', 'implant_data', 'camera_model')
			# SSHFS
		self.main.sshfs.ip.init(conf_dict, 'main', 'sshfs', 'ip')
		self.main.sshfs.user.init(conf_dict, 'main', 'sshfs', 'user')
		self.main.sshfs.ssh_key.init(conf_dict, 'main', 'sshfs', 'ssh_key')
		self.main.sshfs.stg_folder.init(conf_dict, 'main', 'sshfs', 'stg_folder')
		self.main.sshfs.rip_folder.init(conf_dict, 'main', 'sshfs', 'rip_folder')
			# NTP
		self.main.ntp.enabled.init(conf_dict, 'main', 'ntp', 'enabled', type=bool)
		self.main.ntp.ip.init(conf_dict, 'main', 'ntp', 'ip', type=str)
		self.main.ntp.timezone.init(conf_dict, 'main', 'ntp', 'timezone', type=str)
		self.main.ntp.sync_interval.init(conf_dict, 'main', 'ntp', 'sync_interval', type=(int, float))
			# PING
		self.main.ping.enabled.init(conf_dict, 'main', 'ping', 'enabled', type=bool)
		self.main.ping.cameras_ping_interval.init(conf_dict, 'main', 'ping', 'cameras_ping_interval', type=(int, float))
		self.main.ping.servers_ping_interval.init(conf_dict, 'main', 'ping', 'servers_ping_interval', type=(int, float))
			# SETTINGS
		self.main.settings.wait_mosf.init(conf_dict, 'main', 'settings', 'wait_mosf', type=bool)
		self.main.settings.trim_mosf_data.init(conf_dict, 'main', 'settings', 'trim_mosf_data', type=bool)
		# CAMERA
			# IDS
				# PRRA
		self.camera.ids.prrA.id_1.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_id_1')
		self.camera.ids.prrA.id_2.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_id_2')
		self.camera.ids.prrA.id_3.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_id_3')
		self.camera.ids.prrA.id_4.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_id_4')
		self.camera.ids.prrA.id_5.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_id_5')
		self.camera.ids.prrA.id_6.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_id_6')
		self.camera.ids.prrA.ip_1.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_ip_1')
		self.camera.ids.prrA.ip_2.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_ip_2')
		self.camera.ids.prrA.ip_3.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_ip_3')
		self.camera.ids.prrA.ip_4.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_ip_4')
		self.camera.ids.prrA.ip_5.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_ip_5')
		self.camera.ids.prrA.ip_6.init(conf_dict, 'camera', 'ids', 'prrA', 'camera_prrA_ip_6')
				# PRRB
		self.camera.ids.prrB.id_1.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_id_1')
		self.camera.ids.prrB.id_2.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_id_2')
		self.camera.ids.prrB.id_3.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_id_3')
		self.camera.ids.prrB.id_4.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_id_4')
		self.camera.ids.prrB.id_5.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_id_5')
		self.camera.ids.prrB.id_6.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_id_6')
		self.camera.ids.prrB.ip_1.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_ip_1')
		self.camera.ids.prrB.ip_2.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_ip_2')
		self.camera.ids.prrB.ip_3.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_ip_3')
		self.camera.ids.prrB.ip_4.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_ip_4')
		self.camera.ids.prrB.ip_5.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_ip_5')
		self.camera.ids.prrB.ip_6.init(conf_dict, 'camera', 'ids', 'prrB', 'camera_prrB_ip_6')
			# XML_FILES
				# PRRA
		self.camera.xml_files.prrA.xml_1.init(conf_dict, 'camera', 'xml_files', 'prrA', 'camera_prrA_xml_1')
		self.camera.xml_files.prrA.xml_2.init(conf_dict, 'camera', 'xml_files', 'prrA', 'camera_prrA_xml_2')
		self.camera.xml_files.prrA.xml_3.init(conf_dict, 'camera', 'xml_files', 'prrA', 'camera_prrA_xml_3')
		self.camera.xml_files.prrA.xml_4.init(conf_dict, 'camera', 'xml_files', 'prrA', 'camera_prrA_xml_4')
		self.camera.xml_files.prrA.xml_5.init(conf_dict, 'camera', 'xml_files', 'prrA', 'camera_prrA_xml_5')
		self.camera.xml_files.prrA.xml_6.init(conf_dict, 'camera', 'xml_files', 'prrA', 'camera_prrA_xml_6')
				# PRRB
		self.camera.xml_files.prrB.xml_1.init(conf_dict, 'camera', 'xml_files', 'prrB', 'camera_prrB_xml_1')
		self.camera.xml_files.prrB.xml_2.init(conf_dict, 'camera', 'xml_files', 'prrB', 'camera_prrB_xml_2')
		self.camera.xml_files.prrB.xml_3.init(conf_dict, 'camera', 'xml_files', 'prrB', 'camera_prrB_xml_3')
		self.camera.xml_files.prrB.xml_4.init(conf_dict, 'camera', 'xml_files', 'prrB', 'camera_prrB_xml_4')
		self.camera.xml_files.prrB.xml_5.init(conf_dict, 'camera', 'xml_files', 'prrB', 'camera_prrB_xml_5')
		self.camera.xml_files.prrB.xml_6.init(conf_dict, 'camera', 'xml_files', 'prrB', 'camera_prrB_xml_6')
		#
		self.camera.process_type.init(conf_dict, 'camera', 'process_type')
		self.camera.default_path.init(conf_dict, 'camera', 'default_path')
		self.camera.simultaneous_dls.init(conf_dict, 'camera', 'simultaneous_dls', type=int)
		self.camera.trigger_timeout.init(conf_dict, 'camera', 'trigger_timeout', type=(int, float))
		self.camera.max_frame_dl_time.init(conf_dict, 'camera', 'max_frame_dl_time', type=(int, float))
		self.camera.event_timeout.init(conf_dict, 'camera', 'event_timeout', type=(int, float))
		self.camera.restart_attempts.init(conf_dict, 'camera', 'restart_attempts', type=int)
		self.camera.ready_timeout.init(conf_dict, 'camera', 'ready_timeout', type=int)
		# IO
		self.io.device.init(conf_dict, 'io', 'device')
		self.io.speed.init(conf_dict, 'io', 'speed', type=int)
		self.io.timeout.init(conf_dict, 'io', 'timeout', type=(int, float))
		self.io.parity.init(conf_dict, 'io', 'parity')
		self.io.stopbits.init(conf_dict, 'io', 'stopbits', type=int)
		self.io.cts.init(conf_dict, 'io', 'cts', type=int)
		self.io.timeoutAnswer.init(conf_dict, 'io', 'timeoutAnswer', type=(int, float))
		self.io.retries.init(conf_dict, 'io', 'retries', type=int)
		self.io.set_linux_permissions.init(conf_dict, 'io', 'set_linux_permissions', type=bool)
		# BROKER
			# CONSUME
		self.broker.consume.broker.init(conf_dict, 'broker', 'consume', 'broker')
		self.broker.consume.group.init(conf_dict, 'broker', 'consume', 'group')
		self.broker.consume.topic_req.init(conf_dict, 'broker', 'consume', 'topic_req', type=list)
			# PRODUCE
		self.broker.produce.broker.init(conf_dict, 'broker', 'produce', 'broker')
		self.broker.produce.group.init(conf_dict, 'broker', 'produce', 'group')
		self.broker.produce.timeout.init(conf_dict, 'broker', 'produce', 'timeout', type=(int, float))
		# BOOT
		self.boot.exec_dir.init(conf_dict, 'boot', 'exec_dir')
		self.boot.default_exec_path.init(conf_dict, 'boot', 'default_exec_path')
		self.boot.last_version_key.init(conf_dict, 'boot', 'last_version_key')
		self.boot.rig_start_timestamp_key.init(conf_dict, 'boot', 'rig_start_timestamp_key')
		self.boot.rig_termination_key.init(conf_dict, 'boot', 'rig_termination_key')
		self.boot.boot_check_timeout.init(conf_dict, 'boot', 'boot_check_timeout', type=(int, float))
		self.boot.exec_watch_interval.init(conf_dict, 'boot', 'exec_watch_interval', type=(int, float))
		self.boot.alive_key.init(conf_dict, 'boot', 'alive_key')
		# LOGGING
		self.logging.renew_log_files.init(conf_dict, 'logging', 'renew_log_files', type=bool)
		self.logging.renewal_time.init(conf_dict, 'logging', 'renewal_time', type=str, check_func=_check_time)
		self.logging.delete_older_logs.init(conf_dict, 'logging', 'delete_older_logs', type=bool)
		self.logging.days_to_keep.init(conf_dict, 'logging', 'days_to_keep', type=int, check_func=_check_positive)
			# BUS
		self.logging.bus.format.init(conf_dict, 'logging', 'bus', 'format', type=str)
		self.logging.bus.formatter.init(conf_dict, 'logging', 'bus', 'formatter', values=list(conf_values.log_formatter))
		self.logging.bus.console_level.init(conf_dict, 'logging', 'bus', 'console_level', type=int)
		self.logging.bus.file_level.init(conf_dict, 'logging', 'bus', 'file_level', type=int)
		self.logging.bus.file_dir.init(conf_dict, 'logging', 'bus', 'file_dir', type=str)
		self.logging.bus.file_name.init(conf_dict, 'logging', 'bus', 'file_name', type=str)
		self.logging.bus.file_mode.init(conf_dict, 'logging', 'bus', 'file_mode', values=list(conf_values.log_file_mode))
		self.logging.bus.memory_threshold.init(conf_dict, 'logging', 'bus', 'memory_threshold', type=int)
		self.logging.bus.log_to_root.init(conf_dict, 'logging', 'bus', 'log_to_root', type=bool)
			# CAMERA
		self.logging.camera.format.init(conf_dict, 'logging', 'camera', 'format', type=str)
		self.logging.camera.formatter.init(conf_dict, 'logging', 'camera', 'formatter', values=list(conf_values.log_formatter))
		self.logging.camera.console_level.init(conf_dict, 'logging', 'camera', 'console_level', type=int)
		self.logging.camera.file_level.init(conf_dict, 'logging', 'camera', 'file_level', type=int)
		self.logging.camera.file_dir.init(conf_dict, 'logging', 'camera', 'file_dir', type=str)
		self.logging.camera.file_name.init(conf_dict, 'logging', 'camera', 'file_name', type=str)
		self.logging.camera.file_mode.init(conf_dict, 'logging', 'camera', 'file_mode', values=list(conf_values.log_file_mode))
		self.logging.camera.memory_threshold.init(conf_dict, 'logging', 'camera', 'memory_threshold', type=int)
		self.logging.camera.log_to_root.init(conf_dict, 'logging', 'camera', 'log_to_root', type=bool)
			# CONSOLE
		self.logging.console.format.init(conf_dict, 'logging', 'console', 'format', type=str)
		self.logging.console.formatter.init(conf_dict, 'logging', 'console', 'formatter', values=list(conf_values.log_formatter))
		self.logging.console.console_level.init(conf_dict, 'logging', 'console', 'console_level', type=int)
		self.logging.console.file_level.init(conf_dict, 'logging', 'console', 'file_level', type=int)
		self.logging.console.file_dir.init(conf_dict, 'logging', 'console', 'file_dir', type=str)
		self.logging.console.file_name.init(conf_dict, 'logging', 'console', 'file_name', type=str)
		self.logging.console.file_mode.init(conf_dict, 'logging', 'console', 'file_mode', values=list(conf_values.log_file_mode))
		self.logging.console.memory_threshold.init(conf_dict, 'logging', 'console', 'memory_threshold', type=int)
		self.logging.console.log_to_root.init(conf_dict, 'logging', 'console', 'log_to_root', type=bool)
			# FLOW
		self.logging.flow.format.init(conf_dict, 'logging', 'flow', 'format', type=str)
		self.logging.flow.formatter.init(conf_dict, 'logging', 'flow', 'formatter', values=list(conf_values.log_formatter))
		self.logging.flow.console_level.init(conf_dict, 'logging', 'flow', 'console_level', type=int)
		self.logging.flow.file_level.init(conf_dict, 'logging', 'flow', 'file_level', type=int)
		self.logging.flow.file_dir.init(conf_dict, 'logging', 'flow', 'file_dir', type=str)
		self.logging.flow.file_name.init(conf_dict, 'logging', 'flow', 'file_name', type=str)
		self.logging.flow.file_mode.init(conf_dict, 'logging', 'flow', 'file_mode', values=list(conf_values.log_file_mode))
		self.logging.flow.memory_threshold.init(conf_dict, 'logging', 'flow', 'memory_threshold', type=int)
		self.logging.flow.log_to_root.init(conf_dict, 'logging', 'flow', 'log_to_root', type=bool)
			# KAFKA
		self.logging.kafka.format.init(conf_dict, 'logging', 'kafka', 'format', type=str)
		self.logging.kafka.formatter.init(conf_dict, 'logging', 'kafka', 'formatter', values=list(conf_values.log_formatter))
		self.logging.kafka.console_level.init(conf_dict, 'logging', 'kafka', 'console_level', type=int)
		self.logging.kafka.file_level.init(conf_dict, 'logging', 'kafka', 'file_level', type=int)
		self.logging.kafka.file_dir.init(conf_dict, 'logging', 'kafka', 'file_dir', type=str)
		self.logging.kafka.file_name.init(conf_dict, 'logging', 'kafka', 'file_name', type=str)
		self.logging.kafka.file_mode.init(conf_dict, 'logging', 'kafka', 'file_mode', values=list(conf_values.log_file_mode))
		self.logging.kafka.memory_threshold.init(conf_dict, 'logging', 'kafka', 'memory_threshold', type=int)
		self.logging.kafka.log_to_root.init(conf_dict, 'logging', 'kafka', 'log_to_root', type=bool)
			# ROOT
		self.logging.root.format.init(conf_dict, 'logging', 'root', 'format', type=str)
		self.logging.root.formatter.init(conf_dict, 'logging', 'root', 'formatter', values=list(conf_values.log_formatter))
		self.logging.root.console_level.init(conf_dict, 'logging', 'root', 'console_level', type=int)
		self.logging.root.file_level.init(conf_dict, 'logging', 'root', 'file_level', type=int)
		self.logging.root.file_dir.init(conf_dict, 'logging', 'root', 'file_dir', type=str)
		self.logging.root.file_name.init(conf_dict, 'logging', 'root', 'file_name', type=str)
		self.logging.root.file_mode.init(conf_dict, 'logging', 'root', 'file_mode', values=list(conf_values.log_file_mode))
		self.logging.root.memory_threshold.init(conf_dict, 'logging', 'root', 'memory_threshold', type=int)

	def check_configuration_integrity(self) -> bool:
		"""
		Checks integrity for all the sub-configurations.
		This operation is recursive and reaches the leaves (the parameters).
		If at least one integrity check fails, return False.
		"""
		for l_subconf in self._subconfs:
			if l_subconf.check_integrity() is False:
				return False
		return True

	def sync_with_redis(self) -> None:
		"""
		Calls the sync function for every parameter.
		Only some of them need to sync with Redis. 
		"""
		for l_subconf in self._subconfs:
			l_subconf.sync_items()
	
	def reset_configuration(self) -> None:
		"""
		Calls the reset function for every parameter.
		The reset function restore the original parameter value, 
		if it changed during the program execution.
		"""
		for l_subconf in self._subconfs:
			l_subconf.reset_items()


# SINGLETON

_config: Config= None


def init_configuration(conf_dict: dict) -> None:
	global _config, _redisI
	if _config is not None:
		_logger.warning('Tried to initialize configuration more than once. Ignoring...')
		return
	_config= Config(conf_dict)


def get_config() -> Optional[Config]:
	if not isinstance(_config, Config):
		_logger.error('Configuration not initialized')
		return None
	return _config


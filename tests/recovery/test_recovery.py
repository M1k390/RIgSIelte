from datetime import datetime, timedelta
import json
from queue import Queue

from rigproc.commons.logger import logging_manager
from rigproc.commons.config import init_configuration, get_config
from rigproc.commons.redisi import initialize_redis, get_redisI
from rigproc.commons.helper import helper

from rigproc.central.recovery_manager import RecoveryManager

from rigproc.commons.entities import EventToRecover, CameraEvent, CameraShoot, CameraShootArray
from rigproc.params import internal, redis_keys


m_logger= logging_manager.generate_logger(
	logger_name='root',
	format_code='TEST %(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s',
	console_level=10,
	file_level=10,
	log_file_name='',
	log_file_dir='',
	log_file_mode='append',
	root_log_file_prefix=None,
	root_log_dir=None,
	print_to_console=True,
	formatter_setting='color'
)

m_queue= Queue()
m_core= {
	'cmd_q': m_queue
}

# Init config and Redis
# Initialize configuration
conf_file= helper.data_file_path('conf_001.json')
with open(conf_file, 'r') as cf:
	conf_dict= json.load(cf)
init_configuration(conf_dict)
initialize_redis(
	get_config().main.redis.cache.host.get(),
	get_config().main.redis.cache.port.get(),
	get_config().main.redis.pers.host.get(),
	get_config().main.redis.pers.port.get(),
)

# Copy image sample
source_file= helper.data_file_path('sample_image.data')
image_dir= helper.join_paths(helper.abs_path(get_config().main.recovering.local_folder.get()), 'test')
#helper.dir_exists_create(image_dir)
IMAGE_PATH= helper.join_paths(image_dir, 'sample_image.data')
#helper.copy_file(source_file, IMAGE_PATH)

# Init event params
shoot= CameraShoot('TEST_CAM_01', 1, IMAGE_PATH)
shoot_array= CameraShootArray(helper.timestampNow(), [shoot], helper.new_trans_id())
event_id= 'test_event_recovery'
remote_folder= helper.join_paths(
	get_config().main.recovering.remote_folder.get(),
	event_id
)
helper.dir_exists_create(remote_folder)

# Create event to recover
m_event= EventToRecover(
	shoot_array,
	event_id,
	remote_folder,
	'',
	'',
	''
)

m_rm= RecoveryManager(m_core)


def test_store_event():
	m_rm.store_event(m_event)
	assert m_event in m_rm.m_events_to_recover
	assert get_redisI().pers.get(f'{redis_keys.recovery.key_prefix}{m_event.timestamp}', p_default=None) is not None


def test_request_flow_recovery():
	m_rm._request_flow_recovery(m_event)
	assert m_event not in m_rm.m_events_to_recover
	assert m_event in m_rm.m_pending_recoveries
	assert m_event.m_recovery_start is not None
	l_cmd= m_queue.get(block=False)
	assert isinstance(l_cmd, dict) and l_cmd[internal.cmd_key.evt_to_recover] is m_event


def test_recovery_failure():
	m_rm.recovery_failure(m_event)
	assert m_event not in m_rm.m_pending_recoveries
	assert m_event in m_rm.m_events_to_recover


def test_recovery_success():
	m_rm._request_flow_recovery(m_event)
	m_rm.recovery_success(m_event)
	assert m_event not in m_rm.m_events_to_recover
	assert m_event not in m_rm.m_pending_recoveries
	assert get_redisI().pers.get(f'{redis_keys.recovery.key_prefix}{m_event.timestamp}', p_default=None) is None


def	test_clear_event():
	m_rm._clear_event(m_event)
	assert not helper.file_exists(m_event.shoot_array.shoots[0].img_path)


def test_is_massive_time():
	m_rm.m_massive_time_start= helper.onlyTimeNowObj()
	m_rm.m_massive_time_end= helper.onlyTimeNowObj() + timedelta(minutes=30)
	assert m_rm._is_massive_time()
	
	m_rm.m_massive_time_start= helper.onlyTimeNowObj() - timedelta(minutes=60)
	m_rm.m_massive_time_end= helper.onlyTimeNowObj() - timedelta(minutes=30)
	assert not m_rm._is_massive_time()


def test_switch_mode():
	m_rm.m_active= False
	
	m_rm.m_massive_time_start= helper.onlyTimeNowObj()
	m_rm.m_massive_time_end= helper.onlyTimeNowObj() + timedelta(minutes=30)
	m_rm._switch_mode()
	m_rm.m_timer.cancel()
	assert m_rm.m_massive_mode
	
	m_rm.m_massive_time_start= helper.onlyTimeNowObj() - timedelta(minutes=60)
	m_rm.m_massive_time_end= helper.onlyTimeNowObj() - timedelta(minutes=30)
	m_rm._switch_mode()
	m_rm.m_timer.cancel()
	assert not m_rm.m_massive_mode


import os
import json
from queue import Queue

from rigproc.flow.flow_camera_event import FlowCameraEvent

from rigproc.commons.interpreter import interpreter
from rigcam.rig_broker import init_rig_broker, get_rig_broker
from rigproc.commons.entities import CameraShootArray, CameraShoot, CameraEvent

from rigproc.commons.config import init_configuration, get_config
from rigproc.commons.redisi import initialize_redis, get_redisI

from rigproc.commons.logger import logging_manager
from rigproc.commons.helper import helper
from rigproc.params import general, internal, kafka


# Initialize loggers
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
m_flow_logger= logging_manager.generate_logger(
	logger_name='flow',
	format_code='TEST %(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s',
	console_level=10,
	file_level=10,
	log_file_name='',
	log_file_dir='',
	log_file_mode='append',
	root_log_file_prefix=None,
	root_log_dir=None,
	print_to_console=True,
	formatter_setting='alt'
)

# Init core
m_queue= Queue()
m_core= {
	'cmd_q': m_queue
}

event_key= None
camera_event= None

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
helper.dir_exists_create(image_dir)
IMAGE_PATH= helper.join_paths(image_dir, 'sample_image.data')
helper.copy_file(source_file, IMAGE_PATH)

# Initialize RIG broker
init_rig_broker(
	get_config().main.redis.cache.host.get(), 
	get_config().main.redis.cache.port.get()
)

# Get json models
with open(helper.data_file_path('kafka_json_models.json'), 'r') as f:
	m_models= json.load(f)


def test_correct_initialization():
	assert get_config().check_configuration_integrity()


def test_data_sending():
	global event_key

	# Set Redis information
	shoot= CameraShoot('TEST_CAM_01', 1, IMAGE_PATH)
	shoot_array= CameraShootArray(helper.timestampNow(), [shoot], helper.new_trans_id())
	event_key= get_rig_broker().send_event_data(shoot_array.timestamp, 'TEST_POLE', [shoot_array])
	print(event_key)

	assert event_key is not None


def test_data_reading():
	global camera_event

	if event_key is not None:
		print(f'Found event key: {event_key}')
		encoded_event= get_redisI().cache.get(event_key)
		camera_event= interpreter.decode_event(encoded_event)

	assert isinstance(camera_event, CameraEvent)


def test_flow():
	l_flow= FlowCameraEvent(m_core, camera_event)
	
	if camera_event is not None:
		l_flow.start()
		while not l_flow.is_done():
			if l_flow.is_waiting():
				cmd= m_core['cmd_q'].get()
				if cmd[internal.cmd_key.cmd_type] == internal.cmd_type.topic_evt:
					model_dict= json.loads(cmd[internal.cmd_key.json])
					if cmd[internal.cmd_key.topic] == kafka.rip_topic.evt_trigger:
						assert helper.check_dict_keys(model_dict, m_models['EventoPassaggioTreno'])
					elif cmd[internal.cmd_key.topic] == kafka.rip_topic.diag_vip_to_stg:
						assert helper.check_dict_keys(model_dict, m_models['DiagnosiSistemiIVIP_RIPtoSTG'])
					elif cmd[internal.cmd_key.topic] == kafka.rip_topic.mosf_data:
						assert helper.check_dict_keys(model_dict, m_models['MOSFvalues'])
					l_flow.callback({internal.cmd_key.topic_response: general.status_ok})
				else:
					l_flow.missed()
	
	assert l_flow.is_done()
	assert l_flow.get_errors() == []

	shoot_array= camera_event.shoot_arrays[0]
	shoot= shoot_array.shoots[0]
	remote_folder_path= l_flow.m_remote_folder_path[shoot_array]
	file_name= f'{l_flow._get_event_id(shoot_array)}_cam_{shoot.cam_num}'
	file_path= helper.join_paths(remote_folder_path, file_name)
	assert not helper.file_exists(IMAGE_PATH) # The original image was removed
	assert helper.file_exists(file_path) # The new file exists

	helper.remove_file(file_path)
	os.rmdir(remote_folder_path)
	



from pathlib import Path
import json
from pprint import pprint

from rigproc.commons.config import init_configuration, get_config, Config
from rigproc.commons.helper import helper


CONFIG_PATH= helper.data_file_path('conf_001.json')


with open(CONFIG_PATH, 'r') as f:
	conf_dict= json.loads(f.read())


print(init_configuration(conf_dict))
config= get_config()


if __name__ == '__main__':
	pprint(conf_dict)
	print(config.boot.alive_key.get())
	print(config.main.redis.cache.port.get())


def test_config_init():
	assert config is not None
	assert isinstance(config, Config)
	assert config.main.redis.cache.host.get() == conf_dict['main']['redis']['cache']['host']


def _perform_conf_integrity_check(file_name: str):
	with open(helper.data_file_path(file_name), 'r') as f:
		conf_dict= json.loads(f.read())
	config= Config(conf_dict)
	assert config.check_configuration_integrity()


def test_conf_001():
	file_name= 'conf_001.json'
	_perform_conf_integrity_check(file_name)


def test_conf_011():
	file_name= 'conf_011.json'
	_perform_conf_integrity_check(file_name)


def test_conf_101():
	file_name= 'conf_101.json'
	_perform_conf_integrity_check(file_name)


def test_conf_111():
	file_name= 'conf_111.json'
	_perform_conf_integrity_check(file_name)


def test_conf_112():
	file_name= 'conf_112.json'
	_perform_conf_integrity_check(file_name)


def test_conf_exec():
	file_name= 'conf_exec.json'
	_perform_conf_integrity_check(file_name)


def test_sielte_conf():
	file_name= 'sielte_1.1.json'
	_perform_conf_integrity_check(file_name)
	
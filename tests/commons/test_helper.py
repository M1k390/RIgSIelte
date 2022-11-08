import pytest
import json
import os
import time
from datetime import date, datetime
import asyncio

from rigproc.commons.logger import logging_manager
from rigproc.commons.config import init_configuration, get_config
from rigproc.commons.helper import helper, MAIN_DIR, Helper


TEST_FILE= None
COPIED_FILE= None
ZIP_FILE= None
UNZIPPED_FILE= None
MY_FOLDER= None


@pytest.fixture(autouse=True)
def init():
	# Initialize configuration
	conf_file= helper.data_file_path('conf_minimal.json')
	with open(conf_file, 'r') as cf:
		conf_dict= json.load(cf)
	init_configuration(conf_dict)

	# Initialize logger
	logging_manager.generate_logger(
		logger_name='root',
		format_code=get_config().logging.root.format.get(),
		console_level=get_config().logging.root.console_level.get(),
		file_level=get_config().logging.root.file_level.get(),
		log_file_name=get_config().logging.root.file_name.get(),
		log_file_dir=get_config().logging.root.file_dir.get(),
		log_file_mode=get_config().logging.root.file_mode.get(),
		root_log_file_prefix=None,
		root_log_dir=None,
		formatter_setting=get_config().logging.root.formatter.get(),
	)


# SYSTEM


def test_get_my_pid():
	my_pid = helper.get_my_pid()
	assert isinstance(my_pid, int)


def test_get_process_mem_usage():
	my_pid = helper.get_my_pid()
	my_mem = helper.get_process_mem_usage(my_pid)
	assert isinstance(my_mem, (int, float))


def test_parse_elapsed_time_str():
	et_str1 = '    ELAPSED\n      07:10\n'
	et_str2 = '    ELAPSED\n   03:07:10\n'
	et_str3 = '    ELAPSED\n 1-12:15:51\n'
	assert isinstance(helper._parse_elapsed_time_str(et_str1), int)
	assert isinstance(helper._parse_elapsed_time_str(et_str2), int)
	assert isinstance(helper._parse_elapsed_time_str(et_str3), int)


def test_get_process_uptime():
	my_pid = helper.get_my_pid()
	assert isinstance(helper.get_process_uptime(my_pid) , int)


def test_get_cpu_temperature():
	temp = helper.get_cpu_temperature()
	assert isinstance(helper.get_cpu_temperature(), float)
	assert temp < 100


# FILE OPERATIONS

def test_relative_to_abs_path():
	global TEST_FILE, COPIED_FILE, ZIP_FILE, UNZIPPED_FILE

	TEST_FILE= helper.relative_to_abs_path('test_file.txt', __file__)
	assert TEST_FILE != ''

	COPIED_FILE= helper.relative_to_abs_path('test_copy.txt', __file__)
	assert COPIED_FILE != ''

	ZIP_FILE= helper.relative_to_abs_path('test_zip.zip', __file__)
	assert ZIP_FILE != ''

	UNZIPPED_FILE= helper.relative_to_abs_path('test_compressed.txt', __file__)
	assert UNZIPPED_FILE != ''

def test_my_path():
	assert helper.my_path(__file__) == __file__

def test_file_name_from_path():
	assert helper.file_name_from_path('/test/dir/test_file') == 'test_file'

def test_dir_from_path():
	global MY_FOLDER

	MY_FOLDER= helper.dir_from_path(__file__)
	assert MY_FOLDER != ''

def test_abs_path():
	assert helper.abs_path(__file__) == __file__
	assert helper.abs_path('dir/test_file') == os.path.join(MAIN_DIR, 'dir/test_file')

def test_join_paths():
	assert helper.join_paths('/test/dir', 'test_file') == os.path.join('/test/dir', 'test_file')
	assert helper.join_paths(1, 2) == ''

def test_universal_path():
	assert helper.universal_path('/test/dir/file') == os.path.join('/', 'test', 'dir', 'file')

def test_clean_file_name():
	assert helper.clean_file_name('t-1:2(a b)*asd!') == 't-1-2(a_b)asd'

def test_data_file_path():
	assert helper.data_file_path('test_file') == os.path.join(MAIN_DIR, 'data', 'test_file')

def test_dir_exists():
	assert helper.dir_exists(MY_FOLDER)

def test_dir_exists_create():
	test_dir= os.path.join(MY_FOLDER, 'test_dir')
	assert helper.dir_exists_create(test_dir)
	os.rmdir(test_dir)

def test_file_exists():
	assert helper.file_exists(__file__)

def test_file_is_readable():
	assert helper.file_is_readable(__file__)

def test_list_file():
	assert os.path.basename(__file__) in helper.list_file_names(MY_FOLDER)

def test_count_files():
	assert helper.count_files(MY_FOLDER) >= 1

def test_copy_file():
	assert helper.copy_file(TEST_FILE, COPIED_FILE)
	assert os.path.isfile(COPIED_FILE)

def test_write_file():
	with open(TEST_FILE) as f:
		original_content= f.read()
	content= 'test di scrittura'
	helper.write_file(TEST_FILE, content)
	with open(TEST_FILE) as f:
		new_content= f.read()
	assert new_content == content
	helper.write_file(TEST_FILE, original_content)
	with open(TEST_FILE) as f:
		final_content= f.read()
	assert final_content == original_content

def test_get_file_size():
	file_size= helper.get_file_size(TEST_FILE)
	assert file_size is not None and file_size > 0

def test_remove_file():
	assert helper.remove_file(COPIED_FILE)
	assert not os.path.isfile(COPIED_FILE)

def test_remove_dir():
	test_dir= os.path.join(MY_FOLDER, 'test_dir')
	os.mkdir(test_dir)
	assert helper.remove_dir(test_dir)
	assert not os.path.isdir(test_dir)


def test_unzip_file():
	assert helper.unzip_file(ZIP_FILE, MY_FOLDER)
	assert os.path.isfile(UNZIPPED_FILE)
	os.remove(UNZIPPED_FILE)

def test_get_zip_members():
	members= helper.get_zip_members(ZIP_FILE)
	assert len(members) > 0
	assert os.path.basename(UNZIPPED_FILE) in members

def test_make_file_executable():
	made_exec= helper.make_file_executable(TEST_FILE)
	assert made_exec
	stat= os.stat(TEST_FILE)
	exec_permissions= oct(stat.st_mode & 0o777)[-3:-1]
	for exec_perm in exec_permissions:
		assert int(exec_perm) in [1, 3, 5, 7]
	os.system(f'sudo chmod a-x {TEST_FILE}')


# Network operations

def test_ping():
	assert helper.ping('localhost')
	assert helper.ping('127.0.0.1')

def test_check_kafka_broker():
	# Only test if running in localhost
	output= os.popen('ps aux | grep kafka | grep -v grep | wc -l').read()
	kafka_running= int(output) > 0
	kafka_check= helper.check_kafka_broker('localhost:9092')
	if kafka_running:
		assert kafka_check
	else:
		assert not kafka_check

def test_ip_int_to_str():
	assert helper.ip_int_to_str(192 * 16777216 + 168 * 65536 + 1 * 256 + 11) == '192.168.1.11'
	assert helper.ip_int_to_str(11 * 16777216 + 1 * 65536 + 168 * 256 + 192, vimba_std=True) == '192.168.1.11'

# Test mounting sshfs folder is omitted to avoid errors with the program execution


# Json operations

def test_remove_not_jsonable():
	class TestObj:
		pass
	test_dict= {
		'key1': 'test_content',
		'key2': TestObj()
	}

	assert 'key1' in test_dict.keys()
	assert 'key2' in test_dict.keys()

	clean_test_dict= helper._removeNotJasonable(test_dict)

	assert 'key1' in clean_test_dict.keys()
	assert 'key2' not in clean_test_dict.keys()

def test_check_dict_keys():
	l_dict1= {'a': 1, 'b': 2}
	l_dict2= {'b': 2}
	l_dict3= {'b': 2, 'c': 3}
	assert helper.check_dict_keys(l_dict1, l_dict2)
	assert not helper.check_dict_keys(l_dict1, l_dict3)
	assert not helper.check_dict_keys(l_dict2, l_dict1)


# Logging

def test_prettify():
	class TestClass:
		pass
	test_obj= TestClass()
	assert isinstance(helper.prettify('test'), str)
	assert isinstance(helper.prettify({'test': ' val'}), str)
	assert isinstance(helper.prettify(['test', 'test2']), str)
	assert helper.prettify(None) == 'None'
	assert helper.prettify(test_obj) == str(test_obj)

def test_format_bytearray():
	ba= bytearray(b'\x02@Bb0010P\xf5\x03\r\n')
	fmt_ba= helper.format_bytearray(ba)
	assert fmt_ba == '0x02 0x40 0x42 0x62 0x30 0x30 0x31 0x30 0x50 0xf5 0x03 0x0d 0x0a'
	assert type(helper.format_bytearray(1)) == str
	assert type(helper.format_bytearray('wrong type')) == str


# Timestamp

TEST_TS= '94672621500' # 2000/01/01 12:30:15:000
TEST_FTS= '2000-01-01 12:30:15'

def test_time_now_obj():
	assert helper.timeNowObj()

def test_timestamp_now_float():
	ts= helper.timestampNowFloat()
	assert isinstance(ts, int)
	assert len(str(int(time.time()))) + 2 == len(str(ts))

def test_timestamp_now():
	ts= helper.timestampNow()
	assert isinstance(ts, str)

def test_timestamp_now_formatted():
	ts= helper.timestampNowFormatted()
	assert isinstance(ts, str)

def test_time_now():
	ts= helper.timeNow()
	try:
		datetime.strptime(ts, Helper.TIME_FORMAT)
		ok= True
	except:
		ok= False
	assert ok

def test_date_now():
	ts= helper.dateNow()
	try:
		datetime.strptime(ts, Helper.DATE_FORMAT)
		ok= True
	except:
		ok= False
	assert ok

def test_only_time_now_obj():
	ts= helper.onlyTimeNowObj()
	assert isinstance(ts, datetime)
	assert ts < datetime.now()

def test_timestamp_to_formatted():
	ts= str(int(time.time() * 100))
	assert helper.timestamp_to_formatted(ts) == str(datetime.fromtimestamp(int(ts)/100))

def test_timestamp_to_date():
	date= helper.timestamp_to_date(TEST_TS)
	assert isinstance(date, str)
	assert date == '01-01-2000'

def test_timestamp_to_time():
	time_str= helper.timestamp_to_time(TEST_TS)
	assert isinstance(time_str, str)
	assert time_str == '12:30:15'

def test_str_to_time():
	ts= helper.str_to_time(TEST_FTS, time_format='%Y-%m-%d %H:%M:%S')
	assert isinstance(ts, datetime)

def test_seconds_to_formatted():
	assert helper.seconds_to_formatted(60) == '00:01:00'
	assert helper.seconds_to_formatted(304602) == '3 days, 12:36:42'
	assert helper.seconds_to_formatted('wrong type') == None


# Trans id

def test_new_trans_id():
	assert helper.new_trans_id() != helper.new_trans_id()


# Asyncio

def test_wait_first():
	async def task_fun():
		await asyncio.sleep(1)
	async def async_main():
		task= asyncio.create_task(task_fun())
		done, pend= await helper.wait_first([task], timeout=0)
		assert len(done) == 0
		assert task in pend
	asyncio.run(async_main())
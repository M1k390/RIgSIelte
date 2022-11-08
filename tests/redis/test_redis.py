import pytest

import time
import json

from rigproc.commons import redisi
from rigproc.commons import keywords
from rigproc.commons.helper import helper

from enum import Enum, unique


# Create test keys

@unique
class temp(str, Enum):
    sorted_set = 'test_temp_sorted'


class redis_keys_test:
	temp=temp


redisI= redisi.staticBuild()


def test_zset():
	zkey= 'test_redis_z'

	# Svuoto il set
	l_res = redisI.cache.zrange(zkey, 0, -1)
	num_el = len(l_res)
	assert num_el >= 0
	l_res = redisI.cache.zpopmin(zkey, num_el)
	assert len(l_res) == num_el

	# Aggiungo 3 elementi
	l_res = redisI.cache.zadd(zkey, {'one': helper.timestampNowFloat()})
	assert l_res == 1
	time.sleep(.01)
	l_res = redisI.cache.zadd(zkey, {'two': helper.timestampNowFloat()})
	assert l_res == 1
	time.sleep(.01)
	l_res = redisI.cache.zadd(zkey, {'three': helper.timestampNowFloat()})
	assert l_res == 1

	l_res = redisI.cache.zrange(zkey, 0, -1)
	assert l_res == ['one', 'two', 'three']
	l_res = redisI.cache.zpopmin(zkey, 2)
	assert len(l_res) == 2
	l_res = redisI.cache.zrange(zkey, 0, -1)
	assert l_res == ['three']


def test_temp_history():
	# Svuoto il set
	l_res = redisI.pers.zrange(redis_keys_test.temp.sorted_set, 0, -1)
	num_el = len(l_res)
	assert num_el >= 0
	l_res = redisI.pers.zpopmin(redis_keys_test.temp.sorted_set, num_el)
	assert len(l_res) == num_el
	l_res = redisI.pers.zrange(redis_keys_test.temp.sorted_set, 0, -1)
	num_el = len(l_res)
	assert num_el == 0

	# Assegno le chiavi di test
	redisi.redis_keys = redis_keys_test

	for i in range(redisi._TEMP_HISTORY_LIMIT):
		redisI.add_temp_measure(30, 40)
		l_temp_hist = redisI.get_temp_measures_formatted()
		assert l_temp_hist.count('\n') == i
		time.sleep(.01)


def test_default():
	assert redisI.cache.get('non_existant_key', p_default='default_res') == 'default_res'

def test_other():
	l_res= redisI.cache.hset(
		keywords.key_flow_log,
		'id_fake',
		json.dumps({
			keywords.flow_start_time: helper.timestampNowFormatted(),
			keywords.flow_type: 'flow-fake',
			keywords.flow_stop_time: None,
			keywords.flow_errors: None
		})
	)
	assert isinstance(l_res, int)
from argparse import ArgumentParser
import logging
from typing import Optional

from rigproc.commons.redisi import initialize_redis, get_redisI


REDIS_CACHE_HOST= 'localhost'
REDIS_CACHE_PORT= '6379'
REDIS_PERS_HOST= 'localhost'
REDIS_PERS_PORT= '6380'


def list_events_to_recover():
	events= get_redisI().get_events_to_recover()
	for event in events:
		print(repr(event))


def remove_all_events_to_recover():
	events= get_redisI().get_events_to_recover()
	for event in events:
		get_redisI().remove_event_to_recover(event)


if __name__ == '__main__':

	parser= ArgumentParser()
	parser.add_argument('-ch', 		'--cachehost', help='Redis cache host', default=REDIS_CACHE_HOST, type=str)
	parser.add_argument('-cp', 		'--cacheport', help='Redis cache port', default=REDIS_CACHE_PORT, type=str)
	parser.add_argument('-ph', 		'--pershost', help='Redis persistent host', default=REDIS_PERS_HOST, type=str)
	parser.add_argument('-pp', 		'--persport', help='Redis persistent port', default=REDIS_PERS_PORT, type=str)
	parser.add_argument('-op', 		'--operation', help='Name of operation to perform', type=str)
	parser.add_argument('-args', 	'--arguments', help='Operation arguments separated by "-" (arg1-arg2-...)', type=str)
	parser.add_argument('-pers', 	'--persistent', help='Select Redis persistent instead of cache', type=str)
	parser.add_argument('-lr', 		'--listrecovery', help='List events to recover', action='store_true')
	parser.add_argument('-cr', 		'--cleanrecovery', help='List events to recover', action='store_true')
	cli_args= parser.parse_args()

	initialize_redis(cli_args.cachehost, cli_args.cacheport, cli_args.pershost, cli_args.persport)

	if cli_args.listrecovery:
		list_events_to_recover()
	if cli_args.cleanrecovery:
		remove_all_events_to_recover()

	if cli_args.operation:
		if cli_args.persistent:
			instance= get_redisI().pers
		else:
			instance= get_redisI().cache
		try:
			method= getattr(instance, cli_args.operation)
			if cli_args.arguments:
				args= cli_args.arguments.split('-')
			else:
				args= []
			method(*args)
		except Exception as e:
			logging.error(f'Cannot execute {cli_args.operation} with arguments {cli_args.arguments} ({type(e)}): {e}')




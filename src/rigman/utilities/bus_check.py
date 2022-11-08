import argparse
import time

from rigproc.console import client
from rigproc.params import cli, bus, general, redis_keys


TIMEOUT= .5 # secondi tra un check e l'altro
DELAY= 1.5 # secondi tra 2 invii consecutivi
MAX_ATTEMPTS= 6 # tentativi prima di dichiarare ERROR

# senza il campo dati uguale a quello in data/msgs.json, le domande non vengono riconosciute dal fakebus
DATA= {
	bus.cmd.mtx_on_off_a: general.status_on,
	bus.cmd.mtx_on_off_b: general.status_on,
	bus.cmd.mrx_tmos_a: {
		bus.data_key.mosf_tpre: int(25),
		bus.data_key.mosf_tpost: int(25)
	},
	bus.cmd.mrx_tmos_b: {
		bus.data_key.mosf_tpre: int(25),
		bus.data_key.mosf_tpost: int(25)
	},
	bus.cmd.trig_setting_a: {
		bus.data_key.trig_latency: 4,
		bus.data_key.trig_exposure: 20
	},
	bus.cmd.trig_setting_b: {
		bus.data_key.trig_latency: 4,
		bus.data_key.trig_exposure: 20
	},
	bus.cmd.trig_on_off_a: general.status_on,
	bus.cmd.trig_on_off_b: general.status_on,
}


def send_request_wait(cmd, ip='127.0.0.1', port=9999, delay_request=True):
	print(f'> Comando: {cmd}')
	data= None
	if cmd in DATA.keys():
		data= DATA[cmd]
	l_serData= client.build_bus_cmd(cmd, data)
	if l_serData:
		l_serData= client.packData(l_serData)
		client.connect_and_send(l_serData, ip, port)		
	attempts= 0 # conta i tentativi fatti
	while attempts < MAX_ATTEMPTS:
		attempts += 1
		time.sleep(TIMEOUT)
		l_request_data= {
			'key': redis_keys.io_msg.sorted_set,
			'zrange_start': -2,
			'zrange_end': -1
		}
		l_request= client.build_check_msg_sorted_request(None, cmd)
		l_request= client.packData(l_request)
		l_answ= client.connect_and_send(l_request, ip, port)
		try:
			if l_answ['res'] and l_answ['infos']:
				print(f'{cli.color.forw_green}...OK{cli.color.regular}\n')
				return True
		except:
			continue
	print(f'{cli.color.forw_red}...ERROR!{cli.color.regular}\n')
	if delay_request and TIMEOUT * attempts < DELAY: # attendi che sia passato il tempo necessario tra una richiesta e l'altra
		time.sleep(DELAY - TIMEOUT * attempts)
	return False


def send_all_commands(ip='127.0.0.1', port=9999):
	ok_count, error_count= 0, 0 # variabili a fini statistici
	for cmd in client.cmd_list['bus']:
		if cmd == bus.cmd.stop or cmd == bus.cmd.restart:
			continue
		ok= send_request_wait(cmd, ip, port)
		if ok:
			ok_count += 1
		else:
			error_count += 1		
	print(f'> Risultati: {ok_count} OK, {error_count} errori')


def clear_cache(ip='127.0.0.1', port=9999):
	l_request_data= {
		'key': redis_keys.io_msg.sorted_set
	}
	l_request= client.build_delete_cache_data_request(None, l_request_data)
	l_request= client.packData(l_request)
	l_answ= client.connect_and_send(l_request, ip, port)
	try:
		if not l_answ['res']:
			return False
		if not isinstance(l_answ['infos'], int):
			return False
	except:
		return False
	return True


def main(cmd=None, ip='127.0.0.1', port=9999):
	clear= clear_cache(ip, port)
	if not clear:
		print('Errorore durante la pulizia della cache')
		return
	if cmd is None:
		send_all_commands(ip, port)
	else:
		send_request_wait(cmd, delay_request=False)
	

if __name__ == '__main__':
	parser= argparse.ArgumentParser()
	parser.add_argument('-c', '--command', help='send specific command', type=str)
	args= parser.parse_args()

	main(args.command)
	

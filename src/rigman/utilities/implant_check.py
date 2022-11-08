import argparse
import time

from rigman.utilities._implant_check_fields import FIELDS, TODO
from rigproc.console import client
from rigproc.params import cli, internal, general


# Timeout di attesa terminazione del flow
WAIT_TIMEOUT= 300

# Timeout tra un check e l'altro di terminazione del flow
CHECK_TIMEOUT= 5


def print_row(field, width1, width2, title=False, datum=None):
	"""
	Mostra i campi a terminale
	"""
	pos= field['pos']
	des= field['des']
	if title:
		print(f'{cli.color.back_yellow}{pos.ljust(width1+1)}{des.rjust(width2+1)}{cli.color.regular}')
	else:
		if datum is not None:
			if 'fun' in field.keys():
				if 'args' in field.keys():
					datum= field['fun'](datum, field['args'])
				else:
					datum= field['fun'](datum)
			print(f'{cli.color.forw_green}{pos.ljust(width1+1)}{cli.color.regular}{des.rjust(width2+1)} | {datum}')
		else:
			print(f'{cli.color.forw_green}{pos.ljust(width1+1)}{cli.color.regular}{des.rjust(width2+1)} | <none>')


def show(data):
	max_pos= max([len(field['pos']) for field in FIELDS])
	max_des= max([len(field['des']) for field in FIELDS])
	i= 0
	for field in FIELDS:
		if isinstance(field, dict) and 'title' in field.keys() and field['title']:
			print_row(field, max_pos, max_des, title=True)
		elif isinstance(field, dict) and 'status_key' in field.keys() and field['status_key'] is TODO:
			print_row(field, max_pos, max_des, datum='...')
		else:
			try:
				if isinstance(field['module'], list):
					datum= []
					for l_hash, l_key in zip(field['module'], field['status_key']):
						datum.append(data[l_hash][l_key])
				else:
					datum= data[field['module']][field['status_key']]
			except:
				datum= '<error>'
			#print(datum)
			print_row(field, max_pos, max_des, datum=datum)


def trigger_flow(ip='127.0.0.1', port=9999):
	print('Invio richiesta di analisi dei parametri di impianto')
	l_cmd= client.build_trig_cmd(internal.flow_type.implant_status, None)
	l_cmd= client.packData(l_cmd)
	l_answ= client.connect_and_send(l_cmd, ip, port)
	try:
		if l_answ['res']:
			return l_answ['infos']
	except:
		return None


def check_flow_termination(p_request_id, ip='127.0.0.1', port=9999):
	l_request= client.build_flow_termination_request(None, p_request_id)
	l_request= client.packData(l_request)
	l_answ= client.connect_and_send(l_request, ip, port)
	try:
		if l_answ['res']:
			return l_answ['infos']
		else:
			return general.status_ko
	except:
		return general.status_ko


def _build_cache_request_data():
	"""
	Costruisce una struttura dati contente ogni coppia hash-key presente nei FIELDS
	La struttura è come segue:
	[
		{
			'module': chiave del modulo,
			'status_key': field di stato
		}
		...
	]
	"""
	data= []
	for field in FIELDS:
		if isinstance(field, dict) and ('title' not in field.keys() or not field['title']):
			if 'module' in field.keys() and 'status_key' in field.keys():
				#print(field['module'])
				if isinstance(field['module'], list):
					#print('LIST')
					for l_hash, l_key in zip(field['module'], field['status_key']):
						key_field= {
							'module': l_hash,
							'status_key': l_key
						}
						if key_field not in data:
							data.append(key_field)
				else:
					#print('NOT LIST')
					key_field= {
						'module': field['module'],
						'status_key': field['status_key']
					}
					if key_field not in data:
						data.append(key_field)
	return data


def get_implant_status(ip='127.0.0.1', port=9999):
	l_requests_data= _build_cache_request_data()
	l_result= {}
	for l_req_data in l_requests_data:
		l_request= client.build_status_param_request(None, l_req_data)
		l_request= client.packData(l_request)
		l_answ= client.connect_and_send(l_request, ip, port)
		try:
			l_res= l_answ['infos']
		except:
			l_res= general.dato_non_disp
		l_module= l_req_data['module']
		l_status_key= l_req_data['status_key']
		if not l_module in l_result.keys():
			l_result[l_module] = {}
		l_result[l_module][l_status_key]= l_res
	return l_result


def main(ip='127.0.0.1', port=9999):
	request_id= trigger_flow(ip, port)
	if request_id is not None:
		flow_terminated= False
		execution_start= time.time()
		try:
			while not flow_terminated and time.time() - execution_start < WAIT_TIMEOUT:
				time.sleep(CHECK_TIMEOUT)
				print('Verifico la terminazione dell\'analisi...')
				flow_terminated= check_flow_termination(request_id, ip, port) == general.status_ok
				if not flow_terminated:
					print('Analisi in corso')
		except KeyboardInterrupt:
			pass
		if flow_terminated:
			print('Flow terminato')
			data= get_implant_status(ip, port)
			show(data)
		else:
			if execution_start >= WAIT_TIMEOUT:
				print('Errore: il server ha impiegato troppo tempo a rilevare i dati')
			else:
				print('Esecuzione interrotta')
	else:
		print('Errore: impossibile avviare il flow "implant status"')


if __name__ == '__main__':
	parser= argparse.ArgumentParser()
	parser.add_argument('-t', '--timeout', help='Timeout richiesta', default=WAIT_TIMEOUT, type=int)
	parser.add_argument('-i', '--interval', help='Termination check interval', default=CHECK_TIMEOUT, type=int)
	args= parser.parse_args()

	WAIT_TIMEOUT= args.timeout
	CHECK_TIMEOUT= args.interval
	main()
from rigproc.console import client
from rigproc.params import cli


def show(p_data):	
	if isinstance(p_data, dict) and p_data != {}:
		width1= max([len(key) for key in p_data.keys()])
		title=' Configurazione'
		print(f'{cli.color.back_yellow}{title.ljust(width1+1)}{cli.color.regular}')
		for key, value in p_data.items():
			print(f'{cli.color.forw_green}{key.rjust(width1+1)}{cli.color.regular} | {value}')
	else:
		print(f'{cli.color.forw_red}Errore di lettura dei dati di configurazione{cli.color.regular}')

def get_implant_conf(ip='127.0.0.1', port=9999):
	l_request= client.build_conf_request(None, None)
	l_request= client.packData(l_request)
	l_answ= client.connect_and_send(l_request, ip, port)
	l_data= {}
	try:
		if l_answ['res']:
			l_data= l_answ['infos']
	except:
		pass
	return l_data

def main():
	l_data= get_implant_conf()
	if l_data:
		show(l_data)
	else:
		print('Risposta dal server non valida')

if __name__ == '__main__':
	main()
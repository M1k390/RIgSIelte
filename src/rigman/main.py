import sys
import argparse
import json

from rigproc.console import client
from rigproc.params import general, cli
from rigproc.commons.config import init_configuration, get_config, Config

from rigman.cli import Menu, OneShotMenu, Option, Category, Data, clear_console, translate_boolean
from rigman.utilities import bus_check, conf_check, implant_check, kafka_check, kafka_utility



CONSOLE_ADDR= None
CONSOLE_PORT= None

DEFAULT_KAFKA_HOST= 'localhost'
DEFAULT_KAFKA_PORT= '9092'
DEFAULT_KAFKA_GROUP= 'stg'

class MainData(Data):
	def __init__(self, rig_addr, console_port) -> None:
		super().__init__()
		self.rig_addr= rig_addr
		self.console_port= console_port
		self.kafka_host= DEFAULT_KAFKA_HOST
		self.kafka_port= DEFAULT_KAFKA_PORT
		self.kafka_group= DEFAULT_KAFKA_GROUP


# GESTIONE

class Subscribe(Option):
	def __init__(self) -> None:
		super().__init__('Effettua l\'iscrizione del RIP')
	def trigger(self, data: MainData):
		clear_console()
		try:
			print('Richiedo l\'iscrizione del RIP...')
			l_cmd= client.build_subscription_request(None, None)
			l_cmd= client.packData(l_cmd)
			l_answ= client.connect_and_send(l_cmd, ip=data.rig_addr, port=int(data.console_port))
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		try:
			if l_answ is not None and l_answ['info'] == general.status_ok:
				print('Richiesta di iscrizione inviata con successo')
			else:
				print('Iscrizione non riuscita')
		except:
			input(f'Errore: impossibile leggere i dati ricevuti')
			return
		print()
		return super().trigger(data)


# CONFIGURAZIONE

class ShowConf(Option):
	def __init__(self) -> None:
		super().__init__('Mostra la configurazione di impianto in uso')
	def trigger(self, data: MainData):
		clear_console()
		print('Richiedo la configurazione al RIG...')
		try:
			conf_data= conf_check.get_implant_conf(data.rig_addr, int(data.console_port))
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		if conf_data:
			print()
			conf_check.show(conf_data)
		print()
		return super().trigger(data)


class ResetConf(Option):
	def __init__(self) -> None:
		super().__init__('Ripristina i parametri di configurazione')
	def trigger(self, data: MainData):
		clear_console()
		l_choice= None
		while l_choice is None:
			l_choice= input('Sei sicuro? I parametri modificati dal STG verrano ripristinati al valore presente sul file di configurazione (s/N): ')
			l_choice= translate_boolean(l_choice, default=False)
			if l_choice is None:
				print('Inserire una risposta valida')
		if l_choice:
			try:
				print('Ripristino i parametri di impianto...')
				l_cmd= client.build_reset_conf_request(None, None)
				l_cmd= client.packData(l_cmd)
				l_answ= client.connect_and_send(l_cmd, ip=data.rig_addr, port=int(data.console_port))
				if l_answ is not None:
					print('Operazione effettuata con successo')
				else:
					print('Operazione non riuscita')
			except:
				input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
				return
		else:
			print('Operazione annullata')
		return super().trigger(data)



# IMPIANTO

class ShowStatus(Option):
	def __init__(self) -> None:
		super().__init__('Mostra i parametri di impianto più recenti')
	def trigger(self, data: MainData):
		clear_console()
		print('Richiedo i parametri di impianto al RIG...')
		try:
			status_data= implant_check.get_implant_status(data.rig_addr, int(data.console_port))
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		if status_data:
			implant_check.show(status_data)
		return super().trigger(data)


class UpdateStatus(Option):
	def __init__(self) -> None:
		super().__init__('Esegui un\'analisi e mostra i parametri di impianto (più lento)')
	def trigger(self, data: MainData):
		clear_console()
		try:
			implant_check.main(data.rig_addr, int(data.console_port))
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		return super().trigger(data)


class ResetStatus(Option):
	def __init__(self) -> None:
		super().__init__('Ripristina i parametri di impianto al valore di default (eventuali anomalie verranno nuovamente notificate)')
	def trigger(self, data: MainData):
		clear_console()
		print('Ripristino i parametri di impianto...')
		l_req= client.build_reset_status_request(None, None)
		l_req= client.packData(l_req)
		try:
			l_answ= client.connect_and_send(l_req, data.rig_addr, int(data.console_port))
			if l_answ is not None:
				print('Operazione effettuata con successo')
			else:
				print('Operazione non riuscita')
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		return super().trigger(data)


# BUS

class TestBus(Option):
	def __init__(self) -> None:
		super().__init__('Esegui un test del bus di comunicazione con l\'impianto')
	def trigger(self, data: MainData):
		clear_console()
		try:
			bus_check.main(ip=data.rig_addr, port=int(data.console_port))
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		print()
		return super().trigger(data)


class BusHistory(Option):
	def __init__(self) -> None:
		super().__init__('Mostra la cronologia dei messaggi scambiati con l\'impianto')
	def trigger(self, data: MainData):
		clear_console()
		try:
			print('Richiedo la cronologia dei messaggi...')
			l_cmd= client.build_bus_history_request(None, None)
			l_cmd= client.packData(l_cmd)
			l_answ= client.connect_and_send(l_cmd, ip=data.rig_addr, port=int(data.console_port))
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		try:
			if l_answ is not None:
				l_history= l_answ['info']
				print()
				print(l_history)
		except:
			input(f'Errore: impossibile leggere i dati ricevuti')
			return
		print()
		return super().trigger(data)


class BusCommand(Option):
	def trigger(self, data: MainData):
		try:
			l_req= client.build_bus_cmd(self.text, None)
			l_req= client.packData(l_req)
			l_answ= client.connect_and_send(l_req, ip=data.rig_addr, port=int(data.console_port))
			if l_answ is not None:
				print('Comando inviato correttamente')
			else:
				print('Operazione non riuscita')
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		super().trigger(data)

class SendBusCommand(Option):
	def __init__(self) -> None:
		super().__init__('Invia un comando sul bus seriale')
	def trigger(self, data: MainData):
		clear_console()
		l_commands= client.cmd_list['bus']
		l_cmd_menu= OneShotMenu('Scegli un comando', [BusCommand(cmd) for cmd in l_commands])
		l_cmd_menu.data= data
		l_cmd_menu.exit_opt.text= 'Annulla'
		l_cmd_menu.show()
		#return super().trigger(data)


# KAFKA

class KafkaParams(Option):
	def __init__(self) -> None:
		super().__init__('Inserisci i parametri di Kafka')
	def trigger(self, data: MainData):
		clear_console()
		host= input(f'Host (default={data.kafka_host}): ')
		if host == '':
			host= data.kafka_host
		port= input(f'Port (default={data.kafka_port}): ')
		if port == '':
			port= data.kafka_port
		group= input(f'Group (default={data.kafka_group}): ')
		if group == '':
			group= data.kafka_group
		kafka_check.m_broker= f'{host}:{port}'
		kafka_check.m_group= group
		kafka_utility.ADDRESS= host
		kafka_utility.PORT= port
		kafka_utility.GROUP= group
		data.kafka_host= host
		data.kafka_port= port
		data.kafka_group= group

class CheckKafka(Option):
	def __init__(self) -> None:
		super().__init__('Controlla la comunicazione con Kafka')
	def trigger(self, data: MainData):
		clear_console()
		print('Chiedo al RIP i parametri di configurazione...')
		try:
			conf_data= conf_check.get_implant_conf(data.rig_addr, int(data.console_port))
		except:
			input(f'Errore: dati di connessione errati? ({data.rig_addr}, {data.console_port})')
			return
		if isinstance(conf_data, dict) and 'nome_rip' in conf_data.keys():
			print()
			kafka_check.RIP_NAME= conf_data['nome_rip']
			check_functions= {
				'aggiornamento impostazioni': kafka_check.test_aggiornamentoImpostazioni, 
				'aggiornamento finestra inizio tratta': kafka_check.test_aggiornamentoFinestraInizioTratta,
				'aggiornamento software': kafka_check.test_aggiornamentoSoftware
			}
			for desc, func in check_functions.items():
				print(f'{cli.color.back_yellow}Verifico: {desc}{cli.color.regular}')
				l_res= func()
				if l_res:
					print(f'{cli.color.forw_green}...OK{cli.color.regular}\n')
				else:
					print(f'{cli.color.forw_red}...ERROR!{cli.color.regular}\n')
		else:
			print('Impossibile leggere il nome del RIP dalla configurazione')
		return super().trigger(data)


class SimulateSTG(Option):
	def __init__(self) -> None:
		super().__init__('Simula STG')
	def trigger(self, data: MainData):
		clear_console()
		kafka_utility.simulate_stg()
		return super().trigger(data)


class MainMenu(Menu):
	def __init__(self) -> None:
		super().__init__(
			'GESTORE RIG',
			[
				Category('Gestione'),
				Subscribe(),

				Category('Configurazione'),
				ShowConf(),
				ResetConf(),

				Category('Impianto'),
				ShowStatus(),
				UpdateStatus(),
				ResetStatus(),
				
				Category('Bus-485'),
				TestBus(),
				BusHistory(),
				SendBusCommand(),

				Category('Kafka'),
				KafkaParams(),
				CheckKafka(),
				SimulateSTG()
			]
		)

	def update_heading(self):
		self.heading= f'GESTORE RIG\n\nIndirizzo IP: {self.data.rig_addr}\n' +\
			f'Porta console: {self.data.console_port}\n' +\
				f'Kafka: {self.data.kafka_host}:{self.data.kafka_port} (group: {self.data.kafka_group})'

	def preamble(self):
		clear_console()
		if CONSOLE_ADDR is None:
			rig_addr= input('Inserisci l\'indirizzo IP del RIG (default=localhost): ')
			if rig_addr == '':
				rig_addr= 'localhost'
		else:
			rig_addr= CONSOLE_ADDR
		if CONSOLE_PORT is None:
			console_port= input('Inserisci la porta della console (default=9999): ')
			if console_port == '':
				console_port= '9999'
		else:
			console_port= CONSOLE_PORT
		self.data= MainData(rig_addr, console_port)
		self.update_heading()



if __name__ == '__main__':
	parser= argparse.ArgumentParser()
	parser.add_argument('-a', '--address', help='rigproc console IP address', type=str)
	parser.add_argument('-p', '--port', help='rigproc console port', type=str)
	parser.add_argument('-c', '--conf', help='Rig configuration file', type=str)
	parser.add_argument('-stop', '--stop', help='stop rigproc execution', action='store_true')
	args= parser.parse_args()

	let_user_read= False

	CONSOLE_ADDR= args.address
	CONSOLE_PORT= args.port

	if args.conf:
		config= None
		try:
			with open(args.conf) as f:
				conf_dict= json.load(f)
			init_configuration(conf_dict)
			config= get_config()
		except Exception as e:
			print(f'Error reading the configuration file: {e}')
		if isinstance(config, Config):
			CONSOLE_ADDR= config.main.console.server.ip.get()
			CONSOLE_PORT= config.main.console.server.port.get()
			print('Console address set from configuration file')
		else:
			print('Configuration not initialized')
		let_user_read= True

	if args.stop:
		if not CONSOLE_ADDR or not CONSOLE_PORT:
			print('Specificare indirizzo e porta della console con gli argomenti -a e -p')
			sys.exit(-1)
		try:
			l_req= client.build_bus_cmd('stop', None)
			l_req= client.packData(l_req)
			client.connect_and_send(l_req, ip=CONSOLE_ADDR, port=int(CONSOLE_PORT))
		except Exception as e:
			print(f'Errore: dati di connessione errati? ({CONSOLE_ADDR}, {CONSOLE_PORT})')
			print(e)
		sys.exit(0)

	if let_user_read:
		input('Press enter to go ahead...')
	
	main_menu= MainMenu()
	main_menu.show()
import argparse
from datetime import datetime, timedelta
import json
import logging
from pprint import pprint
from datetime import datetime
from confluent_kafka import Consumer, Producer
import confluent_kafka
from confluent_kafka.admin import AdminClient

from rigproc.params import cli
from rigproc import __version__ as version
from rigproc.commons.helper import helper

NOME_RIP= 'RIP_test'

ADDRESS= 'localhost'
PORT= '9092'
GROUP= 'group'

TOPIC= 'default_topic'
MSG= 'default_message'

STG_TOPICS= [
	'EventoPassaggioTreno',
	'DiagnosiSistemiIVIP_RIPtoSTG',
	'MOSFvalues',
	'AllarmeAnomaliaIVIP',
	'AggiornamentoImpostazioni_RIPtoSTG',
	'AggiornamentoFinestraInizioTratta_RIPtoSTG',
	'AggiornamentoSW_RIPtoSTG',
	'IscrizioneRip_RIPtoSTG'
]

DATE_FORMAT= '%d-%m-%Y'
TIME_FORMAT= '%H:%M'

sent_messages= 0

def _callback(err, msg):
	global sent_messages
	if err is None:
		sent_messages += 1
	print(f'Err: {err}')
	print(f'Msg: {helper.prettify(msg)}')

def send(msg, topic):
	producer= Producer({'bootstrap.servers': f'{ADDRESS}:{PORT}'})
	producer.poll(0)
	current_messages= sent_messages
	producer.produce(topic, msg, callback=_callback)
	producer.flush(3.0)
	if sent_messages > current_messages:
		print('Message sent')
	else:
		print('Cannot send the message')

def listen(topics):
	consumer= Consumer({
		'bootstrap.servers': f'{ADDRESS}:{PORT}',
		'group.id': {GROUP},
		'auto.offset.reset': 'earliest'
	})
	consumer.subscribe(topics)
	print('Attendo i messaggi in arrivo... Premi ctrl + C per uscire\n')
	try:
		counter= 0
		while True:
			msg= consumer.poll(1.0)
			if msg is None:
				continue
			if msg.error():
				print('Error!')
			msg_decoded= msg.value().decode('utf-8')
			topic_decoded= msg.topic()
			if msg.timestamp()[0] != confluent_kafka.TIMESTAMP_NOT_AVAILABLE:
				msg_timestamp= datetime.fromtimestamp(msg.timestamp()[1] / 1000)
			else:
				msg_timestamp= 'non disponibile'
			counter += 1
			print(f'{cli.color.back_yellow} Messaggio con timestamp: {msg_timestamp}{cli.color.regular}\n')
			print(f'Topic: {topic_decoded}')
			print(f'Messaggio: {helper.prettify(msg_decoded)}')
			print(f'\n{cli.color.forw_gray}{counter} messaggi{"o" if counter == 1 else ""} ricevut{"o" if counter == 1 else "i"}{cli.color.regular}\n')
	except KeyboardInterrupt:
		print('\nStop\n')
		

def simulate_stg():
	listen(STG_TOPICS)


PKG= 'update.zip'
try:
	vers_nums= [int(str_num) for str_num in version.split('.')]
	vers_nums[-1] += 1
	VERSION= '.'.join([str(num) for num in vers_nums])
except Exception as e:
	logging.error(f'Cannot increment current rig version ({type(e)}): {e}')
	VERSION= '2.0.0'
DELAY= 60


def send_update():
	SW_UPD_TOPIC= 'AggiornamentoSW_STGtoRIP'
	now= datetime.now()
	now_date= now.strftime(DATE_FORMAT)
	now_time= now.strftime(TIME_FORMAT)
	upd_timestamp= now + timedelta(seconds=DELAY)
	upd_date= upd_timestamp.strftime(DATE_FORMAT)
	upd_time= upd_timestamp.strftime(TIME_FORMAT)

	message= {
		"event_type": "rip_software_update",
		"source": "SCP/STG locale",
		"dashboard_place":"località dove ubicata la pdl/pdlc nazionale",
		"user_id": "quale utente ha schedulato l’aggiornamento",	
		"id": "timestamp_nome_stg_dashboard_place",
		"transaction_id": "UUID 128bit",
		"event_date": now_date,
		"event_time": now_time,
		"event_timestamp": str(now),
		"rip_of_interest": [NOME_RIP],
		"update_parameters": {
				"date": upd_date,
				"time": upd_time,
				"package": PKG,
				"version": VERSION
				}
	}

	send(json.dumps(message), SW_UPD_TOPIC)


def send_set_upd():
	SET_UPD_TOPIC= 'AggiornamentoImpostazioni_STGtoRIP'
	TIME= 5
	now= datetime.now()
	now_date= now.strftime(DATE_FORMAT)
	now_time= now.strftime(TIME_FORMAT)

	message= {
		"event_type": "rip_settings_update",
		"source": "SCP/STG locale",
		"dashboard_place":"località dove ubicata la pdl/pdlc nazionale",
		"user_id": "quale utente ha schedulato l’aggiornamento",	
		"id": "timestamp_nome_stg_dashboard_place",
		"transaction_id": "UUID 128bit",
		"event_date": now_date,
		"event_time": now_time,
		"event_timestamp": str(now),
		"rip_of_interest": [NOME_RIP],
		"update_settings": {
			"t_mosf_prrA": TIME,
			"t_mosf_prrB": TIME,
			"t_off_ivip_prrA": TIME,
			"t_off_ivip_prrB": TIME
			}
	}

	send(json.dumps(message), SET_UPD_TOPIC)


def send_win_upd():
	WIN_UPD_TOPIC= 'AggiornamentoFinestraInizioTratta_STGtoRIP'
	TIME= 5
	now= datetime.now()
	now_date= now.strftime(DATE_FORMAT)
	now_time= now.strftime(TIME_FORMAT)

	message= {
		"event_type": "rip_finestra_temp_update",
		"source": "STG",
		"dashboard_place":"località dove ubicata la pdl/pdlc nazionale",
		"user_id": "quale utente ha schedulato l’aggiornamento",	
		"id": "timestamp_nome_stg_dashboard_place",
		"transaction_id": "UUID 128bit",
		"event_date": now_date,
		"event_time": now_time,
		"event_timestamp": str(now),
		"rip_of_interest": [NOME_RIP],
		"update_settings": {
			"finestra_temp_pic_pari": 5,
			"finestra_temp_pic_dispari": 5
			}
	}

	send(json.dumps(message), WIN_UPD_TOPIC)


def show_topic_list():
	admin_client= AdminClient({
		'bootstrap.servers': ADDRESS
	})
	topics= admin_client.list_topics().topics
	pprint(topics)


if __name__ == '__main__':
	parser= argparse.ArgumentParser()
	parser.add_argument('-nr', 	'--nomerip', 	help='Nome rip', default=NOME_RIP, type=str)
	parser.add_argument('-a', 	'--address', 	help='Indirizzo del server Kafka', default=ADDRESS, type=str)
	parser.add_argument('-p', 	'--port', 		help='Porta dal server Kafka', default=PORT, type=str)
	parser.add_argument('-g', 	'--group', 		help='Gruppo del subscriber Kafka', default=GROUP, type=str)
	parser.add_argument('-stg', '--simulatestg', help='Ascolta i messaggi in arrivo sui topic a cui si iscrive STG', action='store_true')
	parser.add_argument('-m', 	'--message', 	help='Messaggio da inviare', default=MSG, type=str)
	parser.add_argument('-t', 	'--topic', 		help='Topic verso cui mandare il messaggio', default=TOPIC, type=str)
	parser.add_argument('-s', 	'--send', 		help='Invia un messaggio', action='store_true')
	parser.add_argument('-u', 	'--update', 	help='Manda un messaggio di agg. sw', action='store_true')
	parser.add_argument('-pkg', '--package', 	help='Path zip di aggiornamento in shared folder', default=PKG, type=str)
	parser.add_argument('-v', 	'--version', 	help='Versione di aggiornamento', default=VERSION, type=str)
	parser.add_argument('-d', 	'--delay', 		help='Ritardo di aggiornamento', default=DELAY, type=int)
	parser.add_argument('-su', 	'--settingsupdate', help='Manda un messaggio di aggiornamento delle impostazioni', action='store_true')
	parser.add_argument('-wu', 	'--windowupdate', help='Manda un messaggio di aggiornamento della finestra temporale', action='store_true')
	parser.add_argument('-lt', 	'--listtopics', help='List the topics created on the server', action='store_true')
	args= parser.parse_args()

	NOME_RIP= args.nomerip

	ADDRESS= args.address
	PORT= args.port
	GROUP= args.group

	MSG= args.message
	TOPIC= args.topic

	PKG= args.package
	VERSION= args.version
	DELAY= args.delay

	if args.simulatestg:
		simulate_stg()
	if args.send:
		send(MSG, TOPIC)
	if args.update:
		send_update()
	if args.settingsupdate:
		send_set_upd()
	if args.windowupdate:
		send_win_upd()
	if args.listtopics:
		show_topic_list()
	

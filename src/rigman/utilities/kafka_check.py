"""
ATTENZIONE!
Affinchè i test funzionino è necessario "svuotare" la lista dei messaggi di Kafka dal RIP all'STG
Per fare ciò è possibile assegnare un periodo di scadenza ai messaggi sufficientemente corto (es: 10 secondi)
Per certi flow può essere necessario regolare il timeout
"""

from confluent_kafka import Consumer, Producer
import time
import argparse
import json

from rigproc.console import client
from rigproc.params import internal, kafka

m_broker= "localhost:9092"
m_group= 'stg'

m_timeout= 10
m_check_interval= 1

RIP_NAME= 'RIP_test'

# REQUEST MODELS

m_aggiornamentoImpostazioni= {
	"event_type": "rip_settings_update",
	"source": "SCP/STG locale",
	"dashboard_place":"località dove ubicata la pdl/pdlc nazionale",
	"user_id": "quale utente ha schedulato l’aggiornamento",	
	"id": "timestamp_nome_stg_dashboard_place",
	"transaction_id": "UUID 128bit",
	"event_date": "dd-mm-YYYY",
	"event_time": "HH:mm:ss",
	"event_timestamp": "timestamp",
	"rip_of_interest": ["RIP_test"],
	"update_settings": {
		"t_mosf_prrA": 5,
		"t_mosf_prrB": 5,
		"t_off_ivip_prrA": 60,
		"t_off_ivip_prrB": 60
	}
}

m_aggiornamentoFinestraInizioTratta= {
	"event_type": "rip_finestra_temp_update",
	"source": "STG",
	"dashboard_place":"località dove ubicata la pdl/pdlc nazionale",
	"user_id": "quale utente ha schedulato l’aggiornamento",	
	"id": "timestamp_nome_stg_dashboard_place",
	"transaction_id": "UUID 128bit",
	"event_date": "dd-mm-YYYY",
	"event_time": "HH:mm:ss",
	"event_timestamp": "timestamp",
	"rip_of_interest": ["RIP_test"],
	"update_settings": {
		"finestra_temp_pic_pari": 10,
		"finestra_temp_pic_dispari": 5
		}
}

m_aggiornamentoSW= {
	"event_type": "rip_software_update",
	"source": "SCP/STG locale",
	"dashboard_place":"località dove ubicata la pdl/pdlc nazionale",
	"user_id": "quale utente ha schedulato l’aggiornamento",	
	"id": "timestamp_nome_stg_dashboard_place",
	"transaction_id": "UUID 128bit",
	"event_date": "dd-mm-YYYY",
	"event_time": "HH:mm:ss",
	"event_timestamp": "timestamp",
	"rip_of_interest": ["RIP_test"],
	"update_parameters": {
			"date": "dd-mm-YYYY",
			"time": "HH:mm:ss",
			"package": "path di salvataggio in shared folder",
			"version": "release version"
			}
}


def encode_dict(kafka_dict):
	kafka_dict['rip_of_interest']= [RIP_NAME]
	return json.dumps(kafka_dict)

def check_kafka_topic(p_topic) -> bool:
	l_answ_found= False
	l_start_time= time.time()
	l_now= l_start_time
	m_consumer= Consumer({
		'bootstrap.servers': m_broker,
		'group.id': m_group,
		'auto.offset.reset': 'earliest'
	})
	m_consumer.subscribe([str(p_topic)])
	print(f'Collegamento a: {m_broker}, gruppo: {m_group}, topic: {p_topic}')
	print(f'Cerco la risposta: attendi fino a {m_timeout} secondi...')
	while not l_answ_found and (l_now - l_start_time) <= m_timeout:
		l_msg= m_consumer.poll(m_check_interval)
		l_now= time.time()
		if l_msg is None:
			continue
		if l_msg.error():
			print(f'Errore Kafka consumer: {l_msg.error()}')
		l_msg_value_decoded= l_msg.value().decode('utf-8')
		print(f'Risposta ricevuta:\n{l_msg_value_decoded}')
		l_answ_found= True
	if l_answ_found:
		return True
	else:
		print('Timeout scaduto')
		return False

m_msg_sent= False

def send_callback(err, msg):
	global m_msg_sent
	if err is None:
		m_msg_sent= True
		print('Messaggio inviato')
	else:
		print(f"Errore durante l'invio del messaggio {msg}: {err}")

def send_kafka_message(p_topic, p_message):
	print('Invio messaggio...')
	m_producer= Producer({'bootstrap.servers': m_broker})
	m_producer.poll(0)
	m_producer.produce(
		str(p_topic),
		p_message.encode('utf-8'),
		callback= send_callback
	)
	m_producer.flush(3.0)
	if m_msg_sent:
		return True
	else:
		print("Errore durante l'invio del messaggio")
		return False

def send_request_check_answer(p_req_topic, p_answ_topic, p_message) -> bool:
	if send_kafka_message(p_req_topic, p_message):
		return check_kafka_topic(p_answ_topic)
	else:
		return False

# TEST

def test_diagnosi() -> bool:
	l_event_req= client.build_trig_cmd(internal.flow_type.diagnosis, None)
	l_event_req= client.packData(l_event_req)
	l_server_answ= client.connect_and_send(l_event_req)
	if l_server_answ is None or not l_server_answ['res']:
		print('Impossibile inviare la richiesta di diagnosi')
		return False
	return check_kafka_topic(kafka.rip_topic.diag_vip_to_stg.value)

def test_aggiornamentoImpostazioni() -> bool:
	l_msg= encode_dict(m_aggiornamentoImpostazioni)
	return send_request_check_answer(
		kafka.stg_topic.int_set_upd_from_stg.value, 
		kafka.rip_topic.int_set_upd_to_stg.value, 
		l_msg
	)

def test_aggiornamentoFinestraInizioTratta() -> bool:
	l_msg= encode_dict(m_aggiornamentoFinestraInizioTratta)
	return send_request_check_answer(
		kafka.stg_topic.time_win_upd_from_stg.value, 
		kafka.rip_topic.time_win_upd_to_stg.value, 
		l_msg
	)

def test_aggiornamentoSoftware() -> bool:
	l_msg= encode_dict(m_aggiornamentoSW)
	return send_request_check_answer(
		kafka.stg_topic.sw_update_from_stg.value, 
		kafka.rip_topic.sw_update_to_stg.value, 
		l_msg
	)

if __name__ == '__main__':
	parser= argparse.ArgumentParser()
	parser.add_argument('-d', '--diagnosi', help='test diagnosi', action='store_true')
	parser.add_argument('-i', '--impostazioni', help='test aggiornamento impostazioni', action='store_true')
	parser.add_argument('-f', '--finestra', help='test aggiornamento finestra inizio tratta', action='store_true')
	parser.add_argument('-u', '--update', help='test aggiornamento software', action='store_true')

	args= parser.parse_args()

	if args.diagnosi:
		test_diagnosi()
	elif args.impostazioni:
		test_aggiornamentoImpostazioni()
	elif args.finestra:
		test_aggiornamentoFinestraInizioTratta()
	elif args.update:
		test_aggiornamentoSoftware()
	else:
		print('Inserisci una opzione')
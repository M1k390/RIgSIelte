#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processo di rilevamento anomalie e invio segnalazione a STG

Per anomalia si intende una condizione di errore riportata in risposta
ad un comando di tipo "Allarme" inviato sul bus

Il rilevamento avviene interrogrando la cache persistente di Redis,
su cui viene salvato lo stato dei componenti
"""

import logging

from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons.scheduler import get_scheduler
from rigproc.params import anomalies, conf_values, bus


class AnomalyDetector:

	def __init__(self):
		self.m_redisI= get_redisI()
		self.m_logger= logging.getLogger('root')

	def detect_anomaly(self, p_paramKey) -> bool:
		""" 
		Cerca il nuovo stato inserito in Redis nella lista di anomalie di stato
		Se l'anomalia viene riconosciuta, richiede la creazione di un topic Anomaly
		"""
		is_binario_doppio= get_config().main.implant_data.configurazione.get() == conf_values.binario.doppio
		prrB_status_modules= [
			bus.module.mosf_rx_b, bus.module.trigger_b,
			bus.module.cam1_b, bus.module.cam2_b, bus.module.cam3_b, 
			bus.module.cam4_b, bus.module.cam5_b, bus.module.cam6_b
		]

		# Ciclo tutti i moduli nella lista delle anomalie
		for l_module, l_params_data in anomalies.status_errors_reference.items():

			# Escludo i moduli sul palo B se non sto usando la configurazione binario_doppio
			# (alcuni componenti del software come il flow implant_status possono cercare di interrogare questi moduli sempre,
			# evito di inviare anomalie)
			
			if not is_binario_doppio and l_module in prrB_status_modules:
					continue

			# Per ogni modulo, ciclo tutti i suoi parametri
			if isinstance(l_params_data, dict):
				for l_param, l_bad_values in l_params_data.items():

					if isinstance(l_bad_values, dict):
						# Per verificare se la chiave Redis cambiata corrisponde ad un parametro sensibile,
						# la confronto con la chiave costruita a partire dal modulo e il parametro attuali
						if p_paramKey == self.m_redisI.moduleStatusKey(l_module, l_param):
							l_value= self.m_redisI.getStatusInfo(l_module, l_param)
							if l_value in l_bad_values.keys():
								l_anomaly= l_bad_values[l_value]
								if isinstance(l_anomaly, anomalies.Anomaly):
									get_scheduler().request_topic_anomaly(
										l_anomaly.device,
										l_anomaly.id,
										l_anomaly.descr,
										l_anomaly.status
									)
									return True
								else:
									self.m_logger.error(f'Internal error: {l_anomaly} was expected to be an Anomaly definition')
					else:
						self.m_logger.error(f'Internal error: {l_bad_values} was expected to be a dict')
			else:
				self.m_logger.error(f'Internal error: {l_params_data} was expected to be a dict')
		return False



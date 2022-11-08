#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subscription flow
"""


from rigproc.commons import keywords
from rigproc.commons.helper import helper
from rigproc.commons.wrappers import wrapkeys
from rigproc.params import internal


def _buildFlowSubscription(self):
	"""
	Flow builder richieta subscription
    Questo flow viene eseguito una unica volta in fase di installazione
	Viene avviato tramite console
    """

	self.m_taskAll= {
        **self.m_taskBegin,
        **self.m_taskSubscribe,
        **self.m_taskClosePipe
        }
	# Indicizzazione taskAll entries
	l_idx= 0
	for task in self.m_taskAll:
		self.m_taskAll[task]['id']= l_idx
		l_idx += 1
	# Lista funzioni registrate realtive ai task
	self.m_taskFuncList= {
		'id': 0,
		'tasks':[
			self._prepareWork,
			self._workTopicSub,
			self._workTopicSubAnswer,
			self._closePipe],
		'continue': True
	}


def _workTopicSub(self, p_data=None):
	""" Invio topic Kafka iscrizione """
	# Model
	l_jsonEvt= self.m_jmodel.getRipSubscriptionModel(self.m_data)
	# Topic dict with data
	self.m_data[keywords.evdata_topic_subscription]= {
		internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
		internal.cmd_key.topic_type:'subscription',
		internal.cmd_key.topic: keywords.topic_rip_subscription,
		internal.cmd_key.evt_name: self.m_evt,
		internal.cmd_key.json: l_jsonEvt,
		internal.cmd_key.trigflow_instance: self
		}
	self.m_logger.info("Json subscription to broker [topic]: "
				+ self.m_data[keywords.evdata_topic_subscription][internal.cmd_key.topic])
	self.m_mainCore['cmd_q'].put(self.m_data[keywords.evdata_topic_subscription])
	#
	self._incTaskId()
	self.m_taskFuncList['continue']= False
	return True

def _workTopicSubAnswer(self, p_data=None):
	""" Verifico invio topic """
	if not p_data:
		self.m_logger.error("Got empty data to parse")
		self.m_error= True
	elif wrapkeys.getValueDefault(p_data, None, keywords.topic_cmd_key) == keywords.status_error:
		self.m_logger.error("Got KO ")
		self.m_error= True
	elif wrapkeys.getValueDefault(p_data, None, keywords.topic_cmd_key) == keywords.status_ok:
		self.m_logger.info("Got Ok ")
	else:
		self.m_logger.error("Unknown data to parse")
		self.m_error= True
	if self.m_error:
		self.m_logger.error("Got error sending topic {}, proceeding anyway".format(keywords.topic_rip_subscription))
	#
	self._incTaskId()
	self.m_taskFuncList['continue']= True
	return True


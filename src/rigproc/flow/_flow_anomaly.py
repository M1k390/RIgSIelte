#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anomaly alarm sending to STG
"""

from rigproc.commons import keywords
from rigproc.commons.wrappers import wrapkeys
from rigproc.flow import eventtrigflow_buildcmd as buildcmd
from rigproc.params import internal


def _buildFlowAnomaly(self):
	"""Tasklist builder anomalia  
    """
	" Task master list "
	self.m_taskAll= {
		**self.m_taskBegin,
		**self.m_taskAnomaly,
		**self.m_taskClosePipe
	}
	" Assegnazione di un ID ad ogni task della master list "
	l_idx= 0
	for task in self.m_taskAll:
		self.m_taskAll[task]['id']= l_idx
		l_idx += 1
	" lista funzioni abbinate alle entries della master task list "
	self.m_taskFuncList= {
		'id': 0,
		'tasks': [
			self._prepareWork,
			self._workTopicAnomaly,
			self._workTopicAnomalyAnswer,
			self._closePipe
		],
		'continue': True
	}

def _workTopicAnomaly(self, p_data=None):
	l_jsonEvt= self.m_jmodel.getAnomalyAlarmModel(self.m_data)
	self.m_data[keywords.evdata_topic_anomaly_alarm]= {
        internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
        internal.cmd_key.topic_type:'topic_anomaly_alarm',
        internal.cmd_key.topic: keywords.topic_anomaly_alarm,
        internal.cmd_key.evt_name: self.m_evt,
        internal.cmd_key.json: l_jsonEvt,
        internal.cmd_key.trigflow_instance: self
    }
	self.m_logger.info("Json model to signal anomaly")
	self.m_mainCore['cmd_q'].put(self.m_data[keywords.evdata_topic_anomaly_alarm])
	# End task
	self._incTaskId()
	self.m_taskFuncList['continue']= False
	return True

def _workTopicAnomalyAnswer(self, p_data=None):
	""" Check invio json al topic anomalie """
	if not p_data:
		self.m_logger.error("Got empty data to parse")
		self.m_error= True
	elif wrapkeys.getValueDefault(p_data, None, keywords.topic_cmd_key) == keywords.status_error:
		self.m_logger.error("Got KO")
		self.m_error= True
	elif wrapkeys.getValueDefault(p_data, None, keywords.topic_cmd_key) == keywords.status_ok:
		self.m_logger.info("Got OK")
	else:
		self.m_logger.error("Unknown data to parse")
		self.m_error= True
	" si prosegue lo stesso "
	self._incTaskId()
	self.m_taskFuncList['continue']= True
	return True
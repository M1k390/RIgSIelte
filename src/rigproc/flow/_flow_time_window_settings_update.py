#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
time window settings update
"""

from rigproc.commons import keywords
from rigproc.commons.wrappers import wrapkeys
from rigproc.params import internal
from rigproc.commons.config import get_config


def _buildFlowTimeWindowSettingsUpdate(self):
	"""Tasklist builder aggiornamento impostazioni interne   
    """
	" Task master list "
	self.m_taskAll= {
		**self.m_taskBegin,
		**self.m_taskTimeWinUpdate,
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
			self._workStoreTimeWinSettings,
			self._workTopicTimeWinUpdate,
			self._workTopicTimeWinUpdateAnswer,
			self._closePipe
		],
		'continue': True
	}


# @TODO Trigger settings?


def _workStoreTimeWinSettings(self, p_data=None):
	l_config= get_config().main.implant_data
	self.m_data[keywords.evdata_time_win_upd_confirmed]= all([
		l_config.distanza_prr_IT_pari.set(wrapkeys.getValue(self.m_data, keywords.evdata_fin_temp_pic_pari)),
		l_config.distanza_prr_IT_dispari.set(wrapkeys.getValue(self.m_data, keywords.evdata_fin_temp_pic_dispari))
	])
	self._incTaskId()
	self.m_taskFuncList['continue']= True
	return True


def _workTopicTimeWinUpdate(self, p_data=None):
	l_jsonEvt= self.m_jmodel.getTimeWindowSettingsUpdateModel(self.m_data)
	self.m_data[keywords.evdata_topic_evt_time_win_to_stg]= {
        internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
        internal.cmd_key.topic_type:'topic_int_sett_update',
        internal.cmd_key.topic: keywords.topic_time_win_upd_to_stg,
        internal.cmd_key.evt_name: self.m_evt,
        internal.cmd_key.json: l_jsonEvt,
        internal.cmd_key.trigflow_instance: self
    }
	self.m_logger.info("Json model to asnwer internal settings update schedule request")
	self.m_mainCore['cmd_q'].put(self.m_data[keywords.evdata_topic_evt_time_win_to_stg])
	# End task
	self._incTaskId()
	self.m_taskFuncList['continue']= False
	return True


def _workTopicTimeWinUpdateAnswer(self, p_data=None):
	""" Check invio json al topic conferma schedulazione sw update """
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
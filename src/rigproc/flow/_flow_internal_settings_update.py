#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
internal settings update
"""

from rigproc.commons import keywords
from rigproc.commons.wrappers import wrapkeys
from rigproc.flow import eventtrigflow_buildcmd as buildcmd
from rigproc.params import internal
from rigproc.commons.config import get_config


def _buildFlowInternalSettingsUpdate(self):
	"""Tasklist builder aggiornamento impostazioni interne   
    """
	" Task master list "
	self.m_taskAll= {
		**self.m_taskBegin,
		**self.m_taskIntSettUpdate,
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
			self._workMosfRxA_mosf,
			self._workMosfRxA_mosfAnswer,
			self._workMosfRxB_mosf,
			self._workMosfRxB_mosfAnswer,
			self._workSetResetTime,
			self._workStoreInternalSettings,
			self._workTopicIntSettUpdate,
			self._workTopicIntSettUpdateAnswer,
			self._closePipe
		],
		'continue': True
	}
			

def _workMosfRxA_mosf(self, p_data=None):
	l_time= wrapkeys.getValue(self.m_data, keywords.evdata_t_mosf_prrA)
	l_data= {
		keywords.data_mosf_tpre_key: l_time,
		keywords.data_mosf_tpost_key: l_time
	}
	self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfRxATmos(self, l_data))
	self._incTaskId()
	self.m_taskFuncList['continue']= False
	return True

def _workMosfRxA_mosfAnswer(self, p_data=None):
	l_time= wrapkeys.getValue(self.m_data, keywords.evdata_t_mosf_prrA)
	l_tPre= wrapkeys.getValueDefault(p_data, 'answ_missing', keywords.data_mosf_tpre_key)
	l_tPost= wrapkeys.getValueDefault(p_data, 'answ_missing', keywords.data_mosf_tpost_key)
	if l_time != l_tPre or l_time != l_tPost:
		self.m_logger.error('Mosf Rx A did not answer to the setting of the measuring time interval. Ignoring and keeping the new setting')
	self._incTaskId()
	self.m_taskFuncList['continue']= True
	return True

def _workMosfRxB_mosf(self, p_data=None):
	l_time= wrapkeys.getValue(self.m_data, keywords.evdata_t_mosf_prrB)
	l_data= {
		keywords.data_mosf_tpre_key: l_time,
		keywords.data_mosf_tpost_key: l_time
	}
	self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfRxBTmos(self, l_data))
	self._incTaskId()
	self.m_taskFuncList['continue']= False
	return True

def _workMosfRxB_mosfAnswer(self, p_data=None):
	l_time= wrapkeys.getValue(self.m_data, keywords.evdata_t_mosf_prrB)
	l_tPre= wrapkeys.getValueDefault(p_data, 'answ_missing', keywords.data_mosf_tpre_key)
	l_tPost= wrapkeys.getValueDefault(p_data, 'answ_missing', keywords.data_mosf_tpost_key)
	if l_time != l_tPre or l_time != l_tPost:
		self.m_logger.error('Mosf Rx B did not answer to the setting of the measuring time interval. Ignoring and keeping the new setting')
	self._incTaskId()
	self.m_taskFuncList['continue']= True
	return True

def _workSetResetTime(self, p_data=None):
	# @TODO
	self._incTaskId()
	self.m_taskFuncList['continue']= True
	return True

def _workStoreInternalSettings(self, p_data=None):
	l_config= get_config().main.implant_data
	self.m_data[keywords.evdata_int_sett_upd_confirmed]= all([
		l_config.t_mosf_prrA.set(wrapkeys.getValue(self.m_data, keywords.evdata_t_mosf_prrA)),
		l_config.t_mosf_prrB.set(wrapkeys.getValue(self.m_data, keywords.evdata_t_mosf_prrB)),
		l_config.t_off_ivip_prrA.set(wrapkeys.getValue(self.m_data, keywords.evdata_t_off_ivip_prrA)),
		l_config.t_off_ivip_prrB.set(wrapkeys.getValue(self.m_data, keywords.evdata_t_off_ivip_prrB)),
	])
	self._incTaskId()
	self.m_taskFuncList['continue']= True
	return True

def _workTopicIntSettUpdate(self, p_data=None):
	l_jsonEvt= self.m_jmodel.getInternalSettingsUpdateModel(self.m_data)
	self.m_data[keywords.evdata_topic_evt_intsettupd_to_stg]= {
        internal.cmd_key.cmd_type: internal.cmd_type.topic_evt,
        internal.cmd_key.topic_type:'topic_int_sett_update',
        internal.cmd_key.topic: keywords.topic_int_set_upd_to_stg,
        internal.cmd_key.evt_name: self.m_evt,
        internal.cmd_key.json: l_jsonEvt,
        internal.cmd_key.trigflow_instance: self
    }
	self.m_logger.info("Json model to asnwer internal settings update schedule request")
	self.m_mainCore['cmd_q'].put(self.m_data[keywords.evdata_topic_evt_intsettupd_to_stg])
	# End task
	self._incTaskId()
	self.m_taskFuncList['continue']= False
	return True

def _workTopicIntSettUpdateAnswer(self, p_data=None):
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
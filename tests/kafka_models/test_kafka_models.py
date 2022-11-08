import pytest
import json
import logging

from rigproc.commons.redisi import initialize_redis, get_redisI
from rigproc.commons import jsonmodel
from rigproc.commons.helper import helper
from rigproc.commons import keywords
from rigproc.central.kafka_broker import KafkaBroker
from rigproc.params import internal
from rigproc.commons.config import init_configuration, get_config


with open(helper.data_file_path('conf_001.json'), 'r') as f:
	m_conf_dict= json.load(f)
with open(helper.data_file_path('kafka_json_models.json'), 'r') as f:
	m_models= json.load(f)

init_configuration(m_conf_dict)
m_config= get_config()
initialize_redis(
	m_config.main.redis.cache.host.get(),
	m_config.main.redis.cache.port.get(),
	m_config.main.redis.pers.host.get(),
	m_config.main.redis.pers.port.get()
)
m_config.reset_configuration()
m_redisI= get_redisI()

m_jsonmodel= jsonmodel.JsonModels()

m_fake_event= {
	keywords.evdata_id: 1,
	keywords.evdata_recovered: False,
	keywords.evdata_uuid: 2,
	keywords.evdata_date:'today',
	keywords.evdata_time: 'now',
	keywords.evdata_timestamp: 'ts',
}

class FakeKafkaBroker(KafkaBroker):

	def __init__(self, p_logger, p_redisI):
		self.m_logger= p_logger
		self.m_redisI= p_redisI

m_fake_kafka_broker= FakeKafkaBroker(logging, m_redisI)


# TEST JSON MODELS (ANSWERS - jsonmodel)

def test_getTrigModel():
	l_data= m_fake_event
	l_dumped_dict= m_jsonmodel.getTrigModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_evt_trigger])
	assert helper.check_dict_keys(m_models[keywords.topic_evt_trigger], l_dict)

def test_recoverTrigModel():
	l_data= m_fake_event
	l_trig_model= m_jsonmodel.getTrigModel(l_data)
	l_dumped_dict= m_jsonmodel.recoverTrigModel(l_trig_model, l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_evt_trigger])
	assert helper.check_dict_keys(m_models[keywords.topic_evt_trigger], l_dict)

def test_getDiagModel():
	l_data= {
		**m_fake_event,
		'on_trigger': False
	}
	l_dumped_dict= m_jsonmodel.getDiagModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_diag_rip_to_stg])
	assert helper.check_dict_keys(m_models[keywords.topic_diag_rip_to_stg], l_dict)

def test_getMosfDataModel():
	l_data= m_fake_event
	l_dumped_dict= m_jsonmodel.getMosfDataModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_mosf_data])
	assert helper.check_dict_keys(m_models[keywords.topic_mosf_data], l_dict)

def test_getAnomalyAlarmModel():
	l_data= m_fake_event
	l_dumped_dict= m_jsonmodel.getAnomalyAlarmModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_anomaly_alarm])
	assert helper.check_dict_keys(m_models[keywords.topic_anomaly_alarm], l_dict)

def test_getInternalSettingsUpdateModel():
	l_data= {keywords.evdata_json_from_stg: m_models['AggiornamentoImpostazioni_STGtoRIP']}
	l_dumped_dict= m_jsonmodel.getInternalSettingsUpdateModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_int_set_upd_to_stg])
	assert helper.check_dict_keys(m_models[keywords.topic_int_set_upd_to_stg], l_dict)

def test_getTimeWindowSettingsUpdateModel():
	l_data= {keywords.evdata_json_from_stg: m_models['AggiornamentoFinestraInizioTratta_STGtoRIP']}
	l_dumped_dict= m_jsonmodel.getTimeWindowSettingsUpdateModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_time_win_upd_to_stg])
	assert helper.check_dict_keys(m_models[keywords.topic_time_win_upd_to_stg], l_dict)

def test_getSwUpdateScheduledModel():
	l_data= {keywords.evdata_json_from_stg: m_models['AggiornamentoSW_STGtoRIP']}
	l_dumped_dict= m_jsonmodel.getSwUpdateScheduledModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_sw_update_to_stg + '-fase1'])
	assert helper.check_dict_keys(m_models[keywords.topic_sw_update_to_stg + '-fase1'], l_dict)

def test_getSwUpdateDoneModel():
	l_data= m_fake_event
	l_dumped_dict= m_jsonmodel.getSwUpdateDoneModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_sw_update_to_stg + '-fase2'])
	assert helper.check_dict_keys(m_models[keywords.topic_sw_update_to_stg + '-fase2'], l_dict)

def test_getRipSubscriptionModel():
	l_data= m_fake_event
	l_dumped_dict= m_jsonmodel.getRipSubscriptionModel(l_data)
	l_dict= json.loads(l_dumped_dict)
	assert isinstance(l_dict, dict)
	assert helper.check_dict_keys(l_dict, m_models[keywords.topic_rip_subscription])
	assert helper.check_dict_keys(m_models[keywords.topic_rip_subscription], l_dict)


# TEST LETTURA MESSAGGI DA PARTE DEL KAFKABROKER

def test_parseInternalSettingsRequest():
	l_msg= m_models['AggiornamentoImpostazioni_STGtoRIP']
	assert m_fake_kafka_broker._isItForMe(l_msg)
	l_cmd= m_fake_kafka_broker._parseInternalSettingsRequest(l_msg)
	assert l_cmd != {}
	assert l_cmd[internal.cmd_key.cmd_type] == internal.cmd_type.action
	assert l_cmd[internal.cmd_key.action_type] == keywords.action_int_set_upd_flow
	assert l_cmd[internal.cmd_key.data][keywords.flin_json_dict] == l_msg

def test_parseTimeWinSettingsRequest():
	l_msg= m_models['AggiornamentoFinestraInizioTratta_STGtoRIP']
	assert m_fake_kafka_broker._isItForMe(l_msg)
	l_cmd= m_fake_kafka_broker._parseTimeWinSettingsRequest(l_msg)
	assert l_cmd != {}
	assert l_cmd[internal.cmd_key.cmd_type] == internal.cmd_type.action
	assert l_cmd[internal.cmd_key.action_type] == keywords.action_time_win_upd_flow
	assert l_cmd[internal.cmd_key.data][keywords.flin_json_dict] == l_msg

def test_parseSwUpdateRequest():
	l_msg= m_models['AggiornamentoSW_STGtoRIP']
	assert m_fake_kafka_broker._isItForMe(l_msg)
	l_cmd= m_fake_kafka_broker._parseSwUpdateRequest(l_msg)
	assert l_cmd != {}
	assert l_cmd[internal.cmd_key.cmd_type] == internal.cmd_type.action
	assert l_cmd[internal.cmd_key.action_type] == keywords.action_update_flow
	assert l_cmd[internal.cmd_key.data][keywords.flin_json_dict] == l_msg


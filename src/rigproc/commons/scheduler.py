from queue import Queue
import logging

from rigproc.commons.config import get_config
from rigproc.params import internal
from rigproc.commons.helper import helper


class Scheduler:

	def __init__(self, p_cmdQ: Queue) -> None:
		self.m_logger= logging.getLogger('root')
		self.m_cmdQ= p_cmdQ

	def request_topic_anomaly(self, faulty_device: str, alarm_id: str, alarm_descr: str, alarm_status: str):
		l_timestamp= helper.timestampNowFormatted()
		l_plant_name= get_config().main.implant_data.nome_ivip.get()
		l_cmd= {
			internal.cmd_key.cmd_type: internal.cmd_type.action,
			internal.cmd_key.action_type: internal.action.anomaly_flow,
			internal.cmd_key.data: {
				# EVENT GENERIC DATA
				internal.flow_input.id: f'{l_timestamp}_{l_plant_name}_{faulty_device}',
				# ANOMALY DATA
				internal.flow_input.alarm_id: alarm_id,
				internal.flow_input.alarm_descr: alarm_descr,
				internal.flow_input.alarm_status: alarm_status
			}
		}
		self.m_cmdQ.put(l_cmd)


# SINGLETON

_scheduler: Scheduler= None


def init_scheduler(p_cmdQ: Queue) -> None:
	global _scheduler
	_scheduler= Scheduler(p_cmdQ)


def get_scheduler() -> Scheduler:
	return _scheduler
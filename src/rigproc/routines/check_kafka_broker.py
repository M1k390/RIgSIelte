from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons.helper import helper
from rigproc.commons.logger import logging_manager

from rigproc.params import redis_keys, general, bus


def check_kafka_broker():
    broker_online= helper.check_kafka_broker(
        broker=get_config().broker.consume.broker.get()
    )
    if not broker_online:
        logging_manager.get_root_logger().error(
            f'Kafka broker did not respond to the periodic check'
        )
    get_redisI().updateStatusInfo(
        bus.module.videoserver,
        redis_keys.rip_status_field.broker_connected,
        general.status_ok if broker_online else general.status_ko
    )
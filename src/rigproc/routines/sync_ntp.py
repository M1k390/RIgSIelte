from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons.helper import helper
from rigproc.commons.logger import logging_manager

from rigproc.params import redis_keys, general, bus


def sync_ntp():
    l_synced = _sync_ntp_jobs()
    get_redisI().updateStatusInfo(
        bus.module.videoserver,
        redis_keys.rip_status_field.ntp_synced,
        general.status_ok if l_synced else general.status_ko
    )

def _sync_ntp_jobs() -> bool:
    l_logger = logging_manager.get_root_logger()
    if not helper.check_command_existance('sudo chronyd'):
        l_logger.error(
            'Cannot use chronyd: is it installed?'
        )
        return False
    
    ntp_addr = get_config().main.ntp.ip.get()

    if helper.chrony_one_shot(ntp_addr=ntp_addr):
        l_logger.info('NTP synced with chrony')
        return True
    else:
        l_logger.error('Error syncing NTP with chrony')
        return False
    
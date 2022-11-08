from rigproc.commons.helper import helper
from rigproc.commons.redisi import get_redisI
from rigproc.commons.logger import logging_manager


m_update_counter = 0


def update_uptime():
    global m_update_counter
    my_pid = helper.get_my_pid()
    if my_pid is None:
        logging_manager.get_root_logger().error(
            'Error retrieving rigproc pid: cannot update uptime'
        )
        return
    l_uptime = helper.get_process_uptime(my_pid)
    if l_uptime is None:
        logging_manager.get_root_logger().error(
            'Cannot get rigproc uptime: will not update'
        )
        return
    get_redisI().set_rigproc_uptime(l_uptime)
    m_update_counter += 1
    if m_update_counter > 9:
        m_update_counter = 0
        l_uptime_formatted = helper.seconds_to_formatted(l_uptime)
        if l_uptime_formatted is not None:
            logging_manager.get_root_logger().info(
                f'rigproc uptime: {l_uptime_formatted}'
            )

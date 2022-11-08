#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semplice thread di diagnostica telecamere ( ping )
"""

from datetime import datetime
import logging
from queue import Queue
from typing import Dict, List, Optional

from rigproc.commons.config import get_config
from rigproc.commons.utils import RecursiveTimer
from rigproc.commons.logger import logging_manager
from rigproc.params import internal

from rigproc.routines.check_kafka_broker import check_kafka_broker
from rigproc.routines.ping_cameras import ping_cameras, preliminary_ping_cameras
from rigproc.routines.ping_sshfs_server import ping_sshfs_server
from rigproc.routines.sync_ntp import sync_ntp
from rigproc.routines.uptime import update_uptime


class RoutinesManager:
    """ 
    Performs side-tasks periodically.
    """

    def __init__(self, p_core: dict) -> None:
        """ 
        Creating this object automatically starts the periodic tasks
        """

        self.m_logger= logging_manager.get_root_logger()
        self.m_command_queue: Queue= p_core['cmd_q']

        self.m_daily_tasks_last_check = datetime.now()
        # {time: cmd_code)
        self.m_daily_tasks: Dict[datetime, str] = {}

        if get_config().logging.renew_log_files.get():
            try:
                l_time = datetime.strptime(
                    get_config().logging.renewal_time.get(),
                    '%H:%M'
                ).time()
                self.m_daily_tasks[l_time] = internal.cmd_type.renew_logs_flow
                self.m_logger.info(f'Added Log file renewal to the daily routines, scheduled for {l_time}')
            except Exception as e:
                self.m_logger.error(
                    f'Cannot add log files renewal to daily tasks ({type(e)}): {e}'
                )

        self.timers: List[RecursiveTimer]= [
            # Daily taksa
            RecursiveTimer(
                interval=60,
                functions=[
                    self._execute_daily_tasks
                ],
                name='daily_tasks'
            ),

            # Uptime update
            RecursiveTimer(
                interval=30,
                functions=[
                    update_uptime
                ],
                name='uptime'
            )
        ]

        if get_config().main.ping.enabled.get():
            self.m_logger.info('Activating periodic ping')
            self.timers += [
                # Camera ping (time interval defined in the configuration)
                RecursiveTimer(
                    interval=get_config().main.ping.cameras_ping_interval.get(), 
                    functions=[
                        ping_cameras
                    ],
                    name='ping_cameras'
                ),

                # Servers ping
                RecursiveTimer(
                    interval=get_config().main.ping.servers_ping_interval.get(),
                    functions=[
                        ping_sshfs_server, 
                        check_kafka_broker
                    ],
                    name='ping_servers'
                )
            ]

        if get_config().main.ntp.enabled.get():
            self.m_logger.info('Activating NTP sync')
            self.timers.append(
                # NTP sync
                RecursiveTimer(
                    interval=get_config().main.ntp.sync_interval.get(),
                    functions=[
                        sync_ntp
                    ],
                    name='ntp_sync'
                )
            )

        # Enable RoutinesManager using start()
        self.enabled= False

    def start(self):
        # Set "enabled" flag to True
        self.enabled= True

        # Do work before starting routines
        self._preliminary_work()

        # Start routines threads
        for timer in self.timers:
            self.m_logger.info(f'Starting timer {timer.name} with interval {timer.interval}')
            timer.start()

    def close(self):
        """ Stop all the created threads """
        if self.enabled:
            for timer in self.timers:
                timer.cancel()
            self.m_logger.info('Periodic pinger threads stopped')

    def wait(self):
        """ Join all the created threads """
        if self.enabled:
            for timer in self.timers:
                timer.wait()
            self.m_logger.info('Periodic pinger threads joined')

    def _preliminary_work(self):
        preliminary_ping_cameras()

    def _request_cmd(self, cmd_code: str):
        cmd_req = {
            internal.cmd_key.cmd_type: cmd_code
        }
        self.m_command_queue.put(cmd_req)

    def _execute_daily_tasks(self):
        l_now = datetime.now()
        l_time = l_now.time()
        l_date = l_now.date()
        l_last_time = self.m_daily_tasks_last_check.time()
        l_last_date = self.m_daily_tasks_last_check.date()
        l_day_passed = l_date != l_last_date
        for task_time, task_code in self.m_daily_tasks.items():
            if (l_day_passed and l_time >= task_time) or\
                (l_time >= task_time and l_last_time < task_time):
                self.m_logger.info(f'Triggering {task_code}, time: {task_time}')
                self._request_cmd(task_code)
        self.m_daily_tasks_last_check = l_now

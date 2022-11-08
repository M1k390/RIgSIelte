from datetime import datetime, timedelta
from typing import List
from rigproc.commons.entities import LogFile
from rigproc.commons.helper import helper
from rigproc.commons.config import get_config
from rigproc.commons.logger import logging_manager
from rigproc.commons.redisi import get_redisI
from rigproc.flow.flow import Flow
from rigproc.params import internal


class FlowRenewLogs(Flow):
    """
    Flow to renew log files and clean log folder from old ones.
    """

    def __init__(self, core, request_id=None):
        Flow.__init__(self, internal.flow_type.renew_logs, core, request_id)
        self.m_tasks = [
            self._delete_older_logs,
            self._renew_log_files,
            #
            Flow._close_pipe
        ]

    # Tasks

    def _delete_older_logs(self):
        if not get_config().logging.delete_older_logs.get():
            self.m_logger.info('Skipping old logs removal')
            self._step()
            return
        try:
            l_kept_interval = timedelta(
                days=get_config().logging.days_to_keep.get())
        except Exception as e:
            self.m_logger.error(
                f'Error generating timedelta: skipping log files removal...')
            self._step()
            return
        l_now = helper.timeNowObj()

        # For each logger, collect its log file prefix and directory
        name_prefixes = [
            get_config().logging.bus.file_name.get(),
            get_config().logging.camera.file_name.get(),
            get_config().logging.console.file_name.get(),
            get_config().logging.flow.file_name.get(),
            get_config().logging.kafka.file_name.get(),
            get_config().logging.root.file_name.get(),
        ]
        dirs = [
            get_config().logging.bus.file_dir.get(),
            get_config().logging.camera.file_dir.get(),
            get_config().logging.console.file_dir.get(),
            get_config().logging.flow.file_dir.get(),
            get_config().logging.kafka.file_dir.get(),
            get_config().logging.root.file_dir.get(),
        ]

        # Filter log files in the directories above
        log_files: list[LogFile] = []

        for name_prefix, log_dir in zip(name_prefixes, dirs):
            # Get all files in the directory
            file_names = helper.list_file_names(log_dir)

            # Filter log files
            for file_name in file_names:
                complete_prefix = f'{name_prefix}_'
                if file_name.startswith(complete_prefix) and file_name.endswith('.log'):
                    file_path = helper.join_paths(log_dir, file_name)

                    # Compute timestamp
                    file_ts = helper.str_to_datetime(
                        file_name.replace(
                            complete_prefix, '').replace('.log', '')
                    )
                    if file_ts is None:
                        logging_manager.get_root_logger().error(
                            f'Cannot read timestamp in the name of file {file_name}: ' +
                            'skipping this file'
                        )
                        continue

                    log_files.append(LogFile(file_path, file_ts))

        removed_files: List[LogFile] = []

        # Remove old log files
        for log_file in log_files:
            if (l_now - log_file.ts) > l_kept_interval:
                l_removed = helper.remove_file(log_file.path)
                if l_removed:
                    removed_files.append(log_file)
                else:
                    self.m_logger.error(
                        f'Error removing log file: {log_file.path}'
                    )

        if len(removed_files) > 0:
            self.m_logger.warning(
                'The following files have been removed:\n' +
                '\n'.join([log_file.path for log_file in removed_files])
            )
        else:
            self.m_logger.info('No log file was removed')

        self._step()

    def _renew_log_files(self):
        l_new_ts = helper.timestampNowFormatted()
        logging_manager.set_session_timestamp(l_new_ts)
        get_redisI().send_new_session_ts(l_new_ts)

        self._step()

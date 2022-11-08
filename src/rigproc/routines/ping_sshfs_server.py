from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons.helper import helper
from rigproc.commons.logger import logging_manager

from rigproc.params import redis_keys, general, bus


def ping_sshfs_server():
    server_ip= get_config().main.sshfs.ip.get()
    server_online= helper.ping(server_ip)
    if not server_online:
        logging_manager.get_root_logger().error(
            f'Pinging sshfs server at address {server_ip} failed'
        )
    get_redisI().updateStatusInfo(
        bus.module.videoserver,
        redis_keys.rip_status_field.sshfs_connected,
        general.status_ok if server_online else general.status_ko
    )

    # If the SSHFS server pings but the folder was not mounted, try to mount it again
    if server_online and not get_redisI().is_sshfs_mounted():
        l_mount_ts = get_redisI().when_was_sshfs_mounted()
        l_now = helper.timestampNowFloat()

        # One attempt every 5 minutes
        if isinstance(l_mount_ts, int) and (l_now - l_mount_ts) < 30000:
            return
        
        l_mounted = helper.mount_sshfs_folder(
            ip= get_config().main.sshfs.ip.get(),
            user= get_config().main.sshfs.user.get(),
            ssh_key= get_config().main.sshfs.ssh_key.get(),
            their_folder= get_config().main.sshfs.stg_folder.get(),
            my_folder= get_config().main.sshfs.rip_folder.get()
        )
        get_redisI().set_sshfs_mounted(l_mounted)
        if not l_mounted:
            logging_manager.get_root_logger().error('Error mounting SSHFS folder')

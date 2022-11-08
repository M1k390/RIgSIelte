from itertools import product

from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons.helper import helper
from rigproc.commons.logger import logging_manager

from rigproc.params import redis_keys, general, conf_values, bus


def preliminary_ping_cameras():
    """
    Sets Redis keys for cameras states to default values.

    To call before starting pinging cameras.
    """
    redis_poles= [redis_keys.camera.prrA_status, redis_keys.camera.prrB_status]
    camera_modules= [
        bus.module.cam1_a, bus.module.cam2_a, bus.module.cam3_a, 
        bus.module.cam4_a, bus.module.cam5_a, bus.module.cam6_a,
        bus.module.cam1_b, bus.module.cam2_b, bus.module.cam3_b, 
        bus.module.cam4_b, bus.module.cam5_b, bus.module.cam6_b
    ]
    for (prr_key, cam_num), module in zip(
        product(redis_poles, range(1, 7)), 
        camera_modules
    ):
        get_redisI().cache.set(f'{prr_key}{cam_num}', general.dato_non_disp)
        get_redisI().updateStatusInfo(
            module,
            module,
            general.dato_non_disp
        )


def ping_cameras():
    """
    Ping cameras and update Redis status keys
    """
    
    # Cameras on pole A
    _ping_camera(
        num=1,
        prr_key=redis_keys.camera.prrA,
        status_key_pref=redis_keys.camera.prrA_status,
        cam_ip=get_config().camera.ids.prrA.ip_1.get(),
        module=bus.module.cam1_a
    )
    _ping_camera(
        num=2,
        prr_key=redis_keys.camera.prrA,
        status_key_pref=redis_keys.camera.prrA_status,
        cam_ip=get_config().camera.ids.prrA.ip_2.get(),
        module=bus.module.cam2_a
    )
    _ping_camera(
        num=3,
        prr_key=redis_keys.camera.prrA,
        status_key_pref=redis_keys.camera.prrA_status,
        cam_ip=get_config().camera.ids.prrA.ip_3.get(),
        module=bus.module.cam3_a
    )
    _ping_camera(
        num=4,
        prr_key=redis_keys.camera.prrA,
        status_key_pref=redis_keys.camera.prrA_status,
        cam_ip=get_config().camera.ids.prrA.ip_4.get(),
        module=bus.module.cam4_a
    )
    _ping_camera(
        num=5,
        prr_key=redis_keys.camera.prrA,
        status_key_pref=redis_keys.camera.prrA_status,
        cam_ip=get_config().camera.ids.prrA.ip_5.get(),
        module=bus.module.cam5_a
    )
    _ping_camera(
        num=6,
        prr_key=redis_keys.camera.prrA,
        status_key_pref=redis_keys.camera.prrA_status,
        cam_ip=get_config().camera.ids.prrA.ip_6.get(),
        module=bus.module.cam6_a
    )

    # If the configuration is different from "binario doppio", stop at pole A
    if get_config().main.implant_data.configurazione.get() !=\
        conf_values.binario.doppio:
        return

    # Cameras on pole B
    _ping_camera(
        num=1,
        prr_key=redis_keys.camera.prrB,
        status_key_pref=redis_keys.camera.prrB_status,
        cam_ip=get_config().camera.ids.prrB.ip_1.get(),
        module=bus.module.cam1_b
    )
    _ping_camera(
        num=2,
        prr_key=redis_keys.camera.prrB,
        status_key_pref=redis_keys.camera.prrB_status,
        cam_ip=get_config().camera.ids.prrB.ip_2.get(),
        module=bus.module.cam2_b
    )
    _ping_camera(
        num=3,
        prr_key=redis_keys.camera.prrB,
        status_key_pref=redis_keys.camera.prrB_status,
        cam_ip=get_config().camera.ids.prrB.ip_3.get(),
        module=bus.module.cam3_b
    )
    _ping_camera(
        num=4,
        prr_key=redis_keys.camera.prrB,
        status_key_pref=redis_keys.camera.prrB_status,
        cam_ip=get_config().camera.ids.prrB.ip_4.get(),
        module=bus.module.cam4_b
    )
    _ping_camera(
        num=5,
        prr_key=redis_keys.camera.prrB,
        status_key_pref=redis_keys.camera.prrB_status,
        cam_ip=get_config().camera.ids.prrB.ip_5.get(),
        module=bus.module.cam5_b
    )
    _ping_camera(
        num=6,
        prr_key=redis_keys.camera.prrB,
        status_key_pref=redis_keys.camera.prrB_status,
        cam_ip=get_config().camera.ids.prrB.ip_6.get(),
        module=bus.module.cam6_b
    )


def _ping_camera(
    num: int, 
    prr_key: str, 
    status_key_pref: str, 
    cam_ip: str, 
    module: bus.module
):
    status_key= f'{status_key_pref}{num}'
    if cam_ip is not None:
        current_status= get_redisI().cache.get(status_key)

        # If using fake camera, simulate successed ping
        if get_config().main.modules_enabled.camera.get() == conf_values.module.fake:
            cam_online= True
        else:
            cam_online= helper.ping(cam_ip)

        # Ping successed
        if cam_online: 
            if current_status != general.status_ok:
                if current_status == general.status_error:
                    logging_manager.get_root_logger().warning(
                        f'La camera {num} sul palo {prr_key} ha risposto dopo un ping fallito'
                    )
                get_redisI().cache.set(status_key, general.status_ok)
        
        # Ping failed
        else:
            if current_status != general.status_error:
                logging_manager.get_root_logger().error(
                    f'Ping alla camera {num} sul palo {prr_key} non riuscito.'
                )
                get_redisI().cache.set(status_key, general.status_error)
        
        get_redisI().updateStatusInfo(
            module,
            module,
            general.status_ok if cam_online else general.status_ko
        )
    else:
        get_redisI().cache.set(status_key, general.status_error)
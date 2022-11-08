"""
Redis cache and persistent keys
"""

from enum import Enum, unique
from rigproc.commons.keywords import module

from rigproc.params import bus


# TODO

last_sw_version= 'last_version'
start_timestamp= 'start_timestamp'

" I/O messages "

# TODO
@unique
class io_msg(str, Enum):
    sorted_set= 'msg_sorted'
    msg_in= 'msg_in'
    msg_out= 'msg_out'


@unique
class temp(str, Enum):
    sorted_set = 'temp_sorted'


" flows "

# TODO
@unique
class flow(str, Enum):
    start= 'flow_start'
    stop= 'flow_stop'
    log= 'flow_log'
    start_time= 'flow_start_time'
    type= 'flow_type'
    stop_time= 'flow_end_time'
    errors= 'flow_errors'


@unique
class system(str, Enum):
    rigproc_pid = 'rigproc_pid'
    rigcam_pid = 'rigcam_pid'
    rigproc_mem_usage = 'rigproc_mem_usage'
    rigcam_mem_usage = 'rigcam_mem_usage'
    rigproc_mem_check_ts = 'rigproc_mem_check_ts'
    rigcam_mem_check_ts = 'rigcam_mem_check_ts'
    rigproc_uptime = 'rigproc_uptime'
    sshfs_mounted = 'sshfs_mounted'
    sshfs_mount_ts = 'sshfs_mount_ts' # also for failed mount attempts


# TODO
@unique
class implant(str, Enum):
    "RIP"
    rip_password= 'password'
    rip_config= 'configurazione'
    rip_name= 'nome_rip'
    plant_name= 'nome_ivip'
    plant_coord= 'coord_impianto'
    ip_remoto= 'ip_remoto'
    " BINARIO E LINEA "
    line_name= 'nome_linea'
    prrA= 'prrA_bin'
    prrB= 'prrB_bin'
    loc_tratta_pari_inizio= "loc_tratta_pari_inizio"
    loc_tratta_pari_fine= "loc_tratta_pari_fine"
    loc_tratta_dispari_inizio= "loc_tratta_dispari_inizio"
    loc_tratta_dispari_fine= "loc_tratta_dispari_fine"
    cod_pic_tratta_pari= 'cod_pic_tratta_pari'
    cod_pic_tratta_dispari= 'cod_pic_tratta_dispari'
    " SETTINGS "
    distanza_prr_IT_pari= 'distanza_prr_IT_pari'
    distanza_prr_IT_dispari= 'distanza_prr_IT_dispari'
    wire_calib_pari= 'wire_calib_pari'
    wire_calib_dispari= 'wire_calib_dispari'
    t_mosf_prrA= 't_mosf_prrA'
    t_mosf_prrB= 't_mosf_prrB'
    t_off_ivip_prrA= 't_off_ivip_prrA'
    t_off_ivip_prrB= 't_off_ivip_prrB'
    " Configurazine camere "
    camera_fov='fov'
    camera_sensor_width= 'sensor_width'
    camera_focal_distance= 'focal_distance'
    camera_brand= 'camera_brand'
    camera_model= 'camera_model'


# TODO
@unique
class sw_update(str, Enum):
	hash= 'schedule'
	date= 'update_date'
	time= 'update_time'
	version= 'update_version'
	transaction_id= 'transaction_id'
	req_id= 'request_id'
	mark_as_waiting= 'waiting'


# TODO
@unique
class camera(str, Enum):
    ready= 'camera_ready'

    prrA= 'prrA'
    prrA_id= 'camera_prrA_id_'
    prrA_status= 'camera_prrA_status_'
    prrA_ip= 'camera_prrA_ip_'

    prrB= 'prrB'
    prrB_id= 'camera_prrB_id_'
    prrB_status= 'camera_prrB_status_'
    prrB_ip= 'camera_prrB_ip_'


@unique
class rip_status_field(str, Enum):
    """ Field di stato su Redis per il videoserver """
    
    imgs_to_recover= 'imgs_to_recover'
    sshfs_connected= 'sshfs_connected'
    broker_connected= 'broker_connected'
    ntp_synced = 'ntp_synced'


@unique
class cam_status_field(str, Enum):
    """ Field di stato su Redis per le camere """

    status= 'status'

    #Values
    disconnected= 'disconnected'
    error= 'error'
    missing_frame= 'missing_frame'
    missing_trigger= 'missing_trigger'


# COMUNICAZIONE PROCESSO CAMERA

@unique
class cam_setup(str, Enum):
    # General Redis key
    key= 'rigcam_setup'

    # Process configuration
    proc_key=           'proc_conf'
    local_dir=          'local_path'
    simultaneous_dls=   'simultaneous_dls'
    trigger_timeout=    'trigger_timeout'
    max_frame_dl_time=  'max_frame_dl_time'
    event_timeout=      'event_timeout'

    # Logging configuration
    logging_key=    'logging_conf'
    format_code=    'format_code'
    formatter=      'formatter'
    console_level=  'console_level'
    file_level=     'file_level'
    file_dir=       'file_dir'
    file_name=      'file_name'
    file_mode=      'file_mode'
    log_to_root=    'log_to_root'
    root_file_prefix = 'root_file_prefix'
    root_dir =      'root_dir'
    session_ts =    'session_ts'

    # Camera configuration
    cam_key=        'camera_conf'
    cameras=        'cameras'
    cam_id=         'id'
    cam_ip=         'ip'
    cam_pole=       'pole'
    cam_num=        'num'
    cam_xml=        'xml'


@unique
class cam_msgs(str, Enum):
    exit= 'cam_exit'
    log_session_ts = 'log_session_ts'


@unique
class cam_startup(str, Enum):
    key=            'startup_report'
    running=        'running'
    opened_cameras= 'opened_cameras'
    errors=         'errors'
    pid =           'pid'


@unique
class cam_crash(str, Enum):
    key= 'cam_crash'


@unique
class cam_error(str, Enum):
    key_prefix= 'cam_error_'
    cam_id=     'cam_id'
    running=    'running'
    error_msg=  'error_msg'


@unique
class cam_event(str, Enum):
    key_prefix= 'cam_event_'
    pole= 'pole'
    shoot_arrays= 'shoot_arrays'
    timestamp= 'timestamp'
    shoots= 'shoots'
    cam_id= 'cam_id'
    cam_num= 'cam_num'
    img_path= 'img_paths'
    trans_id= 'trans_id'


@unique
class cam_stats(str, Enum):
    shoot_count = 'shoot_count'


# RECOVERING

@unique
class recovery(str, Enum):
    key_prefix=         'to_recover_'
    shoot_array=        'shoot_array'
    timestamp=          'timestamp'
    shoots=             'shoots'
    cam_id=             'cam_id'
    cam_num=            'cam_num'
    img_path=           'img_path'
    trans_id=           'trans_id'
    event_id=           'event_id'
    remote_folder=      'remote_folder'
    trig_json_model=    'trig_json_model'
    diag_json_model=    'diag_json_model'
    mosf_json_model=    'mosf_json_model'

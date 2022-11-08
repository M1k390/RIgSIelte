# -*- coding: utf-8 -*-

from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons import keywords
from rigproc.commons.wrappers import wrapkeys
from rigproc.flow import eventtrigflow_buildcmd as buildcmd
from rigproc.params import conf_values, bus, redis_keys, general
from rigproc.commons.helper import helper

def _buildFlowImplantStatus(self):
    """Tasklist builder analisi stato impianto (vedi CHECKLIST sielte)    
    """
    " Task master list"
    self.m_taskAll= {
        **self.m_taskBegin,
        **self.m_taskImplantStatus,
        **self.m_taskClosePipe
        }
    " Assegnazione di un ID ad ogni task della master list "
    l_idx= 0
    for task in self.m_taskAll:
        self.m_taskAll[task]['id']= l_idx
        l_idx += 1
    " lista funzioni abbinate alle entries della master task list "
    self.m_taskFuncList={
        'id': 0,
        'tasks':[self._prepareWork,
                self._checkIoVer, # I/O Ver
                self._checkIoVerAnswer,
                self._workDiagIo, # I/O Allarmi
                self._workDiagIoAnswer,
                self._workDiagMosfTxA, # MOSF TX A Versione
                self._workDiagMosfTxAAnswer,
                self._checkMosfTxASpeedStatus, # MOSF TX A Velocità/Allarmi
                self._checkMosfTxASpeedStatusAnswer,
                self._workMosfTxAOn, # MOSF TX A ON/OFF
                self._workMosfTxAOnAnswer,
                self._workDiagMosfTxB, # MOSF TX Versione B
                self._workDiagMosfTxBAnswer,
                self._checkMosfTxBSpeedStatus, # MOSF TX B Velocità/Allarmi
                self._checkMosfTxBSpeedStatusAnswer,
                self._workMosfTxBOn, # MOSF TX B ON/OFF
                self._workMosfTxBOnAnswer,
                self._workDiagMosfRxA, # MOSF RX A Versione
                self._workDiagMosfRxAAnswer,
                self._checkMosfRxAt0, # MOSF RX A Altezza
                self._checkMosfRxAt0Answer,
                self._checkMosfRxAData, # MOSF RX A Dati
                self._checkMosfRxADataAnswer,
                self._workDiagMosfRxB, # MOSF RX B Versione
                self._workDiagMosfRxBAnswer,
                self._checkMosfRxBt0, # MOSF RX B Altezza
                self._checkMosfRxBt0Answer,
                self._checkMosfRxBData, # MOSF RX B Dati
                self._checkMosfRxBDataAnswer,
                self._checkTrigAVer, # TRIGGER A Versione
                self._checkTrigAVerAnswer,
                self._workDiagTriggerAStatus, # Trigger Allarmi A
                self._workDiagTriggerAStatusAnswer,
                self._checkTrigBVer, # TRIGGER B Versione
                self._checkTrigBVerAnswer,
                self._workDiagTriggerBStatus, # Trigger Allarmi B
                self._workDiagTriggerBStatusAnswer,
                self._checkImgsToRecover,
                self._checkSshfsConnection,
                self._checkBrokerConnection,
                self._checkCamerasConnection,
                self._closePipe],
                # @TODO Trigger setting, trigger click
        'continue': True
        }

" I seguenti medoti (_check...) prelevano delle informazioni dal BUS e le salvano nella cache di Redis "

# NON uso questo work: cancellare parametri di stato provoca infatti l'invio multiplo di anomalie
# Inoltre, il comando implant_check mostra i parametri solo se il flow è terminato correttamente
# e le informazioni sono state pertanto aggiornate
def _workRemoveStatusInfo(self, p_data=None):
    """ 
    Elimino tutti i parametri di stato presenti in Redis 
    che verrano scritti durante questo flow.
    In questo modo, se ci sono problemi, evito di mostrare informazioni datate.
    """
    
    # MOSF TX A
    get_redisI().removeStatusInfo(bus.module.mosf_tx_a,     bus.module.mosf_tx_a)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_a,     bus.data_key.mtx_vers)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_a,     bus.data_key.mtx_velo)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_a,     bus.data_key.mtx_event)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_a,     bus.data_key.mtx_direction)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_a,     bus.data_key.mtx_onoff)

    # MOSF TX B
    get_redisI().removeStatusInfo(bus.module.mosf_tx_b,     bus.module.mosf_tx_b)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_b,     bus.data_key.mtx_vers)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_b,     bus.data_key.mtx_velo)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_b,     bus.data_key.mtx_event)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_b,     bus.data_key.mtx_direction)
    get_redisI().removeStatusInfo(bus.module.mosf_tx_b,     bus.data_key.mtx_onoff)

    # MOSF RX A
    get_redisI().removeStatusInfo(bus.module.mosf_rx_a,     bus.module.mosf_rx_a)
    get_redisI().removeStatusInfo(bus.module.mosf_rx_a,     bus.data_key.mrx_vers)
    get_redisI().removeStatusInfo(bus.module.mosf_rx_a,     bus.data_key.mosf_wire_t0)
    get_redisI().removeStatusInfo(bus.module.mosf_rx_a,     bus.data_key.mosf_wire_data_ok)

    # MOSF RX B
    get_redisI().removeStatusInfo(bus.module.mosf_rx_b,     bus.module.mosf_rx_b)
    get_redisI().removeStatusInfo(bus.module.mosf_rx_b,     bus.data_key.mrx_vers)
    get_redisI().removeStatusInfo(bus.module.mosf_rx_b,     bus.data_key.mosf_wire_t0)
    get_redisI().removeStatusInfo(bus.module.mosf_rx_b,     bus.data_key.mosf_wire_data_ok)

    # TRIGGER A
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.module.trigger_a)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_vers)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_onoff)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_cam_onoff)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_1_status)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_2_status)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_3_status)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_4_status)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_5_status)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_6_status)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_1_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_2_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_3_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_4_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_5_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_a,     bus.data_key.trig_flash_6_efficiency)

    # TRIGGER B
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.module.trigger_b)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_vers)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_onoff)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_cam_onoff)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_1_status)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_2_status)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_3_status)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_4_status)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_5_status)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_6_status)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_1_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_2_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_3_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_4_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_5_efficiency)
    get_redisI().removeStatusInfo(bus.module.trigger_b,     bus.data_key.trig_flash_6_efficiency)

    # IO
    get_redisI().removeStatusInfo(bus.module.io,            bus.module.io)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_alim_batt)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_IVIP_power)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_switch_prr_a)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_switch_prr_b)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_ldc_a)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_ldc_b)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_doors)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_sens1)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_sens2)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_vent1)
    get_redisI().removeStatusInfo(bus.module.io,            bus.data_key.io_vent2)

    # VIDEOSERVER
    get_redisI().removeStatusInfo(bus.module.videoserver,   redis_keys.rip_status_field.imgs_to_recover)
    get_redisI().removeStatusInfo(bus.module.videoserver,   redis_keys.rip_status_field.sshfs_connected)
    get_redisI().removeStatusInfo(bus.module.videoserver,   redis_keys.rip_status_field.broker_connected)

    # CAMERAS
    get_redisI().removeStatusInfo(bus.module.cam1_a,        bus.module.cam1_a)
    get_redisI().removeStatusInfo(bus.module.cam2_a,        bus.module.cam2_a)
    get_redisI().removeStatusInfo(bus.module.cam3_a,        bus.module.cam3_a)
    get_redisI().removeStatusInfo(bus.module.cam4_a,        bus.module.cam4_a)
    get_redisI().removeStatusInfo(bus.module.cam5_a,        bus.module.cam5_a)
    get_redisI().removeStatusInfo(bus.module.cam6_a,        bus.module.cam6_a)
    get_redisI().removeStatusInfo(bus.module.cam1_b,        bus.module.cam1_b)
    get_redisI().removeStatusInfo(bus.module.cam2_b,        bus.module.cam2_b)
    get_redisI().removeStatusInfo(bus.module.cam3_b,        bus.module.cam3_b)
    get_redisI().removeStatusInfo(bus.module.cam4_b,        bus.module.cam4_b)
    get_redisI().removeStatusInfo(bus.module.cam5_b,        bus.module.cam5_b)
    get_redisI().removeStatusInfo(bus.module.cam6_b,        bus.module.cam6_b)
    
    #
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


" MOSF TX Velocità/Allarmi "

def _checkMosfTxASpeedStatus(self, p_data=None):
    """ MOSF TX A Velocità/Allarmi """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTrainSpeedA(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkMosfTxASpeedStatusAnswer(self, p_data=None):
    l_speed= wrapkeys.getValue(p_data, keywords.data_mtx_velo_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_p,
        keywords.data_mtx_velo_key,
        l_speed
    )
    l_event= wrapkeys.getValue(p_data, keywords.data_mtx_event_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_p,
        keywords.data_mtx_event_key,
        wrapkeys.getValue(bus.mtx_event_labels, l_event)
    )
    l_direction= wrapkeys.getValue(p_data, keywords.data_mtx_direction_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_p,
        keywords.data_mtx_direction_key,
        l_direction
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True

def _checkMosfTxBSpeedStatus(self, p_data=None):
    """ MOSF TX B Velocità/Allarmi """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdTrainSpeedB(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkMosfTxBSpeedStatusAnswer(self, p_data=None):
    l_speed= wrapkeys.getValue(p_data, keywords.data_mtx_velo_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_d,
        keywords.data_mtx_velo_key,
        l_speed
    )
    l_event= wrapkeys.getValue(p_data, keywords.data_mtx_event_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_d,
        keywords.data_mtx_event_key,
        wrapkeys.getValue(bus.mtx_event_labels, l_event)
    )
    l_direction= wrapkeys.getValue(p_data, keywords.data_mtx_direction_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_d,
        keywords.data_mtx_direction_key,
        l_direction
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


" MOSF TX ON/OFF "

def _workMosfTxAOn(self, p_data=None):
    """ MOSF TX A ON/OFF """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfTxAOff(self, keywords.status_on))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _workMosfTxAOnAnswer(self, p_data=None):
    l_onoff= wrapkeys.getValue(p_data, keywords.data_mtx_onoff_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_p,
        keywords.data_mtx_onoff_key,
        l_onoff
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _workMosfTxBOn(self, p_data=None):
    """ MOSF TX B ON/OFF """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfTxBOff(self, keywords.status_on))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _workMosfTxBOnAnswer(self, p_data=None):
    l_onoff= wrapkeys.getValue(p_data, keywords.data_mtx_onoff_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_tx_d,
        keywords.data_mtx_onoff_key,
        l_onoff
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


" MOSF RX Altezza "

def _checkMosfRxAt0(self, p_data=None):
    """ MOSF RX A Altezza """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdWireT0A(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkMosfRxAt0Answer(self, p_data=None):
    l_event = wrapkeys.getValue(p_data, keywords.data_mrx_event_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_p,
        keywords.mosf_rx_p,
        wrapkeys.getValue(bus.mrx_event_labels, l_event)
    )
    l_t0= wrapkeys.getValue(p_data, keywords.data_mosf_wire_t0_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_p,
        keywords.data_mosf_wire_t0_key,
        l_t0
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _checkMosfRxBt0(self, p_data=None):
    """ MOSF RX B Altezza """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdWireT0B(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkMosfRxBt0Answer(self, p_data=None):
    l_event = wrapkeys.getValue(p_data, keywords.data_mrx_event_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_d,
        keywords.mosf_rx_d,
        wrapkeys.getValue(bus.mrx_event_labels, l_event)
    )
    l_t0= wrapkeys.getValue(p_data, keywords.data_mosf_wire_t0_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_d,
        keywords.data_mosf_wire_t0_key,
        l_t0
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


" MOSF RX Dati "

def _checkMosfRxAData(self, p_data=None):
    """ MOSF RX A Dati """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfDataA(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkMosfRxADataAnswer(self, p_data=None):
    l_data_ok= wrapkeys.getValue(p_data, keywords.data_mosf_wire_data_ok_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_p,
        keywords.data_mosf_wire_data_ok_key,
        l_data_ok
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _checkMosfRxBData(self, p_data=None):
    """ MOSF RX B Dati """
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdMosfDataB(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkMosfRxBDataAnswer(self, p_data=None):
    l_data_ok= wrapkeys.getValue(p_data, keywords.data_mosf_wire_data_ok_key)
    get_redisI().updateStatusInfo(
        keywords.mosf_rx_d,
        keywords.data_mosf_wire_data_ok_key,
        l_data_ok
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


" I/O Versione "

def _checkIoVer(self, p_data=None):
    self.m_mainCore['cmd_q'].put(buildcmd._buildCmdIOVer(self))
    self._incTaskId()
    self.m_taskFuncList['continue']= False
    return True


def _checkIoVerAnswer(self, p_data=None):
    get_redisI().updateStatusInfo(
        keywords.io,\
        keywords.data_io_vers_key,\
        wrapkeys.getValue(p_data, keywords.data_io_vers_key)
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


# VIDEOSERVER

def _checkImgsToRecover(self, p_data=None):
    recovery_local_folder= get_config().main.recovering.local_folder.get()
    if helper.dir_exists(recovery_local_folder):
        imgs_to_recover= helper.count_files(recovery_local_folder)
    else:
        self.m_logger.error(f'Cannot access local recovery folder: {recovery_local_folder}')
        imgs_to_recover= general.dato_non_disp
    get_redisI().updateStatusInfo(
        bus.module.videoserver,
        redis_keys.rip_status_field.imgs_to_recover,
        imgs_to_recover
    )
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _checkSshfsConnection(self, p_data=None):
    server_ip= get_config().main.sshfs.ip.get()
    server_online= helper.ping(server_ip)
    get_redisI().updateStatusInfo(
        bus.module.videoserver,
        redis_keys.rip_status_field.sshfs_connected,
        general.status_ok if server_online else general.status_ko
    )

    #
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


def _checkBrokerConnection(self, p_data=None):
    broker_online= helper.check_kafka_broker(get_config().broker.consume.broker.get())
    get_redisI().updateStatusInfo(
        bus.module.videoserver,
        redis_keys.rip_status_field.broker_connected,
        general.status_ok if broker_online else general.status_ko
    )

    #
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


# CAMERAS

def _checkCamerasConnection(self, p_data=None):
    camera_ids= get_config().camera.ids
    modules_prrA= [
        bus.module.cam1_a, bus.module.cam2_a, bus.module.cam3_a, 
        bus.module.cam4_a, bus.module.cam5_a, bus.module.cam6_a
    ]
    modules_prrB= [
        bus.module.cam1_b, bus.module.cam2_b, bus.module.cam3_b, 
        bus.module.cam4_b, bus.module.cam5_b, bus.module.cam6_b
    ]
    cam_ips_prrA= [
        camera_ids.prrA.ip_1.get(), camera_ids.prrA.ip_2.get(), camera_ids.prrA.ip_3.get(), 
        camera_ids.prrA.ip_4.get(), camera_ids.prrA.ip_5.get(), camera_ids.prrA.ip_6.get()
    ]
    cam_ips_prrB= [
        camera_ids.prrB.ip_1.get(), camera_ids.prrB.ip_2.get(), camera_ids.prrB.ip_3.get(), 
        camera_ids.prrB.ip_4.get(), camera_ids.prrB.ip_5.get(), camera_ids.prrB.ip_6.get()
    ]
    modules= modules_prrA + modules_prrB
    cam_ips= cam_ips_prrA + cam_ips_prrB

    
    for module, cam_ip in zip(modules, cam_ips):
        # If using fake camera, simulate successed ping
        if get_config().main.modules_enabled.camera.get() == conf_values.module.fake:
            cam_online= True
        else:
            self.m_logger.debug(f'Pinging {module}...')
            cam_online= helper.ping(cam_ip)
        get_redisI().updateStatusInfo(
            module,
            module,
            general.status_ok if cam_online else general.status_ko
        )
    
    #
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True


from rigproc.commons.helper import helper
from rigproc.flow.flow import Flow
from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.params import conf_values, general, internal, bus

from rigproc.commons.wrappers import wrapkeys

from rigproc.flow import eventtrigflow_buildcmd as buildcmd


class ModulesSelection:
	""" Data structure to store the module selection depending on the configuration (binario doppio/unico) """
	def __init__(self, pole_name, mosf_tx: bool, mosf_rx: bool, trigger: bool):
		self.pole_name= pole_name
		self.mosf_tx= mosf_tx
		self.mosf_rx= mosf_rx
		self.trigger= trigger


class FlowDiagnosis(Flow):
	"""
	Flow to execute an implant diagnosis.
	Does not have a task list, it only provide the methods to use in another Flow.
	"""
	def __init__(self, core, request_id=None):
		Flow.__init__(self, internal.flow_type.diagnosis, core, request_id)
		self._set_data()

	def _set_data(self):
		# Set pole modules depending on the configuration (binario doppio/unico)
		self.m_pole_modules= [
			ModulesSelection(
				pole_name=general.binario.pari,
				mosf_tx=True,
				mosf_rx=True,
				trigger=True
			)
		]
		conf_binario= get_config().main.implant_data.configurazione.get()
		if conf_binario == conf_values.binario.doppio:
			self.m_pole_modules.append(
				ModulesSelection(
					pole_name=general.binario.dispari,
					mosf_tx=True,
					mosf_rx=True,
					trigger=True
				)
			)
		else:
			self.m_pole_modules.append(
				ModulesSelection(
					pole_name=general.binario.dispari,
					mosf_tx=True,
					mosf_rx=False,
					trigger=False
				)
			)

		# Bus loop
		self.m_current_pole_index= None	# Reference to the list index of the current pole
		self.m_current_pole= None		# Reference to the current pole
		self.m_bus_loop_index= None		# Task index to perform the bus loop

	# Tasks

	def _bus_io_alarms(self):
		bus_cmd= buildcmd._buildCmdDiagIo(self)
		self.m_command_queue.put(bus_cmd)
		self._step()
		self.pause()

	def _bus_io_alarms_response(self):
		module_status= general.dato_non_disp
		key_status= {
			bus.data_key.io_alim_batt: general.dato_non_disp,
			bus.data_key.io_sw_prr_pari: general.dato_non_disp,
			bus.data_key.io_sw_prr_dispari: general.dato_non_disp,
			bus.data_key.io_rv_pari: general.dato_non_disp,
			bus.data_key.io_rv_dispari: general.dato_non_disp,
			bus.data_key.io_sw_armadio: general.dato_non_disp,
			bus.data_key.io_rip_status: general.dato_non_disp,
			bus.data_key.io_ntc_c: general.dato_non_disp,
			bus.data_key.io_alim_batt: general.dato_non_disp,
		}
		if self._answer is not self._MISSED:
			get_redisI().updateStatusInfo(
				bus.module.io,
				bus.module.io,
				general.status_ok
			)
			alim_batt= wrapkeys.getValue(self._answer, bus.data_key.io_alim_batt)
			get_redisI().updateStatusInfo(
				bus.module.io,
				bus.data_key.io_IVIP_power,
				bus.data_val.alim_alim if alim_batt == general.status_ok else bus.data_val.alim_batt
			)
			module_status= general.status_ok
			for data_key in key_status.keys():
				key_status[data_key]= wrapkeys.getValue(self._answer, data_key)
			# Update temperatures history
			l_ntc_c = wrapkeys.getValue(key_status, bus.data_key.io_ntc_c)
			l_cpu_temp = helper.get_cpu_temperature()
			if l_cpu_temp is None:
				l_cpu_temp = general.dato_non_disp
			get_redisI().add_temp_measure(l_ntc_c, l_cpu_temp)
		else:
			self._warning(f'Missed answer to: io_alarms')
			module_status= general.status_ko
		get_redisI().updateStatusInfo(
			bus.module.io,
			bus.module.io,
			module_status
		)
		for data_key, status in key_status.items():
			get_redisI().updateStatusInfo(
				bus.module.io,
				data_key,
				status
			)
		self._step()

	def _bus_io_ver(self):
		bus_cmd= buildcmd._buildCmdIOVer(self)
		self.m_command_queue.put(bus_cmd)
		self._step()
		self.pause()

	def _bus_io_ver_response(self):
		key_status= {
			bus.data_key.io_vers: general.dato_non_disp
		}
		if self._answer is not self._MISSED:
			for data_key in key_status.keys():
				key_status[data_key]= wrapkeys.getValue(self._answer, data_key)
		else:
			self._warning(f'Missed answer to: io_ver')
		for data_key, status in key_status.items():
			get_redisI().updateStatusInfo(
				bus.module.io,
				data_key,
				status
			)
		self._step()

	def _set_loop_diagnosis(self):
		self.m_bus_loop_index= self._get_current_task() + 1
		self._start_looping()
		self._step()

	def _set_bus_data(self):
		if self.m_current_pole_index is None:
			self.m_current_pole_index= 0
		elif self.m_current_pole_index < (len(self.m_pole_modules) - 1):
			self.m_current_pole_index += 1
		else:
			self.m_logger.critical('Internal error in bus loop management')
			self.m_current_pole_index= None
			self.m_current_pole= None
			self._step()
			return
		self.m_current_pole= self.m_pole_modules[self.m_current_pole_index]
		self._step()

	def _bus_mosf_tx_ver(self):
		if self.m_current_pole.mosf_tx:
			if self.m_current_pole.pole_name == general.binario.pari:
				bus_cmd= buildcmd._buildCmdMosfTxAVer(self)
			else:
				bus_cmd= buildcmd._buildCmdMosfTxBVer(self)
			self.m_command_queue.put(bus_cmd)
			self._step()
			self.pause()
		else:
			self._step()

	def _bus_mosf_tx_ver_response(self):
		if self.m_current_pole.pole_name == general.binario.pari:
			module= bus.module.mosf_tx_a
		else:
			module= bus.module.mosf_tx_b
		module_status= general.dato_non_disp
		key_status= {
			bus.data_key.mtx_vers: general.dato_non_disp
		}
		if self.m_current_pole.mosf_tx:
			if self._answer is not self._MISSED:
				module_status= general.status_ok
				for data_key in key_status.keys():
					key_status[data_key]= wrapkeys.getValue(self._answer, data_key)
			else:
				self._warning(f'Missed answer to: {module}_ver')
				module_status= general.status_ko
		get_redisI().updateStatusInfo(
			module,
			module,
			module_status
		)
		for data_key, status in key_status.items():
			get_redisI().updateStatusInfo(
				module,
				data_key,
				status
			)
		self._step()

	def _bus_mosf_rx_ver(self):
		if self.m_current_pole.mosf_rx:
			if self.m_current_pole.pole_name == general.binario.pari:
				bus_cmd= buildcmd._buildCmdMosfRxAVer(self)
			else:
				bus_cmd= buildcmd._buildCmdMosfRxBVer(self)
			self.m_command_queue.put(bus_cmd)
			self._step()
			self.pause()
		else:
			self._step()

	def _bus_mosf_rx_ver_response(self):
		if self.m_current_pole.pole_name == general.binario.pari:
			module= bus.module.mosf_rx_a
		else:
			module= bus.module.mosf_rx_b
		module_status= general.dato_non_disp
		key_status= {
			bus.data_key.mrx_vers: general.dato_non_disp
		}
		if self.m_current_pole.mosf_rx:
			if self._answer is not self._MISSED:
				module_status= general.status_ok
				for data_key in key_status.keys():
					key_status[data_key]= wrapkeys.getValue(self._answer, data_key)
			else:
				self._warning(f'Missed answer to: {module}_ver')
				module_status= general.status_ko
		get_redisI().updateStatusInfo(
			module,
			module,
			module_status
		)
		for data_key, status in key_status.items():
			get_redisI().updateStatusInfo(
				module,
				data_key,
				status
			)
		self._step()

	def _bus_trigger_alarms(self):
		if self.m_current_pole.trigger:
			if self.m_current_pole.pole_name == general.binario.pari:
				bus_cmd= buildcmd._buildCmdTriggerAStatus(self)
			else:
				bus_cmd= buildcmd._buildCmdTriggerBStatus(self)
			self.m_command_queue.put(bus_cmd)
			self._step()
			self.pause()
		else:
			self._step()

	def _bus_trigger_alarms_response(self):
		if self.m_current_pole.pole_name == general.binario.pari:
			module= bus.module.trigger_a
		else:
			module= bus.module.trigger_b
		module_status= general.dato_non_disp
		key_status= {
			bus.data_key.trig_flash_1_status: general.dato_non_disp,
			bus.data_key.trig_flash_2_status: general.dato_non_disp,
			bus.data_key.trig_flash_3_status: general.dato_non_disp,
			bus.data_key.trig_flash_4_status: general.dato_non_disp,
			bus.data_key.trig_flash_5_status: general.dato_non_disp,
			bus.data_key.trig_flash_6_status: general.dato_non_disp,
			bus.data_key.trig_flash_1_efficiency: general.dato_non_disp,
			bus.data_key.trig_flash_2_efficiency: general.dato_non_disp,
			bus.data_key.trig_flash_3_efficiency: general.dato_non_disp,
			bus.data_key.trig_flash_4_efficiency: general.dato_non_disp,
			bus.data_key.trig_flash_5_efficiency: general.dato_non_disp,
			bus.data_key.trig_flash_6_efficiency: general.dato_non_disp,
		}
		if self.m_current_pole.mosf_rx:
			if self._answer is not self._MISSED:
				module_status= general.status_ok
				for data_key in key_status.keys():
					key_status[data_key]= wrapkeys.getValue(self._answer, data_key)
			else:
				self._warning(f'Missed answer to: {module}_alarms')
				module_status= general.status_ko
		get_redisI().updateStatusInfo(
			module,
			module,
			module_status
		)
		for data_key, status in key_status.items():
			get_redisI().updateStatusInfo(
				module,
				data_key,
				status
			)
		self._step()

	def _bus_trigger_onoff(self):
		if self.m_current_pole.trigger:
			if self.m_current_pole.pole_name == general.binario.pari:
				cmd_data= general.status_on
				bus_cmd= buildcmd._buildCmdTriggerAOff(self, cmd_data)
			else:
				cmd_data= general.status_on
				bus_cmd= buildcmd._buildCmdTriggerBOff(self, cmd_data)
			self.m_command_queue.put(bus_cmd)
			self._step()
			self.pause()
		else:
			self._step()

	def _bus_trigger_onoff_response(self):
		if self.m_current_pole.pole_name == general.binario.pari:
			module= bus.module.trigger_a
		else:
			module= bus.module.trigger_b
		key_status= {
			bus.data_key.trig_flash_onoff: general.dato_non_disp,
			bus.data_key.trig_cam_onoff: general.dato_non_disp
		}
		if self.m_current_pole.mosf_rx:
			if self._answer is not self._MISSED:
				for data_key in key_status.keys():
					key_status[data_key]= wrapkeys.getValue(self._answer, data_key)
			else:
				self._warning(f'Missed answer to: {module}_on_off')
		for data_key, status in key_status.items():
			get_redisI().updateStatusInfo(
				module,
				data_key,
				status
			)
		self._step()

	def _evaluate_loop_diagnosis(self):
		if self.m_current_pole_index < (len(self.m_pole_modules) - 1):
			self._jump(self.m_bus_loop_index)
		else:
			self._stop_looping()
			self._step()
from datetime import datetime
import logging
from queue import Queue
from bisect import bisect_left
from typing import Optional, List

from rigproc.commons.redisi import get_redisI
from rigproc.commons.config import get_config

from rigproc.commons.helper import helper

from rigproc.commons.entities import EventToRecover
from rigproc.commons.utils import RecursiveTimer

from rigproc.params import internal


class RecoveryManager:
	def __init__(self, core):
		self.m_logger= logging.getLogger('root')
		self.m_command_queue: Queue= core['cmd_q']

		self.m_events_to_recover: List[EventToRecover]= sorted(get_redisI().get_events_to_recover())
		self.m_pending_recoveries: List[EventToRecover]= []

		self.m_normal_interval= get_config().main.recovering.timer_normal.get()
		self.m_massive_interval= get_config().main.recovering.timer_massive.get()
		self.m_recovery_timeout= get_config().main.recovering.recovery_timeout.get()

		self.m_massive_time_start= helper.str_to_time(get_config().main.recovering.massive_start.get())
		self.m_massive_time_end= helper.str_to_time(get_config().main.recovering.massive_finish.get())
		self.m_massive_mode= False

		self.m_timer: Optional[RecursiveTimer]= None
		self.m_switcher= RecursiveTimer(60, [self._switch_mode], name='Recovery mode switch')

		self.m_active= get_config().main.recovering.enabled.get()
		if not self.m_active:
			self.m_logger.warning('Recovery disabled')

	def start(self):
		self.m_switcher.start()
		self.m_logger.info('Recovery started')

	def pause(self):
		self.m_logger.warning('Pausing recovering')
		self.m_active= False

	def resume(self):
		self.m_logger.warning('Resuming recovering')
		self.m_active= get_config().main.recovering.enabled.get()

	def close(self):
		self.m_active= False
		self.m_switcher.cancel()
		if isinstance(self.m_timer, RecursiveTimer):
			self.m_timer.cancel()

	def wait(self):
		self.m_switcher.wait()
		if isinstance(self.m_timer, RecursiveTimer):
			self.m_timer.wait()

	def store_event(self, event: EventToRecover):
		threshold= get_config().main.recovering.threshold.get()
		if (len(self.m_events_to_recover) + len(self.m_pending_recoveries)) >= threshold:
			self.m_logger.critical(f'Cannot store any more event: max reached ({threshold})')
			self._clear_event(event)
			return
		event_index= bisect_left(self.m_events_to_recover, event) # Allows keeping the list sorted by timestamp
		self.m_events_to_recover.insert(event_index, event)
		get_redisI().store_event_to_recover(event)
		self.m_logger.warning(f'New event to recover. Total: {len(self.m_events_to_recover)}')

	def recovery_success(self, event: EventToRecover):
		if event in self.m_pending_recoveries:
			get_redisI().remove_event_to_recover(event)
			self.m_pending_recoveries.remove(event)
			self.m_logger.info('Event to recover removed after a recovery success.')
			if self.m_massive_mode:
				self._recover_an_event()
		else:
			self.m_logger.error('Error: tried to delete an event to recover that does not exist')

	def recovery_failure(self, event: EventToRecover):
		if event in self.m_pending_recoveries:
			event_index= bisect_left(self.m_events_to_recover, event)
			self.m_events_to_recover.insert(event_index, event)
			self.m_pending_recoveries.remove(event)
			self.m_logger.info(f'Event to recover restored after a recovery failure. Total to recover: {len(self.m_events_to_recover)}')
		else:
			self.m_logger.error('Error: tried to restore an event to recover that does not exist (anymore). Maybe too much time elapsed?')

	def _recover_an_event(self):
		"""Funzione eseguita periodicamente dal recovery_manager"""
		if len(self.m_events_to_recover) == 0:
			self.m_logger.debug('No event to recover')
		if not self.m_active:
			if len(self.m_events_to_recover) > 0:
				self.m_logger.debug('Recovery disabled')
			return

		# Check for orphans
		l_local_folder = get_config().main.recovering.local_folder.get()
		l_local_shoots = helper.list_file_names(l_local_folder)
		for shoot_name in l_local_shoots:
			l_shoot_path = helper.join_paths(l_local_folder, shoot_name)
			l_found_in_recovery = False
			for l_recovery_event in self.m_events_to_recover:
				for event_shoot in l_recovery_event.shoot_array.shoots:
					if event_shoot.img_path == l_shoot_path:
						l_found_in_recovery = True
						break
				if l_found_in_recovery:
					break
			if not l_found_in_recovery:
				self.m_logger.error(f'Found an orphan: {l_shoot_path}')
		
		l_now= datetime.now()
		for event in self.m_pending_recoveries:
			if (l_now - event.get_recovery_start()).seconds > self.m_recovery_timeout:
				self.m_logger.error('An event took too much time to recover: supposing failure')
				self.recovery_failure(event)
		if len(self.m_pending_recoveries) > 0:
			self.m_logger.debug('Waiting for a pending recovery before sending the next one')
			return
		if len(self.m_events_to_recover) > 0:
			self.m_logger.debug('Recovering an event')
			self._request_flow_recovery(self.m_events_to_recover[0])

	def _request_flow_recovery(self, event: EventToRecover):
		if event in self.m_events_to_recover:
			self.m_events_to_recover.remove(event)
			self.m_pending_recoveries.append(event)
			recovery_flow_request= {
				internal.cmd_key.cmd_type: internal.cmd_type.recovery_flow,
				internal.cmd_key.evt_to_recover: event
			}
			event.start_recovery()
			self.m_logger.info(f'Requesting to recover an event. Remaining: {len(self.m_events_to_recover)}')
			self.m_command_queue.put(recovery_flow_request)
		else:
			self.m_logger.critical('Internal error: tried to recover an event that does not exist')
			self.close()

	def _clear_event(self, event: EventToRecover):
		self.m_logger.critical(f'Deleting images for event: {event.timestamp}')
		for shoot in event.shoot_array.shoots:
			helper.remove_file(shoot.img_path)

	def _switch_mode(self):
		is_massive_time= self._is_massive_time()
		if is_massive_time and (not self.m_massive_mode or self.m_timer is None):
			self.m_logger.info('Recovery: switching to massive mode')
			if isinstance(self.m_timer, RecursiveTimer):
				self.m_timer.cancel()
				self.m_timer.wait()
			self.m_timer= RecursiveTimer(self.m_massive_interval, [self._recover_an_event], name='Massive recovery')
			self.m_massive_mode= True
			self.m_timer.start()
		elif not is_massive_time and (self.m_massive_mode or self.m_timer is None):
			self.m_logger.info('Recovery: switching to normal mode')
			if isinstance(self.m_timer, RecursiveTimer):
				self.m_timer.cancel()
				self.m_timer.wait()
			self.m_timer= RecursiveTimer(self.m_normal_interval, [self._recover_an_event], name='Normal recovery')
			self.m_massive_mode= False
			self.m_timer.start()

	def _is_massive_time(self) -> bool:
		if None in [self.m_massive_time_start, self.m_massive_time_end]:
			return False
		current_time= helper.onlyTimeNowObj()
		return current_time >= self.m_massive_time_start and current_time <= self.m_massive_time_end

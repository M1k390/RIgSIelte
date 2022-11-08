import asyncio
import gc
from enum import Enum, unique, auto
from typing import List, Dict
import logging

from rigcam.vimba_cam import TriggerData, FrameData, CameraData
from rigcam.camera import CameraObserver, CameraScheduler, CameraObject
from rigcam.rig_broker import RigBroker, get_rig_broker

from rigproc.commons.entities import CameraShoot, CameraShootArray
from rigproc.commons.helper import helper
from rigproc.params import internal, cli


#
#	LOG COLORS
#


def get_cam_task_color():
	while True:
		yield cli.color.back_white_forw_red.value
		yield cli.color.back_white_forw_green.value
		yield cli.color.back_white_forw_yellow.value
		yield cli.color.back_white_forw_blue.value
		yield cli.color.back_white_forw_violet.value
		yield cli.color.back_white_forw_teal.value
cam_task_color_iterator= get_cam_task_color()


def _get_cam_thread_color():
	while True:
		yield cli.color.back_sky_forw_red.value
		yield cli.color.back_sky_forw_green.value
		yield cli.color.back_sky_forw_yellow.value
		yield cli.color.back_sky_forw_blue.value
		yield cli.color.back_sky_forw_violet.value
		yield cli.color.back_sky_forw_teal.value
cam_thread_color_iterator= _get_cam_thread_color()


#
# 	POLE SCHEDULER
#


@unique
class ChildCamState(Enum):
	IDLE= 		auto() # before starting an event
	READY= 		auto() # after starting an event
	DELIVERED= 	auto() # data delivered
	MISS_FRAME= auto() # data delivered, but at least one missing frame
	NOT_READY=	auto() # data refused because the cam was not READY 
	REJECTED= 	auto() # data refused because the number of triggers was less than the one of the current event
	ERROR= 		auto() # Vimba error in camera loop (the loop will restart at the next iteration)
	DETACHED= 	auto() # the camera disconnected

PRE_DELIVERY_STATES= [ChildCamState.IDLE, ChildCamState.READY]
FINAL_STATES= [ChildCamState.DELIVERED, ChildCamState.MISS_FRAME, ChildCamState.NOT_READY, ChildCamState.REJECTED, ChildCamState.ERROR, ChildCamState.DETACHED]
ACCEPTED_STATES= [ChildCamState.DELIVERED, ChildCamState.MISS_FRAME]


@unique
class PoleState(str, Enum):
	INIT= 'INIT'				# Initial state	
	BOOTING= 'BOOTING'			# Starting camera tasks
	WAIT_START= 'WAIT_START'	# Waiting for event start
	WAIT_END= 'WAIT_END'		# Waiting for event end (with timeout)
	REPORT= 'REPORT'			# Generating report
	WRITE= 'WRITE'				# Writing images to disk
	SEND_DATA= 'SEND_DATA'		# Sending data to rigproc
	SEND_ERR= 'SEND_ERR'		# Sending errors to rigproc
	CLEAR= 'CLEAR'				# Clearing for restart
	END= 'END'					# Exited loop: terminating camera tasks
	TERM= 'TERM'				# Terminated


class PoleScheduler(CameraObserver):
	"""
	Provides the logic in managing a group of cameras connected to the same pole.
	Runs a loop executing the following operations:
		- wait for one of the cameras to detect the first trigger (camera event start);
		- wait for all the cameras to terminate the event or a timeout;
		- write the images to disk;
		- send the event report to rigproc;
		- send possible errors to rigproc;
		- reset all cameras.
	"""
	def __init__(
		self, 
		pole_name, 
		cameras: List[CameraObject], 
		network_semaphore: asyncio.Semaphore, 
		trigger_timeout, 
		max_frame_dl_time, 
		event_timeout, 
		local_dir
	) -> None:
		self.m_logger= logging.getLogger('camera')
		self.m_broker= get_rig_broker()
		self.pole= pole_name
		self._id= f'Pole {self.pole}'
		self._cameras_dict= {}
		self._schedulers: List[CameraScheduler]= []
		self._tasks= []
		for cam in cameras:
			self._cameras_dict[cam.id]= cam
			cam_sched= CameraScheduler(
				cam, 
				trigger_timeout, 
				max_frame_dl_time, 
				self, 
				task_color=next(cam_task_color_iterator), 
				thread_color=next(cam_thread_color_iterator)
			)
			self._schedulers.append(cam_sched)
			cam_sched.announce()

		self._network_semaphore= network_semaphore
		self._event_timeout= event_timeout
		self._local_dir= local_dir

		self._cam_states= {}
		self._cam_data= {}
		self._event_timestamp= None
		self._expected_triggers= None

		self._reset_cam_data()

		self._event_start= 	asyncio.Event() # Triggered when a whole event starts (i.e.: the first camera notifies an event)
		self._event_end= 	asyncio.Event() # Triggered when all the cameras notified and event (or stop is received)

		self._end_task= False

		self._state= PoleState.INIT

	def _log(self, msg):
		return f'{self._id} (state: {self._state}) >> {msg}'

	def _reset_non_accepted(self):
		for sched, state in zip(self._schedulers, self._cam_states.values()):
			if not state in ACCEPTED_STATES:
				sched.reset_loop()
	
	def _reset_cam_data(self):
		for sched, state in zip(self._schedulers, self._cam_states.values()):
			if state is ChildCamState.DETACHED:
				self.m_logger.warning(self._log(f'Detatching camera {sched.cam_id}'))
				self._schedulers.remove(sched)
				if isinstance(self.m_broker, RigBroker):
					self.m_broker.send_cam_error_report(sched.cam_id, False, internal.cam_error.cam_lost)
				else:
					self.m_logger.warning(self._log('Broker not available'))
		self._cam_states= {}
		self._cam_data= {}
		for sched in self._schedulers:
			self._cam_states[sched.cam_id]= ChildCamState.IDLE
			self._cam_data[sched.cam_id]= None
		self._event_timestamp= None
		self._expected_triggers= None
		if len(self._schedulers) == 0:
			self.m_logger.error(self._log('All cameras disconnected: terminating'))
			self.stop_loop()
	
	async def loop(self):
		self._state= PoleState.BOOTING
		for cam_sched in self._schedulers:
			task= asyncio.create_task(cam_sched.loop())
			opened= await cam_sched.is_camera_opened()
			if opened:
				self._tasks.append(task)
				cam_id= cam_sched.cam_id
				cam_ip= cam_sched.get_camera_ip()
				exp_ip= self._cameras_dict[cam_id].ip
				open_log= f'Camera {cam_id} opened at IP address {cam_ip}'
				if exp_ip != cam_ip:
					open_log += f' (expected was {exp_ip})'
				self.m_logger.info(self._log(open_log))
			else:
				cam_sched.stop_loop()
				self._schedulers.remove(cam_sched)
		self.m_logger.info(self._log(f'{len(self._schedulers)} cameras registered'))

		if len(self._schedulers) > 0:
			for cam_sched in self._schedulers:
				cam_sched.start_loop()
		else:
			self._end_task= True

		# Pole loop
		while not self._end_task:
			# Wait for an event to start
			self._state= PoleState.WAIT_START
			self.m_logger.info(self._log('Waiting event'))
			await self._event_start.wait()
			if self._end_task:
				break
			
			# Execute event
			self._state= PoleState.WAIT_END
			self.m_logger.info(self._log(f'Executing event (timeout = {self._event_timeout})'))
			_, pending= await helper.wait_first([self._event_end.wait()], timeout=self._event_timeout)
			if len(pending) > 0:
				self.m_logger.error(f'Timeout before event completion ({self._event_timeout} seconds)')
				self._reset_non_accepted()
			if self._end_task:
				break
			
			# Event complete: do something with the collected data...
			self._state= PoleState.REPORT
			self.m_logger.info(self._log(f'Processing event: {helper.timestamp_to_formatted(self._event_timestamp)}'))
			total_triggers= 0
			total_frames= 0

			# Print event data and set event timestamp
			self.m_logger.info(f'Generating report. Current cam data: {self._cam_data}')
			try:
				report= ''
				for cam_sched in self._schedulers:
					frames_num= 0
					cam_id= cam_sched.cam_id
					paired_data= self._cam_data[cam_id]
					if isinstance(paired_data, dict):
						for data in paired_data.values():
							if data is not None:
								frames_num += 1
						summary= f' ({len([fr for fr in paired_data.values() if isinstance(fr, FrameData)])}/{self._expected_triggers})'
					else:
						summary= ''
					report += f'\n\x1b[0;30;43m{cam_id}\x1b[0m{summary}'
					state= self._cam_states[cam_id]
					if isinstance(state, ChildCamState):
						report += '\n' + state.name
					if state in ACCEPTED_STATES:
						for trigger, frame in paired_data.items():
							if isinstance(trigger, TriggerData):
								trig_num= trigger.num
								total_triggers += 1
							else:
								trig_num= 'error'
							if isinstance(frame, FrameData):
								frame_id= frame.id
								total_frames += 1
							else:
								frame_id= 'none'
							report += f'\n{trig_num}: {frame_id}'
				report += f'\nTotal: {total_frames}/{total_triggers}'
				self.m_logger.info(report)
			except Exception as e:
				self.m_logger.error(f'Error printing event report: {e}')

			# Write images
			self._state= PoleState.WRITE
			self.m_logger.info('Writing files to disk')
			frame_files: Dict[int, Dict[CameraObject, str]]= {}	# {frame_num: {cam_num: frame_file}}
			frame_timestamps: Dict[int, str]= {}		# {frame_num: timestamp}
			for cam_sched in self._schedulers:
				cam_id= cam_sched.cam_id
				state = self._cam_states[cam_id]
				if not state in ACCEPTED_STATES:
					continue
				paired_data= self._cam_data[cam_id]
				if not isinstance(paired_data, dict):
					continue
				for trigger, frame in paired_data.items():
					if not isinstance(trigger, TriggerData) or not isinstance(frame, FrameData):
						self.m_logger.info(f'Skipping missing frame from camera {cam_id}')
						continue
					self.m_logger.debug(self._log(f'Writing cam {cam_id} frame {trigger.num}'))
					img_file_path= helper.join_paths(
						helper.abs_path(self._local_dir),
						f'evt_{self._event_timestamp}_cam_{cam_id}_frame_{trigger.num}.data'
					)
					l_img_written= helper.write_file(img_file_path, frame.img, binary=True)
					if l_img_written:
						img_file_size= helper.get_file_size(img_file_path)
						if img_file_size is None:
							self.m_logger.error(self._log(f'Error reading file size of frame {trigger.num} from camera {cam_id}'))
						elif img_file_size != frame.img_size:
							self.m_logger.error(self._log(f'Frame {trigger.num}, camera {cam_id}: ' + \
								f'the image file size ({img_file_size} B) is different from the expected frame size ({frame.img_size} B).' + \
									'Try reducing the transmission speed or the maximum allowed simultaneous downloads.'))
						else:
							self.m_logger.info(f'Frame {frame.id} from camera {cam_id} correctly written to disk')
							# Add image file to the list
							if trigger.num not in frame_files.keys():
								frame_files[trigger.num]= {}
							frame_files[trigger.num][cam_sched.camera]= img_file_path
							# Update image timestamp if necessary
							if trigger.num not in frame_timestamps.keys() or trigger.pc_ts < frame_timestamps[trigger.num]:
								frame_timestamps[trigger.num]= trigger.pc_ts
					else:
						self.m_logger.error(self._log(f'The frame {trigger.num} from camera {cam_id} was not written to file'))
					del frame
				del paired_data

			# Send data
			self._state= PoleState.SEND_DATA
			self.m_logger.info('Sending data to rigproc')
			shoot_arrays= []
			for trig_num, frames in frame_files.items():
				shoot_arrays.append(CameraShootArray(
					timestamp= frame_timestamps[trig_num],
					shoots= [CameraShoot(camera.id, camera.num, img_path) for camera, img_path in frames.items()],
					trans_id= helper.new_trans_id()
				))
			if isinstance(self.m_broker, RigBroker):
				self.m_broker.send_event_data(self._event_timestamp, self.pole, shoot_arrays)
			else:
				self.m_logger.warning(self._log('Broker not available'))

			# Send errors
			self._state= PoleState.SEND_ERR
			self.m_logger.info(self._log('Sending errors, if any'))
			for cam_id, state in self._cam_states.items():
				if state is ChildCamState.NOT_READY:
					if isinstance(self.m_broker, RigBroker):
						self.m_broker.send_cam_error_report(cam_id, True, internal.cam_error.unexpected_data)
					else:
						self.m_logger.warning(self._log('Broker not available'))
				elif state is ChildCamState.REJECTED:
					if isinstance(self.m_broker, RigBroker):
						self.m_broker.send_cam_error_report(cam_id, True, internal.cam_error.less_triggers)
					else:
						self.m_logger.warning(self._log('Broker not available'))
				elif state is ChildCamState.ERROR:
					if isinstance(self.m_broker, RigBroker):
						self.m_broker.send_cam_error_report(cam_id, True, internal.cam_error.exec_error)
					else:
						self.m_logger.warning(self._log('Broker not available'))
				elif state is ChildCamState.IDLE:
					if isinstance(self.m_broker, RigBroker):
						self.m_broker.send_cam_error_report(cam_id, True, internal.cam_error.missed_trigger)
					else:
						self.m_logger.warning(self._log('Broker not available'))
				elif state is ChildCamState.READY or state is ChildCamState.MISS_FRAME:
					if isinstance(self.m_broker, RigBroker):
						self.m_broker.send_cam_error_report(cam_id, True, internal.cam_error.missed_frame)
					else:
						self.m_logger.warning(self._log('Broker not available'))

			self._state= PoleState.CLEAR

			self._event_start.clear()
			self._event_end.clear()
			self._reset_cam_data()

			gc.collect()
			self.m_logger.debug(self._log(f'Garbage collector executed: {gc.get_count()}'))

			# Restart all camera loops
			for cam_sched in self._schedulers:
				if await cam_sched.is_camera_opened():
					cam_sched.restart_loop()
				else:
					cam_sched.stop_loop()
					self._schedulers.remove(cam_sched)
			# TODO remove?
			if len(self._schedulers) == 0:
				self.m_logger.error(self._log('Lost connection to all cameras: terminating...'))
				self.stop_loop()
		
		# Loop exited: terminate
		self._state= PoleState.END
		self.m_logger.info(self._log('Terminating camera tasks'))
		for cam_sched in self._schedulers:
			cam_sched.stop_loop()
		for task in self._tasks:
			await task
		
		self._state= PoleState.TERM
		self.m_logger.warning(self._log('Task terminated'))

	def stop_loop(self):
		self.m_logger.info(self._log('Stop command received'))
		self._end_task= True
		self._event_start.set()
		self._event_end.set()

	async def get_opened_cameras(self):
		cameras_opened= []
		for sched in self._schedulers:
			if await sched.is_camera_opened():
				cameras_opened.append(sched.cam_id)
		return cameras_opened
	
	def set_network_semaphore(self, semaphore_arity):
		""" Set the number of simultanous downloads from the cameras """
		self.m_logger.info(self._log(f'Setting network semaphore to {semaphore_arity}'))
		self._network_semaphore= asyncio.Semaphore(semaphore_arity)


	# CameraObserver methods (called by CameraScheduler)

	def start_event(self, cam_id):
		if self._cam_states[cam_id] is ChildCamState.IDLE:
			self._cam_states[cam_id]= ChildCamState.READY
			if not self._event_start.is_set():
				self._event_start.set()
				self._event_timestamp= helper.timestampNow()
	
	def deliver_data(self, cam_data: CameraData):
		if self._cam_states[cam_data.cam_id] is ChildCamState.READY:
			paired_data= cam_data.get_paired_data()
			num_of_shoots= len(paired_data.keys())
			if self._expected_triggers is None:
				self.m_logger.info(self._log(f'Expected shoots: {num_of_shoots}'))
				self._expected_triggers= num_of_shoots
			if self._expected_triggers == num_of_shoots:
				self._cam_data[cam_data.cam_id]= paired_data
				if any([frame is None for frame in paired_data.values()]):
					self._cam_states[cam_data.cam_id]= ChildCamState.MISS_FRAME
				else:
					self._cam_states[cam_data.cam_id]= ChildCamState.DELIVERED
			elif self._expected_triggers < num_of_shoots:
				self.m_logger.warning(self._log(f'Updating expected shoots: {num_of_shoots}'))
				for sched in self._schedulers:
					if self._cam_states[sched.cam_id] in ACCEPTED_STATES:
						self.m_logger.error(self._log(
							f'Rejecting camera {sched.cam_id} because it delivered {self._expected_triggers} instead of {num_of_shoots}'))
						self._cam_states[sched.cam_id]= ChildCamState.REJECTED
						self._cam_data[sched.cam_id]= None
				self._cam_data[cam_data.cam_id]= paired_data
				self._expected_triggers= num_of_shoots
				self._cam_states[cam_data.cam_id]= ChildCamState.DELIVERED
			if all([state in FINAL_STATES for state in self._cam_states.values()]):
				self._event_end.set()
		else:
			self._cam_states[cam_data.cam_id]= ChildCamState.NOT_READY

	async def acquire_download_permission(self):
		await self._network_semaphore.acquire()

	def release_download_permission(self):
		self._network_semaphore.release()

	def report_camera_error(self, cam_id):
		self.m_logger.error(self._log(f'Camera {cam_id}: loop error detected'))
		self._cam_states[cam_id]= ChildCamState.ERROR
		if all([state in FINAL_STATES for state in self._cam_states.values()]):
				self._event_end.set()

	def detach_camera(self, cam_sched: CameraScheduler):
		self._cam_states[cam_sched.cam_id]= ChildCamState.DETACHED
		if not self._event_start.is_set():
			self._reset_cam_data()
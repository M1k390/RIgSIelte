from enum import Enum, unique
import time
import vimba
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from rigcam.vimba_cam import CameraThread
from rigproc.commons.logger import color_delimiter
from rigproc.commons.helper import helper


#
# CAMERA SCHEDULER
#

class CameraObserver:
	"""
	Interface of an observer of che CameraScheduler.
	Provides methods to request and wait for data from the scheduler.
	It is extended by Pole.
	"""
	def start_event(self, cam_id):
		pass
	def deliver_data(self, cam_data):
		pass
	async def acquire_download_permission(self):
		pass
	def release_download_permission(self):
		pass
	def report_camera_error(self, cam_id):
		pass
	def detach_camera(self, cam_sched):
		pass


class CameraObject:
	""" Camera data wrapper """
	def __init__(self, id: str, vimba_camera: vimba.Camera, pole: str, num: int, ip: str, xml_file: str) -> None:
		self.id= id
		self.vimba_camera= vimba_camera
		self.pole= pole
		self.num= num
		self.ip= ip
		self.xml_file= xml_file


#
#	CAMERA SCHEDULER (TASK)
#


@unique
class CameraState(str, Enum):
	INIT= 'INIT'					# Initial state
	WAIT_LOOP= 'WAIT_LOOP'			# Waiting for loop start
	WAIT_START= 'WAIT_START'		# Waiting for event start
	WAIT_TO= 'WAIT_TO'				# Waiting for triggers timeout
	WAIT_DL_PERM= 'WAIT_DL_PERM'	# Waiting for download permission
	WAIT_DL_ALL= 'WAIT_DL_ALL'		# Waiting for download completion
	WAIT_RESTART= 'WAIT_RESTART'	# Waiting for loop restart
	END= 'END'						# Loop end: waiting for thread termination
	TERM= 'TERM'					# Task terminated


class CameraScheduler:
	"""
	Provides the logic in managing a single camera.
	Runs a loop that executes the following operations:
		- wait for a trigger detected by the camera;
		- wait for a timeout, assuring to receive all the triggers;
		- acquire network permission from the pole manager;
		- download the frames from the cameras;
		- stop download and release the network permission.
	"""
	def __init__(self, camera: CameraObject, trigger_timeout, max_frame_dl_time, observer: CameraObserver, 
					task_color=None, thread_color=None):
		self.m_logger= logging.getLogger('camera')
		self.camera= camera
		self.cam_id= camera.id
		self.cam_num= camera.num
		self._id= f'Schedul {self.cam_id}'

		self._trigger_timeout= trigger_timeout
		self._max_frame_dl_time= max_frame_dl_time

		self._observer= observer

		self._log_color= task_color

		self._cam_thread= CameraThread(camera.vimba_camera, camera.xml_file, thread_color)
		self._cam_thread.setName(f'{camera.pole}_{camera.num}')

		self._start_loop= asyncio.Event()	# Wait for this event before starting the loop
		self._reset= asyncio.Event()		# If set, stop looping and wait for restart
		self._restart = asyncio.Event()		# Wait for this event at the end of the loop
		self._end_task= False				# True if terminating

		self._state = CameraState.INIT
	
	def _log(self, msg):
		text= f'{self._id} (state: {self._state}) >> {msg}'
		if self._log_color is not None:
			text= self._log_color + color_delimiter + text
		return text

	def announce(self):
		self.m_logger.info(self._log('Ready'))
		self._cam_thread.announce()

	async def _check_camera_termination(self):
		with ThreadPoolExecutor() as thread_executor:
			await asyncio.get_running_loop().run_in_executor(thread_executor, self._cam_thread.wait_termination)
		self.m_logger.warning('Camera thread termination detected')
		if not self._end_task:
			self._observer.detach_camera(self)
			self.stop_loop()

	def _notify_termination(self):
		if not self._end_task:
			self._observer.detach_camera(self)

	async def loop(self):
		self._state= CameraState.WAIT_LOOP
		self.m_logger.info(self._log('Starting loop'))
		self._cam_thread.start()
		await helper.wait_first([self._reset.wait(), self._start_loop.wait()])
		if not self._end_task:
			self._cam_thread.start_execution()

		while not self._end_task:
			self._reset.clear()
			self._restart.clear()

			# Wait for the first trigger
			self._state= CameraState.WAIT_START
			self.m_logger.info(self._log('Waiting for the first trigger'))
			while True:
				if self._reset.is_set() or\
					self._cam_thread.is_loop_error() or\
					self._cam_thread.is_terminated() or\
					self._cam_thread.is_first_trigger():
					break
				await asyncio.sleep(1)
			if self._cam_thread.is_terminated():
				self._notify_termination()
				break
			if self._reset.is_set():
				self._cam_thread.reset_and_flush()
				continue
			if self._cam_thread.is_loop_error():
				self.m_logger.error(self._log('Loop error detected while waiting for the first trigger'))
				self._observer.report_camera_error(self.cam_id)

			# Wait trigger timeout
			if not self._cam_thread.is_loop_error():
				self._observer.start_event(self.cam_id)
				self._state= CameraState.WAIT_TO
				self.m_logger.info(self._log(f'Waiting for the trigger timeout ({self._trigger_timeout} seconds)'))
				
				# Save current timestamp to check timeout
				first_trigger_timestamp= time.time()
				while True:
					if self._reset.is_set() or\
						self._cam_thread.is_loop_error() or\
						self._cam_thread.is_terminated() or\
						(time.time() - first_trigger_timestamp) >= self._trigger_timeout:
						break
					await asyncio.sleep(1)
				if self._cam_thread.is_terminated():
					self._notify_termination()
					break
				if self._reset.is_set():
					self._cam_thread.reset_and_flush()
					continue
				if self._cam_thread.is_loop_error():
					self.m_logger.error(self._log('Loop error detected while waiting for the trigger timeout'))
					self._observer.report_camera_error(self.cam_id)

			# Tell thread to stop listening to triggers
			if not self._cam_thread.is_loop_error():
				self.m_logger.info(self._log('Stop listening to triggers'))
				self._cam_thread.stop_listening()

			# Acquire network
			if not self._cam_thread.is_loop_error():
				self._state= CameraState.WAIT_DL_PERM
				self.m_logger.info(self._log('Acquiring network'))

				# ONLY wait for acquiring dl permission: 
				# this guarantees that after this line we acquired the permission
				await self._observer.acquire_download_permission()

				if self._cam_thread.is_terminated():
					self._observer.release_download_permission()
					self._notify_termination()
					break
				if self._reset.is_set():
					self._observer.release_download_permission()
					self._cam_thread.reset_and_flush()
					continue

			if self._cam_thread.is_loop_error():
				self._observer.release_download_permission()
			else:
				dl_timeout= self._max_frame_dl_time * self._cam_thread.get_expected_frames()
				self._state= CameraState.WAIT_DL_ALL
				self.m_logger.info(self._log(f'Starting download (timeout = {dl_timeout})'))
				
				# Start download
				self._cam_thread.start_download()
				start_dl_timestamp= time.time()
				dl_timeout_occurred= False
				while True:
					if (time.time() - start_dl_timestamp) >= dl_timeout:
						dl_timeout_occurred= True
						break
					if self._reset.is_set() or\
						self._cam_thread.is_loop_error() or\
						self._cam_thread.is_terminated() or\
						self._cam_thread.is_dl_complete():
						break
					await asyncio.sleep(1)
				if self._cam_thread.is_terminated():
					self._observer.release_download_permission()
					self._notify_termination()
					break
				if self._reset.is_set():
					self._observer.release_download_permission()
					self._cam_thread.reset_and_flush()
					continue
				if self._cam_thread.is_loop_error():
					self.m_logger.info(self._log('Loop error detected while downloading frames. Releasing network'))
					self._observer.release_download_permission()
					self._observer.report_camera_error(self.cam_id)
				if dl_timeout_occurred:
					self.m_logger.error(self._log(f'Timeout before all frames downloaded ({dl_timeout} seconds)'))

			# Stop download and release network
			if not self._cam_thread.is_loop_error():
				self.m_logger.info(self._log('Stopping download and releasing network'))
				self._cam_thread.stop_download()
				self._observer.release_download_permission()

				# Deliver data
				self._observer.deliver_data(self._cam_thread.get_data())

			# Wait for restart signal
			self._state= CameraState.WAIT_RESTART
			self.m_logger.info(self._log('Waiting for restart'))
			while True:
				if self._reset.is_set() or\
					self._cam_thread.is_loop_error() or\
					self._cam_thread.is_terminated() or\
					self._restart.is_set():
					break
				await asyncio.sleep(1)
			if self._cam_thread.is_terminated():
				self._notify_termination()
				break
			if not self._end_task:
				# Reset camera thread execution
				self._cam_thread.restart_execution()
		
		# Exited from loop: interrupt camera thread
		self._state= CameraState.END
		self.m_logger.info(self._log('Exited from loop: terminating camera thread'))
		if not self._cam_thread.is_terminated():
			self._cam_thread.stop_execution()
			while True:
				if self._cam_thread.is_terminated():
					break
				await asyncio.sleep(1)
		
		self._state= CameraState.TERM
		self.m_logger.info(self._log('Task terminated'))

	def start_loop(self):
		""" Start the camera loop """
		self._start_loop.set()

	def reset_loop(self):
		""" 
		Reset loop and wait for restart (for errors and timeouts)
		"""
		self.m_logger.info(self._log('Resetting camera loop'))
		self._reset.set()
	
	def restart_loop(self):
		"""
		Restart loop
		"""
		self._restart.set()

	def stop_loop(self):
		""" Stop the camera loop """
		self._end_task= True
		self._reset.set()

	async def is_camera_opened(self):
		""" Wait for the camera thread to be ready and returns the camera state (open/error) """
		run_loop= asyncio.get_running_loop()
		thread_executor= ThreadPoolExecutor()
		return await run_loop.run_in_executor(thread_executor, self._cam_thread.is_opened)

	def get_camera_ip(self):
		return self._cam_thread.cam_ip
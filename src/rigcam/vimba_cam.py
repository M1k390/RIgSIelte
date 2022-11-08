from enum import Enum, unique
import vimba
from vimba.c_binding import vimba_c
import threading
import time
from typing import List
import logging

from rigproc.commons.logger import color_delimiter
from rigproc.commons.helper import helper
from vimba.camera import PersistType


#
# DATA
#

class TriggerData:
	""" Stores the info about a single trigger signal detected """
	def __init__(self, num, cam_ts, pc_ts):
		self.num= num # trigger number inside the event (starting from 1)
		self.cam_ts= cam_ts # the timestamp provided by the camera
		self.pc_ts= pc_ts # the computer timestamp
	def __repr__(self) -> str:
		return f'Trigger {self.num} (@cam{self.cam_ts}) - (@pc{self.pc_ts})'

class FrameData:
	""" Stores the info about a single frame downloaded """
	def __init__(self, id, cam_ts, img_size, img):
		self.id= id # the frame id provided by the camera
		self.cam_ts= cam_ts # the frame timestamp provided by the camera
		self.img_size= img_size # the image size in bytes
		self.img= img # bytearray containing the image
	def __repr__(self) -> str:
		return f'Frame {self.id} (@cam{self.cam_ts}) - [{len(self.img)}bytes]'

class CameraData:
	""" Stored the info about all the triggers and frames received during an event """
	def __init__(self, cam_id, triggers: List[TriggerData], frames: List[FrameData]):
		self.m_logger = logging.getLogger('camera')
		self.cam_id= cam_id
		self.triggers= triggers
		self.frames= frames

	def get_paired_data(self) -> dict:
		self.m_logger.info(
			f'Retrieving paired data from camera {self.cam_id}. Triggers: {self.triggers}. Frames: {self.frames}')
		paired_data= {}
		for trigger in self.triggers:
			paired_data[trigger]= None
		for frame in self.frames:
			for i, trigger in enumerate(self.triggers):
				if (i + 1) >= len(self.triggers) or self.triggers[i + 1].cam_ts > frame.cam_ts:
					if paired_data[trigger] is None:
						paired_data[trigger]= frame
					break
		return paired_data


#
# CAMERA THREAD
#


@unique
class CameraMode(str, Enum):
	INIT= 'INIT'		# Initial state
	WAIT= 'WAIT'		# Before starting the execution
	STARTED= 'STARTED'	# After starting the execution
	HOLD= 'HOLD'		# STREAM: ON, HOLD: ON -> Register triggers and hold frames
	DL= 'DL'			# STREAM: ON, HOLD: OFF -> Download frames
	FLUSH= 'FLUSH'		# STREAM: OFF, HOLD: OFF -> Flush triggers and frames
	CLOSED= 'CLOSED'	# Camera closed


class CameraThread(threading.Thread):
	"""
	Manages a single camera with the Vimba APIs.
	Its pipeline is managed by a CameraScheduler objects.
	Vimba APIs need to run in a separate thread to correctly receive callbacks.
	"""
	def __init__(self, camera: vimba.Camera, xml_file_path: str, log_color=None):
		threading.Thread.__init__(self)
		self.m_logger= logging.getLogger('camera')
		self._camera= camera
		self.cam_id= camera.get_id()
		self._id= f'_Thread {self.cam_id}'
		self.cam_ip= None
		self._xml_file= helper.abs_path(helper.universal_path(xml_file_path))

		self._log_color= log_color

		# Checking camera connection
		self._camera_open_attempt= threading.Event()

		# Camera features
		self._event_selector_feature= None
		self._event_notification_feature= None
		self._hold_stream_feature= None
		self._trigger_frame_id_feature= None
		self._trigger_timestamp_feature= None
		self._stream_rate_constraint_feature= None

		# Callback activation
		self._listen_to_triggers = False
		self._listen_to_frames = False

		# Looping events
		self._stop_listening= threading.Event()		# Wait for this event while listening to triggers
		self._start_download= threading.Event()		# Wait for this event before setting "dl mode"
		self._stop_download= threading.Event()		# Wait for this event before setting "flush mode"
		self._reset= threading.Event()				# If set, go directly to "flush mode"
		self._restart = threading.Event()			# Wait for this event before restarting the loop

		# Observer flags
		self._camera_opened= False
		self._first_trigger= False
		self._dl_complete= False
		self._loop_error= False
		self._exec_term= False
		self._terminated= False

		# Data
		self._expected_frames= []
		self._triggers: List[TriggerData]= []
		self._frames: List[FrameData]= []

		# Execution
		self._start_loop= threading.Event()

		# Mode
		self._mode = CameraMode.INIT

	def _log(self, msg):
		text= f'{self._id} (mode: {self._mode}) >> {msg}'
		if self._log_color is not None:
			text= self._log_color + color_delimiter + text
		return text

	def announce(self):
		self.m_logger.info(self._log('Ready'))

	def _trigger_detected_callback(self, feature):
		"""
		Callback to the camera's Vimba feature: EventLine1RisingEdgeFrameID.
		This feature is written every time a trigger is detected by the camera.
		"""
		if self._listen_to_triggers:
			trigger_data= TriggerData(
				num=	len(self._triggers) + 1,
				cam_ts=	self._trigger_timestamp_feature.get(),
				pc_ts= 	helper.timestampNow()
			)
			self._triggers.append(trigger_data)
			self.m_logger.info(self._log(f'Trigger detected: {trigger_data}'))

			frame_id= self._trigger_frame_id_feature.get()
			if frame_id == 0 or frame_id in self._expected_frames:
				frame_id += 1
			if frame_id not in self._expected_frames:
				self._expected_frames.append(frame_id)

			# Set first trigger flag
			self._first_trigger= True
		else:
			self.m_logger.warning(self._log('Trigger detected outside trigger listening window: discarded'))

	def _frame_received_callback(self, camera: vimba.Camera, frame: vimba.Frame):
		"""
		Frame receiving callback.
		Called when the camera is streaming.
		"""
		if self._listen_to_frames:
			frame_id= frame.get_id()
			
			if frame.get_buffer_size() == self._expected_frame_size:
				frame_data= FrameData(
					id= 		frame_id,
					cam_ts= 	frame.get_timestamp(),
					img_size= 	frame.get_buffer_size(),
					img= 		frame.get_buffer()
				)
				self._frames.append(frame_data)
				self.m_logger.info(self._log(f'Frame downloaded: {repr(frame_data)}'))
			else:
				self.m_logger.info(self._log(f'Received frame with wrong size: {frame.get_buffer_size()}'))
			
			if frame_id in self._expected_frames:
				self._expected_frames.remove(frame_id)
				if len(self._expected_frames) == 0:
					self._dl_complete= True
			
			camera.queue_frame(frame)
		else:
			self.m_logger.warning(self._log('Frame received otside frame listening window: discarded'))

	def run(self):
		"""
		The main body of the camera thread, executing its pipeline:
		1. Open camera connection with Vimba API
			(by default, retry 3 times if the opening fails)
		2. Setup camera
		3. Wait for the start signal
		4. Loop:
			a. Open streaming and register triggers
			b. Turn StreamHoldEnable off and download frames
			c. Turn StreamHoldEnable on, stop streaming, and wait for delivery completion
			d. Reset all variables and cycle
		"""
		self._mode = CameraMode.WAIT
		self.m_logger.info(self._log('Starting thread execution'))
		retries= 3
		while retries > 0:
			retries -= 1
			try:
				with vimba.Vimba.get_instance():
					with self._camera as camera:
						# Setup
						cam_ip= camera.get_feature_by_name('GevCurrentIPAddress').get()
						self.cam_ip= helper.ip_int_to_str(cam_ip, vimba_std=True)

						self._camera_opened= True
						self._camera_open_attempt.set()

						if helper.file_is_readable(self._xml_file):
							try:
								camera.load_settings(self._xml_file, PersistType.All)
								self.m_logger.info(self._log(f'Loaded settings: {self._xml_file}'))
							except Exception as e:
								self.m_logger.error(self._log(f'Cannot load settings from file ({type(e)}): {e}'))
						else:
							self.m_logger.warning(self._log('Caution! Cannot read the xml configuration file. Keeping the current configuration.'))

						camera.GVSPAdjustPacketSize.run()
						while not camera.GVSPAdjustPacketSize.is_done():
							pass

						self._event_selector_feature= camera.get_feature_by_name('EventSelector')
						self._event_notification_feature= camera.get_feature_by_name('EventNotification')
						self._event_selector_feature.set('Line1RisingEdge')
						self._event_notification_feature.set('On')

						self._trigger_frame_id_feature= camera.get_feature_by_name('EventLine1RisingEdgeFrameID')
						self._trigger_timestamp_feature= camera.get_feature_by_name('EventLine1RisingEdgeTimestamp')
						self._trigger_frame_id_feature.register_change_handler(self._trigger_detected_callback)				

						frame_height= camera.get_feature_by_name('Height').get()
						frame_width= camera.get_feature_by_name('Width').get()
						self._expected_frame_size= frame_height * frame_width

						self._stream_rate_constraint_feature= camera.get_feature_by_name('StreamFrameRateConstrain')
						self._stream_rate_constraint_feature.set(False)

						self._hold_stream_feature= camera.get_feature_by_name('StreamHoldEnable')

						#settings_file_name= f'{self.cam_id}_settings.xml'
						#camera.save_settings(f'{settings_file_name}', PersistType.All)

						# Wait for the initial start loop event (just once)
						self._start_loop.wait()

						self._mode = CameraMode.STARTED

						retries= 0

						# Camera loop
						while not self._exec_term:
							# Enable and start trigger listening
							self._listen_to_triggers= True
							
							try:
								# Set StremHold to On to make the camera holding the frames in the internal buffer,
								# then start streaming to allow Vimba registering triggers and frames
								self._hold_stream_feature.set('On')
								camera.start_streaming(handler=self._frame_received_callback, buffer_count=4)
								self._mode = CameraMode.HOLD
							except Exception as e:
								self.m_logger.error(self._log(f'Loop error while setting "hold mode" ({type(e)}): {e}'))
								self._loop_error= True
								self._listen_to_triggers= False

							if not self._loop_error:
								# Listen to triggers until stop
								if not self._reset.is_set():
									self.m_logger.info(self._log('Registering triggers'))
									self._stop_listening.wait()

								# Disable trigger listening
								self._listen_to_triggers= False
								
							if not self._loop_error:
								# Wait for the start download event
								if not self._reset.is_set():
									self.m_logger.info(self._log('Waiting for download permission'))
									self._start_download.wait()								

								if not self._reset.is_set():
									# Enable frames listening
									self._listen_to_frames= True

									self.m_logger.info(self._log('Downloading images'))
									try:
										# Set StreamHold to Off to let the camera transmit the frames
										self._hold_stream_feature.set('Off')
										self._mode= CameraMode.DL
									except Exception as e:
										self.m_logger.error(self._log(f'Loop error while setting "dl mode" ({type(e)}): {e}'))
										self._loop_error= True

									if not self._loop_error:
										# Wait for the stop download event
										self._stop_download.wait()

								# Disable frames listening
								self._listen_to_frames= False

								if not self._reset.is_set() and not self._loop_error:
									self.m_logger.info(self._log('Stop downloading: delivering data'))
							
							# The following part is always executed, even when a loop error occurs
							
							try:
								# Stop the streming to flush possible unregistered frames or events (also resets frame numbers)
								# Does nothing if streaming was never started
								camera.stop_streaming()
								self._hold_stream_feature.set('Off')
								self._mode= CameraMode.FLUSH
								self.m_logger.info(self._log('Flushing camera'))
							except Exception as e:
								self.m_logger.error(self._log(f'Error while flushing the camera ({type(e)}): {e}'))
								# Do not set loop error event since the loop is going to restart

							# Wait for the restart event 
							# (who sets the restart MUST also clear events, flags, and variables first)
							self._restart.wait()

							# Immediately clear restart event to avoid infinite loop
							self._restart.clear()

						# Exited from loop

						# Remove trigger callback
						self.m_logger.info(self._log('Removing trigger callback'))
						self._trigger_frame_id_feature.unregister_all_change_handlers()
			except vimba.VimbaCameraError as e:
				self.m_logger.info(self._log(f'Vimba camera error. Is the camera already opened by another process? {e}'))
			except vimba_c.VimbaCError as e:
				self.m_logger.info(self._log(f'Internal Vimba C error opening camera. Retry? {e}'))
			except Exception as e:
				self.m_logger.info(self._log(f'Unexpected error ({type(e)}): {e}'))
			finally:
				self._mode= CameraMode.CLOSED
				self._camera_opened= False
				if retries == 0:
					if not self._camera_open_attempt.is_set():
						self.m_logger.info(self._log('Failed to open the camera: terminating...'))
						self._camera_open_attempt.set()
				else:
					self.m_logger.info(self._log(f'{retries} attempts remaining to open the camera. Trying again in 3 seconds'))
					time.sleep(3)
		self._terminated= True
		self.m_logger.info(self._log('Terminated'))

	# Control execution

	def _unlock_until_restart(self):
		""" Unlock all events except for restart """
		self._start_loop.set()
		self._stop_listening.set()
		self._start_download.set()
		self._stop_download.set()

	def start_execution(self):
		self.m_logger.info(self._log('Starting execution'))

		self._start_loop.set()

	def reset_and_flush(self):
		self.m_logger.info(self._log('Resetting and flushing'))

		# Set reset event
		self._reset.set()

		self._unlock_until_restart()

	def restart_execution(self):
		self.m_logger.info(self._log('Restarting execution'))

		# Clear everything
		self._stop_listening.clear()
		self._start_download.clear()
		self._stop_download.clear()
		self._reset.clear()
		self._first_trigger= False
		self._dl_complete= False
		self._loop_error= False
		self._expected_frames= []
		self._triggers= []
		self._frames= []

		# Set restart event
		self._restart.set()

	def stop_execution(self):
		self.m_logger.info(self._log('Stopping execution'))

		# Set stop flag
		self._exec_term= True

		# Set execution events which could lead to a lock
		self._camera_open_attempt.set()

		# Start, reset and restart execution (unlock loop and observer)
		self.start_execution()
		self.reset_and_flush()
		self.restart_execution()

	# Observer checking methods

	def is_opened(self):
		self._camera_open_attempt.wait()
		if self._exec_term or self.is_terminated():
			return None
		return self._camera_opened

	def is_first_trigger(self):
		return self._first_trigger

	def is_dl_complete(self):
		return self._dl_complete

	def is_loop_error(self) -> bool:
		return self._loop_error

	def is_terminated(self) -> bool:
		return self._terminated

	# Interact with the camera loop

	def get_expected_frames(self) -> int:
		return len(self._expected_frames)

	def stop_listening(self):
		self._stop_listening.set()
	
	def start_download(self):
		self._start_download.set()

	def stop_download(self):
		self._stop_download.set()

	def get_data(self) -> CameraData:
		return CameraData(self.cam_id, self._triggers, self._frames)
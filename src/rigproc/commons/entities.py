from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from rigproc.commons.helper import helper


# CAMERA

class CameraShoot:
	""" Represents a single image captured by one camera. """
	def __init__(self, cam_id: str, cam_num: int, img_path: str) -> None:
		self.cam_id= cam_id
		self.cam_num= cam_num
		self.img_path= img_path
		self.copy_path= None
	
	def __repr__(self) -> str:
		return f'Cam {self.cam_num}: {self.img_path}'
	
	def set_copy_path(self, copy_path):
		self.copy_path= copy_path

class CameraShootArray:
	""" 
	Represents a set of images captured by multiple cameras at the same time.
	Corresponds to a "shoot event".
	"""
	def __init__(self, timestamp: str, shoots: List[CameraShoot], trans_id: str):
		self.timestamp= timestamp
		self.shoots= shoots
		self.trans_id= trans_id
	
	def __repr__(self) -> str:
		return f'Shoot array at {helper.timestamp_to_formatted(self.timestamp)}. Tr. id: {self.trans_id}. Shoots:\n' +\
			'\n'.join([repr(shoot) for shoot in self.shoots])

class CameraEvent:
	"""
	Represents more sequential sets of images captured by the cameras at different times.
	Corresponds to multiple shoot events.
	The "shoot events" in the same "camera event" happened within a time frame defined in the configuration file.
	Each shoot event correspond to a pantograph, all belonging to the same train.
	"""
	def __init__(self, pole: str, shoot_arrays: List[CameraShootArray]):
		self.pole= pole
		self.shoot_arrays= shoot_arrays
	
	def __repr__(self) -> str:
		return f'Event -> Pole {self.pole}. Shoot arrays:\n' +\
			'\n'.join([repr(shoot_array) for shoot_array in self.shoot_arrays])


# RECOVERY

class EventToRecover:
	""" 
	Represents a single shoot event to recover.
	Contains the json structures generated during the event's management.
	"""
	def __init__(
		self,
		shoot_array: CameraShootArray, 
		event_id: str, 
		remote_folder_name: str, 
		trig_json_model: str, 
		diag_json_model: str, 
		mosf_json_model: str
	) -> None:
		self.shoot_array= shoot_array
		self.event_id= event_id
		self.remote_folder_name= remote_folder_name
		self.trig_json_model= trig_json_model
		self.diag_json_model= diag_json_model
		self.mosf_json_model= mosf_json_model

		self.m_recovery_start: Optional[datetime]= None
		self.m_recovery_attempts= 0
	
	@property
	def timestamp(self):
		return self.shoot_array.timestamp
	
	def __eq__(self, other) -> bool:
		if isinstance(other, EventToRecover):
			return self.timestamp == other.timestamp
		else:
			return False
	
	def __gt__(self, other) -> bool:
		if isinstance(other, EventToRecover):
			try:
				if self.m_recovery_attempts == other.m_recovery_attempts:
					return int(self.timestamp) > int(other.timestamp)
				else:
					return self.m_recovery_attempts > other.m_recovery_attempts
			except:
				return False
		else:
			return False
	
	def __repr__(self) -> str:
		return 'Event to recover:\n' +\
			repr(self.shoot_array) +\
			f'\nID: {self.event_id}' +\
			f'\nRemote folder: {self.remote_folder_name}'

	def start_recovery(self):
		""" To call before a Recovery Flow """
		self.m_recovery_start= datetime.now()
		self.m_recovery_attempts += 1

	def get_recovery_start(self) -> datetime:
		if self.m_recovery_start is None:
			self.start_recovery()
		return self.m_recovery_start


# LOGGING

@dataclass
class LogFile:
	path: str
	ts: datetime
"""
A "flow" represents a sequence of operations logically related.
"""


from datetime import datetime
from queue import Queue
import logging
from enum import auto
from threading import Event, Thread, Timer
from typing import List, Callable, Optional

from rigproc.flow import eventtrigflow_buildcmd as buildcmd

from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons.helper import helper

from rigproc.params import internal


class Caller:
	"""
	Interface for an entity requiring operations that need an answer, for instance:
		- I/O operations;
		- Kafka operations.
	
	Methods
	-------
	- callback: called to delivery the answer;
	- missed: called when the answer is missed.
	"""
	_MISSED= auto()
	def __init__(self):
		self._answer= self._MISSED
	def callback(self, answer):
		self._answer= answer
	def missed(self):
		self._answer= self._MISSED


class FlowMsg:
	"""
	Internal flow message (e.g.: errors, warnings)

	Attributes
	----------
	info: message's content;
	task_num: number of the task executing when the message is delivered;
	task_name: name of the task executiong when the message is delivered;
	msg_type: message's type (uses a constant attribute of this class).

	Constant attributes
	-------------------
	MSG: message's generic type (not used);
	ERR: message's error type;
	WRN: message's warning type.
	"""
	MSG= 'Message'
	ERR= 'Error'
	WRN= 'Warning'
	def __init__(self, info, task_num, task_name, msg_type: str=None) -> None:
		self.info= info
		self.task_num= task_num
		self.task_name= task_name
		if msg_type is None:
			msg_type= self.MSG
		self.msg_type= msg_type
	def __repr__(self) -> str:
		return f'{self.msg_type} from task {self.task_num} ({self.task_name})' +\
			(f': {self.info}') if self.info is not None else ''


class Flow(Caller):
	"""
	Represents an operations flow.
	Needs to be extended by each specific flow.
	Implements the necessary attributes to be compatible with the old implementation EventTrigFlow.
	Control the execution by calling start, stop, pause, resume.
	Main features:
		- dedicated thread (non-blocking);
		- ability to loop through tasks;
		- pausing operations (I/O ops, Kafka msgs...) and answers management;
		- timers (wait some time before going on).
	"""
	def __init__(self, flow_type: str, core, request_id=None):
		self.m_logger= logging.getLogger('root')
		self.m_flow_logger= logging.getLogger('flow')

		self.m_flow_type= flow_type
		self.m_command_queue: Queue= core['cmd_q']

		self.m_internal_thread= Thread(target=self._loop, name='flow')

		self.m_started= False
		self.m_unlock= Event()	# Allows the Flow thread to loop
		self.m_stop= Event()	# If set, terminates the execution (cannot resume)
		
		self.m_tasks: List[Callable]= []	# List of all the task (methods) in the flow. Each Flow extension implements its own task list.
		self.m_current_task= 0
		self.m_loop_counter= None

		self.m_errors= []
		self.m_warnings= []

		self.m_stop_on_error= False

		super().__init__()
		self.m_flow_logger.debug(f'Flow created: {flow_type}')

		# Compatibility
		self.m_timestamp= helper.timestampNow()
		self.m_uuid= helper.new_trans_id()
		self.m_id= f'{self.m_timestamp}_{get_config().main.implant_data.nome_ivip.get()}'
		self.m_creation_time= helper.timeNowObj()
		self.m_flow_id= f'{self.m_creation_time}_{self.m_flow_type}_{self.m_uuid}'
		self.m_request_id= request_id
		if request_id is not None:
			self.m_flow_id += f'_{request_id}'

	def _loop(self):
		""" Flow thread target. """
		while not self.m_stop.is_set():
			# Wait for the unlock event 
			# (set by start, stop and resume, cleared by pause)
			self.m_unlock.wait()

			if self.m_stop.is_set():
				break

			if self.m_current_task >= len(self.m_tasks):
				self.m_flow_logger.critical('Internal error! The task counter exceded the number of tasks. Terminating flow...')
				self.stop()
				break

			self.m_flow_logger.debug(
				f'Flow {self.m_flow_type}: task {self.m_current_task} -> {self.m_tasks[self.m_current_task].__name__}' +\
					(f' (loop {self.m_loop_counter})' if self.m_loop_counter is not None else '')
			)

			task= self.m_tasks[self.m_current_task]

			# Call the next task.
			# Distiniguish the case when the task is one of my methods,
			# or a method from another Flow extension.
			try:
				my_class= self.__class__.__name__
				task_class= task.__qualname__.split('.')[0]
				if my_class == task_class:
					task()
				else:
					task(self)
			except Exception as e:
				self.m_logger.critical(
					f'Task {self.m_current_task} crashed, stopping flow ({type(e)}): {e}'
				)
				self.stop()
				break
			
			# Reset answer to avoid overlaps
			self._answer= self._MISSED

			if self.m_stop_on_error and len(self.m_errors) > 0:
				self.stop()
		
		if self.m_stop.is_set():
			l_term_msg= f'Flow {self.m_flow_type} terminated.'
			try:
				if len(self.m_errors) > 0:
					l_term_msg += '\n' + '\n'.join([repr(err) for err in self.m_errors])
				if len(self.m_warnings) > 0:
					l_term_msg += '\n' + '\n'.join([repr(wrn) for wrn in self.m_warnings])
			except:
				l_term_msg += ' Errors were encountered.'
			self.m_flow_logger.info(l_term_msg)

	def _close_pipe(self):
		""" Default task to terminate flows. """
		self.m_command_queue.put(buildcmd._buildActionResumePeriodic())
		self.m_command_queue.put(buildcmd._buildCmdPipeEnded(self))
		self.stop()

	def _get_current_task(self):
		return self.m_current_task

	def _step(self):
		""" Go to next task """
		if self.m_current_task < (len(self.m_tasks) + 1):
			self.m_current_task += 1
		else:
			self.m_flow_logger.critical('Cannot step to next task')

	def _jump(self, task_index):
		""" Go to specific task (for looping through tasks) """
		if task_index < len(self.m_tasks):
			if self.m_loop_counter is None:
				self.m_flow_logger.warning(f'Flow {self.m_flow_type} jumped without having started a loop')
				self._start_looping()
			else:
				self.m_loop_counter += 1
				self.m_flow_logger.debug(f'Looping (counter = {self.m_loop_counter})')
			self.m_current_task= task_index
		else:
			self.m_flow_logger.critical(f'Cannot jump to task {task_index}: trying to step to next task instead')
			self._stop_looping()
			self._step()

	def _start_looping(self):
		""" Function to call before entering a task loop block """
		self.m_loop_counter= 0

	def _stop_looping(self):
		""" Function to call after terminating a loop """
		self.m_flow_logger.debug('Stop looping')
		self.m_loop_counter= None

	def start(self):
		""" Start Flow dedicated thread """
		self.m_flow_logger.info(f'Flow started: {self.m_flow_type}')
		self.m_started= True
		get_redisI().startFlow(self.m_id, self.m_flow_type)
		self.m_unlock.set()
		self.m_internal_thread.start()

	def stop(self):
		""" Stop Flow thread (cannot resume) """
		self.m_flow_logger.debug(f'Flow {self.m_flow_type} stopped')
		if self.m_started:
			get_redisI().stopFlow(self.m_id, len(self.m_errors) > 0)
		self.m_stop.set()
		self.m_unlock.set() # Allows to unlock the flow from a pause state

	def pause(self):
		""" Pause Flow execution (can resume) """
		self.m_flow_logger.debug(f'Flow {self.m_flow_type} paused')
		self.m_unlock.clear()

	def resume(self):
		""" Resume Flow execution """
		self.m_flow_logger.debug(f'Flow {self.m_flow_type} resumed')
		self.m_unlock.set()

	def _sleep(self, interval):
		""" Wait some seconds (interval) (block execution) """
		self.pause()
		timer= Timer(interval, self.callback, args=['timeout'])
		timer.setName('flow_t')
		timer.start()
		self.m_flow_logger.debug(f'Timer set: the flow will resume in {interval} seconds')

	def _error(self, info: Optional[str]= None):
		""" Register Flow error message """
		self.m_errors.append(FlowMsg(
			info, 
			self.m_current_task, 
			self.m_tasks[self.m_current_task].__name__,
			msg_type=FlowMsg.ERR
		))

	def _warning(self, info: Optional[str]= None):
		""" Register Flow warning message """
		self.m_warnings.append(FlowMsg(
			info, 
			self.m_current_task, 
			self.m_tasks[self.m_current_task].__name__,
			msg_type=FlowMsg.WRN
		))

	def is_done(self):
		""" Return True if the Flow has finished (False if the Flow is executing or is paused) """
		return self.m_stop.is_set()

	def is_waiting(self):
		""" Return True if the Flow is paused """
		return not self.m_unlock.is_set()

	def callback(self, answer):
		""" Deliver answer """
		super().callback(answer)
		self.m_flow_logger.debug(f'Flow {self.m_flow_type} > answer received: {helper.prettify(answer)}')
		self.resume()

	def missed(self):
		""" Report missed answer """
		super().missed()
		self.m_flow_logger.debug(f'Flow {self.m_flow_type} > missed answer')
		self.resume()

	def get_errors(self):
		return self.m_errors

	# Compatibility

	def _get_data_dict(self):
		""" Generate Flow internal data dict (compatibility with old implementation) """
		data_dict= {
			internal.flow_data.id: self.m_id,
			internal.flow_data.uuid: self.m_uuid,
			internal.flow_data.date: helper.timestamp_to_date(self.m_timestamp),
			internal.flow_data.time: helper.timestamp_to_time(self.m_timestamp),
			internal.flow_data.float_timestamp: self.m_timestamp,
		}
		return data_dict

	def parseAnswer(self, key, data):
		self.callback(data)

	def gotMissedAnswerContinue(self):
		self.missed()

	def isDone(self) -> bool:
		return self.is_done()

	def stopOnError(self):
		self.m_stop_on_error= True

	def getCreationTime(self) -> datetime:
		return self.m_creation_time

	# Compatibility (recovery)

	def hasErrors(self) -> bool:
		return len(self.get_errors()) > 0

	def hasCriticalErrors(self) -> bool:
		return len(self.get_errors()) > 0

	def getAdvancement(self) -> float:
		if len(self.m_tasks) != 0:
			return self.m_current_task / len(self.m_tasks) * 100
		else:
			return 100

	# Compatibility (flow on Redis)

	def getFlowId(self):
		return self.m_flow_id

	def getRequestId(self):
		return self.m_request_id

	


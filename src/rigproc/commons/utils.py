from threading import Event, Thread
import logging
import threading

from typing import Callable, List, Optional


class RecursiveTimer():
	"""
	Executes some operations recursively at a specific time interval
	
	Starts 2 threads: one is the timer, one the executer
	
	The timer sleeps for the interval time, triggers the executer, then cycle
	
	The executer executes some functions sequentially, waits for the timer's trigger, then cycles
	"""

	def __init__(
		self, 
		interval: int, 
		functions: List[Callable], 
		name: str= ''
	):
		self.m_logger= logging.getLogger('root')
		self.interval= interval
		self.functions= functions
		self.name= name
		self.finished= Event()
		self.trigger= Event()
		self.timer_thread: Thread= None
		self.exec_thread: Thread= None

	def start(self):
		""" Create the timer and the executer threads and start them """

		# Timer thread: it will recursively sleep for a specific time interval and then trigger the execution thread
		self.timer_thread= Thread(target=self._timer, name=f'tmr_{self.interval}')

		# Execution thread: it will recursively execute some functions, then wait for the signal from the timer
		self.exec_thread= Thread(target=self._execute, name=f'exe_{self.interval}')

		self.timer_thread.start()
		self.exec_thread.start()

	def cancel(self):
		""" Set the finish event, which stops the timer and the executer """
		self.finished.set()

	def wait(self):
		""" Join the timer and the executer threads """
		if isinstance(self.timer_thread, Thread):
			self.timer_thread.join()
		if isinstance(self.exec_thread, Thread):
			self.exec_thread.join()
		
	def _timer(self):
		while not self.finished.is_set():
			self.finished.wait(self.interval)

			# Trigger the executer even if the finish event is set, so the executer stops waiting
			self.trigger.set()

	def _execute(self):
		while not self.finished.is_set():
			self.trigger.clear()
			self.m_logger.debug(f'Recursive timer (' + (f'timer: {self.name}, ' if self.name != '' else '') + f'interval: {self.interval}) executing')
			
			for function in self.functions:
				
				# Stop the execution, even in the middle of the functions list, if the finish event is set
				if self.finished.is_set():
					break
				
				# Function dict also providing args
				if isinstance(function, (tuple, list)):
					try:
						fun= function[0]
						args= function[1:]
						exit= fun(*args)
					except Exception as e:
						self.m_logger.error(f'Recursive timer error: cannot execute {fun} with args {args}: {e}')
				
				# Simple function with no args
				elif callable(function):
					exit= function()
				
				else:
					self.m_logger.error(f'Recursive timer error: {function} is not a valid function')
			
			self.trigger.wait()


class ExecutionDelayer():
	"""
	Execute some functions with the relative arguments after a threading Event
	is set.
	If the abort event is set, skip execution.
	Does this in a separate thread not to block the caller execution.
	"""

	def __init__(
		self, 
		delayer: threading.Event,
		functions: List[Callable], 
		name=str,
		abort: Optional[threading.Event]=None
	) -> None:
		self.m_logger= logging.getLogger('root')
		self.name= name
		self.delayer= delayer
		self.functions= functions
		self.abort= abort

		self.done= False

		self.exec_thread= threading.Thread(
			target=self._delay_and_execute,
			daemon=True
		)

	def start(self):
		self.exec_thread.start()

	def _delay_and_execute(self):
		self.delayer.wait()

		if isinstance(self.abort, threading.Event):
			if self.abort.is_set():
				return

		self.m_logger.info(f'ExecutionDelayer "{self.name}": executing...')

		for function in self.functions:
			# Function dict also providing args
			if isinstance(function, (tuple, list)):
				try:
					fun= function[0]
					args= function[1:]
					exit= fun(*args)
				except Exception as e:
					self.m_logger.error(f'Execution delayer error: cannot execute {fun} with args {args}: {e}')
			
			# Simple function with no args
			elif callable(function):
				exit= function()
			
			else:
				self.m_logger.error(f'Execution delayer error: {function} is not a valid function')
		
		self.done= True
from threading import Event
import os
from typing import List, Optional

from rigproc.params import cli


def clear_console():
	# for windows
	if os.name == 'nt':
		os.system('cls')
	# for mac and linux(here, os.name is 'posix')
	else:
		os.system('clear')


def translate_boolean(val: str, default: Optional[bool]=None) -> Optional[bool]:
	if isinstance(default, bool) and val == '':
		return default
	if val.lower() in ['y', 'yes', 's', 'si', 'sì', 'sí']:
		return True
	elif val.lower() in ['n', 'no']:
		return False
	else:
		return None


class Data:
	def __init__(self) -> None:
		pass


class Option:
	def __init__(self, text) -> None:
		self.text= text

	def get_text(self, index):
		return f' {cli.color.forw_green}{index:>3d}{cli.color.regular} {self.text}'

	def trigger(self, data: Data):
		input('Premi invio per tornare indietro')


class Category:
	def __init__(self, text) -> None:
		self.text= text
	def get_text(self, text_length=1):
		if len(self.text) < text_length:
			return f'{cli.color.back_yellow} {self.text:>{text_length}s}{cli.color.regular}'
		else:
			return f'{cli.color.back_yellow} {self.text}{cli.color.regular}'


class Exit(Option):
	def __init__(self, exit_event: Event) -> None:
		self.exit_event= exit_event
		super().__init__('Esci')
	def trigger(self, data: Data):
		self.exit_event.set()


class Menu:
	def __init__(self, heading, entries: List[Option or Category]) -> None:
		self.heading= heading
		self.exit= Event()
		self.exit_opt= Exit(self.exit)
		self.entries= entries
		self.options: List[Option]= [entry for entry in entries if isinstance(entry, Option)] + [self.exit_opt]
		self.categories: List[Category]= [entry for entry in entries if isinstance(entry, Category)]
		if len(self.categories) > 0:
			self.max_cat_len= max([len(cat.text) for cat in self.categories])
		else:
			self.max_cat_len= 1
		self.data= Data()

	def update_heading(self):
		pass

	def preamble(self):
		pass

	def trigger_option(self, opt: Option):
		opt.trigger(self.data)

	def show(self):
		self.preamble()
		while not self.exit.is_set():
			clear_console()
			print(self.heading)
			print()

			# Entries
			for i, entry in enumerate(self.entries):
				if isinstance(entry, Option):
					print(entry.get_text(self.options.index(entry) + 1))
				elif isinstance(entry, Category):
					if i != 0:
						print()
					print(entry.get_text(self.max_cat_len))
				else:
					print(entry)

			# Exit
			print()
			print(self.exit_opt.get_text(self.options.index(self.exit_opt) + 1))

			# Selection
			selection= input('\nSeleziona un indice: ')
			try:
				opt_num= int(selection) - 1
				opt_sel= self.options[opt_num]
			except:
				input(f'Seleziona un indice in elenco: "{selection}" non è un\'opzione valida')
				continue
			self.trigger_option(opt_sel)
			self.update_heading()


class OneShotMenu(Menu):
	def trigger_option(self, opt: Option):
		super().trigger_option(opt)
		self.exit.set()
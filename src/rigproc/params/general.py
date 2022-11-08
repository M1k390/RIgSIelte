"""
General usage parameters (ok, ko, errors, default values, etc...)
"""

from enum import Enum, unique

# TODO

status_error= 'error'
status_ko= 'err'
status_ok= 'ok'
status_on= 'on'
status_off= 'off'
status_active= 'active'
status_inactive= 'inactive'

dato_errato= "invalid"
dato_non_disp= "not_available"


@unique
class pole(str, Enum):
	prrA= 'prrA'
	prrB= 'prrB'

@unique
class binario(str, Enum):
	pari= 'pari'
	dispari= 'dispari'


# TODO
@unique
class redis(str, Enum):
	error= dato_errato
	not_found= dato_non_disp


# TODO
@unique
class term_msg(str, Enum):
	exit= 'exit'
	reboot= 'reboot'


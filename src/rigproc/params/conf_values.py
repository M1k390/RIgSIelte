"""
Admitted values for specific configuration parameters
"""

from enum import Enum, unique


# TODO
@unique
class binario(str, Enum):
    doppio= 'binario_doppio'
    unico= 'binario_unico'


@unique
class prr(str, Enum):
    prrA= 'prrA'
    prrB= 'prrB'


# TODO
@unique
class module(str, Enum):
    fake= 'fake'
    deploy= 'deploy'


@unique
class log_formatter(str, Enum):
    color= 'color'
    alt= 'alt'
    custom= 'custom'
    

@unique
class log_file_mode(str, Enum):
    append= 'append'
    write= 'write'

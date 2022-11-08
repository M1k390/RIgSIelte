import logging

from rigproc import params
from rigproc.params import *
from rigproc.params import general

logging.info('Everything correctly imported')

def test_param_type():
	assert isinstance(general.status_ok, str)
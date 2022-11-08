import pytest

from rigproc.commons.wrappers import wrapkeys
from rigproc.commons import keywords

test_dict = {
	'key1': 'value1',
	'key2': {
		'key2-1': 'value2-1',
		'key2-2': 'value2-2'
	}
}

def test_getValue():
	assert wrapkeys.getValue(test_dict, 'key1') == 'value1' 			# vero
	assert wrapkeys.getValue(test_dict, 'key2', 'key2-1') == 'value2-1' # vero 2
	assert wrapkeys.getValue(test_dict, 'key3') != 'value3' 			# falso
	assert wrapkeys.getValue(test_dict, 'key2', 'key2-3') != 'value2-3' # falso 2

def test_getValueDefault():
	assert wrapkeys.getValueDefault(test_dict, 'default', 'key1') == 'value1' 				# vero
	assert wrapkeys.getValueDefault(test_dict, 'default', 'key3') == 'default' 				# falso
	assert wrapkeys.getValueDefault(test_dict, 'default', 'key2', 'key2-3') == 'default' 	# falso annidato
	assert wrapkeys.getValueDefault(test_dict, 'default', 'key4', 'key4-1') == 'default' 	# false annidato 2

def test_getValueError():
	assert wrapkeys.getValue(test_dict, 'key1') == 'value1' 			# vero
	assert wrapkeys.getValue(test_dict, 'key2', 'key2-1') == 'value2-1' # vero 2
	assert wrapkeys.getValue(test_dict, 'key3') != 'value3' 			# falso
	assert wrapkeys.getValue(test_dict, 'key2', 'key2-3') != 'value2-3' # falso 2
	assert wrapkeys.getValue(test_dict) == keywords.status_inactive 	# senza chiavi

def test_setValue():
	l_test_dict= test_dict.copy()
	wrapkeys.setValue(l_test_dict, 'new_value1', 'key1') 							# normale
	wrapkeys.setValue(l_test_dict, 'new_value2-1', 'key2', 'key2-1') 				# normale annidato
	wrapkeys.setValue(l_test_dict, 'new_value2-2-1', 'key2', 'key2-2', 'key2-2-1') 	# sovrascrivi
	wrapkeys.setValue(l_test_dict, 'new_value3-1', 'key3', 'key3-1') 				# nuova
	wrapkeys.setValue(l_test_dict, 'new_value4', 'key4') 							# nuova
	assert l_test_dict['key1'] == 'new_value1'
	assert l_test_dict['key2']['key2-1'] == 'new_value2-1'
	assert l_test_dict['key2']['key2-2']['key2-2-1'] == 'new_value2-2-1'
	assert l_test_dict['key3']['key3-1'] == 'new_value3-1'
	assert l_test_dict['key4'] == 'new_value4'
	assert wrapkeys.setValue({}, None, 'key') # nuovo campo in dict vuoto

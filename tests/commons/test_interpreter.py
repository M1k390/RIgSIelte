import pytest

from rigproc.commons.interpreter import interpreter

def test_encode_camera_error():
    encoded_err = interpreter.encode_camera_error('id_001', True, 'generic_error')
    assert isinstance(encoded_err, str)

def test_decode_camera_error():
    encoded_err = interpreter.encode_camera_error('id_001', True, 'generic_error')
    decoded_err = interpreter.decode_camera_error(encoded_err)

    assert decoded_err is not None

    if decoded_err is not None:
        assert decoded_err.cam_id == 'id_001'
        assert decoded_err.running == True
        assert decoded_err.error_msg == 'generic_error'
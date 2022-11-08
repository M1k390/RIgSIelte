from argparse import ArgumentParser
import logging
from threading import Event, Thread
from serial import Serial, EIGHTBITS, PARITY_NONE, STOPBITS_TWO

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s ~ %(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def is_hex(s: str):
    try:
        int(s, base=16)
        return True
    except:
        return False


def listen_and_log(port: Serial, stop_event: Event):
    while not stop_event.is_set():
        try:
            incoming = port.readline()
        except Exception as e:
            logger.error(f'Error reading port ({type(e)}): {e}')
        if incoming:
            logger.info(f'Incoming msg: {[hex(b) for b in incoming]}')


def send_input(port: Serial, stop_event: Event):
    while not stop_event.is_set():
        msg = input('Msg to send:\n')
        parts = msg.split(' ')

        if msg.lower() == 'exit':
            logger.info('Exiting...')
            stop_event.set()
            continue

        # Hex list
        if all([is_hex(part) and int(part, base=16) < 256 for part in parts]):
            msg = bytearray([int(part, base=16) for part in parts])
        else:
            msg = bytes(msg, encoding='utf8')
        
        try:
            logger.info(f'Sending: {msg}')
            port.write(msg)
        except Exception as e:
            logger.error(f'Error writing to port ({type(e)}): {e}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-d', '--device', help='Device path', type=str)
    args = parser.parse_args()

    if args.device:
        device = args.device
    else:
        device = '/dev/ttyS0'

    port = Serial(
        port=device,
        baudrate=9600,
        bytesize=EIGHTBITS,
        parity=PARITY_NONE,
        stopbits=STOPBITS_TWO,
        timeout=2,
        xonxoff=False,
        rtscts=False, dsrdtr=False,
        exclusive=True
    )
    
    stop_event = Event()
    listen_thread = Thread(target=listen_and_log, args=[port, stop_event])
    write_thread = Thread(target=send_input, args=[port, stop_event])
    listen_thread.start()
    write_thread.start()
    listen_thread.join()
    write_thread.join()

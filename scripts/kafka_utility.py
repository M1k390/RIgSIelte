from multiprocessing import Event
from threading import Thread
from typing import List, Optional
from confluent_kafka import Consumer, Producer

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s ~ %(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class KafkaBroker:
    def __init__(self, url: str, group: str, encoding='utf-8') -> None:
        self.url = url
        self.group = group
        self.encoding = encoding
        self.topics: List[str] = []
        self.listening = False
        self.listen_thread = Optional[Thread]

    def _listen(self):
        kafka_consumer = Consumer({
            'bootstrap.servers': self.url,
            'group.id': self.group,
            'auto.offset.reset': 'earliest'
        })
        kafka_consumer.subscribe(self.topics)
        try:
            while self.listening:
                msg = kafka_consumer.poll(1)
                if msg is None:
                    continue
                if msg.error():
                    logger.error(f'Kafka consumer error: {msg.error()}')
                msg_decoded = msg.value().decode(self.encoding)
                topic = msg.topic()
                logger.info(f'Topic "{topic}": {msg}')
        except Exception as e:
            logger.info(f'Stopped listening for error {type(e)}: {e}')
            self.listening = False

    def start_listening(self, topics: List[str]):
        self.topics = topics
        self.listening = True
        self.listen_thread = Thread(target=self._listen)
        self.listen_thread.start()

    def stop_listening(self):
        self.listening = False
        if isinstance(self.listen_thread, Thread):
            self.listen_thread.join()


def listen_main():
    url = '192.168.2.101:9092'
    group = 'group'
    topics = [
        'DiagnosiSistemiIVIP_STGtoRIP',
        'AggiornamentoSW_STGtoRIP',
        'AggiornamentoImpostazioni_STGtoRIP',
        'AggiornamentoFinestraInizioTratta_STGtoRIP'
    ]

    kafka_broker = KafkaBroker(url, group)
    kafka_broker.start_listening(topics)

    end_event = Event()

    try:
        end_event.wait()
    except:
        kafka_broker.stop_listening()


if __name__ == '__main__':
    listen_main()

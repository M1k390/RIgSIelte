#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
processo gestione end point di comunicazione verso STG

"""

import queue
import logging
import threading
import time
import json
from confluent_kafka import Consumer, Producer

from rigproc.commons import keywords
from rigproc.commons.wrappers import wrapkeys
from rigproc.commons.helper import helper
from rigproc.params import general, internal
from rigproc.commons.config import get_config
from rigproc.commons.redisi import get_redisI
from rigproc.commons.logger import logging_manager


class BrokerInterface():
    def is_ok(self) -> bool:
        return False

    def close(self):
        pass

    def wait(self):
        pass


class FakeBroker(BrokerInterface):
    def __init__(self, p_in_queue: queue.Queue, p_out_queue: queue.Queue) -> None:
        super().__init__()

        # Use the normal Kafka logger, but use "FAKE" as a prefix, formatting logs
        # with self._log
        self.m_logger= logging_manager.generate_logger(
            logger_name='kafka',
            format_code=get_config().logging.kafka.format.get(),
            console_level=get_config().logging.kafka.console_level.get(),
            file_level=get_config().logging.kafka.file_level.get(),
            log_file_name=get_config().logging.kafka.file_name.get(),
            log_file_dir=get_config().logging.kafka.file_dir.get(),
            log_file_mode=get_config().logging.kafka.file_mode.get(),
            root_log_file_prefix=get_config().logging.root.file_name.get() \
                if get_config().logging.kafka.log_to_root.get() else None,
            root_log_dir=get_config().logging.root.file_dir.get() \
                if get_config().logging.kafka.log_to_root.get() else None,
            formatter_setting=get_config().logging.kafka.formatter.get()
        )

        self.m_in_queue = p_in_queue
        self.m_out_queue = p_out_queue
        
        self.m_stop = False

        # Start the thread now
        self.m_thread = threading.Thread(
            target=self._manage_outgoing_messages,
            name='ManageOutgoingMsgs',
            daemon=True
        )
        self.m_thread.start()

    def is_ok(self):
        return True

    def close(self):
        self.m_logger.info(self._log('Closing fake broker...'))
        self.m_stop = True

    def wait(self):
        self.m_thread.join()

    def _log(self, msg: str):
        return f'FAKE ~ {msg}'

    def _manage_outgoing_messages(self):
        self.m_logger.info(self._log('Fake broker start managing outgoing messages'))

        while not self.m_stop:
            try:
                l_cmd = self.m_in_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue
            if not l_cmd:
                continue
            self.m_logger.info(self._log(f'Broker command from mainprocess: {l_cmd}'))
            try:
                self.m_out_queue.put({
                    internal.cmd_key.cmd_type: internal.cmd_type.topic_response,
                    internal.cmd_key.trigflow_instance: l_cmd['trigflow_instance'],
                    internal.cmd_key.topic: l_cmd['topic'],
                    internal.cmd_key.topic_response: general.status_ok
                })
                self.m_logger.info(self._log('Automatic answer: OK'))
            except Exception as e:
                self.m_logger.error(self._log(
                    f'Error sending automatic broker response ({type(e)}): {e}'
                ))    


class KafkaBroker(BrokerInterface):
    """
    Broker comunicazione con il centro.
    Iscritto ai relativi topic.
    Traduce le richieste in eventi redis per condividere le azioni
    con questa app
    """
        
    def __init__(self, p_inQ, p_outQ):
        """
        
        Parameters
        ----------
        p_config : json string
            Configurazione json del modulo broker
            
        p_inQ : queue
            Coda condivisa per ricevere i comandi dal main proc
        
        p_outQ : queue
            Coda condivisa dove inviare comandi al main proc
        
        p_evtHnd : evt handler
            main evt handler
        
        p_identity: dict
            L'identità di questo impianto ( nome, tratta...)
        """

        super().__init__()
        
        self.m_config= get_config().broker
        self.m_logger= logging_manager.generate_logger(
            logger_name='kafka',
            format_code=get_config().logging.kafka.format.get(),
            console_level=get_config().logging.kafka.console_level.get(),
            file_level=get_config().logging.kafka.file_level.get(),
            log_file_name=get_config().logging.kafka.file_name.get(),
            log_file_dir=get_config().logging.kafka.file_dir.get(),
            log_file_mode=get_config().logging.kafka.file_mode.get(),
            root_log_file_prefix=get_config().logging.root.file_name.get() \
                if get_config().logging.kafka.log_to_root.get() else None,
            root_log_dir=get_config().logging.root.file_dir.get() \
                if get_config().logging.kafka.log_to_root.get() else None,
            formatter_setting=get_config().logging.kafka.formatter.get()
        )
        self.m_inQ= p_inQ
        self.m_outQ= p_outQ
        self.m_redisI= get_redisI()
        self.m_stop= False
        self.m_ok= True
        self.m_processedCmd= []
        self.m_currentCmd= {}
        self.m_answeredTopic= {}
        self.m_cmdDelivered= False
        self.m_listen= threading.Thread(
            target= self._listenTo,
            name= 'ListenToTopics',
            daemon= True
        )
        self.m_listen.start()
        self.m_cmds= threading.Thread(
            target= self._listenCmds,                                     
            name= 'TalkToTopics',
            daemon= True
        )
        self.m_cmds.start()                        
        
    def is_ok(self):
        return self.m_ok

    def close(self):
        self.m_logger.info("close requested")
        self.m_stop= True

    def wait(self):
        self.m_listen.join()
        self.m_cmds.join()
                
    """ LISTEN TO MAIN REQ + PRODUCER """ 
        
    def _listenCmds(self):
        """
        Thread ricezione comandi dal main proc
        esempio di msg dal main:
            l_toComm={
                    'topic': 'evt_trigger',
                    'json': l_event_model_json
                    }
        """
        self.m_logger.info("Broker listen to main proc cmd starting")
        self.m_txcompleted={}
        l_broker= self.m_config.produce.broker.get()
        self.m_producer = Producer({'bootstrap.servers': l_broker})        
        self.m_logger.info("Producer on [address]: " + l_broker)
        while not self.m_stop and self.m_ok:            
            try:
                l_cmd= self.m_inQ.get(block= True, timeout= 1.0)
                self.m_currentCmd= l_cmd
            except queue.Empty:
                continue
            " cmd processing "
            if not l_cmd:
                continue
            self.m_logger.info("Broker msg from main proc [topic]: " + wrapkeys.getValue(l_cmd, internal.cmd_key.topic))
            " producing topic "
            if internal.cmd_key.topic in l_cmd.keys():
                self.m_processedCmd.append(l_cmd)
                self._produceEvtJson(l_cmd)
        self.m_logger.info("Terminating broker thread listening to commands...")

    def _produceEvtJson(self, p_what):
        """
        Topic producer
        Riceve un dict con:
            topic
            json
        Invio e verifica:
            l'invio è asincrono
            Poll e flush triggerano l'invio e la generazione del delivery report
            Non controllo che il msg inviato sia relativo ad un pacchetto particolare
            ma attendo con un timeout che il flush sia andato a buon fine.
            Così facendo lavoro un pacchetto alla volta in maniera chiusa.
            Ritorno un dict con i dati del mittente, il msg e lo status di invio
        """
        def delivery_report(err, msg):
            """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
            self.m_cmdDelivered= True
            if err is not None:
                self.m_logger.error('Message delivery failed: {}'.format(err))
            else:
                self.m_logger.info('Message delivered to ' +
                                   msg.topic())
                self.m_txcompleted['status']=keywords.status_ok
                self.m_answeredTopic[internal.cmd_key.topic_response]= keywords.status_ok

        # Trigger any available delivery report callbacks from previous produce() calls
        self.m_producer.poll(0)
        # Dict per il main, preparazione
        self.m_cmdDelivered= False
        self.m_answeredTopic={}
        self.m_answeredTopic[internal.cmd_key.cmd_type]= internal.cmd_type.topic_response
        self.m_answeredTopic[internal.cmd_key.trigflow_instance]= p_what['trigflow_instance']
        self.m_answeredTopic[internal.cmd_key.topic]= p_what['topic']
        self.m_txcompleted['status']=keywords.status_ko
        self.m_answeredTopic[internal.cmd_key.topic_response]= keywords.status_ko
        self.m_txcompleted= p_what
        self.m_logger.info('Producing [topic]: {}, [content]: \n{}'.format(p_what['topic'], p_what['json']))
        try:
            self.m_producer.produce(p_what['topic'],
                                p_what['json'].encode('utf-8'),
                                callback= delivery_report )
        except Exception as e:
            self.m_logger.error("Exception producing msg on topic {}".format(e))            
        self.m_logger.info("producing [topic]: " + p_what['topic']+ " wait callback")
        self.m_producer.flush(self.m_config.produce.timeout.get())
        # attesa report delivery
        l_cnt= 15
        while l_cnt > 0:
            time.sleep(0.1)
            l_cnt = l_cnt -1
            if self.m_cmdDelivered:
                break
        # ora metto il cmd in coda
        self.m_outQ.put(self.m_answeredTopic)
        self.m_logger.info("topic response to main proc cmd queue")

    """ CONSUMER  """
    
    def _listenTo(self):
        """
        topic consumer
        """
        self.m_logger.info("Broker listen to  topic  starting")        
        l_topics= []
        l_consumer= Consumer({
            'bootstrap.servers': self.m_config.consume.broker.get(),
            'group.id': self.m_config.consume.group.get(),
            'auto.offset.reset': 'earliest'
        })
        l_topics.extend(self.m_config.consume.topic_req.get())
        try:
            l_consumer.subscribe(l_topics)
        except Exception as e:
            self.m_logger.error(f'Error subscribing to consumer for topics: {l_topics} ({type(e)}): {e}. Closing...')
            self.m_ok = False
            return
        self.m_logger.info('Subscribed to '+ str(l_topics))
        # Polling topics
        while not self.m_stop and self.m_ok:
            l_msg= l_consumer.poll(1.0)
            if l_msg is None:
                continue
            if l_msg.error():
                self.m_logger.error("Consumer error: {}".format(l_msg.error()))
                continue
            # Ritorna dei bytes, quindi da decodificare
            l_msg_value_decoded= l_msg.value().decode('utf-8')
            l_topic_decoded= l_msg.topic()
            self.m_logger.info('Topic {}, message: {}'.format(l_topic_decoded, l_msg_value_decoded))
            # Processing topic ricevuti
            l_action_dict= self._parseIncomingMsgs(l_topic_decoded, l_msg_value_decoded)
            if l_action_dict == {}:
                continue
            l_action_type= wrapkeys.getValueDefault(l_action_dict, None, internal.cmd_key.action_type)
            if l_action_type is not None:
                self.m_logger.info('Action generated from incoming msg {}'.format(l_action_dict[internal.cmd_key.action_type]))
                # Inserisci la richiesta azione nella coda di output
                self.m_outQ.put(l_action_dict)
            else:
                self.m_logger.warning('Message has been received from Kafka but no action was generated')

        # close consumers
        l_consumer.close()
        self.m_logger.info("Terminating broker thread listening to Kafka...")

    def _parseIncomingMsgs(self, p_topic, p_msg) -> dict:
        """ Decodifica topic in arrivo, generazione azioni corrispondenti 
        Basta estrarre il transaction id e riproporlo al trig flow        
        """
        msg_dict={}
        try:
            msg_dict= json.loads(p_msg)
        except Exception as e:
            self.m_logger.error("Can't convert string to dict {}".format(e))
            return {}
        # Check destinatario
        # TODO parlare con soft strategy e gestire i parametri e le policies 'destinatario del topic'
        if not self._isItForMe(msg_dict):
            self.m_logger.warning('Last message from Kafka was not for me')
            return {}
        # Richiesta aggiornamento impostazioni
        elif p_topic == keywords.topic_int_set_upd_from_stg:
            out_dict= self._parseInternalSettingsRequest(msg_dict)
            return out_dict
        # Richiesta aggiornamento finestra temporale
        elif p_topic == keywords.topic_time_win_upd_from_stg:
            out_dict= self._parseTimeWinSettingsRequest(msg_dict)
            return out_dict
        # Richiesta aggiornamento sw
        elif p_topic == keywords.topic_sw_update_from_stg:
            out_dict= self._parseSwUpdateRequest(msg_dict)
            return out_dict
        else:
            self.m_logger.error(f'Unimplemented topic from Kafka: {p_topic}')
            return {}

    def _parseInternalSettingsRequest(self, p_msg) -> dict:
        """ Parsing richiesta aggiornamento impostazioni interne
        p_data: dict
            Msg da parsare
        """
        out_dict= {}
        out_dict[internal.cmd_key.cmd_type]= internal.cmd_type.action
        out_dict[internal.cmd_key.action_type]= keywords.action_int_set_upd_flow
        try:
            out_dict[internal.cmd_key.data]= {
                keywords.flin_trans_id: p_msg[keywords.stg_transaction_id],
                keywords.flin_id: p_msg[keywords.stg_id],
                keywords.flin_t_mosf_prrA: p_msg[keywords.stg_update_settings][keywords.stg_t_mosf_prrA],
                keywords.flin_t_mosf_prrB: p_msg[keywords.stg_update_settings][keywords.stg_t_mosf_prrB],
                keywords.flin_t_off_ivip_prrA: p_msg[keywords.stg_update_settings][keywords.stg_t_off_ivip_prrA],
                keywords.flin_t_off_ivip_prrB: p_msg[keywords.stg_update_settings][keywords.stg_t_off_ivip_prrB],
                keywords.flin_json_dict: p_msg
            }
        except KeyError as e:
            self.m_logger.error("Missing key from topic diagnosis {}".format(e))
            return {}
        return out_dict

    def _parseTimeWinSettingsRequest(self, p_msg) -> dict:
        """ Parsing richiesta aggiornamento finestra temporale
        p_data: dict
            Msg da parsare
        """
        out_dict = {
            internal.cmd_key.cmd_type: internal.cmd_type.action,
            internal.cmd_key.action_type: keywords.action_time_win_upd_flow
        }
        try:
            out_dict[internal.cmd_key.data]= {
                keywords.flin_trans_id: p_msg[keywords.stg_transaction_id],
                keywords.flin_id: p_msg[keywords.stg_id],
                keywords.flin_fin_temp_pic_pari: p_msg[keywords.stg_update_settings][keywords.stg_fin_temp_pic_pari],
                keywords.flin_fin_temp_pic_dispari: p_msg[keywords.stg_update_settings][keywords.stg_fin_temp_pic_dispari],
                keywords.flin_json_dict: p_msg
            }
        except KeyError as e:
            self.m_logger.error("Missing key from topic diagnosis {}".format(e))
            return {}
        return out_dict

    def _parseSwUpdateRequest(self, p_msg) -> dict:
        """ Parsing richiesta schedulazione sw update 
        p_data: dict
            Msg da parsare
        """
        # Preparazione comando d'usicta
        out_dict={}
        out_dict[internal.cmd_key.cmd_type]= internal.cmd_type.action
        out_dict[internal.cmd_key.action_type]= keywords.action_update_flow
        out_dict[internal.cmd_key.data]= {}
        # Scheduling data
        try:
            out_dict[internal.cmd_key.data]= {
                keywords.flin_trans_id: p_msg[keywords.stg_transaction_id],
                keywords.flin_id: p_msg[keywords.stg_id],
                keywords.flin_schedule_date: p_msg[keywords.stg_update_parameters][keywords.stg_update_date],
                keywords.flin_schedule_time: p_msg[keywords.stg_update_parameters][keywords.stg_update_time],
                keywords.flin_remote_update_path: p_msg[keywords.stg_update_parameters][keywords.stg_update_package],
                keywords.flin_update_version: p_msg[keywords.stg_update_parameters][keywords.stg_update_version],
                keywords.flin_json_dict: p_msg,
            }
        except KeyError as e:
            self.m_logger.error("Missing key from topic sw update {}".format(e))
            return {}
        return out_dict

    def _isItForMe(self, p_msg_dict)-> bool:
        """ check se il msg è per me """
        l_rip_name= get_config().main.implant_data.nome_rip.get()
        l_rip_of_interest= wrapkeys.getValueDefault(p_msg_dict, None, keywords.stg_rip_of_interest)
        if l_rip_of_interest is None:
            self.m_logger.error(f'Identity check error: there is no "{keywords.stg_rip_of_interest}" key in the request')
            return False
        if l_rip_name in l_rip_of_interest:
            return True
        else:
            return False

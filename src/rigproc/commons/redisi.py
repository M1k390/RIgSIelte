#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis wrapper.
The Redis wrapper for Rigproc is a singleton object that must be initialized when the program starts.
Two Redis instances are used by Rigproc:
    - cache: data is volatile and is lost at reboot;
    - persistent: data is kept across sessions.
"""

import logging
import json
from collections.abc import Iterable
import traceback
from typing import Callable, Optional, List, Mapping, Tuple, Union

from redis import StrictRedis
from redis.exceptions import ResponseError, DataError

from rigproc.commons.entities import CameraShoot, CameraShootArray, EventToRecover

from rigproc.commons.helper import helper
from rigproc.commons.wrappers import wrapkeys

from rigproc.commons import  keywords
from rigproc.params import general, redis_keys, bus, cli


# Value returned when a Redis error occurs
_REDIS_DEFAULT_VALUE = general.redis.error

# Other constants
_TEMP_HISTORY_LIMIT = 500


#
# REDIS MANAGER
#

class RedisManager:
    """
    Single Redis instance manager.
    Wraps the main operations on the Redis cache.
    """

    def __init__(self, p_instance_name, p_logger_name, p_host, p_port, p_encoding='utf8'):
        self.m_logger= logging.getLogger(p_logger_name)
        self.m_name= p_instance_name
        self.m_redisI= StrictRedis(p_host, p_port)
        self.m_encoding= p_encoding

    def ping(self) -> bool:
        """Verifies the connection with the Redis cache"""
        try:
            self.m_redisI.ping()
            return True
        except:
            return False

    def _redis_op(self, callable: Callable, args: list, default, decode: bool):
        """
        Executes an operation on the Redis cache and returns its result.

        Arguments
        ---------
        - callable: the Redis operation, e.g.: redis.set;
        - args: the operation's arguments;
        - defualt: a default value to return if the operation fails;
        - decode: if True, decode the result before returning it.
        """
        try:
            res= callable(*args)
            if res is None:
                return default
            elif decode:
                if isinstance(res, bytes):
                    res= res.decode(self.m_encoding)
                elif isinstance(res, (list, set)):
                    for i, m_val in enumerate(res):
                        if isinstance(m_val, bytes):
                            res[i]= m_val.decode(self.m_encoding)
                elif isinstance(res, dict):
                    for key, value in res.items():
                        if isinstance(value, bytes):
                            res[key]= value.decode(self.m_encoding)
            return res
        except KeyError as e:
            self.m_logger.error(f'Not enough arguments ({len(args)}) for the Redis operation {callable.__name__}: {e}')
        except TimeoutError as e:
            self.m_logger.error(f'Error connecting to Redis cache: {e}')
        except ResponseError as e:
            self.m_logger.error(f'Error reading Redis response: {e}')
        except DataError as e:
            self.m_logger.error(f'Error with arguments {args} of Redis operation {callable.__name__}: {e}')
        except Exception as e:
            self.m_logger.error(f'Unexpected Redis error: {e}\n{traceback.format_exc()}')
        return default

    def get(self, p_key, p_default=_REDIS_DEFAULT_VALUE, p_decode=True) -> str:
        """Returns the value stored at <p_key> (always a str). Returns a defualt value if the request fails."""
        self.m_logger.debug(f'Retriving data from Redis {self.m_name} at key "{p_key}"')
        return self._redis_op(self.m_redisI.get, [p_key], default=p_default, decode=p_decode)

    def set(self, p_key, p_value) -> str:
        """Stores a value at <p_key>. Returns "OK" or an error."""
        self.m_logger.debug(f'Redis {self.m_name}, key {p_key}. Setting value: {helper.prettify(p_value)}')
        return self._redis_op(self.m_redisI.set, [p_key, p_value], default=_REDIS_DEFAULT_VALUE, decode=True)
    
    def setex(self, p_key, p_time, p_value) -> str:
        """Sets a value at <p_key> with an expiration time. Returns "OK" or an error."""
        self.m_logger.debug(f'Redis {self.m_name}, key {p_key}, expiration time: {p_time} seconds. Inserting value: {helper.prettify(p_value)}')
        return self._redis_op(self.m_redisI.setex, [p_key, p_time, p_value], default=_REDIS_DEFAULT_VALUE, decode=True)

    def zrange(self, p_key, p_start, p_end) -> list:
        """Returns the specified range of elements in the sorted set stored at <p_key> or an error."""
        self.m_logger.debug(f'Getting values in range {p_start} - {p_end} at key "{p_key}" in Redis {self.m_name}')
        return self._redis_op(self.m_redisI.zrange, [p_key, p_start, p_end], default=_REDIS_DEFAULT_VALUE, decode=True)

    def zadd(self, p_key, p_mapping: Mapping[str, str]) -> int:
        """Adds all the specified members with the specified scores (p_mapping) to the sorted set stored at <p_key>.
        Returns the number of added elements or an error."""
        self.m_logger.debug(f'Redis {self.m_name}, key {p_key}. Zadding: {helper.prettify(p_mapping)}')
        return self._redis_op(self.m_redisI.zadd, [p_key, p_mapping], default=_REDIS_DEFAULT_VALUE, decode=True)

    def zcount(self, p_key, p_min, p_max) -> int:
        """Returns the number of elements in the specified set with key from min to max"""
        self.m_logger.debug(f'Redis {self.m_name}, key {p_key}. Zcount min: {p_min} max: {p_max}')
        return self._redis_op(self.m_redisI.zcount, [p_key, p_min, p_max], default=_REDIS_DEFAULT_VALUE, decode=True)

    def zpopmin(self, p_key, p_n) -> list:
        """Removes n elements with lowest keys from the specified set"""
        self.m_logger.debug(f'Redis {self.m_name}, key {p_key}. Zpopmin n={p_n}')
        return self._redis_op(self.m_redisI.zpopmin, [p_key, p_n], default=_REDIS_DEFAULT_VALUE, decode=True)

    def hkeys(self, p_hash) -> list:
        """Returns all field names in the hash stored at <p_key> or an error."""
        self.m_logger.debug(f'Retriving fields at hash key "{p_hash}" from Redis {self.m_name}')
        return self._redis_op(self.m_redisI.hkeys, [p_hash], default=_REDIS_DEFAULT_VALUE, decode=True)

    def hget(self, p_key, p_field, p_default=_REDIS_DEFAULT_VALUE, p_decode=True) -> str:
        """Returns the value associated with <p_field> in the hash stored at <p_key> or an error."""
        self.m_logger.debug(f'Retriving data from Redis {self.m_name} at hash key "{p_key}" and field "{p_field}"')
        return self._redis_op(self.m_redisI.hget, [p_key, p_field], default=p_default, decode=p_decode)

    def hset(self, p_key, p_field, p_value) -> int:
        """Sets <p_field> in the hash stored at <p_key> to <p_value>.
        Returns the numer of added fileds or an error."""
        self.m_logger.debug(f'Redis {self.m_name}, hash key "{p_key}", field "{p_field}". Setting value: {helper.prettify(p_value)}')
        return self._redis_op(self.m_redisI.hset, [p_key, p_field, p_value], default=_REDIS_DEFAULT_VALUE, decode=True)

    def hdel(self, p_key, p_field) -> int:
        """Removes the specified field from the hash stored at <p_key>.
        Returns the numer of removed fileds or an error."""
        self.m_logger.debug(f'Deleting hash-key from Redis {self.m_name} at hash key "{p_key}" and field "{p_field}"')
        return self._redis_op(self.m_redisI.hdel, [p_key, p_field], default=_REDIS_DEFAULT_VALUE, decode=True)

    def delete(self, *p_keys) -> int:
        """Removes the specified keys. A key is ignored if it does not exist.
        Returns the numer of removed keys or an error."""
        self.m_logger.debug(f'Removing from Redis {self.m_name} the following keys: {p_keys}')
        return self._redis_op(self.m_redisI.delete, [*p_keys], default=_REDIS_DEFAULT_VALUE, decode=True)
        
    def expire(self, p_key, p_time) -> bool:
        """Set a timeout on key. After the timeout has expired, the key will automatically be deleted.
        Return 1 if the timeout was set, 0 if the key does not exist, or an error."""
        self.m_logger.debug(f'Applying expiring timeout of {p_time} to key "{p_key}" in Redis {self.m_name}')
        return self._redis_op(self.m_redisI.expire, [p_key, p_time], default=_REDIS_DEFAULT_VALUE, decode=True)

    def scan_iter(self, p_match) -> Iterable:
        """Returns an iterator containing the keys matching <p_match> or an error."""
        self.m_logger.debug(f'Scan match iter on Redis {self.m_name}: {p_match}')
        return self._redis_op(self.m_redisI.scan_iter, [p_match], default=_REDIS_DEFAULT_VALUE, decode=True)

    def rename(self, p_src, p_dst) -> str:
        """Renames the key <p_src> to <p_dst>. Returns "OK" or an error."""
        self.m_logger.debug(f'Renaming "{p_src}" to "{p_dst}" in Redis {self.m_name}')
        return self._redis_op(self.m_redisI.rename, [p_src, p_dst], default=_REDIS_DEFAULT_VALUE, decode=True)

    def pubsub(self):
        """Returns an idle subscriber to the Redis cache."""
        self.m_logger.debug(f'Gnerating subscriber to Redis {self.m_name}')
        return _RedisSubscriber(self.m_redisI, self.m_encoding, self.m_logger)


class _RedisSubscriber:

    def __init__(self, p_redisI: StrictRedis, p_encoding, p_logger):
        self.m_redisI= p_redisI
        self.m_encoding= p_encoding
        self.m_logger= p_logger
        self.m_subscriber= self.m_redisI.pubsub()

    def psubscribe(self, *p_args, **p_kwargs):
        """Subscribe to one or more patterns.
        Call get_message to get the detected operations on Redis that match at least one pattern."""
        self.m_subscriber.psubscribe(*p_args, **p_kwargs)

    def get_message(self, p_timeout=0) -> Optional[dict]:
        """Returns None if no message was detected, or a dict.
        The dict's values are automatically decoded.
        
        Returned dict's keys
        --------------------
        - pattern: the matched pattern;
        - channel: the key involved, preceded by "__keyspace@0__:";
        - data: the operation performed (get, set...)."""
        l_msg= self.m_subscriber.get_message(timeout=p_timeout)
        if l_msg is None:
            return None
        try:
            for l_key in ['pattern', 'channel', 'data']:
                if isinstance(l_msg[l_key], bytes):
                    l_msg[l_key] = l_msg[l_key].decode(self.m_encoding)
        except Exception as e:
            self.m_logger.error(f'Error handling Redis subscriber response: {e}')
            return None
        return l_msg


#
# DUAL REDIS (CACHE + PERSISTENT)
#

class DualRedis(object):
    """
    Redis wrapper to access the two instances used by Rigproc: "cache" and "persistent".
    Wraps all the main operations on Redis.
    Rigproc should use the methods in this class instead of performing the operations directly on Redis.
    """
    
    def __init__(self, p_cache_host, p_cache_port, p_pers_host, p_pers_port):
        """
        Init cache and persistent
        """
        self.m_logger= logging.getLogger('root')
        self.m_initialized= True
        
        # Cache
        self.cache= RedisManager('cache', 'root', p_cache_host, p_cache_port)
        if not self.cache.ping():
            self.m_logger.error(f"Redis cache connection error to {p_cache_host}:{p_cache_port}")
            self.m_initialized= False
        self.m_logger.info(f"Redis cache on: {p_cache_host}:{p_cache_port}")
        
        # Persistent
        self.pers= RedisManager('pers', 'root', p_pers_host, p_pers_port)
        if not self.pers.ping():
            self.m_logger.error(f"Redis persistent connection error to {p_pers_host}:{p_pers_port}")
            self.m_initialized= False
        self.m_logger.info(f"Redis persistent on: {p_pers_host}:{p_pers_port}")
    
    def setProcError(self, p_proc, p_error):
        """
        Mette le keyword dello stato del processo in questione 
        come ko.

        Parameters
        ----------
        p_proc : string
            nome processo
        p_error : string
            messaggio di errore    
        """
        self.cache.set(p_proc, "ko")
        self.cache.set(p_proc + "_error_msg", p_error)

    
    # RIGCAM

    def send_setup_rigcam(self, setup_message) -> None:
        """Puts an encoded setup message for Rigcam in Redis."""
        # Clear Redis keys
        self.cache.delete(redis_keys.cam_startup.key)
        self.cache.delete(redis_keys.cam_crash.key)
        self.cache.set(redis_keys.cam_setup.key, setup_message)

    def subscribe_to_rigcam_messages(self) -> Optional[_RedisSubscriber]:
        """Returns a Redis subscriber to the incoming messages from Rigcam.
        Returns None if an error occurs."""
        try:
            l_sub= self.cache.pubsub()
            l_sub.psubscribe(
                f'__keyspace@0__:{redis_keys.cam_startup.key}', 
                f'__keyspace@0__:{redis_keys.cam_crash.key}', 
                f'__keyspace@0__:{redis_keys.cam_error.key_prefix}*', 
                f'__keyspace@0__:{redis_keys.cam_event.key_prefix}*'
            )
            return l_sub
        except Exception as e:
            self.m_logger.critical(f'Exception subscribing to Redis messages ({type(e)}): {e}')
            return None

    def send_new_session_ts(self, ts: str) -> None:
        """Puts the new session timestamp for Rigcam in Redis"""
        self.cache.set(redis_keys.cam_msgs.log_session_ts, ts)

    def send_exit_rigcam(self) -> None:
        """Puts an exit message for Rigcam in Redis."""
        self.cache.set(redis_keys.cam_msgs.exit, 1)

    def clear_shoot_counter(self) -> bool:
        return self.cache.set(redis_keys.cam_stats.shoot_count, 0) is True 

    def increment_shoot_counter(self, p_amount: int) -> Optional[int]:
        try:
            l_curr_amount = int(self.cache.get(redis_keys.cam_stats.shoot_count))
        except:
            self.m_logger.error(
                'Error retrieving shoot counter from Redis: resetting to zero.'
            )
            self.clear_shoot_counter()
            l_curr_amount = 0
        try:
            l_new_amount = l_curr_amount + p_amount
            if self.cache.set(redis_keys.cam_stats.shoot_count, l_new_amount) is True:
                return l_new_amount
            else:
                return None
        except Exception as e:
            self.m_logger.error(
                f'Error incrementing shoot counter by {p_amount} ({type(e)}): {e}'
            )
            return None

    def get_shoot_count(self) -> Optional[int]:
        try:
            return int(self.cache.get(redis_keys.cam_stats.shoot_count))
        except:
            return None
                

    # IMPLANT PARAMETERS

    def storeImplantData(self, p_data_dict) -> bool:
        """ 
        Cancellazione set precedente
        Memorizzazione dati configurazione impianto su cache        
        """
        l_ret= True
        if not isinstance(p_data_dict, dict):
            self.m_logger.error("Can't store implnat data, wrong data format!")
            self.pers.hset(keywords.conf_data_hash_key,keywords.conf_data_status_key,keywords.status_ko) 
        else:
            " Cancellazione set precedente "              
            l_res= self.pers.delete(keywords.conf_data_hash_key)
            if l_res == keywords.redis_error:
                self.m_logger.error(f"Can't delete previous implnat data. Returned: {l_res}")
            " salvataggio chiavi "
            for key, value in p_data_dict.items():
                l_res= self.pers.hset(keywords.conf_data_hash_key, key, value)
                if l_res == keywords.redis_error:
                    l_ret= False
                    self.m_logger.error(f"Error saving implant data key {key}. Returned: {l_res}")
        return l_ret

    def updateImplantParam(self, p_key, p_new_value) -> bool:
        """
        Aggiorna un singolo parametro di impianto in cache 
        Ritorna un booleano che indica l'esito dell'operazione
        p_key: chiave corrispondente al parametro in cache
        p_new_value: valore aggiornato per il parametro
        """
        l_res= self.pers.hset(keywords.conf_data_hash_key, p_key, p_new_value)
        return isinstance(l_res, int)

    def getImplantData(self) -> dict:
        """
        Ritorna un dict contentente tutti i parametri di impianto
        memorizzati nella cache di Redis
        """
        l_keys= self.pers.hkeys(keywords.conf_data_hash_key)
        l_data_dict= {}
        if isinstance(l_keys, list):
            for l_key in l_keys:
                l_data_dict[l_key]= self.pers.hget(
                    keywords.conf_data_hash_key,
                    l_key
                )
        else:
            self.m_logger.error(f'Errore nel recupero dei paramteri di impianto dalla cache di Redis: {l_keys}')
        return l_data_dict

    def getImplantParam(self, p_key, p_default=_REDIS_DEFAULT_VALUE) -> str:
        """
        Recupero informazioni dalla cache tramite HGET e i seguenti parametri:
            Hash: keywords.conf_data_hash_key ("implant_data")
            Key: p_key
        """
        return self.pers.hget(keywords.conf_data_hash_key, p_key, p_default=p_default)


    # I/O MESSAGES (MSG_SORTED)
 
    def storeMsgWithScore(self, p_msg_dict):
        """
        Salvo in cache il msg dall'io con il timestampt come score
        query con: zrangebyscore key 0 inf withscores
        oppure da python : zrange('msg', 0, -1, withscores= True)
        Devo adattare il dict allo zadd tramite conversione json
        
        Parameters
        ----------
        p_msg_dict : dizionario con i dati decodificati del msg
        
        Returns : None        
        """
        " Check delle chiavi non serializzabili nel dict"
        p_good_dict= helper._removeNotJasonable(p_msg_dict)
        p_good_dict= {
            'timestamp': helper.timestampNowFormatted(),
            **p_good_dict
        }
        try:
            l_msg_json= json.dumps(p_good_dict)
        except Exception as e:
            self.m_logger.error("Error storing io msg to cache: " + str(e))
            return
        l_res= self.cache.zadd(keywords.key_redis_msg_sorted_set, {l_msg_json: helper.timestampNowFloat()})
        if l_res == keywords.redis_error or not isinstance(l_res, int):
            self.m_logger.error(f"Error storing io msg to cache. Returned: {l_res}")

    def get_bus_history_formatted(self) -> Optional[str]:
        """Returns a formatted text containing the messages exchanged on the bus.
        Returns None if an error occurs."""
        l_msgs: List[dict]= self.cache.zrange(keywords.key_redis_msg_sorted_set, 0, -1)
        if not isinstance(l_msgs, list):
            self.m_logger.error(f'Error getting bus history from redis: expecting list, got {l_msgs}')
            return None
        width1= 0
        for i, l_msg in enumerate(l_msgs):
            try:
                l_msgs[i]= json.loads(l_msg)
            except Exception as e:
                self.m_logger.error(f'Error generating bus formatted history: {e}')
                return None
        
        # Format msgs fields
        for l_msg in l_msgs:
            try:
                if isinstance(l_msg['data'], list) and \
                    all([isinstance(i, int) for i in l_msg['data']]):
                    l_msg['data'] = helper.format_bytearray(l_msg['data'])
                if 'msg' in l_msg.keys() and \
                    isinstance(l_msg['msg'], list) and \
                        all([isinstance(i, int) for i in l_msg['msg']]):
                    l_msg['msg'] = helper.format_bytearray(l_msg['msg'])
                l_date, l_time= l_msg['timestamp'].split()
                l_msg['date']= l_date
                l_msg['time']= l_time
                l_max_width= max(len(l_date), len(l_time))
                width1= max(width1, l_max_width)
            except Exception as e:
                self.m_logger.error(f'Error generating bus formatted history: {e}')
                return None
        
        answ_counter= 0
        l_history= ''
        for l_msg in l_msgs:
            if l_msg is not l_msgs[0]:
                l_history += '\n'

            # Answer
            try:
                l_out= f'{cli.color.back_yellow} IN  <--- {cli.color.regular}\n'
                l_out += (f'{cli.color.forw_green}{l_msg["date"].rjust(width1)}{cli.color.regular} | Source:    {l_msg["src"]}\n')
                l_out += (f'{cli.color.forw_green}{l_msg["time"].rjust(width1)}{cli.color.regular} | Dest:      {l_msg["dest"]}\n')
                l_out +=                                (f'{" ".rjust(width1)} | Valid:     {l_msg["valid"]}\n')
                l_out +=                                (f'{" ".rjust(width1)} | I/O cmd:   {l_msg["io_cmd"]}\n')
                l_out +=                                (f'{" ".rjust(width1)} | Data:      {l_msg["data"]}\n')
                l_out +=                                (f'{" ".rjust(width1)} | Data size: {l_msg["data_size"]}\n')
                l_out +=                                (f'{" ".rjust(width1)} | Pos:       {l_msg["pos"]}\n')
                l_out +=                                (f'{" ".rjust(width1)} | Message:   {l_msg["msg"]}\n')
                l_history += l_out
                answ_counter += 1
                continue
            except:
                pass
            
            # Request
            try:
                l_msg['src']= bus.module.videoserver
                if l_msg['io_cmd'] in [bus.cmd.mtx_on_off_a, bus.cmd.mtx_vel_a, bus.cmd.mtx_ver_a]:
                    l_msg['dest']= bus.module.mosf_tx_a
                elif l_msg['io_cmd'] in [bus.cmd.mtx_on_off_b, bus.cmd.mtx_vel_b, bus.cmd.mtx_ver_b]:
                    l_msg['dest']= bus.module.mosf_tx_b
                elif l_msg['io_cmd'] in [bus.cmd.mrx_ver_a, bus.cmd.mrx_wire_data_a, bus.cmd.mrx_wire_t0_a, bus.cmd.mrx_tmos_a]:
                    l_msg['dest']= bus.module.mosf_rx_a
                elif l_msg['io_cmd'] in [bus.cmd.mrx_ver_b, bus.cmd.mrx_wire_data_b, bus.cmd.mrx_wire_t0_b, bus.cmd.mrx_tmos_b]:
                    l_msg['dest']= bus.module.mosf_rx_b
                elif l_msg['io_cmd'] in [bus.cmd.trig_ver_a, bus.cmd.trig_click_a, bus.cmd.trig_on_off_a, bus.cmd.trig_status_a, bus.cmd.trig_setting_a]:
                    l_msg['dest']= bus.module.trigger_a
                elif l_msg['io_cmd'] in [bus.cmd.trig_ver_b, bus.cmd.trig_click_b, bus.cmd.trig_on_off_b, bus.cmd.trig_status_b, bus.cmd.trig_setting_b]:
                    l_msg['dest']= bus.module.trigger_b
                elif l_msg['io_cmd'] in [bus.cmd.io_ver, bus.cmd.io_test_batt, bus.cmd.io]:
                    l_msg['dest']= bus.module.io
                else:
                    l_msg['dest']= general.dato_non_disp
                l_out= f'{cli.color.back_white} OUT ---> {cli.color.regular}\n'
                l_out += (f'{cli.color.forw_green}{l_msg["date"].rjust(width1)}{cli.color.regular} | Source:    {l_msg["src"]}\n')
                l_out += (f'{cli.color.forw_green}{l_msg["time"].rjust(width1)}{cli.color.regular} | Dest:      {l_msg["dest"]}\n')
                if 'data' in l_msg.keys():
                    l_out +=                            (f'{" ".rjust(width1)} | Data:      {l_msg["data"]}\n')
                if 'io_cmd' in l_msg.keys():
                    l_out +=                            (f'{" ".rjust(width1)} | I/O cmd:   {l_msg["io_cmd"]}\n')
                if 'cmd_type' in l_msg.keys():
                    l_out +=                            (f'{" ".rjust(width1)} | Cmd type:  {l_msg["cmd_type"]}\n')
                l_history += l_out
                continue
            except:
                pass
            
            # Unrecognized message
            l_msg.pop('date')
            l_msg.pop('time')
            l_history += f'{cli.color.back_gray}N/A{cli.color.regular}\n{l_msg}\n'

        l_history += f'\n> {answ_counter}/{len(l_msgs)} messaggi contenevano i campi di una risposta dal bus'
        return l_history

    # SYSTEM

    def clear_rigproc_pid(self) -> bool:
        return self.cache.delete(redis_keys.system.rigproc_pid) > 0

    def clear_rigcam_pid(self) -> bool:
        return self.cache.delete(redis_keys.system.rigcam_pid) > 0

    def set_rigproc_pid(self, p_pid: int) -> bool:
        return self.cache.set(redis_keys.system.rigproc_pid, p_pid) is True
    
    def set_rigcam_pid(self, p_pid: int) -> bool:
        return self.cache.set(redis_keys.system.rigcam_pid, p_pid) is True

    def get_rigproc_pid(self) -> Union[int, str]:
        l_pid = self.cache.get(redis_keys.system.rigproc_pid)
        try:
            return int(l_pid)
        except:
            return l_pid

    def get_rigcam_pid(self) -> Union[int, str]:
        l_pid = self.cache.get(redis_keys.system.rigcam_pid)
        try:
            return int(l_pid)
        except:
            return l_pid

    def set_rigproc_mem_usage(self, mem_usage: int) -> bool:
        if self.cache.set(redis_keys.system.rigproc_mem_usage, mem_usage) is True:
            l_now = helper.timestampNowFormatted()
            return self.cache.set(redis_keys.system.rigproc_mem_check_ts, l_now) is True
        else:
            return False

    def set_rigcam_mem_usage(self, mem_usage: int) -> bool:
        if self.cache.set(redis_keys.system.rigcam_mem_usage, mem_usage) is True:
            l_now = helper.timestampNowFormatted()
            return self.cache.set(redis_keys.system.rigcam_mem_check_ts, l_now) is True
        else:
            return False

    def get_rigproc_mem_usage(self) -> Tuple[str, Union[float, str]]:
        l_ts = self.cache.get(redis_keys.system.rigproc_mem_check_ts)
        l_mem = self.cache.get(redis_keys.system.rigproc_mem_usage)
        try:
            return l_ts, float(l_mem)
        except:
            return l_ts, l_mem

    def get_rigcam_mem_usage(self) -> Tuple[str, Union[float, str]]:
        l_ts = self.cache.get(redis_keys.system.rigcam_mem_check_ts)
        l_mem = self.cache.get(redis_keys.system.rigcam_mem_usage)
        try:
            return l_ts, float(l_mem)
        except:
            return l_ts, l_mem

    def clear_rigproc_uptime(self) -> bool:
        return self.cache.set(redis_keys.system.rigproc_uptime, 0) is True

    def set_rigproc_uptime(self, uptime: int) -> bool:
        return self.cache.set(redis_keys.system.rigproc_uptime, uptime) is True

    def get_rigproc_uptime(self) -> Union[int, str]:
        l_ut = self.cache.get(redis_keys.system.rigproc_uptime)
        try:
            return int(l_ut)
        except:
            return l_ut

    def set_sshfs_mounted(self, p_mounted: bool) -> None:
        self.cache.set(redis_keys.system.sshfs_mounted, 1 if p_mounted else 0)
        self.cache.set(redis_keys.system.sshfs_mount_ts, helper.timestampNowFloat())

    def is_sshfs_mounted(self) -> bool:
        """Returns False if error"""
        l_mounted_val = self.cache.get(redis_keys.system.sshfs_mounted)
        if l_mounted_val == '1':
            return True
        else:
            return False

    def when_was_sshfs_mounted(self) -> Optional[int]:
        """Returns a timestamp for the last sshfs mount attempt"""
        l_ts = self.cache.get(redis_keys.system.sshfs_mount_ts)
        try:
            return int(l_ts)
        except:
            return None

    # SYSTEM STATUS

    def moduleStatusKey(self, p_module, p_status_key):
        """ Restituisce la chiave di stato a partire dal modulo e dallo stato """
        return f'status_{p_module}#{p_status_key}'

    def updateStatusInfo(self, p_module, p_status_key, p_status_value):
        """
        Salvataggio delle informazioni relative allo stato del sistema
        che la cache deve conoscere.
        Vengono salvate tutte le info relative allo stato dei moduli
        hw ed eventuali funzioni di stato del rip stesso.
        Non memorizzo ogni messaggio relativo allo stato ma lo stato stesso.

        Parameters
        ----------
        p_module : string
            chiave relativa al modulo interessato
        p_status_key : string
            Nome dello info di stato che monitoriamo
        p_status_value: string
            Valore della info di stato monitorata
        
        Return:
            Se il valore è diverso dal precedente valore memorizzato o 
            la key non era presente ritorna True (stato aggiornato),
            altrimenti torna False, nessun update eseguito
        """
        l_previous_value= self.pers.get(self.moduleStatusKey(p_module, p_status_key))
        if l_previous_value == None or l_previous_value != p_status_value:
            self.pers.set(
                self.moduleStatusKey(p_module, p_status_key), 
                p_status_value
            )
            return True
        # No update needed 
        return False 

    def getStatusInfo(self, p_module, p_status_key):
        """
        Preleva da Redis le informazioni su un componente del sistema

        Parameters
        ----------
        p_module : string
            chiave relativa al modulo interessato
        p_status_key : string
            Nome dello info di stato che monitoriamo

        Returns
        -------
        Il valore dello stato (str, in genere)
            oppure
        "dato_non_diponibile" in caso di errore o di chiave mancante
        """
        l_status= self.pers.get(
            self.moduleStatusKey(p_module, p_status_key), 
            p_default=keywords.dato_non_disp
        )
        return l_status

    def removeStatusInfo(self, p_module, p_status_key):
        """ Rimuove un parametro di stato da Redis 
        (da eseguire prima dell'implant status per evitare di mostrare parametri vecchi) """
        l_res= self.pers.delete(self.moduleStatusKey(p_module, p_status_key))
        return isinstance(l_res, int)

    def add_temp_measure(self, p_env_temp: int, p_cpu_temp: float):
        """
        Aggiunge una misura di temperatura alla cronologia.
        Fa in modo che ci siano al massimo 500 valori nella cronologia.

        Parameters
        ----------
        `p_env_temp`: misura in °C della temperatura rilevata dall'impianto
        `p_cpu_temp`: misura in °C della temperatura della CPU
        """
        l_now = helper.timestampNowFloat()
        l_now_fmt = helper.timestamp_to_formatted(l_now)
        l_text = f'{l_now_fmt} ~ ENV: {p_env_temp} °C, CPU: {p_cpu_temp} °C'
        self.m_logger.info(f'Adding temperature sample -> {l_text}')
        self.pers.zadd(redis_keys.temp.sorted_set, {l_text: l_now})

        l_count = self.pers.zcount(redis_keys.temp.sorted_set, 0, l_now)
        if isinstance(l_count, int):
            if l_count > _TEMP_HISTORY_LIMIT:
                l_extra = l_count - _TEMP_HISTORY_LIMIT
                l_deleted = self.pers.zpopmin(redis_keys.temp.sorted_set, l_extra)
                if not isinstance(l_deleted, list) and not len(l_deleted) > 0:
                    self.m_logger.error('Error popping items from temperature history')
        else:
            self.m_logger.error('Cannot get temperature history\'s length')


    def get_temp_measures_formatted(self) -> Optional[str]:
        """
        Restituisce una lista di stringhe, 
        ciascuna contenenete un timestamp e il valore di temperatura, leggibili.
        """
        l_history = self.pers.zrange(redis_keys.temp.sorted_set, 0, -1)
        if not isinstance(l_history, list):
            self.m_logger.error('Error getting temperatures history')
            return None
        try:
            return '\n'.join(l_history)
        except Exception as e:
            self.m_logger.error(f'Error formatting temperatures history ({type(e)}): {e}')
            return None


    # DIAGNOSI

    def _setDiagnosticInfosIO(self, p_key, p_value):
        """
        Aggiorna la diagnostica per il dispositivo io che 
        ha generato key, value
        @todo controllare che keyword genero realmente...
        """
        l_device= [key for (key, value) in keywords.io_devices_keys.items() if value == p_value]
        if l_device:
            " Marca lo stato del device come ko "
            if p_value== keywords.key_io_missed_answer or \
                p_value== keywords.key_io_another_answer:
                l_status = keywords.status_ko
            else:
                l_status = keywords.status_ok
            " aggiornamento keywprd status per il device in oggetto "
            self.cache.set(f'diag_{l_device}', l_status) 


    # ESECUZIONE FLOWS

    def startFlow(self, p_flow_id: str, p_flow_type: str) -> bool:
        """ Inserisce il tempo di inizio esecuzione del flow nella cache di Redis """
        l_flow_data= {
                keywords.flow_start_time: helper.timestampNowFormatted(),
                keywords.flow_type: p_flow_type,
                keywords.flow_stop_time: None,
                keywords.flow_errors: None
            }
        try:
            l_flow_data= json.dumps(l_flow_data)
        except:
            self.m_logger.error(f'Error generating flow data: cannot dump json {l_flow_data}')
            return False
        l_res= self.cache.hset(
            keywords.key_flow_log,
            p_flow_id,
            l_flow_data
        )
        return isinstance(l_res, int)

    def stopFlow(self, p_flow_id: str, p_flow_error: str) -> bool:
        """ Inserisce il tempo di termine esecuzione del flow nella cache di Redis """
        l_flow_data= self.cache.hget(keywords.key_flow_log, p_flow_id)
        try:
            l_flow_data= json.loads(l_flow_data)
        except:
            self.m_logger.error(f'Error reading flow data from cache: cannot load json {l_flow_data}')
            return False
        wrapkeys.setValue(l_flow_data, helper.timestampNowFormatted(), keywords.flow_stop_time)
        wrapkeys.setValue(l_flow_data, p_flow_error, keywords.flow_errors)
        try:
            l_flow_data= json.dumps(l_flow_data)
        except:
            self.m_logger.error(f'Error recreating flow data: cannot dump json {l_flow_data}')
            return False
        l_res= self.cache.hset(
            keywords.key_flow_log,
            p_flow_id,
            l_flow_data
        )
        return isinstance(l_res, int)

    
    # RECOVERY

    def store_event_to_recover(self, event: EventToRecover) -> bool:
        """Encodes and stores in Redis an event to recover.
        Returns True if the operation was correctly performed, False otherwise."""
        event_key= f'{redis_keys.recovery.key_prefix}{event.timestamp}'
        event_dict= {
            redis_keys.recovery.shoot_array: {
                redis_keys.recovery.timestamp: event.timestamp,
                redis_keys.recovery.shoots: [{
                    redis_keys.recovery.cam_id: shoot.cam_id,
                    redis_keys.recovery.cam_num: shoot.cam_num,
                    redis_keys.recovery.img_path: shoot.img_path,
                } for shoot in event.shoot_array.shoots],
                redis_keys.recovery.trans_id: event.shoot_array.trans_id,
            },
            redis_keys.recovery.event_id: event.event_id,
            redis_keys.recovery.remote_folder: event.remote_folder_name,
            redis_keys.recovery.trig_json_model: event.trig_json_model,
            redis_keys.recovery.diag_json_model: event.diag_json_model,
            redis_keys.recovery.mosf_json_model: event.mosf_json_model            
        }
        try:
            event_json= json.dumps(event_dict)
            l_res= self.pers.set(event_key, event_json)
            return l_res != _REDIS_DEFAULT_VALUE
        except Exception as e:
            self.m_logger.error(f'Error dumping event to recover to json ({type(e)}): {e}')
            return False

    def get_events_to_recover(self) -> List[EventToRecover]:
        """Gets and decode an event to recover from Redis.
        Returns an empty list if an error occurs."""
        events= []
        keys= self.pers.scan_iter(f'{redis_keys.recovery.key_prefix}*')
        for key in keys:
            event_json= self.pers.get(key)
            try:
                event_dict= json.loads(event_json)
            except Exception as e:
                self.m_logger.error(f'Error trying to load event to recover json ({type(e)}): {e}. Data found was: {event_json}')
                break
            try:
                shoot_array_dict= event_dict[redis_keys.recovery.shoot_array]
                shoots_list= shoot_array_dict[redis_keys.recovery.shoots]
                events.append(EventToRecover(
                    shoot_array=CameraShootArray(
                        timestamp=shoot_array_dict[redis_keys.recovery.timestamp],
                        shoots=[
                            CameraShoot(
                                cam_id=shoot_dict[redis_keys.recovery.cam_id],
                                cam_num=shoot_dict[redis_keys.recovery.cam_num],
                                img_path=shoot_dict[redis_keys.recovery.img_path]
                            )
                            for shoot_dict in shoots_list
                        ],
                        trans_id=shoot_array_dict[redis_keys.recovery.trans_id]
                    ),
                    event_id=event_dict[redis_keys.recovery.event_id],
                    remote_folder_name=event_dict[redis_keys.recovery.remote_folder],
                    trig_json_model=event_dict[redis_keys.recovery.trig_json_model],
                    diag_json_model=event_dict[redis_keys.recovery.diag_json_model],
                    mosf_json_model=event_dict[redis_keys.recovery.mosf_json_model],
                ))
            except Exception as e:
                self.m_logger.error(f'Error decoding event to recoer ({type(e)}): {e}')
        return events

    def remove_event_to_recover(self, event: EventToRecover) -> bool:
        """Removes an event to recover from Redis. 
        Returns True if the operation was correctly performed, False otherwise."""
        event_key= f'{redis_keys.recovery.key_prefix}{event.timestamp}'
        l_res= self.pers.delete(event_key)
        return l_res != _REDIS_DEFAULT_VALUE


#
# STATIC BUILD
#

m_static_redis= None

def staticBuild():
    """
    Istanza di RedisI senza avere il file di configurazione
    Ad esempio per uso diretto su ipython in develop

    Returns
    -------
    Oggetto RedisI istanziato

    """
    # Instance
    m_static_redis= DualRedis('localhost', '6379', 'localhost', '6380')
    return m_static_redis


#
# SINGLETON
#

_redisI: DualRedis= None


def initialize_redis(p_chost, p_cport, p_phost, p_pport) -> bool:
    """Creates the Redis instance for Rigproc (cache and persistent).
    Returns True if the operation was correctly performed, False otherwise."""
    global _redisI
    if isinstance(_redisI, DualRedis):
        return True
    _redisI= DualRedis(p_chost, p_cport, p_phost, p_pport)
    return isinstance(_redisI, DualRedis)


def get_redisI() -> Optional[DualRedis]:
    """Returns the Redis instance for Rigproc (cache and persistent).
    Returns None if the instance was not initialized"""
    if not isinstance(_redisI, DualRedis):
        logging.getLogger('root').error('Redis instance not initialized')
        return None
    return _redisI


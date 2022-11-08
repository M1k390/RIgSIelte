#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fake camera process
"""
import threading
from datetime import datetime
import time
import uuid
import logging
from rigproc.commons.redisi import get_redisI
from rigproc.commons import keywords
from rigproc.commons import helper




class FakeCamera():
    """ Emettitore di eventi camera fake """

    def __init__(self):
        self.m_redisI= get_redisI()
        self.m_logger= logging.getLogger('root')

    def start(self):
        self.m_thread=threading.Thread(target= self._triggerTh)
        self.m_stop= False
        self.m_thread.start()

    def close(self):
        self.m_stop= True

    def wait(self):
        self.m_thread.join()

    def getThread(self):
        return self.m_thread

    def _triggerTh(self):
        """
        Ogni 5 secondi lancio un trigger con expire di 5s
        """
        while not self.m_stop:
            self.fakeEventTrig()
            time.sleep(20)

    def fakeEventTrig(self):
        """
        Fake evt trig
        immagini, e dati come se venissero dalla cam
        key con expire
        """
        try:
            h= helper.Helper()
            l_now= datetime.now()
            l_name= 'evt_trigger_'
            l_hks={}
            l_hks[keywords.key_evt_trig_which_prr]= keywords.key_prrA
            l_hks[keywords.key_evt_tr_id]= h.new_trans_id()
            l_hks[keywords.key_evt_data]=l_now.strftime("%y-%m-%d")
            l_hks[keywords.key_evt_time]=l_now.strftime("%H_%M_%S")
            l_ts=l_now.strftime("%H_%M_%S")
            l_evtName= l_name + l_ts
            " img 0 nome parziale "
            l_hks[keywords.key_img_name_0]= l_ts + "_cam_0"
            l_img0Name= h.data_file_path('cam_0.img')
            with open(l_img0Name, 'rb') as f:
                l_hks[keywords.key_img_data_0]=f.read()
            " img 1 nome parziale "
            l_hks[keywords.key_img_name_1]= l_ts + "_cam_1"
            l_img1Name= h.data_file_path('cam_0.img')
            with open(l_img1Name, 'rb') as f:
                l_hks[keywords.key_img_data_1]=f.read()
            " img 2 nome parziale "
            l_hks[keywords.key_img_name_2]= l_ts + "_cam_2"
            l_img2Name= h.data_file_path('cam_0.img')
            with open(l_img2Name, 'rb') as f:
                l_hks[keywords.key_img_data_2]=f.read()
            " img 3 nome parziale "
            l_hks[keywords.key_img_name_3]= l_ts + "_cam_3"
            l_img3Name= h.data_file_path('cam_0.img')
            with open(l_img3Name, 'rb') as f:
                l_hks[keywords.key_img_data_3]=f.read()
            " img 4 nome parziale "
            l_hks[keywords.key_img_name_4]= l_ts + "_cam_4"
            l_img4Name= h.data_file_path('cam_0.img')
            with open(l_img4Name, 'rb') as f:
                l_hks[keywords.key_img_data_4]=f.read()
            " img 5 nome parziale "
            l_hks[keywords.key_img_name_5]= l_ts + "_cam_5"
            l_img5Name= h.data_file_path('cam_0.img')
            with open(l_img5Name, 'rb') as f:
                l_hks[keywords.key_img_data_5]=f.read()
            " creazione hash evento "
            self.m_redisI.cache.hset(l_evtName, l_hks)
            self.m_redisI.cache.expire(l_evtName, 5)
        except Exception as e:
            self.m_logger.error("Exception crating simulated camera imgs {}".format(e))

" ----- GLOBAL ----- "
def _procFakeCamera():
    fake= FakeCamera()
    #fake.start()
    return fake


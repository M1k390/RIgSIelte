#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recover task flow
"""
import os
import sys
import shutil

from rigproc.commons.helper import helper
from rigproc.commons import keywords

def _buildFlowRecover(self):
    """ Tasklist builder per event  """
    self.m_taskAll= {
        **self.m_taskBegin,
        **self.m_taskImg,
        **self.m_taskTopicT0,
        **self.m_taskTopicDiag,
        **self.m_taskTopicWireData,
        **self.m_taskClosePipe
        }
    " indicizzazione taskAll entries"
    l_idx= 0
    for task in self.m_taskAll:
        self.m_taskAll[task]['id']= l_idx
        l_idx += 1
    " lista funzioni registrate realtive ai task "
    self.m_taskFuncList= {
        'id': 0,
        'tasks':[self._prepareWork,
                self._workImagesRemoteRecover,
                self._workTopicEvent,
                self._workTopicEventAnswer,
                self._workTopicDiagnosis,
                self._workTopicDiagnosisAnswer,
                self._workTopicEvent,
                self._workCleanLocalImages,
                self._closePipe],
        'continue': True
        }


def _workImagesRemoteRecover(self, p_data= None):
    """
    Salva le immagini sulla cartella remota nel flow recovering

    - recovering, prendo le immagini dalla cartella locale
    """
    self.m_logger.debug("entering")
    self.m_pipeFailed= False
    # generazione directory di destinazione
    imgR= self.m_data[keywords.evdata_remoteDir]
    if not os.path.exists(imgR):
        self.m_logger.info("creating dir : " + imgR)
        os.mkdir(imgR)
    # upload time info
    self.m_data[keywords.evdata_upload_started]= helper.timeNow()
    self.m_data[keywords.evdata_upload_finished]= helper.timeNow()
    # cerco i file immagine salvati nella directory locale
    imgf= self.m_data[keywords.evdata_localDir]
    if not os.path.exists(imgf):
        self.m_logger.error("Critical error, local img are missing")
        self.m_error= True
        self.m_criticalError= True
        self.m_done= True
        self.m_stop= True
        return False
    imgs= [f for f in os.listdir(imgf) if os.path.isfile(os.path.join(imgf, f)) ]
    # @todo filtrare i files immagine per estensione/nome ?
    for imgFile in imgs:
        try:
            shutil.copy(os.path.join(imgf,imgFile), os.path.join(imgR,imgFile))
        except:
            l_excMsg= sys.exc_info()[0]
            self.m_logger.error("Error saving local {} to remote {}: ".format(imgFile, os.path.join(imgR,imgFile)))
            self.m_logger.error("stack trace :" +str( l_excMsg))
            self.m_recovering= True
            self.m_error= True
            # solo per i test si usa stop on error
            if self.m_stopOnError:
                self.m_stop= True
                self.m_data[keywords.evdata_upload_is_completed]= False
                return False
    # Check step done
    self.m_data[keywords.evdata_upload_finished]= helper.timeNow()
    self.m_data[keywords.evdata_upload_is_completed]= True
    self.m_logger.info("Images saved to remote folder: " + str(imgs))
    self.m_taskFuncList['continue']= True
    self._incTaskId()
    return True


def _workCleanLocalImages(self, p_data= None):
    """ Se la pipeline del recovering è andata a buon fine cancello le immagini
    in locale """
    if not self.m_error:
        try:
            shutil.rmtree(self.m_data[keywords.evdata_localDir], ignore_errors= True)
        except Exception as e :
            self.m_logger.error("Error removing local images {}".format(e))
        self.m_logger.info("Cleaning local img storage on: " + self.m_data[keywords.evdata_localDir])
    " "
    self._incTaskId()
    self.m_taskFuncList['continue']= True
    return True
#!/usr/bin/env python

import logging
import time

from switcher.agistopology.ce import AGISCE, AGISCEHandler
from switcher.event import Event
from switcher.downtime import DowntimeList, DowntimeListList, DowntimeCollectionList


class CE(AGISCE):

    def __init__(self, endpoint, downtimesconf):
        """
        :param str endpoint: the CE endpoint
        :param SafeConfigParser downtimesconf: config with data about 
                                               when to change status
        """
        super(CE, self).__init__(endpoint)
        self.log = logging.getLogger('switcher')
        self.downtimesconf = downtimesconf
        self.downtimelist = DowntimeList()
        self.event = None
        self._read_config_parameters()
        self.log.debug('Object CESwitcher %s created.' %self.endpoint)


    def _read_config_parameters(self):
        """
        reads configuration from config file
        """
        self.time_to_disable_sec = self.downtimesconf.getint('CE', 'setdisable') * 3600


    def add_downtime(self, downtime):
        self.downtimelist.add(downtime)


    def getDowntimeList(self):
        return self.downtimelist


    def getExtendedDowntimeList(self):
        """
        return a new DowntimeList object 
        where all Downtime instances have been extended.
        The items in the return DowntimeList contain the 
        time interval the CE will be DISABLED, 
        while the original ones contained the time interval
        the CE is in scheduled downtime.
        :return DowntimeList:
        """
        return self.downtimelist.extend(self.time_to_disable_sec)

    # --------------------------------------------------------------------------

    def evaluate(self):
        """
        evaluates if this CE should change status ACTIVE/DISABLED
        """
        self.log.info('Evaluating CE %s' %self.endpoint)
        self.event = None
        new_status = self._get_new_status() 
        self.log.info('New status is %s' %new_status)
        if self.status == new_status:
            self.log.info('New status is the same that current one. Nothing to do.')
            return
        else:
            self.log.info('New status is different. Changing it.')
            self._set_event(new_status)

    
    def _get_new_status(self):
        """
        finds out in which status this CE should be
        :return str:
        """
        self.log.debug('Starting.')
        t_epoch = int( time.time() + self.time_to_disable_sec) 
        if self.check_if_future_downtime(t_epoch):
            return 'DISABLED'
        else:
            return 'ACTIVE'


    def check_if_future_downtime(self, t_epoch):
        """
        checks if there at least one downtime event 
        for this CE t_epoch seconds in the future
        :param int t_epoch: time in seconds since epoch
        :return bool:
        """
        self.log.info('Checking if CE %s is affected by downtime.' %self.endpoint)
        for downtime in self.downtimelist.getlist():
            if t_epoch in downtime:
                self.log.info('CE %s affected by downtime. Returning True.' %self.endpoint)
                return True
        else:
            self.log.info('CE %s is not affected by downtime. Returning False.' %self.endpoint)
            return False


    def _set_event(self, new_status):
        """
        set self.event
        """
        self.event = Event('CE', 
                           self.endpoint, 
                           self.status, 
                           new_status, 
                           )

    # -------------------------------------------------------------------------

    def act(self, agisapi):
        """
        acts to change status of entities, based on the result
        of the evaluate() call.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting over CE %s.' %self.endpoint)
        if self.event:
            self.log.info('There is an Event object recorded for CE %s. Acting.' %self.endpoint)
            self._change_ce_status(agisapi)
        self.log.info('Leaving.')


    def _change_ce_status(self, agisapi):
        """
        """
        new_status = self.event.new
        self.log.info('Changing status of CE %s to %s' %(self.endpoint, new_status))
        comment = "foo" # FIXME
        out, err, rc = agisapi.change_ce_status(self.name, new_status, comment)
        self.log.info('Ouput, Err, and RC from changing status: %s, %s, %s' %(out, err, rc))
        self.status = new_status
        self.log.debug('Leaving.')








# =============================================================================


class CEHandler(AGISCEHandler):

    def evaluate(self):
        for ce in self.getlist():
            ce.evaluate()


    def getDowntimeCollectionList(self):
        """
        to get if all CEs will be DISABLED at the same time.
        :return DowntimeCollectionList:
        """
        downtimelistlist = DowntimeListList()
        for ce in self.getlist():
            downtimelist = ce.getExtendedDowntimeList()        
            downtimelistlist.add(downtimelist)
        return downtimelistlist.getDowntimeCollectionList()

#!/usr/bin/env python

import logging
import time

from switcher.agistopology.queue import AGISQueue
from switcher.topology.ce import CEHandler
from switcher.topology.ddm import DDMHandler
from switcher.event import Event



class Queue(AGISQueue):
    
    def __init__(self, name, qdata, downtimesconf):
        """
        :param str name: the queue name
        :param SafeConfigParser downtimesconf: config with data about 
                                               when to change status
        """
        super(Queue, self).__init__(name, qdata)
        self.log = logging.getLogger('switcher')
        self.cehandler = CEHandler()
        self.ddmhandler = DDMHandler()
        self.downtimesconf = downtimesconf
        self.switcher_status = None
        self.event = None
        self.reason_change = None
        self._read_config_parameters()
        self.log.debug('Object QueueSwitcher %s created.' %self.name)


    def _read_config_parameters(self):
        """
        reads configuration from config file
        """
        var = '%s_setbrokeroff' %self.type # type = analysis | production
        self.time_to_brokeroff_sec = self.downtimesconf.getint('QUEUE', var) * 3600
    
        var = '%s_setoffline' %self.type # type = analysis | production
        self.time_to_offline_sec = self.downtimesconf.getint('QUEUE', var) * 3600


    # --------------------------------------------------------------------------

    def evaluate(self):
        """
        triggers the evaluation of all registered downtimes
        for all CEs and DDMs in this Queue, 
        and change status when needed.
        """
        self.log.info('Evaluating queue %s.' %self.name)
        # we reset first
        self.event = None
        self.reason_change = None

        self.log.info('Evaluating CEs.')
        self.cehandler.evaluate()
        self.ddmhandler.evaluate()

        self.log.info('Getting the new status.')
        new_status = self._get_new_status()
        self.log.info('New status for queue %s is %s.' %(self.name, new_status))
        if new_status == self.status:
            self.log.info('New status is the current status. Nothing to do.')
            return
        else:
            self.log.info('New status is different. Changing it.')
            self._set_event(new_status)
            ###self.change_status(new_status)


    # FIXME 
    # this part - get_new_status(), should_be_offline(), should_be_online() and check_status()-
    # should be done in a nicer way
    # but for now is OK

    def _get_new_status(self):
        """
        finds out in which status this Queue should be
        We check first for OFFLINE, as it is the most restrictive one.
        If queue does not qualify yet for OFFLINE, then we try with BROKEROFF.
        If not of them, then the queue should be ONLINE.
        :return str:
        """
        self.log.debug('Starting.')

        # first, collect all downtimes for entities belonging to this Queue
        ce_downtime_collection_list = self.cehandler.getDowntimeCollectionList()
        ddm_downtime_collection_list = self.ddmhandler.getDowntimeCollectionList()
        downtime_collection_list = ce_downtime_collection_list + ddm_downtime_collection_list

        # second, inspect those downtimes
        if self.should_be_offline(downtime_collection_list):
            return 'offline'
        elif self.should_be_brokeroff(downtime_collection_list):
            return 'brokeroff'
        else:
            return 'online'


    def should_be_offline(self, downtime_collection_list):
        """
        checks if this Queue should be set OFFLINE
        :return bool:
        """
        self.log.debug('Starting.')
        out = self._check_status(self.time_to_offline_sec, downtime_collection_list)
        self.log.debug('Leaving with value %s.' %out)
        return out


    def should_be_brokeroff(self, downtime_collection_list):
        """
        checks if this Queue should be set BROKEROFF 
        :return bool:
        """
        self.log.debug('Starting.')
        out = self._check_status(self.time_to_brokeroff_sec, downtime_collection_list)
        self.log.debug('Leaving with value %s.' %out)
        return out


    def _check_status(self, seconds, downtime_collection_list):
        """
        """
        now = time.time()
        for downtime_collection in downtime_collection_list.getlist():
            timeinterval = downtime_collection.getTimeInterval()
            if (now + seconds) in timeinterval:
                # FIXME: record an Event() here
                out = True
        out = False
        return out
    

    def _set_event(self, new_status):
        """
        set self.event
        """
        self.event = Event('Queue', self.name, self.status, new_status, self.reason_change)


    # -------------------------------------------------------------------------

    def act(self, agisapi):
        """
        acts to change status of entities, based on the result
        of the evaluate() call.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting over queue %s.' %self.name)
        for endpoint,ce in self.cehandler.getitems():
            ce.act(agisapi)
        if self.event:
            self.log.info('There is an Event object recorded for queue %s. Acting.' %self.name)
            self._change_status(agisapi)
        self.log.info('Leaving.')


    def _change_status(self, agisapi):
        """
        change the status of this queue.
        :param str new_status: the new status value
        """
        self.log.debug('Starting.')

        #self.event = Event('Queue', self.name, self.status, new_status, self.reason_change)
        new_status = self.event.new

        comment = "foo" #FIXME
        out, err, rc = agisapi.change_queue_status(self.name, new_status, comment)
        self.log.info('Ouput, Err, and RC from changing status: %s, %s, %s' %(out, err, rc))
        self.status = new_status
        self.log.debug('Leaving.')

    # -------------------------------------------------------------------------

    def _collect_events(self):
        """
        grab all Event instances for this queue
        """
        self.log.info('Starting collecting Events for queue %s.' %self.name)
        event_l = []
        # first check for this queue Event
        if self.event:
            self.log.info('Adding to the list an Event for queue %s' %self.name)
            event_l.append(self.event)
        # then check for the CEs
        for endpoint, ce in self.ce_d.items():
            self.log.debug('Checking CE %s for an Event.' %endpoint)
            if ce.event:
                self.log.info('Adding to the list an Event from CE %s' %endpoint)
                event_l.append(ce.event)
        self.log.info('Queue %s has %s Events. '%(self.name, len(event_l)))
        return event_l
                   

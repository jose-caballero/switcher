#!/usr/bin/env python

import logging
import time
import urllib

from switcher.agistopology.ce import AGISCE, AGISCEHandler
from switcher.event import Event
from switcher.downtime import EndpointDowntimes, EndpointDowntimesSet, OverlapDowntimesList


class CE(AGISCE):

    def __init__(self, endpoint, downtimesconf):
        """
        :param str endpoint: the CE endpoint
        :param SafeConfigParser downtimesconf: config with data about 
                                               when to change status
        """
        super(CE, self).__init__(endpoint)
        self.log = logging.getLogger('topology')
        self.downtimesconf = downtimesconf
        self.endpointdowntimes = EndpointDowntimes()
        self.event = None
        self._read_config_parameters()
        self.log.debug('Object CESwitcher %s created.' %self.endpoint)


    def _read_config_parameters(self):
        """
        reads configuration from config file
        """
        self.time_to_disable_sec = self.downtimesconf.getint('CE', 'setdisable') * 3600


    def add_downtime(self, downtime):
        self.endpointdowntimes.add(downtime)


    def getEndpointDowntimes(self):
        return self.endpointdowntimes


    def getExtendedEndpointDowntimes(self):
        """
        return a new EndpointDowntimes object 
        where all Downtime instances have been extended.
        The items in the return EndpointDowntimes contain the 
        time interval the CE will be INACTIVE, 
        while the original ones contained the time interval
        the CE is in scheduled downtime.
        :return EndpointDowntimes:
        """
        self.log.debug('Starting.')
        out = self.endpointdowntimes.extend(self.time_to_disable_sec)
        self.log.debug('Leaving, returning %s.' %out)
        return out

    # --------------------------------------------------------------------------

    def evaluate(self):
        """
        evaluates if this CE should change status ACTIVE/INACTIVE
        """
        self.log.info('Evaluating CE %s' %self.endpoint)

        if self.event:
            self.log.info('CE %s has already been evaluated. Skipping.' %self.endpoint)
            return

        if self.state not in ['ACTIVE', 'INACTIVE']:
            self.log.debug('CE %s is in a state excluded for Switcher purposes. Doing nothing.' %self.endpoint)
        else:
            self.event = None
            event = self._get_new_status() 
            self.log.info('New status is %s' %event.new_status)
            if self.state == event.new_status:
                self.log.info('New status is the same that current one. Nothing to do.')
                event.old_status = self.state
            else:
                self.log.info('New status is different: %s -> %s. Recording an Event.' %(self.state, event.new_status))
                event.old_status = self.state
            self.event = event
            self.log.debug('Leaving.')

    
    def _get_new_status(self):
        """
        finds out in which status this CE should be.
        An Event object is created with relevant info, and returned.
        :return Event:
        """
        self.log.debug('Starting.')
        event = Event(entitytype='CE', uid=self.name)
        downtime = self.check_if_future_downtime()
        if downtime :
            event.new_status = 'INACTIVE'
            event.downtime = downtime

            # build the comment for later notification
            # FIXME
            # this maybe should not be here, as this part of the code does not know in theory
            # what is going to happen next
            # but for now is OK
            event.comment = 'set.inactive.by.Switcher+%s' %urllib.quote(downtime.info_url, safe='')

        else:
            event.new_status = 'ACTIVE'

            # build the comment for later notification
            # FIXME
            # this maybe should not be here, as this part of the code does not know in theory
            # what is going to happen next
            # but for now is OK
            event.comment = 'set.active.by.Switcher'
        self.log.debug('Leaving, returning event %s.' %event)
        return event


    def check_if_future_downtime(self):
        """
        checks if there at least one downtime event 
        for this CE t_epoch seconds in the future
        If yes, returns that Downtime object. 
        Otherwise, return None
        :return Downtime/None:
        """
        self.log.info('Checking if CE %s is affected by downtime.' %self.endpoint)
        t_epoch = int( time.time() + self.time_to_disable_sec) 
        # FIXME: what happens if there are more than one Downtime that can set the CE disabled???
        for downtime in self.endpointdowntimes.getlist():
            if t_epoch in downtime or downtime < t_epoch:
                self.log.info('CE %s affected by downtime. Returning the culprit downtime.' %self.endpoint)
                return downtime
        else:
            self.log.info('CE %s is not affected by downtime. Returning None.' %self.endpoint)
        return None


    # -------------------------------------------------------------------------

    def act(self, agisapi):
        """
        acts to change status of entities, based on the result
        of the evaluate() call.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting over CE %s.' %self.endpoint)
        if self.event and\
           not self.event.done:
            self.log.info('There is an Event object recorded for CE %s. Acting.' %self.endpoint)
            self._change_ce_status(agisapi)
        self.log.debug('Leaving.')


    def _change_ce_status(self, agisapi):
        """
        performs actual actions to change CE status.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        if not self.event.status_changed:
            self.log.info('CE %s did not change status, still %s. Doing nothing.' %(self.endpoint, self.event.old_status))
        else:
            self.log.info('Changing status of CE %s from %s to %s' %(self.endpoint, self.event.old_status, self.event.new_status))
            try:
                out, err, rc = agisapi.change_ce_status(self.event)
            except Exception as ex:
                self.log.error('Exception caught changing status: %s' %ex)
            else:
                self.log.info('Ouput, Err, and RC from changing status: %s, %s, %s' %(out, err, rc))
                self.state = self.event.new_status
                self.log.debug('Leaving.')
                self.event.done = True
        self.log.debug('Leaving.')




# =============================================================================


class CEHandler(AGISCEHandler):

    def __init__(self):
        super(CEHandler, self).__init__()
        self.log = logging.getLogger('switcher')


    def evaluate(self):
        for ce in self.getlist():
            ce.evaluate()


    def getOverlapDowntimesList(self):
        """
        to get if all CEs will be INACTIVE at the same time.
        :return OverlapDowntimesList:
        """
        self.log.debug('Starting.')
        endpointdowntimesset = EndpointDowntimesSet()
        for ce in self.getlist():
            self.log.debug('Processing CE %s' %ce.endpoint)
            endpointdowntimes = ce.getExtendedEndpointDowntimes()        
            self.log.debug('Got EndpointDowntimes %s' %endpointdowntimes)
            endpointdowntimesset.add(endpointdowntimes)
        out = endpointdowntimesset.getOverlapDowntimesList()
        self.log.debug('Leaving. Returning %s' %out)
        return out

    
    def _collect_events(self):
        """
        """
        self.log.debug('Starting.')
        event_l = []
        for ce in self.getlist():
            if ce.event and ce.event.status_changed and ce.event.done:
                event_l.append(ce.event)
        self.log.debug('Leaving. Returning %s' %event_l)
        return event_l





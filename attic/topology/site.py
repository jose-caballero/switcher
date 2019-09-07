#!/usr/bin/env python

import logging

from switcher.agistopology.site import AGISSite
from switcher.services.serverapi import AGIS


class Site(AGISSite):

    def __init__(self, name):
        super(Site, self).__init__(name)
        self.log = logging.getLogger('switcher')
        self.log.debug('Object SiteSwitcher %s created.' %self.name)

    # -------------------------------------------------------------------------

    def evaluate(self):
        """
        triggers the evaluation of all registered downtimes
        for all Queues in this Site, 
        check with ones need to change status
        """
        self.log.info('Evaluating site %s.' %self.name)
        for queuename, queue in self.queue_d.items():
            queue.evaluate()
        self.log.info('Leaving.')

    # -------------------------------------------------------------------------

    def act(self, agisapi):
        """
        acts to change status of entities, based on the result
        of the evaluate() call.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting over site %s.' %self.name)
        for queuename, queue in self.queue_d.items():
            queue.act(agisapi)
        self.log.info('Leaving.')

    # -------------------------------------------------------------------------

    def _collect_events(self):
        """
        grab all Event instances for this site
        """
        self.log.info('Starting collecting Events for site %s.' %self.name)
        event_l = []
        for qname, queue in self.queue_d.items():
            self.log.debug('Collecting Events for queue %s.' %qname)
            q_event_l = queue._collect_events()
            if q_event_l:
                self.log.info('Queue %s has %s Events. '%(self.name, len(q_event_l)))
                event_l += q_event_l
        self.log.info('Leaving, return %s Events for site %s.'%(len(event_l), self.name))
        return event_l

#!/usr/bin/env python

import logging
import time
from ConfigParser import SafeConfigParser

from switcher.agistopology.cloud import AGISCloud
from switcher.services.serverapi import AGIS
from switcher.utils import timestamp_now
from switcher.event import CloudEventList



class Cloud(AGISCloud):

    def __init__(self, name, notificationconf):
        """
        :param str name: cloud name
        :param SafeConfigParser notificationconf: config with the email addresses
        """
        super(Cloud, self).__init__(name)
        self.log = logging.getLogger('topology')
        self.notificationconf = notificationconf
        self.__read_config_parameters()
        self.log.debug('Object CloudSwitcher %s created.' %self.name)


    def __read_config_parameters(self):
        """
        read the email address
        """
        self.email_address = self.notificationconf.get('CLOUD-NOTIFICATIONS', self.name)

    # -------------------------------------------------------------------------

    def evaluate(self):
        """
        triggers the evaluation of all registered downtimes
        for all Sites in this Cloud, 
        check with ones need to change status
        """
        self.log.info('Evaluating cloud %s.' %self.name)
        for sitename, site in self.site_d.items():
            site.evaluate()
        self.log.info('Leaving.')

    # -------------------------------------------------------------------------

    def act(self, agisapi):
        """
        acts to change status of entities, based on the result
        of the evaluate() call.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting for cloud %s.' %self.name)
        for sitename, site in self.site_d.items():
            site.act(agisapi)
        self.log.info('Leaving.')

    # -------------------------------------------------------------------------


    def notify(self, email):
        """
        send email notification to the cloud
        """
        self.log.info('Starting.')
        cloud_event_l = self._collect_events()
        self.log.debug('Collected Events %s' %cloud_event_l)

        # FIXME
        # prototype
        email.conf = self.notificationconf
        email.cloud = self.name
        email.cloud_event_l = cloud_event_l
        email.send_notification()

        self.log.info('Leaving.')


#    def _collect_events(self):
#        """
#        grab all Event instances for this cloud
#        """
#        self.log.info('Starting collecting Events for all sites in cloud %s.' %self.name)
#        event_d = {} 
#        for sitename, site in self.site_d.items():
#            event_l = site._collect_events()
#            if event_l:
#                event_d[sitename] = event_l
#        self.log.info('Collected events for cloud %s: %s' %(self.name, event_d))
#        return event_d

    def _collect_events(self):
        """
        grab all Event instances for this cloud
        """
        self.log.info('Starting collecting Events for all sites in cloud %s.' %self.name)
        cloud_event_l = CloudEventList(self.name)
        for sitename, site in self.site_d.items():
            site_event_l = site._collect_events()
            cloud_event_l.add(site_event_l)
        self.log.debug('Collected %s Events for cloud %s' %(len(cloud_event_l.get_changed()), self.name))
        return cloud_event_l

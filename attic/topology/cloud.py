#!/usr/bin/env python

import logging
import time
from ConfigParser import SafeConfigParser

from switcher.agistopology.cloud import AGISCloud
from switcher.services.serverapi import AGIS
from switcher.utils import send_notifications, timestamp_now



class Cloud(AGISCloud):

    def __init__(self, name, notificationconf):
        """
        :param str name: cloud name
        :param SafeConfigParser notificationconf: config with the email addresses
        """
        super(Cloud, self).__init__(name)
        self.log = logging.getLogger('switcher')
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
        event_d = self._collect_events()
        self.log.debug('Collected Events %s' %event_d)
        for sitename, event_l in event_d.items():
            self.log.info('Sending notification for site %s' %sitename)
            subject = '[Switcher3 AutoExclusion] Summary for {cloud} at {time}'
            subject = subject.format(cloud=self.name, time=time.time())
            body = self.__build_body(event_d)
            to = self.email_address
            email.send_notification(subject, body, to)
        self.log.info('Leaving.')


    def _collect_events(self):
        """
        grab all Event instances for this cloud
        """
        self.log.info('Starting collecting Events for all sites in cloud %s.' %self.name)
        event_d = {} 
        for sitename, site in self.site_d.items():
            event_l = site._collect_events()
            if event_l:
                event_d[sitename] = event_l
        self.log.info('Collected events for cloud %s: %s' %(self.name, event_d))
        return event_d


    def __build_body(self, event_d):
        """
        compose the body for the email notification
        :param dict event_d: dictionary of Events per Site
        """
        body = 'Dear %s Cloud Support,\n' %self.name
        body += '    Please note that following PanDA Site IDs have been excluded/recovered by the AutoExclusion tool.\n'
        body += '    Note that manual status settings in AGIS may override the status set here.\n\n\n'
        for sitename, event_l in event_d.items():
            body += '    Site %s:\n' % sitename
            for event in event_l:
                body += '    SiteID: %s\n' %sitename
                body += '    SiteID: %s\n' %sitename
                body += '    Reason:\n'
                body += '       '
            body += '\n\n'

        return body



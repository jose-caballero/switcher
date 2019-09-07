#!/usr/bin/env python

import json
import logging
import time
import urllib
import urllib2
from pprint import pprint as pp

from switcher.downtime import Downtime
from switcher.agistopology.topology import Topology
from switcher.topology.cloud import CloudSwitcher
from switcher.topology.site import SiteSwitcher
from switcher.topology.queue import QueueSwitcher
from switcher.topology.ce import CESwitcher
from switcher.topology.ddm import DDMSwitcher
from switcher.utils import load_json

"""

     +--------+            
     |Topology|<*>------+-------------+-------------+------------+----------+
     +--------+         |             |             |            |          |
         ^              V             V             V            V          V
         |           +-----+        +----+       +-----+       +--+       +---+
         |           |Cloud|<*>---->|Site|<*>--->|Queue|<*>--->|CE|<*>--->|DDM|
         |           +-----+        +----+       +-----+       +--+       +---+
         |              ^             ^             ^            ^          ^
         |              |             |             |            |          |
         |              |             |             |            |          |
         |           +------+       +-----+      +------+      +---+      +----+
         |           |CloudS|<*>--->|SiteS|<*>-->|QueueS|<*>-->|CES|<*>-->|DDMS|
         |           +------+       +-----+      +------+      +---+      +----+
         |              ^             ^             ^            ^          ^
     +---------+        |             |             |            |          |
     |TopologyS|<*>-----+-------------+-------------+------------+----------+
     +---------+            

"""


class TopologySwitcher(Topology):

    def __init__(self, schedconfig, ddmtopology, notificationsconf, downtimesconf):
        """
        """
        self.notificationsconf = notificationsconf
        self.downtimesconf = downtimesconf 
        super(TopologySwitcher, self).__init__(schedconfig, ddmtopology)
        self.log = logging.getLogger('switcher')
        self.downtime_l = []
        self.log.debug('Object TopologySwitcher created.')

    # -------------------------------------------------------------------------
    # inherit the entities from agistopology

    def _getNextCloud(self, cloudname):
        return CloudSwitcher(cloudname, self.notificationsconf)
 
    def _getNextSite(self, sitename):
        return SiteSwitcher(sitename)
 
    def _getNextQueue(self, panda_resource, qdata):
        return QueueSwitcher(panda_resource, qdata, self.downtimesconf)
 
    def _getNextCE(self, ce_endpoint):
        return CESwitcher(ce_endpoint, self.downtimesconf)
 
    def _getNextDDM(self, endpoint):
        return DDMSwitcher(endpoint)

    # --------------------------------------------------------------------------

    def add_switcher_status(self, source):
        """
        adds the status in Switcher to the queues
        """
        self.log.debug('Starting.')
        data = load_json(source)
        for qname, info in data.items():
            queue = self.queue_d[qname]
            queue.switcher_status = info['a']['status']['value']
        self.log.debug('Leaving.')

    # --------------------------------------------------------------------------

    def add_downtimes(self, source):
        """
        adds downtimes items to CEs and DDMs entities
        """
        self.log.debug('Starting.')
        data = load_json(source)
        for site, info in data.items():
            self.log.info('Processing site %s' %site)
            try:
                for section in info:
                    service_l = section['services']
                    for service in service_l:
                        type = service['type']
                        if type in ['CE', 'SRM']:
                            endpoint = service['endpoint']
                            self.log.info('Creating Downtime object for endpoint %s' %endpoint)
                            downtime = Downtime(
                                    endpoint = endpoint,
                                    start_time = section['start_time'],
                                    end_time = section['end_time'],
                                    site = site,
                                    type = type,
                                    name = service['name']
                                    )

                            # check this downtime is still valid, just in case 
                            if downtime.end_time_sec <= int(time.time()):
                                self.log.info('Downtime rejected, it finished already')
                            else:
                                if downtime not in self.downtime_l:
                                    if type == 'CE':
                                        ce = self.ce_d.get(endpoint, None)
                                        if ce:
                                            self.log.info('Adding downtime to CE %s' %endpoint)
                                            ce.downtime_l.append(downtime)
                                        else:
                                            self.log.warning('The CE %s is not in the Topology' %endpoint)
                                    if type == 'SRM':
                                        ddm = self.ddm_d.get(endpoint, None)
                                        if ddm:
                                            self.log.info('Adding downtime to DDM %s' %endpoint)
                                            ddm.downtime_l.append(downtime)
                                        else:
                                            self.log.warning('The DDM %s is not in the Topology' %endpoint)
                                    self.downtime_l.append(downtime)

            except Exception as ex:
                self.log.error("Got exception %s" %ex)
        self.log.debug('Leaving.')


# -----------------------------------------------------------------------------

    def evaluate(self):
        """
        triggers the evaluation of all registered downtimes
        for all entitites in the Topology, 
        to check with ones need to change status
        """
        self.log.info('Evaluating all entities.')
        for cloudname, cloud in self.cloud_d.items():
            cloud.evaluate()
        self.log.info('Leaving.')


    def collect_events(self):
        """
        collect all changing status events for each cloud
        """
        self.log.info('Collecting events for all clouds.')
        for cloudname, cloud in self.cloud_d.items():
            cloud.collect_events()
        self.log.info('Leaving.')


    def notify(self):
        """
        notify the clouds in case of changes
        """
        self.log.info('Checking all clouds.')
        for cloudname, cloud in self.cloud_d.items():
            cloud.notify()
        self.log.info('Leaving.')



# =============================================================================

if __name__ == '__main__':
    topology = Topology('../inputs/schedconfig.json', '../inputs/ddm_topology.json')

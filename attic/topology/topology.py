#!/usr/bin/env python

import logging
import time

from switcher.agistopology.topology import AGISTopology
from switcher.downtime import Downtime, get_downtimes
from switcher.topology.cloud import Cloud
from switcher.topology.site import Site
from switcher.topology.queue import Queue
from switcher.topology.ce import CE, CEHandler
from switcher.topology.ddm import DDM
from switcher.utils import load_json



class Topology(AGISTopology):

    def __init__(self, schedconfig, ddmtopology, notificationsconf, downtimesconf):
        """
        """
        self.notificationsconf = notificationsconf
        self.downtimesconf = downtimesconf 
        super(Topology, self).__init__(schedconfig, ddmtopology)
        self.log = logging.getLogger('switcher')
        self.downtime_l = []
        self.log.debug('Object TopologySwitcher created.')

    # -------------------------------------------------------------------------
    # inherit the entities from agistopology

    def _getNextCloud(self, cloudname):
        return Cloud(cloudname, self.notificationsconf)
 
    def _getNextSite(self, sitename):
        return Site(sitename)
 
    def _getNextQueue(self, panda_resource, qdata):
        return Queue(panda_resource, qdata, self.downtimesconf)
 
    def _getNextCE(self, ce_endpoint):
        return CE(ce_endpoint, self.downtimesconf)
 
    def _getNextDDM(self, endpoint):
        return DDM(endpoint)

    def _get_cehandler(self):
        return CEHandler()


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
        downtime_l = get_downtimes(data)
        for downtime in downtime_l:
            self.__add_a_downtime(downtime)
        self.log.debug('Leaving.')


    def __add_a_downtime(self, downtime):
        """
        stores a single Downtime instance
        """
        endpoint = downtime.endpoint
        # check this downtime is still valid, just in case 
        ###if downtime.end_time_sec <= int(time.time()):
        ###if downtime.timeinterval.end_t <= int(time.time()):
        if downtime.expired():
            self.log.info('Downtime rejected, it finished already')
        else:
            if downtime not in self.downtime_l:

                if type == 'CE':
                    ce = self.ce_d.get(endpoint, None)
                    if ce:
                        self.log.info('Adding downtime to CE %s' %endpoint)
                        ###ce.downtime_l.append(downtime)
                        ce.add_downtime(downtime)
                    else:
                        self.log.warning('The CE %s is not in the Topology' %endpoint)
        
                if type == 'SRM':  # FIXME, only SRM ????
                    ddm = self.ddm_d.get(endpoint, None)
                    if ddm:
                        self.log.info('Adding downtime to DDM %s' %endpoint)
                        ###ddm.downtime_l.append(downtime)
                        ddm.add_downtime(downtime)
                    else:
                        self.log.warning('The DDM %s is not in the Topology' %endpoint)

                self.downtime_l.append(downtime)

    # --------------------------------------------------------------------------

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


    def act(self, agisapi):
        """
        acts to change status of entities, based on the result
        of the evaluate() call.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting over all entities.')
        for cloudname, cloud in self.cloud_d.items():
            cloud.act(agisapi)
        self.log.info('Leaving.')


    # --------------------------------------------------------------------------

    def notify(self, email):
        """
        notify the clouds in case of changes
        """
        self.log.info('Notifying all clouds.')
        for cloudname, cloud in self.cloud_d.items():
            cloud.notify(email)
        self.log.info('Leaving.')


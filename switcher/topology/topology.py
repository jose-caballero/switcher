#!/usr/bin/env python

import logging
import time

from switcher.agistopology.topology import AGISTopology
from switcher.switcherexceptions import SwitcherConfigurationFailure
from switcher.downtime import Downtime, get_downtimes
from switcher.topology.cloud import Cloud
from switcher.topology.site import Site
from switcher.topology.queue import Queue
from switcher.topology.ce import CE, CEHandler
from switcher.topology.ddm import DDM
from switcher.utils import load_json



class Topology(AGISTopology):

    # FIXME
    # passing allow_only and excluded_queues should be done in a better way
    # this is a temporary solution
    def __init__(self, schedconfig, allowed_clouds, allowed_sites, allowed_queues, ddmtopology, notificationsconf, downtimesconf):
        """
        """
        self.notificationsconf = notificationsconf
        self.downtimesconf = downtimesconf 
        super(Topology, self).__init__(schedconfig, allowed_clouds, allowed_sites, allowed_queues, ddmtopology)
        self.log = logging.getLogger('topology')
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

        the content of the source data looks like this:

                  "AGLT2_LMEM_SL7-condor": {
                    "a": {
                      "mode": {
                        "AUTO": {
                          "hammercloud": {
                                ...
                                ...
                          },
                          "switcher": {
                                ...
                                ...
                            "value": "ONLINE"
                          }
                        }
                                        

        IMPORTANT NOTE: it is possible, depending of which source of data is 
                        being used, that not all ATLAS queues are part of it. 
                        For example, when restricting the query of 
                                /pandastatus/
                        to AGIS with the constrain 
                                probe=switcher
                        then, only a handful of queues are in the source
                        (those which latest probe was switcher)
        """
        self.log.debug('Starting.')
        try:
            data = load_json(source)
        except Exception as ex:
            self.log.critical('Unable to read switcher status configuration from src. Exception: %s' %ex)
            raise SwitcherConfigurationFailure(source, ex)
        for qname, info_d in data.items():
            self.log.debug('Processing queue %s' %qname)
            queue = self.queue_d.get(qname, None)
            if queue:
                for mode, probes_d in info_d['a']['mode'].items():
                    if 'switcher' in probes_d.keys():
                        switcher_status = probes_d['switcher']['value']
                        switcher_status = switcher_status.lower()
                        if switcher_status not in ['online', 'offline', 'brokeroff']:
                            # we check for weird unexpected values set manually in AGIS
                            switcher_status = 'unrecognized'
                        self.log.debug('Assigning status %s to queue %s' %(switcher_status, qname))
                        queue.switcher_status = switcher_status
            else:
                self.log.warning('Queue %s is not in the Topology. Skipping it.' %qname)
        self.log.debug('Leaving.')

    # --------------------------------------------------------------------------

    def add_downtimes(self, source):
        """
        adds downtimes items to CEs and DDMs entities
        """
        self.log.debug('Starting.')
        try:
            data = load_json(source)
        except Exception as ex:
            self.log.critical('Unable to read donwtimes configuration from src. Exception: %s' %ex)
            raise SwitcherConfigurationFailure(source, ex)
        downtime_l = get_downtimes(data)
        self.log.debug('Downtimes: %s' %downtime_l)
        for downtime in downtime_l:
            self.__add_a_downtime(downtime)
        self.log.debug('Leaving.')


    def __add_a_downtime(self, downtime):
        """
        stores a single Downtime instance
        """
        self.log.debug('Starting.')
        endpoint = downtime.endpoint
        # check this downtime is still valid, just in case 
        ###if downtime.end_time_sec <= int(time.time()):
        ###if downtime.timeinterval.end_t <= int(time.time()):
        if downtime.severity == 'WARNING':
            self.log.warning('Severity level for this downtime is WARNING. Ignoring it.')
        elif downtime.expired():
            self.log.warning('Downtime finished already. Ignoring it.')
        else:
            if downtime not in self.downtime_l:

                if downtime.type == 'CE':
                    ce = self.ce_d.get(endpoint, None)
                    if ce:
                        self.log.info('Adding downtime to CE %s' %endpoint)
                        ###ce.downtime_l.append(downtime)
                        ce.add_downtime(downtime)
                    else:
                        self.log.warning('The CE %s is not in the Topology. Skipping it.' %endpoint)

        
                if downtime.type == 'SRM':  # FIXME, only SRM ????
                    ddm = self.ddm_d.get(endpoint, None)
                    if ddm:
                        self.log.info('Adding downtime to DDM %s' %endpoint)
                        ###ddm.downtime_l.append(downtime)
                        ddm.add_downtime(downtime)
                    else:
                        self.log.warning('The DDM %s is not in the Topology. Skipping it.' %endpoint)

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
            self.log.info('Evaluating cloud %s.' %cloudname)
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
            self.log.info('Acting on cloud %s.' %cloudname)
            cloud.act(agisapi)
        self.log.info('Leaving.')


    # --------------------------------------------------------------------------

    def reevaluate(self, schedconfig):
        """
        check the actual final status of the panda queues.
        If a queue still have a value different that the new Switcher value, 
        a WARNING message will be added to the email notifications
        :param schedconfig: url or path to the sched config data

        FIXME ?
        Maybe the right way of doing this is to create a second whole Topology tree, 
        and merge it against the current one.
        For example, Topology.reevaluate() calls Topology.update(newtopology)
                     -> Cloud.update(newtopology) 
                     -> Site.update(newtopology) 
                     -> Queue.update(newtopology) 
        and the value of queue_final_status is assigned 
        to self.event in Queue.update()
        """
        self.log.info('Starting.')
        new_schedconfig_data = load_json(schedconfig)

        for qname, queue in self.queue_d.items():
            self.log.debug('considering queue %s for reevaluation' %qname)
            if queue.event:
                self.log.debug('queue %s is candidate for reevaluation' %qname)
                final_status = new_schedconfig_data[qname]['status']
                self.log.debug('final status for queue %s is %s' %(qname, final_status))
                queue.event.queue_final_status = final_status

        self.log.info('Leaving.')


    def notify(self, email):
        """
        notify the clouds in case of changes
        """
        self.log.info('Notifying all clouds.')
        for cloudname, cloud in self.cloud_d.items():
            self.log.info('Notifying cloud %s.' %cloudname)
            cloud.notify(email)
        self.log.info('Leaving.')


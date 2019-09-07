#!/usr/bin/env python

import json
import logging
import time
import urllib
import urllib2
from pprint import pprint as pp

from switcher.switcherexceptions import SwitcherConfigurationFailure
from switcher.agistopology.cloud import AGISCloud
from switcher.agistopology.site import AGISSite 
from switcher.agistopology.queue import AGISQueue 
from switcher.agistopology.ce import AGISCE, AGISCEHandler
from switcher.agistopology.ddm import AGISDDM
from switcher.downtime import Downtime
from switcher.utils import load_json

# =============================================================================

class AGISTopology(object):

    def __init__(self, schedconfig, allowed_clouds, allowed_sites, allowed_queues, ddm_topology=None):
        """
        """

        self.log = logging.getLogger('agistopology')

        self.cloud_d = {}
        self.site_d = {}
        self.queue_d = {}
        self.ce_d = {}
        self.ddm_d = {}

        self.allowed_clouds = allowed_clouds
        self.allowed_sites = allowed_sites
        self.allowed_queues = allowed_queues
        # build the topology 
        self.__build_topology_from_schedconfig(schedconfig)
        self.__add_ddm_to_topology(ddm_topology)
        self.log.debug('Object Topology created.')

    # -------------------------------------------------------------------------
    
    def _get_cloud(self, cloudname):
        self.log.debug('Starting.')
        if cloudname not in self.cloud_d.keys():
            self.log.info('Instantiating a new Cloud object for %s' %cloudname)
            self.cloud_d[cloudname] = self._getNextCloud(cloudname)
        self.log.debug('Leaving, returning Cloud object for %s.'%cloudname)
        return self.cloud_d[cloudname]

    def _getNextCloud(self, cloudname):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return AGISCloud(cloudname)

    # -------------------------------------------------------------------------

    def _get_site(self, sitename):
        self.log.debug('Starting.')
        if sitename not in self.site_d.keys():
            self.log.info('Instantiating a new Site object for %s' %sitename)
            self.site_d[sitename] = self._getNextSite(sitename)
        self.log.debug('Leaving, returning Site object for %s.'%sitename)
        return self.site_d[sitename]

    def _getNextSite(self, sitename):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return AGISSite(sitename)

    # -------------------------------------------------------------------------

    def _get_queue(self, qname, panda_resource, qdata):
        self.log.debug('Starting.')
        if qname not in self.queue_d.keys():
            self.log.info('Instantiating a new Queue object for %s' %qname)
            self.queue_d[qname] = self._getNextQueue(panda_resource, qdata)
        self.log.debug('Leaving, returning Queue object for %s.'%qname)
        return self.queue_d[qname]

    def _getNextQueue(self, panda_resource, qdata):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return AGISQueue(panda_resource, qdata)

    # -------------------------------------------------------------------------

    def _get_ce(self, ce_endpoint):
        self.log.debug('Starting.')
        if ce_endpoint not in self.ce_d.keys():
            self.log.info('Instantiating a new CE object for %s' %ce_endpoint)
            self.ce_d[ce_endpoint] = self._getNextCE(ce_endpoint)
        self.log.debug('Leaving, returning CE object for %s.'%ce_endpoint)
        return self.ce_d[ce_endpoint]

    def _getNextCE(self, ce_endpoint):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return AGISCE(ce_endpoint)

    # -------------------------------------------------------------------------

    def _get_ddm(self, endpoint):
        self.log.debug('Starting.')
        if endpoint not in self.ddm_d.keys():
            self.log.info('Instantiating a new DDM object for %s' %endpoint)
            self.ddm_d[endpoint] = self._getNextDDM(endpoint)
        self.log.debug('Leaving, returning DDM object for %s.'%endpoint)
        return self.ddm_d[endpoint]

    def _getNextDDM(self, endpoint):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return AGISDDM(endpoint)

    # -------------------------------------------------------------------------

    def __build_topology_from_schedconfig(self, schedconfig):
        """
        builds the ATLAS topology from AGIS schedconfig
        """
        self.log.debug('Starting.')
        try:
            self.schedconfig_data = load_json(schedconfig)
        except Exception as ex:
            self.log.critical('Unable to read queues configuration from src. Exception: %s' %ex)
            raise SwitcherConfigurationFailure(schedconfig, ex)
               
        for qname, qdata in self.schedconfig_data.items():
            self.log.info('Processing queue %s' %qname)
            try:
                self.__build_topology_queue(qname, qdata)
            except Exception as ex:
                self.log.error('Failure processing queue %s: %s' %(qname, ex))

        self.log.debug('Leaving.')


    def __build_topology_queue(self, qname, qdata):
        """
        process each queue from schedconfig
        """
        vo = qdata['vo_name']
        if vo != 'atlas':
            self.log.warning('queue %s does not belong to ATLAS. Skipping it.' %vo)
            return

        cloud = self.__build_cloud(qdata)
        if cloud:
            site = self.__build_site(qdata)
            if site:
                cloud.site_d[site.name] = site
                queue = self.__build_queue(qname, qdata)
                if queue:
                    site.queue_d[qname] = queue


    def __build_cloud(self, qdata):
        """
        get the Cloud object for this queue
        """
        cloudname = qdata['cloud']
        if cloudname not in self.allowed_clouds:
            self.log.warning('cloud %s is excluded. Skipping it.' %cloudname)
            return None
        else:
            self.log.info('Processing cloud %s' %cloudname)
            cloud = self._get_cloud(cloudname)
            #cloud._read_config_parameters()
            return cloud


    def __build_site(self, qdata):
        """
        get ths Site object for this queue
        """
        sitename = qdata['atlas_site']
        if sitename not in self.allowed_sites:
            self.log.warning('site %s is excluded. Skipping it.' %sitename)
            return None
        else:
            self.log.info('Processing site %s' %sitename)
            site = self._get_site(sitename)
            return site


    def __build_queue(self, qname, qdata):
        """
        creates the Queue object
        """
        if qname not in self.allowed_queues:
            self.log.warning('queue %s is excluded. Skipping it.' %qname)
            return None
        else:
            panda_resource = qdata['panda_resource']
            self.log.info('Processing queue %s' %panda_resource)
            queue = self._get_queue(qname, panda_resource, qdata)
            queue.probe = qdata['probe']
            #queue.configure(qdata)
            #queue._read_config_parameters()

            # get the CEs 
            queue_l = qdata['queues']
            for q in queue_l:
                ce_name = q['ce_name']
                ce_endpoint = q['ce_endpoint']
                self.log.info('Processing ce %s' %ce_endpoint)
                ce = self._get_ce(ce_endpoint)
    
                #queue.ce_d[ce_endpoint] = ce
                #queue.cehandler.add(ce)
                queue.add_ce(ce)

                ce.name = ce_name 
                ce.state = q['ce_state']
                #ce._read_config_parameters()
            return queue



    def __add_ddm_to_topology(self, ddm_topology):
        """
        Add DDM Endpoints to the topology
        Steps:
            for each queue:
                1. find the space token
                2. check if that token is in DDM Topology
                3. if token is in DDM Topology:
                    3.1 check if there is an endpoint in 
                        write_lan block for that token
                    3.2 if not, check if there is an endpoint 
                        in write_wan block for that token
                4. associate whatever endpoint found
                   to the queue
        """
        self.log.debug('Starting.')
        try:
            ddm_topology_data = load_json(ddm_topology)
        except Exception as ex:
            self.log.critical('Unable to read ddm configuration from src. Exception: %s' %ex)
            raise SwitcherConfigurationFailure(ddm_topology, ex)
        for queue in self.queue_d.values():
            self.__add_ddm_to_queue(queue, ddm_topology_data)
        self.log.debug('Leaving.')


    def __add_ddm_to_queue(self, queue, ddm_topology_data):
        """
        add ddm endpoints to a given queue
        """
        self.log.debug('Processing queue %s' %queue.name)
        token = self.__find_token(queue, ddm_topology_data)       # step 1. & 2.
        if not token:
            return
        endpoint = self.__find_endpoint(token, ddm_topology_data) # step 3.
        if not endpoint:
            return
        self.__associate_ddm_to_queue(queue, token, endpoint)     # step 4.
        self.log.debug('Leaving.')


    def __find_token(self, queue, ddm_topology_data):
        """
        find if the queue has a spacetoken
        """
        if not queue.token:
            self.log.info('Queue %s has no token. Skipping.' %queue.name)
            return None

        token = queue.token
        self.log.info('Token for queue %s is %s' %(queue.name, token))

        # step 2.
        if token not in ddm_topology_data.keys():
            self.log.info('Token %s is not in DDM endpoints source. Skipping.' %token)
            return None

        return token


    def __find_endpoint(self, token, ddm_topology_data):
        """
        find if there is a valid endpoint
        """

        data = ddm_topology_data[token]
        arprotocols = data['arprotocols']
        if 'write_lan' in arprotocols.keys():
            endpoint = arprotocols['write_lan'][0]['endpoint']
            self.log.info('Endpoint from write_lan: %s' %endpoint)
            return endpoint
        elif 'write_wan' in arprotocols.keys():
            endpoint = arprotocols['write_wan'][0]['endpoint']
            self.log.info('Endpoint from write_wan: %s' %endpoint)
            return endpoint
        else:
            self.log.info('There is neither write_lan nor write_wan section in "arprotocols" for token %s.' %token)
            return None 


    def __associate_ddm_to_queue(self, queue, token, endpoint):
        """
        set the DDM object for queue
        """
        ddm = self._get_ddm(endpoint)
        ddm.token = token
        self.ddm_d[endpoint] = ddm
        ###queue.ddm = ddm
        queue.add_ddm(ddm)


    # --------------------------------------------------------------------------

    def add_nucleus(self, sites):
        """
        checks which site is a nucleus and which one is not
        """
        self.log.debug('Starting.')
        try:
            data = load_json(sites)
        except Exception as ex:
            self.log.critical('Unable to read sites configuration from src. Exception: %s' %ex)
            raise SwitcherConfigurationFailure(sites, ex)

        for siteinfo in data:
            sitename = siteinfo['name']
            if 'Nucleus' in siteinfo['datapolicies']:
                site = self.site_d.get(sitename, None)
                if site:
                    #self.site_d[sitename].nucleus = True
                    site.nucleus = True
                else:
                    self.log.warning('Site %s is not in the Topology. Skipping it.' %sitename)

        self.log.debug('Leaving.')

    # --------------------------------------------------------------------------

    def __str__(self):
        """
        ancillary method to get a friendly, easy to read, 
        representation of the topology
        """
        str = 'Topology:\n'
        for cloud in self.cloud_d.values():
            str += '    %s' %cloud
        return str


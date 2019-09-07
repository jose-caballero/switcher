#!/usr/bin/env python

import json
import logging
import time
import urllib
import urllib2
from pprint import pprint as pp

from switcher.agistopology.cloud import Cloud
from switcher.agistopology.site import Site 
from switcher.agistopology.queue import Queue 
from switcher.agistopology.ce import CE
from switcher.agistopology.ddm import DDM
from switcher.downtime import Downtime
from switcher.utils import load_json

# =============================================================================

class Topology(object):
    """
                                                +--------+    
                                                |Topology|
                                                +--------+
                                                  |  | |
                                                  |  | |
                                    +-------------+  | |
                                    |          +-----+ +---------+
                                    |          |                 |
                                    |          |                 |
                                 +-----+   +-----+            +-----+
                                 |Cloud|   |Cloud|    ...     |Cloud|
                                 +-----+   +-----+            +-----+
                                  | | |
                                  | | |
                         +--------+ | +----------+
                         |          |            |
                         |          |            |
                      +----+     +----+        +----+
                      |Site|     |Site|  ...   |Site|
                      +----+     +----+        +----+
                       | ||                       |
                       | ||                       |
              +--------+ |+---------------+       +-------+
              |          |                |               |
              |          |                |               |
           +-----+     +-----+         +-----+         +-----+
           |Queue|     |Queue|   ...   |Queue|         |Queue|
           +-----+     +-----+         +-----+         +-----+
            |  |         |  |             |               |
            |  |         |  |             |               |
     +------+  +-+ +-----+  |             +------+ +------+
     |           | |        |                    | | 
     |           | |        |                    | |
    +--+        +--+      +--+                  +---+
    |CE|  ...   |CE|      |CE|                  |DDM|
    +--+        +--+      +--+                  +---+

    """

    def __init__(self, schedconfig=None, ddm_topology=None):
        """
        class to build the ATLAS topology from AGIS configuration. 
        This class does not perform any action after topology is built.
        In order to add functionalities to the topology, 
        a new child class needs to be used that inherits from this one:

                class UsefulTopology(Topology)

        This class holds the following dictionaries 
        
                self.cloud_d = {}
                self.site_d = {}
                self.queue_d = {}
                self.ce_d = {}
                self.ddm_d = {}

        The dictionary index is the Unique ID that indetifies each 
        entity. For example, the Cloud name, or the CE endpoint.
        
        These dictionaries have two purposes:
        
            -- it makes easier to find a given entity by its unique ID
               This way, to find a given entity, there is no need to 
               search the entire tree to find it
            
            -- second reason is to make sure there is only one instance
               of each entity with the same ID. 
               When a new entity is requested, if its ID is already a key
               in the corresponding dictionary, 
               the existing object is returned.
               Otherwise, a new object is created, and added to the 
               dictionary.
               In other words, the dictionaries are used to ensure all
               entities are Singletons. 
               One example is a CE object that serves multiple Queues. 
               We only want one instance of that CE, not many.

        For the second purpose explained above, when a new instance of an 
        entity is requested, a method _get_XYZ() is called:

                self._get_cloud()
                self._get_site()
                self._get_queue()
                self._get_ce()
                self._get_ddm()

        Those methods, if a truly new instance is needed, 
        will issue a new call:

                self._getNextCloud()
                self._getNextSite()
                self._getNextQueue()
                self._getNextCE()
                self._getNextDDM()

        These _getNextXYZ() need to be overriden by classes that inherit
        from this one, in order to make sure they use the right code for 
        clouds, sites, queues, etc.
        """

        self.log = logging.getLogger('agistopology')

        self.cloud_d = {}
        self.site_d = {}
        self.queue_d = {}
        self.ce_d = {}
        self.ddm_d = {}

        # build the topology 
        self.__build_topology_from_schedconfig(schedconfig)
        self.__add_ddm_to_topology(ddm_topology)
        self.log.debug('Object Topology created.')

    # -------------------------------------------------------------------------
    
    def _get_cloud(self, cloudname):
        if cloudname not in self.cloud_d.keys():
            self.cloud_d[cloudname] = self._getNextCloud(cloudname)
        return self.cloud_d[cloudname]

    def _getNextCloud(self, cloudname):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return Cloud(cloudname)

    # -------------------------------------------------------------------------

    def _get_site(self, sitename):
        if sitename not in self.site_d.keys():
            self.site_d[sitename] = self._getNextSite(sitename)
        return self.site_d[sitename]

    def _getNextSite(self, sitename):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return Site(sitename)

    # -------------------------------------------------------------------------

    def _get_queue(self, qname, panda_resource, qdata):
        if qname not in self.queue_d.keys():
            self.queue_d[qname] = self._getNextQueue(panda_resource, qdata)
        return self.queue_d[qname]

    def _getNextQueue(self, panda_resource, qdata):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return Queue(panda_resource)

    # -------------------------------------------------------------------------

    def _get_ce(self, ce_endpoint):
        if ce_endpoint not in self.ce_d.keys():
            self.ce_d[ce_endpoint] = self._getNextCE(ce_endpoint)
        return self.ce_d[ce_endpoint]

    def _getNextCE(self, ce_endpoint):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return CE(ce_endpoint)

    # -------------------------------------------------------------------------

    def _get_ddm(self, endpoint):
        if endpoint not in self.ddm_d.keys():
            self.ddm_d[endpoint] = self._getNextDDM(endpoint)
        return self.ddm_d[endpoint]

    def _getNextDDM(self, endpoint):
        """
        To implement inheritance, 
        override this method in the child class
        """
        return DDM(endpoint)

    # -------------------------------------------------------------------------

    def __build_topology_from_schedconfig(self, schedconfig):

        if schedconfig:
            self.schedconfig = schedconfig
        else:
            self.schedconfig = 'http://atlas-agis-api.cern.ch/request/pandaqueue/query/list/?json&preset=schedconf.all'
        self.schedconfig_data = load_json(self.schedconfig)
               
        for qname, qdata in self.schedconfig_data.items():

            # get the cloud
            cloudname = qdata['cloud']
            cloud = self._get_cloud(cloudname)
            #cloud._read_config_parameters()

            # get the site
            sitename = qdata['atlas_site']
            site = self._get_site(sitename)
            cloud.site_d[sitename] = site

            # get the queue
            panda_resource = qdata['panda_resource']
            queue = self._get_queue(qname, panda_resource, qdata)
            site.queue_d[qname] = queue
            #queue.configure(qdata)
            #queue._read_config_parameters()

            # get the CEs 
            queue_l = qdata['queues']
            for q in queue_l:
                ce_name = q['ce_name']
                ce_endpoint = q['ce_endpoint']
                ce = self._get_ce(ce_endpoint)
                queue.ce_d[ce_endpoint] = ce
                ce.name = ce_name 
                ce.status = q['ce_state']
                #ce._read_config_parameters()


###    def __add_ddm_to_topology(self, ddm_topology):
###
###        if ddm_topology:
###            self.ddm_topology = ddm_topology
###        else:
###            self.ddm_topology = 'http://atlas-agis-api.cern.ch/request/ddmendpoint/query/list/?json&preset=dict'
###        self.ddm_topology_data = load_json(self.ddm_topology)
###
###        ddm_l = []
###        
###        for token, data in self.ddm_topology_data.items():
###            if data['type'] == 'DATADISK':
###                rprotocols = data['rprotocols']
###                for id, protocol_data in rprotocols.items():
###                    try:
###                        if 'write_lan' in protocol_data['activities']:
###                            if protocol_data['flavour'] in ['SRM', 'SRMv2']:
###                                endpoint = protocol_data['endpoint']
###                                #ddm = DDM(endpoint) 
###                                ddm = self._get_ddm(endpoint)
###                                ddm.token = token
###                                #ddm.site = data['site']
###                                ddm_l.append(ddm)
###                    except:
###                       pass
###
###        for queue in self.queue_d.values():
###            for ddm in ddm_l:
###                if ddm.token in queue.tokens:
###                    queue.ddm = ddm
###                    self.ddm_d[ddm.endpoint] = ddm


    def __add_ddm_to_topology(self, ddm_topology):
        """
        """
        self.ddm_topology_data = load_json(ddm_topology)

        for queue in self.queue_d.values():
            if not queue.token:
                #FIXME : log message
                continue
            token = queue.token
            if token not in self.ddm_topology_data.keys():
                #FIXME : log message
                continue
            data = self.ddm_topology_data[token]
            arprotocols = data['arprotocols']
            if 'write_lan' in arprotocols.keys():
                endpoint = arprotocols['write_lan'][0]['endpoint']
            elif 'write_wan' in arprotocols.keys():
                endpoint = arprotocols['write_wan'][0]['endpoint']
            else:
                #FIXME : log message
                continue 
            ddm = self._get_ddm(endpoint)
            ddm.token = token
            self.ddm_d[endpoint] = ddm
            queue.ddm = ddm


    # --------------------------------------------------------------------------

    def add_nucleus(self, sites):
        """
        checks which site is a nucleus and which one is not
        """
        data = load_json(sites)
        for siteinfo in data:
            sitename = siteinfo['name']
            if 'Nucleus' in siteinfo['datapolicies']:
                self.site_d[sitename].nucleus = True


# =============================================================================

if __name__ == '__main__':
    topology = Topology('../inputs/schedconfig.json', '../inputs/ddm_topology.json')

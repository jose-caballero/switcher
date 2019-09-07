#!/usr/bin/env python 

import json
import urllib
import urllib2
from pprint import pprint as pp

from lib.topology import *

class Topology(object):

    def __init__(self):
        self.cloudhandler = CloudHandler()
        self.ce_d = {}
        self.ddm_d = {}

    def get_topology(self):
        URL = "http://atlas-agis-api.cern.ch/request/pandaqueue/query/list/?json&preset=schedconf.all"
        self.agis_data = json.load(urllib2.urlopen(URL))        
        for queue, data in self.agis_data.items():

            cloud = data['cloud']
            #print cloud
            ###cloud = cloudhandler.get(cloud)
            cloud = self.cloudhandler.get(cloud)

            sitename = data['atlas_site']
            atlassite = atlassitehandler.get(sitename)
            cloud.add_site(atlassite)

            pandaqueue = PandaQueue(queue)
            pandaqueue.set(data)
            atlassite.add_pandaqueue(pandaqueue)

            for ce in pandaqueue.ce_l:
               if ce.endpoint not in self.ce_d.keys():
                   self.ce_d[ce.endpoint] = []
               self.ce_d[ce.endpoint].append(ce)
    
    
    def add_switcher_status(self):
        #SWITCHER_STATUS_URL = 'http://atlas-agis-api.cern.ch/request/pandaqueuestatus/query/list/?json&probe=switcher'
        #data = json.load(urllib.urlopen(SWITCHER_STATUS_URL))
        data = json.load(open('switcher_status.json'))        

        for panda_queue, info in data.items():
            panda_queue = find_panda_queue(panda_queue)
            panda_queue.switcher_status = info['a']['status']['value']
    
    
    def add_ddm(self):
    
        # URL = http://atlas-agis-api.cern.ch/request/ddmendpoint/query/list/?json&preset=dict
        ddm_endpoint_filename = 'ddm_endpoints_dict.json'
        ddm_endpoint_f = open(ddm_endpoint_filename)
        ddm_endpoint_data = json.load(ddm_endpoint_f)
        
        ddm_l = []
        
        for token, data in ddm_endpoint_data.items():
            if data['type'] == 'DATADISK':
                rprotocols = data['rprotocols']
                for id, protocol_data in rprotocols.items():
                    try:
                        # ========================================================================
                        # FIXME
                        # what to do if there is no "write_lan" in ddm json, but that token
                        # is in write_lan in schedconfig ???
                        # ========================================================================
                        if 'write_lan' in protocol_data['activities']:
                            if protocol_data['flavour'] in ['SRM', 'SRMv2']:
                                #print token, protocol_data['endpoint'], data['site']
                                ddm = DDM(
                                    endpoint = protocol_data['endpoint'],
                                    site = data['site'],
                                    token = token
                                )
                                ddm_l.append(ddm)
                    except:
                        pass
        
        
        for queue, data in self.agis_data.items():
            site = data['atlas_site'] 
            try:
                #tokens = data['astorages0']['write_lan'][site]
                site, tokens = data['astorages0']['write_lan'].items()[0]
        
            #print tokens
                for ddm in ddm_l:
                    if ddm.site == site:
                        if ddm.token in tokens:
                            #print site, queue, ddm.token
                            pandaqueue = find_panda_queue(queue)
                            #print pandaqueue.name
                            pandaqueue.set_ddm(ddm)
       
                            if ddm.endpoint not in self.ddm_d.keys():
                                self.ddm_d[ddm.endpoint] = []
                            self.ddm_d[ddm.endpoint].append(ddm)
                        
        
            except:
                pass
        

    def check(self):
        self.cloudhandler.check()


def add_downtimes(topology):
    #
    # FIXME : missing taking into account severity and excluding SRM.nearline
    #
#    URL = 'http://atlas-agis-api.cern.ch/request/downtime/query/list/?json&filter=henceforward'
#    data = json.load(urllib.urlopen(URL))
#    for sitename, info in data.items():
#        for service in info[0]['services']:
#            if service['type'] in ['CE', 'SRM']:
#                atlassite = atlassitehandler.get(sitename)
#                atlassite.add_downtime(service)

    downtimes_filename = 'downtimes_from_agis.json'
    downtimes_f = open(downtimes_filename)
    downtimes_data = json.load(downtimes_f)
    
    from lib.downtime import Downtime
    
    downtime_l = []
    
    for site, info in downtimes_data.items():
        #print site
        #pp(info)
        try:
            for section in info:
                service_l = section['services']
                #pp(service_l) 
                for service in service_l:
                    type = service['type']
                    if type in ['CE', 'SRM']:
                        downtime = Downtime(
                            endpoint = service['endpoint'],
                            start_time = section['start_time'],
                            end_time = section['end_time'],
                            site = site,
                            type = type,
                            name = service['name']
                        )
                        if downtime not in downtime_l:
                            downtime_l.append(downtime)
                 
        except:
            pass
    
    #print len(downtime_l)
    #for downtime in downtime_l:
    #    print downtime.type, downtime.name, downtime.endpoint

###    for downtime in downtime_l: 
###       #print 
###       #print "checking downtime... %s %s %s" %(downtime.type, downtime.site, downtime.endpoint)
###
###       site = downtime.site
###       for cloud in topology.cloudhandler.cloud_d.values():
###           for site in cloud.site_l:
###               for queue in site.pandaqueue_l:
###                   #print "inspecting queue %s in site %s " %(queue.name, site.name)
###                   if downtime.type == "CE":
###                       for ce in queue.ce_l:
###                           if downtime.endpoint == ce.endpoint:
###                               #print "match ", site.name, queue.name, ce.endpoint               
###                   ce.downtime_l.append(downtime)
###                   if downtime.type == "SRM":
###                       if queue.ddm:
###                           if queue.ddm.endpoint == downtime.endpoint:
###                               #print "match ", site.name, queue.name, queue.ddm.endpoint, downtime.endpoint               
###                               queue.ddm.downtime_l.append(downtime)
                            

    for downtime in downtime_l:
        if downtime.type == "CE":
            ce_l = topology.ce_d.get(downtime.endpoint, None)
            if ce_l:
                for ce in ce_l:
                    ce.downtime_l.append(downtime)
        if downtime.type == "SRM":
            ddm_l = topology.ddm_d.get(downtime.endpoint, None)
            if ddm_l:
                for ddm in ddm_l:
                    ddm.downtime_l.append(downtime)


topology = Topology()
topology.get_topology()
topology.add_ddm()
topology.add_switcher_status()

add_downtimes(topology)

#topology.check()




#!/usr/bin/env python

import logging 
import time

from ConfigParser import SafeConfigParser

from switcher.agistopology.topology import AGISTopology
from switcher.topology.topology import Topology
from switcher.services.serverapi import AGIS, AGISMock
from switcher.services.notify import Email, EmailMock


# -----------------------------------------------------------------------------
#   for tests, log to stdout
# -----------------------------------------------------------------------------
log = logging.getLogger()
logStream = logging.StreamHandler()
FORMAT='%(asctime)s (UTC) [ %(levelname)s ] %(name)s %(filename)s:%(lineno)d %(funcName)s(): %(message)s'
FORMAT='[%(levelname)s] %(name)s %(filename)s:%(lineno)d %(funcName)s(): %(message)s'    # FIXME: remove this line !!!
formatter = logging.Formatter(FORMAT)
formatter.converter = time.gmtime  # to convert timestamps to UTC
logStream.setFormatter(formatter)
log.addHandler(logStream)
log.setLevel('DEBUG')
# -----------------------------------------------------------------------------


source = 'URLS'
source = 'FILES'

if source == 'URLS':
    schedconfig = 'http://atlas-agis-api.cern.ch/request/pandaqueue/query/list/?json&preset=schedconf.all'
    ddm_topology = 'http://atlas-agis-api.cern.ch/request/ddmendpoint/query/list/?json&preset=dict'
    switcher_status = 'http://atlas-agis-api.cern.ch/request/pandaqueuestatus/query/list/?json&probe=switcher '
    downtimes_calendar = 'http://atlas-agis-api.cern.ch/request/downtime/query/list/?json&filter=henceforward'
    sites = 'http://atlas-agis-api.cern.ch/request/site/query/list/?json&vo_name=atlas'
if source == 'FILES':
    schedconfig = '../etc/inputs/schedconfig.json'
    ddm_topology = '../etc/inputs/ddm_topology.json'
    switcher_status = '../etc/inputs/switcher_status.json'
    downtimes_calendar = '../etc/inputs/downtimes_calendar.json'
    ### BEGIN TEST ###
    downtimes_calendar = './inputs/calendar_one_ce.json'
    ### END TEST ###
    sites = '../etc/inputs/sites.json'


notificationsconf = SafeConfigParser()
notificationsconf.readfp(open('../etc/notifications.conf'))
downtimesconf = SafeConfigParser()
downtimesconf.readfp(open('../etc/downtimes.conf'))

# -----------------------------------------------------------------------------
# verify that the AGIS Topology works stand-alone
agistopology = AGISTopology(schedconfig, ddm_topology)
log.debug(agistopology)

# -----------------------------------------------------------------------------
topology = Topology(schedconfig, ddm_topology, notificationsconf, downtimesconf)
topology.add_switcher_status(switcher_status)
topology.add_downtimes(downtimes_calendar)
topology.add_nucleus(sites)

topology.evaluate()
topology.act(AGISMock())
topology.notify(EmailMock())




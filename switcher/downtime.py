#!/usr/bin/env python

import copy
import logging

from switcher.utils import timeconverter2seconds
from switcher.timeinterval import TimeInterval


class Downtime(object):
    """
    class representing an scheduled downtime event 
    """

    def __init__(self, endpoint, start_t_str, end_t_str, description, classification, type, site, name, info_url, severity):
        """
        :param str endpoint: the endpoint affected by the downtime
        :param str start_t_str: string representing the starting time
        :param str end_t_str: string representing the ending time
        :param str type: CE or SRM
        :param str site: the site that the endpoint belongs to
        :param str name: the name of the entity with that endpoint
        :param str info_url: the URL from the EGI portal
        :param str severity: the severity level 
        """
        self.log = logging.getLogger('downtime')
        self.log.debug('Downtime event created with inputs %s, %s, %s, %s, %s, %s, %s, %s, %s, %s' 
                        %(endpoint, start_t_str, end_t_str, description, classification, type, site, name, info_url, severity)
                      )
        self.endpoint = endpoint

        self.start_t_str = start_t_str
        self.end_t_str = end_t_str
        start_t_sec = timeconverter2seconds(start_t_str) 
        end_t_sec = timeconverter2seconds(end_t_str) 
        self.timeinterval = TimeInterval(start_t_sec, end_t_sec)

        self.description = description
        self.classification = classification
        self.type = type
        self.site = site
        self.name = name
        self.info_url = info_url
        self.severity = severity
        self.log.debug('Object Downtime for %s created.' %endpoint)


   # --------------------------------------------------------------------------
   #    interfacing Downtime object with TimeInterval object
   # --------------------------------------------------------------------------

    def getTimeInterval(self):
        """
        returns the time interval for this downtime 
        :return TimeInterval:
        """
        return self.timeinterval


    def __contains__(self, t_epoch):
        """
        checks if a given time falls in the time interval of this downtime.
        :param int t_epoch: time, in seconds since epoch
        :return bool:
        """
        return t_epoch in self.timeinterval


    def __lt__(self, t_epoch):
        """
        checks if a given time is beyond the time interval of this downtime.
        :param int t_epoch: time, in seconds since epoch
        :return bool:
        """
        return self.timeinterval < t_epoch


    def expired(self):
        """
        tells if the time interval for this downtime is over.
        :return bool:
        """
        return self.timeinterval.expired()

    
    def shorter_than(self, seconds):
        """
        checks if the timeinterval for this downtime is shorter
        than a given amount of time
        :param int seconds: number of seconds
        :return bool:
        """
        return self.timeinterval.shorter_than(seconds)


    def extend(self, extra):
        """
        returns a copy of this Downtime object
        with an extended TimeInterval
        """
        newdowntime = copy.copy(self)
        newdowntime.timeinterval = self.timeinterval.extend(extra)
        return newdowntime

    
    def overlap(self, other):
        """
        checks if both Downtime objects have overlapping TimeIntervals
        If yes, returns the overlapping TimeInterval
        :return None/TimeInterval:
        """
        return self.timeinterval.overlap(other.timeinterval)


# =============================================================================


class EndpointDowntimes(object):
    """
    container for a list of Downtime objects.
    For example, to handle together all Downtimes for a given CE object.
    """
    def __init__(self):
        self.log = logging.getLogger('downtime')
        self.downtime_l = []


    def add(self, downtime):
        """
        :param Downtime downtime:
        """
        self.downtime_l.append(downtime)


    def getlist(self):
        """
        return the list of Downtime objects for this Endpoint
        :return list of Downtime:
        """
        return self.downtime_l


    def extend(self, extend_sec):
        """
        returns a new EndpointDowntimes, where all Downtimes
        have an extended TimeInterval
        :param int extend_sec: number of seconds to advance the start time
        :return EndpointDowntimes:
        """
        self.log.debug('Starting.')
        newendpointdowntimes = EndpointDowntimes()
        for downtime in self.getlist():
            newdowntime = downtime.extend(extend_sec)
            newendpointdowntimes.add(newdowntime)
        out = newendpointdowntimes
        self.log.debug('Leaving, returing %s.' %out)
        return out


    def overlap(self, other):
        """
        calculates the overlapping between two EndpointDowntimes objects, 
        this and a new one.

        For each pair of Downtime objects that overlap, 
        creates a OverlapDowntimes object with them, 
        and adds it to a OverlapDowntimesList object.
        :param EndpointDowntimes other: the another EndpointDowntimes object
        :return OverlapDowntimesList:
        """
        overlapdowntimeslist = OverlapDowntimesList()
        for downtime1 in self.getlist():
            for downtime2 in other.getlist():
                if downtime1.overlap(downtime2):
                    overlaps = OverlapDowntimes()
                    overlaps.add(downtime1)
                    overlaps.add(downtime2)
                    overlapdowntimeslist.add(overlaps)
        return overlapdowntimeslist


# =============================================================================


class OverlapDowntimes(object):
    """
    container for a list of overlapping Downtime objects.
    For example, to handle together all Downtimes from CE objects with overlapping TimeIntervals.
    """
    def __init__(self):
        self.downtime_l = []
        self.timeinterval = None # overlapping TimeInterval


    def getlist(self):
        """
        return the list of Downtime objects for this 
        collection of overlapping downtimes
        :return list of Downtime:
        """
        return self.downtime_l


    def add(self, downtime):
        """
        adds a new Downtime object, only if it overlaps 
        with the existing list of Downtime objects in the list.
        If it overlaps, the timeinterval is recalculated
        :param Downtime downtime:
        """
        if not self.downtime_l:
            self.downtime_l.append(downtime)
            self.timeinterval = downtime.timeinterval
        else:
            newtimeinterval = self.overlap(downtime)
            if newtimeinterval:
                self.downtime_l.append(downtime)
                self.timeinterval = newtimeinterval


    def overlap(self, downtime):
        """
        checks if a new Downtime object has a TimeInterval
        overlapping with the TimeInterval object of this collection.
        :param Downtime downtime:
        :return TimeInterval/None:
        """
        return self.timeinterval.overlap(downtime.timeinterval)


    def getTimeInterval(self):
        """
        return the overlapping time interval
        :return TimeInterval:
        """
        return self.timeinterval



# =============================================================================


class OverlapDowntimesList(object):
    """
    container to handle together a list of OverlapDowntimes objects.
    For example, all collections of overlapping Downtimes 
    for all CEs in a Queue.
    """
    def __init__(self):
        self.overlapdowntimes_l = []


    def add(self, collection):
        """
        :param OverlapDowntimes collection:
        """
        self.overlapdowntimes_l.append(collection)


    def getlist(self):
        """
        returns the list of collections of overlapping downtimes.
        :return list of OverlapDowntimes:
        """
        return self.overlapdowntimes_l


    def overlap(self, endpointdowntimes):
        """
        checks if the current list of OverlapDowntimes objects
        and a EndpointDowntimes object contain TimeIntervals that overlap.
        :param EndpointDowntimes endpointdowntimes:
        :return OverlapDowntimesList:
        """
        newcollection_l = []
        for collection in self.overlapdowntimes_l:
            for downtime in endpointdowntimes.getlist():
                if collection.overlap(downtime):
                    #newcollection = copy.deepcopy(collection)
                    newcollection = copy.copy(collection)
                    newcollection.add(downtime)
                    newcollection_l.append(newcollection)

        if newcollection_l:
            overlapdowntimeslist = OverlapDowntimesList()
            for collection in newcollection_l:
                overlapdowntimeslist.add(collection)
            return overlapdowntimeslist
        else:
            return OverlapDowntimesList()


    def __add__(self, other):
        """
        combines 2 OverlapDowntimesList objects
        :param OverlapDowntimesList other:
        :return OverlapDowntimesList:
        """
        newcollectionlist = OverlapDowntimesList()
        for collection in self.getlist():
            newcollectionlist.add(collection)
        for collection in other.getlist():
            newcollectionlist.add(collection)
        return newcollectionlist



# =============================================================================

class EndpointDowntimesSet(object):
    """
    container to handle together a list of EndpointDowntimes objects.
    In other words, a list of lists of Downtimes. 
    For example, the EndpointDowntimes objects for all CEs in a Queue.
    """
    def __init__(self):
        self.endpointdowntimes_l = []


    def add(self, endpointdowntimes):
        """
        :param EndpointDowntimes endpointdowntimes:
        """
        self.endpointdowntimes_l.append(endpointdowntimes)


    def getOverlapDowntimesList(self):
        """
        calculates all overlappings between all EndpointDowntimes objects, 
        and returns the list of OverlapDowntimes 
        :return OverlapDowntimesList:
        """
        if len(self.endpointdowntimes_l) == 0:
            return OverlapDowntimesList()

        if len(self.endpointdowntimes_l) == 1:
            out = OverlapDowntimesList()
            for d in self.endpointdowntimes_l[0].getlist():
                coll = OverlapDowntimes()
                coll.add(d)
                out.add(coll)
            return out

        if len(self.endpointdowntimes_l) >= 2:
            return reduce(lambda x,y: x.overlap(y), self.endpointdowntimes_l) 


# =============================================================================

def get_downtimes(data):
    """
    returns a list of Downtime objects from source json

    example of input data for a given queue:

                "CERN-PROD": [
                  {
                    "affected_services": "SRM, XRootD",
                    "classification": "SCHEDULED",
                    "create_time": "2019-06-24T13:18:02",
                    "description": "CASTOR Namespace Oracle DB upgrade",
                    "end_time": "2019-07-23T18:00:00",
                    "id": 125598,
                    "info_url": "https://goc.egi.eu/portal/index.php?Page_Type=Downtime&id=27387",
                    "is_published": false,
                    "last_modified": "2019-07-04T11:00:14.224919",
                    "last_published": null,
                    "pid": "105998G0",
                    "provider": "GOCDB",
                    "rc_site": "CERN-PROD",
                    "services": [
                      {
                        "endpoint": "srm://srm-atlas.cern.ch:8443/srm/managerv2?SFN=",
                        "flavour": "SRM",
                        "id": 2338,
                        "last_modified": "2015-01-29T17:01:27.053739",
                        "name": "CERN-PROD-SRM-srm-atlas.cern.ch",
                        "site": "CERN-PROD",
                        "state": "ACTIVE",
                        "state_comment": "",
                        "state_update": null,
                        "status": "production",
                        "type": "SRM"
                      },
                      {
                        "endpoint": "root://castoratlas.cern.ch",
                        "flavour": "XROOTD",
                        "id": 17212,
                        "last_modified": "2016-09-05T16:21:50.015346",
                        "name": "CERN-PROD-XROOTD-castoratlas.cern.ch",
                        "site": "CERN-PROD",
                        "state": "ACTIVE",
                        "state_comment": "State set to ACTIVE after DDMEndpoint creation",
                        "state_update": "2016-09-05T15:39:34.845361",
                        "status": "",
                        "type": "SRM"
                      }
                    ],
                    "severity": "OUTAGE",
                    "site": "CERN-PROD",
                    "site_id": 1198,
                    "start_time": "2019-07-23T09:00:00",
                    "state": "ACTIVE"
                  }
                ]


    :param json data: the json dump from the AGIS Downtime Calendar
    :return list:
    """
    log = logging.getLogger('downtime')
    log.debug('Starting.')
    downtime_l = []

    for site, info in data.items():
        log.info('Processing info for site %s' %site)
        info = data[site]
        try:
            for section in info:
                log.info('Processing section %s' %section)
                affected_services = [x.strip() for x in section['affected_services'].split(',')]
                description = section['description']
                classification = section['classification']
                service_l = section['services']
                info_url = section['info_url']
                severity = section['severity']
                for service in service_l:
                    log.info('Processing service %s' %service)
                    type = service['type']
                    if type not in ['CE', 'SRM']:
                        log.debug("service is neither a CE nor a SRM one. Skipping")
                        continue
                    if type == "SRM" and\
                       "SRM" not in affected_services and\
                       "SRMv2" not in affected_services:
                        log.debug("service is SRM but SRM is not listed in affected_services. Skipping")
                        continue
                    endpoint = service['endpoint']
                    downtime = Downtime(
                            endpoint = endpoint,
                            start_t_str = section['start_time'],
                            end_t_str = section['end_time'],
                            description = description,
                            classification = classification,
                            site = site,
                            type = type,
                            name = service['name'],
                            info_url = info_url,
                            severity = severity
                            )
                    log.info('Adding downtime to the list.')
                    downtime_l.append(downtime)

        except Exception as ex:
            log.error("Got exception %s" %ex)

    return downtime_l









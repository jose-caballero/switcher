#!/usr/bin/env python

import copy
import logging

from switcher.utils import timeconverter2seconds
from switcher.timeinterval import TimeInterval


class Downtime(object):
    """
    class representing an scheduled downtime event 
    """

    def __init__(self, endpoint, start_t_str, end_t_str, description, type, site, name, info_url):
        """
        :param str endpoint: the endpoint affected by the downtime
        :param str start_t_str: string representing the starting time
        :param str end_t_str: string representing the ending time
        :param str type: CE or SRM
        :param str site: the site that the endpoint belongs to
        :param str name: the name of the entity with that endpoint
        :param str info_url: the URL from the EGI portal
        """
        self.log = logging.getLogger('downtime')
        self.log.debug('Downtime event created with inputs %s, %s, %s, %s, %s, %s, %s' 
                        %(endpoint, start_t_str, end_t_str, description, type, site, name)
                      )
        self.endpoint = endpoint

        self.start_t_str = start_t_str
        self.end_t_str = end_t_str
        start_t_sec = timeconverter2seconds(start_t_str) 
        end_t_sec = timeconverter2seconds(end_t_str) 
        self.timeinterval = TimeInterval(start_t_sec, end_t_sec)

        self.description = description
        self.type = type
        self.site = site
        self.name = name
        self.info_url = info_url
        self.log.debug('Object Downtime for %s created.' %endpoint)


   # --------------------------------------------------------------------------
   #    interfacing Downtime object with TimeInterval object
   # --------------------------------------------------------------------------

    def getTimeInterval(self):
        return self.timeinterval


    #def contains(self, t_epoch=None):
    #    return self.timeinterval.contains(t_epoch)

    def __contains__(self, t_epoch):
        return t_epoch in self.timeinterval


    def expired(self):
        return self.timeinterval.expired()

    
    def shorter_than(self, seconds):
        return self.timeinterval.shorter_than(seconds)


    def extend(self, extra):
        """
        returns a copy of this Downtime object
        with an extended TimeInterval
        """
        newdowntime = copy.deepcopy(self)
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


class DowntimeList(object):
    """
    container for a list of Downtime objects.
    For example, to handle together all Downtimes for a given CE object.
    """
    def __init__(self):
        """
        """
        self.downtime_l = []


    def add(self, downtime):
        """
        :param Downtime downtime:
        """
        self.downtime_l.append(downtime)


    def getlist(self):
        return self.downtime_l


    def extend(self, extend_sec):
        """
        returns a new DowntimeList, where all Downtimes
        have an extended TimeInterval
        :param int extend_sec: number of seconds to advance the start time
        :return DowntimeList:
        """
        newdowntimelist = DowntimeList()
        for downtime in self.getlist():
            newdowntime = downtime.extend(extend_sec)
            newdowntimelist.add(newdowntime)
        return newdowntimelist


    def overlap(self, other):
        """
        calculates the overlapping between two DowntimeList objects, 
        this and a new one.

        For each pair of Downtime objects that overlap, 
        creates a DowntimeCollection object with them, 
        and adds it to a DowntimeCollectionList object.
        :param DowntimeList other: the another DowntimeList object
        :return DowntimeCollectionList:
        """
        downtimecollectionlist = DowntimeCollectionList()
        for downtime1 in self.getlist():
            for downtime2 in other.getlist():
                if downtime1.overlap(downtime2):
                    collection = DowntimeCollection()
                    collection.add(downtime1)
                    collection.add(downtime2)
                    downtimecollectionlist.add(collection)
        return downtimecollectionlist


# =============================================================================


class DowntimeCollection(object):
    """
    container for a list of overlapping Downtime objects.
    For example, to handle together all Downtimes from CE objects with overlapping TimeIntervals.
    """
    def __init__(self):
        self.downtime_l = []
        self.timeinterval = None # overlapping TimeInterval


    def getlist(self):
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
        return self.timeinterval



# =============================================================================


class DowntimeCollectionList(object):
    """
    container to handle together a list of DowntimeCollection objects.
    For example, all collections of overlapping Downtimes 
    for all CEs in a Queue.
    """
    def __init__(self):
        self.downtimecollection_l = []


    def add(self, collection):
        """
        :param DowntimeCollection collection:
        """
        self.downtimecollection_l.append(collection)


    def getlist(self):
        return self.downtimecollection_l


    def overlap(self, downtimelist):
        """
        checks if the current list of DowntimeCollection objects
        and a DowntimeList object contain TimeIntervals that overlap.
        :param DowntimeList downtimelist:
        :return DowntimeCollectionList:
        """
        newcollection_l = []
        for collection in self.downtimecollection_l:
            for downtime in downtimelist.getlist():
                if collection.overlap(downtime):
                    newcollection = copy.deepcopy(collection)
                    newcollection.add(downtime)
                    newcollection_l.append(newcollection)

        if newcollection_l:
            downtimecollectionlist = DowntimeCollectionList()
            for collection in newcollection_l:
                downtimecollectionlist.add(collection)
            return downtimecollectionlist
        else:
            return DowntimeCollectionList()


    def __add__(self, other):
        """
        combines 2 DowntimeCollectionList objects
        :param DowntimeCollectionList other:
        :return DowntimeCollectionList:
        """
        newcollectionlist = DowntimeCollectionList()
        for collection in self.getlist():
            newcollectionlist.add(collection)
        for collection in other.getlist():
            newcollectionlist.add(collection)
        return newcollectionlist



# =============================================================================

class DowntimeListList(object):
    """
    container to handle together a list of DowntimeList objects.
    In other words, a list of lists of Downtimes. 
    For example, the DowntimeList objects for all CEs in a Queue.
    """
    def __init__(self):
        self.downtimelist_l = []


    def add(self, downtimelist):
        self.downtimelist_l.append(downtimelist)


###    def getDowntimeCollectionList(self):
###        """
###        calculates all overlappings between all DowntimeList objects, 
###        and returns the list of DowntimeCollections 
###        :return DowntimeCollectionList:
###        """
###        return reduce(lambda x,y: x.overlap(y), self.downtimelist_l)


    def getDowntimeCollectionList(self):
        """
        calculates all overlappings between all DowntimeList objects, 
        and returns the list of DowntimeCollections 
        :return DowntimeCollectionList:
        """
        if len(self.downtimelist_l) == 0:
            return DowntimeCollectionList()

        if len(self.downtimelist_l) == 1:
            out = DowntimeCollectionList()
            for d in self.downtimelist_l[0].getlist():
                coll = DowntimeCollection()
                coll.add(d)
                out.add(coll)
            return out

        if len(self.downtimelist_l) >= 2:
            return reduce(lambda x,y: x.overlap(y), self.downtimelist_l) 






# =============================================================================



###class OverlappingDowntimeCollection(object):
###    """
###    container for a list of Downtimes with overlapping TimeIntervals.
###    For example, two Downtimes for two CEs, with overlapping DISABLED periods.
###    """
###    def __init__(self):
###        self.downtime_l = []
###
###
###    def add(self, downtime):
###        """
###        :param Downtime downtime:
###        """
###        if self.overlap(downtime):
###            self.downtime_l.append(downtime)
###
###
###    def getTimeInterval(self):
###        """
###        returns the overlapping TimeInterval
###        """
###
###    def overlap(self, downtime):
###        """
###        checks if the downtime object has a TimeInterval
###        that overlaps with the overlapping TimeInterval of this 
###        Collection
###        :return None/TimeInterval:
###        """







# =============================================================================

def get_downtimes(data):
    """
    returns a list of Downtime objects from source json
    :param json data: the json dump from the AGIS Downtime Calendar
    :return list:
    """
    downtime_l = []

    for site, info in data.items():
        info = data[site]
        try:
            for section in info:
                description = section['description']
                service_l = section['services']
                info_url = section['info_url']
                for service in service_l:
                    type = service['type']
                    if type in ['CE', 'SRM']:
                        endpoint = service['endpoint']
                        downtime = Downtime(
                                endpoint = endpoint,
                                start_t_str = section['start_time'],
                                end_t_str = section['end_time'],
                                description = description,
                                site = site,
                                type = type,
                                name = service['name'],
                                info_url = info_url
                                )
                        downtime_l.append(downtime)

        except Exception as ex:
            pass
            ##self.log.error("Got exception %s" %ex)

    return downtime_l









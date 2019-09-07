#!/usr/bin/env python

import copy
import logging
import time

from switcher.utils import timeconverter2seconds


class TimeInterval(object):
    """
    class to manipulate time intervals
    """
    def __init__(self, start_t, end_t, extend_sec=0):
        """
        :param int start_t: starting time in seconds since epoch
        :param int end_t: starting time in seconds since epoch
        :param int extend_sec: number of seconds to advance the start_t
        """
        self.log = logging.getLogger('timeinterval')
        self.log.debug('TimeInterval object with inputs %s, %s.' %(start_t, end_t))
        self.original_start_t = start_t  # we keep record, for extended intervals
        self.start_t = start_t - extend_sec
        self.end_t = end_t
        self.log.debug('TimeInterval object initialized.')
    

    def belongs(self, t_epoch=None):
        """
        returns if time t_epoch, 
        in seconds since epoch, in between the 
        start time and end time of this interval
        :param int t_epoch: time in seconds since epoch.
                            If no value is passed, 
                            current time will be calculated.
        :return boolean:
        """
        self.log.debug('Starting for time %s.' %t_epoch)
        if not t_epoch:
            t_epoch = int(time.time())  # now
        out = t_epoch >= self.start_t and\
              t_epoch < self.end_t
        self.log.debug('Leaving, returning %s.' %out)
        return out


    def extend(self, extend_sec):
        """
        returns a new TimeInterval object where the start_t
        has moved to take into account when the downtime starts having
        real impact
        :param int extend_sec: number of seconds to advance the start time
        :return TimeInterval:
        """
        self.log.debug('Starting with extend_sec %s.' %extend_sec)
        out = TimeInterval(self.start_t, self.end_t, extend_sec)
        self.log.debug('Leaving, returing %s.' %out)
        return out

    
    def overlap(self, other):
        """
        returns a new TimeInterval object with only the overlapping time intevals.
        :param TimeInterval other: another TimeInterval object
        :return TimeInterval or None:
        """
        self.log.debug('Starting with other %s.' %other)
        max_start_t = max(self.start_t, other.start_t)
        min_end_t = min(self.end_t, other.end_t)
        if max_start_t >= min_end_t:
            self.log.info('Original itervals do not overlap.')
            return None
        else:
            out = TimeInterval(max_start_t, min_end_t)
            self.log.info('Leaving, returning %s.' %out)
            return out


    def expired(self):
        """
        check if the end time of this TimeInterval
        is already in the past
        :return bool:
        """
        self.log.debug('Starting.')
        now = int(time.time())
        out = now <= self.end_t
        self.log.debug('Leaving, returning %s.' %out)
        return out


    def shorter_than(self, seconds):
        """
        checks if the TimeInterval is shorter than 
        a given amount of time
        :param int seconds: numbrer of seconds to compare with
        :return bool:
        """
        self.log.debug('Starting.')
        out = (self.end_t - self.start_t) < seconds
        self.log.debug('Leaving, returning %s.' %out)
        return out



# ===================================================================

class TimeIntervalCollection(object):
    """
    container for a list of TimeInterval objects.
    For example, to handle together all TimeIntervals for a given CE object.
    """
    def __init__(self, t_interval_l):
        """
        :param list t_interval_l: a list of TimeInterval objects
        """
        self.t_interval_l = t_interval_l



# ===================================================================
#    
#    utils to manage multiple TimeIntervals at once
#   
# ===================================================================

def overlap2collections(t_intervalcollection_1, t_intervalcollection_2):
    """
    given 2 objects TimeIntervalCollection, 
    returns another TimeIntervalCollection with the 
    overlappings
    """
    new_t_interval_l = []
    for i in t_intervalcollection_1.t_interval_l:
        for j in t_intervalcollection_2.t_interval_l:
            new_t_interval = i.overlap(j)
            if new_t_interval:
                new_t_interval_l.append(new_t_interval)
    return TimeIntervalCollection(new_t_interval_l)


def overlapNcollections(*t_intervalcollection_l):
    """
    given a list of TimeIntervalCollection objects, 
    returns a new TimeIntervalCollection with the overall overlappings 
    """
    return reduce(overlap2collections, t_intervalcollection_l)
    











###
###  sorting TimeInterval events by time may become helpful in the future
###  for performance reasons
###  but for now I am not using it
###
###     #    def __eq__(self, other):
###     #        return self.start_t == other.start_t and\
###     #               self.end_t == other.end_t and\
###     #               self.type == other.type and\
###     #               self.endpoint == other.endpoint
###     
###         def __eq__(self, other):
###             return self.start_t == other.start_t and\
###                    self.end_t == other.end_t
###     
###     
###         def __ne__(self, other):
###             return not self.__eq__(other)
###     
###     
###         def __lt__(self, other):
###             return (self.start_t < other.start_t) or\
###                    (self.start_t == other.start_t and\
###                    self.end_t < other.end_t)
###     
###     
###         def __le__(self, other):
###             return self.__lt__(other) or self.__eq__(other)
###     
###     
###         def __gt__(self, other):
###             return not self.__le__(other)
###     
###     
###         def __ge__(self, other):
###             return self.__gt__(other) or self.__eq__(other)

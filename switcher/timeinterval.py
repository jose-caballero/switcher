#!/usr/bin/env python

import copy
import logging
import time


class TimeInterval(object):
    """
    class to manipulate time intervals
    """
    def __init__(self, start_t, end_t):
        """
        :param int start_t: starting time in seconds since epoch
        :param int end_t: starting time in seconds since epoch
        """
        self.log = logging.getLogger('timeinterval')
        self.log.debug('TimeInterval object with inputs %s, %s.' %(start_t, end_t))
        self.start_t = start_t
        self.end_t = end_t
        self.original_timeinterval = None  # to be filled when 
                                           # method extend() is called
        self.log.debug('TimeInterval object initialized.')


    def get_original_start_t(self):
        """
        returns the original value of start time
        In the case of a TimeInterval object, it is just the value of 
        self.start_d
        But we have here this method as a part of the common API
        between TimeInterval and ExtendedTimeInterval classes
        """
        return self.start_t


    def get_original_end_t(self):
        """
        returns the original value of end time
        In the case of a TimeInterval object, it is just the value of 
        self.end_d
        But we have here this method as a part of the common API
        between TimeInterval and ExtendedTimeInterval classes
        """
        return self.end_t

    
    def extend(self, extend_sec):
        """
        returns a new TimeInterval object where the start_t
        has moved to take into account when the downtime starts having
        real impact
        :param int extend_sec: number of seconds to advance the start time
        :return TimeInterval:
        """
        self.log.debug('Starting with extend_sec %s.' %extend_sec)
        new_timeinterval = ExtendedTimeInterval(self.start_t - extend_sec, self.end_t)
        new_timeinterval.original_timeinterval = copy.copy(self)
        #new_timeinterval.original_timeinterval = TimeInterval(self.start_t, self.end_t)
        self.log.debug('Leaving, returing %s.' %new_timeinterval)
        return new_timeinterval 


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
        out = now > self.end_t
        self.log.debug('Leaving, returning %s.' %out)
        return out


    def __contains__(self, t_epoch):
        """
        Implementation of operator "in".
        Returns if time t_epoch, 
        in seconds since epoch, is in between the 
        start time and end time of this interval
        Examples:
            if now in timeinterval
            if 1541012063 in timeinterval

        :param int t_epoch: time in seconds since epoch.
        :return boolean:
        """
        self.log.debug('Starting for time %s.' %t_epoch)
        out = t_epoch >= self.start_t and\
              t_epoch < self.end_t
        self.log.debug('Leaving, returning %s.' %out)
        return out


    # FIXME: maybe this is not a good idea
    def __lt__(self, t_epoch):
        """
        implementation of operator "<".
        Returns if time t_epoch,
        in seconds since epoch, is beyond this 
        time interval.
        :param int t_epoch: time in seconds since epoch
        :return boolean:
        """
        self.log.debug('Starting for time %s.' %t_epoch)
        out = t_epoch > self.end_t
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


class ExtendedTimeInterval(TimeInterval):
    """
    class with a TimeInterval that have been extended to
    advance the starting time.
    It contains a reference to the original TimeInterval instance
    so it is possible to retrieve the original times later on. 
    """

    def get_original_start_t(self):
        """
        returns the original value of start time.
        In the case of a ExtendedTimeInterval object, 
        we query TimeInterval instance being recorded.
        """
        return self.original_timeinterval.get_original_start_t()


    def get_original_end_t(self):
        """
        returns the original value of end time.
        In the case of a ExtendedTimeInterval object, 
        we query TimeInterval instance being recorded.
        """
        return self.original_timeinterval.get_original_end_t()








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

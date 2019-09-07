#!/usr/bin/env python

import calendar
import json
import logging
import smtplib
import time
import urllib2

from datetime import timedelta, datetime
from time import strptime, mktime

try:
    from email.mime.text import MIMEText
except:
    from email.MIMEText import MIMEText



log = logging.getLogger('utils')


def timeconverter2seconds(timestring):
    """
    converts time from string with date in expected format to 
    seconds since epoch
    """
    log.debug('Starting for time %s.' %timestring)
    # timestring = "2011-11-02 15:28:01"
    time_format1 = "%Y-%m-%d %H:%M:%S"
    # timestring = "2013-09-14T23:59:00"
    time_format2 = "%Y-%m-%dT%H:%M:%S"
    try:
        mytime = datetime.strptime(timestring, time_format1)
    except ValueError:
        mytime = datetime.strptime(timestring, time_format2)
    out = calendar.timegm(mytime.timetuple())
    log.debug('Leaving with output %s.' %out)
    return out


def timestamp_now():
    """
    returns a timestamp, in UTC, for this instant right now
    """
    out = datetime.utcnow().strftime("%F %H:%M UTC")
    log.debug('Leaving with output %s.' %out)
    return out


def send_notifications(subject, body, sender, to, cc=''):
    """
    sends email
    """
    log.debug('Starting with subject %s, body %s, sender %s, to = %s, CC list %s.' %(subject, body, sender, to, cc))

    message = MIMEText(body)
    message['subject'] = subject
    message['From'] = sender 
    message['To'] = to
    message['Cc'] = cc

    to = [x.strip() for x in to.split()]
    cc = [x.strip() for x in cc.split()]
    to += cc

    server = smtplib.SMTP("localhost") # FIXME
    server.sendmail(sender, to, message.as_string())
    server.close()

    log.debug('Leaving.')


#def load_json(source):
#    """
#    get the json data either from URL or from file
#    """
#    log.debug('Starting with source %s' %source)
#    if source.startswith('http'):
#        data = json.load(urllib2.urlopen(source))
#    else:
#        data = json.load(open(source))
#    log.debug('Leaving with output %s.' %data)
#    return data


def load_json(source):
    """
    get the json data either from URL or from file
    """
    log.debug('Starting with source %s' %source)
    max_trials = 3
    trial = 0
    while trial < max_trials:
        try:
            data = _attemp_load_json(source)
            break
        except Exception as ex:
            trial += 1
            if trial < max_trials:
                time.sleep(30)
    else:
        # while loop got to the end without breaking
        # which means it did not work
        # we re-raise the last Exception
        raise ex

    log.debug('Leaving with output %s.' %data)
    return data

def _attemp_load_json(source):
    """
    attempt to get the json data either from URL or from file
    """
    log.debug('Starting with source %s' %source)
    try:
        if source.startswith('http'):
            data = json.load(urllib2.urlopen(source))
        else:
            data = json.load(open(source))
    except Exception as ex:
        log.error('unabled to load data from %s' %source)
        raise ex
    log.debug('Leaving with output %s.' %data)
    return data


# =============================================================================

class AllowedEntities(object):
    """
    class to facilitate the decision making 
    about when to take into account 
    an entity (Cloud, Site, Queue) from SchedConfig or not
    """
    def __init__(self, allow_only=None, excluded=None):
        self.allow_only = allow_only
        self.excluded = excluded

    def __contains__(self, entity):

        if self.excluded:
            if entity in self.excluded:
                return False

        if self.allow_only:
            if entity not in self.allow_only:
                return False

        # default
        return True





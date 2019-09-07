#!/usr/bin/env python

import json
import time
import urllib
import urllib2
from pprint import pprint as pp
from ConfigParser import SafeConfigParser

from switcher.serverapi import AGIS


# =============================================================================

class Cloud(object):
    
    def __init__(self, name):
        self.name = name
        self.email_address = None
        self.site_d = {}


# =============================================================================

class Site(object):
    
    def __init__(self, name):
        self.name = name
        self.nucleus = False
        self.queue_d = {}


# =============================================================================

class Queue(object):
    
    def __init__(self, name, data_d):
        self.name = name
        self.status = None
        self.tier_level = None
        self.type = None
        self.ce_d = {}
        self.ddm = None
        self.__configure(data_d)

        #self.__read_config_parameters()

#    def _read_config_parameters(self):
#        """
#        reads configuration from config file
#        """
#        conf = SafeConfigParser()
#        conf.readfp(open('../etc/downtimes.conf'))   # FIXME !! path is hardcoded !!
#
#        var = '%s_setbrokeroff' %self.type # type = analysis | production
#        self.time_to_brokeroff_sec = conf.getint('QUEUE', var) * 3600
#
#        var = '%s_setoffline' %self.type # type = analysis | production
#        self.time_to_offline_sec = conf.getint('QUEUE', var) * 3600

    # --------------------------------------------------------------------------
    
    def __configure(self, data_d):
        """
        configure the queue with info from Schedconfig
        """
        self.status = data_d['status']
        self.tier_level = data_d['tier_level']
        self.type = data_d['type']
        self.__add_ddm_tokens(data_d)


###    def __add_ddm_tokens(self, data_d):
###        try:
###            self.tokens = data_d['astorages0']['write_lan'].items()[0][1][0]
###        except:
###            self.tokens = []
    
###    def __add_ddm_tokens(self, data_d):
###        """
###        """
###        self.tokens = []
###        try:
###            for k, tokens in data_d['astorages0']['write_lan'].items():
###                token = tokens[0]
###                if token not in self.tokens:
###                    self.tokens.append(token)
###        except Exception as ex:
###            # FIXME
###            pass
    
    def __add_ddm_tokens(self, data_d):
        try:
            self.token = data_d['astorages']['write_lan'][0]
        except:
            self.token = None 

# =============================================================================

class CE(object):

    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.name = None 
        self.status = None


#    def _read_config_parameters(self):
#        """
#        reads configuration from config file
#        """
#        conf = SafeConfigParser()
#        conf.readfp(open('../etc/downtimes.conf'))   # FIXME !! path is hardcoded !!
#        self.time_to_disable_sec = conf.getint('CE', 'setdisable') * 3600

# =============================================================================

class DDM(object):

    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.name = None
        self.token = None
        #self.site = None





#!/usr/bin/env python


from switcher.agistopology.ce import AGISCEHandler
from switcher.agistopology.ddm  import AGISDDMHandler

class AGISQueue(object):
    
    def __init__(self, name, data_d):
        self.name = name
        self.status = None
        self.tier_level = None
        self.type = None
        self.cehandler = AGISCEHandler()
        self.ddmhandler = AGISDDMHandler()
        ###self.ddm = None
        self.__configure(data_d)


    def __configure(self, data_d):
        """
        configure the queue with info from Schedconfig
        """
        self.status = data_d['status']
        self.tier_level = data_d['tier_level']
        self.type = data_d['type']
        self.__add_ddm_tokens(data_d)

    
    def __add_ddm_tokens(self, data_d):
        try:
            self.token = data_d['astorages']['write_lan'][0]
        except:
            self.token = None 

    # -------------------------------------------------------------------------

    def add_ce(self, ce):
        self.cehandler.add(ce)

    def add_ddm(self, ddm):
        self.ddmhandler.add(ddm)

    # -------------------------------------------------------------------------

    def __str__(self):
        """
        ancillary method to get a friendly, easy to read, 
        representation of the topology
        """
        str = '        queue %s\n' %self.name
        for ce in self.cehandler.getlist():
            str += '                ce %s (%s)\n' %(ce.endpoint, ce.state)

        for ddm in self.ddmhandler.getlist():
            str += '                ddm %s\n' %ddm.endpoint
        ###if self.ddm:
        ###    str += '                ddm %s\n' %self.ddm.endpoint

        return str



#!/usr/bin/env python


class AGISCE(object):

    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.name = None 
        self.state = None


class AGISCEHandler(object):
    """
    class to handle multiple CE objects at once.
    For example, all CEs for a given Queue
    """
    def __init__(self):
        """
        """
        self.ce_d = {}


    def add(self, ce):
        """
        adds an object CE to the list
        :param CE ce: 
        """
        endpoint = ce.endpoint
        if endpoint not in self.ce_d.keys():
            self.ce_d[endpoint] = ce


    def getlist(self):
        """
        get the list of CEs
        """
        return self.ce_d.values()


    def getlistendpoints(self):
        """
        get the list of endpoints 
        """
        return self.ce_d.keys()


    def getitems(self):
        """
        """
        return self.ce_d.items()


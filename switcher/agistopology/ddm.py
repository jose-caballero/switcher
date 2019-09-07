#!/usr/bin/env python


class AGISDDM(object):

    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.name = None
        self.token = None
        #self.site = None


class AGISDDMHandler(object):
    """
    class to handle the DDM objects.
    """

    def __init__(self):
        self.ddm_d = {}


    def add(self, ddm):
        """
        adds an object DDM to the list dict.
        :param DDM ddm:
        """
        endpoint = ddm.endpoint
        if endpoint not in self.ddm_d.keys():
            self.ddm_d[endpoint] = ddm


    def getlist(self):
        """
        get the list of DDM objects
        """
        return self.ddm_d.values()



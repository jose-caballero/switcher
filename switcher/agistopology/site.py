#!/usr/bin/env python


class AGISSite(object):
    
    def __init__(self, name):
        self.name = name
        self.nucleus = False
        self.queue_d = {}


    def __str__(self):
        """
        ancillary method to get a friendly, easy to read, 
        representation of the topology
        """
        str = '    site %s\n' %self.name
        for queue in self.queue_d.values():
            str += '    %s' %queue 
        return str


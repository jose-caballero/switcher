#!/usr/bin/env python


class AGISCloud(object):
    
    def __init__(self, name):
        self.name = name
        self.email_address = None
        self.site_d = {}

    def __str__(self):
        """
        ancillary method to get a friendly, easy to read, 
        representation of the topology
        """
        str = 'cloud %s\n' %self.name
        for site in self.site_d.values():
            str += '    %s' %site
        return str


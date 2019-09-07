#!/usr/bin/env python

import logging
import time

from switcher.agistopology.ddm import AGISDDM, AGISDDMHandler
from switcher.services.serverapi import AGIS
from switcher.downtime import EndpointDowntimes, OverlapDowntimes, OverlapDowntimesList


class DDM(AGISDDM):

    def __init__(self, endpoint):
        super(DDM, self).__init__(endpoint)
        self.log = logging.getLogger('topology')
        ###self.downtime_l = []
        self.endpointdowntimes = EndpointDowntimes()
        self.log.debug('Object DDMSwitcher created.')


    def add_downtime(self, downtime):
        self.endpointdowntimes.add(downtime)


    def getEndpointDowntimes(self):
        return self.endpointdowntimes


    # --------------------------------------------------------------------------

    def is_in_downtime(self, seconds):
        """
        checks if there at least one downtime event 
        for this DDM a given number of seconds in the future.
        We do it by checking if we are alrady affected by an
        extended TimeInterval for any of the Downtime events registered.
        :param int seconds: how many seconds to look into the future
        :return bool:
        """
        self.log.info('Checking if DDM %s is affected by downtime.' %self.endpoint)
        for downtime in self.endpointdowntimes.getlist():
            timeinterval = downtime.timeinterval
            extended_timeinterval = timeinterval.extend(seconds)
            #if extended_timeinterval.belongs():
            #    return True
            if int(time.time()) in extended_timeinterval:
                return True

        else:
            self.log.info('DDM %s is not affected by downtime. Returning False.' %self.endpoint)
            return False


# =============================================================================

class DDMHandler(AGISDDMHandler):


    def getOverlapDowntimesList(self):
        """
        to get if all DDMs will be in downtime at the same time.
        It returns a OverlapDowntimesList, so the output has the same 
        shape that the one returned by CEHandler.
        :return OverlapDowntimesList:
        """
        # Currently, there is only one DDM per DDMHandler,
        # therefore, we convert each Downtime to a 
        # OverlapDowntimes, because we know there are no
        # more than one Downtimes (overlapping or not), 
        # because there are no more than one DDM

        overlapdowntimeslist = OverlapDowntimesList()
        for ddm in self.getlist():
            downtime_l = ddm.getEndpointDowntimes()
            for downtime in downtime_l.getlist():
                # we make a collection from each Downtime
                overlapdowntimes = OverlapDowntimes()
                overlapdowntimes.add(downtime)
                # we add the collection to the list of collections
                overlapdowntimeslist.add(overlapdowntimes)
        return overlapdowntimeslist

    




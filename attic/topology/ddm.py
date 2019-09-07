#!/usr/bin/env python

import logging
import time

from switcher.agistopology.ddm import AGISDDM, AGISDDMHandler
from switcher.services.serverapi import AGIS
from switcher.downtime import DowntimeList, DowntimeCollection, DowntimeListList, DowntimeCollectionList


class DDM(AGISDDM):

    def __init__(self, endpoint):
        super(DDM, self).__init__(endpoint)
        self.log = logging.getLogger('switcher')
        ###self.downtime_l = []
        self.downtimelist = DowntimeList()
        self.log.debug('Object DDMSwitcher created.')


    def add_downtime(self, downtime):
        self.downtimelist.add(downtime)


    def getDowntimeList(self):
        return self.downtimelist


    # --------------------------------------------------------------------------

    def evaluate(self):
        # for now, doing nothing
        pass


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
        for downtime in self.downtimelist.getlist():
            timeinterval = downtime.timeinterval
            extended_timeinterval = timeinterval.extend(seconds)
            #if extended_timeinterval.belongs():
            #    return True
            if time.time() in extended_timeinterval:
                return True

        else:
            self.log.info('DDM %s is not affected by downtime. Returning False.' %self.endpoint)
            return False


# =============================================================================

class DDMHandler(AGISDDMHandler):

    def evaluate(self):
        for ddm in self.getlist():
            ddm.evaluate()


    def getDowntimeCollectionList(self):
        """
        to get if all DDMs will be in downtime at the same time.
        It returns a DowntimeCollectionList, so the output has the same 
        shape that the one returned by CEHandler.
        :return DowntimeCollectionList:
        """
        downtimecollectionlist = DowntimeListList()
        for ddm in self.getlist():
            downtime_l = ddm.getDowntimeList()
            for downtime in downtime_l:
                # we make a collection from each Downtime
                downtime_coll = DowntimeCollection()
                downtime_coll.add(downtime)
                # we add the collection to the list of collections
                downtimecollectionlist.add(downtime_coll)
        return downtimecollectionlist

    




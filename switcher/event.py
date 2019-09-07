#!/usr/bin/env python


class Event(object):
    """
    class to record a switching event:
        -- set CE DISABLED or ACTIVE
        -- set a queue ONLINE, OFFLINE or BROKEROFF
    Having the need for a status change recorded can server several purposes:
        -- the change can be performed
        -- all changes can be collected and reported (by email, for example)
    """

    def __init__(self, entitytype, 
                       uid, 
                       old_status=None, 
                       new_status=None, 
                       start=None, 
                       end=None, 
                       timeinterval=None,
                       downtime=None,
                       overlap_downtimes=None,
                       message=None):
        """
        :param str entitytype: type of entity (CE, Queue)
        :param str uid: uniq id for the entity
        :param str old_status: previous status
        :param str new_status: new status
        :param int start: seconds since epoch for Downtime start
        :param int end: seconds since epoch for Downtime end
        :param TimeInterval timeinterval: timeinterval of the scheduled Downtime 
                                          that triggers an event
        :param Downtime downtime: scheduled Downtime that triggers an event
        :param OverlapDowntimes overlap_downtimes : collection of Downtimes
                                          that triggers an event
        :param str message: explanatory message
        """
        self.entitytype = entitytype
        self.uid = uid
        self.old_status = old_status
        self.new_status = new_status
        self.start = start
        self.end = end
        self.timeinterval = timeinterval
        self.downtime = downtime
        self.overlap_downtimes = overlap_downtimes
        self.message = message
        self.comment = None
        self.done = False


    @property
    def status_changed(self):
        return self.old_status != self.new_status


class QueueEvent(Event):

    def __init__(self, *k, **kw):
        super(QueueEvent, self).__init__(*k, **kw)
        self.queue_final_status = None

    @property
    def queue_affected(self):
        return self.new_status == self.queue_final_status



# =============================================================================
#   Container classes 
#    
#       main purpose is to be able to collect and act upon all Events
#       in an organized way,
#       mostly for notifications
# =============================================================================


class QueueEventList(object):

    def __init__(self, name):
        self.name = name
        self.event_l = []

    def add(self, event):
        self.event_l.append(event)

    def get_changed(self):
        """
        returns only those Event objects that have changed
        """
        return filter(lambda event : event.status_changed, self.event_l)

    def list(self):
        return self.event_l


class SiteEventList(object):

    def __init__(self, name):
        self.name = name
        self.queue_event_l = [] 

    def add(self, queue_event_l):
        """
        :param QueueEventList queue_event_l:
        """
        self.queue_event_l.append(queue_event_l)

    def get_changed(self):
        out = []
        for queue_event_l in self.queue_event_l:
            out += queue_event_l.get_changed()
        return out
        # code above is equivalent to this
        #
        #   sum(map(lambda x:x.get_changed(), 
        #           self.queue_event_l
        #          ), 
        #       []
        #      )
        #
        # but that is less easy to read

    def list(self):
        return self.queue_event_l


class CloudEventList(object):

    def __init__(self, name):
        self.name = name
        self.site_event_l = []

    def add(self, site_event_l):
        """
        :param SiteEventList site_event_l:
        """
        self.site_event_l.append(site_event_l)

    def get_changed(self):
        out = []
        for site_event_l in self.site_event_l:
            out += site_event_l.get_changed()
        return out

    def list(self):
        return self.site_event_l



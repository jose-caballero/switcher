#!/usr/bin/env python

import logging
import time
import urllib

from switcher.agistopology.queue import AGISQueue
from switcher.topology.ce import CEHandler
from switcher.topology.ddm import DDMHandler
from switcher.event import QueueEvent, QueueEventList



class Queue(AGISQueue):
    
    def __init__(self, name, qdata, downtimesconf):
        """
        :param str name: the queue name
        :param SafeConfigParser downtimesconf: config with data about 
                                               when to change status
        """
        super(Queue, self).__init__(name, qdata)
        self.log = logging.getLogger('topology')
        self.cehandler = CEHandler()
        self.ddmhandler = DDMHandler()
        self.downtimesconf = downtimesconf
        self.switcher_status = None
        self.event = None
        #self.reason_change = None
        self._read_config_parameters()
        self.log.debug('Object QueueSwitcher %s created.' %self.name)


    def _read_config_parameters(self):
        """
        reads configuration from config file
        """

        self.max_duration_tooshort = self.downtimesconf.getint('QUEUE', 'max_duration_tooshort') * 3600
        self.max_duration_short = self.downtimesconf.getint('QUEUE', 'max_duration_short') * 3600

        self.downtime_length_d = {}
        self.downtime_length_d['CE'] = {}
        self.downtime_length_d['CE']['setbrokeroff'] = {}
        self.downtime_length_d['CE']['setoffline'] = {}
        self.downtime_length_d['DDM'] = {}
        self.downtime_length_d['DDM']['setbrokeroff'] = {}
        self.downtime_length_d['DDM']['setoffline'] = {}

        if self.type in ['analysis', 'production']:
            queue_type = self.type
        else:
            queue_type = 'other'

        # -------------------------------------------------
        def get_value(key):
            try:
                value = self.downtimesconf.getint('QUEUE', key) * 3600
            except:
                value = None
            return value
        # -------------------------------------------------

        key = 'tooshort_CE_%s_setbrokeroff' %queue_type
        self.downtime_length_d['CE']['setbrokeroff']['tooshort'] = get_value(key)

        key = 'tooshort_CE_%s_setoffline' %queue_type
        self.downtime_length_d['CE']['setoffline']['tooshort'] = get_value(key)

        key = 'tooshort_SRM_%s_setbrokeroff' %queue_type
        self.downtime_length_d['DDM']['setbrokeroff']['tooshort'] = get_value(key)

        key = 'tooshort_SRM_%s_setoffline' %queue_type
        self.downtime_length_d['DDM']['setoffline']['tooshort'] = get_value(key)

        key = 'short_CE_%s_setbrokeroff' %queue_type
        self.downtime_length_d['CE']['setbrokeroff']['short'] = get_value(key)

        key = 'short_CE_%s_setoffline' %queue_type
        self.downtime_length_d['CE']['setoffline']['short'] = get_value(key)

        key = 'short_SRM_%s_setbrokeroff' %queue_type
        self.downtime_length_d['DDM']['setbrokeroff']['short'] = get_value(key)

        key = 'short_SRM_%s_setoffline' %queue_type
        self.downtime_length_d['DDM']['setoffline']['short'] = get_value(key)

        key = 'long_CE_%s_setbrokeroff' %queue_type
        self.downtime_length_d['CE']['setbrokeroff']['long'] = get_value(key)

        key = 'long_CE_%s_setoffline' %queue_type
        self.downtime_length_d['CE']['setoffline']['long'] = get_value(key)

        key = 'long_SRM_%s_setbrokeroff' %queue_type
        self.downtime_length_d['DDM']['setbrokeroff']['long'] = get_value(key)

        key = 'long_SRM_%s_setoffline' %queue_type
        self.downtime_length_d['DDM']['setoffline']['long'] = get_value(key)


    # --------------------------------------------------------------------------

    def evaluate(self):
        """
        triggers the evaluation of all registered downtimes
        for all CEs and DDMs in this Queue, 
        and change status when needed.
        """
        self.log.info('Evaluating queue %s.' %self.name)
        # we reset first
        self.event = None
        #self.reason_change = None

        self.log.info('Evaluating CEs.')
        self.cehandler.evaluate()
        # NOTE: if needed in the future, evaluating DDMs would be here
        self.log.info('Evaluating Queue.')
        self.evaluate_this_queue()
        self.log.debug('Leaving.')


    def evaluate_this_queue(self):
        """
        """
        self.log.debug('Starting.')
        self.log.info('Getting the new status.')
        event = self._get_new_status()
        event.old_status = self.switcher_status
        self.log.info('New status for queue %s is %s.' %(self.name, event.new_status))
        if not event.status_changed:
            # FIXME
            # maybe this is too soon to make such a decision
            # perhaps is better to keep all events, and only at the end,
            # before acting, check if they are needed or not
            self.log.info('New status is the current status. Nothing to do.')
            self.event = event
        else:
            # FIXME
            # maybe this is too soon to make such a decision
            # perhaps is better to keep all events, and only at the end,
            # before acting, check if they are needed or not
            if self._transition_allowed(event):
                self.log.info('New status is different: %s -> %s. Recording an Event.' %(event.old_status, event.new_status))
                self.event = event
            else:
                self.log.info('New status is different: %s -> %s, but old status was not set by Switcher. Doing nothing.' %(event.old_status, event.new_status))

        self.log.debug('Leaving.')



    # FIXME 
    # this part - get_new_status(), should_be_offline(), should_be_online() and check_status()-
    # should be done in a nicer way
    # but for now is OK

    def _get_new_status(self):
        """
        finds out in which status this Queue should be
        We check first for OFFLINE, as it is the most restrictive one.
        If queue does not qualify yet for OFFLINE, then we try with BROKEROFF.
        If not of them, then the queue should be ONLINE.
        :return Event:
        """
        self.log.debug('Starting.')

        # first, collect all downtimes for entities belonging to this Queue
        ce_downtime_collection_list = self.cehandler.getOverlapDowntimesList()
        ddm_downtime_collection_list = self.ddmhandler.getOverlapDowntimesList()

        # First, we check if Queue should be OFFLINE becuase CE 
        event = self.should_be_offline(ce_downtime_collection_list, self.downtime_length_d['CE']['setoffline'])
        if event:
            return event

        # First, we check if Queue should be OFFLINE becuase DDM
        event = self.should_be_offline(ddm_downtime_collection_list, self.downtime_length_d['DDM']['setoffline'])
        if event:
            return event

        # If not OFFLINE, we check if Queue should be BROKEROFF because CE
        event = self.should_be_brokeroff(ce_downtime_collection_list, self.downtime_length_d['CE']['setbrokeroff'])
        if event:
            return event

        # If not OFFLINE, we check if Queue should be BROKEROFF because DDM
        event = self.should_be_brokeroff(ddm_downtime_collection_list, self.downtime_length_d['DDM']['setbrokeroff'])
        if event:
            return event

        # If neither OFFLINE nor BROKEROFF, then the Queue should be ONLINE
        event = QueueEvent(entitytype='Queue',
                      uid=self.name,
                      new_status = 'online')
        event.comment = 'set.online.by.Switcher'

        self.log.debug('Leaving with value %s.' %event)
        return event


    # FIXME
    # too much duplicated code between this method and should_be_brokeroff
    def should_be_offline(self, downtime_collection_list, downtime_length_d):
        """
        checks if this Queue should be set OFFLINE
        :return Event:
        """
        self.log.debug('Starting.')
        overlap_downtimes = self._check_status(downtime_collection_list, downtime_length_d)
        if overlap_downtimes:
            self.log.info('This Queue should be in status OFFLINE')
            event = QueueEvent(entitytype='Queue',
                          uid=self.name,
                          new_status='offline',
                          overlap_downtimes=overlap_downtimes)

            # build the comment for later notification
            # FIXME
            # this maybe should not be here, as this part of the code does not know in theory
            # what is going to happen next
            # but for now is OK
            event.comment = 'set.offline.by.Switcher'

            info_url_l = []
            for downtime in overlap_downtimes.getlist():
                if downtime.info_url not in info_url_l:
                    info_url_l.append(downtime.info_url)
            for info_url in info_url_l:
                event.comment += '+%s' %urllib.quote(info_url, safe='')

            out = event
        else:
            out = None
        self.log.debug('Leaving with value %s.' %out)
        return out



    # FIXME
    # too much duplicated code between this method and should_be_offline
    def should_be_brokeroff(self, downtime_collection_list, downtime_length_d):
        """
        checks if this Queue should be set BROKEROFF 
        :return Event:
        """
        self.log.debug('Starting.')
        ###overlap_downtimes = self._check_status(self.time_to_brokeroff_sec, downtime_collection_list)
        overlap_downtimes = self._check_status(downtime_collection_list, downtime_length_d)
        if overlap_downtimes:
            self.log.info('This Queue should be in status BROKEROFF')
            event = QueueEvent(entitytype='Queue',
                          uid=self.name,
                          new_status='brokeroff',
                          overlap_downtimes=overlap_downtimes)

            # build the comment for later notification
            # FIXME
            # this maybe should not be here, as this part of the code does not know in theory
            # what is going to happen next
            # but for now is OK
            event.comment = 'set.brokeroff.by.Switcher'
            info_url_l = []
            for downtime in overlap_downtimes.getlist():
                if downtime.info_url not in info_url_l:
                    info_url_l.append(downtime.info_url)
            for info_url in info_url_l:
                event.comment += '+%s' %urllib.quote(info_url, safe='')

            out = event
        else:
            out = None
        self.log.debug('Leaving with value %s.' %out)
        return out


    def _check_status(self, downtime_collection_list, downtime_length_d):
        """
        checks if this Queue will be in Downtime in a number of seconds in the future
        If so, returns the collection of Downtimes with an overlapping TimeInterval
        that contains that point time in the future.
        :param int seconds: number of seconds into the future to check 
        :param OverlapDowntimesList downtime_collection_list: 
        :return OverlapDwontimes/None:
        """
        self.log.debug('Starting.')
        now = time.time()
        out = None

        # -------------------------------------------------
        def check_interval(seconds):
            out = None
            if seconds == None:
                self.log.info('configuration = None, no action will be done.')
            else:
                if (now + seconds) in timeinterval or\
                   timeinterval < (now + seconds):
                    out = downtime_collection
            return out
        # -------------------------------------------------

        for downtime_collection in downtime_collection_list.getlist():
            timeinterval = downtime_collection.getTimeInterval()
            self.log.info('there is a time interval: %s - %s' %(timeinterval.start_t, timeinterval.end_t))

            if timeinterval.shorter_than(self.max_duration_tooshort):
                self.log.info('The timeinterval is too short, no need for action.')
            else:
                # check for short timeinterval
                if timeinterval.shorter_than(self.max_duration_short):
                    seconds = downtime_length_d['short']
                    out = check_interval(seconds)
                    if out:
                        break
                else:
                    # long timeinterval
                    seconds = downtime_length_d['long']
                    out = check_interval(seconds)
                    if out:
                        break

        else:
            out = None
        self.log.debug('Leaving with value %s.' %out)
        return out


    def _transition_allowed(self, event):
        """
        :param Event event: includes the new status and the probe
        :return bool:
        """
        # FIXME: 
        # this is just a prototype. 
        # Investigate a nicer solution.
        # If one day this class is implemented trully as a state machine,
        # Transitions can be a class.
        # But for now this is OK
        self.log.debug('Starting.')
        forbidden_transitions = [(None, 'online'),
                                 ('unrecognized', 'online'),
                                ]
        attempted_transition = (event.old_status, event.new_status)
        if attempted_transition in forbidden_transitions:
            msg = 'Transition "{initial}" -> "{final}" not allowed '
            msg = msg.format(initial=event.old_status, final=event.new_status)
            self.log.info(msg)
            out = False
        else:
            out = True
        self.log.debug('Leaving, with output %s.' %out)
        return out




    # -------------------------------------------------------------------------

    def act(self, agisapi):
        """
        acts to change status of entities, based on the result
        of the evaluate() call.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting over Queue %s.' %self.name)
        self._act_on_ce(agisapi)
        self._act_on_queue(agisapi)
        self.log.info('Leaving.')


    def _act_on_ce(self, agisapi):
        """
        Pass the call to the CEs
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting over queue %s.' %self.name)
        for ce in self.cehandler.getlist():
            ce.act(agisapi)
        self.log.info('Leaving.')


    def _act_on_queue(self, agisapi):
        """
        Acting on the actual Queue entity.
        :param serverapi agisapi: interface to change entities status in AGIS
        """
        self.log.info('Acting over queue %s.' %self.name)
        if self.event and\
           not self.event.done:
            self.log.info('There is an Event object recorded for queue %s. Acting.' %self.name)
            self._change_status(agisapi)
        self.log.info('Leaving.')


    def _change_status(self, agisapi):
        """
        Performing the actual actions to change the Queue.
        change the status of this queue.
        :param str new_status: the new status value
        """
        self.log.debug('Starting.')
        if not self.event.status_changed:
            self.log.debug('Queue %s did not changed status. Nothing to do.' %self.name) 
        else:
            self.log.info('Changing status for queue %s.' %self.name) 
            new_status = self.event.new_status
            try:
                out, err, rc = agisapi.change_queue_status(self.event)
            except Exception as ex:
                self.log.error('Exception caught changing status: %s' %ex)
            else:
                self.log.info('Output, Err, and RC from changing status: %s, %s, %s' %(out, err, rc))
                self.status = new_status
                self.event.done = True
        self.log.debug('Leaving.')

    # -------------------------------------------------------------------------

                   
    def _collect_events(self):
        """
        grab all Event instances for this queue
        """
        self.log.info('Starting collecting Events for queue %s.' %self.name)
        queue_event_l = QueueEventList(self.name)

        # first check for this Queue's Event
        if self.event and self.event.status_changed and self.event.done:
            self.log.info('Adding to the list an Event for queue %s' %self.name)
            queue_event_l.add(self.event)
        # second, check for all CEs in this Queue
        for event in self.cehandler._collect_events():
            queue_event_l.add(event)
        # FIXME
        #self.log.info('Queue %s has %s Events. '%(self.name, len(event_l)))
        return queue_event_l

    # -------------------------------------------------------------------------

    def __str__(self):
        """
        ancillary method to get a friendly, easy to read, 
        representation of the topology
        """
        str = super(Queue, self).__str__()
        str += '                switcher status %s\n' %self.switcher_status
        return str




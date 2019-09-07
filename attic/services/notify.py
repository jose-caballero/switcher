#!/usr/bin/env python


import logging
import smtplib
import time

try:
    from email.mime.text import MIMEText
except:
    from email.MIMEText import MIMEText

from switcher.utils import timestamp_now

class Email(object):


    def __init__(self, active): 
        self.log = logging.getLogger('email')
        self.sender = 'adcssb02@mail.cern.ch'  # FIXME
        self.serverhost = 'localhost' # FIXME
        self.active = active 

        # FIXME
        # prototype
        self.conf = None
        self.cloud = None
        self.cloud_event_l = None


    def send_notification(self):
        """
        """

        self.log.debug('Starting.')
        # FIXME
        # prototype
        total_l = self.cloud_event_l.get_changed()
        self.log.debug('Total amount of events to process for notification: %s.' %len(total_l))


        if not total_l:
            return

        to = self.conf.get('CLOUD-NOTIFICATIONS', self.cloud)
        #cc = 'atlas-adc-notifications-autoexclusion-queues@cern.ch'
        cc = self.conf.get('CLOUD-NOTIFICATIONS', 'extra_recipients')
        if cc == 'None':
            cc = ''
        subject = '[Switcher3 AutoExclusion] Summary for {cloud} at {time}'
        subject = subject.format(cloud=self.cloud, time=timestamp_now())
        body = self._build_body()
        message = MIMEText(body)
        message['subject'] = subject
        message['From'] = self.sender 
        message['To'] = to
        message['Cc'] = cc
        to = [x.strip() for x in to.split(',')]
        cc = [x.strip() for x in cc.split(',')]
        to += cc

        self._send(to, message)
        self.log.debug('Leaving.')


    # FIXME: this is a prototype
    # FIXME: consider using a template, and fill it with Jinja2 (or similar tool)
    def _build_body(self):
        """
        compose the body for the email notification
        :param dict event_d: dictionary of Events per Site
        """
        self.log.debug('Starting.')

        body = ""

        if not self.active:
            body += 'WARNING:\n'
            body += 'The Switcher probe is currently DISABLED in AGIS.\n'
            body += 'All actions performed by Switcher to modify the status of PanDA queue will be ignored by AGIS until the probe is set ACTIVE again.\n'
            body += '\n\n'

        body += 'Dear %s Cloud Support,\n' %self.cloud
        body += '    Please note that following PanDA Site IDs and/or CE Endpoints have been excluded/recovered by the AutoExclusion tool.\n'
        body += '    Note that, for the PanDA queues, the manual status settings in AGIS may override the status set here.\n\n\n'

        for site_event_l in self.cloud_event_l.list():
            self.log.debug('Processing site %s.' %site_event_l.name)
            
            for queue_event_l in site_event_l.list():
                self.log.debug('Processing queue %s.' %queue_event_l.name)

                # FIXME
                # using break and continue are very error prone
                # do it in a different way
                event_l = queue_event_l.list()
                if len(event_l) == 0:
                    continue
                
                body += '    Site %s:\n' % site_event_l.name
                body += '        PanDA Resource %s:\n' % queue_event_l.name

                for event in event_l:

                    if event.status_changed:

                        if event.entitytype == 'Queue':
                            self.log.debug('Event type is Queue')
                            body += '            PanDA Resource: %s\n' %event.uid
                            body += '            status changed from %s to %s\n' %(event.old_status, event.new_status)
                            if event.overlap_downtimes:
                                body += '            Reason:\n'
                                for downtime in event.overlap_downtimes.getlist():
                                    body += '                Scheduled downtime:\n'
                                    body += '                    start time: %s UTC (%s)\n' %(downtime.start_t_str, downtime.getTimeInterval().get_original_start_t())
                                    body += '                    end time: %s UTC (%s)\n' %(downtime.end_t_str, downtime.getTimeInterval().get_original_end_t())
                                    body += '                    endpoint : %s\n' %downtime.endpoint
                                    body += '                    description: %s\n' %downtime.description
                                    body += '                    info_url: %s\n' %downtime.info_url
                            else:
                                body += '            Reason:\n'
                                body += '                downtimes are over\n'
                            body += '       \n'

                        if event.entitytype == 'CE':
                            self.log.debug('Event type is CE')
                            body += '            CE name: %s\n' %event.uid
                            body += '            status changed from %s to %s\n' %(event.old_status, event.new_status)
                            if event.downtime:
                                body += '            Reason:\n'
                                body += '                Scheduled downtime:\n'
                                body += '                    start time: %s UTC (%s)\n' %(event.downtime.start_t_str, event.downtime.getTimeInterval().get_original_start_t())
                                body += '                    end time: %s UTC (%s)\n' %(event.downtime.end_t_str, event.downtime.getTimeInterval().get_original_end_t())
                                body += '                    endpoint : %s\n' %event.downtime.endpoint
                                body += '                    description: %s\n' %event.downtime.description
                                body += '                    info_url: %s\n' %event.downtime.info_url
                            else:
                                body += '            Reason:\n'
                                body += '                downtimes are over\n'
                            body += '       \n'



                body += '\n\n'

        body += """
Switcher documentation is available at [1].
PanDA queues are set brokeroff or offline before a downtime, and set online after a downtime ends.
HammerCloud Production Funtional Tests (PFT)/Analysis Functional Tests (AFT)
may set queues to test if there are problems after a downtime ends.
You may check progress of test jobs at [2] (PFT) or [3] (AFT).
Summary of HC exclusion/recovery actions is at [4].

[1] https://twiki.cern.ch/twiki/bin/view/AtlasComputing/SwitcherBlacklisting
[2] http://bigpanda.cern.ch/dash/production?processingtype=gangarobot-pft
[3] http://bigpanda.cern.ch/dash/analysis?processingType=gangarobot
[4] http://hammercloud.cern.ch/hc/app/atlas/robot/incidents/

--
Comments or questions please direct to <atlas-adc-autoexclusion-support@cern.ch>
"""

        self.log.debug('Leaving.')
        return body






    def _send(self, to, message):
        self.log.info('Sending email to %s, from %s, with suject %s and content %s ' %(to, self.sender, message['subject'], message.get_payload()))
        try:
            self.server = smtplib.SMTP(self.serverhost)
            self.server.sendmail(self.sender, to, message.as_string())
            self.server.close()
        except Exception as ex:
            self.log.error('Failure sending email: %s.' %ex)




class EmailMock(Email):
    """
    mock class for testing
    """
    def _send(self, to, message):
        self.log.info('Fake call to send email to %s, from %s, with suject %s and content %s ' %(to, self.sender, message['subject'], message.get_payload()))


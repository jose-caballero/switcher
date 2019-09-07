#!/usr/bin/env python

#
#   daemon for Switcher
#
# author = Jose Caballero <jcaballero@bnl.gov>
#

import logging
import os
import pwd
import sys
import socket
import time
import traceback

from ConfigParser import SafeConfigParser
from optparse import OptionParser

from switcher.services.serverapi import AGIS, AGISMock
from switcher.services.notify import Email, EmailMock
from switcher.switcherexceptions import SwitcherConfigurationFailure, SwitcherEmailSendFailure
from switcher.topology.topology import Topology
from switcher.utils import AllowedEntities, load_json, send_notifications


# =============================================================================

def send_failure_notification(subject, body, to):
    #FIXME: From is hardcoded 
    #       when fixed, we can call send_notifications directly
    send_notifications(subject, 
                       body,
                       'adcssb02@mail.cern.ch',
                       to)

# =============================================================================


class SwitcherCLI(object):

    def __init__(self):
        self.__parseopts()
        self.__createconfig()
        self.__readconfig()
        self.__setuplogging()
        self.__checkroot()


    def __parseopts(self):

        parser = OptionParser()
        parser.add_option('--conf', 
                          dest='conffile',
                          default='/etc/switcher/switcher.conf',
                          action='store',
                          metavar='FILE1[,FILE2,FILE3]',
                          help='Load configuration from FILEs (comma separated list)')
        (self.options, self.args) = parser.parse_args()


    def __readconfig(self):
        """
        reads the basic configuration parameters for the daemon
        """
        self.logfile = self.switcherconf.get('SWITCHER', 'logfile')

        loglevel = self.switcherconf.get('SWITCHER', 'loglevel')
        if loglevel == 'debug':
            self.loglevel = logging.DEBUG
        elif loglevel == 'info':
            self.loglevel = logging.INFO
        elif loglevel == 'warning':
            self.loglevel = logging.WARNING

        self.runAs = self.switcherconf.get('SWITCHER', 'runAs')

        self.dryrun = self.switcherconf.getboolean('SWITCHER', 'dryrun')
        self.allow_notifications = self.switcherconf.getboolean('SWITCHER', 'allow_notifications')
        self.failure_notifications = self.switcherconf.get('SWITCHER', 'failure_notifications')


    def __setuplogging(self):
        """
        Setup logging 
        
        General principles we have tried to used for logging: 
        
        -- Logging syntax and semantics should be uniform throughout the program,  
           based on whatever organization scheme is appropriate.  
        
        -- Have sufficient DEBUG messages to show domain problem calculations input and output.
           DEBUG messages should never span more than one line. 
        
        -- A moderate number of INFO messages should be logged to mark major  
           functional steps in the operation of the program,  
           e.g. when a persistent object is instantiated and initialized,  
           when a functional cycle/loop is complete.  
           It would be good if these messages note summary statistics,  
           e.g. "the last submit cycle submitted 90 jobs and 10 jobs finished".  
           A program being run with INFO log level should provide enough output  
           that the user can watch the program function and quickly observe interesting events. 
        
        -- Initially, all logging should be directed to a single file.  
           But provision should be made for eventually directing logging output from different subsystems  
           (submit, info, proxy management) to different files,  
           and at different levels of verbosity (DEBUG, INFO, WARN), and with different formatters.  
           Control of this distribution should use the standard Python "logging.conf" format file: 
        
        -- All messages are always printed out in the logs files, 
           but also to the stderr when DEBUG or INFO levels are selected. 
        
        -- We keep the original python levels meaning,  
           including WARNING as being the default level.  
        
                DEBUG      Detailed domain problem information related to scheduling, calculations,
                           program state.  
                INFO       High level confirmation that things are working as expected.  
                WARNING    An indication that something unexpected happened,  
                           or indicative of some problem in the near future (e.g. 'disk space low').  
                           The software is still working as expected. 
                ERROR      Due to a more serious problem, the software has not been able to perform some function. 
                CRITICAL   A serious error, indicating that the program itself may be unable to continue running. 
        
        """
        self.log = logging.getLogger()

        logfile = os.path.expanduser(self.logfile)
        if logfile == 'syslog':
            logStream = logging.handlers.SysLogHandler('/dev/log')
        elif logfile == 'stdout':
            logStream = logging.StreamHandler()
        else:
            lf = os.path.expanduser(logfile)
            logdir = os.path.dirname(lf)
            if not os.path.exists(logdir):
                os.makedirs(logdir)
            runuid = pwd.getpwnam(self.runAs).pw_uid
            rungid = pwd.getpwnam(self.runAs).pw_gid
            os.chown(logdir, runuid, rungid)
            logStream = logging.FileHandler(filename=lf)

        FORMAT='%(asctime)s (UTC) [ %(levelname)s ] %(name)s %(filename)s:%(lineno)d %(funcName)s(): %(message)s'
        formatter = logging.Formatter(FORMAT)
        formatter.converter = time.gmtime  # to convert timestamps to UTC
        logStream.setFormatter(formatter)
        self.log.addHandler(logStream)
        self.log.setLevel(self.loglevel)
        self.log.info('Logging initialized.')


    def __checkroot(self):
        """
        If running as root, drop privileges to --runas' account.
        """
        starting_uid = os.getuid()
        starting_gid = os.getgid()
        starting_uid_name = pwd.getpwuid(starting_uid)[0]

        hostname = socket.gethostname()

        if os.getuid() != 0:
            self.log.info("Already running as unprivileged user %s at %s" % (starting_uid_name, hostname))

        if os.getuid() == 0:
            try:
                runuid = pwd.getpwnam(self.runAs).pw_uid
                rungid = pwd.getpwnam(self.runAs).pw_gid
                os.chown(self.logfile, runuid, rungid)

                os.setgid(rungid)
                os.setuid(runuid)
                os.seteuid(runuid)
                os.setegid(rungid)

                self.log.info("Now running as user %d:%d at %s..." % (runuid, rungid, hostname))

            except KeyError as e:
                self.log.critical('No such user %s, unable run properly. Error: %s' % (self.options.runAs, e))
                send_failure_notification('[Switcher3 FATAL Failure]', 
                                          'Switcher3 service shut down, unable to change user', 
                                          self.failure_notifications)
                sys.exit(1)

            except OSError as e:
                self.log.critical('Could not set user or group id to %s:%s. Error: %s' % (runuid, rungid, e))
                send_failure_notification('[Switcher3 FATAL Failure]', 
                                          'Switcher3 service shut down, unable to change user',
                                          self.failure_notifications)
                sys.exit(1)


    def __createconfig(self):
        """
        get the basic configuration for the daemon
        """
        self.switcherconf = SafeConfigParser()
        self.switcherconf.readfp(open(self.options.conffile))
        

    def run(self):
        """
        Create Switcher object and enter main loop
        """
        try:
            self.log.info('Creating Switcher object and entering main loop...')

            switcherloop = SwitcherLoop(self.switcherconf)
            switcherloop.run(self.dryrun, self.allow_notifications)

        except KeyboardInterrupt:
            self.log.info('Caught keyboard interrupt - exitting')
            switcher.stop()
            sys.exit(0)
        except SwitcherConfigurationFailure as e:
            self.log.critical('Switcher configuration failure: %s', e)
            send_failure_notification('[Switcher3 FATAL Failure]', 
                                      'Switcher3 service shut down due Configuration Failure',
                                      self.failure_notifications)
            sys.exit(1)
        except ImportError as e:
            self.log.critical('Failed to import necessary python module: %s' % e)
            send_failure_notification('[Switcher3 FATAL Failure]', 
                                      'Switcher3 service shut down due Import Error',
                                      self.failure_notifications)
            sys.exit(1)
        except Exception as ex:
            self.log.critical("""Please report to Jose <jcaballero@bnl.gov>""")
            self.log.critical(traceback.format_exc(None))
            print(traceback.format_exc(None))
            send_failure_notification('[Switcher3 FATAL Failure]', 
                    'Switcher3 service shut down due Unkown Error: %s' %ex, 
                    self.failure_notifications)
            sys.exit(1)



class SwitcherLoop(object):
    """
    class to implement the main loop
    """

    def __init__(self, switcherconf):
        self.log = logging.getLogger('switcher')
        self.switcherconf = switcherconf
        self.shutdown = False
        self.sleep = self.switcherconf.getint('SWITCHER', 'sleep')


    def run(self, dryrun, allow_notifications):
        """
        main loop
        """
        try:
            while not self.shutdown:
                try:
                    switcher = Switcher(self.switcherconf)
                    switcher._run(dryrun, allow_notifications)
                except SwitcherConfigurationFailure as ex:
                    self.log.critical('Exception raised during Switcher main loop run: %s.' % ex)
                except SwitcherEmailSendFailure as ex:
                    self.log.critical('Exception raised during Switcher main loop run: %s.' % ex)
                except Exception as ex:
                    self.log.critical('Exception raised during Switcher main loop run: %s.' % ex)
                time.sleep(self.sleep)
                self.log.debug('Checking for interrupt.')
        except Exception as ex:
        # FIXME: unless we used specific Exceptions inside while loop, this code will never run 
            self.log.fatal('Unrecognized Exception raised during Switcher main loop run: %s. Aborting.' % ex)
            self.shutdown = True
            raise ex
        self.log.debug('Leaving.')



class Switcher(object):
    """
    class implementing actions to be performed on 
    each cycle of the loop
    """

    def __init__(self, switcherconf):
        """
        :param SafeConfigParser switcherconf: primary config object
        """
        self.log = logging.getLogger('switcher')
        self.shutdown = False
        self.switcherconf = switcherconf

        self.__readconfig()


    def __readconfig(self):     
        """
        get the configuration parameters for this class
        and create the rest of Config objects
        """
        self.sleep = self.switcherconf.getint('SWITCHER', 'sleep')

        downtimesconf = self.switcherconf.get('SWITCHER', 'downtimesconf')
        self.downtimesconf = SafeConfigParser()
        self.downtimesconf.readfp(open(downtimesconf))

        notificationsconf = self.switcherconf.get('SWITCHER', 'notificationsconf')
        self.notificationsconf = SafeConfigParser()
        self.notificationsconf.readfp(open(notificationsconf))

        self.schedconfig = self.switcherconf.get('SOURCE', 'schedconfig')
        self.ddmtopology = self.switcherconf.get('SOURCE', 'ddmtopology')
        self.switcherstatus = self.switcherconf.get('SOURCE', 'switcherstatus')
        self.sites = self.switcherconf.get('SOURCE', 'sites')
        self.downtimescalendar = self.switcherconf.get('SOURCE', 'downtimescalendar')

        self.probe_state_source = self.switcherconf.get('SOURCE', 'probestate')

        self.allowed_clouds = self.__get_allowed_entities('clouds')
        self.allowed_sites = self.__get_allowed_entities('sites')
        self.allowed_queues = self.__get_allowed_entities('queues')


    def __get_allowed_entities(self, name):
        """
        gets from the schedconfig if certain entitties
        are allowed or excluded.
        :param string name: can be "clouds", "sites" or "queues"
        :return AllowedEntities:
        """

        config_allowed_key = 'allowed_%s' %name
        config_excluded_key = 'excluded_%s' %name

        def _get_value(key):
            if self.switcherconf.has_option('SOURCE', key):
                value = self.switcherconf.get('SOURCE', key)
                if value == 'None':
                    value = None
                if value is not None:
                    value = [x.strip() for x in value.split(',')]
            else:
                value = None
            return value
        
        allowed = _get_value(config_allowed_key)
        excluded = _get_value(config_excluded_key)
        return AllowedEntities(allowed, excluded) 


#    def run(self, dryrun=False, allow_notifications=True):
#        """
#        main loop
#        """
#        try:        
#            while not self.shutdown:
#                try:
#                    self._run(dryrun, allow_notifications)
#                except Exception as ex:
#                    self.log.error('Exception raised during Switcher main loop run: %s.' % ex)
#                time.sleep(self.sleep) 
#                self.log.debug('Checking for interrupt.')
#        except Exception as ex:
#        # FIXME: unless we used specific Exceptions inside while loop, this code will never run 
#            self.log.error('Unrecognized Exception raised during Switcher main loop run: %s. Aborting.' % ex)
#            self.shutdown = True
#            raise ex
#        self.log.debug('Leaving.')


    def _run(self, dryrun=False, allow_notifications=True):
        """
        actual actions performed in the main loop
        """
        self.log.info('Starting new loop.')

        # FIXME
        # passing allow_only and excluded_queues should be done in a better way
        # this is a temporary solution
        topology = Topology(self.schedconfig, self.allowed_clouds, self.allowed_sites, self.allowed_queues, self.ddmtopology, self.notificationsconf, self.downtimesconf)
        topology.add_switcher_status(self.switcherstatus)
        topology.add_downtimes(self.downtimescalendar)
        topology.add_nucleus(self.sites)
        self.log.info('Topology tree generated %s.' %topology)

        if dryrun:
            agis = AGISMock(self.switcherconf)
        else:
            agis = AGIS(self.switcherconf)

        try:
            probe_state = load_json(self.probe_state_source)['switcher']['state'].lower()
        except Exception as ex:
            self.log.critical('Unable to read probe state configuration from src. Exception: %s' %ex)
            raise SwitcherConfigurationFailure(self.probe_state_source, ex)
        active = (probe_state == 'active')
        if allow_notifications:
            email = Email(active)
        else:
            email = EmailMock(active)

        topology.evaluate()
        topology.act(agis)
        topology.reevaluate(self.schedconfig)
        topology.notify(email)

        # =====================================================================
        # FIXME 
        # temporary solution
        # =====================================================================
        from switcher.services.ssb import ssb, ssbmock
        if dryrun:
            ssb_fun = ssbmock
        else:
            ssb_fun = ssb
        ssb_fun(topology)

        self.log.info('Actions finished.')


if __name__ == '__main__':
    
    cli = SwitcherCLI()
    cli.run()



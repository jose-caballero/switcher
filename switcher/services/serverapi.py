#!/usr/bin/env python

import logging
import subprocess


from switcher.switcherexceptions import SwitcherServiceFailure

class AGIS(object):

    def __init__(self, switcherconf):
        self.log = logging.getLogger('agis')
        self.switcherconf = switcherconf

        # FIXME
        # temporary solution
        self.x509_cert_dir = self.switcherconf.get('SERVERAPI', 'x509_cert_dir')
        self.x509_user_proxy = self.switcherconf.get('SERVERAPI', 'x509_user_proxy')


    def change_queue_status(self, event):

        queue = event.uid
        status = event.new_status
        comment = event.comment

        url = ''
        url = url.format(panda_resource=queue, value=status.upper(), reason=comment)
        cmd = 'curl --capath {capath} --cacert {cert} --cert {cert} \'{url}\'' 
        cmd = cmd.format(capath=self.x509_cert_dir, cert=self.x509_user_proxy, url=url)
        
        return self._run_command(cmd)


    def change_ce_status(self, event):

        ###ce_name = event.uid.split(':')[0]  # remove the port in case it is part of the CE endpoint string
        ce_name = event.uid
        status = event.new_status
        comment = event.comment

        url = '' %(ce_name, status.upper(), comment)
        cmd = 'curl --capath {capath} --cacert {cert} --cert {cert} \'{url}\'' 
        cmd = cmd.format(capath=self.x509_cert_dir, cert=self.x509_user_proxy, url=url)
        return self._run_command(cmd)



    def _run_command(self, cmd):

        self.log.info('Attempt to run command: %s' %cmd)
        try:
            # FIXME: figure out how to do this with a python library (pycurl, urllib, ...)
            subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            (out, err) = subproc.communicate()
            st = subproc.returncode
            return out, err, st
        except Exception as ex:
            self.log.error('Failure running command "%s": %s' %(cmd, ex))
            raise SwitcherServiceFailure(cmd, ex)


class AGISMock(AGIS):
    """
    mock class for testing
    """
    def _run_command(self, cmd):
        self.log.info('Fake call to run command %s' %cmd)
        return None, None, None

    

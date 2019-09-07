#!/usr/bin/env python
#
# Setup for Switcher
#
#

release_version="3.1.1"

import os
import re
import sys

from setuptools import setup

# ===========================================================
#                D A T A     F I L E S 
# ===========================================================

etc_files = [
            'etc/downtimes-example.conf',
            'etc/notifications-example.conf',
            'etc/switcher-example.conf',
            ]


sysconfig_files = [
            'etc/sysconfig/switcher-example',
                  ]

logrotate_files = [
            'etc/logrotate/switcher-example',
                  ]

systemd_files = [
            'etc/switcher',
            'etc/switcher.service',
                ]

# -----------------------------------------------------------

rpm_data_files=[
                ('/etc/switcher', etc_files),
                ('/etc/sysconfig', sysconfig_files),
                ('/etc/logrotate.d', logrotate_files),                                        
                ('/etc/systemd/system', systemd_files),
               ]


home_data_files=[
                 ('etc/switcher', etc_files),
                 ('etc/switcher', sysconfig_files),
                ]

# -----------------------------------------------------------

def choose_data_file_locations():
    local_install = False

    if '--user' in sys.argv:
        local_install = True
    elif any([re.match('--home(=|\s)', arg) for arg in sys.argv]):
        local_install = True
    elif any([re.match('--prefix(=|\s)', arg) for arg in sys.argv]):
        local_install = True

    if local_install:
        return home_data_files
    else:
        return rpm_data_files
       
# ===========================================================

# setup for distutils
setup(
    name="switcher",
    version=release_version,
    description='Switcher package',
    long_description="""This package contains Switcher""",
    license='GPL',
    author='Jose Caballero',
    author_email='jcaballero@bnl.gov',
    maintainer='Jose Caballero',
    maintainer_email='jcaballero@bnl.gov',
    url='https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/SwitcherBlacklisting',
    packages=['switcher',
              'switcher.agistopology',
              'switcher.topology',
              'switcher.services',
              ],
    scripts = [ # Utilities and main script
               'bin/switcher',
              ],
    
    data_files = choose_data_file_locations()
)

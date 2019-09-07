#!/usr/bin/env python


import logging
import smtplib
import time
import datetime


# =============================================================================
#   FIXME
#   this is a temporary solution
# =============================================================================

def ssb(topology):

    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    action_color_d = {'online': 'green',
                      'offline': 'red',
                      'brokeroff': 'brown',
                      'no_action': 'green'
                     }

    status_color_d = {'online': 'green',
                      'offline': 'red',
                      'brokeroff': 'brown',
                      'test': 'yellow'
                     }

    #output_switcher_actions = '/tmp/switcher_actions.data'
    #output_panda_resource_status = '/tmp/panda_resource_status.data'
    output_switcher_actions = '/data/www/switcher_actions.data'
    output_panda_resource_status = '/data/www/panda_resource_status.data'
    output_switcher_actions_f = open(output_switcher_actions, 'w') 
    output_panda_resource_status_f = open(output_panda_resource_status, 'w')
    

    for queue in topology.queue_d.values():
        panda_resource = queue.name
        if queue.event:
            action = queue.event.new_status 
            action_color = action_color_d.get(action, 'grey')
            if action != "online":
                scheduled = queue.event.overlap_downtimes.downtime_l[0].classification
                scheduled = scheduled.lower()
                action = '%s_%s' %(action, scheduled)
                if scheduled == 'unscheduled':
                    action_color = 'dark' + action_color
            action = 'set'+action
        else:
            action = 'no_action'
            action_color = action_color_d.get(action, 'grey')

        current_status = queue.status
        status_color = status_color_d.get(current_status, 'grey')
        sitetype = queue.type

        output_switcher_actions_f.write('%s %s %s %s http://xxxxxxxxxxxxxxxxxx/agis/calendar/\n' %(timestamp, panda_resource, action, action_color))
        output_panda_resource_status_f.write('%s %s %s %s %s\n' %(timestamp, panda_resource, current_status, status_color, sitetype))
 

def ssbmock(topology):
    pass


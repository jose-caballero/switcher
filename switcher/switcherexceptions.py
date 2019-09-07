#!/usr/bin/env python

    
class SwitcherServiceFailure(Exception):
    def __init__(self, cmd, ex):
        self.value = 'Failure executing command "%s" : %s' %(cmd, ex)
    def __str__(self):
        return self.value


class SwitcherConfigurationFailure(Exception):
    def __init__(self, value, ex):
        self.value = 'Failure reading configuration from %s : %s' %(value, ex)
    def __str__(self):
        return repr(self.value)


class SwitcherAGISReadFailure(Exception):
    def __init__(self, value, ex):
        self.value = 'Failure reading data from AGIS %s : %s' %(value, ex)
    def __str__(self):
        return repr(self.value)


class SwitcherAGISWriteFailure(Exception):
    def __init__(self, value, ex):
        self.value = 'Failure writing data to AGIS %s : %s' %(value, ex)
    def __str__(self):
        return repr(self.value)


class SwitcherEmailSendFailure(Exception):
    def __init__(self, value, ex):
        self.value = 'Failure sending email to %s : %s' %(value, ex)
    def __str__(self):
        return repr(self.value)










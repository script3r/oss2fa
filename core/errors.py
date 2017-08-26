from __future__ import unicode_literals


class MFAError(object):
    message = ''

    def __init__(self, message, *args, **kwargs):
        self.message = message.format(*args) if len(args) > 0 else message

    def __str__(self):
        return self.message

    def __unicode__(self):
        return self.message


class MFAMissingInformationError(MFAError):
    pass


class MFAInconsistentStateError(MFAError):
    pass


class MFASecurityError(MFAError):
    pass

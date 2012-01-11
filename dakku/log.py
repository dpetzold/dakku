from fabric import colors
import logging

from decorator import decorator
from django.http import HttpRequest

# http://stackoverflow.com/questions/384076/how-can-i-make-the-python-logging-output-to-be-colored

class StripFormatter(logging.Formatter):
    def __init__(self, format=None):
        logging.Formatter.__init__(self, format)

    def format(self, record):
        return logging.Formatter.format(self, record).strip()

class ColoredFormatter(logging.Formatter):
    def __init__(self, format=None, mappings={}):
        self.mappings = mappings
        logging.Formatter.__init__(self, format)

    def format(self, record):
        level = record.levelname.lower()
        if level in self.mappings:
            record.msg = eval('%s(record.msg)' % (self.mappings[level]))
        return logging.Formatter.format(self, record).strip()

class RequestInfo(object):

    def __init__(self, request):
        self.request = request
        super(RequestInfo, self).__init__()

    def __getitem__(self, name):
        if name == 'user.email':
            if self.request.user.is_authenticated():
                return self.request.user.email
            return '<anonymous>'
        elif name == 'path':
            return self.request.path
        elif name == 'session_key':
            return self.request.session.session_key
        else:
            return '<?>'

    def __iter__(self):
        keys = ['path', 'user.email', 'session_key']
        keys.extend(self.__dict__.keys())
        return keys.__iter__()

def logger(name='crowdtube.views'):
    def wrap(func):
        def caller(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, HttpRequest):
                    request = arg

            if 'logger' not in kwargs:
                if request is not None:
                    kwargs['logger'] = logging.LoggerAdapter(
                            logging.getLogger(name), RequestInfo(request))
                else:
                    kwargs['logger'] = logging.getLogger(name)
            return func(*args, **kwargs)
        return caller
    return wrap


from fabric import colors
import logging

from decorator import decorator
from django.http import HttpRequest

# http://stackoverflow.com/questions/384076/how-can-i-make-the-python-logging-output-to-be-colored

_logger = logging.getLogger(__name__)

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
        _logger.info(name)
        if not name.startswith('request.'):
            return None
        return eval('self.%s' % (name))

    def _get_attrs(self, obj):
        return [ a for a in dir(obj) if not a.startswith('_') and not callable(a) ]

    def __iter__(self):
        keys = []
        keys.extend(['request.%s' % (a) for a in self._get_attrs(self.request)])
        keys.extend(['request.session.%s' % (a) for a in
            self._get_attrs(self.request.session)])
        keys.extend(['request.user.%s' % (a) for a in
            self._get_attrs(self.request.user)])
        keys.extend(self.__dict__.keys())
        return keys.__iter__()

def logger(name):
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

from fabric import colors
import logging
import socket

from decorator import decorator
from django.http import HttpRequest, HttpResponse

import json
import jsonlogger

# http://stackoverflow.com/questions/384076/how-can-i-make-the-python-logging-output-to-be-colored

_logger = logging.getLogger(__name__)

class NoUserAgent(Exception):
    pass

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

class JsonFormatter(jsonlogger.JsonFormatter):
    def parse(self):
        return eval(self._fmt)

class RequestInfo(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, name):
        _logger.debug(name)
        if name == 'request.host':
            return socket.gethostname()
        if name.startswith('request.meta.'):
            val = name.split('.')[2]
            try:
                return self.request.META[val.upper()]
            except KeyError as e:
                return None
        return eval('self.%s' % (name))

    def _get_attrs(self, obj):
        attrs = []
        for attr in dir(obj):
            try:
                if not attr.startswith('_') and \
                        not callable(getattr(obj, attr)):
                    attrs.append(attr)
            except AttributeError:
                pass
        return attrs

    def __iter__(self):
        keys = ['request.host']
        keys.extend(['request.%s' % (a) for a in
                self._get_attrs(self.request)])
        keys.extend(['request.session.%s' % (a) for a in
            self._get_attrs(self.request.session)])
        keys.extend(['request.user.%s' % (a) for a in
            self._get_attrs(self.request.user)])
        keys.extend(['request.meta.%s' % (a.lower()) for a in
            self.request.META.keys()])
        _logger.debug(keys)
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


def entrypoint(name):
    def wrap(func):
        def caller(*args, **kwargs):
            for arg in args:
                if isinstance(arg, HttpRequest):
                    request = arg
                    break

            if request is not None:

                try:
                    request.META['HTTP_USER_AGENT']
                except KeyError:
                    _logger.info('No user agent')
                    response = HttpResponse(status=403)
                    response.write('Forbidden')
                    return response

                logger = logging.LoggerAdapter(
                        logging.getLogger(name), RequestInfo(request))
            else:
                logger = logging.getLogger(name)

            if request.session.exists(request.session.session_key):
                logger.info('returning visitor')
            else:
                logger.info('new visitor')

            return func(*args, **kwargs)
        return caller
    return wrap



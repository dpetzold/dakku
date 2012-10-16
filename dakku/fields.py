"""
Django Extensions additional model fields
"""

from django.db import models

import random
import string

try:
    from django.utils.timezone import now as datetime_now
except ImportError:
    import datetime
    datetime_now = datetime.datetime.now  # noqa

class BaseUniqueField(models.CharField):

    def find_unique(self, model_instance, value, callback, *args):
        # exclude the current model instance from the queryset used in finding
        # next valid hash
        queryset = model_instance.__class__._default_manager.all()
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        # form a kwarg dict used to impliment any unique_together contraints
        kwargs = {}
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                for param in params:
                    kwargs[param] = getattr(model_instance, param, None)
        kwargs[self.attname] = value

        while queryset.filter(**kwargs):
            value = callback()
            kwargs[self.attname] = value
        return value

class RandomCharField(BaseUniqueField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('editable', False)

        self.lower = kwargs.pop('lower', False)
        self.digits_only = kwargs.pop('digits_only', False)
        self.alpha_only = kwargs.pop('alpha_only', False)
        self.include_punctuation = kwargs.pop('include_punctuation', False)
        self.length = kwargs.pop('length', 8)
        kwargs['max_length'] = self.length

        # legacy
        kwargs.pop('include_digits', False)

        self.valid_chars = string.lowercase

        if self.digits_only:
            self.valid_chars = string.digits
        else:
            if not self.lower:
                self.valid_chars += string.uppercase

            if not self.alpha_only:
                self.valid_chars += string.digits

            if self.include_punctuation and not self.alpha_only:
                self.valid_chars += string.punctuation

        super(RandomCharField, self).__init__(*args, **kwargs)

    def generate_chars(self, *args, **kwargs):

        return ''.join([random.choice(list(self.valid_chars)) for x in range(self.length)])

    def pre_save(self, model_instance, add):
        if not add:
            return getattr(model_instance, self.attname)

        initial = self.generate_chars()
        value = self.find_unique(model_instance, initial, self.generate_chars)
        setattr(model_instance, self.attname, value)
        return value

    def get_internal_type(self):
        return "CharField"

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = '%s.RandomCharField' % (self.__module__)
        args, kwargs = introspector(self)
        kwargs.update({
            'alpha_only': repr(self.alpha_only),
            'digits_only': repr(self.digits_only),
            'include_punctuation': repr(self.include_punctuation),
            'length': repr(self.length),
            'lower': repr(self.lower),
        })
        # That's our definition!
        return (field_class, args, kwargs)

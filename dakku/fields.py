"""
Django Extensions additional model fields
"""

from django.db.models import CharField

import random
import string

try:
    from django.utils.timezone import now as datetime_now
except ImportError:
    import datetime
    datetime_now = datetime.datetime.now  # noqa

class BaseAutoField(object):

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

        # increases the number while searching for the next valid slug
        # depending on the given slug, clean-up

        slug = args[0]
        next = int(args[1])
        while queryset.filter(**kwargs):
            value = callback(slug, next)
            next += 1
            kwargs[self.attname] = value
        setattr(model_instance, self.attname, value)
        return value

class RandomCharField(BaseAutoField, CharField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('editable', False)

        self.lower = kwargs.pop('lower', False)
        self.include_digits = kwargs.pop('include_digits', True)
        self.length = kwargs.pop('length', 8)
        kwargs['max_length'] = self.length
        super(RandomCharField, self).__init__(*args, **kwargs)

    def generate_hash(self, chars):
        return ''.join([random.choice(list(chars)) for x in range(self.length)])

    def pre_save(self, model_instance, add):
        if not add:
            return getattr(model_instance, self.attname)
        if self.lower:
            chars = string.lowercase
        else:
            chars = string.letters
        if self.include_digits:
            chars += string.digits

        auto_hash = self.generate_hash(chars)
        return super(RandomCharField, self).find_unique(model_instance,
                auto_hash, self.generate_hash, chars)

    def get_internal_type(self):
        return "RandomCharField"

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = '%s.AutoHashField' % self.__module__
        args, kwargs = introspector(self)
        kwargs.update({
            'lower': repr(self.lower),
            'include_digits': repr(self.include_digits),
            'length': repr(self.length),
        })
        # That's our definition!
        return (field_class, args, kwargs)

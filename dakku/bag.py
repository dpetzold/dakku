import json

class Bag(dict):
    # http://stackoverflow.com/questions/1305532/convert-python-dict-to-object
    def __init__(self, d={}):
        for a, b in d.iteritems():
            if a is None:
                continue
            a  = a.lower().replace('$', '')
            if a == 'class':
                a = 'klass'
            if isinstance(b, (list, tuple)):
               setattr(self, a, [Bag(x) if isinstance(x, dict) else x for x in b])
            else:
               setattr(self, a, Bag(b) if isinstance(b, dict) else b)

    def todict(self):
        d = {}
        for attr, val in self.iteritems():
            if isinstance(val, (list, tuple)):
                d[attr] = [x.todict() if isinstance(x, Bag) else x for x in val]
            elif callable(val):
                continue
            else:
                d[attr] = val.todict() if isinstance(val, Bag) else val
        return d

    def __getitem__(self, key):
        print(key)

    def __str__(self):
        return json.dumps(self.todict(), indent=4, cls=JsonEncoder)

    def __len__(self):
        return len(self.todict())

    def __iter__(self):

        for attr in dir(self):
            if attr.startswith('__') or  attr == 'todict':
                continue
            val = getattr(self, attr)
            if callable(val):
                continue
            yield attr

    def iteritems(self):
        for attr in self:
            yield attr, getattr(self, attr)

    def itervalues(self):
        for attr in self:
            yield getattr(self, attr)

class JsonEncoder(json.JSONEncoder):
    def default(self, obj):

        if isinstance(obj, datetime.datetime):
            return str(obj)

        try:
            if issubclass(obj, dict) or issubclass(obj, list):
                return list(obj)
        except:
            pass

        return json.JSONEncoder.default(self, obj)

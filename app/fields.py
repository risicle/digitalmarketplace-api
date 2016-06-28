from sqlalchemy.ext.mutable import Mutable

from six import iteritems

def _coerce_item_value(cls, value):
    if isinstance(value, dict):
        return RecursiveMutableDict(value)
    elif isinstance(value, (list, tuple,)):
        return RecursiveMutableList(value)
    else:
        return value

class RecursiveMutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to RecursiveMutableDict."
        if value is None:
            # it's not our job to filter out nulls here
            return None
        elif not isinstance(value, RecursiveMutableDict):
            if isinstance(value, dict):
                return RecursiveMutableDict(value)

            # this call will raise ValueError
            return super(RecursiveMutableDict, cls).coerce(key, value)
        else:
            return value

    @staticmethod
    def _common_init_update_inner(*args, **kwargs):
        if args:
            if hasattr(args[0], "items") and callable(args[0].items):
                args[0] = {k: _coerce_item_value(v) for k, v in iteritems(args[0])}
            else:
                args[0] = tuple((k,_coerce_item_value(v)) for k, v in args[0])
        kwargs = {k: _coerce_item_value(v) for k, v in iteritems(kwargs)}
        return args, kwargs

    def __init__(self, *args, **kwargs):
        args, kwargs = self._common_init_update_inner(*args, **kwargs)
        

    def __setitem__(self, key, value):
        # intercept and coerce any newly assigned json-like values
        r = super(RecursiveMutableDict, self).__setitem__(key, _coerce_item_value(value))
        self.changed()
        return r

    def __delitem__(self, *args, **kwargs):
        r = super(RecursiveMutableDict, self).__delitem__(*args, **kwargs)
        self.changed()
        return r

    def clear(self, *args, **kwargs):
        r = super(RecursiveMutableDict, self).clear(*args, **kwargs)
        self.changed()
        return r

    def pop(self, *args, **kwargs):
        r = super(RecursiveMutableDict, self).pop(*args, **kwargs)
        self.changed()
        return r

    def popitem(self, *args, **kwargs):
        r = super(RecursiveMutableDict, self).popitem(*args, **kwargs)
        self.changed()
        return r

    def setdefault(self, *args, **kwargs):
        # intercept and coerce any newly assigned json-like values
        if len(args)>1:
            args[1] = _coerce_item_value(args[1])
        r = super(RecursiveMutableDict, self).setdefault(*args, **kwargs)
        self.changed()
        return r

    def update(self, *args, **kwargs):
        # a slightly intricate little dance here to make sure we intercept and coerce any newly assigned json-like
        # values
        if args:
            if hasattr(args[0], "items") and callable(args[0].items):
                args[0] = {k: _coerce_item_value(v) for k, v in iteritems(args[0])}
            else:
                args[0] = tuple((k,_coerce_item_value(v)) for k, v in args[0])
        kwargs = {k: _coerce_item_value(v) for k, v in iteritems(kwargs)}
        r = super(RecursiveMutableDict, self).update(*args, **kwargs)
        self.changed()
        return r

class RecursiveMutableList(Mutable, list):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to RecursiveMutableList."
        if value is None:
            # it's not our job to filter out nulls here
            return None
        elif not isinstance(value, RecursiveMutableList):
            if isinstance(value, (tuple, list,)):
                return RecursiveMutableList(value)

            # this call will raise ValueError
            return super(RecursiveMutableList, cls).coerce(key, value)
        else:
            return value
    
    def __setitem__(self, key, value):
        # intercept and coerce any newly assigned json-like values
        if isinstance(key, slice):
            value = tuple(_coerce_item_value(v) for v in value)
        else:
            value = _coerce_item_value(value)
        r = super(RecursiveMutableList, self).__setitem__(key, value)
        self.changed()
        return r

    def __delitem__(self, *args, **kwargs):
        r = super(RecursiveMutableList, self).__delitem__(*args, **kwargs)
        self.changed()
        return r

    def __setslice__(self, i, j, seq):
        # apparently though this method is deprecated since python 2.0 we still have to implement it as the cpython
        # builtin types still implement it.
        # intercept and coerce any newly assigned json-like values
        seq = tuple(_coerce_item_value(v) for v in seq)
        r = super(RecursiveMutableList, self).__setslice__(i, j, seq)
        self.changed()
        return r

    def __delslice__(self, *args, **kwargs):
        r = super(RecursiveMutableList, self).__delslice__(*args, **kwargs)
        self.changed()
        return r

    def __iadd__(self, seq):
        # intercept and coerce any newly assigned json-like values
        seq = tuple(_coerce_item_value(v) for v in seq)
        r = super(RecursiveMutableList, self).__iadd__(seq)
        self.changed()
        return r

    def __imul__(self, *args, **kwargs):
        r = super(RecursiveMutableList, self).__imul__(*args, **kwargs)
        self.changed()
        return r

    def append(self, value):
        r = super(RecursiveMutableList, self).append(_coerce_item_value(value))
        self.changed()
        return r

    def extend(self, seq):
        seq = tuple(_coerce_item_value(v) for v in seq)
        r = super(RecursiveMutableList, self).extend(seq)
        self.changed()
        return r

    def insert(self, i, value):
        r = super(RecursiveMutableList, self).insert(i, _coerce_item_value(value))
        self.changed()
        return r

    def pop(self, *args, **kwargs):
        r = super(RecursiveMutableList, self).pop(*args, **kwargs)
        self.changed()
        return r

    def reverse(self, *args, **kwargs):
        r = super(RecursiveMutableList, self).reverse(*args, **kwargs)
        self.changed()
        return r

    def sort(self, *args, **kwargs):
        r = super(RecursiveMutableList, self).sort(*args, **kwargs)
        self.changed()
        return r

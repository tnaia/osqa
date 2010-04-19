import inspect

class OverridableObject(object):
    def __init__(self, obj):
        self._origin = obj
        self._type = (inspect.isfunction(obj) and "function") or (inspect.ismethod(obj) and "method")

        self._override = None

    def override(self, fn, needs_origin):
        def overrided(*args, **kwargs):
            if needs_origin:
                return fn(self._origin, *args, **kwargs)
            else:
                return fn(*args, **kwargs)

        self._override = overrided

    def __call__(self, *args, **kwargs):
        if self._override is None:
            return self._origin(*args, **kwargs)
        else:
            return self._override(*args, **kwargs)


def overridable(fn):
    return OverridableObject(fn)

def override(origin, needs_origin=False):
    if not isinstance(origin, OverridableObject):
        raise Exception('Not an overridable function: %s' % origin.name)

    def decorator(fn):
        origin.override(fn, needs_origin)
        return origin

    return decorator


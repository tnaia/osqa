import cPickle as pickle

class SettingSet(list):
    def __init__(self, name, title, description, weight=1000):
        self.name = name
        self.title = title
        self.description = description
        self.weight = weight

class BaseSetting():
    def __init__(self, name, default, field_context):
        self.name = name
        self.default = default
        self.field_context = field_context

    @property
    def value(self):
        from forum.models import KeyValue

        try:
            kv = KeyValue.objects.get(key=self.name)
        except:
            kv = KeyValue(key=self.name, value=pickle.dumps(self.default))
            kv.save()

        return pickle.loads(kv.value.encode('utf-8'))

    def set_value(self, new_value):
        new_value = self._parse(new_value)
        from forum.models import KeyValue

        try:
            kv = KeyValue.objects.get(key=self.name)
        except:
            kv = KeyValue(key=self.name)

        kv.value = pickle.dumps(new_value)
        kv.save()


    def _parse(self, value):
        return value

    def __str__(self):
        return str(self.value)

    def __unicode__(self):
        return unicode(self.value)

    def __nonzero__(self):
        return bool(self.value)


class StringSetting(BaseSetting):
    def _parse(self, value):
        return str(value)

    def __add__(self, other):
        return str(self) + str(other)

    def __cmp__(self, other):
        return cmp(str(self), str(other))

class IntegerSetting(BaseSetting):
    def _parse(self, value):
        return int(value)

    def __int__(self):
        return int(self.value)

    def __add__(self, other):
        return int(self) + int(other)

    def __sub__(self, other):
        return int(self) - int(other)

    def __cmp__(self, other):
        return int(self) - int(other)

class BoolSetting(BaseSetting):
    def _parse(self, value):
        return bool(value)


class Setting(object):
    sets = {}

    def __new__(cls, name, default, set=None, field_context={}):
        if isinstance(default, bool):
            instance = BoolSetting(name, default, field_context)
        elif isinstance(default, str):
            instance = StringSetting(name, default, field_context)
        elif isinstance(default, int):
            instance = IntegerSetting(name, default, field_context)
        else:
            instance = BaseSetting(name, default, field_context)

        if set is not None:
            if not set.name in cls.sets:
                cls.sets[set.name] = set

            cls.sets[set.name].append(instance)

        return instance



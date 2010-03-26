from django.db import models
from django.core.cache import cache
from django.conf import settings
try:
	import cPickle as pickle
except ImportError:
	import pickle
import django.dispatch

class CountableField(models.IntegerField):

    __metaclass__ = models.SubfieldBase

    def contribute_to_class(self, cls, name):

        signal_sender = object()

        def increment(instance):
            old_value = instance.__dict__[name]
            new_value = old_value + 1

            instance.__dict__[name] = new_value
            countable_update.send(sender=signal_sender, instance=instance, new_value=new_value, old_value=old_value)

        def decrement(instance):
            old_value = instance.__dict__[name]
            new_value = old_value - 1

            instance.__dict__[name] = new_value
            countable_update.send(sender=signal_sender, instance=instance, new_value=new_value, old_value=old_value)

        cls.add_to_class("increment_%s" % name, increment)
        cls.add_to_class("decrement_%s" % name, decrement)
        cls.add_to_class("%s_sender" % name, signal_sender)

        super(CountableField, self).contribute_to_class(cls, name)

countable_update = django.dispatch.Signal(providing_args=['instance', 'old_value', 'new_value'])

class PickledObject(str):
	pass

class PickledObjectField(models.Field):
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance (value, PickledObject):
            return value

        try:
            return pickle.loads(value.encode('utf-8'))
        except:
            return value
    
    def get_db_prep_save(self, value):
        if value is not None:
            if isinstance(value, PickledObject):
                return str(value)
            else:
			    value = pickle.dumps(value)

        return value

    def get_internal_type(self):
        return 'TextField'


class KeyValueManager(models.Manager):

    def create_cache_key(self, key):
        return "%s:key_value:%s" % (settings.APP_URL, key)

    def save_to_cache(self, instance):
        cache.set(self.create_cache_key(instance.key), instance, 2592000)

    def remove_from_cache(self, instance):
        cache.delete(self.create_cache_key(instance.key))

    def get(self, **kwargs):
        if 'key' in kwargs:
            instance = cache.get(self.create_cache_key(kwargs['key']))

            if instance is None:
                instance = super(KeyValueManager, self).get(**kwargs)
                self.save_to_cache(instance)

            return instance

        else:
            return super(KeyValueManager, self).get(**kwargs)

class KeyValue(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = PickledObjectField()

    objects = KeyValueManager()

    class Meta:
        app_label = 'forum'

    def save(self):
        super(KeyValue, self).save()
        KeyValue.objects.save_to_cache(self)

    def delete(self):
        KeyValue.objects.remove_from_cache(self)
        super(KeyValue, self).delete()



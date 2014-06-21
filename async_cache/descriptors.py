from datetime import datetime
import logging

try:
    import cPickle as pickle
except ImportError:
    import pickle

from async_cache.tasks import invalidate_cache

log = logging.getLogger(__name__)




class async_cache_property(object):

    def __init__(self, getter, soft_ttl, timeout=None, callback_task=None):
        '''
        :getter: function to call to generate value
        timeout: cache timeout [None = Default, False = Never]
        '''
        self.__name__ = getter.__name__

        self.soft_ttl = soft_ttl
        self.timeout = timeout
        self.callback_task = callback_task or invalidate_cache

    def _make_key(self, instance):
        '''Build the cache key to use'''
        parts = [
            instance._meta.app_label,
            instance._meta.object_name,
            str(instance.pk),
        ]
        parts.append(self.__name__)
        return ':'.join(parts)


    def __get__(self, instance, owner):
        '''Get the value, or generate if needed'''
        if instance is None:
            return self

        # Generate cache key
        key = self._make_key(instance)

        try:
            result = self.cache.get(key)
        except RuntimeError:
            import traceback
            log.error('Unpicklable [%s]: %r - %s', key, self.cache.raw_client.get(key), traceback.format_exc())
            result = None
        except pickle.UnpicklingError:
            import traceback
            log.error('Unpickling error: %r', traceback.format_exc())
            result = None

        # Cache miss, generate call the task a function
        # synchronously
        if result is None:
            value, expire = self.callback_task(
                key=key,
                app_label=instance._meta.app_label,
                model_name=instance._meta.model_name,
                pk=instance.pk,
                getter=self.__name__,
                ttl=self.soft_ttl,
                do_return=True,
            )
            self.cache.set(key, (value, expire), self.timeout)
        else:
            now = datetime.now()
            value, expire = result

            # If soft ttl has expired, schedule a task
            # to invalidate the cache and serve stale value
            if now > expire:
                self.callback_task.delay(
                    key=key,
                    app_label=instance._meta.app_label,
                    model_name=instance._meta.model_name,
                    pk=instance.pk,
                    getter=self.__name__,
                    ttl=self.soft_ttl,
                )
        return value

    def __delete__(self, instance):
        """
        Delete cached value
        """
        key = self._make_key(instance)
        self.cache.delete(key)


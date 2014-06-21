from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from datetime import datetime, timedelta


from async_cache.settings import CELERY_APP_PATH

if CELERY_APP_PATH:
    from importlib import import_module
    task = import_module('%s.app.task' % CELERY_APP_PATH)
else:
    from celery.task import task



@task(ignore_result=True)
def invalidate_cache_task(key, app_label, model_name, pk, getter, ttl, do_return=False):
    ctype = ContentType.objects.get(app_label=app_label, model=model_name)
    model = ctype.model_class()
    instance = model.objects.get(pk=pk)
    getter = getattr(instance, getter)
    value = getter()

    expire = datetime.now() + timedelta(seconds=ttl)
    cache.set(key, (value, expire), False)

    if do_return:
        return value, expire
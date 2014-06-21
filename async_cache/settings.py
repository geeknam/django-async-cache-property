from django.conf import settings

CELERY_APP_PATH = getattr(settings, 'CELERY_APP_PATH', None)

ASYNC_CACHE_TTL = getattr(settings, 'ASYNC_DEFAULT_CACHE_TTL', 60 * 5)
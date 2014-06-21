django-async-cache-property
=============================

Purpose
----------
A caching descriptor that refreshes stale cache items asynchronously using a Celery task.
The key idea being that it's better to serve a stale item (and populate the cache asynchronously) than block
the user in order to populate the cache synchronously.

Installation
-------------
    pip install django-async-cache-property


Usage
---------
Sample usage::

    # models.py

    class Article(models.Model):

        title = models.CharField(max_length=255)

        @property
        def upvote(self):
            return self.votes.filter(sign='plus').count()

        @property
        def downvote(self):
            return self.votes.filter(sign='minus').count()

        @property
        def score(self):
            return self.upvote - self.downvote

        @async_cache_property
        def ranking(self):
            """
            Your super expensive calculation
            """
            score = self.score
            order = log(max(abs(score), 1), 10)
            sign = 1 if score > 0 else -1 if score < 0 else 0
            seconds = int(time.time()) - 1134028003
            return round(order + sign * seconds / 45000, 7)


Custmisation::

    @async_cache_property(soft_ttl=60*10, timeout=60 * 60, callback_task=mytask)


- soft_ttl: after this time, the cache should be invalidated
- timeout: timeout of key in your cache backend, this prevents us serving super stale data
- callback_task: task you want to call if soft_ttl has expired

.. _api:

Huey's API
==========

Most end-users will interact with the API using the two decorators:

* :py:meth:`Huey.task`
* :py:meth:`Huey.periodic_task`

The API documentation will follow the structure of the huey API, starting with
the highest-level interfaces (the decorators) and eventually discussing the
lowest-level interfaces, the :py:class:`BaseQueue` and :py:class:`BaseDataStore` objects.

.. _function-decorators:

Function decorators and helpers
-------------------------------

.. py:class:: Huey(queue[, result_store=None[, schedule=None[, events=None[, store_none=False[, always_eager=False]]]]])

    Huey executes tasks by exposing function decorators that cause the function
    call to be enqueued for execution by the consumer.

    Typically your application will only need one Huey instance, but you can
    have as many as you like -- the only caveat is that one consumer process
    must be executed for each Huey instance.

    :param queue: a queue instance, e.g. :py:class:`RedisQueue`.
    :param result_store: a place to store results and the task schedule,
        e.g. :py:class:`RedisDataStore`.
    :param schedule: scheduler implementation, e.g. an instance of :py:class:`RedisSchedule`.
    :param events: event emitter implementation, e.g. an instance of :py:class:`RedisEventEmitter`.
    :param boolean store_none: Flag to indicate whether tasks that return ``None``
        should store their results in the result store.
    :param always_eager: Useful for testing, this will execute all tasks
        immediately, without enqueueing them.

    Example usage:

    .. code-block:: python

        from huey.api import Huey, crontab
        from huey.backends.redis_backend import RedisBlockingQueue, RedisDataStore,\
            RedisSchedule

        huey = RedisHuey('my-app')

        # THIS IS EQUIVALENT TO ABOVE CODE:
        #queue = RedisBlockingQueue('my-app')
        #result_store = RedisDataStore('my-app')
        #schedule = RedisSchedule('my-app')
        #huey = Huey(queue, result_store, schedule)

        @huey.task()
        def slow_function(some_arg):
            # ... do something ...
            return some_arg

        @huey.periodic_task(crontab(minute='0', hour='3'))
        def backup():
            # do a backup every day at 3am
            return

    .. py:method:: task([retries=0[, retry_delay=0[, retries_as_argument=False[, include_task=False]]]])

        Function decorator that marks the decorated function for processing by the
        consumer. Calls to the decorated function will do the following:

        1. Serialize the function call into a message suitable for storing in the queue
        2. Enqueue the message for execution by the consumer
        3. If a ``result_store`` has been configured, return an :py:class:`AsyncData`
           instance which can retrieve the result of the function, or ``None`` if not
           using a result store.

        .. note::
            Huey can be configured to execute the function immediately by
            instantiating it with ``always_eager = True`` -- this is useful for
            running in debug mode or when you do not wish to run the consumer.

        Here is how you might use the ``task`` decorator:

        .. code-block:: python

            # assume that we've created a huey object
            from huey import RedisHuey

            huey = RedisHuey()

            @huey.task()
            def count_some_beans(num):
                # do some counting!
                return 'Counted %s beans' % num

        Now, whenever you call this function in your application, the actual processing
        will occur when the consumer dequeues the message and your application will
        continue along on its way.

        Without a result store:

        .. code-block:: pycon

            >>> res = count_some_beans(1000000)
            >>> res is None
            True

        With a result store:

        .. code-block:: pycon

            >>> res = count_some_beans(1000000)
            >>> res
            <huey.api.AsyncData object at 0xb7471a4c>
            >>> res.get()
            'Counted 1000000 beans'

        :param int retries: number of times to retry the task if an exception occurs
        :param int retry_delay: number of seconds to wait between retries
        :param boolean retries_as_argument: whether the number of retries should
            be passed in to the decorated function as an argument.
        :param boolean include_task: whether the task instance itself should be
            passed in to the decorated function as the ``task`` argument.
        :rtype: decorated function

        The return value of any calls to the decorated function depends on whether
        the :py:class:`Huey` instance is configured with a ``result_store``.  If a
        result store is configured, the decorated function will return
        an :py:class:`AsyncData` object which can fetch the result of the call from
        the result store -- otherwise it will simply return ``None``.

        The ``task`` decorator also does one other important thing -- it adds
        a special function **onto** the decorated function, which makes it possible
        to *schedule* the execution for a certain time in the future:

        .. py:function:: {decorated func}.schedule(args=None, kwargs=None, eta=None, delay=None, convert_utc=True)

            Use the special ``schedule`` function to schedule the execution of a
            queue task for a given time in the future:

            .. code-block:: python

                import datetime

                # get a datetime object representing one hour in the future
                in_an_hour = datetime.datetime.now() + datetime.timedelta(seconds=3600)

                # schedule "count_some_beans" to run in an hour
                count_some_beans.schedule(args=(100000,), eta=in_an_hour)

                # another way of doing the same thing...
                count_some_beans.schedule(args=(100000,), delay=(60 * 60))

            :param args: arguments to call the decorated function with
            :param kwargs: keyword arguments to call the decorated function with
            :param datetime eta: the time at which the function should be executed
            :param int delay: number of seconds to wait before executing function
            :param convert_utc: whether the ``eta`` should be converted from local
                                time to UTC, defaults to ``True``
            :rtype: like calls to the decorated function, will return an :py:class:`AsyncData`
                    object if a result store is configured, otherwise returns ``None``

        .. py:function:: {decorated func}.call_local

            Call the ``@task``-decorated function without enqueueing the call. Or, in other words, ``call_local()`` provides access to the actual function.

            .. code-block:: pycon

                >>> count_some_beans.call_local(1337)
                'Counted 1337 beans'

        .. py:attribute:: {decorated func}.task_class

            Store a reference to the task class for the decorated function.

            .. code-block:: pycon

                >>> count_some_beans.task_class
                tasks.queuecmd_count_beans


    .. py:method:: periodic_task(validate_datetime)

        Function decorator that marks the decorated function for processing by the
        consumer *at a specific interval*.  Calls to functions decorated with ``periodic_task``
        will execute normally, unlike :py:meth:`~Huey.task`, which enqueues tasks
        for execution by the consumer.  Rather, the ``periodic_task`` decorator
        serves to **mark a function as needing to be executed periodically** by the
        consumer.

        .. note::
            By default, the consumer will execute ``periodic_task`` functions. To
            disable this, run the consumer with ``-n`` or ``--no-periodic``.

        The ``validate_datetime`` parameter is a function which accepts a datetime
        object and returns a boolean value whether or not the decorated function
        should execute at that time or not.  The consumer will send a datetime to
        the function every minute, giving it the same granularity as the linux
        crontab, which it was designed to mimic.

        For simplicity, there is a special function :py:func:`crontab`, which can
        be used to quickly specify intervals at which a function should execute.  It
        is described below.

        Here is an example of how you might use the ``periodic_task`` decorator
        and the ``crontab`` helper:

        .. code-block:: python

            from huey import crontab
            from huey import RedisHuey

            huey = RedisHuey()

            @huey.periodic_task(crontab(minute='*/5'))
            def every_five_minutes():
                # this function gets executed every 5 minutes by the consumer
                print "It's been five minutes"

        .. note::
            Because functions decorated with ``periodic_task`` are meant to be
            executed at intervals in isolation, they should not take any required
            parameters nor should they be expected to return a meaningful value.
            This is the same regardless of whether or not you are using a result store.

        :param validate_datetime: a callable which takes a ``datetime`` and returns
            a boolean whether the decorated function should execute at that time or not
        :rtype: decorated function

        Like :py:meth:`~Huey.task`, the periodic task decorator adds several helpers
        to the decorated function.  These helpers allow you to "revoke" and "restore" the
        periodic task, effectively enabling you to pause it or prevent its execution.

        .. py:function:: {decorated_func}.revoke([revoke_until=None[, revoke_once=False]])

            Prevent the given periodic task from executing.  When no parameters are
            provided the function will not execute again.

            This function can be called multiple times, but each call will overwrite
            the limitations of the previous.

            :param datetime revoke_until: Prevent the execution of the task until the
                given datetime.  If ``None`` it will prevent execution indefinitely.
            :param bool revoke_once: If ``True`` will only prevent execution the next
                time it would normally execute.

            .. code-block:: python

                # skip the next execution
                every_five_minutes.revoke(revoke_once=True)

                # pause the command indefinitely
                every_five_minutes.revoke()

                # pause the command for 24 hours
                every_five_minutes.revoke(datetime.datetime.now() + datetime.timedelta(days=1))

        .. py:function:: {decorated_func}.is_revoked([dt=None])

            Check whether the given periodic task is revoked.  If ``dt`` is specified,
            it will check if the task is revoked for the given datetime.

            :param datetime dt: If provided, checks whether task is revoked at the
                given datetime

        .. py:function:: {decorated_func}.restore()

            Clears any revoked status and run the task normally

        If you want access to the underlying task class, it is stored as an attribute
        on the decorated function:

        .. py:attribute:: {decorated_func}.task_class

            Store a reference to the task class for the decorated function.


.. py:function:: crontab(month='*', day='*', day_of_week='*', hour='*', minute='*')

    Convert a "crontab"-style set of parameters into a test function that will
    return ``True`` when a given ``datetime`` matches the parameters set forth in
    the crontab.

    Acceptable inputs:

    - "*" = every distinct value
    - "\*/n" = run every "n" times, i.e. hours='\*/4' == 0, 4, 8, 12, 16, 20
    - "m-n" = run every time m..n
    - "m,n" = run on m and n

    :rtype: a test function that takes a ``datetime`` and returns a boolean

AsyncData
---------

.. py:class:: AsyncData(huey, task)

    Although you will probably never instantiate an ``AsyncData`` object yourself,
    they are returned by any calls to :py:meth:`~Huey.task` decorated functions
    (provided that "huey" is configured with a result store).  The ``AsyncData``
    talks to the result store and is responsible for fetching results from tasks.
    Once the consumer finishes executing a task, the return value is placed in the
    result store, allowing the producer to retrieve it.

    Working with the ``AsyncData`` class is very simple:

    .. code-block:: python

        >>> from main import count_some_beans
        >>> res = count_some_beans(100)
        >>> res  # what is "res" ?
        <huey.queue.AsyncData object at 0xb7471a4c>

        >>> res.get()  # get the result of this task, assuming it executed
        'Counted 100 beans'

    What happens when data isn't available yet?  Let's assume the next call takes
    about a minute to calculate:

    .. code-block:: python

        >>> res = count_some_beans(10000000) # let's pretend this is slow
        >>> res.get()  # data is not ready, so returns None

        >>> res.get() is None  # data still not ready
        True

        >>> res.get(blocking=True, timeout=5)  # block for 5 seconds
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
          File "/home/charles/tmp/huey/src/huey/huey/queue.py", line 46, in get
            raise DataStoreTimeout
        huey.exceptions.DataStoreTimeout

        >>> res.get(blocking=True)  # no timeout, will block until it gets data
        'Counted 10000000 beans'

    .. py:method:: get([blocking=False[, timeout=None[, backoff=1.15[, max_delay=1.0[, revoke_on_timeout=False]]]]])

        Attempt to retrieve the return value of a task.  By default, it will simply
        ask for the value, returning ``None`` if it is not ready yet.  If you want
        to wait for a value, you can specify ``blocking = True`` -- this will loop,
        backing off up to the provided ``max_delay`` until the value is ready or
        until the ``timeout`` is reached.  If the ``timeout`` is reached before the
        result is ready, a :py:class:`DataStoreTimeout` exception will be raised.

        :param blocking: boolean, whether to block while waiting for task result
        :param timeout: number of seconds to block for (used with `blocking=True`)
        :param backoff: amount to backoff delay each time no result is found
        :param max_delay: maximum amount of time to wait between iterations when
            attempting to fetch result.
        :param bool revoke_on_timeout: if a timeout occurs, revoke the task

    .. py:method:: revoke()

        Revoke the given task.  Unless it is in the process of executing, it will
        be revoked and the task will not run.

        .. code-block:: python

            in_an_hour = datetime.datetime.now() + datetime.timedelta(seconds=3600)

            # run this command in an hour
            res = count_some_beans.schedule(args=(100000,), eta=in_an_hour)

            # oh shoot, I changed my mind, do not run it after all
            res.revoke()

    .. py:method:: restore()

        Restore the given task.  Unless it has already been skipped over, it
        will be restored and run as scheduled.


Queues and DataStores
---------------------

Huey communicates with two types of data stores -- queues and datastores.  Thinking
of them as python datatypes, a queue is sort of like a ``list`` and a datastore is
sort of like a ``dict``.  Queues are FIFOs that store tasks -- producers put tasks
in on one end and the consumer reads and executes tasks from the other.  DataStores
are key-based stores that can store arbitrary results of tasks keyed by task id.
DataStores can also be used to serialize task schedules so in the event your consumer
goes down you can bring it back up and not lose any tasks that had been scheduled.

Huey, like just about a zillion other projects, uses a "pluggable backend" approach,
where the interface is defined on a couple classes :py:class:`BaseQueue` and :py:class:`BaseDataStore`,
and you can write an implementation for any datastore you like.  The project ships
with backends that talk to `redis <http://redis.io>`_, a fast key-based datastore,
but the sky's the limit when it comes to what you want to interface with.  Below is
an outline of the methods that must be implemented on each class.

Base classes
^^^^^^^^^^^^

.. py:class:: BaseQueue(name, **connection)

    Queue implementation -- any connections that must be made should be created
    when instantiating this class.

    :param name: A string representation of the name for this queue
    :param connection: Connection parameters for the queue

    .. py:attribute:: blocking = False

        Whether the backend blocks when waiting for new results.  If set to ``False``,
        the backend will be polled at intervals, if ``True`` it will read and wait.

    .. py:method:: write(data)

        Write data to the queue - has no return value.

        :param data: a string

    .. py:method:: read()

        Read data from the queue, returning None if no data is available --
        an empty queue should not raise an Exception!

        :rtype: a string message or ``None`` if no data is present

    .. py:method:: remove(data)

        Remove all instances of given data from queue, returning number removed

        :param string data:
        :rtype: number of instances removed

    .. py:method:: flush()

        Optional: Delete everything in the queue -- used by tests

    .. py:method:: __len__()

        Optional: Return the number of items in the queue -- used by tests

.. py:class:: BaseDataStore(name, **connection)

    Data store implementation -- any connections that must be made should be created
    when instantiating this class.

    :param name: A string representation of the name for this data store
    :param connection: Connection parameters for the data store

    .. py:method:: put(key, value)

        Store the ``value`` using the ``key`` as the identifier

    .. py:method:: peek(key)

        Retrieve the value stored at the given ``key``, returns a special value
        :py:class:`EmptyData` if nothing exists at the given key.

    .. py:method:: get(key)

        Retrieve the value stored at the given ``key``, returns a special value
        :py:class:`EmptyData` if no data exists at the given key.  This is to
        differentiate between "no data" and a stored ``None`` value.

        .. warning:: After a result is fetched it will be removed from the store!

    .. py:method:: flush()

        Remove all keys

.. py:class:: BaseSchedule(name, **connection)

    Schedule tasks, should be able to efficiently find tasks that are ready
    for execution.

    .. py:method:: add(data, timestamp)

        Add the timestamped data (a serialized task) to the task schedule.

    .. py:method:: read(timestamp)

        Return all tasks that are ready for execution at the given timestamp.

    .. py:method:: flush()

        Remove all tasks from the schedule.

.. py:class:: BaseEventEmitter(channel, **connection)

    A send-and-forget event emitter that is used for sending real-time updates
    for tasks in the consumer.

    .. py:method:: emit(data)

        Send the data on the specified channel.


Redis implementation
^^^^^^^^^^^^^^^^^^^^

All the following use the `python redis driver <https://github.com/andymccurdy/redis-py>`_
written by Andy McCurdy.

.. py:class:: RedisQueue(name, **connection)

    Does a simple ``RPOP`` to pull messages from the queue, meaning that it polls.

    :param name: the name of the queue to use
    :param connection: a list of values passed directly into the ``redis.Redis`` class

.. py:class:: RedisBlockingQueue(name, **connection)

    Does a ``BRPOP`` to pull messages from the queue, meaning that it blocks on reads.

    :param name: the name of the queue to use
    :param connection: a list of values passed directly into the ``redis.Redis`` class

.. py:class:: RedisDataStore(name, **connection)

    Stores results in a redis hash using ``HSET``, ``HGET`` and ``HDEL``

    :param name: the name of the data store to use
    :param connection: a list of values passed directly into the ``redis.Redis`` class

.. py:class:: RedisSchedule(name, **connection)

    Uses sorted sets to efficiently manage a schedule of timestamped tasks.

    :param name: the name of the data store to use
    :param connection: a list of values passed directly into the ``redis.Redis`` class

 .. py:class:: RedisEventEmitter(channel, **connection)

    Uses Redis pubsub to emit json-serialized updates about tasks in real-time.

    :param channel: the channel to send messages on.
    :param connection: values passed directly to the ``redis.Redis`` class.

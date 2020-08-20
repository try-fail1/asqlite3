import threading
from collections import deque
import sqlite3
from collections.abc import Coroutine
from functools import update_wrapper
from asyncio import AbstractEventLoop


class ResolveFutures(threading.Thread):
    """An internal class that is used to
    resolve the futures passed through a
    queue"""

    internal_queue = deque(maxlen=20)

    def __init__(self, loop):
        super().__init__(daemon=True)
        self.loop = loop

    def run(self):
        while True:
            try:
                future, function, args, kwargs = self.internal_queue.pop()
            except IndexError:
                continue

            try:
                self.loop.call_soon_threadsafe(
                    future.set_result, function(*args, **kwargs))
            except Exception as e:
                self.loop.call_soon_threadsafe(future.set_exception, e)


async def run_through_thread(function, *args, **kwargs):
    loop = kwargs.pop('loop')
    future = loop.create_future()
    ResolveFutures.internal_queue.append((future, function, args, kwargs))
    return await future


class AddFunctionality(Coroutine):
    __slots__ = ('coro', 'done')

    def __init__(self, coro):
        self.coro = coro
        self.done = None

    async def __aenter__(self):
        self.done = await self.coro
        return self.done

    async def __aexit__(self, *exc):
        await self.done.close()
        self.done = None

    def __await__(self):
        return self.coro.__await__()

    def send(self, val):
        self.coro.send(val)

    def throw(self, typ, val=None, tb=None):
        super().throw(typ, val, tb)

    def close(self):
        super().close()


def make_ctx(meth):
    def within(self, *args, **kwargs):
        return AddFunctionality(meth(self, *args, **kwargs))
    return within


def make_async_method(method, kls):

    async def inner(self, *args, **kwargs):
        actual_method = getattr(self._internal, method)
        loop = self._loop

        if method == 'backup':
            if 'target' in kwargs:
                if not isinstance(kwargs['target'], sqlite3.Connection):
                    try:
                        kwargs['target'] = kwargs['target']._internal
                    except AttributeError:
                        raise TypeError(
                            "'target' must be an instance of" +
                            "sqlite3.Connection or asqlite3.Connection")
            else:
                if not isinstance(args[0], sqlite3.Connection):
                    try:
                        args = (args[0]._internal,)
                    except AttributeError:
                        raise TypeError(
                            "'target' must be an instance of" +
                            "sqlite3.Connection or asqlite3.Connection")

        ret = await run_through_thread(
            actual_method, *args, loop=loop, **kwargs)

        if isinstance(ret, sqlite3.Cursor):
            if type(self) == Cursor:
                return self
            return Cursor(self._internal, self, loop)
        return ret

    if method in ('cursor', 'executemany' 'executescript', 'execute'):
        # These methods return a cursor instance
        inner = make_ctx(inner)
    # Preserve function metadata
    if kls.__name__ == 'Cursor':
        update_wrapper(inner, sqlite3.Cursor.__dict__[method])
    elif kls.__name__ == 'Connection':
        update_wrapper(inner, sqlite3.Connection.__dict__[method])
    return inner


def decorate_conn_or_cur(connection_attrs):
    def affect_class(cls):
        for i in connection_attrs:
            setattr(cls, i, make_async_method(i, cls))
        return cls
    return affect_class


class Descriptor:
    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        setattr(instance._internal, self.name, value)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance._internal, self.name)

    def __delete__(self, instance):
        delattr(instance._internal, self.name)


@decorate_conn_or_cur(
    ['execute', 'executemany',
        'executescript', 'fetchone',
        'fetchmany', 'fetchall',
        'close']
)
class Cursor:
    rowcount = Descriptor()
    lastrowid = Descriptor()
    arraysize = Descriptor()
    description = Descriptor()
    connection = Descriptor()

    def __init__(
            self, connection: sqlite3.Connection,
            async_connection: "Connection", # noqa:
            loop: AbstractEventLoop):
        self._internal = sqlite3.Cursor(connection)
        self._async_connection = async_connection
        self._loop = loop

    @property
    def async_connection(self):
        """The asynchronous connection"""
        return self._async_connection

    @property
    def loop(self):
        """The asyncio event loop passed into the Cursor"""
        return self._loop

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, tb):
        await self.close()

    async def __aiter__(self):
        return self

    async def __anext__(self):
        f = await self.fetchone()
        if not f:
            raise StopAsyncIteration
        return f

    def __repr__(self):
        return (f"<Cursor: rowcount={self.rowcount}" +
                f"lastrowid={self.lastrowid} arraysize={self.arraysize}>")

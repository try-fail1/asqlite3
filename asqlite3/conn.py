import sqlite3
from os import PathLike
from typing import Union, Optional
import asyncio

from .usefuls import decorate_conn_or_cur, Descriptor, ResolveFutures


@decorate_conn_or_cur(
    ['commit', 'rollback', 'close', 'create_collation',
        'execute', 'executemany', 'executescript',
        'create_function', 'create_aggregate', 'interrupt',
        'set_authorizer', 'set_progress_handler',
        'set_trace_callback', 'enable_load_extension',
        'load_extension', 'backup', 'cursor']
)
class Connection:
    """An asynchronous-compatible class that
    is meant to be similar to :class:`sqlite3.Connection`.

    It should not be directly instantiated, as it's returned
    by the ``asqlite3.connect`` function."""

    isolation_level = Descriptor()
    in_transaction = Descriptor()
    row_factory = Descriptor()
    text_factory = Descriptor()
    total_changes = Descriptor()

    def __init__(self, actual_conn, loop):
        self._internal = actual_conn
        self._loop = loop

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    async def __aenter__(self) -> "Connection":
        return self

    async def iterdump(self):
        for i in self._internal.iterdump():
            yield i

    async def __aexit__(self, exc_type, exc_value, tb) -> None:
        await self.close()

    def __repr__(self) -> str:
        return ' '.join([
            f"<Connection: isolation_level='{self.isolation_level}'",
            f"total_changes={self.total_changes}",
            f"in_transaction={self.in_transaction}>"
            ])


def connect(

    database: Union[str, PathLike, bytes],
    timeout: Optional[int] = 5.0,
    detect_types: Optional[int] = 0,
    isolation_level: Optional[str] = 'DEFERRED',
    check_same_thread: Optional[bool] = False,
    factory: Optional[sqlite3.Connection] = sqlite3.Connection,
    cached_statements: Optional[int] = 100,
    uri: Optional[bool] = False,
    *,
    loop: Optional[asyncio.AbstractEventLoop] = None
) -> Connection:

    """Used to connect to the database.

    .. note::

        You should rarely call this function because it spawns
        a new thread. It is best practice to set a connection
        variable in the global scope and use it throughout your
        script."""

    if check_same_thread:
        raise RuntimeError("'check_same_thread' must be False")
    if loop is None:
        loop = asyncio.get_event_loop()

    sq = sqlite3.connect(
        database, timeout, detect_types,
        isolation_level, check_same_thread,
        factory, cached_statements, uri
    )
    t = ResolveFutures(loop=loop)
    t.start()
    return Connection(sq, loop)

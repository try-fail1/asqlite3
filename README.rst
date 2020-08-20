asqlite3
============

Purpose
-----------

An asynchronous way to connect to an `sqlite3 <https://docs.python.org/3/library/sqlite3.html>`_
database. Normally, this would block the
`asyncio <https://docs.python.org/3/library/asyncio.html>`_ event loop and slow down the execution
speed of the script. This is because asyncio
isn't meant for I/O bound tasks. `threading <https://docs.python.org/3/library/threading.html>`_ is
more efficient for that, which is exactly why this
module uses it under the hood.

Features
----------

* A similar syntax to the ``sqlite3`` module in the Standard library
* Has ``asyncio`` idioms such as ``async for``, ``await``, and ``async with``
* Provides all features of the built-in ``sqlite3`` module

Installation
-----------------

Installing ``asqlite3`` should be done through `PIP <https://pypi.org/project/pip/>`_:

.. code:: sh

    $ pip install asqlite3

Contributing
--------------

Contributions are always encouraged and open.

Examples
-----------

.. code-block:: python

    import asyncio

    import asqlite3

    conn = asqlite3.connect(':memory:')

    async def connection():
        async with conn:
            await conn.execute("CREATE TABLE table (plate INT)")
            await conn.execute("INSERT INTO table VALUES (5)")
        # connection is automatically closed
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connection())

.. code-block:: python

    import asyncio

    import asqlite3

    conn = asqlite3.connect(':memory:')

    async def cursor():
        cur = await conn.cursor()
        rows = [i async for i in cur]
        return rows
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cursor())

License
----------

``asqlite`` is currently under the MIT license.
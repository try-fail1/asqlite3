import setuptools
import re


def get_version():
    with open('asqlite3/__init__.py') as f:
        version = re.search(
            r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(),
            re.M).group(1)
    return version


def get_readme():
    with open('README.rst') as f:
        return f.read()


setuptools.setup(
    name='asqlite3',
    version=get_version(),
    long_description=get_readme(),
    description='An async sqlite3 module',
    author='Ryan Vink',
    author_email='ryantvink@gmail.com',
    license='MIT',
    keywords=['sql', 'sqlite3', 'asyncio'],
    url='https://github.com/try-fail1/asqlite3',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries",
    ]
)

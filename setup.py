import os
from setuptools import setup, find_packages


setup(
    name='huey',
    version=__import__('huey').__version__,
    description='huey, a little task queue',
    author='Charles Leifer',
    author_email='coleifer@gmail.com',
    url='http://github.com/coleifer/huey/',
    packages=find_packages(),
    package_data = {
        'huey': [
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    test_suite='runtests.runtests',
    scripts = ['huey/bin/huey_consumer.py'],
)

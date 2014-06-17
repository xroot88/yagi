import os
from pip.req import parse_requirements
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
install_reqs = [str(r.req) for r in parse_requirements(req_file)]


setup(
    name='yagi',
    version='0.13',
    author='Matthew Dietz, Monsyne Dragon',
    author_email='matthew.dietz@gmail.com, mdragon@rackspace.com',
    description=("A PubSubHubBub Publisher and ATOM feed generator that "
                   "can consume events from multiple input sources and "
                   "publish them to standard PSHB hubs"),
    license='Apache License (2.0)',
    keywords='PubSubHubBub notifications events ATOM RSS',
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6'
    ],
    url='https://github.com/Cerberus98/yagi',
    scripts=['bin/yagi-feed', 'bin/yagi-event'],
    long_description=read('README.md'),
    install_requires=install_reqs,
    zip_safe=False
)

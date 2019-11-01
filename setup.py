"""Packaging settings."""


from codecs import open
from os.path import dirname, join
from subprocess import call
from setuptools import Command, find_packages, setup
from plugnpy import __version__ as VERSION


def read(fname):
    return open(join(dirname(__file__), fname), encoding='utf-8').read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call([
            'py.test',
            '--verbose',
            '--cov=plugnpy',
            '--cov-report=term-missing',
            '--cov-config=.coveragerc',
            '--junitxml=.junit.xml',
        ])
        raise SystemExit(errno)


setup(
    name='plugnpy',
    version=VERSION,
    description='A Simple Python Library for creating Opsview Opspack plugins',
    long_description=read('README.md'),
    url='https://github.com/opsview/plugnpy',
    author='Opsview Ltd',
    author_email='support@opsview.com',
    license='Apache-2.0',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Libraries',
        'License :: Apache-2.0',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='plugnpy',
    packages=['plugnpy'],
    data_files=[
        ('info', ['VERSION', 'LICENSE', 'README.md'])
    ],
    install_requires=[
        'geventhttpclient',
    ],
    extras_require={
        'test': [
            'coverage',
            'pytest',
            'pytest-benchmark',
            'pytest-cov',
            'pytest-mock',
            'pycodestyle',
            'pylint',
            'pyflakes',
        ],
    },
    cmdclass={'test': RunTests},
)

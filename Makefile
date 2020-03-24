# MAKEFILE
#
# @link        https://github.com/opsview/plugnpy
#
# This makefile is based on https://github.com/tecnickcom/pygen by Nicola Asuni (MIT license)
# ------------------------------------------------------------------------------

# List special make targets that are not associated with files
.PHONY: help venv version wheel test lint doc format clean

# Use bash as shell (Note: Ubuntu now uses dash which doesn't support PIPESTATUS).
SHELL=/bin/bash

# CVS path (path to the parent dir containing the project)
CVSPATH=github.com/opsview/plugnpy

# Project owner
OWNER=Opsview Ltd

# Project vendor
VENDOR=opsview

# Project name
PROJECT=plugnpy

# Project version
VERSION=$(shell cat VERSION)

# Name of RPM or DEB package
PKGNAME=${VENDOR}-${PROJECT}

# Current directory
CURRENTDIR=$(dir $(realpath $(firstword $(MAKEFILE_LIST))))

# Path to python3
PYTHON3_BIN=/opt/opsview/python3/bin/python3

# --- MAKE TARGETS ---

# Display general help about this command
help:
	@echo ""
	@echo "$(PROJECT) Makefile."
	@echo "The following commands are available:"
	@echo ""
	@echo "    make venv       : Set up development virtual environment"
	@echo "    make version    : Set version from VERSION file"
	@echo "    make build      : Build a Wheel package"
	@echo "    make verify     : Run tests and linting"
	@echo "    make test       : Execute tests in py27 and py37 envs"
	@echo "    make lint       : Evaluate code"
	@echo "    make doc        : Start a server to display source code documentation"
	@echo "    make format     : Format the source code"
	@echo "    make clean      : Remove any build artifact"
	@echo ""

all: help

# Build dev env
venv: venv/bin/activate

venv/bin/activate: requirements.txt setup.py
	test -d .venv || virtualenv .venv
	source .venv/bin/activate ; \
	pip install -r requirements.txt ; \
	pip install -e '.[test]' ; \
	pip install -e '.[examples]'

# Build dev env for python3
venv3: venv3/bin/activate

venv3/bin/activate: requirements.txt setup.py
	test -d .venv3 || ${PYTHON3_BIN} -m venv .venv3
	source .venv3/bin/activate ; \
	pip install -r requirements.txt ; \
	pip install -e '.[test]' ; \
	pip install -e '.[examples]'

# Set the version from VERSION file
version:
	sed -i "s/__version__.*$$/__version__ = '$(VERSION)'/" plugnpy/__init__.py

# Build a Wheel package
build: clean version venv
	cp LICENSE README.md plugnpy; \
	source .venv/bin/activate ; \
	python setup.py sdist bdist_wheel; \
	rm plugnpy/LICENSE plugnpy/README.md

# Run tests and linting
verify: test lint

# Test using tox
test: venv
	source .venv/bin/activate ; \
	python -m tox ; \
	coverage html

# Run tests only on python2
tox2: venv
	source .venv/bin/activate ; \
	python -m tox -e py27

# Run tests only on python3
tox3: venv3
	source .venv3/bin/activate ; \
	python -m tox -e py37

# Evaluate code
lint: venv
	source .venv/bin/activate ; \
	pyflakes ${PROJECT} ; \
	pylint ${PROJECT} ; \
	pycodestyle --max-line-length=120 ${PROJECT}

# Generate source code documentation
doc:
	pydoc -p 1234 $(PROJECT)

# Format the source code
format:
	find . -path ./target -prune -o -type f -name '*.py' -exec autopep8 --in-place --max-line-length=240 {} \;

# Remove any build artifact
clean:
	rm -rf .venv .venv3 .tox target htmlcov build dist .cache .benchmarks ./test/*.so ./test/__pycache__ ./plugnpy/__pycache__ ./plugnpy.egg-info .pytest_cache .coverage .junit.xml
	find . -type f -name '*.pyc' -exec rm -f {} \;

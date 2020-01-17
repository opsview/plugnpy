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

# --- MAKE TARGETS ---

# Display general help about this command
help:
	@echo ""
	@echo "$(PROJECT) Makefile."
	@echo "The following commands are available:"
	@echo ""
	@echo "    make venv       : Set up development virtual environment"
	@echo "    make version    : Set version from VERSION file"
	@echo "    make wheel      : Build a Wheel package"
	@echo "    make test       : Execute test command"
	@echo "    make lint       : Evaluate code"
	@echo "    make doc        : Start a server to display source code documentation"
	@echo "    make format     : Format the source code"
	@echo "    make clean      : Remove any build artifact"
	@echo ""

all: help

# Build dev env
venv: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	source venv/bin/activate ; \
	pip install -r requirements.txt ; \
	pip install -e '.[test]'

# Set the version from VERSION file
version:
	sed -i "s/__version__.*$$/__version__ = '$(VERSION)'/" plugnpy/__init__.py

# Build a Wheel package
wheel: clean version venv
	cp LICENSE README.md plugnpy; \
	source venv/bin/activate ; \
	python setup.py sdist bdist_wheel; \
	rm plugnpy/LICENSE plugnpy/README.md

# Test using setuptools
test: venv
	source venv/bin/activate ; \
	python setup.py test ; \
	coverage html

# Evaluate code
lint: venv
	source venv/bin/activate ; \
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
	rm -rf venv target htmlcov build dist .cache .benchmarks ./test/*.so ./test/__pycache__ ./plugnpy/__pycache__ ./plugnpy.egg-info .pytest_cache .coverage .junit.xml
	find . -type f -name '*.pyc' -exec rm -f {} \;

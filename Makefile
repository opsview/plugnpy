# MAKEFILE
#
# @link        https://github.com/opsview/plugnpy
#
# This makefile is based on https://github.com/tecnickcom/pygen by Nicola Asuni (MIT license)
# ------------------------------------------------------------------------------

# List special make targets that are not associated with files
.PHONY: help version conda conda_dev build wheel vtest test lint doc format clean

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

# Project release number (packaging build number)
RELEASE=$(shell cat RELEASE)

# Name of RPM or DEB package
PKGNAME=${VENDOR}-${PROJECT}

# Current directory
CURRENTDIR=$(dir $(realpath $(firstword $(MAKEFILE_LIST))))

# Conda environment
CONDA_ENV=$(shell dirname ${CURRENTDIR})/env-${PROJECT}

# Include default build configuration
include $(CURRENTDIR)/config.mk

# extract all packages
ALLPACKAGES=$(shell cat conda/meta.yaml | grep -oP '^\s*-\s\K(.*)' | sed "s/.*${PROJECT}//" | sed '/^\s*$$/d' | sort -u | tr -d ' ' | sed 's/[^ ][^ ]*/"&"/g' | tr '\r\n' ' ')


# --- MAKE TARGETS ---

# Display general help about this command
help:
	@echo ""
	@echo "$(PROJECT) Makefile."
	@echo "The following commands are available:"
	@echo ""
	@echo "    make version    : Set version from VERSION file"
	@echo "    make conda      : Build minimal Conda environment"
	@echo "    make conda_dev  : Build development Conda environment"
	@echo "    make build      : Build a Conda package"
	@echo "    make wheel      : Build a Wheel package"
	@echo "    make vtest      : Execute tests inside a Python 2.7 virtualenv"
	@echo "    make test       : Execute test command"
	@echo "    make lint       : Evaluate code"
	@echo "    make doc        : Start a server to display source code documentation"
	@echo "    make format     : Format the source code"
	@echo "    make clean      : Remove any build artifact"
	@echo ""

all: help

# Set the version from VERSION file
version:
	sed -i "s/version:.*$$/version: $(VERSION)/" conda/meta.yaml
	sed -i "s/number:.*$$/number: $(RELEASE)/" conda/meta.yaml
	sed -i "s/__version__.*$$/__version__ = '$(VERSION)'/" plugnpy/__init__.py
	sed -i "s/__release__.*$$/__release__ = '$(RELEASE)'/" plugnpy/__init__.py

# Build minimal Conda environment
conda:
	./conda/setup-conda.sh

# Build development Conda environment
conda_dev:
	ENV_NAME=env-dev-plugnpy ./conda/setup-conda.sh
	. ../env-dev-plugnpy/bin/activate && \
	../env-dev-plugnpy/bin/conda install --override-channels $(CONDA_CHANNELS) -y $(ALLPACKAGES)

# Build a conda package
build: clean version conda
	mkdir -p target
	PROJECT_ROOT=${CURRENTDIR} "${CONDA_ENV}/bin/conda" build --prefix-length 128 --no-anaconda-upload --override-channels $(CONDA_CHANNELS) conda

# Build a Wheel package
wheel: clean version
	python setup.py sdist bdist_wheel

# Test th eproject in a Python 2.7 virtual environment
vtest:
	rm -rf venv
	virtualenv -p /usr/bin/python2.7 venv
	source venv/bin/activate && pip install -e .[test] && make test

# Test using setuptools
test:
	python setup.py test

# Evaluate code
lint:
	pylint --max-line-length=240 ${PROJECT}

# Generate source code documentation
doc:
	pydoc -p 1234 $(PROJECT)

# Format the source code
format:
	find . -path ./target -prune -o -type f -name '*.py' -exec autopep8 --in-place --max-line-length=240 {} \;

# Remove any build artifact
clean:
	rm -rf target htmlcov build dist .cache .benchmarks ./tests/*.so ./tests/__pycache__ ./plugnpy/__pycache__ ./plugnpy.egg-info
	find . -type f -name '*.pyc' -exec rm -f {} \;

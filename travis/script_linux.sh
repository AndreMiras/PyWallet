#!/bin/bash
# Linux specific Travis script

# exits on fail
set -e

# creates & uses the virtualenv
virtualenv --python=python2.7 --no-site-packages venv
source venv/bin/activate

# installs requirements
pip install --install-option="--no-cython-compile" $(grep Cython requirements/requirements.txt)
# pip install -r requirements/test_requirements.txt
# pip install -r requirements.txt

# runs tests
# isort --check-only --recursive src/
# flake8 src/
# python -m unittest discover --start-directory=src/
deactivate

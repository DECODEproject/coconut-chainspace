#!/usr/bin/env bash

source ../.chainspace.env/bin/activate && python -m pytest -vs --disable-pytest-warnings tests/test_petition.py

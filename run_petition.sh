#!/usr/bin/env bash

echo "Going to run a python script that executes the petition end to end"

source ../.chainspace.env/bin/activate && python ./run_petition.py

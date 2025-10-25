#!/bin/bash
# Helper script to run agents with correct PYTHONPATH

export PYTHONPATH="$(pwd):${PYTHONPATH}"
python "$@"

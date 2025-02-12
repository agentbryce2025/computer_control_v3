#!/bin/bash
export DISPLAY=:1
cd "$(dirname "$0")"
export PYTHONPATH=$PYTHONPATH:$(pwd)
./computer_use_demo/terminal.py "$@"
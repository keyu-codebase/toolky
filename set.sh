#!/usr/bin/env bash

rm -rf build dist toolky.egg-info
python3 setup.py sdist bdist_wheel

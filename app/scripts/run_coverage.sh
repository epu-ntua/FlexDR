#!/bin/bash
echo "Running tests"
coverage run -m pytest
echo "Creating report"
coverage report -m
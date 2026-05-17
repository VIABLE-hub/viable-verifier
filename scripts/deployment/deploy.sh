#!/bin/bash

# VIABLE Credentials Deployment Wrapper Script
# This script calls the actual deployment script located in deploy/scripts/

# Change to deploy/scripts directory and run the main deploy script
cd deploy/scripts
exec ./deploy.sh "$@" 
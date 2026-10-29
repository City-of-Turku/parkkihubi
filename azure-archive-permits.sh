#!/bin/bash

# Helper script for Azure WebJobs. Archives permits that ended over 185 days ago.
cd /parkkihub
./manage.py archive_permits --keep-days 185 -v 2

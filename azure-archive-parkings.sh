#!/bin/bash

# Helper script for Azure WebJobs. Archives parkings older than 185 days.
cd /parkkihub
./manage.py archive_parkings --keep-days 185 -v 2
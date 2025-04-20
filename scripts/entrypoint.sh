#!/bin/bash
echo "Executing as non-root user: $(whoami)"
# Execute root script securely
sudo /app/venv/bin/python /app/chrony_exporter.py
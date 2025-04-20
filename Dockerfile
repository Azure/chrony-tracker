# Use Ubuntu as the base image with version latest
FROM ubuntu:latest

# Set environment variables to prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && \
apt-get install -y \
chrony \
procps \
bash \
sudo \
python3 \
python3-pip \
python3-venv \
&& apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a directory for the application
WORKDIR /app

# Copy the logging script to the image
COPY scripts/chrony_exporter.py /app/chrony_exporter.py
COPY config/chrony.conf /etc/chrony/chrony.conf
COPY scripts/requirements.txt requirements.txt

#Create a virtual environment and install Python dependencies
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install -r /app/requirements.txt

# Copy the root-execution script
COPY scripts/entrypoint.sh /app/entrypoint.sh

# Create a non-root user with a specific UID (1001) and GID (1001)
RUN groupadd -g 1001 appgroup && \
    useradd -m -u 1001 -g 1001 appuser

# Allow non-root user to run only `/app/run_as_root.sh` as root
RUN echo "appuser ALL=(ALL) NOPASSWD: /app/venv/bin/python /app/chrony_exporter.py" >> /etc/sudoers

# Secure the root-execution script
RUN chmod 700 /app/chrony_exporter.py && chown root:root /app/chrony_exporter.py

# Secure the entrypoint script (executed as appuser)
RUN chmod 755 /app/entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 9100

# Set the default entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Start chronyd in read-only mode and then run the logging script
CMD ["/bin/bash", "-c", "chronyd -r && /app/entrypoint.sh"]
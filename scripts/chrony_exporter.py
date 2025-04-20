#!/usr/bin/env python3
import subprocess
import time
import re
import os
from prometheus_client import start_http_server, Gauge


# Prometheus metric for clock error
clock_error_gauge = Gauge('chrony_clock_error_ms', 'Clock error in milliseconds')

# Get the sleep interval from an environment variable, default to 60 seconds
SLEEP_INTERVAL = int(os.environ.get('SLEEP_INTERVAL', 60))


def parse_tracking_output():
    """Parses `chronyc tracking` and calculates clock error."""
    try:
        result = subprocess.run(['chronyc', 'tracking'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        output = result.stdout.decode('utf-8')

        last_offset = root_dispersion = root_delay = None

        for line in output.splitlines():
            if line.startswith('Last offset'):
                match = re.search(r'([-+]?[0-9]*\.?[0-9]+)', line)
                if match:
                    last_offset = abs(float(match.group(1)))
            elif line.startswith('Root dispersion'):
                match = re.search(r'([-+]?[0-9]*\.?[0-9]+)', line)
                if match:
                    root_dispersion = float(match.group(1))
            elif line.startswith('Root delay'):
                match = re.search(r'([-+]?[0-9]*\.?[0-9]+)', line)
                if match:
                    root_delay = float(match.group(1))

        if None not in (last_offset, root_dispersion, root_delay):
            clock_error_sec = last_offset + root_dispersion + (0.5 * root_delay)
            return clock_error_sec * 1000  # convert to ms
    except subprocess.CalledProcessError as e:
        print(f"chronyc error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None

def main():
    start_http_server(9100)
    print("Exporter running at http://localhost:9100/metrics")

    while True:
        clock_error_ms = parse_tracking_output()
        if clock_error_ms is not None:
            clock_error_gauge.set(clock_error_ms)
            print(f"Updated clock error: {clock_error_ms:.3f} ms")
        else:
            print("Clock error computation failed.")
        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    main()

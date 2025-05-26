import requests
import ssl
import socket
import json
from datetime import datetime
from urllib.parse import urlparse

# Your sites to check
sites = [
    "https://gxqit.co.za",
    "https://goodx.co.za",
    "https://goodxhealthcare.ca",
    "https://goodx.co.nz",
    "https://goodxnamibia.com",
    "https://goodx.co.bw",
    "https://goodx.co.uk",
    "https://goodx.us",
    "https://goodx.international",
    "https://goodxeye.com",
    "https://goodx.cloud",
    "https://aditiv.co.za",
    "https://www.imprimatur.co.za",
]

def check_ssl_expiry(hostname):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (expiry_date - datetime.utcnow()).days
                return days_left
    except Exception as e:
        return None

def check_site(url):
    status = "offline"
    ssl_status = "unknown"
    ssl_days_left = None
    response_time = None # Initialize response_time

    try:
        response = requests.get(url, timeout=10)
        response_time = round(response.elapsed.total_seconds(), 2) # Capture response time in seconds, rounded to 2 decimal places
        if response.status_code == 200:
            status = "online"
        else:
            status = f"error {response.status_code}"
    except Exception:
        status = "offline"
        response_time = None # Set to None if request fails

    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        if not hostname or ':' in hostname:
            raise ValueError(f"Could not extract a valid hostname from {url}")

        days_left = check_ssl_expiry(hostname)
        if days_left is None:
            ssl_status = "unknown"
        elif days_left < 0:
            ssl_status = "expired"
        else:
            ssl_status = "valid"
            ssl_days_left = days_left
    except Exception:
        ssl_status = "unknown"

    return {
        "url": url,
        "status": status,
        "ssl_status": ssl_status,
        "ssl_days_left": ssl_days_left,
        "response_time": response_time # Add response_time to the returned dict
    }

def main():
    results = []
    for site in sites:
        results.append(check_site(site))

    output = {
        "last_checked": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "sites": results
    }

    with open("status.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()

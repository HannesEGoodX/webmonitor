import requests
import ssl
import socket
import json
from datetime import datetime
from urllib.parse import urlparse
import logging

# Configure logging to output to console (which GitHub Actions captures)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Set a shorter timeout for SSL connection to avoid long hangs
        with socket.create_connection((hostname, 443), timeout=3) as sock: # SSL handshake timeout remains 3s
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (expiry_date - datetime.utcnow()).days
                return days_left
    except Exception as e:
        logging.warning(f"SSL check failed for {hostname}: {e}")
        return None

def check_site(url):
    status = "offline"
    ssl_status = "unknown"
    ssl_days_left = None
    response_time = None

    try:
        # Increased timeout for requests.get to 15 seconds
        response = requests.get(url, timeout=15, verify=True)
        response_time = round(response.elapsed.total_seconds(), 2)

        if response.status_code == 200:
            status = "online"
            logging.info(f"{url} is online (200 OK), response time: {response_time}s")
        else:
            status = f"error {response.status_code}"
            logging.warning(f"{url} responded with status code {response.status_code}")

    except requests.exceptions.Timeout:
        status = "offline (timeout)"
        logging.error(f"{url} timed out after 15 seconds.")
        response_time = None
    except requests.exceptions.ConnectionError as e:
        status = "offline (connection error)"
        logging.error(f"{url} connection error: {e}")
        response_time = None
    except requests.exceptions.RequestException as e:
        status = "offline (request error)"
        logging.error(f"{url} request error: {e}")
        response_time = None
    except Exception as e:
        status = "offline (unexpected error)"
        logging.error(f"{url} unexpected error: {e}")
        response_time = None

    # SSL check part
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        if not hostname or ':' in hostname:
            raise ValueError(f"Could not extract a valid hostname from {url}")

        days_left = check_ssl_expiry(hostname)
        if days_left is None:
            ssl_status = "unknown"
            logging.warning(f"SSL check for {hostname} returned unknown status.")
        elif days_left < 0:
            ssl_status = "expired"
            logging.error(f"SSL certificate for {hostname} is expired ({abs(days_left)} days ago).")
        else:
            ssl_status = "valid"
            ssl_days_left = days_left
            logging.info(f"SSL certificate for {hostname} is valid, {days_left} days left.")
    except Exception as e:
        ssl_status = "unknown"
        logging.error(f"Failed to perform SSL check for {url}: {e}")

    return {
        "url": url,
        "status": status,
        "ssl_status": ssl_status,
        "ssl_days_left": ssl_days_left,
        "response_time": response_time
    }

def main():
    logging.info("Starting website monitoring script.")
    results = []
    for site in sites:
        results.append(check_site(site))

    output = {
        "last_checked": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "sites": results
    }

    with open("status.json", "w") as f:
        json.dump(output, f, indent=2)
    logging.info("status.json updated successfully.")

if __name__ == "__main__":
    main()
import requests
import ssl
import socket
import json
from datetime import datetime
from urllib.parse import urlparse
import logging

# Configure logging
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
        with socket.create_connection((hostname, 443), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (expiry_date - datetime.utcnow()).days
                return days_left
    except Exception as e:
        logging.warning(f"SSL check failed for {hostname}: {e}")
        return None

def check_site(url, num_pings=3, timeout=15): # Added num_pings and timeout parameters
    successful_pings = 0
    total_response_time = 0
    final_status = "offline"
    final_response_time = None

    logging.info(f"Checking site: {url} with {num_pings} pings...")

    for i in range(num_pings):
        status_during_ping = "offline"
        response_time_during_ping = None
        try:
            response = requests.get(url, timeout=timeout, verify=True)
            response_time_during_ping = round(response.elapsed.total_seconds(), 2)

            if response.status_code == 200:
                status_during_ping = "online"
                successful_pings += 1
                total_response_time += response_time_during_ping
                logging.info(f"  Ping {i+1} for {url}: Online (200 OK) in {response_time_during_ping}s")
            else:
                status_during_ping = f"error {response.status_code}"
                logging.warning(f"  Ping {i+1} for {url}: Responded with status code {response.status_code}")

        except requests.exceptions.Timeout:
            status_during_ping = "offline (timeout)"
            logging.error(f"  Ping {i+1} for {url}: Timed out after {timeout}s.")
        except requests.exceptions.ConnectionError as e:
            status_during_ping = "offline (connection error)"
            logging.error(f"  Ping {i+1} for {url}: Connection error: {e}")
        except requests.exceptions.RequestException as e:
            status_during_ping = "offline (request error)"
            logging.error(f"  Ping {i+1} for {url}: Request error: {e}")
        except Exception as e:
            status_during_ping = "offline (unexpected error)"
            logging.error(f"  Ping {i+1} for {url}: Unexpected error: {e}")

    if successful_pings == num_pings:
        final_status = "online"
        final_response_time = round(total_response_time / num_pings, 2)
        logging.info(f"{url} is ONLINE (3 consecutive successful pings). Average response time: {final_response_time}s")
    else:
        final_status = f"offline ({successful_pings}/{num_pings} pings successful)"
        logging.warning(f"{url} is OFFLINE ({successful_pings}/{num_pings} pings successful).")
        # If any ping failed, response_time is N/A
        final_response_time = None 


    # SSL check part (remains unchanged)
    ssl_status = "unknown"
    ssl_days_left = None
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
        "status": final_status,
        "ssl_status": ssl_status,
        "ssl_days_left": ssl_days_left,
        "response_time": final_response_time
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
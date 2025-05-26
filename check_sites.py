import requests
import ssl
import socket
import json
from datetime import datetime
from urllib.parse import urlparse
import logging
import time # Import the time module for delays

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Your sites to check
sites = [
    "https://gxqit.co.za",
    "https://goodx.co.za",
    "https://goodxhealthcare.ca",
    "https://goodx.co.nz",
    "https://goodxnamibia.com",
    "https://goodx.co.bw", # This is the site in question
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

def check_site(url, http_timeout=30, max_retries=5, retry_delay=10): # UPDATED PARAMETERS
    final_status = "offline"
    final_response_time = None
    
    logging.info(f"Attempting to check: {url} with {max_retries} retries, {retry_delay}s delay...")

    # Loop for retries (to overcome transient connection issues)
    for attempt in range(max_retries):
        current_attempt_status = "offline"
        current_attempt_response_time = None
        
        logging.info(f"  Retry Attempt {attempt+1}/{max_retries} for {url}")

        try:
            response = requests.get(url, timeout=http_timeout, verify=True)
            current_attempt_response_time = round(response.elapsed.total_seconds(), 2)

            if response.status_code == 200:
                current_attempt_status = "online"
                logging.info(f"  Attempt {attempt+1} for {url}: Online (200 OK) in {current_attempt_response_time}s")
                final_status = "online" # Mark as online if any attempt succeeds
                final_response_time = current_attempt_response_time
                break # Exit retry loop if successful
            else:
                current_attempt_status = f"error {response.status_code}"
                logging.warning(f"  Attempt {attempt+1} for {url}: Responded with status code {response.status_code}.")

        except requests.exceptions.Timeout:
            current_attempt_status = "offline (timeout)"
            logging.error(f"  Attempt {attempt+1} for {url}: Timed out after {http_timeout}s.")
        except requests.exceptions.ConnectionError as e:
            current_attempt_status = "offline (connection error)"
            logging.error(f"  Attempt {attempt+1} for {url}: Connection error: {e}.") # Now explicitly logging the error
        except requests.exceptions.RequestException as e:
            current_attempt_status = "offline (request error)"
            logging.error(f"  Attempt {attempt+1} for {url}: Request error: {e}.") # Now explicitly logging the error
        except Exception as e:
            current_attempt_status = "offline (unexpected error)"
            logging.error(f"  Attempt {attempt+1} for {url}: Unexpected error: {e}.") # Now explicitly logging the error

        # If it's not the last attempt AND we haven't succeeded, wait before retrying
        if current_attempt_status != "online" and attempt < max_retries - 1:
            logging.info(f"  Waiting {retry_delay}s before next retry for {url}...")
            time.sleep(retry_delay)
        elif current_attempt_status != "online" and attempt == max_retries - 1:
            # If all retries failed, the final status is the last attempt's status
            final_status = current_attempt_status
            final_response_time = current_attempt_response_time


    # Now, apply the 3-consecutive-successful-pings logic *after* overcoming initial connection issues.
    # We'll run this check *only if* the initial retry loop determined the site was reachable at least once.
    if final_status == "online":
        logging.info(f"{url} was initially reachable. Now performing 3-consecutive-ping test...")
        successful_pings_for_consecutive_check = 0
        total_time_for_consecutive = 0

        for i in range(3): # Hardcoding 3 pings for this specific logic
            try:
                # Use the same timeout as the initial check for consistency
                response = requests.get(url, timeout=http_timeout, verify=True) 
                if response.status_code == 200:
                    successful_pings_for_consecutive_check += 1
                    total_time_for_consecutive += response.elapsed.total_seconds()
                    logging.info(f"  Consecutive Ping {i+1} for {url}: Online (200 OK)")
                else:
                    logging.warning(f"  Consecutive Ping {i+1} for {url}: Status code {response.status_code}. Breaking consecutive test.")
                    successful_pings_for_consecutive_check = 0 # Reset count
                    break # Break out of the consecutive loop
            except requests.exceptions.RequestException as e:
                logging.error(f"  Consecutive Ping {i+1} for {url}: Failed ({e}). Breaking consecutive test.")
                successful_pings_for_consecutive_check = 0 # Reset count
                break # Break out of the consecutive loop
            
            if i < 2: # Only sleep if there are more pings to do
                time.sleep(1) # Small delay between consecutive pings

        if successful_pings_for_consecutive_check == 3:
            final_status = "online"
            final_response_time = round(total_time_for_consecutive / 3, 2)
            logging.info(f"{url} is CONFIRMED ONLINE (3 consecutive successful pings). Average response time: {final_response_time}s")
        else:
            final_status = "offline (failed 3-consecutive-ping test)"
            final_response_time = None
            logging.warning(f"{url} is OFFLINE (failed 3-consecutive-ping test).")
    else:
        logging.warning(f"{url} is OFFLINE (initial reachability check failed after all retries).")


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
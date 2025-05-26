import requests
import socket
import ssl
from datetime import datetime

# URLs and hostnames to monitor
sites = [
    {"url": "https://gxqit.co.za", "host": "gxqit.co.za"},
    {"url": "https://goodx.co.za", "host": "goodx.co.za"},
    {"url": "https://goodx.healthcare", "host": "goodx.healthcare"},
]

def check_website(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"[HTTP] {url} is UP (status code 200).")
            return True
        else:
            print(f"[HTTP] {url} returned status code {response.status_code}.")
            return False
    except requests.RequestException as e:
        print(f"[HTTP ERROR] {url} is DOWN or unreachable. Error: {e}")
        return False

def check_ssl_expiry(hostname):
    context = ssl.create_default_context()
    conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)
    try:
        conn.settimeout(5.0)
        conn.connect((hostname, 443))
        cert = conn.getpeercert()
        expire_date = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
        days_left = (expire_date - datetime.utcnow()).days
        if days_left > 0:
            print(f"[SSL] {hostname} certificate expires in {days_left} days.")
            return True
        else:
            print(f"[SSL WARNING] {hostname} certificate has expired!")
            return False
    except Exception as e:
        print(f"[SSL ERROR] Could not check SSL certificate for {hostname}. Error: {e}")
        return False

def main():
    print("Starting website and SSL checks...\n")
    for site in sites:
        check_website(site["url"])
        check_ssl_expiry(site["host"])
        print("")  # blank line for readability

if __name__ == "__main__":
    main()

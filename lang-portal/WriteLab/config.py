#!/usr/bin/env python3
# Import necessary modules
import subprocess  # To run system commands
import ipaddress  # To handle IP addresses and networks
import concurrent.futures  # To handle concurrent execution
import platform  # To check the operating system
import argparse  # To parse command line arguments
from datetime import datetime  # To handle date and time

def ping_host(ip):
    """
    Ping a host to check if it's active.
    Returns the IP address if the host is active, None otherwise.
    """
    # Adjust ping command based on operating system
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    # Use subprocess to run ping command with a timeout
    command = ['ping', param, '1', '-w', '1', str(ip)]

    try:
        # Run the ping command and capture output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)

        # Check if ping was successful
        if result.returncode == 0:
            return str(ip)  # Return IP if host is active
        return None  # Return None if ping failed
    except subprocess.TimeoutExpired:
        return None  # Return None if ping timed out
    except Exception as e:
        print(f"Error pinging {ip}: {e}")  # Print error message if an exception occurs
        return None

def scan_network(subnet):
    """
    Scan a network subnet for active hosts.
    Returns a list of active IP addresses.
    """
    # Parse the subnet to get all possible IP addresses
    network = ipaddress.ip_network(subnet)
    print(f"Starting scan of {subnet} at {datetime.now().strftime('%H:%M:%S')}")
    print(f"Scanning {network.num_addresses} addresses...")

    active_hosts = []

    # Use ThreadPoolExecutor to ping hosts concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        # Submit ping tasks for each IP in the subnet
        future_to_ip = {executor.submit(ping_host, ip): ip for ip in network.hosts()}

        # Process results as they complete
        count = 0
        for future in concurrent.futures.as_completed(future_to_ip):
            count += 1
            if count % 25 == 0:
                print(f"Progress: {count}/{network.num_addresses-2} IPs checked")

            result = future.result()
            if result:
                print(f"Host discovered: {result}")
                active_hosts.append(result)  # Add active host to the list

    return active_hosts  # Return the list of active hosts

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Simple Network Scanner')
    parser.add_argument('subnet', help='Subnet to scan, e.g., 192.168.1.0/24')
    args = parser.parse_args()

    try:
        # Run the network scan
        active_hosts = scan_network(args.subnet)

        # Display results
        print("\n--- Scan Results ---")
        print(f"Scan completed at {datetime.now().strftime('%H:%M:%S')}")
        print(f"Found {len(active_hosts)} active hosts:")
        for host in sorted(active_hosts, key=lambda ip: [int(part) for part in ip.split('.')]):
            print(host)

    except ValueError as e:
        print(f"Error: {e}")  # Print error message if an exception occurs

if __name__ == "__main__":
    main()  # Execute the main function if the script is run directly
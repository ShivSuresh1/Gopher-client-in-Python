import socket
import time

# GLOBAL VARIABLES to track crawling statistics
visited_selectors = set() 
directories = []  
text_files = [] 
binary_files = [] 
errors = [] 
external_servers = {}  

# Tracking smallest/largest files
smallest_text = {"path": "", "content": "", "size": float("inf")}  # Info about smallest text file
largest_text_size = 0                
smallest_binary_size = float("inf")
largest_binary_size = 0


def send_gopher_request(host, port, selector):
    """
    Send a gopher request to the specified server and return the response.
    
    Args:
        host (str): The Gopher server hostname/IP
        port (int): The port number to connect to
        selector (str): The Gopher selector path to request
        
    Returns:
        bytes: The raw response from the server, or None if connection failed
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # 5 seconds timeout
            s.connect((host, port))
            timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
            request_line = selector + "\r\n"
            print(f"{timestamp} Sending request: {selector}")
            s.sendall(request_line.encode())
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
            return response
    except Exception as e:
        print(f"Connection failed to {host}:{port} for selector '{selector}' - {e}")
        return None


def crawl(host, port, selector=""):
    """
    Recursively crawl a Gopher server starting from the given selector.
    
    Args:
        host (str): The Gopher server hostname/IP
        port (int): The port number to connect to
        selector (str): The Gopher selector path to start crawling from (default: "")
    """
    global largest_text_size, smallest_binary_size, largest_binary_size

    # Skip if we've already visited this selector
    if (host, port, selector) in visited_selectors:
        return
    visited_selectors.add((host, port, selector))

    # Send request and handle response
    response = send_gopher_request(host, port, selector)
    if response is None:
        errors.append((host, port, selector))
        return

    try:
        lines = response.split(b'\r\n')
        for line in lines:
            if not line:
                continue
            if line == b".":  # Gopher protocol end marker
                break

            try:
                # Parse Gopher menu line format: type+display+selector+host+port
                item_type = chr(line[0])
                parts = line[1:].decode(errors="replace").split('\t')
                if len(parts) < 4:
                    print(f"Malformed line: {line}")
                    errors.append((host, port, selector))
                    continue
                display_string, item_selector, item_host, item_port = parts
            except Exception as e:
                print(f"Failed to parse line: {line}, error: {e}")
                errors.append((host, port, selector))
                continue

            item_port = int(item_port)

            # Handle different Gopher item types
            if item_type == "1":  # Directory
                directories.append(item_selector)
                if item_host == host and item_port == port:
                    # Local directory - recurse into it
                    crawl(host, port, item_selector)
                else:
                    # External server - track its status
                    key = (item_host, item_port)
                    if key not in external_servers:
                        test_response = send_gopher_request(item_host, item_port, "")
                        external_servers[key] = (test_response is not None)
            
            elif item_type == "0":  # Text file
                file_response = send_gopher_request(item_host, item_port, item_selector)
                if file_response:
                    size = len(file_response)
                    text_files.append(item_selector)
                    # Track smallest/largest text files
                    if size < smallest_text["size"]:
                        smallest_text["path"] = item_selector
                        smallest_text["content"] = file_response.decode('utf-8', errors='replace')
                        smallest_text["size"] = size
                    if size > largest_text_size:
                        largest_text_size = size
            
            elif item_type == "9":  # Binary file
                file_response = send_gopher_request(item_host, item_port, item_selector)
                if file_response:
                    size = len(file_response)
                    binary_files.append(item_selector)
                    # Track smallest/largest binary files
                    if size < smallest_binary_size:
                        smallest_binary_size = size
                    if size > largest_binary_size:
                        largest_binary_size = size
            
            elif item_type == "3":  # Error message
                errors.append((item_host, item_port, item_selector))
            else:
                # Skip info messages or unknown types
                pass
    except Exception as e:
        print(f"Failed to process response for selector '{selector}': {e}")
        errors.append((host, port, selector))


def main():
    """
    Main function that orchestrates the Gopher crawling process.
    Gets user input, initiates crawl, and displays results.
    """
    # Get user input for server host and port
    server_host = input("Enter the Gopher server host: ").strip()
    server_port = input("Enter the Gopher server port: ").strip()
    try:
        server_port = int(server_port)
    except ValueError:
        print("Invalid port number. Please enter a valid integer.")
        return

    # Start crawling from root selector
    crawl(server_host, server_port)

    # Display results summary
    print("\n--- Summary ---")
    print(f"Number of Gopher directories: {len(directories)}\n")

    print(f"Number of text files: {len(text_files)}")
    for f in text_files:
        print(f" - {f}")
    print()

    print(f"Number of binary files: {len(binary_files)}")
    for f in binary_files:
        print(f" - {f}")
    print()

    if smallest_text["path"]:
        print(f"Contents of the smallest text file '{smallest_text['path']}':")
        print(smallest_text["content"])
    else:
        print("No text files found.")

    print(f"\nSize of the largest text file: {largest_text_size} bytes")
    print(f"Size of the smallest binary file: {smallest_binary_size} bytes")
    print(f"Size of the largest binary file: {largest_binary_size} bytes\n")

    print(f"Number of unique invalid references (errors): {len(errors)}")
    for e in errors:
        print(f" - {e}")
    print()

    print(f"External servers referenced:")
    for (host, port), is_up in external_servers.items():
        status = "UP" if is_up else "DOWN"
        print(f" - {host}:{port} -> {status}")


if __name__ == "__main__":
    main()
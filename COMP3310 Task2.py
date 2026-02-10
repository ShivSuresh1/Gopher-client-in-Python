import socket
import time

# GLOBAL VARIABLES
visited_selectors = set()
directories = []
text_files = []
binary_files = []
errors = []
external_servers = {}
smallest_text = {"path": "", "content": "", "size": float("inf")}
largest_text_size = 0
smallest_binary_size = float("inf")
largest_binary_size = 0

def send_gopher_request(host, port, selector):
    """Send a gopher request to the specified server."""
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
    global largest_text_size, smallest_binary_size, largest_binary_size

    if (host, port, selector) in visited_selectors:
        return
    visited_selectors.add((host, port, selector))

    response = send_gopher_request(host, port, selector)
    if response is None:
        errors.append((host, port, selector))
        return

    try:
        lines = response.split(b'\r\n')
        for line in lines:
            if not line:
                continue
            if line == b".":
                break

            try:
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

            if item_type == "1":  # Directory
                directories.append(item_selector)
                if item_host == host and item_port == port:
                    crawl(host, port, item_selector)
                else:
                    key = (item_host, item_port)
                    if key not in external_servers:
                        test_response = send_gopher_request(item_host, item_port, "")
                        external_servers[key] = (test_response is not None)
            elif item_type == "0":  # Text file
                file_response = send_gopher_request(item_host, item_port, item_selector)
                if file_response:
                    size = len(file_response)
                    text_files.append(item_selector)
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
                    if size < smallest_binary_size:
                        smallest_binary_size = size
                    if size > largest_binary_size:
                        largest_binary_size = size
            elif item_type == "3":  # Error
                errors.append((item_host, item_port, item_selector))
            else:
                # Skip info messages or unknown types
                pass
    except Exception as e:
        print(f"Failed to process response for selector '{selector}': {e}")
        errors.append((host, port, selector))

def main():
    # Get user input for server host and port
    server_host = input("Enter the Gopher server host: ").strip()
    server_port = input("Enter the Gopher server port: ").strip()
    try:
        server_port = int(server_port)
    except ValueError:
        print("Invalid port number. Please enter a valid integer.")
        return

    crawl(server_host, server_port)

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

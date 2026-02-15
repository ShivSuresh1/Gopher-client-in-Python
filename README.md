# Gopher Protocol Crawler (Python)

A low-level **Gopher protocol crawler** implemented in Python using raw TCP sockets.  
The crawler recursively traverses a Gopher server, downloads content, and produces detailed statistics about directories, files, and external server references.

This project demonstrates networking fundamentals, protocol parsing, and robust recursive crawling without relying on high-level HTTP libraries.

---

## Why This Project?

Most modern applications abstract networking behind HTTP libraries.  
This project intentionally works below that abstraction to demonstrate:

- Understanding of TCP/IP communication
- Ability to read and implement a formal protocol specification
- Careful handling of malformed data and unreliable networks
- Clean, maintainable Python systems code

---

## Key Features

- Raw TCP socket communication (no third-party networking libraries)
- Recursive directory crawling with loop prevention
- Accurate parsing of Gopher menu entries
- Support for multiple Gopher item types:
  - Directories
  - Text files
  - Binary files
  - Error entries
- File analysis:
  - Smallest and largest text files
  - Smallest and largest binary files
- External server detection and availability checking
- Graceful handling of malformed responses and network failures

---

## How It Works

1. Establishes a TCP connection to a Gopher server  
2. Sends selectors terminated with CRLF (`\r\n`)  
3. Parses responses according to the Gopher menu format:

   ```
   <type><display>\t<selector>\t<host>\t<port>
   ```

4. Recursively crawls local directories  
5. Downloads and analyses files  
6. Tracks visited selectors to avoid infinite recursion  
7. Aggregates crawl statistics and prints a final summary  

---

## Tech Stack

- Python 3
- TCP Socket Programming
- Gopher Protocol
- Recursive Algorithms
- Byte-level Data Processing
- Exception Handling & Fault Tolerance

---

## Skills Demonstrated

### Systems & Networking
- Low-level TCP client implementation
- Protocol-aware request/response handling
- Timeout management and network reliability considerations

### Software Engineering
- Modular design with clear function separation
- Defensive programming
- Structured error handling
- Readable and well-documented code

### Algorithms & Data Structures
- Recursive traversal
- Cycle detection using sets
- Aggregation and comparison of file statistics

---

## Running the Project

```bash
python3 crawler.py
```

You will be prompted for:
- Gopher server hostname
- Gopher server port

Example:

```
Enter the Gopher server host: gopher.example.com
Enter the Gopher server port: 70
```

---

## Example Output

- Total directories discovered
- List of text and binary files
- Contents of the smallest text file
- Largest file sizes
- Invalid or unreachable references
- Availability status of external Gopher servers

---

## Possible Improvements

- Add concurrency (asyncio or threading)
- Add CLI arguments for depth limits and output formats
- Export results to JSON or CSV
- Replace print statements with structured logging
- Add unit tests for protocol parsing

---

## Author

Shiv Suresh  

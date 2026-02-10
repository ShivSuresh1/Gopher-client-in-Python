#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 22 16:31:11 2025

@author: shiv
"""

import socket
import time
from collections import defaultdict
from urllib.parse import urlparse
from queue import Queue

class GopherCrawler:
    def __init__(self, host, port=70):
        self.host = host
        self.port = port
        self.visited = set()
        self.queue = Queue()
        self.stats = {
            'directories': 0,
            'text_files': [],
            'binary_files': [],
            'errors': [],
            'external_servers': defaultdict(bool)
        }
        self.smallest_text = {'size': float('inf'), 'content': '', 'path': ''}
        self.largest_text = {'size': 0, 'path': ''}
        self.smallest_binary = {'size': float('inf'), 'path': ''}
        self.largest_binary = {'size': 0, 'path': ''}

    def log_request(self, selector):
        print(f"[{time.strftime('%H:%M:%S')}] Requesting: {selector}")

    def fetch_resource(self, host, port, selector):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((host, port))
                s.sendall((selector + "\r\n").encode())
                
                data = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                
                return data
        except Exception as e:
            self.stats['errors'].append(f"Error fetching {selector}: {str(e)}")
            return None

    def is_text_file(self, data):
        try:
            data.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False

    def process_item(self, item_type, description, selector, host, port):
        identifier = f"{item_type}{selector}@{host}:{port}"
        if identifier in self.visited:
            return
        
        self.visited.add(identifier)
        full_path = selector if selector else "/"
        
        if item_type == '1':  # Directory
            self.stats['directories'] += 1
            self.log_request(full_path)
            data = self.fetch_resource(host, port, selector)
            if data:
                self.process_directory(data, host, port)
        
        elif item_type == '0':  # Text file
            self.log_request(full_path)
            data = self.fetch_resource(host, port, selector)
            if data:
                self.process_text_file(data, full_path)
        
        elif item_type in ['I', '9']:  # Binary file
            self.log_request(full_path)
            data = self.fetch_resource(host, port, selector)
            if data:
                self.process_binary_file(data, full_path)
        
        elif item_type == '3':  # Error
            self.stats['errors'].append(f"Error item: {full_path}")
        
        elif item_type == 'h':  # HTML (external)
            if host != self.host or port != self.port:
                self.check_external_server(host, port)

    def process_directory(self, data, host, port):
        try:
            lines = data.decode('utf-8').split('\r\n')
            for line in lines:
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 4:
                    continue
                
                item_type = parts[0][0]
                description = parts[0][1:].strip()
                selector = parts[1]
                item_host = parts[2] if parts[2] else host
                item_port = int(parts[3]) if parts[3] else port
                
                self.process_item(item_type, description, selector, item_host, item_port)
        except UnicodeDecodeError:
            self.stats['errors'].append("Invalid directory encoding")

    def process_text_file(self, data, path):
        try:
            content = data.decode('utf-8')
            size = len(data)
            
            self.stats['text_files'].append(path)
            
            if size < self.smallest_text['size']:
                self.smallest_text = {
                    'size': size,
                    'content': content[:1000],  # Only keep first 1000 chars
                    'path': path
                }
            
            if size > self.largest_text['size']:
                self.largest_text = {
                    'size': size,
                    'path': path
                }
        except UnicodeDecodeError:
            self.stats['errors'].append(f"Text file decoding failed: {path}")

    def process_binary_file(self, data, path):
        size = len(data)
        self.stats['binary_files'].append(path)
        
        if size < self.smallest_binary['size']:
            self.smallest_binary = {
                'size': size,
                'path': path
            }
        
        if size > self.largest_binary['size']:
            self.largest_binary = {
                'size': size,
                'path': path
            }

    def check_external_server(self, host, port):
        key = f"{host}:{port}"
        if key not in self.stats['external_servers']:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3)
                    s.connect((host, port))
                    self.stats['external_servers'][key] = True
            except:
                self.stats['external_servers'][key] = False

    def crawl(self):
        print(f"Starting crawl of gopher://{self.host}:{self.port}")
        start_time = time.time()
        
        # Start with root directory
        self.process_item('1', 'Root', '', self.host, self.port)
        
        print("\n=== Crawl Complete ===")
        print(f"Time taken: {time.time() - start_time:.2f} seconds")
        self.print_summary()

    def print_summary(self):
        print("\n=== Summary ===")
        print(f"Directories: {self.stats['directories']}")
        
        print(f"\nText files ({len(self.stats['text_files'])}):")
        for f in sorted(self.stats['text_files'])[:10]:  # Show first 10
            print(f"  - {f}")
        if len(self.stats['text_files']) > 10:
            print(f"  ... and {len(self.stats['text_files']) - 10} more")
        
        print(f"\nBinary files ({len(self.stats['binary_files'])}):")
        for f in sorted(self.stats['binary_files'])[:10]:
            print(f"  - {f}")
        if len(self.stats['binary_files']) > 10:
            print(f"  ... and {len(self.stats['binary_files']) - 10} more")
        
        print("\nFile size statistics:")
        if self.smallest_text['path']:
            print(f"Smallest text file: {self.smallest_text['path']} ({self.smallest_text['size']} bytes)")
            print(f"Sample content:\n{self.smallest_text['content'][:200]}...")
        if self.largest_text['path']:
            print(f"Largest text file: {self.largest_text['path']} ({self.largest_text['size']} bytes)")
        if self.smallest_binary['path']:
            print(f"Smallest binary file: {self.smallest_binary['path']} ({self.smallest_binary['size']} bytes)")
        if self.largest_binary['path']:
            print(f"Largest binary file: {self.largest_binary['path']} ({self.largest_binary['size']} bytes)")
        
        print("\nExternal servers:")
        for server, status in self.stats['external_servers'].items():
            print(f"  - {server}: {'UP' if status else 'DOWN'}")
        
        if self.stats['errors']:
            print("\nErrors encountered:")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.stats['errors']) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more")

if __name__ == "__main__":
    # Example usage:
    crawler = GopherCrawler("comp3310.ddns.net")  # Try with a public gopher server
    crawler.crawl()
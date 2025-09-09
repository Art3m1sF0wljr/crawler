import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue

def download_file(url, save_path):
    """Download a file from URL to the specified path"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded: {save_path}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def parse_directory_listing(url, base_save_dir, visited_urls=None, max_workers=5):
    """
    Parse a directory listing page and recursively process files and subdirectories
    
    Args:
        url: The URL of the directory listing page
        base_save_dir: Base directory to save downloaded files
        visited_urls: Set of URLs already visited to avoid infinite loops
        max_workers: Number of concurrent download threads
    """
    if visited_urls is None:
        visited_urls = set()
    
    # Normalize URL to avoid processing the same page multiple times
    normalized_url = url.rstrip('/') + '/'
    if normalized_url in visited_urls:
        return
    
    visited_urls.add(normalized_url)
    print(f"Processing directory: {url}")
    
    try:
        # Fetch the directory listing page
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Create a queue for download tasks
        download_queue = Queue()
        
        # Find all anchor tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip parent directory links and self-references
            if href in ['../', './', '', '/lile/'] or href.startswith('?'):
                continue
            
            # Build full URL
            full_url = urljoin(url, href)
            
            # Check if it's a directory (ends with /)
            if href.endswith('/'):
                # It's a directory - process recursively
                parse_directory_listing(full_url, base_save_dir, visited_urls, max_workers)
            
            # Check if it's a JPG/JPEG file (case insensitive)
            elif any(href.lower().endswith(ext) for ext in ['.jpg', '.jpeg']):
                # Create filename from URL
                filename = os.path.basename(href)
                save_path = os.path.join(base_save_dir, filename)
                
                # Add to download queue
                download_queue.put((full_url, save_path))
        
        # Process download queue with multiple workers
        if not download_queue.empty():
            print(f"Downloading {download_queue.qsize()} files with {max_workers} workers...")
            
            def download_worker():
                while True:
                    try:
                        file_url, file_save_path = download_queue.get_nowait()
                    except:
                        break
                    
                    download_file(file_url, file_save_path)
                    # Add a small delay to be polite to the server
                    time.sleep(0.1)
                    download_queue.task_done()
            
            # Create and start worker threads
            threads = []
            for _ in range(min(max_workers, download_queue.qsize())):
                thread = threading.Thread(target=download_worker)
                thread.start()
                threads.append(thread)
            
            # Wait for all downloads to complete
            for thread in threads:
                thread.join()
                
    except Exception as e:
        print(f"Error processing {url}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Recursively download JPG/JPEG files from web directory listings')
    parser.add_argument('url', help='URL of the directory listing page')
    parser.add_argument('--output-dir', '-o', default='downloads', 
                       help='Output directory for downloaded files (default: downloads)')
    parser.add_argument('--workers', '-w', type=int, default=5,
                       help='Number of concurrent download workers (default: 5)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Starting download from: {args.url}")
    print(f"Saving files to: {args.output_dir}")
    print(f"Using {args.workers} concurrent workers")
    print("-" * 50)
    
    # Start processing
    parse_directory_listing(args.url, args.output_dir, max_workers=args.workers)
    
    print("-" * 50)
    print("Download completed!")

if __name__ == "__main__":
    main()

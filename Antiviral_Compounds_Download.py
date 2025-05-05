"""
🧪 Molecule File Downloader Script
-----------------------------------
This script automates the downloading of `.mol` molecule files from URLs listed in `.txt` files.
It supports multithreaded downloads, retries, polite delays, logging, and summary reporting.

Key Features
-Multithreaded downloading for better performance
-Robust error handling with retry mechanism
-Progress tracking with tqdm progress bar
-Detailed logging to file and console
-Summary report generation

Author: Hariprasad T
Date: 10-10-2024
"""

# -------------------- IMPORT LIBRARIES --------------------
import os
import requests
import logging
import time
import random
from tqdm import tqdm
import concurrent.futures

# -------------------- CONFIGURATION --------------------
# Directory containing .txt files with molecule download URLs
LINKS_DIRECTORY = "F:\\D\\HARI PRASAD\\VIRAL-TARGETS-SuperNaturalDatabase"

# Directory to save the downloaded .mol files
OUTPUT_DIRECTORY = "F:\\D\\HARI PRASAD\\VIRAL-TARGETS-SuperNaturalDatabase"

# Delay range between requests to avoid overloading server (in seconds)
REQUEST_DELAY = (0.5, 2)

# Number of retry attempts for failed downloads
MAX_RETRIES = 3

# Number of threads to run concurrently
MAX_WORKERS = 5

# -------------------- LOGGING SETUP --------------------
# Setup logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("molecule_downloader.log"),
        logging.StreamHandler()
    ]
)

# -------------------- FUNCTION: Ensure output directory exists --------------------
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        logging.info(f"Creating directory: {directory}")
        os.makedirs(directory)

# -------------------- FUNCTION: Download molecule file with retry --------------------
def download_molecule(url, output_path, retries=0):
    try:
        # Respectful delay between requests
        time.sleep(random.uniform(*REQUEST_DELAY))

        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Send GET request to download molecule file
        response = requests.get(url, headers=headers, stream=True, timeout=30)

        if response.status_code == 200:
            # Save content to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        else:
            # Retry if response is not successful
            logging.warning(f"Failed to download from {url} - Status code: {response.status_code}")
            if retries < MAX_RETRIES:
                logging.info(f"Retrying download ({retries+1}/{MAX_RETRIES}): {url}")
                time.sleep((2 ** retries) + random.random())  # exponential backoff
                return download_molecule(url, output_path, retries + 1)
            return False

    except requests.exceptions.RequestException as e:
        # Retry on network errors
        logging.error(f"Request error for {url}: {e}")
        if retries < MAX_RETRIES:
            logging.info(f"Retrying download ({retries+1}/{MAX_RETRIES}): {url}")
            time.sleep((2 ** retries) + random.random())
            return download_molecule(url, output_path, retries + 1)
        return False

    except Exception as e:
        # Handle unexpected errors
        logging.error(f"Error downloading from {url}: {e}")
        return False

# -------------------- FUNCTION: Process single .txt file --------------------
def process_link_file(file_path):
    try:
        file_name = os.path.basename(file_path)
        compound_id = os.path.splitext(file_name)[0]  # extract compound ID
        with open(file_path, 'r') as f:
            url = f.read().strip()

        if not url:
            logging.warning(f"Empty URL in file: {file_path}")
            return compound_id, False

        output_path = os.path.join(OUTPUT_DIRECTORY, f"{compound_id}.mol")
        success = download_molecule(url, output_path)

        # Check if download is valid
        if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return compound_id, True
        else:
            if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
                logging.warning(f"Downloaded empty file for {compound_id}")
                os.remove(output_path)
            return compound_id, False

    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        return os.path.basename(file_path), False

# -------------------- MAIN FUNCTION --------------------
def main():
    ensure_directory_exists(OUTPUT_DIRECTORY)

    # Gather all .txt link files in the directory
    try:
        link_files = [
            os.path.join(LINKS_DIRECTORY, f)
            for f in os.listdir(LINKS_DIRECTORY)
            if f.endswith('.txt') and os.path.isfile(os.path.join(LINKS_DIRECTORY, f))
        ]
    except Exception as e:
        logging.error(f"Error accessing directory {LINKS_DIRECTORY}: {e}")
        return

    total_files = len(link_files)
    logging.info(f"Found {total_files} link files to process")

    if total_files == 0:
        logging.warning(f"No .txt files found in {LINKS_DIRECTORY}")
        return

    successful_downloads = 0
    failed_downloads = 0

    # Use thread pool for parallel downloading
    with tqdm(total=total_files, desc="Downloading molecules") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_file = {
                executor.submit(process_link_file, file_path): file_path
                for file_path in link_files
            }

            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    compound_id, success = future.result()
                    if success:
                        successful_downloads += 1
                    else:
                        failed_downloads += 1
                        logging.warning(f"Failed to download molecule for {compound_id}")
                except Exception as e:
                    failed_downloads += 1
                    logging.error(f"Exception processing {file_path}: {e}")
                pbar.update(1)

    # Log final summary
    logging.info(f"Download complete. Results: {successful_downloads} successful, {failed_downloads} failed")
    print(f"\nDownload Results: {successful_downloads} successful, {failed_downloads} failed")

    # Write summary to file
    try:
        with open(os.path.join(OUTPUT_DIRECTORY, "download_summary.txt"), "w") as f:
            f.write(f"Total files processed: {total_files}\n")
            f.write(f"Successfully downloaded: {successful_downloads}\n")
            f.write(f"Failed downloads: {failed_downloads}\n")
    except Exception as e:
        logging.error(f"Error writing summary file: {e}")

# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    logging.info("Starting molecule file downloader")
    start_time = time.time()
    main()
    elapsed_time = time.time() - start_time
    logging.info(f"Script execution completed in {elapsed_time:.2f} seconds")

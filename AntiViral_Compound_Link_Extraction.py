"""
Supernatural Compound Scraper

This script uses Selenium to automate the retrieval of 'mol-file' download links for chemical compounds 
from the SuperNatural III database. It reads a list of compound IDs from a text file, performs searches 
on the website, and saves the corresponding download links to individual files.

Key features:
- Automated browser control using Selenium
- Robust error handling 
- Progress tracking 
- Implemented rate limiting 
- Better logging 
- Directory creation 
- Better organization 
- Results verification
- "No compounds found" handling 
- Improved WebDriver management 
- Configuration parameters

Author: Hariprasad T
Date: 25-09-2025
"""




```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import logging
import time
import random

# Setup logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("supernatural_scraper.log"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

# Configuration parameters (consider moving to a config file)
DRIVER_PATH = "C:\\Users\\SEL NIVEDI\\Videos\\HARI\\chromedriver-win64\\chromedriver.exe"
DOWNLOAD_DIRECTORY = "C:\\Users\\SEL NIVEDI\\Videos\\HARI\\compounds"
ID_FILE_PATH = "C:\\Users\\SEL NIVEDI\\Videos\\HARI\\unique_ids.txt"
BASE_URL = "https://bioinf-applied.charite.de/supernatural_3/subpages/compounds.php"
REQUEST_DELAY = (1, 3)  # Random delay between requests in seconds (min, max)

# Create download directory if it doesn't exist
if not os.path.exists(DOWNLOAD_DIRECTORY):
    logging.info(f"Creating download directory: {DOWNLOAD_DIRECTORY}")
    os.makedirs(DOWNLOAD_DIRECTORY)

# Initialize the Chrome WebDriver with proper error handling
def initialize_webdriver():
    """Initialize and return a configured Chrome WebDriver."""
    try:
        service = Service(DRIVER_PATH)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")

        # Set download preferences
        prefs = {
            "download.default_directory": DOWNLOAD_DIRECTORY,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Error initializing WebDriver: {e}")
        raise

def get_link_url(driver, compound_id):
    """
    Get the 'mol-file' link URL for a given compound ID.
    Returns the URL if successful, None otherwise.
    """
    try:
        # Navigate to the search page with a random delay to avoid detection
        driver.get(BASE_URL)

        # Wait for page to fully load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//body")))

        # Locate and interact with the search box
        search_box = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="id"]')))
        search_box.clear()
        search_box.send_keys(compound_id)

        # Click the search button
        find_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="searchform"]/table/tbody/tr[5]/td/div/input[2]')
        ))
        find_button.click()

        # Check if "No compounds found" message appears
        try:
            no_results = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'No compounds found')]"))
            )
            logging.warning(f"No compounds found for ID {compound_id}")
            return None
        except TimeoutException:
            # Continue if "No compounds found" message is not present
            pass

        # Look for the mol-file link
        try:
            mol_file_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'mol-file')))
            link_url = mol_file_link.get_attribute("href")
            return link_url
        except TimeoutException:
            logging.warning(f"'mol-file' link not found for ID {compound_id}")
            return None

    except Exception as e:
        logging.error(f"Error processing ID {compound_id}: {e}")
        return None

def process_ids(id_file):
    """
    Process each ID in the given text file and save the 'mol-file' link URL.
    Implements error handling for individual compounds.
    """
    # Verify the ID file exists
    if not os.path.exists(id_file):
        logging.error(f"ID file not found: {id_file}")
        return

    try:
        with open(id_file, 'r') as file:
            ids = [line.strip() for line in file.readlines()]

        total_ids = len(ids)
        logging.info(f"Found {total_ids} compound IDs to process")

        # Initialize counter variables
        successful_downloads = 0
        failed_downloads = 0

        # Initialize WebDriver
        driver = initialize_webdriver()

        # Process each compound ID
        for index, compound_id in enumerate(ids):
            if not compound_id:  # Skip empty lines
                continue

            # Log progress
            logging.info(f"Processing ID {index+1}/{total_ids}: {compound_id}")

            try:
                # Get the mol-file link URL
                link_url = get_link_url(driver, compound_id)

                if link_url:
                    # Save the link URL to a file
                    url_file_path = os.path.join(DOWNLOAD_DIRECTORY, f"{compound_id}.txt")
                    try:
                        with open(url_file_path, "w") as file:
                            file.write(link_url)
                        logging.info(f"Link URL for {compound_id} saved to {url_file_path}")
                        successful_downloads += 1
                    except Exception as e:
                        logging.error(f"Error writing link URL for {compound_id} to file: {e}")
                        failed_downloads += 1
                else:
                    logging.warning(f"Failed to retrieve link for ID {compound_id}")
                    failed_downloads += 1

                # Add a random delay between requests to avoid overloading the server
                time.sleep(random.uniform(*REQUEST_DELAY))

            except Exception as e:
                logging.error(f"Error processing compound {compound_id}: {e}")
                failed_downloads += 1

        # Log summary statistics
        logging.info(f"Processing complete. Results: {successful_downloads} successful, {failed_downloads} failed")

    except Exception as e:
        logging.error(f"Error reading ID file {id_file}: {e}")
    finally:
        # Ensure the WebDriver is properly closed
        try:
            driver.quit()
            logging.info("WebDriver closed successfully")
        except Exception as e:
            logging.error(f"Error closing WebDriver: {e}")

if __name__ == "__main__":
    logging.info("Starting supernatural compound scraper")
    process_ids(ID_FILE_PATH)
    logging.info("Script execution completed")
```

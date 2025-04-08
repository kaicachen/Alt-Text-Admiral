from transformers import DetrImageProcessor, DetrForObjectDetection, logging
from csv import reader, writer, QUOTE_ALL
import google.generativeai as genai
from dotenv import load_dotenv
from data_processor import *
from os import path, getenv
from sqlite3 import connect
from hashlib import sha256
from web_scraper import *
from json import loads
from time import sleep
from torch import cuda
from sys import argv
from re import sub


class SiteProcessor:
    def __init__(self, url, annotations):
        load_dotenv()
        # Loads Gemini model
        self._gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        genai.configure(api_key=getenv('GEMINI_API_KEY'))
        sleep(1)

        # Sets active device as GPU if available, otherwise it runs on the CPU
        self._device = "cuda" if cuda.is_available() else "cpu"

        # Load the DETR model and processor
        self._detr_processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        self._detr_model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(self._device)

        # Reduce console output
        logging.set_verbosity_error()

        # Save site URL for future use
        self.site_url = url

        # Replaces characters in the URL to make it a valid file name
        self.file_name = sub(r'[\/:*?"<>|]', '-', url)[:20]

        # Saves image annotations
        self.annotations = annotations


    def _generate_alt_text(self, image_type, image_url, text, fetch_db=True):
        # Open cache database
        cache_db = connect(path.join("app", "app_code", "cached_results.db"))
        cache_db_cursor = cache_db.cursor()

        # Ensure the table exists
        cache_db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_results (
                hash VARCHAR(255) PRIMARY KEY,
                alt_text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                                """)
        
        # Compute hash to see if alt text has already been generated
        hash = sha256(str((type, image_url, text)).encode())
        cache_db_cursor.execute("SELECT alt_text FROM cached_results WHERE hash=?", (hash.hexdigest(),))
        db_fetch = cache_db_cursor.fetchone()

        # Updates the timestamp of the value if found in database
        if db_fetch:
            cache_db_cursor.execute("UPDATE cached_results SET timestamp=CURRENT_TIMESTAMP WHERE hash=?", (hash.hexdigest(),))

        # Returns database value if enabled
        if fetch_db and db_fetch:
            cache_db.commit()
            cache_db.close()
            return db_fetch[0]

        # Create data processor object
        image_processor = DataProcessor(image_url, image_type, text, self._gemini_model, self._detr_model, self._detr_processor, self._device)

        # Generate alt-text
        alt_text = image_processor.process_data()

        # Update database with newest alt-text
        if db_fetch:
            cache_db_cursor.execute("UPDATE cached_results SET alt_text=? WHERE hash=?", (hash.hexdigest(), alt_text))

        # Add to database
        else:
            cache_db_cursor.execute("INSERT INTO cached_results (hash, alt_text) VALUES (?, ?)", (hash.hexdigest(), alt_text))

        # Check if the row count exceeds 500, then delete the oldest rows
        cache_db_cursor.execute("SELECT COUNT(*) FROM cached_results")
        row_count = cache_db_cursor.fetchone()[0]

        if row_count > 500:
            cache_db_cursor.execute("""
                DELETE FROM cached_results
                WHERE timestamp = (SELECT timestamp FROM cached_results ORDER BY timestamp ASC LIMIT 1)
                                    """)
        
        cache_db.commit()
        cache_db.close()

        return alt_text
    

    '''Takes in a list of indices to remove given images from a CSV found with the given URL'''
    def _exclude_images(self):
        # Early exit for no changes
        if len(self.annotations) == 0:
            return

        # Creates list to store image, text tuples from the site CSV
        site_data = []

        # Reads all image, text tuples scraped from the URL
        with open(path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{self.file_name}.csv"), mode="r", newline="", encoding="utf-8") as file:
            csv_reader = reader(file)
            
            # Read a header row
            next(csv_reader)
            
            # Stores the image, text tuple
            for row in csv_reader:
                site_data.append(tuple(row))

        # Reopens the same CSV to write the updated list with exclusions
        with open(path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{self.file_name}.csv"), mode="w", newline="", encoding="utf-8") as file:
            csv_writer = writer(file, quoting=QUOTE_ALL)
            
            # Write a header row
            csv_writer.writerow(["image_type", "image_link", "surrounding_text"])
            
            # Iterate through image, text tuples
            for i in range(len(site_data)):
                # Skip over exclusions
                if self.annotations[i] == 3:
                    continue

                # Rewrite tuples
                csv_writer.writerow([
                    self.annotations[i],
                    site_data[i][0],
                    site_data[i][1]
                ])


    '''Generates alt-text for each image, text tuple in a given CSV'''
    def _process_csv(self):
        # Creates list to store image, text tuples from the site CSV
        site_data = []

        # Reads all image, text tuples scraped from the URL
        with open(path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{self.file_name}.csv"), mode="r", newline="", encoding="utf-8") as file:
            csv_reader = reader(file)
            
            # Read a header row
            next(csv_reader)
            
            # Stores the image, text tuple
            for row in csv_reader:
                site_data.append(tuple(row))

        # Early exit if there are no images to process
        if site_data is None:
            return

        # Opens a file to store the output of images and alt-text
        with open(path.join("app", "app_code", "outputs", "CSVs", f"{self.file_name}.csv"), mode="w", newline="", encoding="utf-8") as file:
            csv_writer = writer(file, quoting=QUOTE_ALL)
            
            # Write a header row
            csv_writer.writerow(["image_link", "generated_output"])

            # Writes the image URL and alt-text to the CSV
            for type, image, text in site_data:
                csv_writer.writerow([
                    image,
                    self._generate_alt_text(type, image, text)
                ])
    

    def process_site(self):
        self._exclude_images()
        self._process_csv()


if __name__ == "__main__":
    url = argv[1]
    annotations = loads(argv[2])
    site_processor = SiteProcessor(url, annotations)
    site_processor.process_site()
from transformers import DetrImageProcessor, DetrForObjectDetection, logging
from google import genai
from dotenv import load_dotenv
from app_code.data_processor import *
from warnings import filterwarnings
from os import path, getenv
from sqlite3 import connect
from hashlib import sha256
from app_code.web_scraper import *
from json import loads
from time import sleep
from torch import cuda
from sys import argv


class SiteProcessor:
    def __init__(self, site_data, annotations):
        # Don't show non-meta parameter warning
        filterwarnings("ignore", message=".*copying from a non-meta parameter.*")

        # Reduce console output
        logging.set_verbosity_error()

        # Load environmental variables
        load_dotenv()
        
        # Loads Gemini client and a model name
        self._gemini_client = genai.Client(api_key=getenv('GEMINI_API_KEY'))

        sleep(1)

        # Sets active device as GPU if available, otherwise it runs on the CPU
        self._device = "cuda" if cuda.is_available() else "cpu"

        # Load the DETR model and processor
        self._detr_processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        self._detr_model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(self._device)

        # Saves site data
        self.site_data = site_data

        # Saves image annotations
        self.annotations = annotations


    '''Generate alt-text from the given data or fetch from the database if possible'''
    def generate_alt_text(self, image_type, image_url, text, href, fetch_db=True):
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
        hash = sha256(str((image_type, image_url, text, href)).encode())
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
        image_processor = DataProcessor(image_url, image_type, text, href, self._gemini_client, self._detr_model, self._detr_processor, self._device)

        # Generate alt-text
        alt_text = image_processor.process_data()

        # Update database with newest alt-text
        if db_fetch:
            cache_db_cursor.execute("UPDATE cached_results SET alt_text=? WHERE hash=?", (alt_text, hash.hexdigest()))

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


    '''Generates the needed alt-text for all images'''
    def process_site(self):
        # Early exit if there are no images to process
        if self.site_data is None:
            return
        
        generated_data = []

        # Adds the image URL and alt-text to the list
        for i in range(len(self.site_data)):
            print(f"Processing image {i + 1} of {len(self.site_data)}")

            # Pass if the image shall be excluded
            if self.annotations[i] == 3:
                continue

            # Add image, alt-text tuple to list
            generated_data.append((
                self.site_data[i][0],
                self.generate_alt_text(
                    image_type = self.annotations[i],
                    image_url  = self.site_data[i][0],
                    text       = self.site_data[i][1], 
                    href       = self.site_data[i][2])
            ))

        return generated_data


if __name__ == "__main__":
    url = loads(argv[1])
    annotations = loads(argv[2])
    site_processor = SiteProcessor(site_data, annotations)
    site_processor.process_site()
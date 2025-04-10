from transformers import DetrImageProcessor, DetrForObjectDetection, logging
from supabase import create_client, Client
from csv import reader, writer, QUOTE_ALL
from datetime import datetime, timezone
import google.generativeai as genai
from dotenv import load_dotenv
from data_processor import *
from os import path, getenv, getcwd
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
        # Load environmental variables
        load_dotenv()

        # Get environmental variables
        gemini_key  : str = getenv("GEMINI_API_KEY")
        supabase_url: str = getenv("SUPABASE_URL")
        supabase_key: str = getenv("SUPABASE_API_KEY")

        # Loads Gemini model
        self._gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        genai.configure(api_key=gemini_key)
        sleep(1)

        # Initializes Supabase Connection
        self._supabase: Client = create_client(supabase_url, supabase_key)

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


    '''Generate alt-text from the given data or fetch from the database if possible'''
    def _generate_alt_text(self, image_type, image_url, text, href, fetch_db=True):        
        # Compute hash to see if alt text has already been generated
        hash = sha256(str((image_type, image_url, text, href)).encode())

        # Attempt to read from database
        response = (
            self._supabase.table("Cached Results")
            .select("alt_text")
            .eq("hash", hash.hexdigest())
            .execute()
            )

        # Updates the timestamp of the value if found in database
        if len(response.data):
            response = (
                self._supabase.table("Cached Results")
                .update({"last_access" : datetime.now(timezone.utc).isoformat()})
                .eq("hash", hash.hexdigest())
                .execute()
            )

        # Returns database value if enabled
        if fetch_db and len(response.data):
            return response.data[0]["alt_text"]

        # Create data processor object
        image_processor = DataProcessor(image_url, image_type, text, href, self._gemini_model, self._detr_model, self._detr_processor, self._device)

        # Generate alt-text
        alt_text = image_processor.process_data()

        # Update database with newest alt-text
        if len(response.data):
            response = (
                self._supabase.table("Cached Results")
                .update({"alt_text" : alt_text})
                .eq("hash", hash.hexdigest())
                .execute()
            )

        # Add to database
        else:
            try:
                response = (
                    self._supabase.table("Cached Results")
                    .insert({"hash": hash.hexdigest(),
                            "alt_text": alt_text
                            })
                    .execute()
                    )
                
            except Exception as e:
                print(f"Error adding tuple to the database: hash: {hash.hexdigest()}, alt-text: {alt_text}, ERROR: {e}")

        return alt_text


    '''Generates the needed alt-text for all images'''
    def process_site(self):
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
            for i in range(len(site_data)):
                # Pass if the image shall be excluded
                if self.annotations[i] == 3:
                    continue

                csv_writer.writerow([
                    site_data[i][0],
                    self._generate_alt_text(
                        image_type = self.annotations[i],
                        image_url  = site_data[i][0],
                        text       = site_data[i][1], 
                        href       = site_data[i][2])
                ])


if __name__ == "__main__":
    url = argv[1]
    annotations = loads(argv[2])
    site_processor = SiteProcessor(url, annotations)
    site_processor.process_site()
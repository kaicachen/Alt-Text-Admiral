from transformers import DetrImageProcessor, DetrForObjectDetection, logging
from supabase import create_client, Client
from datetime import datetime, timezone
from warnings import filterwarnings
from dotenv import load_dotenv
from .data_processor import *
from base64 import b64decode
from os import path, environ
from hashlib import sha256
from .web_scraper import *
from google import genai
from json import loads
from time import sleep
from torch import cuda
from io import BytesIO
from sys import argv


class SiteProcessor:
    def __init__(self, site_data, annotations):
        # Don't show non-meta parameter warning
        filterwarnings("ignore", message=".*copying from a non-meta parameter.*")

        # Reduce console output
        logging.set_verbosity_error()

        # Load environmental variables
        load_dotenv(".env")

        # Get environmental variables
        gemini_key  : str = environ.get("GEMINI_API_KEY")
        supabase_url: str = environ.get("SUPABASE_URL")
        supabase_key: str = environ.get("SUPABASE_API_KEY")

        # Loads Gemini client and a model name
        self._gemini_client = genai.Client(api_key=gemini_key)
        sleep(1)

        # Initializes Supabase Connection
        self._supabase: Client = create_client(supabase_url, supabase_key)

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
        # Compute hash to see if alt text has already been generated
        hash = sha256(str((image_type, image_url, text, href)).encode())

        # Attempt to read from database
        try:
            response = (
                self._supabase.table("Cached Results")
                .select("alt_text")
                .eq("hash", hash.hexdigest())
                .execute()
                )
        except Exception as e:
            print(f"Error reading tuple from the database: hash: {hash.hexdigest()}, ERROR: {e}")
            response = None

        # Updates the timestamp of the value if found in database
        if response and len(response.data):
            try:
                response = (
                    self._supabase.table("Cached Results")
                    .update({"last_access" : datetime.now(timezone.utc).isoformat()})
                    .eq("hash", hash.hexdigest())
                    .execute()
                )
            except Exception as e:
                print(f"Error updating tuple time in the database: hash: {hash.hexdigest()} ERROR: {e}")
                response = None

        # Returns database value if enabled
        if fetch_db and response and len(response.data):
            return response.data[0]["alt_text"]

        # Create data processor object
        if type(image_url) is BytesIO:
            image_processor = DataProcessor(image_url, image_type, text, href, self._gemini_client, self._detr_model, self._detr_processor, self._device, URL=False)
            
        else:
            image_processor = DataProcessor(image_url, image_type, text, href, self._gemini_client, self._detr_model, self._detr_processor, self._device)

        # Generate alt-text
        alt_text = image_processor.process_data()

        # Update database with newest alt-text
        if response and len(response.data):
            try:
                response = (
                    self._supabase.table("Cached Results")
                    .update({"alt_text" : alt_text})
                    .eq("hash", hash.hexdigest())
                    .execute()
                )
            except Exception as e:
                print(f"Error updating tuple alt-text in the database: hash: {hash.hexdigest()}, alt-text: {alt_text} ERROR: {e}")
                response = None

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

            # User added image
            if self.site_data[i][0] is None:
                # Split the header from the actual base64 data
                header, base64_data = self.site_data[i][3].split("base64,", 1)

                # Optional: Extract MIME type from the header
                mime_type = header.split(":")[1].split(";")[0]

                # Decode base64 to bytes
                image_bytes = b64decode(base64_data)

                # Add image, alt-text tuple to list
                generated_data.append((
                    self.site_data[i][3],
                    self.generate_alt_text(
                        image_type = self.annotations[i],
                        image_url  = BytesIO(image_bytes),
                        text       = self.site_data[i][1], 
                        href       = self.site_data[i][2])
                ))

            # Standard scraped URL image
            else:
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
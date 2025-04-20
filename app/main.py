from .app_code.site_processor import SiteProcessor
from .app_code.web_scraper import WebScraper
from supabase import create_client, Client
from .app_code.user_info import UserInfo
from base64 import b64decode, b64encode
from dotenv import load_dotenv
from sys import getsizeof
from os import environ
from io import BytesIO
from PIL import Image

'''Login or create new user and then login'''
def login_user(email):
    user_info = UserInfo(email=email)
    return user_info.user_id


'''Scrape website'''
def web_scraper(url):
    web_scraper = WebScraper(url)
    return web_scraper.scrape_site()


'''Generate alt-text for all data tuples'''
def process_site(site_data, annotations, url, user_id):
    # Process data
    site_processor = SiteProcessor(site_data, annotations)
    generated_data = site_processor.process_site()

    # Initialize generation ID and data_ids
    generation_id = None
    data_ids = [None] * len(generated_data)

    # Store the generation
    if url is not None and user_id is not None:
        user_info = UserInfo(user_id=user_id)
        generation_id, data_ids = user_info.store_generation(url, generated_data)

    print(f"Length of generated data: {len(generated_data)}, length of data IDs: {len(data_ids)}, generation ID: {generation_id}")
    return generated_data, generation_id, data_ids


'''Shows previous site generation information'''
def load_history(user_id):
    user_info = UserInfo(user_id=user_id)
    return user_info.previous_generations()


'''Loads previous site generation'''
def load_generation(generation_id):
    user_info = UserInfo()
    return user_info.load_generation(generation_id)


'''Regenerate alt-text for an image'''
def regenerate(data_id, image_type, image_url, text, href):
    # Site data and annotation list not needed
    site_processor = SiteProcessor(None, None)

    # User uploaded image
    if image_url[:23] == "data:image/jpeg;base64,":
        # Split the header from the actual base64 data
        _, base64_data = image_url.split("base64,", 1)

        # Decode base64 to bytes
        image_bytes = b64decode(base64_data)

        # Generate alt-text
        alt_text = site_processor.generate_alt_text(image_type, BytesIO(image_bytes), text, href, fetch_db=False)

    # Standard scraped image
    else:
        alt_text = site_processor.generate_alt_text(image_type, image_url, text, href, fetch_db=False)

    # Update the stored generation
    if data_id is not None:
        # Load environmental variables
        load_dotenv(".env")

        # Get environmental variables
        supabase_url: str = environ.get("SUPABASE_URL")
        supabase_key: str = environ.get("SUPABASE_API_KEY")

        # Initializes Supabase Connection
        supabase: Client = create_client(supabase_url, supabase_key)

        # Update the alt text for the data ID
        try:
            response = (
                supabase.table("Generation Data")
                .update({"alt_text" : alt_text})
                .eq("data_id", data_id)
                .execute()
                )
            
        except Exception as e:
            print(f"Error adding tuple to the database: data_id: {data_id}, alt_text: {alt_text}, ERROR: {e}")

    return alt_text


'''Reduce size of added images'''
def reduce_image_size(base64_str, max_width=512):
    # Split metadata header
    _, base64_data = base64_str.split(',', 1)

    # Decode base64 to bytes
    image_data = b64decode(base64_data)
    image = Image.open(BytesIO(image_data))

    # Resize if image is wider than max_width
    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_size = (max_width, int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Re-encode image to bytes (compressed)
    output_buffer = BytesIO()
    image = image.convert('RGB')
    image.save(output_buffer, format='JPEG', quality=70)
    compressed_bytes = output_buffer.getvalue()

    # Convert back to base64
    compressed_base64 = b64encode(compressed_bytes).decode('utf-8')
    
    # Show size change
    print(f"Original size: {getsizeof(base64_data)} New size: {getsizeof(compressed_base64)}")

    # Add back the header
    return f"data:image/jpeg;base64,{compressed_base64}"
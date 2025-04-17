from app_code.site_processor import SiteProcessor
from app_code.web_scraper import WebScraper
from supabase import create_client, Client
from app_code.user_info import UserInfo
from dotenv import load_dotenv
from os import environ

'''Login or create new user and then login'''
def login_user(username, email):
    user_info = UserInfo(username=username, email=email)
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


'''Regenerate alt-text for an image'''
def regenerate(data_id, image_type, image_url, text, href):
    # Site data and annotation list not needed
    site_processor = SiteProcessor(None, None)
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


'''Add image to generation'''
def add_image(generation_id, image_url):
    # Site data and annotation list not needed
    site_processor = SiteProcessor(None, None)
    alt_text = site_processor.generate_alt_text(0, image_url, "", "")

    # Add the image to the generation ID
    if generation_id is not None:
        # Load environmental variables
        load_dotenv(".env")

        # Get environmental variables
        supabase_url: str = environ.get("SUPABASE_URL")
        supabase_key: str = environ.get("SUPABASE_API_KEY")

        # Initializes Supabase Connection
        supabase: Client = create_client(supabase_url, supabase_key)

        # Add data to the database
        try:
            response = (
                supabase.table("Generation Data")
                .insert({
                    "image_url" : image_url,
                    "alt_text" : alt_text,
                    "generation_id" : generation_id})
                .execute()
                )
            
        except Exception as e:
            print(f"Error adding tuple to the database: generation_id: {generation_id}, image_url: {image_url} alt_text: {alt_text}, ERROR: {e}")

    return alt_text
from app_code.site_processor import SiteProcessor
from app_code.web_scraper import WebScraper

'''Scrape website'''
def web_scraper(url):
    web_scraper = WebScraper(url)
    return web_scraper.scrape_site()


'''Generate alt-text for all data tuples'''
def process_site(site_data, annotations):
    site_processor = SiteProcessor(site_data, annotations)
    return site_processor.process_site()


'''Regenerate alt-text for an image'''
def regenerate(image_type, image_url, text, href):
    # site data and annotation list not needed
    site_processor = SiteProcessor(None, None)
    return site_processor.generate_alt_text(image_type, image_url, text, href, fetch_db=False)


'''Add image to generation'''
def add_image(image_type, image_url, href):
    # site data and annotation list not needed
    site_processor = SiteProcessor(None, None)
    return site_processor.generate_alt_text(image_type, image_url, "", href)
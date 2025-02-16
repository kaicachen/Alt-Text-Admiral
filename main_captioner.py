from create_caption import *
from web_scraper import *
import csv

def caption_site(url):
    site_data = scrape(url)

    if site_data is None:
        return

    with open(f"{url}.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write a header row (optional)
        writer.writerow(["image_link", "generated_output"])
        
        for image, text in site_data:
            writer.writerow([
                image,
                create_caption(image, text, URL=True)
            ])

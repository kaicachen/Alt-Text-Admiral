from create_caption import *
from web_scraper import *
from csv_to_pdf import *
import csv

def caption_site(url, output_name='site'):
    site_data = scrape(url)

    if site_data is None:
        return

    with open(f"{output_name}.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write a header row (optional)
        writer.writerow(["image_link", "generated_output"])
        
        for image, text in site_data:
            writer.writerow([
                image,
                create_caption(image, text, URL=True)
            ])

if __name__ == "__main__":
    output_name = "lied_center"
    caption_site("https://lied.ku.edu", output_name=output_name)
    create_pdf(output_name)
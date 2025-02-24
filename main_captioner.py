from create_caption import create_caption
from web_scraper import scrape
from csv_to_pdf import create_pdf
import csv
import time

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
    start_time = time.time()
    
    output_name = "lied_center"
    site_url = "https://lied.ku.edu/?event=mnozil-brass-2025&event_date=2025-03-03%2019:30"
    caption_site(site_url, output_name=output_name)
    create_pdf(output_name)
    
    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")

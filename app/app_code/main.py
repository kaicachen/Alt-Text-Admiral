import os
from create_caption import *
from csv_to_pdf import create_pdf
from app.app_code.generate_alt_text import *
from web_scraper import *
import csv
import time


def run():
    url = sys.argv[1]  # url is passed to script through argv
    # site_data = scrape_site(url)
    # for data in site_data:
    #     create_caption(data[0],data[1])

    # process_site(url)

    output_name = re.sub(r'[\/:*?"<>|]', '-', url)[:20]

    scraped = scrape_site(url)
    print(f"Scraped {len(scraped)} tuples")

    print("All scraped images:\n------------------------------------------------------------")
    # Print all image links
    with open(os.path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{output_name}.csv"), mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        # Read a header row
        next(reader)
        
        count = 0
        for image, text in reader:
            print(f"{count}: {image}")
            count += 1

    print("------------------------------------------------------------\nEnter image indices to exclude, separate by a space")
    index_string = input("Indices: ")
    image_idx = [int(x) for x in index_string.split()]
    
    exclude_images(url, image_idx)
    process_csv(url)

if __name__ == "__main__":
    run()
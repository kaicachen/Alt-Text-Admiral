from create_caption import *
from web_scraper import *
from csv_to_pdf import *
import json
import csv
import os
import re

'''Scrapes entire site and generates alt-text for all images found'''
def process_site(url):
    # Scrape site
    site_data = scrape_site(url)

    # Early exit if no data is scraped
    if site_data is None:
        return

    # Replaces characters in the URL to make it a valid file name
    output_name = re.sub(r'[\/:*?"<>|]', '-', url)[:20]

    # Opens a file to store the output of images and alt-text
    with open(os.path.join("app", "app_code", "outputs", "CSVs", f"{output_name}.csv"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write a header row
        writer.writerow(["image_link", "generated_output"])
        
        # Writes the image URL and alt-text to the CSV
        for image, text in site_data:
            writer.writerow([
                image,
                create_caption(image, text, URL=True)
            ])


'''Takes in a list of indices to remove given images from a CSV found with the given URL'''
def exclude_images(url, image_idices):
    # Early exit for no changes
    if len(image_idices) == 0:
        return

    # Creates list to store image, text tuples from the site CSV
    site_data = []

    # Replaces characters in the URL to make it a valid file name
    output_name = re.sub(r'[\/:*?"<>|]', '-', url)[:20]

    # Reads all image, text tuples scraped from the URL
    with open(os.path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{output_name}.csv"), mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        # Read a header row
        next(reader)
        
        # Stores the image, text tuple
        for row in reader:
            site_data.append(tuple(row))

    # Reopens the same CSV to write the updated list with exclusions
    with open(os.path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{output_name}.csv"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        
        # Write a header row
        writer.writerow(["image_type", "image_link", "surrounding_text"])
        
        # Iterate through image, text tuples
        for i in range(len(site_data)):
            # Skip over exclusions
            if image_idices[i] == 3:
                continue

            # Rewrite tuples
            writer.writerow([
                image_idices[i],
                site_data[i][0],
                site_data[i][1]
            ])


'''Generates alt-text for each image, text tuple in a given CSV'''
def process_csv(url):
    # Creates list to store image, text tuples from the site CSV
    site_data = []

    # Replaces characters in the URL to make it a valid file name
    output_name = re.sub(r'[\/:*?"<>|]', '-', url)[:20]

    # Reads all image, text tuples scraped from the URL
    with open(os.path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{output_name}.csv"), mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        # Read a header row
        next(reader)
        
        # Stores the image, text tuple
        for row in reader:
            site_data.append(tuple(row))

    # Early exit if there are no images to process
    if site_data is None:
        return

    # Opens a file to store the output of images and alt-text
    with open(os.path.join("app", "app_code", "outputs", "CSVs", f"{output_name}.csv"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        
        # Write a header row
        writer.writerow(["image_link", "generated_output"])

        # Writes the image URL and alt-text to the CSV
        for type, image, text in site_data:
            writer.writerow([
                image,
                create_caption(type, image, text, URL=True)
            ])


if __name__ == "__main__":
    url = sys.argv[1]
    tags = json.loads(sys.argv[2])
    print(f"URL: {url}")
    print(f"TAGS: {tags}")
    exclude_images(url, tags)
    process_csv(url)
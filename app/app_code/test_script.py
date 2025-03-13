import os
from create_caption import *
from csv_to_pdf import create_pdf
from main_captioner import *
from web_scraper import *
import csv
import time


def run():
    url = sys.argv[1]  # url is passed to script through argv
    # site_data = scrape(url)
    # for data in site_data:
    #     create_caption(data[0],data[1])

    caption_site(url)


def run_tests():
    input_data = []

    # Open and read the CSV file
    with open(os.path.join("app", "app_code", "inputs", "CSVs", "test_inputs.csv"), mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        next(reader)

        # Convert reader object to a list or iterate over rows
        for row in reader:
            input_data.append(row)

    with open(os.path.join("app", "app_code", "outputs", "CSVs", "test_outputs.csv"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write a header row (optional)
        writer.writerow(["image_loc", "generated_output"])
        
        for url, image, text in input_data:
            old_image_name = image
            print(image)
            if url == "0":
                base_path = os.path.join(os.path.dirname(__file__), "inputs", "Images")
                image = os.path.join(base_path, image)

            writer.writerow([
                old_image_name,
                create_caption(image, text, URL=bool(int(url)))
            ])

def run_site_tests(pool=1):
    input_data = []

    # Open and read the CSV file
    # with open(os.path.join("app", "app_code", "inputs", "CSVs", "website_test_inputs.csv"), mode="r", newline="", encoding="utf-8") as file:
    with open(os.path.join("app", "app_code", "inputs", "CSVs", "website_test_inputs.csv"), mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        next(reader)

        # Convert reader object to a list or iterate over rows
        for row in reader:
            input_data.append(row)

    with open(os.path.join("app", "app_code", "outputs", "CSVs", "website_test_outputs.csv"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write a header row (optional)
        writer.writerow(["website", "start_time", "end_time", "run_time"])
    
        total_start_time = time.time()
        for website, output_name in input_data:
            start_time = time.time()
            caption_site(website, output_name=output_name, pool=pool)
            end_time = time.time()
            writer.writerow([
                website,
                start_time,
                end_time,
                end_time - start_time
            ])
            create_pdf(output_name)

        total_end_time = time.time()
        writer.writerow([
            "TOTAL_TIME",
            total_start_time,
            total_end_time,
            total_end_time - total_start_time
            ])
        

def run_multiprocess_tests():
    output_name = "ku_lied"
    site_url = "https://lied.ku.edu"

    with open(os.path.join("app", "app_code", "outputs", "CSVs", "multiprocess_test_outputs.csv"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "pool",
            "start_time",
            "end_time",
            "run_time"
        ])
        for pool in range(1, 5):
            start_time = time.time()
            caption_site(site_url, output_name=output_name, pool=pool)
            create_pdf(f"{output_name}_pool_{pool}")
            end_time = time.time()
            print(f"Execution time: {end_time - start_time:.2f} seconds")
            writer.writerow([
                pool,
                start_time,
                end_time,
                end_time - start_time
            ])


if __name__ == "__main__":
    run_tests()
    # create_pdf("test_outputs")
    # run_site_tests()
    # run_multiprocess_tests()
    # run()

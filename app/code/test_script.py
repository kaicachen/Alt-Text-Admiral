import os
from create_caption import *
from csv_to_pdf import create_pdf
from main_captioner import *
import csv
import time


def run_tests(self):
    input_data = []

    # Open and read the CSV file
    with open(os.path.join("inputs", "CSVs", "test_inputs.csv"), mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        next(reader)

        # Convert reader object to a list or iterate over rows
        for row in reader:
            input_data.append(row)

    with open(os.path.join("outputs", "CSVs", "test_outputs.csv"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write a header row (optional)
        writer.writerow(["image_loc", "generated_output"])
        
        for url, image, text in input_data:
            if url == "0":
                image = os.path.join(self.INPUTS_DIR, "Images", image)

            writer.writerow([
                image,
                create_caption(image, text, URL=bool(int(url)))
            ])

def run_site_tests(self, pool=1):
    input_data = []

    # Open and read the CSV file
    with open(os.path.join("inputs", "CSVs", "website_test_inputs.csv"), mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        next(reader)

        # Convert reader object to a list or iterate over rows
        for row in reader:
            input_data.append(row)

    with open(os.path.join("outputs", "CSVs", "website_test_outputs.csv"), mode="w", newline="", encoding="utf-8") as file:
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


if __name__ == "__main__":
    # run_tests()
    # create_pdf("test_outputs")
    run_site_tests()

import sys
import os

# Get the absolute path to the root directory of your project
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))  # This will give the path to /Root
CODE_DIR = os.path.join(ROOT_DIR, 'Backend', 'Code')  # This points to /Root/Backend/Code

# Add the Backend/Code directory to sys.path
sys.path.append(CODE_DIR)

from Main.create_caption import *
from csv_to_pdf import create_pdf
from Main.main_captioner import *
import csv
import time

class TestScript:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.INPUTS_DIR = os.path.join(BASE_DIR, 'Inputs')
        self.OUTPUTS_DIR = os.path.join(BASE_DIR, 'Outputs')


    def run_tests(self):
        input_data = []

        # Open and read the CSV file
        with open(os.path.join(self.INPUTS_DIR, "CSVs", "test_inputs.csv"), mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            
            next(reader)

            # Convert reader object to a list or iterate over rows
            for row in reader:
                input_data.append(row)

        with open(os.path.join(self.OUTPUTS_DIR, "CSVs", "test_outputs.csv"), mode="w", newline="", encoding="utf-8") as file:
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
        with open(os.path.join(self.INPUTS_DIR, "CSVs", "website_test_inputs.csv"), mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            
            next(reader)

            # Convert reader object to a list or iterate over rows
            for row in reader:
                input_data.append(row)

        with open(os.path.join(self.OUTPUTS_DIR, "CSVs", "website_test_outputs.csv"), mode="w", newline="", encoding="utf-8") as file:
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
    tests = TestScript()
    # tests.run_tests()
    # create_pdf("test_outputs")
    tests.run_site_tests()

"""
    Saves image metadata to a CSV file, including tag repetition counts.

    Parameters:
    - csv_filename (str): The name of the output CSV file.
    - image_data (list of dicts): A list of dictionaries containing image metadata.
"""
import sys
import os

# Get the absolute path to the root directory of your project
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))  # This will give the path to /Root
CODE_DIR = os.path.join(ROOT_DIR, 'Backend', 'Code')  # This points to /Root/Backend/Code

# Add the Backend/Code directory to sys.path
sys.path.append(CODE_DIR)

import csv
from collections import defaultdict

def compile_to_csv(csv_filename, image_data):
    # tag_counts = defaultdict(int)

    # # Count tag occurrences across all images
    # for img in image_data:
    #     for tag in img["tags"]:
    #         tag_counts[tag] += 1

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    OUTPUTS_DIR = os.path.join(BASE_DIR, 'Outputs')

    # Writing to CSV
    with open(os.path.join(OUTPUTS_DIR, "CSVs", csv_filename), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Writing header
        writer.writerow(["image_name", "tags_and_counts", "is_decorative", "is_link", "is_infographic"])
        
        # Writing rows
        for img in image_data:
            tags_with_counts = [f"{tag}" for tag in img["tags"]] # ({tag_counts[tag]})
            writer.writerow([
                img["image_name"], 
                ", ".join(tags_with_counts),  # Tags with counts formatted as "tag (count)"
                img["is_decorative"], 
                img["is_link"], 
                img["is_infographic"]
            ])

    print(f"CSV file '{csv_filename}' has been created successfully.")

# Example usage
# if __name__ == "__main__":
#     sample_data = [
#         {"image_name": "sunset.jpg", "tags": ["nature", "sunset", "sky"], "is_decorative": False, "is_link": False, "is_infographic": False},
#         {"image_name": "chart.png", "tags": ["data", "infographic", "business"], "is_decorative": False, "is_link": False, "is_infographic": True},
#         {"image_name": "logo.svg", "tags": ["branding", "company"], "is_decorative": True, "is_link": True, "is_infographic": False},
#         {"image_name": "forest.jpg", "tags": ["nature", "trees", "sky"], "is_decorative": False, "is_link": False, "is_infographic": False},
#     ]

#     save_image_metadata("image_metadata.csv", sample_data)

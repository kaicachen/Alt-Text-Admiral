from create_caption import *
import csv

def run_tests():
    input_data = []

    # Open and read the CSV file
    with open("test_inputs.csv", mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        next(reader)

        # Convert reader object to a list or iterate over rows
        for row in reader:
            input_data.append(row)

    with open("test_outputs.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write a header row (optional)
        writer.writerow(["image_loc", "generated_output"])
        
        for URL, image, text in input_data:
            writer.writerow([
                image,
                create_caption(image, text, URL=bool(int(URL)))
            ])


if __name__ == "__main__":
    run_tests()
from create_caption import create_caption
from web_scraper import scrape
from csv_to_pdf import create_pdf
import multiprocessing
import csv
import time

# Takes in split list of images and text from main function and returns them captioned with run time
def _multiprocess_caption(site_data, process_number, return_values):
    processed_images = []
    start_time = time.time()
    for image, text in site_data:
        processed_images.append(
            image,
            create_caption(image, text, URL=True)
        )
    end_time = time.time()

    return_values[process_number] = (processed_images, end_time - start_time)

# Captions entire site with a default number of threads of 16
def caption_site(url, output_name='site', pool=16):
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

    # PLACEHOLDER SO EXISTING CODE ISN'T BROKEN
    if True:
        return

    sublistSize  = len(site_data) // pool                 # number of images per multiprocessor list
    splitSiteData = []                                              # creates list that will store subsets of the possible keys for multiprocessing
    processList   = []                                              # creates list that will store the process references
    return_values = multiprocessing.Manager().dict()                # initialized shared dictionary for return values

    # startTime = time.perf_counter()                                 # records the start time of the iteration
    for i in range(pool):                                           # iterates over the number of processes to split
        splitSiteData.append([])                                         # appends a new list to store each process' site data
        for j in range(sublistSize):                                    # iterates over the set size of the sublist
            splitSiteData[i].append(next(iter(site_data)))                # appends the next value of the itertools iterator

    for i in range(len(splitSiteData)):                              # iterates through the split key lists
        processList.append(multiprocessing.Process(target=_multiprocess_caption, args=(splitSiteData[i], i, return_values)))
                                                                        # appends process reference calling tryKeys with each possibleKey sublist
        processList[i].start()                                          # starts the process

    for process in processList:                                     # iterates through the processes
        process.join()                                                  # joins them to end the processes

    processList.clear()                                             # clears the process references

    with open(f"{output_name}.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write a header row (optional)
        writer.writerow(["image_link", "generated_output"])
    
        captioned_images = []
        run_times = []

        for i in return_values:
            captioned_images.extend(return_values[i][0])
            run_times.extend(return_values[i][1])

        for image, text in captioned_images:
            writer.writerow([
                image,
                text
            ])

        writer.writerow("RUN_TIMES", run_times)

        # endTime = time.perf_counter()                                   # records the end time of the iteration
        # print(f"iteration: {i} took {endTime - startTime} seconds")     # print that the iteration completed and display the time it took

if __name__ == "__main__":
    start_time = time.time()
    
    output_name = "ku_union"
    site_url = "https://union.ku.edu"
    caption_site(site_url, output_name=output_name)
    create_pdf(output_name)
    
    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")

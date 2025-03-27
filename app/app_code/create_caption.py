import os
import hashlib
import sqlite3
from image_processing import *
from text_processing import *
from sentence_generator import *

def mergeTags(entities):  # Function to merge tags
    
    for category in entities:  # Iterate through all tags to check for words starting with "##"
        fixedTags = []  # Create an empty array to fix all of the tags for the category, resets for each category
        temp_name = ""  # Stores the tag that we are merging, will get added to fixedTags when merged

        for name in entities[category]:
            if name.startswith("##"):  # If "##" is at the start, we need to combine it with the previous name
                temp_name += name[2:]  # Grab the slice of everything after '##' and append it to the previous tag
            else:
                if temp_name:  # The temp name is the whole word and no more merging needs to be done
                    fixedTags.append(temp_name)  # Save the previous merged name
                temp_name = name  # Move on to the next name

        if temp_name:  # Add the last processed name, this happens if the last word needs to be merged
            fixedTags.append(temp_name)

        entities[category] = fixedTags  # Makes the category the new fixed tags
    return entities  # Returns the entire entities dictionary


def create_caption(image_path, text, URL=False):
    # Open cache database
    cache_db = sqlite3.connect(os.path.join("app", "app_code", "cached_results.db"))
    cache_db_cursor = cache_db.cursor()

    # Ensure the table exists
    cache_db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS cached_results (
            hash VARCHAR(255) PRIMARY KEY,
            alt_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
                            """)
    
    # Compute hash to see if alt text has already been generated
    hash = hashlib.sha256(str((image_path, text)).encode())
    cache_db_cursor.execute("SELECT alt_text FROM cached_results WHERE hash=?", (hash.hexdigest(),))
    db_fetch = cache_db_cursor.fetchone()

    # Return previously generated alt text
    if len(db_fetch) != 0:
        cache_db.close()
        return db_fetch[0]

    # Create image processor object
    URL = image_path.startswith("http") or image_path.startswith("https")
    image_processor = ImageProcessor(image_path, URL=URL)  # Instantiate an Image Processor Class
    
    # Create caption and find objects
    caption = image_processor.generate_caption_with_blip()  # Generate caption through Salesforce Blip captioning
    detected_objects = image_processor.find_image_objects()  # Extract tags from image (image_processing.py)

    # Skip if no information is extracted from the image, likely due to an error
    if caption == "" and detected_objects == {}:
        return ""

    # Extract text entities
    entities = extract_entities(text)   # Extracts tags from text (text_processing.py)
    entities = mergeTags(entities)  # Fixes issue where some words would be prepended by "##"
    # Example: [Leb, ##ron James]  -> [Lebron James]

    tags = ""  # Create tags variable to store all gathered tags

    for object, quantity in detected_objects.items():  # Add image tags to tag string
        # cur_string = f"{object} {quantity}, "
        cur_string = f"{object}, "
        tags += cur_string
    
    # Add text tags to tag string
    for person in entities["People"]:  # Add all people
        tags += f"{person}, "
    for person in entities["Organizations"]: # Add all organizations
        tags += f"{person}, "

    # We just do this for now because the OTHER category usually isn't important for alt text

    # for tag, tag_list in entities.items():
    #     cur_string = ""
    #     for entity in tag_list:
    #         cur_string += f"{entity}, "
    #     tags += cur_string

    # for tag, tag_list in entities.items():
    #     cur_string = f"{tag}: ("
    #     for entity in tag_list:
    #         cur_string += f"{entity}, "
    #     cur_string += ") "
    #     tags += cur_string

    print(f"Caption: {caption}\nTags: {tags}")
    alt_text = generate_sentence(caption, tags) # Pass the created caption and extracted tags to our alt-text generator

    # Store in database
    cache_db_cursor.execute("INSERT INTO cached_results (hash, alt_text) VALUES (?, ?)", (hash.hexdigest(), alt_text))

    # NOT WORKING FOR NOW BUT NEEDED SO DB IS PURGED WHEN TOO LARGE
    # # Delete the oldest rows if count exceeds 500
    # cache_db_cursor.execute("""
    #     DELETE FROM cached_results WHERE timestamp IN (
    #         SELECT timestamp FROM cached_results ORDER BY timestamp ASC LIMIT (SELECT COUNT(*) - 500 FROM cached_results)
    #         )
    #                         """)
    
    cache_db.commit()
    cache_db.close()

    return alt_text


if __name__ == "__main__":
    # image_path = "images/basketball.jpg"
    # text = "Elon Musk is the CEO of Tesla and SpaceX. Steve Jobs was the co-founder of Apple and ate an apple every day."

    '''
    Source for the following image and text are https://www.espn.com/nba/story/_/id/43833377/a-rivalry-bromance-failed-reunion-steph-kd-lebron-reunite-all-star-weekend
    '''

    image_path = "basketball.jpg"
    text = "No. 17 Kansas defeated Colorado 71-59 on Tuesday night at Allen Fieldhouse. The Jayhawks (17-7, 8-5 Big 12) won their first of two matchups between the sides. A big reason for that was KU’s defense — a calling card for Bill Self teams. The Jayhawks stepped up on that end in pivotal moments, doing so in a new look of sorts on Tuesday."

    caption = create_caption(os.path.join("app", "app_code", "inputs", "Images", image_path), text)
    print(f"Caption: {caption}")
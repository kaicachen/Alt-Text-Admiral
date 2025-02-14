from image_processing import ImageProcessor
from text_processing import *
from sentence_generator import *

def merge_subwords(entities):
    
    for category in entities:
        merged_people = []
        temp_name = ""

        for name in entities[category]:
            if name.startswith("##"):
                temp_name += name[2:]  # Remove "##" and append
            else:
                if temp_name:
                    merged_people.append(temp_name)  # Save the previous merged name
                temp_name = name  # Start a new name

        if temp_name:  # Add the last processed name
            merged_people.append(temp_name)

        entities[category] = merged_people
    return entities


def create_caption(image_path, text):
    image_processor = ImageProcessor(image_path)
    caption = image_processor.generate_caption_with_blip()
    detected_objects = image_processor.find_image_objects()

    entities = extract_entities(text)
    entities = merge_subwords(entities)
    

    tags = ""

    for object, quantity in detected_objects.items():
        # cur_string = f"{object} {quantity}, "
        cur_string = f"{object}, "
        tags += cur_string

    for person in entities["People"]:
        tags += f"{person}, "
    for person in entities["Organizations"]:
        tags += f"{person}, "

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
    return generate_sentence(caption, tags)

if __name__ == "__main__":
    # image_path = "images/basketball.jpg"
    # text = "Elon Musk is the CEO of Tesla and SpaceX. Steve Jobs was the co-founder of Apple and ate an apple every day."

    '''
    Source for the following image and text are https://www.espn.com/nba/story/_/id/43833377/a-rivalry-bromance-failed-reunion-steph-kd-lebron-reunite-all-star-weekend
    '''

    image_path = "images/basketball.jpg"
    text = "No. 17 Kansas defeated Colorado 71-59 on Tuesday night at Allen Fieldhouse. The Jayhawks (17-7, 8-5 Big 12) won their first of two matchups between the sides. A big reason for that was KU’s defense — a calling card for Bill Self teams. The Jayhawks stepped up on that end in pivotal moments, doing so in a new look of sorts on Tuesday."

    caption = create_caption(image_path, text)
    print(f"Caption: {caption}")
from detr import *
from entity_recognition import *
from tag_synthesizer import *

def create_caption(image_path, text):
    detected_objects = find_image_objects(image_path)

    entities = extract_entities(text)

    all_info = ""

    for object, quantity in detected_objects.items():
        cur_string = f"{object} {quantity}, "
        all_info += cur_string

    for tag, tag_list in entities.items():
        cur_string = f"{tag}: ("
        for entity in tag_list:
            cur_string += f"{entity}, "
        cur_string += ")"
        all_info += cur_string

    print(all_info)
    return generate_sentence(all_info)

if __name__ == "__main__":
    image_path = "images/KU-Honors-Concrete-canoe.png"
    text = "Jayhawks celebrate at The University of Kansas"
    caption = create_caption(image_path, text)
    print(f"Caption: {caption}")
from image_processing import ImageProcessor
from text_processing import *
from sentence_generator import *

def create_caption(image_path, text):
    image_processor = ImageProcessor(image_path)
    caption = image_processor.generate_caption_with_blip()
    detected_objects = image_processor.find_image_objects()

    entities = extract_entities(text)

    tags = ""

    for object, quantity in detected_objects.items():
        # cur_string = f"{object} {quantity}, "
        cur_string = f"{object}, "
        tags += cur_string

    for person in entities["People"]:
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

    image_path = "images/sport guy.jpg"
    text = "IN THE MOMENTS after LeBron James topped Stephen Curry's 37 points with an ageless 42-point, 17-rebound effort to lift the Los Angeles Lakers to a 120-112 win in their latest duel, the Golden State Warriors star had to hear 'I Love L.A.' blare as he ran into the storied franchise's newest superstar."
    caption = create_caption(image_path, text)
    print(f"Caption: {caption}")
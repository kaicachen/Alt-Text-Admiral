from torch import no_grad, tensor
from requests import get
from time import sleep
from io import BytesIO
from PIL import Image


'''Class to handle all processing of a image, text tuple passed in'''
class DataProcessor:
    def __init__(self, image_loc, image_type, text, gemini_model, detr_model, detr_processor, device, URL=True):
        # Saves image path for future output
        self.loc = image_loc

        # Store image type and text
        self.image_type = int(image_type)
        self.text = text

        # Store models and processor
        self._gemini_model = gemini_model
        self._detr_model = detr_model
        self._detr_processor = detr_processor
        self._device = device

        # Location is a URL
        if URL:
            try:
                response = get(image_loc)
                self.image = Image.open(BytesIO(response.content))

            except:
                self.image = None
                print(f"ERROR LOADING IMAGE {self.loc}")
                return
        
        # Location is a local file path
        else:
            self.image = Image.open(image_loc)

        # Convert image to RGB
        self.image = self.image.convert("RGB")


    '''Generates a generic caption of the image'''
    def _generate_image_caption(self):
        # Check if generation has completed
        not_generated = True
        sleep_length  = 1

        # Keeps attempting until completion or manual time out
        while(not_generated):
            try:
                caption = self._gemini_model.generate_content([self.image,"Describe this image in a detailed caption. "]).text
                not_generated = False
                return caption
            
            except Exception as e:
                # Wait before regenerating and increase sleep time incase of repeat error
                if "You exceeded your current quota" in str(e) and sleep_length < 10:
                    print(f"ResourceExhausted occured, sleeping for {sleep_length} second then regenerating")
                    sleep(sleep_length)
                    sleep_length +=1

                else:
                    raise e


    '''Generates a list of objects detected in the image'''
    def _generate_image_objects(self):
        # Run processor
        try:
            inputs = self._detr_processor(images=self.image, return_tensors="pt").to(self._device)

        except Exception as e:
            print(f"FAILED TO PROCESS {self.loc} with Exception: {e}")
            return {}

        # Perform inference
        with no_grad():
            outputs = self._detr_model(**inputs)

        # Process results
        target_sizes = tensor([self.image.size[::-1]])  # (height, width)
        results = self._detr_processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]

        # Prepare metadata storage
        detected_objects = {}

        # Save objects with at least 70% confidence
        for score, label in zip(results["scores"], results["labels"]):
            if score >= .7:
                obj_name = self._detr_model.config.id2label[label.item()]
                detected_objects[obj_name] = detected_objects.get(obj_name, 0) + 1

        # Convert detected objects to list format for CSV
        tags_list = [f"{tag} ({count})" for tag, count in detected_objects.items()]

        return detected_objects
    
    '''Generates alt-text based on the image caption and tags with the specified type'''
    def _generate_alt_text(self, image_caption, image_objects):
        # Check if generation has completed
        not_generated = True
        sleep_length = 1

        caption_input = ""
        text_input = ""
        objects_input = ""

        # Does not include the following items in the prompt if they do not exist
        if image_caption:
            caption_input = f"- **Caption:** {image_caption}\n"

        if self.text:
            text_input = f"- **Surrounding Text:** {self.text}\n"

        if image_objects:
            objects_input = f"- **Tags:** {image_objects}\n"

        # Keeps attempting until completion or manual time out
        while(not_generated):
            try:
                response = self._gemini_model.generate_content(
                    f"You are generating **ADA-compliant** alt text based on the given **{(caption_input and "caption")}, {(text_input and "surrounding text")}, and {(objects_input and "tags")}**.\n\n"
                    f"### **Input Data:**\n"
                    f"{caption_input}"
                    f"{text_input}"
                    f"{objects_input}"

                    f"\n"
                    
                    f"### **Guidelines for Alt Text:**\n"
                    f"1. **Be concise:** Keep the alt text under **150 characters**.\n"
                    f"2. **Be descriptive and meaningful:** Focus on the **essential content** of the image, rather than just its appearance.\n"
                    f"3. **Avoid redundancy:** Do **not** repeat details already provided in the surrounding text.\n"
                    f"4. **Use natural language:** Write in a **clear, fluent, and grammatically correct** way.\n"
                    f"5. **Maintain relevance:** Your response **must** include details from the caption, text, and tags.\n"
                    f"6. **Do NOT** generate generic alt text. The description should be unique to the image.\n\n"
                    
                    f"### **Examples:**\n"
                    f"**Good Alt Text:** 'A person in a wheelchair crossing the street on a sunny day.' (Concise, relevant, and informative)\n"
                    f"**Bad Alt Text:** 'An image of a person outside.' (Too vague, lacks key details)\n\n"
                    
                    f"Now, generate **one** alt text description following these rules."
                    )
                not_generated = False

            except Exception as e:
                # Wait before regenerating and increase sleep time incase of repeat error
                if "You exceeded your current quota" in str(e) and sleep_length < 10:
                    print(f"ResourceExhausted occured, sleeping for {sleep_length} second then regenerating")
                    sleep(sleep_length)
                    sleep_length +=1

                else:
                    raise e

        return response.text
    

    '''Fully process the inputted data and return the alt-text'''
    def process_data(self):
        if self.image is None or self.image_type == 2:
            return " "
        
        image_caption = self._generate_image_caption()
        image_objects = self._generate_image_objects()
        
        # Early exit if no data extracted from the image
        if image_caption == "" and image_objects == {}:
            return ""
        
        image_objects_str = ""

        # Convert image objects to a string
        for object, quantity in image_objects.items():
            cur_string = f"{object}, "
            image_objects_str += cur_string

        # Return alt-text
        return self._generate_alt_text(image_caption, image_objects_str)


if __name__ == "__main__":
    # Load and preprocess the image
    image_path = "images/lebron.jpg"
    data_processor = DataProcessor(image_path, 0, "", URL=False)
    detected_objects = data_processor._generate_image_objects()
    caption = data_processor._generate_image_caption()
    alt_text = data_processor.process_data
    print(f"Caption: ({caption})\nObjects: ({detected_objects})\nAlt-Text: ({alt_text})")
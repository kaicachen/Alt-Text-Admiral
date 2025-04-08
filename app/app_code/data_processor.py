from transformers import DetrImageProcessor, DetrForObjectDetection, logging
import google.generativeai as genai
from io import BytesIO
from PIL import Image
import requests
import torch
import time


'''Class to handle all processing of a image, text tuple passed in'''
class DataProcessor:
    def __init__(self, image_loc, image_type, text, URL=True):
        # Saves image path for future output
        self.loc = image_loc
        
        # Location is a URL
        if URL:
            try:
                response = requests.get(image_loc)
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

        # Store image type and text
        self.image_type = image_type
        self.text = text

        # Reduce console output
        logging.set_verbosity_error()


    '''Generates a generic caption of the image'''
    def _generate_image_caption(self):
        # Loads Gemini model
        model = genai.GenerativeModel("gemini-1.5-flash")
        API_KEY = self._retrieveKey()
        genai.configure(api_key=API_KEY)
        time.sleep(1)

        # Check if generation has completed
        not_generated = True
        sleep_length  = 1

        # Keeps attempting until completion or manual time out
        while(not_generated):
            try:
                caption = model.generate_content([self.image,"Describe this image in a detailed caption. "]).text
                not_generated = False
                return
            
            except Exception as e:
                # Wait before regenerating and increase sleep time incase of repeat error
                if "You exceeded your current quota" in str(e) and sleep_length < 10:
                    print(f"ResourceExhausted occured, sleeping for {sleep_length} second then regenerating")
                    time.sleep(sleep_length)
                    sleep_length +=1

                else:
                    raise e


    '''Generates a list of objects detected in the image'''
    def _generate_image_objects(self):
        # Load the DETR model and processor
        device = "cuda" if torch.cuda.is_available() else "cpu"  # Sets active device as GPU if available, otherwise it runs on the CPU
        print(torch.cuda.device_count())
        processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(device)

        # Run processor
        try:
            inputs = processor(images=self.image, return_tensors="pt").to(device)

        except:
            print(f"FAILED TO PROCESS {self.loc}")
            return {}

        # Perform inference
        with torch.no_grad():
            outputs = model(**inputs)

        # Process results
        target_sizes = torch.tensor([self.image.size[::-1]])  # (height, width)
        results = processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]

        # Prepare metadata storage
        detected_objects = {}

        # Save objects with at least 70% confidence
        for score, label in zip(results["scores"], results["labels"]):
            if score >= .7:
                obj_name = model.config.id2label[label.item()]
                detected_objects[obj_name] = detected_objects.get(obj_name, 0) + 1

        # Convert detected objects to list format for CSV
        tags_list = [f"{tag} ({count})" for tag, count in detected_objects.items()]

        return detected_objects
    
    '''Generates alt-text based on the image caption and tags with the specified type'''
    def _generate_image_caption(self, image_caption, image_objects):
        # Loads Gemini model
        API_KEY = self._retrieveKey()
        genai.configure(api_key=API_KEY)
        model=genai.GenerativeModel("gemini-1.5-flash")

        # Check if generation has completed
        not_generated = True
        sleep_length = 1

        # Keeps attempting until completion or manual time out
        while(not_generated):
            try:
                response = model.generate_content(
                    f"You are generating **ADA-compliant** alt text based on the given **caption, surrounding text, and tags**.\n\n"
                    f"### **Input Data:**\n"
                    f"- **Caption:** {image_caption}\n"
                    f"- **Surrounding Text:** {self.text}\n"
                    f"- **Tags:** {image_objects}\n\n"
                    
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
                    time.sleep(sleep_length)
                    sleep_length +=1

                else:
                    raise e

        return response.text
    

    '''Retrieve Gemini API key'''
    def _retrieveKey():
        file = open("key.txt","r")
        return file.readline()
    

    '''Fully process the inputted data and return the alt-text'''
    def process_data(self):
        image_caption = self._generate_image_caption()
        image_objects = self._generate_image_objects()
        
        # Early exit if no data extracted from the image
        if image_caption == "" and image_objects == {}:
            return ""
        
        # Convert image objects to a string
        for object, quantity in image_objects.items():
            cur_string = f"{object}, "
            image_objects_str += cur_string

        # Return alt-text
        return self._generate_image_caption(image_caption, image_objects_str)


if __name__ == "__main__":
    # Load and preprocess the image
    image_path = "images/lebron.jpg"
    data_processor = DataProcessor(image_path, 0, "", URL=False)
    detected_objects = data_processor._generate_image_objects()
    caption = data_processor._generate_image_caption()
    alt_text = data_processor.process_data
    print(f"Caption: ({caption})\nObjects: ({detected_objects})\nAlt-Text: ({alt_text})")
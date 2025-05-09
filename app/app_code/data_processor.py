'''
Author: Aiden Patel
Created:
Last modified:

Description:
This file contains the DataProcessor class, which is responsible for processing images and generating alt-text using the Gemini model.
Inputs: 
    image_loc: A url or local file path to the image
    image_type: Type of the image (0 for informative, 1 for link, 2 for decorative, 3 for not included)
    text: Text surrounding the image for context
    href: href if the img has some
    gemini_client: The Gemini client used to access the Gemini model
    detr_model: The DETR model used for object detection in images (DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(self._device))from site processor
    detr_processor: The detr model used to process images for the object detection model. (DetrImageProcessor.from_pretrained("facebook/detr-resnet-50"))from site processor
    device: Whether to use the GPU or CPU for processing (self._device = "cuda" if cuda.is_available() else "cpu") from site processor
    URL=True: Whether to treat the image_loc as a URL or a local file path, default is Treat like a url
    training = False: Whether to collect data for training or not, default is False, do not collect data
    tuned = True: Whether to use the tuned model or not, default is True, use the tuned model
Outputs:
'''


from requests import get, exceptions
from torch import no_grad, tensor
from bs4 import BeautifulSoup
from time import sleep
from io import BytesIO
from PIL import Image
from .training import Trainer
from google import genai
from transformers import DetrImageProcessor, DetrForObjectDetection


'''Class to handle all processing of a image, text tuple passed in'''
class DataProcessor:
    def __init__(self, image_loc:str|BytesIO, image_type:int, text:str, href:str, gemini_client:genai.Client, detr_model:DetrForObjectDetection, detr_processor:DetrImageProcessor, device:str, URL=True, training = True, tuned = True):
        # Saves image path for future output
        self.loc = image_loc

        # Store image type, text, and href
        self.image_type = int(image_type)
        self.text = text
        self.href = href

        #Used to access client to use all models (TODO, move this to site processor)
        self._gemini_client = gemini_client

        #determine if the tuned model should be used
        self._tuned = tuned

        # Store models and processor
        self._gemini_model_name = "gemini-1.5-flash"
        self._detr_model = detr_model
        self._detr_processor = detr_processor
        self._device = device
        

        #true if data is saved for training, false otherwise
        if training:
            self._trainer = Trainer("gemini-1.5-flash")
            self._training = True
        else:
            self._trainer = None
            self._training = False

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
    def _generate_image_caption(self) -> str:
        # Check if generation has completed
        not_generated = True
        sleep_length  = 1

        # Keeps attempting until completion or manual time out
        while(not_generated):
            try:
                caption = self._gemini_client.models.generate_content(
                    model=self._gemini_model_name,
                    contents=[self.image,"Describe this image in a detailed caption. "]
                )
                not_generated = False
                return caption.text
            
            except Exception as e:
                # Wait before regenerating and increase sleep time incase of repeat error
                if "You exceeded your current quota" in str(e) and sleep_length < 10:
                    print(f"ResourceExhausted occured, sleeping for {sleep_length} second then regenerating")
                    sleep(sleep_length)
                    sleep_length +=1

                else:
                    raise e


    '''Generates a list of objects detected in the image'''
    def _generate_image_objects(self) -> dict:
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

        return detected_objects
    

    '''Generates alt-text based on the image caption and tags with the specified type'''
    def _generate_alt_text(self, image_caption:str, image_objects:str) -> str:
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

        prompt = (
                    f"You are generating **ADA-compliant** alt text based on the given **{(caption_input and 'caption')}, {(text_input and 'surrounding text')}, and {(objects_input and 'tags')}**.\n\n"
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

        # Keeps attempting until completion or manual time out
        while(not_generated):
            try:
                if self._tuned:
                    response = self._gemini_client.models.generate_content(
                        model="tunedModels/test-tuned-model-icran2mmdiyb",
                        contents= prompt
                    )
                else:
                    response = self._gemini_client.models.generate_content(
                        model=self._gemini_model_name,
                        contents= prompt
                    )
                if self._training:
                    self._trainer.add_to_dataset(self.loc, prompt, image_type="informative")
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
    
    
    '''Gets the H1 text from a given link if it exists'''
    def _get_link_title(self)-> str|None:
        try:
            # Gets a response from the URL and raises an error for failure
            response = get(self.href)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            h1 = soup.find('h1')
            if h1:
                return h1.get_text(strip=True)
            else:
                return None
            
        # Error in getting a response from the URL
        except exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    '''Generates a description of the destination link attached to the image'''
    def _generate_link_description(self) -> str|None:
        # Early exit if no href scraped
        if not self.href:
            return "NO HREF FOUND"
        
        # Return site title if found
        link_title = self._get_link_title()
        if link_title:
            return f"Links to: {link_title}"
        
        # Check if generation is complete
        not_generated = True
        sleep_length = 1

        prompt = (
                    f"You are generating **ADA-compliant** alt text describing the destination of the following link**.\n\n"
                    f"### **Input Data:**\n"
                    f"{self.href}"

                    f"\n"
                    
                    f"### **Guidelines for Alt Text:**\n"
                    f"1. **Be concise:** Keep the alt text under **150 characters**.\n"
                    f"2. **Be descriptive and meaningful:** Focus on the **basic content** of the website, rather than the details.\n"
                    f"4. **Use natural language:** Write in a **clear, fluent, and grammatically correct** way.\n"
                    f"5. **Maintain relevance:** Your response **must** include information of the website's primary focus.\n"
                    f"6. **Do NOT** generate generic alt text. The description should be unique to the website.\n\n"
                    
                    f"### **Examples:**\n"
                    f"**Good Alt Text:** 'A view of a user's shopping cart.' (Concise, relevant, and informative)\n"
                    f"**Bad Alt Text:** 'A link to a page.' (Too vague, lacks key details)\n\n"
                    
                    f"Now, generate **one** alt text description following these rules."
                    )

        # Prompt Gemini to describe the site
        while(not_generated):
            try:
                if False: #self._tuned: #Block off the branch as no tuned model yet #TODO: make link datset, make tuned model, use tuned model
                    response = self._gemini_client.models.generate_content(
                        model="tunedModels/test-tuned-model-icran2mmdiyb",#TODO: change tuned model to be the one trained for links
                        contents= prompt
                    )
                else:
                    response = self._gemini_client.models.generate_content(
                        model=self._gemini_model_name,
                        contents= prompt
                    )
                if self._training:
                    self._trainer.add_to_dataset(self.loc, prompt, image_type="link")

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
    def process_data(self) -> str:
        # Return empty tag if no image is present or if "decorative" type
        if self.image is None or self.image_type == 2:
            return " "
        
        if self.image_type == 1:
            return self._generate_link_description()
        
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
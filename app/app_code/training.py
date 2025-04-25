'''
Author: John
Created: 3/10/2025
Last modified: 4/13/2025

Description:
Code to train the model. specifically gemini
'''

from requests import get as requests_get
from requests.exceptions import RequestException
from io import BytesIO

from PIL.ImageOps import contain
from PIL.Image import LANCZOS,open as pil_open
from PIL.ImageTk import PhotoImage

from tkinter.scrolledtext import ScrolledText
from tkinter import Tk, WORD,INSERT,Label,Text, Event, END

from os.path import join
from os import getenv
from json import load as json_load, dump as json_dump, JSONDecodeError


from google import genai
from google.genai.types import CreateTuningJobConfig, TuningDataset, TuningExample

from time import sleep
from PIL import Image
from requests import get
from torch import no_grad, cuda, tensor
from transformers import DetrImageProcessor, DetrForObjectDetection, logging
logging.set_verbosity_error()

from web_scraper import WebScraper #import the webscraper class from web_scraper.py


class Trainer:
    def __init__(self, model_name:str):
        self._model_name = model_name[7:] #reomove the "model\" because it is not a vlid file name
        self._full_model_name = model_name #save the full model name for later use  
        self._client = genai.Client(api_key=getenv('GEMINI_API_KEY'))
        # Sets active device as GPU if available, otherwise it runs on the CPU
        self._device = "cuda" if cuda.is_available() else "cpu"

        self._detr_processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        self._detr_model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(self._device)
        self.image = None
        self._image_loc = None
    
    '''complete the dataset by creating the proper output given a prompt and image.'''
    def complete_dataset(self, dataset_filename:str)->None: #where dataset is the name of the json file

        updated_data = []  # Create an empty list to store the updated data
        
        #open the json file as data.
        try: 
            with open(join("app", "app_code", "outputs", "training_json","unprocessed", dataset_filename), 'r') as file:  # Open the JSON file for reading
                data = json_load(file)  # Load the JSON data into a variable
        except FileNotFoundError:
            print(f"Error: File not found: {dataset_filename}")
            return  # Exit the function if the file is not found 
        except JSONDecodeError:
            print(f"Error: Invalid JSON format in: {dataset_filename}")
            return
        except Exception as e:  # Catch any other exceptions that may occur
            print(f"Error: {e}")
            return
        

        for entry in data:
            url = entry['link']  # Extract the image URL from the entry
            prompt = entry['input']  # Extract the prompt from the entry


            #now i need to show user the prompt and image and get output. Now that i think about it, the json doesnt need out, im just gonna make a new file.
            try:
                response = requests_get(url)
            except RequestException as e:
                print(f"Error fetching image from {url}: {e}")
                continue  # Skip to the next entry if there's an error fetching the image

            

            root = Tk()  # Create a Tkinter window 
            root.geometry("1000x800")  # Set the window size
            root.title("Alt-Text dataset")  # Set the window title
            
            prompt_area = ScrolledText(root, wrap=WORD, width=50, height=10)  # Create a scrolled text area for the prompt
            prompt_area.insert(INSERT, prompt)  # Insert the prompt text into the scrolled text area
            prompt_area.pack()  # Pack the label into the window
            
            img = pil_open(BytesIO(response.content)) #open the image from the url
            img = contain(img, (600, 800), LANCZOS)  # Resize the image to fit the window
            tkimg = PhotoImage(img)  # Convert the image to a Tkinter-compatible format
            image_label = Label(root, image=tkimg)  # Create a label to display the image
            image_label.pack()  # Pack the label into the window

            getter = Text(root, width=50, height=10)  # Create a label to display the prompt
            getter.insert(INSERT, "Enter Alt-Text for the image above:")  # Insert the prompt text into the label
            getter.pack()  # Pack the label into the window

            def delete_default_text(event:Event): ## This function auto deletes the default text when the user clicks on the text area
                event.widget.delete("1.0", END)
                # Unbind so that the default text is not deleted on subsequent focus
                event.widget.unbind("<FocusIn>", on_focus_in) 

            on_focus_in = getter.bind("<FocusIn>", delete_default_text)  # Clear the text area when it gains focus
            root.bind("<Return>", lambda event: root.quit())  # Bind the Enter key to close the window
            root.mainloop()  # Start the Tkinter event loop to display the image

            print(getter.get("1.0", END))  # Print the user input

            output = getter.get("1.0", END)  # Get user input for alt text
            
            #add output to training data
            updated_data.append({"text_input":prompt, "output": output})  # Add the prompt and user input to the updated data list
            root.destroy()  # Destroy the Tkinter window after getting user input
        
        #once thats done, save to new json file
        new_file_dir = join("app", "app_code", "outputs", "training_json", "processed", f"processed_{dataset_filename}")  # Append the subdirectory to the file path
        with open(new_file_dir, 'w') as file:  # Save the updated data to a new JSON file
            json_dump(updated_data, file, indent=4)  # Write the updated data to the file in JSON format
            
        print(f"Updated dataset saved as {new_file_dir}")  # Print the location of the saved file
    

    '''Add data to an unprocessed dataset'''
    def add_to_dataset(self, image_url:str, prompt:str, image_type:str = "") ->None: #used to make the dataset in a program for help.
        #add to the dataset into a jsonl file
        training_data = [{ #This is the data that will be added to the jsonl file
                "link" : f"{image_url}",
                "input": f"{prompt}"
            }]
        
        # append.jsonl to the filename
        jsonl_filename = f"{image_type}{self._model_name}.jsonl"
        
        # open the json, convert to list, append new data, resave
        try:
            with open(join("app", "app_code", "outputs", "training_json","unprocessed", f"{jsonl_filename}"), "r", encoding="utf-8") as file:
                data = json_load(file) # Load existing data from the JSONL file into a list
        except FileNotFoundError:#if the file does not exist, create empty list
            print(f"Error: File not found: {jsonl_filename}\nNew file will be created.")
            data = []
        except JSONDecodeError: #if the file is not a valid json, create empty list
            print(f"Error: Invalid JSON format in: {jsonl_filename}\nNew file will be created.")
            data = []
        
        data.append(training_data[0])  # Append the new data to the existing list

        # Save the updated data back to the JSONL file
        try:
            with open(join("app", "app_code", "outputs", "training_json","unprocessed", f"{jsonl_filename}"), "w", encoding="utf-8") as file:
                json_dump(data, file, ensure_ascii=False, indent=4)  # Write the updated data to the file in JSON format
            print(f"Dataset saved as {jsonl_filename}")
        except Exception as e: # on failure to save, print error message
            print(f"Error saving dataset: {e}")
    
    #function to create a tuned model using a dataset
    def create_gemini_model(self, dataset_filename:str)->None: #where dataset is the name of the json file
        #call the google create model thing to do the thing
        data = json_load(open(join("app", "app_code", "outputs", "training_json","processed", dataset_filename), 'r')) # Load the training data from the JSON file
        training_data = TuningDataset(
            examples=[TuningExample(
                text_input=entry.get("text_input"),  # Use the 'input' field from the JSON data
                output=entry.get("output")  # Use the 'output' field from the JSON data
            ) for entry in data
            ]
        )

        tuning_job = self._client.tunings.tune(#dummy hyperparameters, can do more testing when we have a bigger dataset
            base_model='models/gemini-1.5-flash-001-tuning',
            training_dataset=training_data,
            config=CreateTuningJobConfig(
                epoch_count= 5,
                batch_size=4,
                learning_rate=0.001,
                tuned_model_display_name="test tuned model"
            )
        )
        print(tuning_job.name)#for debugging purposes
    
    def check_tuning_job_status(self, job_id:str)->None:#check the status of the tuning job
        tuning_job = self._client.tunings.get(name=job_id)
        print(tuning_job)

    #TODO: make this function
    def update_gemini_model(dataset_filename:str): #where dataset is the name of the json file
        pass

#Current task, make a function to collect data from websites without going through all the generation steps.
    def collect_from_sites(self, file_name:str)->None: #where file_name is a file witha list of urls to collect from
        try:
            with open(join("app", "app_code", "inputs",  file_name), 'r') as file:  # Open the JSON file for reading
                data:list[str] = json_load(file)
        except FileNotFoundError:
            print(f"Error: File not found: {file_name}")
            return
        #we'll just assume I made a json file with list[str] of urls

        for url in data:# for each url, call webscraper, do dummy annotations, generate prompt, and add to dataset
            try:
                webscraper = WebScraper(url)  # Create a WebScraper object with the URL
                _, site_data=  webscraper.scrape_site()  # Call the scrape_site method to get the image and text data
            except Exception as e:
                print(f"Error scraping site {url}: {e}")
                continue
        
        for img_url, surrounding_text, href in site_data:  #Iterate through the image and text data
            # Location is a URL
            try:
                response = get(img_url)
                self.image = Image.open(BytesIO(response.content))
                self._image_loc = img_url  # Save the image location for later use
            except:
                try: 
                    self.image = Image.open(img_url)
                    self._image_loc = img_url
                except:
                    self.image = None
                    print(f"ERROR LOADING IMAGE {img_url}")
                    continue  # Skip to the next entry if there's an error fetching the image
            self.image = self.image.convert("RGB")
            
            image_caption = self._generate_image_caption()  # Generate the image caption
            image_objects = self._generate_image_objects()  # Generate the image objects

            # Early exit if no data extracted from the image
            if image_caption == "" and image_objects == {}:
                continue  # Skip to the next entry if no data is extracted from the image (#### Maybe not? but for now yes)
            
            #now process the objects.
            image_objects_str = ""

            # Convert image objects to a string
            for object, _ in image_objects.items():
                cur_string = f"{object}, "
                image_objects_str += cur_string
            
            #now make the prompt
            prompt = self._prompt_generator(image_caption, image_objects_str, surrounding_text)
            
            #I have the prompt and image_url, now aadd to the dataset.
            self.add_to_dataset(img_url, prompt, image_type="untyped_")  # Add the prompt and image URL to the dataset
        

    
    ### COPIED FROM DATA PROCESSOR, slightly modified
        '''Generates a generic caption of the image'''
    def _generate_image_caption(self) -> str|None:
        
        not_generated = True
        sleep_length  = 1
        # Keeps attempting until completion or manual time out
        while(not_generated):
            try:
                caption = self._client.models.generate_content(
                    model=self._full_model_name,
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
    ### COPIED FROM DATA PROCESSOR, slightly modified
    '''Generates a list of objects detected in the image'''
    def _generate_image_objects(self) -> dict:
        # Run processor
        try:
            inputs = self._detr_processor(images=self.image, return_tensors="pt").to(self._device)

        except Exception as e:
            print(f"FAILED TO PROCESS {self._image_loc} with Exception: {e}")
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
    
    def _prompt_generator(self, image_caption:str, image_objects:str, surrounding_text:str) ->str:
        caption_input = ""
        text_input = ""
        objects_input = ""

        # Does not include the following items in the prompt if they do not exist
        if image_caption:
            caption_input = f"- **Caption:** {image_caption}\n"

        if surrounding_text:
            text_input = f"- **Surrounding Text:** {surrounding_text}\n"

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
        return prompt
        


if __name__ == "__main__":  # Used for testing purposes
    #create client with dummy name
    dummy = Trainer("models/gemini-1.5-flash")
    # #list all the tuned models
    # for model_info in dummy._client.tunings.list():
    #     print(model_info.name)
    dummy.complete_dataset("untyped_gemini-1.5-flash.jsonl")
    
    #dummy.collect_from_sites("websites.txt")
    # dummy.create_gemini_model("processed_informativegemini-1.5-flash.jsonl")
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


class Trainer:
    def __init__(self, model_name:str):
        self._model_name = model_name[7:] #reomove the "model\" because it is not a vlid file name
        self._full_model_name = model_name #save the full model name for later use  
        self._client = genai.Client(api_key=getenv('GEMINI_API_KEY'))
    
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


    def update_gemini_model(dataset_filename:str): #where dataset is the name of the json file
        pass



if __name__ == "__main__":  # Used for testing purposes
    #create client with dummy name
    dummy = Trainer("models/gemini-1.5-flash")
    #list all the tuned models
    for model_info in dummy._client.tunings.list():
        print(model_info.name)
    
    # dummy.create_gemini_model("processed_informativegemini-1.5-flash.jsonl")
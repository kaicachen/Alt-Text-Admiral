'''
Author: John
Created: 3/10/2025
Last modified: 3/10/2025

Description:
Code to train the model. test line
'''

import requests
from io import BytesIO
import tkinter as tk
from PIL import Image, ImageTk, ImageOps

from tkinter import scrolledtext

from os.path import join
from os import getenv
from json import load as json_load, dump as json_dump, JSONDecodeError


from google import genai
from google.genai import types
from google.genai.types import CreateTuningJobConfig, TuningDataset, TuningExample


class Trainer:
    def __init__(self, model_name:str):
        self._model_name = model_name[7:] #reomove the "model\" because it is not a vlid file name
        self._full_model_name = model_name #save the full model name for later use  
        self._client = genai.Client(api_key=getenv('GEMINI_API_KEY'))
        print(f"Trainer initialized with model name: {self._model_name}")  # Print the model name for debugging
    
    ### this is such a nightmare of a function.
    #complete the dataset by creating the proper output given a prompt and image.
    def complete_dataset(dataset_filename:str): #where dataset is the name of the json file

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
                response = requests.get(url)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching image from {url}: {e}")
                continue  # Skip to the next entry if there's an error fetching the image

            img = Image.open(BytesIO(response.content))

            root = tk.Tk()  # Create a Tkinter window 
            root.geometry("1000x800")  # Set the window size
            root.title("Alt-Text dataset")  # Set the window title

            outie = tk.StringVar()  # Create a StringVar to hold the user input
            outie.set("Enter the alt text for the image: ")  # Set the initial text for the entry field
            
            prompt_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=10)  # Create a scrolled text area for the prompt
            prompt_area.insert(tk.INSERT, prompt)  # Insert the prompt text into the scrolled text area
            prompt_area.pack()  # Pack the label into the window

            #img = img.thumbnail((400, 400), Image.LANCZOS)  # Resize the image to fit the window
            img = ImageOps.contain(img, (600, 800), Image.LANCZOS)  # Resize the image to fit the window
            tkimg = ImageTk.PhotoImage(img)  # Convert the image to a Tkinter-compatible format
            image_label = tk.Label(root, image=tkimg)  # Create a label to display the image
            image_label.pack()  # Pack the label into the window

            getter = tk.Text(root, width=50, height=10)  # Create a label to display the prompt
            getter.insert(tk.INSERT, "Enter Alt-Text for the image above:")  # Insert the prompt text into the label
            getter.pack()  # Pack the label into the window

            def delete_default_text(event:tk.Event):
                event.widget.delete("1.0", tk.END)
                # Unbind so that the default text is not deleted on subsequent focus
                event.widget.unbind("<FocusIn>", on_focus_in) 

            on_focus_in = getter.bind("<FocusIn>", delete_default_text)  # Clear the text area when it gains focus
            root.bind("<Return>", lambda event: root.quit())  # Bind the Enter key to close the window
            root.mainloop()  # Start the Tkinter event loop to display the image

            print(getter.get("1.0", tk.END))  # Print the user input
            #now i just need to display the image and prompt and get the output from the user.
            #output = input(f"Prompt: {prompt}\n\nEnter the alt text for the image: ")  # Get user input for alt text
            output = getter.get("1.0", tk.END)  # Get user input for alt text
            
            #add output to training data
            updated_data.append({"text_input":prompt, "output": output})  # Add the prompt and user input to the updated data list
            root.destroy()  # Destroy the Tkinter window after getting user input
        
        #once thats done, save to new json file
        new_file_dir = join("app", "app_code", "outputs", "training_json", "processed", f"processed_{dataset_filename}")  # Append the subdirectory to the file path
        with open(new_file_dir, 'w') as file:  # Save the updated data to a new JSON file
            json_dump(updated_data, file, indent=4)  # Write the updated data to the file in JSON format
            
        print(f"Updated dataset saved as {new_file_dir}")  # Print the location of the saved file
    

    '''Add data to an unprocessed dataset'''
    def add_to_dataset(self, image_url:str, prompt:str, image_type:str = ""): #used to make the dataset in a program for help.
        #add to the dataset into a jsonl file
        training_data = [{ #This is the data that will be added to the jsonl file
                "link" : f"{image_url}",
                "input": f"{prompt}"
            }]
        
        # appedn.jsonl to the filename
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
    

    def create_gemini_model(self, dataset_filename:str): #where dataset is the name of the json file
        #call the google create model thing to do the thing
        data = json_load(open(join("app", "app_code", "outputs", "training_json","processed", dataset_filename), 'r')) # Load the training data from the JSON file
        training_data = TuningDataset(
            examples=[TuningExample(
                text_input=entry.get("text_input"),  # Use the 'input' field from the JSON data
                output=entry.get("output")  # Use the 'output' field from the JSON data
            ) for entry in data
            ]
        )

        print(f"Training data: {training_data}")  # Print the training data for debugging
        tuning_job = self._client.tunings.tune(
            base_model='models/gemini-1.5-flash-001-tuning',
            training_dataset=training_data,
            config=CreateTuningJobConfig(
                epoch_count= 5,
                batch_size=4,
                learning_rate=0.001,
                tuned_model_display_name="test tuned model"
            )
        )
        print(tuning_job)
    
    def check_tuning_job_status(self, job_id:str):
        #check the status of the tuning job
        tuning_job = self._client.tunings.get(name=job_id)
        print(tuning_job)


    def update_gemini_model(dataset_filename:str): #where dataset is the name of the json file
        pass



if __name__ == "__main__":  # Used for testing purposes
    
    # for model_info in genai.models.list():  # List all available models
    #     print(model_info.name)

    #Trainer.complete_dataset("informativegemini-1.5-flash.jsonl")
    print("Starting Trainer...")
    dummy = Trainer("models/gemini-1.5-flash")
    dummy._client.models.list() #list all models
    # for model_info in dummy._client.models.list():
    #     print(model_info.name)
    for model_info in dummy._client.tunings.list():
        print(model_info.name)
    # dummy.create_gemini_model("processed_informativegemini-1.5-flash.jsonl")

    dummy._client.tunings


    # data = json_load(open(join("app", "app_code", "outputs", "training_json","processed", "processed_informativegemini-1.5-flash.jsonl"), 'r')) # Load the training data from the JSON file
    # training_data = TuningDataset(
    #         examples=[TuningExample(
    #             text_input=entry.get("text_input"),  # Use the 'input' field from the JSON data
    #             output=entry.get("output")  # Use the 'output' field from the JSON data
    #         ) for entry in data
    #         ]
    #     )
    # dummy_dict = {
    #     "text_input": "test",
    #     "output": "test"
    # }
    # dummy_dict.get("text_input")
    # for entry in data:

    #     print(entry.get("text_input"),entry.get("output"))
    # for entry in training_data.examples:
    #     print(entry.text_input)
    #     print(entry.output)

    

    # dummy.check_tuning_job_status("tunedModels/test-tuned-model-icran2mmdiyb")

    # response = dummy._client.models.generate_content(
    #     model="tunedModels/test-tuned-model-icran2mmdiyb",
    #     contents="You are generating **ADA-compliant** alt text based on the given **caption, , and **.\n\n### **Input Data:**\n- **Caption:** Here is a description of the image:\n\nClose-up view of a logo for a company named \"Natural Breeze Professional Remodelers\".\u00c2\u00a0\n\n\nHere's a breakdown of the logo's elements:\n\n* **Text:** The primary text is \"natural breeze,\" styled in a bold, slightly stylized font with some overlapping and layering of the letters.  The words \"PROFESSIONAL REMODELERS\" appear below in a simpler, sans-serif font.\n\n* **Graphic:**\u00c2\u00a0A stylized leaf or maple leaf-like shape is integrated into the design, partially overlapping and behind the text \"Natural Breeze.\" The leaf has a striped pattern.\n\n* **Color:** The entire logo is rendered in shades of gray, appearing monochromatic.\n\n* **Style:** The overall style is clean but somewhat playful, suggesting a blend of natural elements (the leaf) and professionalism (the clear text and layout).\n\n\nThe logo is well-designed and clearly communicates the company name and its business focus.\n\n\n### **Guidelines for Alt Text:**\n1. **Be concise:** Keep the alt text under **150 characters**.\n2. **Be descriptive and meaningful:** Focus on the **essential content** of the image, rather than just its appearance.\n3. **Avoid redundancy:** Do **not** repeat details already provided in the surrounding text.\n4. **Use natural language:** Write in a **clear, fluent, and grammatically correct** way.\n5. **Maintain relevance:** Your response **must** include details from the caption, text, and tags.\n6. **Do NOT** generate generic alt text. The description should be unique to the image.\n\n### **Examples:**\n**Good Alt Text:** 'A person in a wheelchair crossing the street on a sunny day.' (Concise, relevant, and informative)\n**Bad Alt Text:** 'An image of a person outside.' (Too vague, lacks key details)\n\nNow, generate **one** alt text description following these rules.",

    #     )
    
    # print(response.text)
    # print("Pause")
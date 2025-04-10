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
from PIL import Image, ImageTk

import json
import os


from google import generativeai as genai

from google.generativeai.models import list_models
from google.generativeai.models import create_tuned_model
from google.generativeai.models import update_tuned_model

from google.generativeai import types


def retrieveKey():
    file = open("key.txt","r")
    return file.readline()


# training_args = TrainingArguments(output_dir="test_trainer", eval_strategy="epoch")
def add_to_dataset(dataset_filename:str, image_url:str, prompt:str): #used to make the dataset in a program for help.
    #add to the dataset into a jsonl file
    training_data = [
        {
            "link" : f"{image_url}",
            "input": f"{prompt}",
            "output": "DUMMY OUTPUT"
        }
    ]
    jsonl_filename = f"{dataset_filename}.jsonl"
    # open the json, convert to list, append new data, resave
    try:
        with open(os.path.join("app", "app_code", "outputs", "training_json","unprocessed", f"{jsonl_filename}"), "r", encoding="utf-8") as file:
        # Load existing data from the JSONL file into a list
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found: {jsonl_filename}")
        data = []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in: {jsonl_filename}")
        return None
    
    data.append(training_data[0])  # Append the new data to the existing list

    # Save the updated data back to the JSONL file
    with open(os.path.join("app", "app_code", "outputs", "training_json","unprocessed", f"{jsonl_filename}"), "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)  # Write the updated data to the file in JSON format

    print(f"Dataset saved as {jsonl_filename}")
    


### this is such a nightmare of a function.
def complete_dataset(dataset_filename:str): #where dataset is the name of the json file
    
    file_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file

    updated_data = []  # Create an empty list to store the updated data
    data = []  # Create an empty list to store the data from the JSON file

    for entry in data:
        url = entry['link']  # Extract the image URL from the entry
        prompt = entry['input']  # Extract the prompt from the entry
        #now i need to show user the prompt and image and get output. Now that i think about it, the json doesnt need out, im just gonna make a new file.
        # thread = threading.Thread(target=display_image, args=(url))  # Create a thread to display the image
        # thread.start()  # Start the thread to display the image
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        root = tk.Tk()  # Create a Tkinter window 
        tkimg = ImageTk.PhotoImage(img)  # Convert the image to a Tkinter-compatible format
        outie = tk.StringVar()  # Create a StringVar to hold the user input
        outie.set("Enter the alt text for the image: ")  # Set the initial text for the entry field
        label = tk.Label(root, image=tkimg)  # Create a label to display the image
        getter = tk.Entry(root, textvariable=outie)  # Create a label to display the prompt
        label.pack()  # Pack the label into the window
        getter.pack()  # Pack the label into the window
        root.bind("<Return>", lambda event: root.quit())  # Bind the Enter key to close the window
        root.mainloop()  # Start the Tkinter event loop to display the image

        print(outie.get())  # Print the user input
        #now i just need to display the image and prompt and get the output from the user.
        #output = input(f"Prompt: {prompt}\n\nEnter the alt text for the image: ")  # Get user input for alt text
        output = outie.get()  # Get user input for alt text
        
        #add output to training data
        updated_data.append({"prompt":prompt, "output": output})  # Add the prompt and user input to the updated data list
        root.destroy()  # Destroy the Tkinter window after getting user input
    
    #once thats done, save to new json file
    new_file_dir = os.path.join(file_dir, "outputs", "training_json", "processed", "alt_text_dataset_post.jsonl")  # Append the subdirectory to the file path
    with open(new_file_dir, 'w') as file:  # Save the updated data to a new JSON file
        json.dump(updated_data, file, indent=4)  # Write the updated data to the file in JSON format
        
    print(f"Updated dataset saved as {new_file_dir}")  # Print the location of the saved file

def create_gemini_model(dataset_filename:str): #where dataset is the name of the json file
    #call the google create model thing to do the thing
    create_tuned_model(genai.GenerativeModel("gemini-1.5-flash"),
                       dataset_filename,
                       "ada_gemini-1.5-flash",
                        "ADA gemini",
                        "Model for generating ADA compliant alt text")
                        # temperature= 0.0,
                        # top_p: float | None = None,
                        # top_k: int | None = None,
                        # epoch_count: int | None = None,
                        # batch_size: int | None = None,
                        # learning_rate: float | None = None,
                        # input_key: str = "text_input",
                        # output_key: str = "output",
                        # client: ModelServiceClient | None = None,
                        # request_options: RequestOptionsType | None = None)


def update_gemini_model(dataset_filename:str): #where dataset is the name of the json file
    pass
    

def display_image(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    root = tk.Tk()  # Create a Tkinter window 
    tkimg = ImageTk.PhotoImage(img)  # Convert the image to a Tkinter-compatible format
    label = tk.Label(root, image=tkimg)  # Create a label to display the image
    label.pack()  # Pack the label into the window
    root.mainloop()  # Start the Tkinter event loop to display the image



if __name__ == "__main__":  # Used for testing purposes
    genai.configure(api_key=retrieveKey())

    print()
    list_models() 
    print()
    
    # for model_info in genai.models.list():  # List all available models
    #     print(model_info.name)

    #complete_dataset("gemini.jsonl")
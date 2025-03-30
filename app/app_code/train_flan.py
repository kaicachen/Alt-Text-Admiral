'''
Author: John
Created: 3/10/2025
Last modified: 3/10/2025

Description:
Code to train the model. 
'''

import requests
from io import BytesIO
import tkinter as tk
from PIL import Image, ImageTk
import threading
import subprocess

import json
import os


# from transformers import AutoModelForSequenceClassification
# from transformers import TrainingArguments
# from transformers import AutoTokenizer
# # from datasets import load_dataset

# import numpy as np
# # import evaluate
# from transformers import TrainingArguments, Trainer

##here we load things to make our own usage of the model
# from web_scraper import * #web scraper to get URLS?
# maybe pull code directly from the file for more control?
#man lets just try with one thing.

# metric = evaluate.load("accuracy")
# tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")

# def compute_metrics(eval_pred):
#     logits, labels = eval_pred
#     predictions = np.argmax(logits, axis=-1)
#     # return metric.compute(predictions=predictions, references=labels)

# def tokenize_function(examples):
#     return tokenizer(examples["text"], padding="max_length", truncation=True)


# model = AutoModelForSequenceClassification.from_pretrained("google/flan-t5-large", num_labels=5, torch_dtype="auto")

# training_args = TrainingArguments(output_dir="test_trainer", eval_strategy="epoch")

def clean_dataset(dataset_filename:str): #where dataset is the name of the json file
    #clean the dataset into a jsonl file because Its annoying to make it properly during data collection
    file_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
    file_path = os.path.join(file_dir, "outputs", "training_json", "unprocessed", f'{dataset_filename}')  # Append the subdirectory to the file path

    new_list = []  # Create an empty list to store the cleaned data
    with open(file_path, 'r') as file:  # Load the dataset
        for line in file:
            try:
                clean_line = line.replace("\n", "")  # Remove newline characters from each line as json hates them
                data = json.loads(clean_line)  # Parse each line as JSON
                new_list.append(data)  # Append the parsed data to the new list
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")

    #move the cleaned data to a new file
    new_file_dir = os.path.join(file_dir, "outputs", "training_json", "unprocessed", f'json_{dataset_filename}')  # Append the subdirectory to the file path
    with open(new_file_dir, 'w') as file:  # Save the cleaned data to a new JSON file
        try:
            json.dump(new_list, file, indent=4)  # Write the cleaned data to the file in JSON format
        except Exception as e:
            print(f"Error writing JSON: {e}")
    print(f"Cleaned dataset saved as {new_file_dir}")  # Print the location of the saved file
    return new_list

def train_model(dataset_filename:str): #where dataset is the name of the json file
    # tokenized_datasets = dataset.map(tokenize_function, batched=True)
    # small_train_dataset = tokenized_datasets["train"].shuffle(seed=42).select(range(1000))
    # small_eval_dataset = tokenized_datasets["test"].shuffle(seed=42).select(range(1000))
    # #we gonna give exactly one example for the trainer and see what that does
    # trainer = Trainer(
    #     model=model,
    #     args=training_args,
    #     train_dataset=small_train_dataset,
    #     eval_dataset=small_eval_dataset,
    #     compute_metrics=compute_metrics,
    # )
    #we switched to gemini for the model so this code is kinda redundant now.

    # #instead, use this to load images and create a dataset for the model to train on.
    file_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
    # file_dir = os.path.join(file_dir, "outputs", "training_json", "unprocessed", f'{dataset_filename}')  # Append the subdirectory to the file path
    
    
    # updated_data = []
    # with open(file_dir, 'r') as file: # load the dataset
    #     data = json.load(file)
    
    data = clean_dataset(dataset_filename)  # Load the dataset
    updated_data = []  # Create an empty list to store the updated data

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
    data = json.dumps(updated_data, indent=4)  # Convert the updated data to JSON format
    with open(new_file_dir, 'w') as file:  # Save the updated data to a new JSON file
        file.write(data)  # Write the JSON data to the file
    print(f"Updated dataset saved as {new_file_dir}")  # Print the location of the saved file

def display_image(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    root = tk.Tk()  # Create a Tkinter window 
    tkimg = ImageTk.PhotoImage(img)  # Convert the image to a Tkinter-compatible format
    label = tk.Label(root, image=tkimg)  # Create a label to display the image
    label.pack()  # Pack the label into the window
    root.mainloop()  # Start the Tkinter event loop to display the image




#okay, i want to train the model on input given to it? alternatively I want to create datasets from a website,
#and then give good alt text for that model and then train it on that. SO i need to change the code from sentence_generator.py 
#or main captioner to send data to a file instead of a model


#what i need: captions, tags from sentence generator to make the prompt. PLus the prompt. I kinda also need the image site and link? so i can make good alt text
#then I combine prompt and the alt text to make the input for the model.
#I could redo all of the code so It pauses on each image. or I make new code that does that.
# What I want (Site URL, Image URL, prompt, good alt text)
# we get site URL from initial input, image url from src, prompt from the generator, and we provide good alt text
#so ...... how do i get all the things in order. Need to pass to a certain file. Ugh, we need to streamline this shit

#okay in a bass ackwards way I can use just the prompt and make text from that.




if __name__ == "__main__":  # Used for testing purposes
    # Input words
    # caption = "A field on a sunny day"
    # tags = "blue, sky, bright, sun"
    #sentence = generate_sentence(caption, tags)
    #print(sentence)
    train_model("alt_text_dataset_pre.jsonl")
    #clean_dataset("alt_text_dataset_pre.jsonl")
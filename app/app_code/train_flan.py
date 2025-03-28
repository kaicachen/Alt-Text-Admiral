'''
Author: John
Created: 3/10/2025
Last modified: 3/10/2025

Description:
Code to train the Flan model. 
'''

from transformers import AutoModelForSequenceClassification
from transformers import TrainingArguments
from transformers import AutoTokenizer
from datasets import load_dataset

import numpy as np
import evaluate
from transformers import TrainingArguments, Trainer

##here we load things to make our own usage of the model
from web_scraper import * #web scraper to get URLS?
# maybe pull code directly from the file for more control?
#man lets just try with one thing.

metric = evaluate.load("accuracy")
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
dataset = load_dataset("imdb")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True)


model = AutoModelForSequenceClassification.from_pretrained("google/flan-t5-large", num_labels=5, torch_dtype="auto")

training_args = TrainingArguments(output_dir="test_trainer", eval_strategy="epoch")


def train_model(dataset):
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    small_train_dataset = tokenized_datasets["train"].shuffle(seed=42).select(range(1000))
    small_eval_dataset = tokenized_datasets["test"].shuffle(seed=42).select(range(1000))
    #we gonna give exactly one example for the trainer and see what that does
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=small_train_dataset,
        eval_dataset=small_eval_dataset,
        compute_metrics=compute_metrics,
    )
    
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

def create_data(data_file):
    #take in a datafile, from json which is of the form prompt,response.
    #how to make json files
    pass



if __name__ == "__main__":  # Used for testing purposes
    # Input words
    caption = "A field on a sunny day"
    tags = "blue, sky, bright, sun"
    #sentence = generate_sentence(caption, tags)
    #print(sentence)
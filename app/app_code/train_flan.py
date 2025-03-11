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

metric = evaluate.load("accuracy")
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")

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
#



if __name__ == "__main__":  # Used for testing purposes
    # Input words
    caption = "A field on a sunny day"
    tags = "blue, sky, bright, sun"
    #sentence = generate_sentence(caption, tags)
    #print(sentence)
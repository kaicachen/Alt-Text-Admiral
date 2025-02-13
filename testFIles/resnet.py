from transformers import AutoImageProcessor, ResNetForImageClassification
import torch
# from compile_to_csv import compile_to_csv

# from datasets import load_dataset

from PIL import Image   # For testing purposes - access a locally stored image on your machine
image_path = "images/cat.png"
image = Image.open(image_path).convert('RGB')  # Image.open() doesn't like transparent images, so converted to raw RGB

#dataset = load_dataset("huggingface/cats-image")
#image = dataset["test"]["image"][0]

processor = AutoImageProcessor.from_pretrained("microsoft/resnet-50")
model = ResNetForImageClassification.from_pretrained("microsoft/resnet-50")

inputs = processor(image, return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits

# model predicts one of the 1000 ImageNet classes
predicted_label = logits.argmax(-1).item()
# print(model.config.id2label[predicted_label])

# # Save prediction to CSV
# image_metadata = [
#     {
#         "image_name": image_path,
#         "tags": [predicted_label],  # Using the predicted label as a tag
#         "is_decorative": False,
#         "is_link": False,
#         "is_infographic": False
#     }
# ]

# compile_to_csv("image_predictions.csv", image_metadata)
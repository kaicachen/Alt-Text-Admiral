from transformers import AutoImageProcessor, ResNetForImageClassification
import torch

# from datasets import load_dataset

from PIL import Image   # For testing purposes - access a locally stored image on your machine

image = Image.open("images/cat.png").convert('RGB')  # Image.open() doesn't like transparent images, so converted to raw RGB

#dataset = load_dataset("huggingface/cats-image")
#image = dataset["test"]["image"][0]

processor = AutoImageProcessor.from_pretrained("microsoft/resnet-50")
model = ResNetForImageClassification.from_pretrained("microsoft/resnet-50")

inputs = processor(image, return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits

# model predicts one of the 1000 ImageNet classes
predicted_label = logits.argmax(-1).item()
print(model.config.id2label[predicted_label])

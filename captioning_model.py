'''
This code was largely written by ChatGPT
'''

import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import requests

# Load the BLIP processor and model
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to("cuda" if torch.cuda.is_available() else "cpu")

import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import requests

# Load the BLIP processor and model
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to("cuda" if torch.cuda.is_available() else "cpu")

# Load an example image
image_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQE1beX5NmDZEd_vN2gja1SCmN6RW7kMwb_xsx9nHrHseAadgMQIFvIs1V8Hy7aG7flV_Tt2g" # "https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg"
image = Image.open(requests.get(image_url, stream=True).raw)

# Process image
inputs = processor(images=image, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")

# Generate caption from image only
caption_ids = model.generate(**inputs)
caption = processor.decode(caption_ids[0], skip_special_tokens=True)
print("Generated Caption:", caption)

# Provide additional context for captioning
context_text = "movie poster for a christopher nolan film" # "This is an image about a person riding a horse on the beach."
inputs = processor(images=image, text=context_text, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")


inputs = processor(images=image, text=context_text, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
caption_ids = model.generate(**inputs)
caption = processor.decode(caption_ids[0], skip_special_tokens=True)
print("Generated Caption with Context:", caption)

# # Generate caption with additional context
# caption_ids = model.generate(**inputs)
# caption = processor.decode(caption_ids[0], skip_special_tokens=True)
# print("Generated Caption with Context:", caption)

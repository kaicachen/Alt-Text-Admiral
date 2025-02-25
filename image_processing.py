'''
This code was written with help from ChatGPT
'''

from transformers import DetrImageProcessor, DetrForObjectDetection, BlipProcessor, BlipForConditionalGeneration, logging
import torch
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from compile_to_csv import compile_to_csv  # Import the correct function

class ImageProcessor:
    def __init__(self, image_loc, URL=False):
        self.loc = image_loc # saves path or url for CSV writing later

        if URL: # runs if location passed in is a URL
            response = requests.get(image_loc)
            
            if response.status_code != 200:
                self.image = None
                print(f"ERROR LOADING IMAGE {self.loc}")
                return
            
            self.image = Image.open(BytesIO(response.content))

        else: # runs if a direct file path is given
            self.image = Image.open(image_loc) #.convert("RGB")

        self.image = self.image.convert("RGB")
        logging.set_verbosity_error()

    def generate_caption_with_blip(self):
        # Initialize the BLIP processor and model
        blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
        blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

        try:
            # Prepare the image for caption generation
            inputs = blip_processor(images=self.image, return_tensors="pt")
        except:
            print(f"FAIELD TO PROCESS {self.loc}")
            return ""

        # Generate caption
        out = blip_model.generate(**inputs)
        caption = blip_processor.decode(out[0], skip_special_tokens=True)
        
        return caption

    def find_image_objects(self, show_graph=False):
        # Load the model and processor (DETR - Facebook's object detection model)
        device = "cuda" if torch.cuda.is_available() else "cpu"  # Sets active device as GPU if available, otherwise it runs on the CPU
        print(torch.cuda.device_count())
        processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(device)

        try:
            inputs = processor(images=self.image, return_tensors="pt").to(device)
        except:
            print(f"FAIELD TO PROCESS {self.loc}")
            return {}

        # Perform inference
        with torch.no_grad():
            outputs = model(**inputs)

        # Process results
        target_sizes = torch.tensor([self.image.size[::-1]])  # (height, width)
        results = processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]

        # Prepare metadata storage
        detected_objects = {}

        if show_graph:
            # Visualize results
            fig, ax = plt.subplots(1, figsize=(10, 5))
            ax.imshow(self.image)

        # Draw bounding boxes
        
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                
                if score >= .7:
                    obj_name = model.config.id2label[label.item()]
                    detected_objects[obj_name] = detected_objects.get(obj_name, 0) + 1

                if show_graph and score > 0.5:  # Filter low-confidence predictions
                    x, y, w, h = box
                    rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor="r", facecolor="none")
                    ax.add_patch(rect)
                    ax.text(x, y, f"{model.config.id2label[label.item()]}: {score:.2f}", color="white",
                            bbox=dict(facecolor="red", alpha=0.5))
                    # print(f"{model.config.id2label[label.item()]}: {score:.2f}")
            

        # print(f"Detected objects: {detected_objects}\n")

        # Convert detected objects to list format for CSV
        tags_list = [f"{tag} ({count})" for tag, count in detected_objects.items()]

        # Save detected objects to CSV
        image_metadata = [
            {
                "image_name": self.loc,
                "tags": tags_list,  # Extract just the tag names
                "is_decorative": False,
                "is_link": False,
                "is_infographic": False
            }
        ]

        compile_to_csv("detection_results.csv", image_metadata)  # Use correct function

        if show_graph:
            plt.show()

        return detected_objects


if __name__ == "__main__":
    # Load and preprocess the image
    image_path = "images/lebron.jpg"
    # image = Image.open(image_path).convert("RGB")
    image_processor = ImageProcessor(image_path)
    caption = image_processor.generate_caption_with_blip()
    detected_objects = image_processor.find_image_objects(show_graph=True)
    print(f"Caption: ({caption})\nObjects: ({detected_objects})")
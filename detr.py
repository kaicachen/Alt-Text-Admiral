from transformers import DetrImageProcessor, DetrForObjectDetection
import torch
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Load the model and processor (DETR - Facebook's object detection model)
processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

# Load and preprocess the image
image = Image.open("images/basketball.jpg").convert("RGB")
inputs = processor(images=image, return_tensors="pt")

# Perform inference
with torch.no_grad():
    outputs = model(**inputs)

# Process results
target_sizes = torch.tensor([image.size[::-1]])  # (height, width)
results = processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]

# Visualize results
fig, ax = plt.subplots(1, figsize=(10, 5))
ax.imshow(image)

# Draw bounding boxes
for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
    if score > 0.5:  # Filter low-confidence predictions
        x, y, w, h = box
        rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor="r", facecolor="none")
        ax.add_patch(rect)
        ax.text(x, y, f"{model.config.id2label[label.item()]}: {score:.2f}", color="white", 
                bbox=dict(facecolor="red", alpha=0.5))
        print(f"{model.config.id2label[label.item()]}: {score:.2f}")

plt.show()

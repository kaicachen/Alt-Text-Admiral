from transformers import DetrImageProcessor, DetrForObjectDetection
import torch
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from compile_to_csv import compile_to_csv  # Import the correct function

def find_image_objects(image_path):
    # Load the model and processor (DETR - Facebook's object detection model)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(torch.cuda.device_count())
    processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
    model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(device)

    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)

    # Perform inference
    with torch.no_grad():
        outputs = model(**inputs)

    # Process results
    target_sizes = torch.tensor([image.size[::-1]])  # (height, width)
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]

    # Prepare metadata storage
    detected_objects = {}

    # Visualize results
    fig, ax = plt.subplots(1, figsize=(10, 5))
    ax.imshow(image)

    # Draw bounding boxes
    
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):

            # Store detected object info
            obj_name = model.config.id2label[label.item()]
            detected_objects[obj_name] = detected_objects.get(obj_name, 0) + 1

            '''
        if score > 0.5:  # Filter low-confidence predictions
            x, y, w, h = box
            rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor="r", facecolor="none")
            ax.add_patch(rect)
            ax.text(x, y, f"{model.config.id2label[label.item()]}: {score:.2f}", color="white",
                    bbox=dict(facecolor="red", alpha=0.5))
            # print(f"{model.config.id2label[label.item()]}: {score:.2f}")
        '''

    # print(f"Detected objects: {detected_objects}\n")

    # Convert detected objects to list format for CSV
    tags_list = [f"{tag} ({count})" for tag, count in detected_objects.items()]

    # Save detected objects to CSV
    image_metadata = [
        {
            "image_name": image_path,
            "tags": tags_list,  # Extract just the tag names
            "is_decorative": False,
            "is_link": False,
            "is_infographic": False
        }
    ]

    compile_to_csv("detection_results.csv", image_metadata)  # Use correct function
    return detected_objects

    # plt.show()

if __name__ == "__main__":
    # Load and preprocess the image
    image_path = "images/basketball.jpg"
    # image = Image.open(image_path).convert("RGB")
    detected_objects = find_image_objects(image_path)
    print(detected_objects)
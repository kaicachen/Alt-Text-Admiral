from PIL import Image
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import csv

def create_pdf(file_name):
    image_text_list = []

    with open(f"{file_name}.csv", mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        
        next(reader)

        # Convert reader object to a list or iterate over rows
        for row in reader:
            image_text_list.append(row)

    c = canvas.Canvas(f"{file_name}.pdf", pagesize=letter)
    width, height = letter
    y_position = height - 200  # Initial vertical position

    for image_url, text in image_text_list:
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))

        except Exception as e:
            print(f"Error loading image {image_url}: {e}")
            image = Image.open(image_url).convert("RGB")

        img_reader = ImageReader(image)
        
        if y_position < 100:
            c.showPage()
            y_position = height - 200

        c.drawImage(img_reader, 50, y_position, width=150, height=150)
        c.drawString(220, y_position + 65, text)
        y_position -= 200  # Move down for next entry

    c.save()
    print(f"PDF saved as {file_name}.pdf")

if __name__ == "__main__":
    create_pdf("lied_center")

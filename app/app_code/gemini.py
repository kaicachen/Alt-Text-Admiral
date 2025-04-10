import google.generativeai as genai
import os
import json

def geminiGenerate(caption,text,tags, image_url, training=False):
    API_KEY = retrieveKey()
    genai.configure(api_key=API_KEY)
    model=genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"You are generating **ADA-compliant** alt text based on the given **caption, surrounding text, and tags**.\n\n"
        f"### **Input Data:**\n"
        f"- **Caption:** {caption}\n"
        f"- **Surrounding Text:** {text}\n"
        f"- **Tags:** {tags}\n\n"
        
        f"### **Guidelines for Alt Text:**\n"
        f"1. **Be concise:** Keep the alt text under **150 characters**.\n"
        f"2. **Be descriptive and meaningful:** Focus on the **essential content** of the image, rather than just its appearance.\n"
        f"3. **Avoid redundancy:** Do **not** repeat details already provided in the surrounding text.\n"
        f"4. **Use natural language:** Write in a **clear, fluent, and grammatically correct** way.\n"
        f"5. **Maintain relevance:** Your response **must** include details from the caption, text, and tags.\n"
        f"6. **Do NOT** generate generic alt text. The description should be unique to the image.\n\n"
        
        f"### **Examples:**\n"
        f"**Good Alt Text:** 'A person in a wheelchair crossing the street on a sunny day.' (Concise, relevant, and informative)\n"
        f"**Bad Alt Text:** 'An image of a person outside.' (Too vague, lacks key details)\n\n"
        
        f"Now, generate **one** alt text description following these rules."
        )
    #if training, save prompt and response to a file.
    if training:
        training_data = [
            {
                "link" : f"{image_url}",
                "input": 
                    f"You are generating **ADA-compliant** alt text based on the given **caption, surrounding text, and tags**.\n\n"
                    f"### **Input Data:**\n"
                    f"- **Caption:** {caption}\n"
                    f"- **Surrounding Text:** {text}\n"
                    f"- **Tags:** {tags}\n\n"

                    f"### **Guidelines for Alt Text:**\n"
                    f"1. **Be concise:** Keep the alt text under **150 characters**.\n"
                    f"2. **Be descriptive and meaningful:** Focus on the **essential content** of the image, rather than just its appearance.\n"
                    f"3. **Avoid redundancy:** Do **not** repeat details already provided in the surrounding text.\n"
                    f"4. **Use natural language:** Write in a **clear, fluent, and grammatically correct** way.\n"
                    f"5. **Maintain relevance:** Your response **must** include details from the caption, text, and tags.\n"
                    f"6. **Do NOT** generate generic alt text. The description should be unique to the image.\n\n"

                    f"### **Examples:**\n"
                    f"**Good Alt Text:** 'A person in a wheelchair crossing the street on a sunny day.' (Concise, relevant, and informative)\n"
                    f"**Bad Alt Text:** 'An image of a person outside.' (Too vague, lacks key details)\n\n"

                    f"Now, generate **one** alt text description following these rules.",
                "output": "DUMMY OUTPUT"
            }
        ]
        jsonl_filename = "alt_text_dataset_pre.jsonl"
        with open(os.path.join("app", "app_code", "outputs", "training_json","unprocessed", f"{jsonl_filename}"), "a", encoding="utf-8") as file:
            for entry in training_data:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"Dataset saved as {jsonl_filename}")
        
    return response.text

def retrieveKey():
    file = open("key.txt","r")
    return file.readline()

if __name__ == "__main__":
    response = geminiGenerate()
    print(response)


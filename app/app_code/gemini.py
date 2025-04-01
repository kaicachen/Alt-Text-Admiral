import google
import google.generativeai as genai
import time

def geminiGenerate(image_type, caption,text,tags):
    API_KEY = retrieveKey()
    genai.configure(api_key=API_KEY)
    model=genai.GenerativeModel("gemini-1.5-flash")

    # Check if generation has completed
    not_generated = True
    sleep_length = 1

    while(not_generated):
        try:
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
            not_generated = False

        except Exception as e:
            # Wait before regenerating and increase sleep time incase of repeat error
            if "You exceeded your current quota" in str(e) and sleep_length < 10:
                print(f"ResourceExhausted occured, sleeping for {sleep_length} second then regenerating")
                time.sleep(sleep_length)
                sleep_length +=1

            else:
                raise e

            

    
    
    return response.text

def retrieveKey():
    file = open("key.txt","r")
    return file.readline()

if __name__ == "__main__":
    response = geminiGenerate()
    print(response)


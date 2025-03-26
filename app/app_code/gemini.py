import google.generativeai as genai

def geminiGenerate(caption,text,tags):
    API_KEY = retrieveKey()
    genai.configure(api_key=API_KEY)
    model=genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"Use the example caption, surrounding text, and important tags to create a well-structured and fluent ADA compliant alt-text for an image:\n"
        f"Caption: {caption}\nText: {text}\nTags: {tags}\n"  # Ensures that the caption is passed in along with the tags we want
        f"Make sure the sentence is clear, natural, and grammatically correct."

        # ============================================ ADA-Compliant Alt-text Rules ============================================
        f"Alt-text should be short and to the point."
        f"Alt-text should communicate the same information as the visual content."
        f"Alt-text should refer to relevant content provided by the image, rather than simply describing how the image looks."
        f"Alt-text should not contain any extra or unnecessary information, and should not repeat information that is already provided in the text."
        f"Alt-text must be in the same language as the main content."
        f"Please keep your response to a maximum of 150 characters.\n"
        "**Important:** You must use the provided caption, surrounding text, and tags to create the description. Do NOT generate unrelated or generic responses.\n\n")
    
    return response.text

def retrieveKey():
    file = open("key.txt","r")
    return file.readline()

if __name__ == "__main__":
    response = geminiGenerate()
    print(response)


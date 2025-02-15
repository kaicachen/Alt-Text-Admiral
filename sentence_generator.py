from transformers import pipeline
import torch

def generate_sentence(captions, tags):
    # Load the model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    generator = pipeline("text2text-generation", model="google/flan-t5-large",device=device)


    # Generate a sentence
    # output = generator(f"Form a proper sentence using these words: {words}", max_length=500)
    # output = generator(f"Form a proper sentence using these words and names: {tags}", max_length=1000)

    prompt = (
        f"Use the example caption and tags to create a well-structured and fluent ADA compliant alt-text for an image:\n"
        f"Caption: {captions}\nTags: {tags}\n\n"
        f"Make sure the sentence is clear, natural, and grammatically correct."
        f"Alt-text should be short and to the point."
        f"Alt-text should communicate the same information as the visual content."
        f"Alt-text should refer to relevant content provided by the image, rather than simply describing how the image looks."
        f"Alt-text should not contain any extra or unnecessary information, and should not repeat information that is already provided in the text."
        f"Alt-text must be in the same language as the main content."
    )

    

    output = generator(prompt, max_length=1000)

    #print(output[0]["generated_text"])
    return output[0]["generated_text"]

if __name__ == "__main__":
    # Input words
    caption = "A field on a sunny day"
    tags = "blue, sky, bright, sun"
    sentence = generate_sentence(caption, tags)
    print(sentence)
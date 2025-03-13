from transformers import pipeline, logging
import torch

def generate_sentence(captions, text):
    logging.set_verbosity_error()
    # Load the model
    device = "cuda" if torch.cuda.is_available() else "cpu"  # Sets active device as GPU if available, otherwise it runs on the CPU
    generator = pipeline("text2text-generation", model="google/flan-t5-large",device=device)  # Creates a pipeline to load the model


    # Generate a sentence
    # output = generator(f"Form a proper sentence using these words: {words}", max_length=500)
    # output = generator(f"Form a proper sentence using these words and names: {tags}", max_length=1000)

    prompt = (  # Prompt to pass into the alt-text generator
        f"Use the example caption and surrounding text to create a well-structured and fluent ADA compliant alt-text for an image:\n"
        f"Caption: {captions}\nText: {text}\n\n"  # Ensures that the caption is passed in along with the tags we want
        f"Make sure the sentence is clear, natural, and grammatically correct."

        # ============================================ ADA-Compliant Alt-text Rules ============================================
        f"Alt-text should be short and to the point."
        f"Alt-text should communicate the same information as the visual content."
        f"Alt-text should refer to relevant content provided by the image, rather than simply describing how the image looks."
        f"Alt-text should not contain any extra or unnecessary information, and should not repeat information that is already provided in the text."
        f"Alt-text must be in the same language as the main content."
    )

    

    output = generator(prompt, max_length=1000)  # Generates the alt-text based on the prompt

    return output[0]["generated_text"]  # The generated text is formatted as a single-element list with a dictionary, where "generated_text" is the key

if __name__ == "__main__":  # Used for testing purposes
    # Input words
    caption = "A field on a sunny day"
    tags = "blue, sky, bright, sun"
    sentence = generate_sentence(caption, tags)
    print(sentence)
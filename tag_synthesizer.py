from transformers import pipeline

def generate_sentence(words):
    # Load the model
    generator = pipeline("text2text-generation", model="google/flan-t5-large")

    # Generate a sentence
    # output = generator(f"Form a proper sentence using these words: {words}", max_length=500)
    output = generator(f"Form a proper sentence using these words and names: {words}", max_length=1000)

    #print(output[0]["generated_text"])
    return output[0]["generated_text"]

if __name__ == "__main__":
    # Input words
    words = "blue, sky, bright, sun"
    sentence = generate_sentence(words)
    print(sentence)
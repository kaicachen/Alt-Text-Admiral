from transformers import pipeline, logging
import torch
# This is here to test GPU capability, couldn't get it running because I'm out of storage so I'll reconfig stuff later - AAP
# import torch
# print(torch.cuda.is_available())  # Should return True if a GPU is available
# print(torch.cuda.device_count())  # Number of available GPUs
# print(torch.cuda.get_device_name(0))  # Name of the first GPU

def extract_entities(text):
    logging.set_verbosity_error()
    # Load a better NER model with token aggregation
    device = "cuda" if torch.cuda.is_available() else "cpu"  # Sets active device as GPU if available, otherwise it runs on the CPU
    ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple",device=device)

    results = ner_pipeline(text)

    # # Print all detected entities
    # for entity in results:
    #     print(f"Entity: {entity['word']}, Type: {entity['entity_group']}, Score: {entity['score']:.4f}")

    # Extract just the names (persons)
    sorted_entities = {"People":[entity['word'] for entity in results if entity['entity_group'] == "PER"],
                       "Organizations":[entity['word'] for entity in results if entity['entity_group'] == "ORG"],
                       "OTHER":[entity['word'] for entity in results if (entity['entity_group'] != "PER" and entity['entity_group'] != "ORG")]}
    
    return sorted_entities

if __name__ == "__main__":
    text = "Elon Musk is the CEO of Tesla and SpaceX. Steve Jobs was the co-founder of Apple and ate an apple every day."
    entities = extract_entities(text)
    print(entities)
